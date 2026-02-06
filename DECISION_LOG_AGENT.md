# Decision Log Agent - Copilot-CLI Integration Guide

## Overview

The **Decision Log Agent** captures and maintains institutional memory of technical decisions, their rationale, context, alternatives considered, and evolution over time. This is one of the most underrated agents because teams often lose critical context about why decisions were made, leading to repeated debates, reversal of good decisions, or inability to evaluate trade-offs.

## Why This Agent is Underrated

**Common Problem**: Six months after a technical decision, the team asks:
- "Why did we choose PostgreSQL over MongoDB?"
- "What were the trade-offs we considered?"
- "Has the context changed since then?"
- "Who made this decision and why?"

**Without Decision Logs**: Knowledge lives in people's heads, old Slack messages, or scattered meeting notes. New team members don't understand the rationale. Decisions get reversed without understanding the original constraints.

**With Decision Log Agent**: Every significant decision is captured with full context, alternatives, trade-offs, and can be revisited when circumstances change. The knowledge base becomes the organization's technical memory.

## Use Cases

- **Architecture Decision Records (ADRs)**: Document architectural choices with rationale
- **Technology Selection**: Track why specific tools/frameworks were chosen
- **API Design Decisions**: Document interface design choices and evolution
- **Performance Optimization**: Record what was tried, what worked, what didn't
- **Security Decisions**: Track security trade-offs and risk acceptance
- **Process Changes**: Document why processes were changed
- **Refactoring Decisions**: Capture refactoring rationale and approach
- **Onboarding**: New team members understand historical context
- **Decision Review**: Revisit decisions when context changes

## Architecture

### Entity Types

1. **Decisions**: The core decision with rationale, alternatives, and outcome
2. **Contexts**: Environmental factors influencing decisions (constraints, requirements)
3. **Alternatives**: Options that were considered but not chosen
4. **Consequences**: Realized outcomes (positive and negative)
5. **Reviews**: Periodic reassessments of decisions
6. **Stakeholders**: People involved in or affected by decisions

### Link Types

- `supersedes`: New decision replaces old one
- `builds_on`: Decision builds upon previous decision
- `conflicts_with`: Decisions that are incompatible
- `influences`: One decision affects another
- `implements`: Implementation of a decision
- `reviews`: Consequence or review of a decision
- `considers`: Alternative that was considered

### Decision Metadata

```json
{
  "type": "decision",
  "status": "accepted|rejected|deprecated|superseded",
  "category": "architecture|technology|process|security|performance",
  "decision_date": "2026-02-06",
  "author": "username",
  "stakeholders": ["team-lead", "architect", "security"],
  "impact": "high|medium|low",
  "reversibility": "reversible|difficult|irreversible",
  "cost_to_change": "low|medium|high",
  "review_date": "2026-08-06"
}
```

## Workflow 1: Capturing Architecture Decisions

### Goal
Document architecture decisions using ADR format with full context.

### Process

