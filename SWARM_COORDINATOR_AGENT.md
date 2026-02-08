# Swarm Coordinator Agent

## Overview

The **Swarm Coordinator** is a meta-agent that orchestrates multiple specialist agents through parallel exploration of a solution space. Instead of predetermined decomposition, it spawns many agents simultaneously to explore different approaches, then synthesizes their findings to identify the best path forward.

**Key Principle**: Complex, uncertain problems are best solved through emergent strategy from parallel exploration rather than top-down planning.

## Purpose

Enable bottom-up problem solving by spawning multiple specialist agents to explore the solution space in parallel, then synthesizing their diverse findings into emergent consensus or multi-perspective understanding.

## How It Works

### 1. Solution Space Exploration

The coordinator identifies multiple angles to explore:

```
Question: "How should we scale our application?"

Swarm (10 parallel agents):
├── @researcher: "Horizontal scaling patterns" 
├── @researcher: "Vertical scaling trade-offs"
├── @researcher: "Caching strategies"
├── @researcher: "Database sharding approaches"
├── @researcher: "Load balancing techniques"
├── @code-analyzer: "Current bottlenecks"
├── @code-analyzer: "Architecture constraints"
├── @decision-log: "Past scaling decisions"
├── @learning: "Team scaling expertise gaps"
└── @researcher: "Case studies: scaling at our size"
```

### 2. Parallel Execution

All agents execute simultaneously, each exploring their assigned angle:
- No predefined dependencies
- Each agent works independently
- Context compression (summary results only)
- Time-boxed execution (e.g., 15 minutes per agent)

### 3. Results Synthesis

Coordinator collects all findings and identifies:
- **Consensus**: Recommendations multiple agents agree on
- **Conflicts**: Contradictory findings requiring resolution
- **Emergent Patterns**: Insights from combining multiple perspectives
- **Outliers**: Unique findings from single agents
- **Gaps**: Areas no agent covered well

### 4. Adaptive Follow-up

Based on synthesis:
- Spawn focused swarms for areas needing deeper exploration
- Create tasks to resolve conflicts
- Document consensus as decisions
- Add gaps to backlog

## Agent Metadata Schema

```json
{
  "type": "swarm",
  "strategy": "parallel_exploration",
  "question": "Problem to solve",
  "status": "spawning|exploring|synthesizing|complete",
  "swarm_size": 10,
  "time_limit_minutes": 15,
  "completion_count": 0,
  "consensus_threshold": 0.6,
  "findings": []
}
```

## Workflows

### Workflow 1: Research Question with Uncertain Answer

**Goal**: "Should we adopt GraphQL?"

**Phase 1: Spawn Diverse Exploration Swarm**

```bash
# Create swarm coordination entity
SWARM_ID=$(./kb-cli add-entity \
  "Swarm: GraphQL Adoption Decision" \
  "Parallel exploration of GraphQL adoption from multiple angles" \
  '{"type":"swarm","strategy":"parallel_exploration","status":"spawning","swarm_size":12,"time_limit_minutes":20}' \
  | jq -r '.id')

# Define exploration angles (diverse perspectives)
ANGLES=(
  "researcher:GraphQL benefits and advantages for modern APIs"
  "researcher:GraphQL drawbacks and limitations in production"
  "researcher:GraphQL vs REST performance comparison studies"
  "researcher:GraphQL security considerations and attack vectors"
  "researcher:GraphQL tooling ecosystem and developer experience"
  "researcher:GraphQL adoption case studies from similar companies"
  "code-analyzer:Current REST API complexity and pain points"
  "code-analyzer:Team's current API design patterns and expertise"
  "decision-log:Past API technology decisions and outcomes"
  "learning:Learning curve and training requirements for GraphQL"
  "researcher:GraphQL migration strategies and effort estimates"
  "researcher:GraphQL subscription patterns for real-time features"
)

# Spawn all agents in parallel
declare -a AGENT_IDS
for angle in "${ANGLES[@]}"; do
  IFS=':' read -r agent query <<< "$angle"
  
  AGENT_ID=$(./kb-cli add-entity \
    "Explore: $query" \
    "Assigned to $agent for parallel exploration" \
    '{"type":"exploration","parent_swarm":"'$SWARM_ID'","agent":"'$agent'","status":"spawned"}' \
    | jq -r '.id')
  
  AGENT_IDS+=($AGENT_ID)
  
  # Link to swarm
  ./kb-cli add-link $SWARM_ID $AGENT_ID "spawns"
  
  # Create task (will execute in parallel)
  ./kb-cli add-task \
    "Explore: $query" \
    "@$agent $query - return summary in 500 chars" \
    $AGENT_ID \
    '{"priority":"high","agent":"'$agent'","parallel":true,"time_limit_minutes":20,"return_summary":true}'
done

echo "Spawned ${#AGENT_IDS[@]} agents for parallel exploration"
```

