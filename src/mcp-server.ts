#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from '@modelcontextprotocol/sdk/types.js';
import { ResearchAgent } from './research/research-agent.js';
import { WebSearcher } from './research/web-searcher.js';
import { KnowledgeBase } from './knowledge-base/knowledge-base.js';
import fs from 'fs-extra';
import path from 'path';

// Type interfaces for tool arguments
interface InitializeKnowledgeBaseArgs {
  path?: string;
}

interface SearchWebArgs {
  query: string;
  numResults?: number;
}

interface ConductResearchArgs {
  topic: string;
  depth?: number;
  save?: boolean;
  knowledgeBasePath?: string;
}

interface ConductParallelResearchArgs {
  topics: string[];
  depth?: number;
  save?: boolean;
  knowledgeBasePath?: string;
}

interface KnowledgeBasePathArgs {
  knowledgeBasePath?: string;
}

interface ViewEntryArgs extends KnowledgeBasePathArgs {
  entryName: string;
}

interface SearchKnowledgeBaseArgs extends KnowledgeBasePathArgs {
  query: string;
}

interface LinkEntriesArgs extends KnowledgeBasePathArgs {
  entry1: string;
  entry2: string;
}

// Define the tools that the MCP server will expose
const TOOLS: Tool[] = [
  {
    name: 'initialize_knowledge_base',
    description: 'Initialize a new knowledge base for storing research',
    inputSchema: {
      type: 'object',
      properties: {
        path: {
          type: 'string',
          description: 'Path where to initialize the knowledge base',
          default: './knowledge-base',
        },
      },
    },
  },
  {
    name: 'search_web',
    description: 'Perform a web search on a topic',
    inputSchema: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description: 'Search query',
        },
        numResults: {
          type: 'number',
          description: 'Number of results to return',
          default: 5,
        },
      },
      required: ['query'],
    },
  },
  {
    name: 'conduct_research',
    description: 'Conduct deep research on a single topic with configurable depth',
    inputSchema: {
      type: 'object',
      properties: {
        topic: {
          type: 'string',
          description: 'Topic to research',
        },
        depth: {
          type: 'number',
          description: 'Research depth (1-5)',
          default: 3,
        },
        save: {
          type: 'boolean',
          description: 'Whether to save results to knowledge base',
          default: true,
        },
        knowledgeBasePath: {
          type: 'string',
          description: 'Path to knowledge base',
          default: './knowledge-base',
        },
      },
      required: ['topic'],
    },
  },
  {
    name: 'conduct_parallel_research',
    description: 'Research multiple topics in parallel for efficiency. Uses parallel subagent spawning and keeps only results, not full context.',
    inputSchema: {
      type: 'object',
      properties: {
        topics: {
          type: 'array',
          items: {
            type: 'string',
          },
          description: 'Array of topics to research in parallel',
        },
        depth: {
          type: 'number',
          description: 'Research depth (1-5)',
          default: 3,
        },
        save: {
          type: 'boolean',
          description: 'Whether to save results to knowledge base',
          default: true,
        },
        knowledgeBasePath: {
          type: 'string',
          description: 'Path to knowledge base',
          default: './knowledge-base',
        },
      },
      required: ['topics'],
    },
  },
  {
    name: 'list_knowledge_base_entries',
    description: 'List all entries in the knowledge base',
    inputSchema: {
      type: 'object',
      properties: {
        knowledgeBasePath: {
          type: 'string',
          description: 'Path to knowledge base',
          default: './knowledge-base',
        },
      },
    },
  },
  {
    name: 'view_knowledge_base_entry',
    description: 'View a specific entry from the knowledge base',
    inputSchema: {
      type: 'object',
      properties: {
        entryName: {
          type: 'string',
          description: 'Name of the entry to view',
        },
        knowledgeBasePath: {
          type: 'string',
          description: 'Path to knowledge base',
          default: './knowledge-base',
        },
      },
      required: ['entryName'],
    },
  },
  {
    name: 'search_knowledge_base',
    description: 'Search within the knowledge base',
    inputSchema: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description: 'Search query',
        },
        knowledgeBasePath: {
          type: 'string',
          description: 'Path to knowledge base',
          default: './knowledge-base',
        },
      },
      required: ['query'],
    },
  },
  {
    name: 'link_knowledge_base_entries',
    description: 'Create a link between two knowledge base entries',
    inputSchema: {
      type: 'object',
      properties: {
        entry1: {
          type: 'string',
          description: 'First entry name',
        },
        entry2: {
          type: 'string',
          description: 'Second entry name',
        },
        knowledgeBasePath: {
          type: 'string',
          description: 'Path to knowledge base',
          default: './knowledge-base',
        },
      },
      required: ['entry1', 'entry2'],
    },
  },
  {
    name: 'update_knowledge_base_index',
    description: 'Update the knowledge base index',
    inputSchema: {
      type: 'object',
      properties: {
        knowledgeBasePath: {
          type: 'string',
          description: 'Path to knowledge base',
          default: './knowledge-base',
        },
      },
    },
  },
];

// Create the MCP server
const server = new Server(
  {
    name: 'researcher',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Handle list tools request
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: TOOLS,
  };
});

