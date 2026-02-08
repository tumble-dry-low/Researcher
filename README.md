# Researcher 🔬

An automatic knowledge base system for AI agents. Minimal code, maximum automation - agents just add information, the system manages everything else.

## Overview

This repository provides an **automated knowledge base** with:
- **Entities**: Research notes with automatic ID generation
- **Links**: Relationships managed automatically
- **Task Backlog**: Future work tracked automatically, tied to notes

Agents don't manually manage structure - they just call simple commands and the system handles storage, linking, and task tracking.

## Seven Agent Implementations

The knowledge base system supports multiple specialized agents:

### Specialist Agents (Task Execution)

1. **[Researcher Agent](COPILOT_CLI_GUIDE.md)**: Deep research with parallel perspectives, tree-based exploration, source citation
2. **[Code Analyzer Agent](CODE_ANALYZER_AGENT.md)**: Codebase analysis, architecture documentation, technical debt tracking, staleness detection
3. **[Learning Path Agent](LEARNING_PATH_AGENT.md)**: Personalized learning curricula, skill trees, knowledge gap analysis
4. **[Decision Log Agent](DECISION_LOG_AGENT.md)**: Technical decision tracking with rationale, alternatives, and evolution

### Meta-Agent Coordinators (Multi-Agent Orchestration)

5. **[Hierarchical Planner Agent](HIERARCHICAL_PLANNER_AGENT.md)**: Top-down recursive decomposition, manages complex goals through task hierarchies with dependency tracking
6. **[Swarm Coordinator Agent](SWARM_COORDINATOR_AGENT.md)**: Bottom-up parallel exploration, spawns many agents simultaneously to explore solution space and synthesize consensus
7. **[Pipeline Manager Agent](PIPELINE_MANAGER_AGENT.md)**: Sequential chaining through stages, each stage enriches and validates previous output

**How They Work Together**: Meta-agents coordinate specialist agents. For example, Hierarchical Planner decomposes "Build API" into research → analyze → decide → train, delegating each to specialist agents. Swarm Coordinator might spawn 10 Researcher agents in parallel to explore different angles. Pipeline Manager chains Researcher → Code Analyzer → Decision Log → Learning Path sequentially.

All agents share the same KB infrastructure (entities, links, tasks) with agent-specific workflows.

## Two Approaches

### 1. Automated Database (Recommended for MVP)

**Minimal Python implementation** - agents use CLI, system manages everything:

```bash
# Add entity (auto-generates ID)
./kb-cli add-entity "Research Question" "Content here" '{"type":"question"}'

# Link entities automatically
./kb-cli add-link abc123 def456 "child"

# Add task to backlog (tied to entity)
./kb-cli add-task "Follow-up research" "Details..." abc123

# Query tasks
./kb-cli get-tasks pending
```

**Database schema:**
- `entities` table: id, title, content, metadata, timestamps
- `links` table: from_id, to_id, link_type
- `tasks` table: title, description, status, entity_id, metadata

See `kb.py` and `kb-cli` for the ~300 line implementation.

### 2. Markdown Files (Documentation-only)

Instructions-based approach using markdown files with random IDs.

## Prerequisites

### For Database Approach
- Python 3.7+
- SQLite (built-in)

### For Markdown Approach  
- An AI agent with file read/write capabilities (e.g., Claude Desktop with filesystem MCP)
- Web search capability (built-in or via MCP server)

## Research Methodology

### Core Principles

1. **Everything is markdown**: All research stored as `.md` files with YAML frontmatter
2. **Wiki-style linking**: Use `[text](./filename.md)` to link between research nodes
3. **Hierarchical tree structure**: Research questions branch into sub-questions
4. **Source citation required**: All findings must cite sources - no sources = inadmissible
5. **Parallel exploration**: Research multiple perspectives/positions simultaneously

### File Naming Conventions

Use random identifiers for filenames. The wiki links tell the story, not the filenames.

```
knowledge-base/entries/
├── a1b2c3d4.md    # Any research entry
├── e5f6g7h8.md    # Another entry
├── i9j0k1l2.md    # Links between files show relationships
└── m3n4o5p6.md    # Descriptive titles in frontmatter, not filenames
```

**Suggested identifier format:** 8 random alphanumeric characters (e.g., `a1b2c3d4.md`)
**Alternative:** UUID, timestamp, or any unique identifier