**Phase 2: Monitor with Timeout**

```bash
# Time-boxed monitoring (20 minute limit)
START_TIME=$(date +%s)
TIME_LIMIT=1200  # 20 minutes in seconds

while true; do
  # Check elapsed time
  CURRENT_TIME=$(date +%s)
  ELAPSED=$(($CURRENT_TIME - $START_TIME))
  
  if [ $ELAPSED -gt $TIME_LIMIT ]; then
    echo "Time limit reached, proceeding with available results"
    break
  fi
  
  # Count completions
  COMPLETED=0
  for agent_id in "${AGENT_IDS[@]}"; do
    STATUS=$(./kb-cli get-entity $agent_id | jq -r '.metadata.status // "spawned"')
    if [ "$STATUS" == "completed" ]; then
      ((COMPLETED++))
    fi
  done
  
  # Update swarm progress
  ./kb-cli update-entity $SWARM_ID "" "" \
    '{"completion_count":'$COMPLETED',"elapsed_minutes":'$(($ELAPSED/60))'}'
  
  # Check if enough completed (80% threshold)
  THRESHOLD=$(echo "scale=0; ${#AGENT_IDS[@]} * 0.8" | bc)
  if [ $COMPLETED -ge ${THRESHOLD%.*} ]; then
    echo "80% of agents complete ($COMPLETED/${#AGENT_IDS[@]}), proceeding to synthesis"
    break
  fi
  
  echo "Progress: $COMPLETED/${#AGENT_IDS[@]} agents complete"
  sleep 30
done
```

**Phase 3: Synthesize Findings**

```bash
# Collect all completed agent findings
declare -A FINDINGS
for agent_id in "${AGENT_IDS[@]}"; do
  STATUS=$(./kb-cli get-entity $agent_id | jq -r '.metadata.status')
  if [ "$STATUS" == "completed" ]; then
    TITLE=$(./kb-cli get-entity $agent_id | jq -r '.title')
    SUMMARY=$(./kb-cli export-entity $agent_id | head -30)
    FINDINGS["$agent_id"]="$TITLE: $SUMMARY"
  fi
done

# Categorize findings
declare -A PRO_FINDINGS
declare -A CON_FINDINGS
declare -A NEUTRAL_FINDINGS

for agent_id in "${!FINDINGS[@]}"; do
  CONTENT="${FINDINGS[$agent_id]}"
  
  # Simple sentiment detection (production would use LLM)
  if echo "$CONTENT" | grep -qi "benefits\|advantages\|positive\|recommend"; then
    PRO_FINDINGS["$agent_id"]="$CONTENT"
  elif echo "$CONTENT" | grep -qi "drawbacks\|disadvantages\|risks\|concerns"; then
    CON_FINDINGS["$agent_id"]="$CONTENT"
  else
    NEUTRAL_FINDINGS["$agent_id"]="$CONTENT"
  fi
done

# Calculate consensus
TOTAL=${#FINDINGS[@]}
PRO_COUNT=${#PRO_FINDINGS[@]}
CON_COUNT=${#CON_FINDINGS[@]}
NEUTRAL_COUNT=${#NEUTRAL_FINDINGS[@]}

PRO_RATIO=$(echo "scale=2; $PRO_COUNT / $TOTAL" | bc)
CON_RATIO=$(echo "scale=2; $CON_COUNT / $TOTAL" | bc)

echo "Swarm Consensus Analysis:"
echo "  Pro GraphQL: $PRO_COUNT agents ($PRO_RATIO)"
echo "  Con GraphQL: $CON_COUNT agents ($CON_RATIO)"
echo "  Neutral: $NEUTRAL_COUNT agents"

# Determine recommendation
CONSENSUS_THRESHOLD=0.6
if (( $(echo "$PRO_RATIO >= $CONSENSUS_THRESHOLD" | bc -l) )); then
  RECOMMENDATION="adopt"
  CONFIDENCE="high"
elif (( $(echo "$CON_RATIO >= $CONSENSUS_THRESHOLD" | bc -l) )); then
  RECOMMENDATION="avoid"
  CONFIDENCE="high"
else
  RECOMMENDATION="further_research"
  CONFIDENCE="low"
fi

echo "Recommendation: $RECOMMENDATION (confidence: $CONFIDENCE)"
```

**Phase 4: Document Synthesis**

