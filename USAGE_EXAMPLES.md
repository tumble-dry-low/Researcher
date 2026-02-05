# Usage Examples

This document provides practical examples of using the Researcher CLI.

## Getting Started

### 1. Initialize Your First Knowledge Base

```bash
# Initialize in the default location (./knowledge-base)
researcher init

# Initialize in a custom location
researcher init --path ~/my-research

# Initialize in the current directory
researcher init --path .
```

**What happens:**
- Creates directory structure
- Generates config.json
- Creates README.md and index.md
- Sets up entries/ and assets/ folders

### 2. Your First Web Search

```bash
# Basic search
researcher search "quantum computing"

# Search with more results
researcher search "artificial intelligence" --num 10

# Search and save to knowledge base
researcher search "machine learning" --save
```

**Output:**
```
🔍 Searching for: quantum computing
  Results: 5

✓ Found 5 results:

1. Quantum Computing - Overview
   https://example.com/quantum
   Introduction to quantum computing principles...

2. Quantum Computers Explained
   ...
```

### 3. Conduct Deep Research

```bash
# Basic research (depth 3)
researcher research "neural networks"

# Shallow research (quick overview)
researcher research "blockchain" --depth 1

# Deep research (comprehensive)
researcher research "climate change" --depth 5

# Research without saving
researcher research "test topic" --no-save
```

**Output:**
```
🔬 Starting deep research on: neural networks
  Depth level: 3

✓ Research complete!

Topic: neural networks
Summary: Research on "neural networks" has been completed...

Key Findings:
  1. Neural networks are computing systems inspired by biological neural networks
  2. Deep learning is a subset of machine learning using neural networks
  ...

Sources:
  1. Neural Networks Explained - https://...
  2. Deep Learning Tutorial - https://...

💾 Saving research to knowledge base...
✓ Research saved to knowledge base
```

## Working with the Knowledge Base

### Viewing Your Research

```bash
# List all entries
researcher kb list

# View a specific entry
researcher kb view research-neural-networks

# View another entry
researcher kb view search-quantum-computing
```

### Searching Your Knowledge Base

```bash
# Search for entries containing "neural"
researcher kb search neural

# Search for "machine learning"
researcher kb search "machine learning"
```

**Output:**
```
🔍 Searching knowledge base for: neural

✓ Found 2 results:

1. neural networks
   research-neural-networks.md
   ...Neural networks are computing systems...

2. deep learning
   research-deep-learning.md
   ...Deep learning uses neural networks with...
```

### Linking Related Topics

```bash
# Link two related research topics
researcher kb link research-neural-networks research-deep-learning

# Link search results to research
researcher kb link search-ai research-artificial-intelligence
```

**What happens:**
- Adds a "Related" section to the first entry
- Creates a markdown link to the second entry
- Makes it easy to navigate between related topics

### Updating the Index

```bash
# Regenerate the knowledge base index
researcher kb index
```

**What happens:**
- Scans all entries in the knowledge base
- Groups them by tags
- Creates alphabetical list
- Updates index.md with timestamps

## Real-World Workflows

### Workflow 1: Learning a New Technology

```bash
# Initialize a knowledge base for your learning
mkdir ~/learning/rust-lang
cd ~/learning/rust-lang
researcher init

# Start with an overview
researcher research "Rust programming language" --depth 3

# Dig deeper into specific topics
researcher research "Rust ownership and borrowing" --depth 4
researcher research "Rust async programming" --depth 3
researcher research "Rust error handling" --depth 3

# Link related concepts
researcher kb link research-rust-programming-language research-rust-ownership-and-borrowing
researcher kb link research-rust-programming-language research-rust-async-programming

# Update index
researcher kb index

# View what you've learned
researcher kb list
```

### Workflow 2: Project Research

```bash
# Create a project research base
cd ~/projects/my-app
researcher init --path ./research

# Research different options
researcher research "React vs Vue.js" --depth 4
researcher research "PostgreSQL vs MongoDB" --depth 3
researcher research "AWS vs Azure vs GCP" --depth 3

# Quick searches for specific questions
researcher search "React hooks best practices" --save
researcher search "PostgreSQL indexing strategies" --save

# Review findings
researcher kb list
researcher kb view research-react-vs-vuejs
```

### Workflow 3: Academic Research

```bash
# Set up research knowledge base
mkdir ~/research/thesis
cd ~/research/thesis
researcher init

# Research main topic
researcher research "machine learning in healthcare" --depth 5

# Research related subtopics
researcher research "medical image analysis" --depth 4
researcher research "clinical decision support systems" --depth 4
researcher research "privacy in healthcare AI" --depth 4

# Link everything together
researcher kb link research-machine-learning-in-healthcare research-medical-image-analysis
researcher kb link research-machine-learning-in-healthcare research-clinical-decision-support-systems
researcher kb link research-machine-learning-in-healthcare research-privacy-in-healthcare-ai

# Generate comprehensive index
researcher kb index

# Search across all research
researcher kb search "neural network"
researcher kb search "patient data"
```

