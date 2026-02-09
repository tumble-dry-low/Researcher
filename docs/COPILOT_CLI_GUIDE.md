# Researcher for Copilot CLI

Complete guide for using the Researcher knowledge base system with copilot-cli agents.

## Quick Start for Agents

This system is designed for **maximum automation** - agents just add information, the system manages everything else automatically.

### What Agents Do

```bash
# 1. Add research findings (ID auto-generated)
./kb-cli add "Research Title" "Content with sources" '{"tags":["AI","ML"]}'

# 2. Link related findings (automatic)
./kb-cli link parent_id child_id "child"

# 3. Add follow-up tasks (automatic backlog)
./kb-cli add-task "Research topic X" "Details..." parent_id '{"priority":"high"}'

# 4. Query next work
./kb-cli tasks pending
```

### What System Manages

✅ ID generation (random 8-char IDs)
✅ Storage (SQLite database)
✅ Relationships (links between entities)
✅ Task backlog (prioritized work queue)
✅ Timestamps (automatic)
✅ Search indexing

## Agent Workflows

### Workflow 1: Standard Research

**Goal**: Research a single topic thoroughly

```bash
# 1. Start research
TOPIC="GraphQL vs REST APIs"
QUERIES=("benefits of GraphQL" "GraphQL performance" "REST API advantages" "API comparison")

# 2. For each query, get web search results
for query in "${QUERIES[@]}"; do
    # Agent conducts web search here
    # Collects sources and synthesizes findings
    echo "Researching: $query"
done

# 3. Synthesize all findings into one entity
RESEARCH_CONTENT="# GraphQL vs REST APIs

## Key Findings
1. GraphQL reduces over-fetching (Source: ...)
2. REST has better caching (Source: ...)
...

## Sources
- [Source 1](url)
- [Source 2](url)
"

# 4. Save to knowledge base
ENTITY_ID=$(./kb-cli add "$TOPIC" "$RESEARCH_CONTENT" '{"type":"standard","sources":10,"depth":3}' | jq -r '.id')

echo "Research saved: $ENTITY_ID"
```

### Workflow 2: Structured Research (Debate)

**Goal**: Research multiple perspectives in parallel

```bash
# 1. Define positions
QUESTION="Should we adopt microservices?"
POSITIONS=("pro:Advocate for microservices" "con:Argue against microservices")

# 2. Research each position IN PARALLEL
declare -a POSITION_IDS

for pos in "${POSITIONS[@]}"; do
    stance="${pos%%:*}"
    description="${pos##*:}"
    
    # Generate stance-specific queries
    if [ "$stance" = "pro" ]; then
        QUERIES=("microservices benefits" "microservices advantages" "success stories microservices")
    else
        QUERIES=("microservices drawbacks" "microservices problems" "microservices failures")
    fi
    
    # Research with web searches...
    CONTENT="## Position: $stance
    
Arguments:
1. Point 1 (Source: ...)
2. Point 2 (Source: ...)

Strength: strong (7 sources, 8 arguments)
"
    
    # Save position
    POS_ID=$(./kb-cli add "$QUESTION - $stance" "$CONTENT" "{\"stance\":\"$stance\",\"type\":\"position\"}" | jq -r '.id')
    POSITION_IDS+=("$POS_ID")
done

# 3. Create parent structured research node linking all positions
PARENT_ID=$(./kb-cli add "$QUESTION" "Structured research with multiple perspectives" '{"type":"structured","positions":2}' | jq -r '.id')

for pos_id in "${POSITION_IDS[@]}"; do
    ./kb-cli link "$PARENT_ID" "$pos_id" "position"
done

echo "Structured research completed: $PARENT_ID"
```

### Workflow 3: Tree Research (Hierarchical)

**Goal**: Recursive exploration with automatic branching

```bash
# 1. Start with root question
ROOT_Q="Should we migrate to cloud?"
ROOT_ID=$(./kb-cli add "$ROOT_Q" "Root question" '{"type":"tree-root","depth":0}' | jq -r '.id')

# 2. Research root with multiple positions
# ... conduct structured research on root question ...

# 3. Evaluate: Is it conclusive?
# If one position is "strong" (5+ sources, 5+ args) and others are "weak" (< 3 sources/args):
IS_CONCLUSIVE=false  # Set based on research results

if [ "$IS_CONCLUSIVE" = "true" ]; then
    # Mark conclusive, don't branch
    ./kb-cli update "$ROOT_ID" "" "" '{"conclusive":true,"correct_position":"yes"}'
    echo "Research conclusive: $ROOT_ID"
else
    # Generate follow-up questions from moderate findings
    FOLLOW_UPS=("What are the security implications?" "Cost analysis for cloud migration?")
    
    for followup in "${FOLLOW_UPS[@]}"; do
        # Create child node
        CHILD_ID=$(./kb-cli add "$followup" "Follow-up question" "{\"type\":\"tree-node\",\"depth\":1,\"parent\":\"$ROOT_ID\"}" | jq -r '.id')
        
        # Link to parent
        ./kb-cli link "$ROOT_ID" "$CHILD_ID" "child"
        
        # Add to task backlog for recursive research
        ./kb-cli add-task "Research: $followup" "Conduct structured research on this follow-up" "$CHILD_ID" '{"priority":"high"}'
    done
fi

# 4. Work through backlog recursively
PENDING=$(./kb-cli tasks pending | jq -r '.[].id' | head -1)
if [ ! -z "$PENDING" ]; then
    echo "Next task: $PENDING"
    # Process this task (recursive call to step 2)
fi
```