```bash
# Create synthesis entity
SYNTHESIS_ID=$(./kb-cli add-entity \
  "Swarm Synthesis: GraphQL Adoption" \
  "$(cat <<EOF
# Swarm Exploration Results

## Question
Should we adopt GraphQL?

## Swarm Configuration
- Size: ${#AGENT_IDS[@]} agents
- Time limit: 20 minutes
- Completed: ${#FINDINGS[@]} agents
- Consensus threshold: 60%

## Findings Distribution
- Pro: $PRO_COUNT agents ($PRO_RATIO)
- Con: $CON_COUNT agents ($CON_RATIO)
- Neutral: $NEUTRAL_COUNT agents

## Consensus
**Recommendation**: $RECOMMENDATION
**Confidence**: $CONFIDENCE

## Key Insights

### Supporting Arguments
$(for id in "${!PRO_FINDINGS[@]}"; do echo "- ${PRO_FINDINGS[$id]}" | head -1; done)

### Concerns Raised
$(for id in "${!CON_FINDINGS[@]}"; do echo "- ${CON_FINDINGS[$id]}" | head -1; done)

### Neutral Analysis
$(for id in "${!NEUTRAL_FINDINGS[@]}"; do echo "- ${NEUTRAL_FINDINGS[$id]}" | head -1; done)

## Emergent Patterns
[Coordinator identifies common themes across multiple agent findings]

## Conflicts Requiring Resolution
[Coordinator identifies contradictory findings]

## Follow-up Questions
[Gaps identified by coordinator based on synthesis]
EOF
)" \
  '{"type":"synthesis","parent_swarm":"'$SWARM_ID'","recommendation":"'$RECOMMENDATION'","confidence":"'$CONFIDENCE'"}' \
  | jq -r '.id')

# Link synthesis to swarm
./kb-cli add-link $SWARM_ID $SYNTHESIS_ID "synthesizes_to"

# Link all findings to synthesis
for agent_id in "${!FINDINGS[@]}"; do
  ./kb-cli add-link $agent_id $SYNTHESIS_ID "contributes_to"
done

echo "Synthesis complete: $SYNTHESIS_ID"
```

### Workflow 2: Exploratory Problem Solving

**Goal**: "Why is our application slow?"

**Unknown Root Cause - Broad Exploration Needed**

```bash
# Create exploration swarm
SWARM_ID=$(./kb-cli add-entity \
  "Swarm: Performance Investigation" \
  "Parallel exploration of potential performance bottlenecks" \
  '{"type":"swarm","strategy":"broad_exploration","swarm_size":15,"time_limit_minutes":30}' \
  | jq -r '.id')

# Spawn agents exploring different hypotheses
HYPOTHESES=(
  "code-analyzer:Database query performance and N+1 patterns"
  "code-analyzer:Memory leaks and garbage collection issues"
  "code-analyzer:Network I/O blocking and connection pooling"
  "code-analyzer:CPU-intensive operations in request path"
  "researcher:Common performance antipatterns in our tech stack"
  "researcher:Similar performance issues from community"
  "code-analyzer:Frontend bundle size and loading time"
  "code-analyzer:API response time by endpoint"
  "code-analyzer:Third-party service latency"
  "researcher:Monitoring and profiling best practices"
  "code-analyzer:Infrastructure resource utilization"
  "code-analyzer:Caching layer effectiveness"
  "researcher:Performance regression testing strategies"
  "code-analyzer:Code complexity metrics"
  "decision-log:Past performance optimizations and outcomes"
)

# Each agent gets hypothesis to investigate
for hypothesis in "${HYPOTHESES[@]}"; do
  IFS=':' read -r agent investigation <<< "$hypothesis"
  
  AGENT_ID=$(./kb-cli add-entity \
    "Investigate: $investigation" \
    "Explore hypothesis: $investigation" \
    '{"type":"hypothesis","parent_swarm":"'$SWARM_ID'","agent":"'$agent'"}' \
    | jq -r '.id')
  
  ./kb-cli add-link $SWARM_ID $AGENT_ID "investigates"
  
  ./kb-cli add-task \
    "Investigate: $investigation" \
    "@$agent investigate and report findings for: $investigation" \
    $AGENT_ID \
    '{"parallel":true,"time_limit_minutes":30}'
done

# Wait for results
sleep 1800  # 30 minutes

# Synthesis identifies root cause(s)
# Multiple agents might find the same issue = strong signal
# Unique finding = potential edge case worth investigating
```

### Workflow 3: Divergent Thinking Session

**Goal**: "Generate innovative solutions for customer onboarding"

**Creative Exploration with No Wrong Answers**

