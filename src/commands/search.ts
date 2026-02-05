import chalk from 'chalk';
import { WebSearcher } from '../research/web-searcher.js';
import { KnowledgeBase } from '../knowledge-base/knowledge-base.js';

interface SearchOptions {
  num: string;
  save?: boolean;
}

export async function searchCommand(query: string, options: SearchOptions): Promise<void> {
  console.log(chalk.blue('🔍 Searching for:'), chalk.cyan(query));
  console.log(chalk.gray('  Results:'), options.num);

  try {
    const searcher = new WebSearcher();
    const results = await searcher.search(query, parseInt(options.num, 10));

    console.log(chalk.green(`\n✓ Found ${results.length} results:\n`));

    results.forEach((result, index) => {
      console.log(chalk.yellow(`${index + 1}. ${result.title}`));
      console.log(chalk.gray(`   ${result.url}`));
      if (result.snippet) {
        console.log(chalk.white(`   ${result.snippet}`));
      }
      console.log();
    });

    if (options.save) {
      console.log(chalk.blue('💾 Saving to knowledge base...'));
      const kb = new KnowledgeBase();
      await kb.saveSearchResults(query, results);
      console.log(chalk.green('✓ Saved to knowledge base'));
    }
  } catch (error) {
    console.error(chalk.red('✗ Search failed:'), error);
    process.exit(1);
  }
}