// Handle tool execution
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    // Type guard for args
    if (!args || typeof args !== 'object') {
      throw new Error('Invalid arguments provided');
    }

    switch (name) {
      case 'initialize_knowledge_base': {
        const typedArgs = args as unknown as InitializeKnowledgeBaseArgs;
        const kbPath = path.resolve(typedArgs.path || './knowledge-base');
        
        await fs.ensureDir(kbPath);
        await fs.ensureDir(path.join(kbPath, 'entries'));
        await fs.ensureDir(path.join(kbPath, 'assets'));

        const config = {
          name: 'Research Knowledge Base',
          createdAt: new Date().toISOString(),
          version: '1.0.0',
          settings: {
            indexEnabled: true,
            autoLink: true,
          },
        };

        await fs.writeJSON(path.join(kbPath, 'config.json'), config, { spaces: 2 });

        const readme = `# Research Knowledge Base

Initialized on ${new Date().toISOString()}.

## Structure

- \`entries/\` - Markdown files for research entries
- \`assets/\` - Images, documents, and other assets
- \`index.md\` - Main index of all entries
- \`config.json\` - Configuration file
`;

        await fs.writeFile(path.join(kbPath, 'README.md'), readme);

        const index = `# Knowledge Base Index

*Last updated: ${new Date().toISOString()}*

## Entries

(No entries yet)
`;

        await fs.writeFile(path.join(kbPath, 'index.md'), index);

        return {
          content: [
            {
              type: 'text',
              text: `Knowledge base initialized successfully at ${kbPath}`,
            },
          ],
        };
      }

      case 'search_web': {
        const typedArgs = args as unknown as SearchWebArgs;
        const searcher = new WebSearcher();
        const results = await searcher.search(typedArgs.query, typedArgs.numResults || 5);

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(results, null, 2),
            },
          ],
        };
      }

      case 'conduct_research': {
        const typedArgs = args as unknown as ConductResearchArgs;
        const agent = new ResearchAgent();
        const research = await agent.conductResearch(typedArgs.topic, typedArgs.depth || 3);

        if (typedArgs.save !== false) {
          const kb = new KnowledgeBase(typedArgs.knowledgeBasePath || './knowledge-base');
          await kb.saveResearch(research);
        }

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(research, null, 2),
            },
          ],
        };
      }

      case 'conduct_parallel_research': {
        const typedArgs = args as unknown as ConductParallelResearchArgs;
        const agent = new ResearchAgent();
        const results = await agent.conductParallelResearch(
          typedArgs.topics,
          typedArgs.depth || 3
        );

        if (typedArgs.save !== false) {
          const kb = new KnowledgeBase(typedArgs.knowledgeBasePath || './knowledge-base');
          await Promise.all(results.map(research => kb.saveResearch(research)));
        }

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(results, null, 2),
            },
          ],
        };
      }

      case 'list_knowledge_base_entries': {
        const typedArgs = args as unknown as KnowledgeBasePathArgs;
        const kb = new KnowledgeBase(typedArgs.knowledgeBasePath || './knowledge-base');
        const entries = await kb.listEntries();

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(entries, null, 2),
            },
          ],
        };
      }

      case 'view_knowledge_base_entry': {
        const typedArgs = args as unknown as ViewEntryArgs;
        const kb = new KnowledgeBase(typedArgs.knowledgeBasePath || './knowledge-base');
        const entry = await kb.getEntry(typedArgs.entryName);

        if (!entry) {
          return {
            content: [
              {
                type: 'text',
                text: 'Entry not found',
              },
            ],
            isError: true,
          };
        }

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(entry, null, 2),
            },
          ],
        };
      }

      case 'search_knowledge_base': {
        const typedArgs = args as unknown as SearchKnowledgeBaseArgs;
        const kb = new KnowledgeBase(typedArgs.knowledgeBasePath || './knowledge-base');
        const results = await kb.search(typedArgs.query);

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(results, null, 2),
            },
          ],
        };
      }

      case 'link_knowledge_base_entries': {
        const typedArgs = args as unknown as LinkEntriesArgs;
        const kb = new KnowledgeBase(typedArgs.knowledgeBasePath || './knowledge-base');
        await kb.linkEntries(typedArgs.entry1, typedArgs.entry2);

        return {
          content: [
            {
              type: 'text',
              text: `Successfully linked ${typedArgs.entry1} and ${typedArgs.entry2}`,
            },
          ],
        };
      }

      case 'update_knowledge_base_index': {
        const typedArgs = args as unknown as KnowledgeBasePathArgs;
        const kb = new KnowledgeBase(typedArgs.knowledgeBasePath || './knowledge-base');
        await kb.updateIndex();

        return {
          content: [
            {
              type: 'text',
              text: 'Knowledge base index updated successfully',
            },
          ],
        };
      }

      default:
        return {
          content: [
            {
              type: 'text',
              text: `Unknown tool: ${name}`,
            },
          ],
          isError: true,
        };
    }
  } catch (error) {
    return {
      content: [
        {
          type: 'text',
          text: `Error: ${error instanceof Error ? error.message : String(error)}`,
        },
      ],
      isError: true,
    };
  }
});

// Start the server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Researcher MCP Server running on stdio');
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
