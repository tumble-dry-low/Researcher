import chalk from 'chalk';
import { ResearchAgent } from '../research/research-agent.js';
import { KnowledgeBase } from '../knowledge-base/knowledge-base.js';

interface ResearchOptions {
  depth: string;
  save: boolean;
}

export async function researchCommand(topic: string, options: ResearchOptions): Promise<void> {
  const depth = parseInt(options.depth, 10);

  console.log(chalk.blue('🔬 Starting deep research on:'), chalk.cyan(topic));
  console.log(chalk.gray('  Depth level:'), depth);
  console.log();

  try {
    const agent = new ResearchAgent();
    const research = await agent.conductResearch(topic, depth);

    console.log(chalk.green('\n✓ Research complete!\n'));
    console.log(chalk.yellow('Topic:'), chalk.white(research.topic));
    console.log(chalk.yellow('Summary:'), chalk.white(research.summary));
    console.log();

    if (research.findings.length > 0) {
      console.log(chalk.yellow('Key Findings:'));
      research.findings.forEach((finding, index) => {
        console.log(chalk.white(`  ${index + 1}. ${finding}`));
      });
      console.log();
    }

    if (research.sources.length > 0) {
      console.log(chalk.yellow('Sources:'));
      research.sources.forEach((source, index) => {
        console.log(chalk.gray(`  ${index + 1}. ${source.title} - ${source.url}`));
      });
      console.log();
    }

    if (options.save) {
      console.log(chalk.blue('💾 Saving research to knowledge base...'));
      const kb = new KnowledgeBase();
      await kb.saveResearch(research);
      console.log(chalk.green('✓ Research saved to knowledge base'));
    }
  } catch (error) {
    console.error(chalk.red('✗ Research failed:'), error);
    process.exit(1);
  }
}
