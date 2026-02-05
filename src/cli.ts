#!/usr/bin/env node

import { Command } from 'commander';
import chalk from 'chalk';
import { searchCommand } from './commands/search';
import { researchCommand } from './commands/research';
import { parallelResearchCommand } from './commands/parallel-research';
import { knowledgeCommand } from './commands/knowledge';
import { initCommand } from './commands/init';

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
