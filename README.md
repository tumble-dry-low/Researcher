# Researcher 🔬

A prompt-based deep research system for AI agents. No code required - just instructions for conducting hierarchical research with wiki-linked markdown files.

## Overview

This repository provides a methodology for AI agents (Claude, GPT, etc.) to conduct structured, hierarchical research and maintain a linked knowledge base using markdown files. The agent uses its built-in file operations and web search capabilities - no custom code needed.

## What's Included

- **This README**: Complete instructions for the research methodology
- **knowledge-base/**: Empty directory where research results are saved

## Prerequisites

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

```
knowledge-base/entries/
├── research-{topic-slug}.md              # Single topic research
├── structured-{question-slug}.md         # Debate-style multi-perspective
├── tree-{question}-index.md              # Tree research overview
├── tree-{question}-node-d{N}-{slug}.md   # Individual tree nodes at depth N
```

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

**Index File** (`tree-{question}-index.md`):
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

**Node File** (`tree-{question}-node-d{N}-{slug}.md`):
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

1. **Link between related research**: `[Related Topic](./research-related-topic.md)`
2. **Parent to children**: `[Follow-up Question](./tree-...-node-d2-follow-up.md)`
3. **Index to nodes**: Tree index links to all nodes for navigation
4. **Bidirectional**: When linking A→B, also add B→A

### Query Generation by Stance

**Pro stance**: Use "benefits", "advantages", "why [option]", "evidence for"
**Con stance**: Use "drawbacks", "disadvantages", "problems with", "risks", "criticism"
**Analysis**: Use "analysis", "comparison", "evaluation", "pros and cons"

## Usage Examples

### Example 1: Yes/No Question Tree

```
Root: "Should we adopt microservices?"
├─ If non-conclusive, branch to:
   ├─ "What are the deployment challenges?" (Yes/No)
   ├─ "Is our team size adequate?" (Yes/No)
   └─ "What about data consistency?" (Yes/No)
```

Each node saved as separate file with parent context.

### Example 2: Multi-Option Debate

Question: "Which database: PostgreSQL, MongoDB, or MySQL?"
- Creates 6 positions (pro/con for each option)
- Each researched in parallel
- Results in one structured markdown file

### Example 3: Parallel Research

Research "AI, ML, DL" as 3 separate topics in parallel.
- Each topic → separate markdown file
- Only final results kept (memory efficient)

## File Structure Example

After tree research on "Should we use cloud storage?":

```
knowledge-base/
├── entries/
│   ├── tree-should-we-use-cloud-storage-index.md
│   ├── tree-should-we-use-cloud-storage-node-d0-should-we-use-cloud-storage.md
│   ├── tree-should-we-use-cloud-storage-node-d1-what-are-security-concerns.md
│   ├── tree-should-we-use-cloud-storage-node-d1-cost-analysis-needed.md
│   └── tree-should-we-use-cloud-storage-node-d2-encryption-standards.md
└── assets/
```

## Agent Instructions

When asked to conduct research:

1. **Choose research type** based on the question
2. **Conduct web searches** for each position/query
3. **Require sources**: Exclude any findings without citations
4. **Generate markdown** following the format conventions above
5. **Use wiki links** to connect related research
6. **Save files** to `knowledge-base/entries/`
7. **For trees**: Save leaf nodes first (bottom-up)

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