The important part is the content and links, not the filename.

### Research Types

#### 1. Standard Research

Single topic, multiple queries, synthesized results.

**Frontmatter:**
```yaml
---
title: "Topic Name"
tags: [research, topic-area]
createdAt: "ISO-8601 timestamp"
depth: 3
sources: 15
---
```

**Structure:**
- Introduction/Summary
- Key Findings (numbered list)
- Sources (with links)
- Related Topics (wiki links to other research)

#### 2. Structured Research (Debate-Style)

Multiple perspectives researched in parallel (pro/con, multiple options).

**Frontmatter:**
```yaml
---
title: "Structured Research: Question"
tags: [structured-research, debate, analysis]
question: "Should we...?"
positionCount: 6
createdAt: "ISO-8601 timestamp"
---
```

**Structure:**
- Context/Question
- Summary
- Positions (one section per position)
  - Each position: stance (pro/con), strength (strong/moderate/weak), arguments with sources
- Inadmissible positions (those without sources) excluded

#### 3. Tree Research (Hierarchical)

Recursive question exploration with automatic branching and pruning.

**Index File** (e.g., `a1b2c3d4.md`):
```yaml
---
title: "Tree Research Index: Root Question"
tags: [tree-research, hierarchical, analysis, index]
totalNodes: 5
maxDepthReached: 2
conclusiveNodes: 1
openQuestionsCount: 3
createdAt: "ISO-8601 timestamp"
---
```

**Node File** (e.g., `e5f6g7h8.md`):
```yaml
---
title: "Node Question"
tags: [tree-research-node, depth-N, status]
depth: N
status: completed|max_depth|conclusive
conclusive: false
parentChain: ["Parent Q1", "Parent Q2"]
createdAt: "ISO-8601 timestamp"
---
```

**Each Node Contains:**
- Previous Questions and Branches (parent chain for context)
- Metadata (depth, status, conclusive flag)
- Research results (all positions with sources)
- Wiki links to child nodes (if any)
- Open questions (at max depth)

### Tree Research Algorithm

1. **Start at root**: Research initial question with all positions in parallel
2. **Evaluate results**:
   - If conclusive (1 strong position, others weak) → mark correct, don't branch
   - If non-conclusive → generate follow-up questions from moderate findings
3. **Branch recursively**: Create child nodes for each follow-up question
4. **Respect max depth**: At max depth, list open questions instead of branching
5. **Save bottom-up**: Create leaf nodes first, then parents (so wiki links work)
6. **Full context**: Each child node receives complete parent question chain

### Branch Pruning Logic

A node is **conclusive** when:
- One position is "strong" (5+ sources, 5+ arguments)
- All other positions are "weak" (< 3 sources or < 3 arguments)

When conclusive:
- Mark the correct position
- Don't create child branches
- Other alternatives "merit no further investigation"

### Position Strength Assessment

**Strong**: 5+ sources AND 5+ arguments
**Moderate**: 3-4 sources AND 3-4 arguments  
**Weak**: < 3 sources OR < 3 arguments

### Wiki Linking Best Practices

1. **Link between related research**: `[Related Topic](./a1b2c3d4.md)`
2. **Parent to children**: `[Follow-up Question](./i9j0k1l2.md)`
3. **Index to nodes**: Tree index links to all nodes for navigation
4. **Bidirectional**: When linking A→B, also add B→A
5. **Descriptive link text**: Use meaningful text since filenames are random

### Query Generation by Stance

**Pro stance**: Use "benefits", "advantages", "why [option]", "evidence for"
**Con stance**: Use "drawbacks", "disadvantages", "problems with", "risks", "criticism"
**Analysis**: Use "analysis", "comparison", "evaluation", "pros and cons"

## Usage Examples

### Specialist Agents

**Researcher Agent**:
```bash
@researcher research "GraphQL best practices"
# → Parallel queries, source citations, saved to KB
```

**Code Analyzer Agent**:
```bash
@code-analyzer analyze codebase and identify technical debt
# → Components mapped, debt tracked, staleness detection enabled
```

**Learning Path Agent**:
```bash
@learning create curriculum for "Advanced TypeScript"
# → Skill tree with prerequisites, resources, milestones
```

