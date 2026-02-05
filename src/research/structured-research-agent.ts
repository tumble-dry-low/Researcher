import { WebSearcher, SearchResult } from './web-searcher.js';

/**
 * Represents a position/perspective in a debate or analysis
 */
export interface ResearchPosition {
  position: string;
  stance: 'pro' | 'con' | 'neutral' | 'analysis';
  description: string;
}

/**
 * Result from researching a specific position
 */
export interface PositionResearchResult {
  position: string;
  stance: 'pro' | 'con' | 'neutral' | 'analysis';
  arguments: string[];
  sources: SearchResult[];
  strength: 'strong' | 'moderate' | 'weak';
  createdAt: string;
}

/**
 * Complete structured research result with multiple perspectives
 */
export interface StructuredResearchResult {
  question: string;
  context: string;
  positions: PositionResearchResult[];
  summary: string;
  createdAt: string;
}

/**
 * StructuredResearchAgent conducts research from multiple perspectives
 * Each perspective is researched in parallel by independent agents
 * All findings must be backed by sources
 */
export class StructuredResearchAgent {
  private searcher: WebSearcher;

  constructor() {
    this.searcher = new WebSearcher();
  }

  /**
   * Conduct structured research on a question with multiple positions
   * Each position is researched in parallel to make the strongest case
   * @param question - The question or topic to research
   * @param context - Shared context for all positions
   * @param positions - Array of positions/perspectives to research
   * @param depth - Research depth (1-5)
   * @returns Structured research results
   */
  async conductStructuredResearch(
    question: string,
    context: string,
    positions: ResearchPosition[],
    depth: number = 3
  ): Promise<StructuredResearchResult> {
    console.log(`[StructuredResearchAgent] Starting structured research on "${question}"`);
    console.log(`[StructuredResearchAgent] Researching ${positions.length} positions in parallel`);

    // Research all positions in parallel
    const positionPromises = positions.map(position =>
      this.researchPosition(question, context, position, depth)
    );

    const positionResults = await Promise.all(positionPromises);

    // Filter out positions with no sources (inadmissible)
    const admissibleResults = positionResults.filter(result => result.sources.length > 0);

    if (admissibleResults.length < positionResults.length) {
      console.log(
        `[StructuredResearchAgent] ${positionResults.length - admissibleResults.length} positions had no sources and were excluded`
      );
    }

    const summary = this.generateStructuredSummary(question, admissibleResults);

    return {
      question,
      context,
      positions: admissibleResults,
      summary,
      createdAt: new Date().toISOString(),
    };
  }

  /**
   * Research a specific position to make the strongest case
   * @param question - The overall question
   * @param context - Shared context
   * @param position - The position to research
   * @param depth - Research depth
   * @returns Position research result
   */
  private async researchPosition(
    question: string,
    context: string,
    position: ResearchPosition,
    depth: number
  ): Promise<PositionResearchResult> {
    console.log(`[StructuredResearchAgent] Researching position: ${position.position} (${position.stance})`);

    // Generate queries tailored to this position
    const queries = this.generatePositionQueries(question, position, depth);

    // Perform searches
    const sources = await this.searcher.deepSearch(queries);

    // Extract arguments from sources
    const args = this.extractArguments(sources, position, depth);

    // Assess strength based on number of sources and quality
    const strength = this.assessStrength(sources, args);

    return {
      position: position.position,
      stance: position.stance,
      arguments: args,
      sources,
      strength,
      createdAt: new Date().toISOString(),
    };
  }

  /**
   * Generate queries tailored to a specific position
   */
  private generatePositionQueries(
    question: string,
    position: ResearchPosition,
    depth: number
  ): string[] {
    const queries: string[] = [];

    // Base query with position
    queries.push(`${question} ${position.position}`);

    // Stance-specific queries
    if (position.stance === 'pro') {
      queries.push(`${position.position} benefits`);
      queries.push(`${position.position} advantages`);
      queries.push(`why ${position.position}`);
      queries.push(`${position.position} evidence`);
      queries.push(`${position.position} research`);
    } else if (position.stance === 'con') {
      queries.push(`${position.position} drawbacks`);
      queries.push(`${position.position} disadvantages`);
      queries.push(`problems with ${position.position}`);
      queries.push(`${position.position} risks`);
      queries.push(`${position.position} criticism`);
    } else if (position.stance === 'analysis') {
      queries.push(`${position.position} analysis`);
      queries.push(`${position.position} comparison`);
      queries.push(`${position.position} evaluation`);
      queries.push(`${position.position} pros and cons`);
    }

    // Add context-aware queries
    queries.push(`${position.description}`);
    queries.push(`${position.description} evidence`);

    // Return based on depth
    const numQueries = Math.min(3 + depth, queries.length);
    return queries.slice(0, numQueries);
  }