## Position Strength Assessment

**Agents should classify each position:**

```bash
# Count sources and arguments
SOURCES=7
ARGUMENTS=8

if [ $SOURCES -ge 5 ] && [ $ARGUMENTS -ge 5 ]; then
    STRENGTH="strong"
elif [ $SOURCES -ge 3 ] && [ $ARGUMENTS -ge 3 ]; then
    STRENGTH="moderate"
else
    STRENGTH="weak"
fi

# Include in metadata
./kb-cli add "Position" "Content" "{\"strength\":\"$STRENGTH\",\"sources\":$SOURCES,\"arguments\":$ARGUMENTS}"
```

## Branch Pruning Logic

**For tree research, determine if a node is conclusive:**

```python
def is_conclusive(positions):
    """
    A node is conclusive if:
    - Exactly 1 position is "strong" (5+ sources, 5+ arguments)
    - All other positions are "weak" (< 3 sources OR < 3 arguments)
    """
    strong_count = sum(1 for p in positions if p['strength'] == 'strong')
    weak_count = sum(1 for p in positions if p['strength'] == 'weak')
    
    return strong_count == 1 and weak_count == len(positions) - 1
```

## Task Management

**Agents should actively manage the backlog:**

```bash
# Get next task
TASK=$(./kb-cli tasks pending | jq -r '.[0]')
TASK_ID=$(echo "$TASK" | jq -r '.id')
ENTITY_ID=$(echo "$TASK" | jq -r '.entity_id')

# Mark as in progress
./kb-cli update-task "$TASK_ID" in_progress

# Do the research work...
# ... conduct web searches, synthesize findings ...

# Save results
./kb-cli update "$ENTITY_ID" "Title" "Research results..."

# Mark task as completed
./kb-cli update-task "$TASK_ID" completed

# Check for more work
REMAINING=$(./kb-cli tasks pending | jq '. | length')
echo "Remaining tasks: $REMAINING"
```

## Query Generation by Stance

**Generate appropriate queries based on the position stance:**

```python
def generate_queries(topic, stance):
    """Generate stance-appropriate search queries."""
    if stance == "pro":
        return [
            f"{topic} benefits",
            f"{topic} advantages",
            f"why {topic}",
            f"evidence for {topic}",
            f"{topic} success stories"
        ]
    elif stance == "con":
        return [
            f"{topic} drawbacks",
            f"{topic} disadvantages", 
            f"problems with {topic}",
            f"{topic} risks",
            f"{topic} criticism"
        ]
    else:  # analysis/neutral
        return [
            f"{topic} analysis",
            f"{topic} comparison",
            f"{topic} evaluation",
            f"{topic} pros and cons"
        ]
```

## Source Citation Requirements

**All findings MUST cite sources. Positions without sources are inadmissible.**

```markdown
## Valid Finding

GraphQL reduces over-fetching by allowing clients to specify exact data requirements (Source: [Apollo GraphQL Docs](https://apollographql.com/docs))

## Invalid Finding (No Source)

~~GraphQL is faster than REST.~~ ❌ INADMISSIBLE - No source cited
```

## Error Handling

**Agents should handle errors gracefully:**

```bash
# Check if command succeeded
if ! RESULT=$(./kb-cli add "Title" "Content" '{}' 2>&1); then
    echo "Error adding entity: $RESULT" >&2
    exit 1
fi

# Validate JSON output
if ! ENTITY_ID=$(echo "$RESULT" | jq -r '.id' 2>/dev/null); then
    echo "Error parsing response: $RESULT" >&2
    exit 1
fi

# Verify entity was created
if ! ./kb-cli get "$ENTITY_ID" >/dev/null 2>&1; then
    echo "Entity not found: $ENTITY_ID" >&2
    exit 1
fi
```

## Statistics and Metrics

**Track research progress:**

