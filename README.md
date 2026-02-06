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