**Decision Log Agent**:
```bash
@decision-log document "Switch to GraphQL" decision with alternatives
# → ADR format, rationale captured, review scheduled
```

### Meta-Agent Coordinators

**Hierarchical Planner** (top-down decomposition):
```bash
# Goal: "Build GraphQL API"
# Planner decomposes into:
#   Research (→ Researcher)
#   Analysis (→ Code Analyzer)
#   Decision (→ Decision Log)
#   Training (→ Learning Path)
# Each executes when dependencies complete
```

**Swarm Coordinator** (parallel exploration):
```bash
# Question: "How to scale our app?"
# Spawns 10 agents simultaneously:
#   - 6 Researchers (different angles)
#   - 2 Code Analyzers (current bottlenecks)
#   - 1 Decision Log (past decisions)
#   - 1 Learning Path (team capabilities)
# Synthesizes consensus from parallel findings
```

**Pipeline Manager** (sequential chaining):
```bash
# Pipeline: Research → Analyze → Decide → Train
# Each stage:
#   1. Receives compressed output from previous stage
#   2. Executes its task
#   3. Passes summary to next stage
# Final stage has full accumulated context
```

### Multi-Agent Workflows

```bash
# Hierarchical Planner orchestrates complex project
./hierarchical_planner.sh "Modernize Authentication System"
# → Decomposes into subtasks
# → Delegates to specialist agents (Researcher, Code Analyzer, etc.)
# → Tracks dependencies and monitors progress

# Swarm explores uncertain problem
./swarm_coordinator.py "Why is checkout slow?" --swarm-size 12
# → 12 agents investigate different hypotheses in parallel
# → Coordinator synthesizes findings into consensus

# Pipeline for sequential workflow
./pipeline_manager.py "Feature Specification"
# → Research → Analyze → Decide → Train → Validate
# → Each stage feeds into next with validation
```

## When to Use Which Coordinator

| Coordinator | Best For | Example | Parallelism | Complexity |
|-------------|----------|---------|-------------|------------|
| **Hierarchical Planner** | Complex projects with clear decomposition | "Build microservices platform" | Medium (within levels) | High (DAG management) |
| **Swarm Coordinator** | Uncertain problems, exploration | "Why is app slow?" | Maximum (all parallel) | Medium (synthesis) |
| **Pipeline Manager** | Linear workflows, validation gates | "Research → Analyze → Decide → Train" | None (sequential) | Low |

**Combining Coordinators**: A Hierarchical Planner might use a Swarm Coordinator for one subtask (exploratory research) and a Pipeline Manager for another (sequential implementation). Meta-agents can coordinate other meta-agents.

- Each topic → separate markdown file
- Only final results kept (memory efficient)

## File Structure Example

After tree research on "Should we use cloud storage?":

```
knowledge-base/
├── entries/
│   ├── a1b2c3d4.md  # "Tree Research Index: Should we use cloud storage?"
│   ├── e5f6g7h8.md  # Root: "Should we use cloud storage?" → links to i9j0k1l2, m3n4o5p6
│   ├── i9j0k1l2.md  # Child: "What are the security concerns?" → links to q7r8s9t0
│   ├── m3n4o5p6.md  # Child: "Cost analysis needed?"
│   └── q7r8s9t0.md  # Grandchild: "Encryption standards?"
└── assets/
```

Filenames are random identifiers. Titles in frontmatter and wiki links tell the story.

## Agent Instructions

When asked to conduct research:

1. **Choose research type** based on the question
2. **Generate random filename** (8 alphanumeric chars, e.g., `a1b2c3d4.md`)
3. **Conduct web searches** for each position/query
4. **Require sources**: Exclude any findings without citations
5. **Generate markdown** following the format conventions above
6. **Use wiki links** to connect related research (e.g., `[Security Concerns](./i9j0k1l2.md)`)
7. **Save files** to `knowledge-base/entries/`
8. **For trees**: Save leaf nodes first (bottom-up), then link from parents

## Configuration

No configuration needed. The agent follows these instructions directly.

## MCP Servers (Optional)

If available, these enhance the experience:
- `@modelcontextprotocol/server-filesystem` - for file operations
- Any web search MCP - for research capabilities

But they're optional - use Claude's built-in capabilities if available.

## License

MIT

## Contributing

This is a methodology, not code. Contributions welcome to improve the instructions or add examples.