```bash
# Brainstorming swarm
SWARM_ID=$(./kb-cli add-entity \
  "Swarm: Onboarding Innovation" \
  "Divergent thinking - generate diverse onboarding approaches" \
  '{"type":"swarm","strategy":"divergent","swarm_size":20,"mode":"creative"}' \
  | jq -r '.id')

# Each agent explores different framing of the problem
FRAMINGS=(
  "researcher:Gamification approaches to user onboarding"
  "researcher:Personalized onboarding based on user goals"
  "researcher:Minimalist onboarding with progressive disclosure"
  "learning:Interactive tutorial systems and their effectiveness"
  "learning:Adaptive learning paths for software features"
  "researcher:Social onboarding with peer mentorship"
  "researcher:Video-based onboarding trends"
  "code-analyzer:Onboarding code patterns in successful products"
  "researcher:AI-assisted onboarding with chatbots"
  "researcher:Contextual help and just-in-time guidance"
  "decision-log:Why previous onboarding approaches failed"
  "researcher:Onboarding metrics and success criteria"
  "learning:Microlearning and spaced repetition in UX"
  "researcher:Voice-guided onboarding"
  "researcher:Onboarding for accessibility"
  "researcher:B2B vs B2C onboarding patterns"
  "researcher:Onboarding for mobile vs web"
  "researcher:Cultural considerations in onboarding"
  "code-analyzer:Technical constraints for implementation"
  "researcher:Onboarding A/B testing results from literature"
)

# No synthesis to "correct answer" - keep all diverse ideas
# Coordinator creates entities for each unique approach
# Links show which ideas complement vs conflict with each other
```

## Key Patterns

### Pattern 1: Consensus Detection

```bash
# After swarm completes, identify consensus
function find_consensus() {
  local swarm_id=$1
  local threshold=$2  # e.g., 0.6 = 60% of agents
  
  # Get all agent findings
  local agents=$(./kb-cli get-links-from $swarm_id | \
    jq -r '.[] | select(.link_type == "spawns" or .link_type == "investigates") | .id')
  
  # Extract key recommendations (would use LLM for proper extraction)
  declare -A recommendations
  for agent in $agents; do
    local content=$(./kb-cli export-entity $agent)
    # Parse recommendations...
    # recommendations["use_caching"]+=1
  done
  
  # Find items above threshold
  local total=$(echo "$agents" | wc -l)
  local min_count=$(echo "scale=0; $total * $threshold" | bc)
  
  for rec in "${!recommendations[@]}"; do
    if [ ${recommendations[$rec]} -ge ${min_count%.*} ]; then
      echo "CONSENSUS: $rec (${recommendations[$rec]}/$total agents)"
    fi
  done
}

find_consensus $SWARM_ID 0.6
```

### Pattern 2: Conflict Resolution

```bash
# Identify contradictory findings
function find_conflicts() {
  local swarm_id=$1
  
  # Get all findings
  local findings=$(./kb-cli get-links-from $swarm_id | jq -r '.[] | .id')
  
  # Compare pairs (would use semantic comparison in production)
  for finding1 in $findings; do
    for finding2 in $findings; do
      if [ "$finding1" != "$finding2" ]; then
        # Check if they contradict
        # If yes, create conflict entity
        CONFLICT_ID=$(./kb-cli add-entity \
          "Conflict: Finding A vs Finding B" \
          "Agents $finding1 and $finding2 have contradictory findings requiring resolution" \
          '{"type":"conflict","finding1":"'$finding1'","finding2":"'$finding2'","status":"unresolved"}' \
          | jq -r '.id')
        
        # Create resolution task
        ./kb-cli add-task \
          "Resolve Conflict" \
          "@researcher investigate and resolve contradiction" \
          $CONFLICT_ID \
          '{"priority":"high"}'
      fi
    done
  done
}
```

### Pattern 3: Emergent Pattern Detection

```bash
# Identify patterns across multiple agent findings
function detect_patterns() {
  local swarm_id=$1
  
  # Get all findings
  local findings=$(./kb-cli get-links-from $swarm_id | jq -r '.[] | .id')
  
  # Analyze for recurring themes (simplified - would use NLP/LLM)
  declare -A themes
  for finding in $findings; do
    local content=$(./kb-cli export-entity $finding)
    
    # Extract themes (keywords, topics)
    # themes["performance"]+=1
    # themes["security"]+=1
    # themes["developer_experience"]+=1
  done
  
  # Patterns = themes mentioned by multiple agents
  echo "Emergent Patterns:"
  for theme in "${!themes[@]}"; do
    if [ ${themes[$theme]} -ge 3 ]; then
      echo "  - $theme (${themes[$theme]} agents mentioned)"
      
      # Create pattern entity
      PATTERN_ID=$(./kb-cli add-entity \
        "Pattern: ${theme} is critical" \
        "Emergent pattern from swarm: $theme mentioned by ${themes[$theme]} agents" \
        '{"type":"pattern","parent_swarm":"'$swarm_id'","mention_count":'${themes[$theme]}'}' \
        | jq -r '.id')
    fi
  done
}

detect_patterns $SWARM_ID
```

