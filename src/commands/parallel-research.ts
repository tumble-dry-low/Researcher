import chalk from 'chalk';
import { ResearchAgent } from '../research/research-agent.js';
import { KnowledgeBase } from '../knowledge-base/knowledge-base.js';

interface ParallelResearchOptions {
  depth: string;
  save: boolean;
}

export async function parallelResearchCommand(
  topics: string,
  options: ParallelResearchOptions
): Promise<void> {
  const depth = parseInt(options.depth, 10);
  
  // Parse topics - support comma-separated
  const topicList = topics.split(',').map(t => t.trim()).filter(t => t.length > 0);

  if (topicList.length === 0) {
    console.error(chalk.red('✗ No topics provided'));
    process.exit(1);
  }

  console.log(chalk.blue('🔬 Starting parallel research on'), chalk.cyan(`${topicList.length} topics`));
  console.log(chalk.gray('  Depth level:'), depth);
  console.log(chalk.gray('  Topics:'), topicList.join(', '));
  console.log();

  try {
    const agent = new ResearchAgent();
    
    // Execute research in parallel - keeps only results, not full context
    const startTime = Date.now();
    const results = await agent.conductParallelResearch(topicList, depth);
    const duration = ((Date.now() - startTime) / 1000).toFixed(2);

    console.log(chalk.green(`\n✓ Parallel research complete in ${duration}s!\n`));

    // Display summary for each topic
    results.forEach((research, index) => {
      console.log(chalk.yellow(`[${index + 1}/${results.length}] ${research.topic}`));
      console.log(chalk.white(`  Summary: ${research.summary}`));
      console.log(chalk.gray(`  Findings: ${research.findings.length} | Sources: ${research.sources.length}`));
      console.log();
    });

    if (options.save) {
      console.log(chalk.blue('💾 Saving all research to knowledge base...'));
      const kb = new KnowledgeBase();
      
      // Save all results in parallel
      await Promise.all(results.map(research => kb.saveResearch(research)));
      
      console.log(chalk.green(`✓ Saved ${results.length} research entries to knowledge base`));
    }
  } catch (error) {
    console.error(chalk.red('✗ Parallel research failed:'), error);
    process.exit(1);
  }
}
