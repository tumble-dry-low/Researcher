import chalk from 'chalk';
import { StructuredResearchAgent, ResearchPosition } from '../research/structured-research-agent.js';
import { KnowledgeBase } from '../knowledge-base/knowledge-base.js';

interface StructuredResearchOptions {
  depth: string;
  save: boolean;
  type: 'yesno' | 'options' | 'custom';
  options?: string;
}

export async function structuredResearchCommand(
  question: string,
  options: StructuredResearchOptions
): Promise<void> {
  const depth = parseInt(options.depth, 10);

  console.log(chalk.blue('🔬 Starting structured research on:'), chalk.cyan(question));
  console.log(chalk.gray('  Depth level:'), depth);
  console.log(chalk.gray('  Type:'), options.type);
  console.log();

  try {
    const agent = new StructuredResearchAgent();
    let positions: ResearchPosition[];
    let context = '';

    // Generate positions based on type
    if (options.type === 'yesno') {
      positions = StructuredResearchAgent.createYesNoPositions(question, context);
      console.log(chalk.yellow('📋 Researching positions:'), 'Yes, No');
    } else if (options.type === 'options' && options.options) {
      const optionsList = options.options.split(',').map(o => o.trim());
      positions = StructuredResearchAgent.createMultiOptionPositions(optionsList, context);
      console.log(chalk.yellow('📋 Researching pro/con for options:'), optionsList.join(', '));
    } else if (options.type === 'custom' && options.options) {
      // Custom positions format: "position1:pro:description1,position2:con:description2"
      const customPositions = options.options.split(',').map(p => p.trim());
      positions = customPositions.map(pos => {
        const [position, stance, description] = pos.split(':').map(s => s.trim());
        return {
          position,
          stance: (stance as 'pro' | 'con' | 'neutral' | 'analysis') || 'analysis',
          description: description || position,
        };
      });
      console.log(chalk.yellow('📋 Researching custom positions:'), positions.length);
    } else {
      console.error(chalk.red('✗ Invalid type or missing options'));
      console.log(chalk.gray('\nUsage examples:'));
      console.log(chalk.gray('  --type yesno'));
      console.log(chalk.gray('  --type options --options "option1,option2,option3"'));
      console.log(chalk.gray('  --type custom --options "pos1:pro:desc1,pos2:con:desc2"'));
      process.exit(1);
    }

    console.log();

    const result = await agent.conductStructuredResearch(question, context, positions, depth);

    console.log(chalk.green('\n✓ Structured research complete!\n'));

    // Display results
    console.log(chalk.yellow('Question:'), chalk.white(result.question));
    console.log(chalk.yellow('Summary:'), chalk.white(result.summary));
    console.log();

    // Display each position
    result.positions.forEach((pos, index) => {
      console.log(chalk.cyan(`\n[${index + 1}] ${pos.position} (${pos.stance})`));
      console.log(chalk.gray(`  Strength: ${pos.strength}`));
      console.log(chalk.gray(`  Sources: ${pos.sources.length}`));
      
      if (pos.arguments.length > 0) {
        console.log(chalk.white('  Arguments:'));
        pos.arguments.forEach((arg, i) => {
          if (i < 3) { // Show first 3 arguments
            console.log(chalk.white(`    ${i + 1}. ${arg}`));
          }
        });
        if (pos.arguments.length > 3) {
          console.log(chalk.gray(`    ... and ${pos.arguments.length - 3} more`));
        }
      }

      if (pos.sources.length > 0) {
        console.log(chalk.white('  Key Sources:'));
        pos.sources.slice(0, 3).forEach((source, i) => {
          console.log(chalk.gray(`    ${i + 1}. ${source.title}`));
          console.log(chalk.gray(`       ${source.url}`));
        });
        if (pos.sources.length > 3) {
          console.log(chalk.gray(`    ... and ${pos.sources.length - 3} more sources`));
        }
      }
    });

    console.log();

    if (options.save) {
      console.log(chalk.blue('💾 Saving structured research to knowledge base...'));
      const kb = new KnowledgeBase();
      await kb.saveStructuredResearch(result);
      console.log(chalk.green('✓ Structured research saved to knowledge base'));
    }
  } catch (error) {
    console.error(chalk.red('✗ Structured research failed:'), error);
    process.exit(1);
  }
}