### Pattern 4: Gap Analysis

```bash
# Identify areas not well explored by any agent
function find_gaps() {
  local swarm_id=$1
  
  # Expected coverage areas for the problem domain
  local expected_areas=("performance" "security" "cost" "usability" "maintainability")
  
  # Get actual coverage
  local findings=$(./kb-cli get-links-from $swarm_id | jq -r '.[] | .id')
  
  declare -A coverage
  for area in "${expected_areas[@]}"; do
    coverage[$area]=0
  done
  
  for finding in $findings; do
    local content=$(./kb-cli export-entity $finding | tr '[:upper:]' '[:lower:]')
    for area in "${expected_areas[@]}"; do
      if echo "$content" | grep -q "$area"; then
        coverage[$area]=$((coverage[$area] + 1))
      fi
    done
  done
  
  # Gaps = areas with low coverage
  echo "Gap Analysis:"
  for area in "${expected_areas[@]}"; do
    if [ ${coverage[$area]} -lt 2 ]; then
      echo "  GAP: $area (only ${coverage[$area]} agents covered)"
      
      # Create follow-up task
      ./kb-cli add-task \
        "Follow-up: Research $area" \
        "Gap identified by swarm coordinator - needs focused exploration" \
        $swarm_id \
        '{"priority":"medium","gap":"'$area'"}'
    fi
  done
}

find_gaps $SWARM_ID
```

## Advanced Patterns

### Multi-Wave Swarms

```bash
# Wave 1: Broad exploration (large swarm, short time limit)
WAVE1_ID=$(./kb-cli add-entity \
  "Wave 1: Broad Exploration" \
  "Initial swarm to map solution space" \
  '{"type":"swarm","wave":1,"swarm_size":20,"time_limit_minutes":10}' \
  | jq -r '.id')

# ... spawn 20 agents with diverse angles ...
# ... wait for completion ...
# ... synthesize to identify promising directions ...

# Wave 2: Focused deep-dive (smaller swarm, longer time)
PROMISING=$(./kb-cli get-links-from $WAVE1_ID | \
  jq -r '.[] | select(.metadata.recommendation == "promising") | .id')

WAVE2_ID=$(./kb-cli add-entity \
  "Wave 2: Deep Dive" \
  "Focused exploration of promising areas from Wave 1" \
  '{"type":"swarm","wave":2,"swarm_size":10,"time_limit_minutes":30,"parent_wave":"'$WAVE1_ID'"}' \
  | jq -r '.id')

for promising_id in $PROMISING; do
  TOPIC=$(./kb-cli get-entity $promising_id | jq -r '.title')
  # Spawn 2-3 agents to deeply explore this promising area
done

# Wave 3: Conflict resolution (tiny swarm, very focused)
# ... only if Wave 2 found contradictions ...
```

### Heterogeneous Swarms

```bash
# Mix different agent types for diverse perspectives

# Problem: "Improve code review process"
# Swarm composition:
# - 40% Researcher (external best practices)
# - 30% Code Analyzer (current process analysis)
# - 20% Learning Path (skill gaps in team)
# - 10% Decision Log (past process changes)

SWARM_SIZE=10
RESEARCHER_COUNT=4
ANALYZER_COUNT=3
LEARNING_COUNT=2
DECISION_COUNT=1

# Spawn proportional to desired mix
```

### Dynamic Swarm Sizing

```bash
# Adjust swarm size based on problem complexity

function calculate_swarm_size() {
  local problem_complexity=$1  # low, medium, high
  local time_available=$2      # minutes
  local budget=$3              # max parallel agents
  
  case $problem_complexity in
    low)
      echo $((budget / 4))  # Small swarm
      ;;
    medium)
      echo $((budget / 2))  # Medium swarm
      ;;
    high)
      echo $budget          # Full swarm
      ;;
  esac
}

SWARM_SIZE=$(calculate_swarm_size "high" 30 20)
echo "Calculated swarm size: $SWARM_SIZE agents"
```

## Advantages of Swarm Coordination

