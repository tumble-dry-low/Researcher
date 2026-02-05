import chalk from 'chalk';
import { TreeResearchAgent } from '../research/tree-research-agent.js';
import { StructuredResearchAgent, ResearchPosition } from '../research/structured-research-agent.js';
import { KnowledgeBase } from '../knowledge-base/knowledge-base.js';

interface TreeResearchOptions {
  depth: string;
  maxDepth: string;
  save: boolean;
  type: 'yesno' | 'options' | 'custom';
  options?: string;
}

export async function treeResearchCommand(
  question: string,
  options: TreeResearchOptions
): Promise<void> {
  const researchDepth = parseInt(options.depth, 10);
  const maxDepth = parseInt(options.maxDepth, 10);

  console.log(chalk.blue('🌳 Starting tree-based research on:'), chalk.cyan(question));
  console.log(chalk.gray('  Research depth:'), researchDepth);
  console.log(chalk.gray('  Max tree depth:'), maxDepth);
  console.log(chalk.gray('  Type:'), options.type);
  console.log();

  try {
    const agent = new TreeResearchAgent();
    let positions: ResearchPosition[];
    const context = '';

    // Generate initial positions based on type
    if (options.type === 'yesno') {
      positions = StructuredResearchAgent.createYesNoPositions(question, context);
      console.log(chalk.yellow('📋 Initial positions:'), 'Yes, No');
    } else if (options.type === 'options' && options.options) {
      const optionsList = options.options.split(',').map(o => o.trim());
      positions = StructuredResearchAgent.createMultiOptionPositions(optionsList, context);
      console.log(chalk.yellow('📋 Initial pro/con for options:'), optionsList.join(', '));
    } else if (options.type === 'custom' && options.options) {
      const customPositions = options.options.split(',').map(p => p.trim());
      positions = customPositions.map(pos => {
        const [position, stance, description] = pos.split(':').map(s => s.trim());
        return {
          position,
          stance: (stance as 'pro' | 'con' | 'neutral' | 'analysis') || 'analysis',
          description: description || position,
        };
      });
      console.log(chalk.yellow('📋 Initial custom positions:'), positions.length);
    } else {
      console.error(chalk.red('✗ Invalid type or missing options'));
      console.log(chalk.gray('\nUsage examples:'));
      console.log(chalk.gray('  --type yesno'));
      console.log(chalk.gray('  --type options --options "option1,option2,option3"'));
      console.log(chalk.gray('  --type custom --options "pos1:pro:desc1,pos2:con:desc2"'));
      process.exit(1);
    }

    console.log();

    const result = await agent.conductTreeResearch(
      question,
      context,
      positions,
      maxDepth,
      researchDepth
    );

    console.log(chalk.green('\n✓ Tree research complete!\n'));

    // Display summary statistics
    console.log(chalk.yellow('📊 Statistics:'));
    console.log(chalk.white(`  Total nodes explored: ${result.totalNodes}`));
    console.log(chalk.white(`  Maximum depth reached: ${result.maxDepthReached}`));
    console.log(chalk.white(`  Conclusive nodes: ${result.conclusiveNodes}`));
    console.log(chalk.white(`  Open questions: ${result.openQuestions.length}`));
    console.log();

    // Display tree structure
    console.log(chalk.yellow('🌳 Research Tree:'));
    displayNode(result.tree, '');

    console.log();

    // Display open questions
    if (result.openQuestions.length > 0) {
      console.log(chalk.yellow('❓ Open Questions:'));
      result.openQuestions.slice(0, 5).forEach((q, i) => {
        console.log(chalk.white(`  ${i + 1}. ${q}`));
      });
      if (result.openQuestions.length > 5) {
        console.log(chalk.gray(`  ... and ${result.openQuestions.length - 5} more`));
      }
      console.log();
    }

    if (options.save) {
      console.log(chalk.blue('💾 Saving tree research to knowledge base...'));
      const kb = new KnowledgeBase();
      const summary = agent.generateTreeSummary(result);
      await kb.saveTreeResearch(result, summary);
      console.log(chalk.green('✓ Tree research saved to knowledge base'));
    }
  } catch (error) {
    console.error(chalk.red('✗ Tree research failed:'), error);
    process.exit(1);
  }
}

function displayNode(node: any, indent: string): void {
  const statusIcon = node.status === 'completed' ? '✓' : 
                     node.status === 'max_depth' ? '⚠' :
                     node.status === 'pruned' ? '✗' : '○';

  console.log(chalk.cyan(`${indent}${statusIcon} [Depth ${node.depth}] ${node.question}`));

  if (node.conclusive) {
    console.log(chalk.green(`${indent}  → Conclusive: ${node.correctPosition}`));
  }

  if (node.result) {
    const strongCount = node.result.positions.filter((p: any) => p.strength === 'strong').length;
    const moderateCount = node.result.positions.filter((p: any) => p.strength === 'moderate').length;
    const weakCount = node.result.positions.filter((p: any) => p.strength === 'weak').length;

    console.log(chalk.gray(`${indent}  Positions: ${strongCount} strong, ${moderateCount} moderate, ${weakCount} weak`));
  }

  if (node.status === 'max_depth') {
    if (node.openQuestions && node.openQuestions.length > 0) {
      console.log(chalk.gray(`${indent}  Open questions: ${node.openQuestions.length}`));
    }
    if (node.potentialAnswers && node.potentialAnswers.length > 0) {
      console.log(chalk.gray(`${indent}  Potential answers: ${node.potentialAnswers.length}`));
    }
  }

  if (node.children && node.children.length > 0) {
    node.children.forEach((child: any) => {
      displayNode(child, indent + '  ');
    });
  }
}
