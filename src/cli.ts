#!/usr/bin/env node

import { Command } from 'commander';
import chalk from 'chalk';
import { searchCommand } from './commands/search.js';
import { researchCommand } from './commands/research.js';
import { parallelResearchCommand } from './commands/parallel-research.js';
import { structuredResearchCommand } from './commands/structured-research.js';
import { treeResearchCommand } from './commands/tree-research.js';
import { knowledgeCommand } from './commands/knowledge.js';
import { initCommand } from './commands/init.js';

const program = new Command();

program
  .name('researcher')
  .description('AI-powered deep research agent with web search and knowledge base')
  .version('1.0.0');

// Initialize command - sets up knowledge base
program
  .command('init')
  .description('Initialize a new knowledge base in the current directory')
  .option('-p, --path <path>', 'Path to initialize knowledge base', './knowledge-base')
  .action(initCommand);

// Search command - perform web searches
program
  .command('search <query>')
  .description('Perform a web search on a topic')
  .option('-n, --num <number>', 'Number of results to return', '5')
  .option('-s, --save', 'Save results to knowledge base')
  .action(searchCommand);

// Research command - deep dive into a topic
program
  .command('research <topic>')
  .description('Perform deep research on a topic')
  .option('-d, --depth <number>', 'Research depth (1-5)', '3')
  .option('-s, --save', 'Save research to knowledge base', true)
  .action(researchCommand);

// Parallel research command - research multiple topics efficiently
program
  .command('parallel <topics>')
  .description('Research multiple topics in parallel (comma-separated)')
  .option('-d, --depth <number>', 'Research depth (1-5)', '3')
  .option('-s, --save', 'Save research to knowledge base', true)
  .action(parallelResearchCommand);

// Structured research command - research with multiple perspectives
program
  .command('structured <question>')
  .description('Conduct structured research with multiple perspectives (pro/con analysis, debate)')
  .option('-d, --depth <number>', 'Research depth (1-5)', '3')
  .option('-s, --save', 'Save research to knowledge base', true)
  .option('-t, --type <type>', 'Type: yesno, options, or custom', 'yesno')
  .option('-o, --options <options>', 'Options for research (comma-separated for options type)')
  .action(structuredResearchCommand);

// Tree research command - hierarchical research following question branches
program
  .command('tree <question>')
  .description('Conduct tree-based hierarchical research, exploring branches until conclusive or max depth')
  .option('-d, --depth <number>', 'Research depth per node (1-5)', '3')
  .option('-m, --max-depth <number>', 'Maximum tree depth', '3')
  .option('-s, --save', 'Save research to knowledge base', true)
  .option('-t, --type <type>', 'Initial position type: yesno, options, or custom', 'yesno')
  .option('-o, --options <options>', 'Options for initial positions')
  .action(treeResearchCommand);

// Knowledge base commands
const knowledge = program
  .command('knowledge')
  .alias('kb')
  .description('Manage knowledge base');

knowledge
  .command('list')
  .description('List all entries in knowledge base')
  .action(knowledgeCommand.list);

knowledge
  .command('view <entry>')
  .description('View a knowledge base entry')
  .action(knowledgeCommand.view);

knowledge
  .command('link <entry1> <entry2>')
  .description('Create a link between two entries')
  .action(knowledgeCommand.link);

knowledge
  .command('index')
  .description('Generate/update the knowledge base index')
  .action(knowledgeCommand.index);

knowledge
  .command('search <query>')
  .description('Search within the knowledge base')
  .action(knowledgeCommand.search);

program.parse();