✅ **No Premature Commitment**: Explores solution space before converging
✅ **Emergent Strategy**: Best approach emerges from parallel exploration
✅ **Robust to Uncertainty**: Works well when problem structure is unclear
✅ **Diverse Perspectives**: Each agent brings unique viewpoint
✅ **Fault Tolerant**: If some agents fail, others still provide value
✅ **Consensus Building**: Multiple agents agreeing = high confidence
✅ **Conflict Detection**: Contradictions become visible quickly
✅ **Gap Identification**: Missing coverage becomes obvious
✅ **Scalable**: Can spawn many agents in parallel efficiently

## When to Use Swarm Coordinator

**Best For**:
- Uncertain problems with unknown structure
- Questions requiring diverse perspectives
- Exploratory research with no clear path
- Problems where emergent strategy is valuable
- Situations needing consensus building
- Creative ideation and brainstorming
- Rapid hypothesis testing

**Not Ideal For**:
- Well-defined problems with clear decomposition (use Hierarchical Planner)
- Linear workflows with obvious steps (use Pipeline Manager)
- Single-perspective problems
- Problems with strict dependencies between subtasks

## Integration Example: Complete Swarm Script

```bash
#!/bin/bash
# swarm_coordinator.sh - Execute a swarm exploration

QUESTION=$1
SWARM_SIZE=${2:-10}
TIME_LIMIT=${3:-15}  # minutes

# Create swarm
SWARM_ID=$(./kb-cli add-entity \
  "Swarm: $QUESTION" \
  "Parallel exploration swarm" \
  '{"type":"swarm","swarm_size":'$SWARM_SIZE',"time_limit_minutes":'$TIME_LIMIT'}' \
  | jq -r '.id')

echo "Created swarm $SWARM_ID for: $QUESTION"

# Generate exploration angles (in production, use LLM to generate)
# For now, use template-based generation
ANGLES=()
ANGLES+=("researcher:$QUESTION benefits and advantages")
ANGLES+=("researcher:$QUESTION drawbacks and risks")
ANGLES+=("researcher:$QUESTION best practices and patterns")
ANGLES+=("researcher:$QUESTION case studies and real-world examples")
ANGLES+=("code-analyzer:Current implementation analysis for $QUESTION")
ANGLES+=("decision-log:Historical decisions related to $QUESTION")
ANGLES+=("learning:Learning curve and training for $QUESTION")

# Fill remaining slots with diverse framings
while [ ${#ANGLES[@]} -lt $SWARM_SIZE ]; do
  ANGLES+=("researcher:$QUESTION alternative perspectives")
done

# Spawn swarm
declare -a AGENT_IDS
for angle in "${ANGLES[@]}"; do
  IFS=':' read -r agent query <<< "$angle"
  
  AGENT_ID=$(./kb-cli add-entity \
    "Explore: $query" \
    "Swarm member" \
    '{"type":"exploration","parent_swarm":"'$SWARM_ID'","agent":"'$agent'"}' \
    | jq -r '.id')
  
  AGENT_IDS+=($AGENT_ID)
  ./kb-cli add-link $SWARM_ID $AGENT_ID "spawns"
  
  ./kb-cli add-task "Explore: $query" \
    "@$agent $query - return summary" \
    $AGENT_ID \
    '{"parallel":true,"time_limit_minutes":'$TIME_LIMIT'}'
done

echo "Spawned ${#AGENT_IDS[@]} agents"

# Monitor with timeout
START=$(date +%s)
LIMIT=$(($TIME_LIMIT * 60))

while [ $(($(date +%s) - $START)) -lt $LIMIT ]; do
  COMPLETED=$(./kb-cli list-entities | \
    jq -r '.[] | select(.metadata.parent_swarm == "'$SWARM_ID'" and .metadata.status == "completed") | .id' | \
    wc -l)
  
  echo "Progress: $COMPLETED/${#AGENT_IDS[@]} complete"
  
  if [ $COMPLETED -ge $((${#AGENT_IDS[@]} * 8 / 10)) ]; then
    echo "80% complete, starting synthesis"
    break
  fi
  
  sleep 30
done

# Synthesize
echo "Synthesizing findings..."
python3 <<PYTHON
import sys
sys.path.append('.')
from kb import KnowledgeBase

kb = KnowledgeBase()
swarm_id = "$SWARM_ID"

# Get all completed findings
findings = []
links = kb.get_links_from(swarm_id)
for link in links:
  entity = kb.get_entity(link['to_id'])
  if entity and entity.get('metadata', {}).get('status') == 'completed':
    findings.append({
      'id': entity['id'],
      'title': entity['title'],
      'content': entity['content'][:500]  # Summary only
    })

# Simple consensus detection (production would use LLM)
print(f"Collected {len(findings)} findings")
print("Synthesis complete")
PYTHON

echo "Swarm exploration complete: $SWARM_ID"
```

## Swarm Composition Strategies