```bash
#!/bin/bash
# capture_architecture_decision.sh

DECISION_TITLE="Use PostgreSQL for Primary Database"
DECISION_DATE=$(date -u +%Y-%m-%d)

# 1. Document the decision with full context
DECISION_CONTENT=$(cat <<'EOF'
## Status
Accepted

## Context
We need a database for the user management system. Requirements:
- ACID transactions for user data integrity
- Complex queries with JOINs for reporting
- 10K users initially, potential to scale to 100K
- Team has SQL experience
- Budget constraints favor open-source solutions

## Decision
We will use PostgreSQL as the primary database.

## Rationale
- Strong ACID guarantees for financial data
- Excellent support for complex queries and transactions
- Proven scalability to millions of rows
- Rich ecosystem of tools and extensions
- Team expertise in SQL databases
- Open-source with strong community support
- Battle-tested in production environments

## Alternatives Considered

### MongoDB
- **Pros**: Flexible schema, horizontal scaling, JSON documents
- **Cons**: Weaker consistency guarantees, team lacks NoSQL experience, overhead for simple transactional operations
- **Why Not Chosen**: ACID requirements and team expertise favor SQL

### MySQL
- **Pros**: Popular, well-documented, team familiar
- **Cons**: Less robust feature set than PostgreSQL, licensing concerns for some use cases
- **Why Not Chosen**: PostgreSQL offers more features for same operational complexity

### SQLite
- **Pros**: Simple, embedded, no server
- **Cons**: Not suitable for multi-user concurrent access, limited scalability
- **Why Not Chosen**: Need multi-user support from day one

## Consequences

### Positive
- Strong data integrity guarantees
- Complex reporting queries will be efficient
- Can leverage team's existing SQL knowledge
- Rich ecosystem of monitoring and management tools

### Negative
- Vertical scaling limitations compared to distributed databases
- More operational complexity than managed NoSQL services
- Need to manage backup and replication ourselves

### Risks
- If we exceed PostgreSQL's vertical scaling limits, migration will be costly
- Team needs to learn PostgreSQL-specific features (vs generic SQL)

## Implementation
- Version: PostgreSQL 15
- Hosting: AWS RDS for managed operations
- Connection pooling: PgBouncer
- Backup strategy: Daily snapshots + WAL archiving

## Review
This decision should be reviewed in 6 months when we reach 50K users.
EOF
)

DECISION_ID=$(./kb-cli add-entity \
    "$DECISION_TITLE" \
    "$DECISION_CONTENT" \
    "{\"type\":\"decision\",\"status\":\"accepted\",\"category\":\"architecture\",\"decision_date\":\"$DECISION_DATE\",\"impact\":\"high\",\"reversibility\":\"difficult\",\"review_date\":\"2026-08-06\"}" | jq -r '.id')

echo "Decision logged: $DECISION_ID"

# 2. Create entities for alternatives
MONGO_ID=$(./kb-cli add-entity \
    "Alternative: MongoDB" \
    "Considered MongoDB for flexible schema and horizontal scaling, but rejected due to consistency requirements and team expertise." \
    "{\"type\":\"alternative\",\"for_decision\":\"$DECISION_ID\",\"status\":\"rejected\",\"reason\":\"consistency_requirements\"}" | jq -r '.id')

./kb-cli add-link "$DECISION_ID" "$MONGO_ID" "considers"

MYSQL_ID=$(./kb-cli add-entity \
    "Alternative: MySQL" \
    "Considered MySQL as familiar option, but PostgreSQL offers more features for similar complexity." \
    "{\"type\":\"alternative\",\"for_decision\":\"$DECISION_ID\",\"status\":\"rejected\",\"reason\":\"feature_set\"}" | jq -r '.id')

./kb-cli add-link "$DECISION_ID" "$MYSQL_ID" "considers"

# 3. Document stakeholders
STAKEHOLDER_ID=$(./kb-cli add-entity \
    "Decision Stakeholders: $DECISION_TITLE" \
    "Lead: @architect\nReviewers: @tech-lead, @security-lead\nAffected Teams: Backend, DevOps, Data" \
    "{\"type\":\"stakeholders\",\"decision_id\":\"$DECISION_ID\",\"lead\":\"architect\",\"teams\":[\"backend\",\"devops\",\"data\"]}" | jq -r '.id')

./kb-cli add-link "$DECISION_ID" "$STAKEHOLDER_ID" "involves"

# 4. Create review task
./kb-cli add-task \
    "Review database decision at 50K users" \
    "Assess if PostgreSQL is still meeting needs or if architecture changes are needed" \
    "$DECISION_ID" \
    "{\"priority\":\"medium\",\"type\":\"review\",\"trigger\":\"50k_users\",\"due_date\":\"2026-08-06\"}"

echo "Decision captured with alternatives, stakeholders, and review task"
```

### Output

```
Decision logged: a1b2c3d4
Alternative considered: e5f6g7h8 (MongoDB - rejected)
Alternative considered: i9j0k1l2 (MySQL - rejected)
Stakeholders documented: m3n4o5p6
Review task created: Task #5
```

## Workflow 2: Decision Evolution Tracking

### Goal
Track how decisions evolve over time as context changes.

### Process

