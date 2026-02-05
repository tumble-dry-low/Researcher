import { StructuredResearchAgent, ResearchPosition, StructuredResearchResult } from './structured-research-agent.js';

/**
 * Represents a node in the research tree
 */
export interface ResearchNode {
  question: string;
  context: string;
  depth: number;
  maxDepth: number;
  positions: ResearchPosition[];
  result?: StructuredResearchResult;
  children?: ResearchNode[];
  status: 'pending' | 'researching' | 'completed' | 'pruned' | 'max_depth';
  conclusive?: boolean; // If true, one answer is clearly correct
  correctPosition?: string; // The position determined to be correct
  openQuestions?: string[]; // Open questions at max depth or unresolved
  potentialAnswers?: string[]; // Potential answers for open questions
  fileName?: string; // Markdown filename for this node
  parentChain?: string[]; // Array of parent questions leading to this node
}

/**
 * Result from tree-based research
 */
export interface TreeResearchResult {
  rootQuestion: string;
  tree: ResearchNode;
  totalNodes: number;
  maxDepthReached: number;
  conclusiveNodes: number;
  openQuestions: string[];
  createdAt: string;
}

/**
 * TreeResearchAgent conducts hierarchical research following a tree structure
 * Each node represents a question with multiple alternatives to explore
 * Branches can be pruned when one answer is determined to be correct
 * Depth is limited to prevent infinite recursion
 */
export class TreeResearchAgent {
  private structuredAgent: StructuredResearchAgent;
  private readonly MAX_FOLLOW_UP_QUESTIONS = 2;
  private readonly MAX_FOLLOW_UP_ARGUMENT_LENGTH = 100;
  private readonly MAX_POTENTIAL_ANSWER_LENGTH = 150;

  constructor() {
    this.structuredAgent = new StructuredResearchAgent();
  }

  /**
   * Conduct tree-based research starting from a root question
   * @param rootQuestion - The initial question to research
   * @param context - Initial context
   * @param positions - Initial positions to explore
   * @param maxDepth - Maximum depth of the tree
   * @param researchDepth - Research depth for each node (1-5)
   * @returns Tree research result
   */
  async conductTreeResearch(
    rootQuestion: string,
    context: string,
    positions: ResearchPosition[],
    maxDepth: number = 3,
    researchDepth: number = 3
  ): Promise<TreeResearchResult> {
    console.log(`[TreeResearchAgent] Starting tree research on "${rootQuestion}"`);
    console.log(`[TreeResearchAgent] Max depth: ${maxDepth}, Research depth: ${researchDepth}`);

    const rootNode: ResearchNode = {
      question: rootQuestion,
      context,
      depth: 0,
      maxDepth,
      positions,
      status: 'pending',
    };

    await this.exploreNode(rootNode, researchDepth);

    const stats = this.calculateStatistics(rootNode);

    return {
      rootQuestion,
      tree: rootNode,
      totalNodes: stats.totalNodes,
      maxDepthReached: stats.maxDepthReached,
      conclusiveNodes: stats.conclusiveNodes,
      openQuestions: stats.openQuestions,
      createdAt: new Date().toISOString(),
    };
  }