  /**
   * Extract arguments from sources for a position
   */
  private extractArguments(
    sources: SearchResult[],
    position: ResearchPosition,
    depth: number
  ): string[] {
    const args: string[] = [];

    if (sources.length === 0) {
      return args;
    }

    // Build arguments from source snippets
    args.push(`Position: ${position.description}`);

    // Extract key points from sources
    sources.forEach((source, index) => {
      if (source.snippet && index < depth * 2) {
        args.push(`${source.snippet} (Source: ${source.title})`);
      }
    });

    return args;
  }

  /**
   * Assess the strength of a position based on sources
   */
  private assessStrength(sources: SearchResult[], args: string[]): 'strong' | 'moderate' | 'weak' {
    if (sources.length === 0) {
      return 'weak';
    }

    if (sources.length >= 5 && args.length >= 5) {
      return 'strong';
    }

    if (sources.length >= 3 && args.length >= 3) {
      return 'moderate';
    }

    return 'weak';
  }

  /**
   * Generate a summary of structured research
   */
  private generateStructuredSummary(
    question: string,
    positions: PositionResearchResult[]
  ): string {
    if (positions.length === 0) {
      return `No admissible positions found for "${question}". All positions must have supporting sources.`;
    }

    const strongPositions = positions.filter(p => p.strength === 'strong');
    const moderatePositions = positions.filter(p => p.strength === 'moderate');
    const weakPositions = positions.filter(p => p.strength === 'weak');

    let summary = `Structured research on "${question}" completed with ${positions.length} positions:\n`;

    if (strongPositions.length > 0) {
      summary += `\n- ${strongPositions.length} strong position(s) with substantial evidence`;
    }
    if (moderatePositions.length > 0) {
      summary += `\n- ${moderatePositions.length} moderate position(s) with supporting evidence`;
    }
    if (weakPositions.length > 0) {
      summary += `\n- ${weakPositions.length} weak position(s) with limited evidence`;
    }

    summary += `\n\nAll positions are backed by sources and represent the strongest available case.`;

    return summary;
  }

  /**
   * Helper method to create pro/con positions for an option
   * @param option - The option to analyze
   * @param context - Context about the option
   * @returns Array of pro and con positions
   */
  static createProConPositions(option: string, context: string = ''): ResearchPosition[] {
    return [
      {
        position: `Pro: ${option}`,
        stance: 'pro',
        description: `Arguments in favor of ${option}${context ? ` considering ${context}` : ''}`,
      },
      {
        position: `Con: ${option}`,
        stance: 'con',
        description: `Arguments against ${option}${context ? ` considering ${context}` : ''}`,
      },
    ];
  }

  /**
   * Helper method to create pro/con positions for multiple options
   * @param options - Array of options to analyze
   * @param context - Shared context
   * @returns Array of all pro/con positions
   */
  static createMultiOptionPositions(options: string[], context: string = ''): ResearchPosition[] {
    const positions: ResearchPosition[] = [];

    for (const option of options) {
      positions.push(...this.createProConPositions(option, context));
    }

    return positions;
  }

  /**
   * Helper method to create positions for a yes/no question
   * @param question - The yes/no question
   * @param context - Context for the question
   * @returns Array of yes/no positions
   */
  static createYesNoPositions(question: string, context: string = ''): ResearchPosition[] {
    return [
      {
        position: 'Yes',
        stance: 'pro',
        description: `Arguments supporting "yes" to: ${question}${context ? ` in context of ${context}` : ''}`,
      },
      {
        position: 'No',
        stance: 'con',
        description: `Arguments supporting "no" to: ${question}${context ? ` in context of ${context}` : ''}`,
      },
    ];
  }
}