```bash
#!/bin/bash
# track_decision_evolution.sh

ORIGINAL_DECISION_ID="a1b2c3d4"  # PostgreSQL decision

# Context has changed: now at 80K users, experiencing performance issues
NEW_DECISION_CONTENT=$(cat <<'EOF'
## Status
Supersedes Previous Decision

## Context Change
Original decision: Use PostgreSQL for primary database (6 months ago)
Current situation:
- Reached 80K users (ahead of projections)
- Read traffic exceeds single-server capacity
- Write traffic still manageable
- PostgreSQL becoming a bottleneck for read-heavy queries

## Decision
Implement read replicas and caching layer while keeping PostgreSQL as primary.

## Rationale
- Don't need full migration to distributed database yet
- Read replicas will handle 80% of queries
- Redis cache will offload common queries
- Preserves investment in PostgreSQL infrastructure
- Maintains ACID guarantees for writes
- Lower risk and cost than full migration

## Changes from Original
- Added: 2 read replicas for scaling reads
- Added: Redis cache layer for frequently accessed data
- Modified: Application uses read replicas for reports
- Kept: PostgreSQL for all writes and critical reads

## Alternative Considered
- **Full Migration to Distributed Database**: Too expensive and risky now. Revisit at 500K users.

## Implementation
- Set up 2 PostgreSQL read replicas
- Deploy Redis cluster
- Modify application to route reads appropriately
- Monitor to determine if additional replicas needed
EOF
)

# Create new decision entity
NEW_DECISION_ID=$(./kb-cli add-entity \
    "Database Architecture: Add Read Replicas" \
    "$NEW_DECISION_CONTENT" \
    "{\"type\":\"decision\",\"status\":\"accepted\",\"category\":\"architecture\",\"decision_date\":\"$(date -u +%Y-%m-%d)\",\"impact\":\"high\",\"supersedes\":\"$ORIGINAL_DECISION_ID\"}" | jq -r '.id')

# Link to original decision
./kb-cli add-link "$NEW_DECISION_ID" "$ORIGINAL_DECISION_ID" "builds_on"

# Update original decision status
ORIGINAL_CONTENT=$(./kb-cli get-entity "$ORIGINAL_DECISION_ID" | jq -r '.content')
./kb-cli update-entity "$ORIGINAL_DECISION_ID" \
    "Use PostgreSQL for Primary Database (Evolved)" \
    "$ORIGINAL_CONTENT\n\n## Evolution\nThis decision evolved on $(date -u +%Y-%m-%d). See: $NEW_DECISION_ID" \
    "{\"type\":\"decision\",\"status\":\"evolved\",\"evolved_to\":\"$NEW_DECISION_ID\"}"

echo "Decision evolution tracked: $ORIGINAL_DECISION_ID → $NEW_DECISION_ID"
```

## Workflow 3: Decision Impact Analysis

### Goal
Track consequences of decisions over time to inform future choices.

### Process

```bash
#!/bin/bash
# track_decision_consequences.sh

DECISION_ID="a1b2c3d4"  # PostgreSQL decision
MONTHS_LATER=6

# Document realized consequences after 6 months
CONSEQUENCE_CONTENT=$(cat <<'EOF'
## 6-Month Review of PostgreSQL Decision

### Predicted Consequences (from original decision)
✅ Strong data integrity - **REALIZED** (zero data corruption incidents)
✅ Complex queries efficient - **REALIZED** (reporting queries performant)
✅ Leverage SQL knowledge - **REALIZED** (team productive immediately)
⚠️ Vertical scaling limits - **PARTIALLY REALIZED** (hit limits earlier than expected)
✅ Rich tooling ecosystem - **REALIZED** (excellent monitoring with pganalyze)

### Unexpected Consequences
➕ **Positive Surprise**: PostgreSQL's JSONB support eliminated need for separate document store
➕ **Positive Surprise**: Point-in-time recovery saved us twice during incidents
➖ **Negative Surprise**: Memory usage higher than expected with large JSONB columns
➖ **Negative Surprise**: Connection pool exhaustion under traffic spikes (mitigated with PgBouncer)

### Cost Analysis
- Infrastructure: $500/month (lower than projected $800/month)
- Engineering time: 2 person-weeks for optimization (lower than estimated)
- Training: Minimal (team already had SQL skills)

### Would We Decide the Same Way Again?
**YES** - Despite hitting scaling limits earlier than expected, the decision was sound. The alternatives would not have solved our problems better, and PostgreSQL's strengths outweighed the scaling challenges.

### Lessons Learned
1. Underestimated read traffic - future architectural decisions should plan for 3x growth
2. Connection pooling is critical - should be part of initial setup
3. JSONB feature was a hidden benefit - evaluate database features more thoroughly
4. Monitoring early is key - pganalyze caught issues before users noticed
EOF
)

CONSEQUENCE_ID=$(./kb-cli add-entity \
    "Consequences: PostgreSQL Decision (6-month review)" \
    "$CONSEQUENCE_CONTENT" \
    "{\"type\":\"consequence\",\"decision_id\":\"$DECISION_ID\",\"review_date\":\"$(date -u +%Y-%m-%d)\",\"months_after\":$MONTHS_LATER,\"overall_assessment\":\"positive\"}" | jq -r '.id')

./kb-cli add-link "$CONSEQUENCE_ID" "$DECISION_ID" "reviews"

# Update decision with review reference
DECISION_CONTENT=$(./kb-cli get-entity "$DECISION_ID" | jq -r '.content')
./kb-cli update-entity "$DECISION_ID" \
    "$(./kb-cli get-entity "$DECISION_ID" | jq -r '.title')" \
    "$DECISION_CONTENT\n\n## 6-Month Review\nSee consequence analysis: $CONSEQUENCE_ID" \
    "{\"type\":\"decision\",\"status\":\"accepted\",\"reviewed\":true,\"last_review\":\"$(date -u +%Y-%m-%d)\"}"

echo "Consequences documented and linked to decision"
```