  /**
   * Explore a node in the research tree
   */
  private async exploreNode(node: ResearchNode, researchDepth: number, parentChain: string[] = []): Promise<void> {
    console.log(`[TreeResearchAgent] Exploring node at depth ${node.depth}: "${node.question}"`);

    node.status = 'researching';
    node.parentChain = parentChain;

    // Build full context from parent chain
    if (parentChain.length > 0) {
      const currentContext = node.context || '';
      node.context = `Previous questions and branches:\n${parentChain.map((q, i) => `${i + 1}. ${q}`).join('\n')}\n\nCurrent context: ${currentContext}`;
    }

    // Check if we've reached max depth
    if (node.depth >= node.maxDepth) {
      console.log(`[TreeResearchAgent] Max depth reached at node: "${node.question}"`);
      node.status = 'max_depth';
      await this.handleMaxDepthNode(node, researchDepth);
      return;
    }

    // Conduct structured research on this node
    const result = await this.structuredAgent.conductStructuredResearch(
      node.question,
      node.context,
      node.positions,
      researchDepth
    );

    node.result = result;

    // Analyze results to determine next steps
    const analysis = this.analyzeResults(result);

    if (analysis.conclusive) {
      // One position is clearly correct
      console.log(`[TreeResearchAgent] Conclusive result found: ${analysis.correctPosition}`);
      node.conclusive = true;
      node.correctPosition = analysis.correctPosition;
      node.status = 'completed';
      // Don't explore further branches
      return;
    }

    // Check if we should continue exploring
    if (node.depth + 1 < node.maxDepth && analysis.followUpQuestions.length > 0) {
      console.log(`[TreeResearchAgent] Generating ${analysis.followUpQuestions.length} follow-up questions`);

      node.children = [];

      // Build parent chain for children
      const childParentChain = [...parentChain, node.question];

      // Explore follow-up questions in parallel
      const childPromises = analysis.followUpQuestions.map(async (followUp) => {
        const childNode: ResearchNode = {
          question: followUp.question,
          context: node.context,
          depth: node.depth + 1,
          maxDepth: node.maxDepth,
          positions: followUp.positions,
          status: 'pending',
        };

        await this.exploreNode(childNode, researchDepth, childParentChain);
        return childNode;
      });

      node.children = await Promise.all(childPromises);
    }

    node.status = 'completed';
  }

  /**
   * Handle nodes that have reached maximum depth
   */
  private async handleMaxDepthNode(node: ResearchNode, researchDepth: number): Promise<void> {
    // Still conduct research but don't branch further
    const result = await this.structuredAgent.conductStructuredResearch(
      node.question,
      node.context,
      node.positions,
      researchDepth
    );

    node.result = result;

    // Extract open questions and potential answers
    node.openQuestions = this.extractOpenQuestions(result);
    node.potentialAnswers = this.extractPotentialAnswers(result);

    console.log(`[TreeResearchAgent] At max depth - Open questions: ${node.openQuestions.length}, Potential answers: ${node.potentialAnswers.length}`);
  }

  /**
   * Analyze research results to determine if conclusive and generate follow-up questions
   */
  private analyzeResults(result: StructuredResearchResult): {
    conclusive: boolean;
    correctPosition?: string;
    followUpQuestions: Array<{ question: string; positions: ResearchPosition[] }>;
  } {
    // Simple heuristic: if one position is "strong" and others are "weak", consider it conclusive
    const strongPositions = result.positions.filter(p => p.strength === 'strong');
    const weakPositions = result.positions.filter(p => p.strength === 'weak');

    const conclusive = strongPositions.length === 1 && weakPositions.length === result.positions.length - 1;

    const followUpQuestions: Array<{ question: string; positions: ResearchPosition[] }> = [];

    if (!conclusive && result.positions.length > 0) {
      // Generate follow-up questions based on findings
      // For now, we'll generate questions for positions that need more research
      const moderatePositions = result.positions.filter(p => p.strength === 'moderate');

      moderatePositions.forEach(position => {
        if (position.arguments.length > 1) {
          // Extract a key argument as a follow-up question
          const keyArgument = position.arguments[1]; // Skip the "Position:" description
          if (keyArgument && !keyArgument.startsWith('Position:')) {
            const followUpQuestion = `Is this claim accurate: ${keyArgument.substring(0, this.MAX_FOLLOW_UP_ARGUMENT_LENGTH)}...?`;

            followUpQuestions.push({
              question: followUpQuestion,
              positions: StructuredResearchAgent.createYesNoPositions(followUpQuestion),
            });
          }
        }
      });
    }

    return {
      conclusive,
      correctPosition: conclusive ? strongPositions[0]?.position : undefined,
      followUpQuestions: followUpQuestions.slice(0, this.MAX_FOLLOW_UP_QUESTIONS),
    };
  }

  /**
   * Extract open questions from research results
   */
  private extractOpenQuestions(result: StructuredResearchResult): string[] {
    const openQuestions: string[] = [];

    // Extract questions from positions that have weak or moderate strength
    result.positions.forEach(position => {
      if (position.strength !== 'strong') {
        openQuestions.push(`What additional evidence supports or refutes: ${position.position}?`);
      }
    });

    return openQuestions;
  }