### Workflow 4: Competitive Analysis

```bash
# Create competitive research base
mkdir ~/business/competitors
cd ~/business/competitors
researcher init

# Research competitors
researcher research "Competitor A product features" --depth 3
researcher research "Competitor B pricing strategy" --depth 3
researcher research "Market trends in SaaS" --depth 4

# Quick searches for recent news
researcher search "Competitor A latest funding" --save
researcher search "Industry reports 2024" --save

# Review insights
researcher kb list
researcher kb search "pricing"
```

## Advanced Usage

### Organizing by Project

```bash
# Use different knowledge bases for different projects
~/projects/
  ├── project-a/
  │   └── knowledge-base/
  ├── project-b/
  │   └── knowledge-base/
  └── learning/
      └── knowledge-base/

# Navigate to project and use researcher
cd ~/projects/project-a
researcher research "topic"  # Uses ./knowledge-base
```

### Batch Research

```bash
#!/bin/bash
# research-topics.sh

topics=(
  "artificial intelligence"
  "machine learning"
  "deep learning"
  "neural networks"
  "natural language processing"
)

for topic in "${topics[@]}"; do
  echo "Researching: $topic"
  researcher research "$topic" --depth 3
  sleep 2  # Rate limiting
done

researcher kb index
echo "Research complete! View with: researcher kb list"
```

### Exporting Research

```bash
# View the markdown files directly
cd knowledge-base/entries
ls -l

# Copy to another location
cp -r knowledge-base ~/Dropbox/Research/

# View in a markdown viewer
cd knowledge-base
# Open index.md in your favorite markdown viewer
```

### Integration with Other Tools

#### Obsidian

```bash
# Initialize in your Obsidian vault
cd ~/Obsidian/MyVault
researcher init --path ./Research

# Research topics - they'll appear in Obsidian!
researcher research "topic" --depth 3
```

#### VS Code

```bash
# Research while coding
cd ~/my-project
researcher init

# Quick research without leaving terminal
researcher search "how to optimize React performance" --save

# View in VS Code
code knowledge-base/entries/
```

#### Git

```bash
# Version control your research
cd knowledge-base
git init
git add .
git commit -m "Initial research on AI"

# After more research
researcher research "new topic" --depth 3
git add .
git commit -m "Added research on new topic"
```

## Tips and Tricks

### Quick Reference Card

```bash
# Essential commands
researcher init                           # Start new KB
researcher research <topic> --depth 3     # Research
researcher kb list                        # List all
researcher kb view <entry>                # View entry
researcher kb search <query>              # Search KB
researcher kb index                       # Update index

# Shortcuts
researcher kb    # Alias for: researcher knowledge
```

### Productivity Hacks

```bash
# 1. Create shell aliases
alias ri='researcher init'
alias rr='researcher research'
alias rs='researcher search'
alias rl='researcher kb list'
alias rv='researcher kb view'

# 2. Use tab completion (if your shell supports it)
researcher kb view res<TAB>

# 3. Chain commands
researcher research "topic" --depth 3 && researcher kb index
```

### Naming Conventions

Good entry names are:
- Descriptive: `research-neural-networks` ✓
- Kebab-case: `machine-learning-basics` ✓
- Searchable: `react-hooks-guide` ✓

Avoid:
- Generic: `research-1` ✗
- Spaces: `machine learning` ✗
- Special chars: `research_@_topic` ✗

## Troubleshooting

### "Knowledge base not initialized"

```bash
# Make sure you're in the right directory
pwd

# Check if knowledge-base exists
ls -la

# Initialize if needed
researcher init
```

### "Entry not found"

```bash
# List all entries first
researcher kb list

# Use exact filename (without .md)
researcher kb view research-neural-networks
```

### View Raw Files

```bash
# Navigate to entries
cd knowledge-base/entries

# View with cat, less, or your editor
cat research-neural-networks.md
less search-quantum-computing.md
vim research-ai.md
```

## Next Steps

1. **Extend the system**: See [EXTENDING.md](./EXTENDING.md) for how to add real web search APIs, LLM integration, and vector databases

2. **Customize**: Modify the templates in `src/knowledge-base/knowledge-base.ts` to match your preferred format

3. **Automate**: Create scripts to batch process research topics

4. **Share**: Version control your knowledge base and share with your team

5. **Integrate**: Connect to your existing tools and workflows
