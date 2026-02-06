# Automated Knowledge Base - Quick Start

## Setup

```bash
# Clone the repository
git clone https://github.com/c25l/Researcher.git
cd Researcher

# That's it! No dependencies to install (uses Python 3 built-in sqlite3)
```

## Basic Workflow

### 1. Add Research Note

```bash
./kb-cli add-entity "Should we adopt GraphQL?" "Research question..." '{"type":"question"}'
# Output: {"id": "a1b2c3d4", "title": "Should we adopt GraphQL?"}
```

### 2. Add Child Research

```bash
./kb-cli add-entity "GraphQL Performance" "Performance characteristics..." '{"type":"research"}'
# Output: {"id": "e5f6g7h8", "title": "GraphQL Performance"}
```

### 3. Link Them Automatically

```bash
./kb-cli add-link a1b2c3d4 e5f6g7h8 "child"
# Output: {"link_id": 1, "from": "a1b2c3d4", "to": "e5f6g7h8", "type": "child"}
```

### 4. Add Follow-up Task

```bash
./kb-cli add-task "Research caching strategies" "Look into DataLoader and Redis" e5f6g7h8 '{"priority":"high"}'
# Output: {"task_id": 1, "title": "Research caching strategies"}
```

### 5. Work the Backlog

```bash
# Get all pending tasks
./kb-cli get-tasks pending

# Get task details
./kb-cli get-task 1

# Mark as in progress
./kb-cli update-task-status 1 in_progress

# Mark as completed
./kb-cli update-task-status 1 completed
```

### 6. Navigate the Knowledge Graph

```bash
# Get all links from a node (children)
./kb-cli get-links-from a1b2c3d4

# Get all links to a node (parents)
./kb-cli get-links-to e5f6g7h8

# Search across all content
./kb-cli search "GraphQL"
```

## Agent Workflow

For AI agents conducting research, the system is fully automatic:

```python
# 1. Agent conducts web research on topic
research_content = agent.web_search("GraphQL performance")

# 2. Agent adds entity (ID auto-generated)
result = subprocess.run(['./kb-cli', 'add-entity', 
    'GraphQL Performance', research_content, 
    '{"sources": 5, "confidence": "high"}'], 
    capture_output=True)
entity_id = json.loads(result.stdout)['id']

# 3. Agent identifies follow-up questions
# 4. Agent adds them as tasks automatically
subprocess.run(['./kb-cli', 'add-task',
    'Research GraphQL subscriptions', 
    'Investigate real-time capabilities',
    entity_id,
    '{"priority": "medium"}'])

# 5. Agent links related entities
subprocess.run(['./kb-cli', 'add-link', parent_id, entity_id, 'child'])
```

## Database Schema

```sql
entities (
  id TEXT PRIMARY KEY,           -- Random 8-char ID
  title TEXT NOT NULL,
  content TEXT,
  metadata TEXT,                 -- JSON for flexible data
  created_at TEXT,
  updated_at TEXT
)

links (
  id INTEGER PRIMARY KEY,
  from_id TEXT → entities(id),
  to_id TEXT → entities(id),
  link_type TEXT,                -- "child", "related", "follows"
  created_at TEXT
)

tasks (
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT,
  status TEXT,                   -- "pending", "in_progress", "completed"
  entity_id TEXT → entities(id), -- Optional: tie task to entity
  metadata TEXT,                 -- JSON for priority, tags, etc.
  created_at TEXT,
  updated_at TEXT
)
```

## Link Types

- `child`: Parent→Child relationship (tree research)
- `related`: Horizontal relationship (related topics)
- `follows`: Sequential relationship (task dependencies)
- Custom: Define your own

## Task Statuses

- `pending`: Not started (default)
- `in_progress`: Currently being worked on
- `completed`: Finished
- `cancelled`: Abandoned

## API Reference

See `kb-cli` for all commands:

```bash
./kb-cli
```

## Why This Approach?

✅ **Automatic**: Agents just call commands, system manages structure
✅ **Minimal**: ~300 lines of Python, no dependencies
✅ **Flexible**: JSON metadata supports any schema
✅ **Trackable**: Built-in task backlog for future work
✅ **Queryable**: SQL queries for complex analysis
✅ **Version-controllable**: SQLite database in git (optional)

## Integration with Claude Desktop

The KB can be exposed as MCP tools. Example MCP server (pseudo-code):

```python
@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "add_research_note":
        result = subprocess.run(['./kb-cli', 'add-entity', 
            arguments['title'], arguments['content'], 
            json.dumps(arguments.get('metadata', {}))])
        return json.loads(result.stdout)
    # ... etc
```

Then Claude can use natural language: "Add a research note about GraphQL performance" → system handles everything automatically.
