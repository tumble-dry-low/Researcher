# MCP Server Configuration

This file provides configuration examples for integrating the Researcher MCP server with various clients.

## Claude Desktop Configuration

To use the Researcher MCP server with Claude Desktop, add the following to your Claude configuration file:

### macOS/Linux: `~/Library/Application Support/Claude/claude_desktop_config.json`
### Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "researcher": {
      "command": "node",
      "args": [
        "/absolute/path/to/Researcher/dist/mcp-server.js"
      ]
    }
  }
}
```

Or if you've installed it globally with `npm link`:

```json
{
  "mcpServers": {
    "researcher": {
      "command": "researcher-mcp"
    }
  }
}
```

## Available Tools

The Researcher MCP server exposes the following tools:

### 1. initialize_knowledge_base
Initialize a new knowledge base for storing research.

**Parameters:**
- `path` (string, optional): Path where to initialize the knowledge base (default: `./knowledge-base`)

### 2. search_web
Perform a web search on a topic.

**Parameters:**
- `query` (string, required): Search query
- `numResults` (number, optional): Number of results to return (default: 5)

### 3. conduct_research
Conduct deep research on a single topic with configurable depth.

**Parameters:**
- `topic` (string, required): Topic to research
- `depth` (number, optional): Research depth 1-5 (default: 3)
- `save` (boolean, optional): Whether to save results to knowledge base (default: true)
- `knowledgeBasePath` (string, optional): Path to knowledge base (default: `./knowledge-base`)

### 4. conduct_parallel_research
Research multiple topics in parallel for efficiency. Uses parallel subagent spawning and keeps only results, not full context.

**Parameters:**
- `topics` (array of strings, required): Array of topics to research in parallel
- `depth` (number, optional): Research depth 1-5 (default: 3)
- `save` (boolean, optional): Whether to save results to knowledge base (default: true)
- `knowledgeBasePath` (string, optional): Path to knowledge base (default: `./knowledge-base`)

### 5. list_knowledge_base_entries
List all entries in the knowledge base.

**Parameters:**
- `knowledgeBasePath` (string, optional): Path to knowledge base (default: `./knowledge-base`)

### 6. view_knowledge_base_entry
View a specific entry from the knowledge base.

**Parameters:**
- `entryName` (string, required): Name of the entry to view
- `knowledgeBasePath` (string, optional): Path to knowledge base (default: `./knowledge-base`)

### 7. search_knowledge_base
Search within the knowledge base.

**Parameters:**
- `query` (string, required): Search query
- `knowledgeBasePath` (string, optional): Path to knowledge base (default: `./knowledge-base`)

### 8. link_knowledge_base_entries
Create a link between two knowledge base entries.

**Parameters:**
- `entry1` (string, required): First entry name
- `entry2` (string, required): Second entry name
- `knowledgeBasePath` (string, optional): Path to knowledge base (default: `./knowledge-base`)

### 9. update_knowledge_base_index
Update the knowledge base index.

**Parameters:**
- `knowledgeBasePath` (string, optional): Path to knowledge base (default: `./knowledge-base`)

## Testing the MCP Server

You can test the MCP server directly using the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector node dist/mcp-server.js
```

This will open a web interface where you can test all the available tools.

## Running the MCP Server

To run the MCP server directly:

```bash
npm run mcp
```

Or if built:

```bash
node dist/mcp-server.js
```

## Example Usage with Claude

Once configured, you can ask Claude to use the researcher tools:

**Example 1: Initialize and conduct research**
```
Please initialize a knowledge base and then research "quantum computing" with depth 3.
```

**Example 2: Parallel research**
```
Research these topics in parallel: "machine learning", "neural networks", and "deep learning"
```

**Example 3: Search and link**
```
Search the knowledge base for "quantum" and link related entries.
```

## Notes

- The MCP server runs on stdio transport, which is the standard for MCP servers
- All research operations use the same mock search data as the CLI tool
- The knowledge base is stored as markdown files with YAML frontmatter
- Parallel research uses Promise.all for efficiency and doesn't maintain intermediate agent state