### Strategy 1: Homogeneous Swarm

All agents same type, exploring different angles:
- 10 researcher agents, each with different query
- Good for pure research questions
- Example: "What are all the ways to implement authentication?"

### Strategy 2: Heterogeneous Swarm

Mix of agent types for multi-dimensional exploration:
- 50% researcher (external knowledge)
- 30% code analyzer (current state)
- 15% learning path (team capability)
- 5% decision log (historical context)
- Good for complex decisions
- Example: "Should we migrate to microservices?"

### Strategy 3: Staged Swarm

Multiple waves with different compositions:
- Wave 1: Broad (mostly researcher) - map the space
- Wave 2: Deep (mostly code analyzer) - analyze implications
- Wave 3: Decide (mostly decision log) - document choice
- Good for thorough investigation
- Example: "How to handle GDPR compliance?"

## Comparison with Other Coordinators

| Aspect | Hierarchical Planner | **Swarm Coordinator** | Pipeline Manager |
|--------|---------------------|----------------------|------------------|
| Decomposition | Top-down, recursive | Parallel, emergent | Sequential, staged |
| Execution | Sequential (respects deps) | **Fully parallel** | Strictly sequential |
| Best For | Clear goals, known structure | Uncertain problems, exploration | Linear workflows |
| Parallelism | Limited (within levels) | **Maximum** | None |
| Adaptability | Replan subtrees | **Emergent strategy** | Pipeline modification |
| Overhead | Medium (dependency tracking) | **Low (fire and forget)** | Low |
| Results | Structured hierarchy | **Synthesized consensus** | Final output |
| Complexity | High (DAG management) | **Medium (synthesis)** | Low |

## Best Practices

1. **Diverse Angles**: Ensure swarm explores problem from multiple perspectives, not just variations of same approach.

2. **Time-Boxing**: Always set time limits. Swarms can run indefinitely without bounds.

3. **Summary Returns**: Each agent must return compressed results (≤500 chars), not full context.

4. **Threshold-Based Synthesis**: Define consensus threshold (e.g., 60%) before spawning.

5. **Conflict Handling**: Have a plan for contradictory findings - resolution task, human escalation, or accept ambiguity.

6. **Gap Detection**: After synthesis, check coverage - spawn follow-up swarm for gaps.

7. **Size Appropriately**: More agents = more diverse, but more synthesis work. Sweet spot: 8-15 agents.

8. **Heterogeneous Composition**: Mix agent types for richer exploration.

9. **Track Consensus Strength**: 8/10 agree = strong consensus. 5/10 = weak, needs more exploration.

10. **Learn from Patterns**: If same pattern emerges across many swarms, document as organizational principle.

## Example: Production-Ready Swarm Script