```bash
# Get research statistics
TOTAL_ENTITIES=$(./kb-cli list | jq '. | length')
TOTAL_LINKS=$(./kb-cli stats | jq '.links')
PENDING_TASKS=$(./kb-cli tasks pending | jq '. | length')
COMPLETED_TASKS=$(./kb-cli tasks completed | jq '. | length')

echo "Research Progress:"
echo "  Entities: $TOTAL_ENTITIES"
echo "  Links: $TOTAL_LINKS"
echo "  Pending: $PENDING_TASKS"
echo "  Completed: $COMPLETED_TASKS"
```

## Export and Sharing

**Export research for sharing:**

```bash
# Export single entity as markdown
./kb-cli export abc123 > research-abc123.md

# Export entire knowledge graph
./kb-cli export --all > knowledge-base-export.json

# Generate visual graph (requires graphviz)
./kb-cli graph | dot -Tpng > knowledge-graph.png
```

## Integration with Copilot CLI

### As a Custom Agent

Create a `.github/agents/researcher.md` file:

````markdown
# Researcher Agent

You are a research agent with access to an automatic knowledge base system.

## Your Capabilities

1. **Web Search**: You can search the web for information
2. **Knowledge Base**: You have `kb-cli` commands to manage research
3. **Task Management**: You can add and complete tasks autonomously

## Your Workflow

When asked to research a topic:

1. Determine research type (standard, structured, or tree)
2. Conduct web searches using appropriate queries
3. Save findings to knowledge base using `kb-cli add`
4. Link related findings using `kb-cli link`
5. Add follow-up tasks using `kb-cli add-task`
6. Work through backlog using `kb-cli tasks pending`

## Example

User: "Research GraphQL vs REST APIs"

You should:
```bash
# 1. Generate queries
queries=("GraphQL benefits" "REST advantages" "API performance comparison")

# 2. Search and synthesize
# ... conduct web searches ...

# 3. Save to KB
./kb-cli add "GraphQL vs REST" "$content" '{"type":"standard"}'

# 4. Report results
echo "Research completed. Key findings: ..."
```

## Rules

- **Always cite sources**: Findings without sources are inadmissible
- **Work the backlog**: Check `kb-cli tasks pending` and complete tasks autonomously
- **Link related work**: Use `kb-cli link` to connect related research
- **Use metadata**: Include tags, confidence, depth in all entities
````

### As MCP Tools

Expose kb-cli commands as MCP tools for Claude/other agents:

```python
# Example MCP server wrapping kb-cli
from mcp.server import Server, types

server = Server("researcher")

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "add_research_note":
        result = subprocess.run([
            './kb-cli', 'add',
            arguments['title'],
            arguments['content'],
            json.dumps(arguments.get('metadata', {}))
        ], capture_output=True, text=True)
        
        return [types.TextContent(
            type="text",
            text=result.stdout
        )]
    
    # ... other tools ...
```

## Best Practices

### 1. Iterative Deepening

Start broad, then go deep:

```bash
# Level 1: Overview
./kb-cli add "Topic Overview" "High-level summary" '{"depth":1}'

# Level 2: Key aspects
./kb-cli add "Aspect A" "Detailed research" '{"depth":2}'
./kb-cli add "Aspect B" "Detailed research" '{"depth":2}'

# Level 3: Specific questions
./kb-cli add "Detail X" "Very specific finding" '{"depth":3}'
```

### 2. Parallel Processing

Research multiple aspects simultaneously:

```bash
# Launch parallel research
for topic in "${TOPICS[@]}"; do
    (
        # Each runs in background
        ./kb-cli add "$topic" "$(research_topic $topic)" '{}'
    ) &
done

# Wait for all to complete
wait
```

### 3. Continuous Learning

Keep building the knowledge base:

```bash
while true; do
    # Get next pending task
    TASK=$(./kb-cli tasks pending | jq -r '.[0]')
    
    if [ "$TASK" = "null" ]; then
        echo "No more tasks. Research complete."
        break
    fi
    
    # Process task
    process_task "$TASK"
    
    # Mark completed
    ./kb-cli update-task "$(echo $TASK | jq -r '.id')" completed
done
```

## Troubleshooting

### Command Not Found

```bash
# Make kb-cli executable
chmod +x ./kb-cli

# Check Python version (needs 3.7+)
python3 --version
```

### Database Locked

```bash
# Only one process should write at a time
# Use advisory locks for parallel writes
flock /tmp/kb.lock ./kb-cli add "..." "..." '{}'
```

### Invalid JSON

```bash
# Always validate JSON before passing
if ! echo "$METADATA" | jq . >/dev/null 2>&1; then
    echo "Invalid JSON: $METADATA"
    exit 1
fi
```

## See Also

- `AUTOMATED_KB.md` - Automation patterns
- `../README.md` - Overview and CLI reference
- `../kb.py` - Python implementation
- `../kb-cli` - Command-line interface
- `agents/coordinators/` - Coordinator agent definitions
- `agents/specialists/` - Specialist agent definitions