  /**
   * Extract potential answers from research results
   */
  private extractPotentialAnswers(result: StructuredResearchResult): string[] {
    const potentialAnswers: string[] = [];

    result.positions.forEach(position => {
      if (position.arguments.length > 0) {
        // Take the first non-description argument as a potential answer
        const relevantArgs = position.arguments.filter(arg => !arg.startsWith('Position:'));
        if (relevantArgs.length > 0) {
          potentialAnswers.push(`${position.position}: ${relevantArgs[0].substring(0, this.MAX_POTENTIAL_ANSWER_LENGTH)}...`);
        }
      }
    });

    return potentialAnswers;
  }

  /**
   * Calculate statistics about the research tree
   */
  private calculateStatistics(node: ResearchNode): {
    totalNodes: number;
    maxDepthReached: number;
    conclusiveNodes: number;
    openQuestions: string[];
  } {
    let totalNodes = 1;
    let maxDepthReached = node.depth;
    let conclusiveNodes = node.conclusive ? 1 : 0;
    const openQuestions: string[] = [...(node.openQuestions || [])];

    if (node.children) {
      node.children.forEach(child => {
        const childStats = this.calculateStatistics(child);
        totalNodes += childStats.totalNodes;
        maxDepthReached = Math.max(maxDepthReached, childStats.maxDepthReached);
        conclusiveNodes += childStats.conclusiveNodes;
        openQuestions.push(...childStats.openQuestions);
      });
    }

    return {
      totalNodes,
      maxDepthReached,
      conclusiveNodes,
      openQuestions,
    };
  }

  /**
   * Generate a text summary of the research tree
   */
  generateTreeSummary(result: TreeResearchResult): string {
    let summary = `# Tree Research: ${result.rootQuestion}\n\n`;
    summary += `**Statistics:**\n`;
    summary += `- Total nodes explored: ${result.totalNodes}\n`;
    summary += `- Maximum depth reached: ${result.maxDepthReached}\n`;
    summary += `- Conclusive nodes: ${result.conclusiveNodes}\n`;
    summary += `- Open questions: ${result.openQuestions.length}\n\n`;

    summary += this.generateNodeSummary(result.tree, '');

    if (result.openQuestions.length > 0) {
      summary += `\n## Open Questions\n\n`;
      result.openQuestions.forEach((q, i) => {
        summary += `${i + 1}. ${q}\n`;
      });
    }

    return summary;
  }

  /**
   * Generate summary for a node and its children recursively
   */
  private generateNodeSummary(node: ResearchNode, indent: string): string {
    let summary = `${indent}## ${node.question}\n\n`;
    summary += `${indent}**Depth:** ${node.depth}, **Status:** ${node.status}\n\n`;

    if (node.conclusive) {
      summary += `${indent}✓ **Conclusive Result:** ${node.correctPosition}\n\n`;
    }

    if (node.result) {
      summary += `${indent}**Positions researched:** ${node.result.positions.length}\n`;
      node.result.positions.forEach(pos => {
        summary += `${indent}- ${pos.position} (${pos.stance}): ${pos.strength} (${pos.sources.length} sources)\n`;
      });
      summary += `\n`;
    }

    if (node.status === 'max_depth' && node.openQuestions) {
      summary += `${indent}**Open questions at max depth:**\n`;
      node.openQuestions.forEach(q => {
        summary += `${indent}- ${q}\n`;
      });
      summary += `\n`;

      if (node.potentialAnswers) {
        summary += `${indent}**Potential answers:**\n`;
        node.potentialAnswers.forEach(a => {
          summary += `${indent}- ${a}\n`;
        });
        summary += `\n`;
      }
    }

    if (node.children && node.children.length > 0) {
      summary += `${indent}**Follow-up research (${node.children.length} branches):**\n\n`;
      node.children.forEach(child => {
        summary += this.generateNodeSummary(child, indent + '  ');
      });
    }

    return summary;
  }
}