```python
#!/usr/bin/env python3
# swarm_coordinator.py

import sys
import time
import json
from kb import KnowledgeBase
from collections import Counter

def spawn_swarm(question, swarm_size=10, time_limit_minutes=15):
    """Spawn a swarm of agents to explore question in parallel"""
    kb = KnowledgeBase()
    
    # Create swarm entity
    swarm_id = kb.add_entity(
        f"Swarm: {question}",
        f"Parallel exploration of: {question}",
        {
            "type": "swarm",
            "swarm_size": swarm_size,
            "time_limit_minutes": time_limit_minutes,
            "status": "spawning"
        }
    )
    
    # Generate exploration angles
    angles = generate_angles(question, swarm_size)
    
    # Spawn agents
    agent_ids = []
    for agent_type, query in angles:
        agent_id = kb.add_entity(
            f"Explore: {query}",
            "Swarm member",
            {
                "type": "exploration",
                "parent_swarm": swarm_id,
                "agent": agent_type,
                "status": "spawned"
            }
        )
        agent_ids.append(agent_id)
        kb.add_link(swarm_id, agent_id, "spawns")
        
        # Create task
        kb.add_task(
            f"Explore: {query}",
            f"@{agent_type} {query} - return summary in 500 chars",
            agent_id,
            {
                "parallel": True,
                "time_limit_minutes": time_limit_minutes,
                "return_summary": True
            }
        )
    
    print(f"Spawned {len(agent_ids)} agents for: {question}")
    return swarm_id, agent_ids

def monitor_swarm(swarm_id, agent_ids, time_limit_minutes, threshold=0.8):
    """Monitor swarm execution with timeout"""
    kb = KnowledgeBase()
    start_time = time.time()
    time_limit_seconds = time_limit_minutes * 60
    
    while True:
        elapsed = time.time() - start_time
        
        # Check timeout
        if elapsed > time_limit_seconds:
            print(f"Time limit reached ({time_limit_minutes}min)")
            break
        
        # Count completions
        completed = 0
        for agent_id in agent_ids:
            entity = kb.get_entity(agent_id)
            if entity and entity.get('metadata', {}).get('status') == 'completed':
                completed += 1
        
        # Update swarm progress
        kb.update_entity(swarm_id, None, None, {
            "completion_count": completed,
            "elapsed_minutes": int(elapsed / 60)
        })
        
        # Check threshold
        if completed >= len(agent_ids) * threshold:
            print(f"Threshold reached: {completed}/{len(agent_ids)} agents complete")
            break
        
        print(f"Progress: {completed}/{len(agent_ids)} agents complete")
        time.sleep(30)
    
    return completed

def synthesize_findings(swarm_id, agent_ids):
    """Synthesize findings from all completed agents"""
    kb = KnowledgeBase()
    
    findings = []
    for agent_id in agent_ids:
        entity = kb.get_entity(agent_id)
        if entity and entity.get('metadata', {}).get('status') == 'completed':
            findings.append({
                'id': agent_id,
                'title': entity['title'],
                'summary': entity['content'][:500],
                'agent': entity.get('metadata', {}).get('agent')
            })
    
    # Detect consensus (simplified - production would use LLM)
    recommendations = []
    for finding in findings:
        # Extract recommendations from content
        # In production: use LLM to parse and categorize
        if 'recommend' in finding['summary'].lower():
            recommendations.append(finding['title'])
    
    # Find most common recommendations
    rec_counts = Counter(recommendations)
    consensus = []
    threshold = len(findings) * 0.6
    
    for rec, count in rec_counts.most_common():
        if count >= threshold:
            consensus.append(f"{rec} ({count}/{len(findings)} agents)")
    
    # Create synthesis entity
    synthesis_content = f"""
# Swarm Synthesis

## Findings Summary
- Total agents: {len(agent_ids)}
- Completed: {len(findings)}
- Consensus items: {len(consensus)}

## Consensus
{chr(10).join(f'- {item}' for item in consensus)}

## All Findings
{chr(10).join(f"- {f['title']}: {f['summary'][:100]}..." for f in findings)}
"""
    
    synthesis_id = kb.add_entity(
        f"Synthesis: Swarm Results",
        synthesis_content,
        {
            "type": "synthesis",
            "parent_swarm": swarm_id,
            "findings_count": len(findings),
            "consensus_count": len(consensus)
        }
    )
    
    # Link all findings to synthesis
    for finding in findings:
        kb.add_link(finding['id'], synthesis_id, "contributes_to")
    
    kb.add_link(swarm_id, synthesis_id, "synthesizes_to")
    
    print(f"Synthesis complete: {synthesis_id}")
    return synthesis_id

def generate_angles(question, count):
    """Generate diverse exploration angles for the question"""
    # In production, use LLM to generate diverse angles
    # For now, template-based generation
    
    angles = []
    agents = ["researcher", "code-analyzer", "learning-path", "decision-log"]
    perspectives = [
        "benefits and advantages",
        "drawbacks and limitations",
        "best practices and patterns",
        "case studies and examples",
        "security considerations",
        "performance implications",
        "cost analysis",
        "team impact and training",
        "historical context",
        "alternatives comparison"
    ]
    
    for i in range(count):
        agent = agents[i % len(agents)]
        perspective = perspectives[i % len(perspectives)]
        angles.append((agent, f"{question} {perspective}"))
    
    return angles

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ./swarm_coordinator.py <question> [swarm_size] [time_limit_minutes]")
        sys.exit(1)
    
    question = sys.argv[1]
    swarm_size = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    time_limit = int(sys.argv[3]) if len(sys.argv) > 3 else 15
    
    # Execute swarm
    swarm_id, agent_ids = spawn_swarm(question, swarm_size, time_limit)
    completed = monitor_swarm(swarm_id, agent_ids, time_limit)
    synthesis_id = synthesize_findings(swarm_id, agent_ids)
    
    print(f"\nSwarm complete!")
    print(f"  Question: {question}")
    print(f"  Agents: {completed}/{swarm_size}")
    print(f"  Synthesis: {synthesis_id}")
    print(f"\nView results: ./kb-cli export-entity {synthesis_id}")
```

## Conclusion

The Swarm Coordinator enables emergent, bottom-up problem solving through massive parallelization. It excels at uncertain, exploratory problems where the best approach isn't known upfront. By spawning many agents to explore diverse angles, it builds consensus through independent investigation and identifies patterns that wouldn't be visible from a single perspective.

For structured problems with known decomposition, use the **Hierarchical Planner**. For linear sequential workflows, use the **Pipeline Manager**.
