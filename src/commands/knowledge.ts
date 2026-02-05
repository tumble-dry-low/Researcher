import chalk from 'chalk';
import { KnowledgeBase } from '../knowledge-base/knowledge-base';

export const knowledgeCommand = {
  async list(): Promise<void> {
    console.log(chalk.blue('📚 Knowledge Base Entries:'));
    console.log();

    try {
      const kb = new KnowledgeBase();
      const entries = await kb.listEntries();

      if (entries.length === 0) {
        console.log(chalk.gray('  (No entries yet)'));
        console.log(chalk.gray('\n  Use `researcher research <topic>` to create entries.'));
        return;
      }

      entries.forEach((entry) => {
        console.log(chalk.yellow(`  • ${entry.title}`));
        console.log(chalk.gray(`    ${entry.path}`));
        if (entry.tags && entry.tags.length > 0) {
          console.log(chalk.cyan(`    Tags: ${entry.tags.join(', ')}`));
        }
        console.log();
      });

      console.log(chalk.green(`\n✓ Total entries: ${entries.length}`));
    } catch (error) {
      console.error(chalk.red('✗ Error listing entries:'), error);
      process.exit(1);
    }
  },

  async view(entryName: string): Promise<void> {
    console.log(chalk.blue('📄 Viewing entry:'), chalk.cyan(entryName));
    console.log();

    try {
      const kb = new KnowledgeBase();
      const entry = await kb.getEntry(entryName);

      if (!entry) {
        console.log(chalk.red('✗ Entry not found'));
        return;
      }

      console.log(chalk.yellow('Title:'), chalk.white(entry.title));
      if (entry.tags && entry.tags.length > 0) {
        console.log(chalk.yellow('Tags:'), chalk.cyan(entry.tags.join(', ')));
      }
      console.log();
      console.log(chalk.white(entry.content));
      console.log();

      if (entry.links && entry.links.length > 0) {
        console.log(chalk.yellow('Linked entries:'));
        entry.links.forEach((link) => {
          console.log(chalk.gray(`  → ${link}`));
        });
      }
    } catch (error) {
      console.error(chalk.red('✗ Error viewing entry:'), error);
      process.exit(1);
    }
  },

  async link(entry1: string, entry2: string): Promise<void> {
    console.log(chalk.blue('🔗 Linking entries:'));
    console.log(chalk.gray(`  ${entry1} ↔ ${entry2}`));

    try {
      const kb = new KnowledgeBase();
      await kb.linkEntries(entry1, entry2);
      console.log(chalk.green('✓ Entries linked'));
    } catch (error) {
      console.error(chalk.red('✗ Error linking entries:'), error);
      process.exit(1);
    }
  },

  async index(): Promise<void> {
    console.log(chalk.blue('📇 Updating knowledge base index...'));

    try {
      const kb = new KnowledgeBase();
      await kb.updateIndex();
      console.log(chalk.green('✓ Index updated'));
    } catch (error) {
      console.error(chalk.red('✗ Error updating index:'), error);
      process.exit(1);
    }
  },

  async search(query: string): Promise<void> {
    console.log(chalk.blue('🔍 Searching knowledge base for:'), chalk.cyan(query));
    console.log();

    try {
      const kb = new KnowledgeBase();
      const results = await kb.search(query);

      if (results.length === 0) {
        console.log(chalk.gray('  No results found'));
        return;
      }

      console.log(chalk.green(`✓ Found ${results.length} results:\n`));

      results.forEach((result, index) => {
        console.log(chalk.yellow(`${index + 1}. ${result.title}`));
        console.log(chalk.gray(`   ${result.path}`));
        if (result.excerpt) {
          console.log(chalk.white(`   ...${result.excerpt}...`));
        }
        console.log();
      });
    } catch (error) {
      console.error(chalk.red('✗ Error searching:'), error);
      process.exit(1);
    }
  },
};