## Workflow 4: Decision Query and Analysis

### Goal
Query the decision log for insights and patterns.

### Process

```bash
#!/bin/bash
# query_decisions.sh

echo "=== Decision Log Analysis ==="

# 1. Count decisions by category
echo "\n## Decisions by Category"
./kb-cli list-entities | jq -r '.[] | select((.metadata | fromjson).type == "decision") | (.metadata | fromjson).category' | sort | uniq -c

# 2. Find high-impact decisions
echo "\n## High-Impact Decisions"
./kb-cli list-entities | jq -r '.[] | select((.metadata | fromjson).type == "decision" and (.metadata | fromjson).impact == "high") | "\(.title) - \((.metadata | fromjson).decision_date)"'

# 3. Decisions needing review
echo "\n## Decisions Due for Review"
CURRENT_DATE=$(date -u +%Y-%m-%d)
./kb-cli list-entities | jq -r --arg date "$CURRENT_DATE" '.[] | select((.metadata | fromjson).type == "decision" and (.metadata | fromjson).review_date? and (.metadata | fromjson).review_date < $date) | "\(.title) - Review due: \((.metadata | fromjson).review_date)"'

# 4. Superseded decisions
echo "\n## Evolution Chain"
./kb-cli list-entities | jq -r '.[] | select((.metadata | fromjson).status == "evolved") | .title' | while read title; do
    echo "- $title"
    # Find what it evolved to
    ENTITY_ID=$(./kb-cli list-entities | jq -r --arg t "$title" '.[] | select(.title == $t) | .id')
    ./kb-cli get-links-from "$ENTITY_ID" | jq -r '.[] | select(.link_type == "builds_on") | "  └→ \(.to_title)"'
done

# 5. Most referenced decisions
echo "\n## Most Referenced Decisions"
./kb-cli list-entities | jq -r '.[] | select((.metadata | fromjson).type == "decision") | .id' | while read id; do
    COUNT=$(./kb-cli get-links-to "$id" | jq 'length')
    TITLE=$(./kb-cli get-entity "$id" | jq -r '.title')
    echo "$COUNT - $TITLE"
done | sort -rn | head -5

# 6. Decisions by reversibility
echo "\n## Irreversible Decisions (High Risk)"
./kb-cli list-entities | jq -r '.[] | select((.metadata | fromjson).type == "decision" and (.metadata | fromjson).reversibility == "irreversible") | "\(.title) - \((.metadata | fromjson).decision_date)"'
```

## Integration with Copilot-CLI

### Custom Agent Definition

Create `.github/agents/decision-log.md`:

```markdown
# Decision Log Agent

You are a technical decision documentation expert that captures institutional memory.

## Your Role

1. Capture technical decisions with full context
2. Document alternatives considered and why they were rejected
3. Track decision evolution as context changes
4. Record realized consequences over time
5. Maintain decision relationships and dependencies
6. Surface relevant decisions during new decision-making

## Decision Documentation Format

For each decision, capture:
- **Status**: Accepted, rejected, deprecated, superseded
- **Context**: Why is this decision being made? What constraints exist?
- **Decision**: What exactly are we deciding?
- **Rationale**: Why is this the best choice?
- **Alternatives**: What else was considered? Why not chosen?
- **Consequences**: Predicted positive/negative outcomes
- **Implementation**: How will this be implemented?
- **Review Criteria**: When/how should this be revisited?

## Metadata to Track

- Decision date and author
- Category (architecture, technology, process, security)
- Impact level (high, medium, low)
- Reversibility (reversible, difficult, irreversible)
- Stakeholders and affected teams
- Review date for reassessment

## Workflow

1. When team discusses a decision, propose documenting it
2. Capture full context including constraints and requirements
3. List all alternatives considered with pros/cons
4. Document why chosen option is best
5. Predict consequences (positive and negative)
6. Create review tasks for future reassessment
7. Link related decisions
8. Update decisions when context changes

## Success Criteria

- Every significant decision is documented
- New team members can understand historical context
- Decisions can be revisited when circumstances change
- Patterns in decision-making are visible
- Cost of poor decisions is reduced
```

