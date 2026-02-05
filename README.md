# Researcher 🔬

A deep research agent with web search capabilities and a linked knowledge base management system. Built to work seamlessly with copilot-cli.

## Features

- 🌐 **Web Research**: Perform web searches and deep research on any topic
- ⚡ **Parallel Execution**: Research multiple topics simultaneously for efficiency
- 📚 **Knowledge Base**: Accumulate research in a markdown-based wiki with automatic linking
- 🔗 **Linked Notes**: Create connections between research entries
- 📇 **Smart Indexing**: Automatic index generation and search within your knowledge base
- 🎯 **Deep Research**: Multi-level research with configurable depth
- 🚀 **CLI-First**: Built for command-line usage and copilot integration

## Installation

```bash
npm install
npm run build
```

To install globally (optional):
```bash
npm link
```

## Quick Start

1. **Initialize a knowledge base**:
   ```bash
   researcher init
   ```

2. **Search the web**:
   ```bash
   researcher search "quantum computing"
   ```

3. **Conduct deep research**:
   ```bash
   researcher research "artificial intelligence" --depth 3
   ```

4. **View your knowledge base**:
   ```bash
   researcher knowledge list
   ```

## Commands

### Initialize Knowledge Base

```bash
researcher init [options]
```

Creates a new knowledge base in the current directory.

**Options:**
- `-p, --path <path>` - Path to initialize knowledge base (default: `./knowledge-base`)

**Example:**
```bash
researcher init --path ./my-research
```

### Web Search

```bash
researcher search <query> [options]
```

Perform a web search on a topic.

**Options:**
- `-n, --num <number>` - Number of results to return (default: 5)
- `-s, --save` - Save results to knowledge base

**Example:**
```bash
researcher search "machine learning" --num 10 --save
```

### Deep Research

```bash
researcher research <topic> [options]
```

Conduct comprehensive research on a topic with multiple search queries and synthesis.

**Options:**
- `-d, --depth <number>` - Research depth from 1-5 (default: 3)
- `-s, --save` - Save research to knowledge base (default: true)

**Example:**
```bash
researcher research "neural networks" --depth 5
```

### Parallel Research

```bash
researcher parallel <topics> [options]
```

Research multiple topics in parallel for maximum efficiency. Uses parallel subagent spawning and keeps only the results (not full context) for optimal performance.

**Options:**
- `-d, --depth <number>` - Research depth from 1-5 (default: 3)
- `-s, --save` - Save research to knowledge base (default: true)

**Topics Format:**
- Comma-separated: `"topic1,topic2,topic3"`

**Example:**
```bash
# Research multiple topics simultaneously
researcher parallel "quantum computing,machine learning,neural networks" --depth 3

# All results are saved efficiently without keeping full context
```

**Benefits:**
- ⚡ Faster execution through parallel processing
- 💾 Memory efficient - only final results are retained
- 🎯 Perfect for batch research tasks

### Knowledge Base Management

#### List Entries

```bash
researcher knowledge list
# or
researcher kb list
```

List all entries in your knowledge base.

#### View Entry

```bash
researcher knowledge view <entry>
# or
researcher kb view <entry>
```

View a specific knowledge base entry.

**Example:**
```bash
researcher kb view research-quantum-computing
```

#### Link Entries

```bash
researcher knowledge link <entry1> <entry2>
# or
researcher kb link <entry1> <entry2>
```

Create a bidirectional link between two knowledge base entries.

**Example:**
```bash
researcher kb link research-ai research-machine-learning
```

#### Update Index

```bash
researcher knowledge index
# or
researcher kb index
```

Generate or update the knowledge base index with all entries organized by topic.

#### Search Knowledge Base

```bash
researcher knowledge search <query>
# or
researcher kb search <query>
```

Search within your knowledge base entries.

**Example:**
```bash
researcher kb search "neural networks"
```

## Knowledge Base Structure

When you initialize a knowledge base, it creates the following structure:

```
knowledge-base/
├── README.md           # Introduction and usage guide
├── config.json         # Configuration file
├── index.md           # Auto-generated index of all entries
├── entries/           # Markdown files for each research entry
│   ├── research-topic-1.md
│   ├── research-topic-2.md
│   └── search-query.md
└── assets/            # Images, PDFs, and other resources
```

### Entry Format

Each entry is a markdown file with YAML frontmatter:

```markdown
---
title: "Quantum Computing"
tags: ["research", "quantum", "computing"]
createdAt: "2024-01-01T00:00:00.000Z"
---

# Quantum Computing

## Summary
...

## Key Findings
1. ...
2. ...

## Sources
1. [Title](url)
```

## Integration with Copilot CLI

This tool is designed to work seamlessly with copilot-cli. You can use it in your copilot workflows:

```bash
# Use researcher commands in your copilot session
researcher init
researcher research "topic" --depth 3
researcher kb list
```

## Future Enhancements

The scaffolding supports future additions:

- 🔌 **Vector Database Integration**: Add semantic search capabilities
- 🤖 **LLM Integration**: Enhanced summarization and synthesis
- 🌐 **Multiple Search APIs**: Google, Bing, DuckDuckGo integration
- 📊 **Visualization**: Knowledge graph visualization
- 🔄 **Sync**: Cloud synchronization of knowledge bases
- 📱 **Web UI**: Browser-based interface for knowledge base

## Development

### Build

```bash
npm run build
```

### Development Mode

```bash
npm run dev -- <command>
```

### Clean Build

```bash
npm run clean
npm run build
```

## Architecture

### Components

1. **CLI Layer** (`src/cli.ts`)
   - Command-line interface using Commander.js
   - Entry point for all operations

2. **Commands** (`src/commands/`)
   - Individual command implementations
   - User interaction and output formatting

3. **Research Engine** (`src/research/`)
   - `web-searcher.ts`: Web search capabilities (scaffold for API integration)
   - `research-agent.ts`: Deep research orchestration and synthesis

4. **Knowledge Base** (`src/knowledge-base/`)
   - `knowledge-base.ts`: Markdown file management, linking, indexing

### Extension Points

- **Web Searcher**: Integrate real search APIs (Google, Bing, etc.)
- **Research Agent**: Add LLM-based analysis and summarization
- **Knowledge Base**: Add vector database for semantic search

## License

ISC

## Contributing

Contributions welcome! This is a scaffold meant to be extended with:
- Real web search API integration
- LLM-based content analysis
- Vector database support
- Additional export formats
- Knowledge graph visualization