### Python Example

```python
#!/usr/bin/env python3
# decision_logger.py

import json
import subprocess
from datetime import datetime, timedelta

class DecisionLogger:
    def __init__(self):
        self.kb_cli = "./kb-cli"
    
    def log_decision(self, title, context, decision, rationale, alternatives,
                    consequences, category="architecture", impact="medium",
                    reversibility="difficult", review_months=6):
        """Log a comprehensive decision with all context"""
        
        # Build decision content
        content = f"""## Status
Accepted

## Context
{context}

## Decision
{decision}

## Rationale
{rationale}

## Alternatives Considered
{alternatives}

## Consequences
{consequences}

## Review
This decision should be reviewed in {review_months} months.
"""
        
        # Calculate review date
        review_date = (datetime.now() + timedelta(days=30*review_months)).strftime("%Y-%m-%d")
        
        # Create decision entity
        metadata = {
            "type": "decision",
            "status": "accepted",
            "category": category,
            "decision_date": datetime.now().strftime("%Y-%m-%d"),
            "impact": impact,
            "reversibility": reversibility,
            "review_date": review_date
        }
        
        result = subprocess.run(
            [self.kb_cli, "add-entity", title, content, json.dumps(metadata)],
            capture_output=True,
            text=True
        )
        
        decision_id = json.loads(result.stdout)["id"]
        print(f"Decision logged: {decision_id}")
        
        # Create review task
        subprocess.run([
            self.kb_cli, "add-task",
            f"Review: {title}",
            f"Reassess this decision after {review_months} months",
            decision_id,
            json.dumps({"priority": "medium", "type": "review"})
        ])
        
        return decision_id
    
    def update_consequences(self, decision_id, consequences_text, assessment="positive"):
        """Update decision with realized consequences"""
        
        consequence_content = f"""## Realized Consequences
{consequences_text}

## Assessment
Overall assessment: {assessment}
Review date: {datetime.now().strftime("%Y-%m-%d")}
"""
        
        metadata = {
            "type": "consequence",
            "decision_id": decision_id,
            "review_date": datetime.now().strftime("%Y-%m-%d"),
            "assessment": assessment
        }
        
        result = subprocess.run(
            [self.kb_cli, "add-entity",
             f"Consequences Review",
             consequence_content,
             json.dumps(metadata)],
            capture_output=True,
            text=True
        )
        
        consequence_id = json.loads(result.stdout)["id"]
        
        # Link to decision
        subprocess.run([
            self.kb_cli, "add-link",
            consequence_id, decision_id, "reviews"
        ])
        
        return consequence_id

# Usage example
if __name__ == "__main__":
    logger = DecisionLogger()
    
    decision_id = logger.log_decision(
        title="Use React for Frontend",
        context="Need to choose frontend framework for new web app. Team has varied experience.",
        decision="We will use React for the frontend framework.",
        rationale="Large ecosystem, team has some experience, good hiring market, component model fits our needs.",
        alternatives="Vue (smaller ecosystem), Angular (steeper learning curve), Svelte (less mature)",
        consequences="Positive: Fast development, large community. Negative: Bundle size concerns, frequent breaking changes.",
        category="technology",
        impact="high",
        reversibility="difficult"
    )
    
    print(f"✓ Decision logged: {decision_id}")
```

## Best Practices

1. **Document Early**: Capture decisions when context is fresh
2. **Be Honest**: Include real alternatives and trade-offs, not justifications
3. **Track Evolution**: Link new decisions to old ones they build on or supersede
4. **Review Regularly**: Set review dates and actually review them
5. **Keep it Simple**: Use consistent format, but don't let process slow decisions
6. **Include Dissent**: Document opposing viewpoints for completeness
7. **Link to Code**: Reference PRs, commits, or files that implement decisions
8. **Update Consequences**: Come back and document what actually happened
9. **Learn from History**: Review old decisions before making similar new ones
10. **Make it Searchable**: Use consistent terminology and tags

## Why This Agent Matters

Without decision logs, organizations repeatedly:
- Debate the same decisions
- Reverse good decisions without understanding original constraints
- Make incompatible choices across teams
- Lose institutional knowledge when people leave
- Can't evaluate if circumstances have changed enough to warrant revisiting

With decision logs, teams:
- Build institutional memory that survives turnover
- Make better decisions by learning from past choices
- Onboard new members faster with historical context
- Revisit decisions systematically when context changes
- Avoid "decision thrashing" from incomplete information

This is one of the most underrated practices in software engineering. The Decision Log Agent makes it systematic and sustainable.
