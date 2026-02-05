import fs from 'fs-extra';
import path from 'path';
import matter from 'gray-matter';
import MarkdownIt from 'markdown-it';
import { SearchResult } from '../research/web-searcher.js';
import { ResearchResult } from '../research/research-agent.js';
import { StructuredResearchResult } from '../research/structured-research-agent.js';
import { TreeResearchResult } from '../research/tree-research-agent.js';

export interface KnowledgeEntry {
  title: string;
  path: string;
  content: string;
  tags?: string[];
  links?: string[];
  createdAt?: string;
  updatedAt?: string;
}

export interface SearchResultEntry {
  title: string;
  path: string;
  excerpt?: string;
  score?: number;
}

/**
 * KnowledgeBase manages a markdown-based knowledge base with linking
 */
export class KnowledgeBase {
  private basePath: string;
  private entriesPath: string;
  private md: MarkdownIt;

  constructor(basePath: string = './knowledge-base') {
    this.basePath = path.resolve(basePath);
    this.entriesPath = path.join(this.basePath, 'entries');
    this.md = new MarkdownIt();
  }

  /**
   * Ensure knowledge base exists
   */
  private async ensureExists(): Promise<void> {
    const configPath = path.join(this.basePath, 'config.json');
    if (!(await fs.pathExists(configPath))) {
      throw new Error(`Knowledge base not initialized. Run 'researcher init' first.`);
    }
  }

  /**
   * List all entries in the knowledge base
   */
  async listEntries(): Promise<KnowledgeEntry[]> {
    await this.ensureExists();

    const entries: KnowledgeEntry[] = [];
    const files = await fs.readdir(this.entriesPath);

    for (const file of files) {
      if (path.extname(file) === '.md') {
        const filePath = path.join(this.entriesPath, file);
        const content = await fs.readFile(filePath, 'utf-8');
        const parsed = matter(content);

        entries.push({
          title: parsed.data.title || path.basename(file, '.md'),
          path: file,
          content: parsed.content,
          tags: parsed.data.tags || [],
          createdAt: parsed.data.createdAt,
          updatedAt: parsed.data.updatedAt,
        });
      }
    }

    return entries;
  }

  /**
   * Get a specific entry
   */
  async getEntry(entryName: string): Promise<KnowledgeEntry | null> {
    await this.ensureExists();

    // Normalize entry name
    const fileName = entryName.endsWith('.md') ? entryName : `${entryName}.md`;
    const filePath = path.join(this.entriesPath, fileName);

    if (!(await fs.pathExists(filePath))) {
      return null;
    }

    const content = await fs.readFile(filePath, 'utf-8');
    const parsed = matter(content);

    // Extract links from content
    const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
    const links: string[] = [];
    let match;
    while ((match = linkRegex.exec(parsed.content)) !== null) {
      if (match[2].endsWith('.md')) {
        links.push(match[2]);
      }
    }

    return {
      title: parsed.data.title || path.basename(fileName, '.md'),
      path: fileName,
      content: parsed.content,
      tags: parsed.data.tags || [],
      links,
      createdAt: parsed.data.createdAt,
      updatedAt: parsed.data.updatedAt,
    };
  }

  /**
   * Save search results to knowledge base
   */
  async saveSearchResults(query: string, results: SearchResult[]): Promise<void> {
    await this.ensureExists();

    const slug = this.slugify(query);
    const fileName = `search-${slug}.md`;
    const filePath = path.join(this.entriesPath, fileName);

    const frontmatter = {
      title: `Search: ${query}`,
      tags: ['search', 'web-search'],
      query,
      createdAt: new Date().toISOString(),
    };

    let content = '# Search Results\n\n';
    content += `Query: **${query}**\n\n`;
    content += `Found ${results.length} results:\n\n`;

    results.forEach((result, index) => {
      content += `## ${index + 1}. ${result.title}\n\n`;
      content += `**URL:** ${result.url}\n\n`;
      if (result.snippet) {
        content += `${result.snippet}\n\n`;
      }
      content += `---\n\n`;
    });

    const fileContent = matter.stringify(content, frontmatter);
    await fs.writeFile(filePath, fileContent);
  }

  /**
   * Save research results to knowledge base
   */
  async saveResearch(research: ResearchResult): Promise<void> {
    await this.ensureExists();

    const slug = this.slugify(research.topic);
    const fileName = `research-${slug}.md`;
    const filePath = path.join(this.entriesPath, fileName);

    const frontmatter = {
      title: research.topic,
      tags: ['research', 'deep-research'],
      depth: research.depth,
      createdAt: research.createdAt,
    };

    let content = `# ${research.topic}\n\n`;
    content += `## Summary\n\n${research.summary}\n\n`;

    if (research.findings.length > 0) {
      content += `## Key Findings\n\n`;
      research.findings.forEach((finding, index) => {
        content += `${index + 1}. ${finding}\n`;
      });
      content += '\n';
    }

    if (research.sources.length > 0) {
      content += `## Sources\n\n`;
      research.sources.forEach((source, index) => {
        content += `${index + 1}. [${source.title}](${source.url})\n`;
        if (source.snippet) {
          content += `   - ${source.snippet}\n`;
        }
      });
      content += '\n';
    }

    if (research.relatedTopics && research.relatedTopics.length > 0) {
      content += `## Related Topics\n\n`;
      research.relatedTopics.forEach((topic) => {
        content += `- ${topic}\n`;
      });
      content += '\n';
    }

    const fileContent = matter.stringify(content, frontmatter);
    await fs.writeFile(filePath, fileContent);
  }

  /**
   * Save structured research results to knowledge base
   */
  async saveStructuredResearch(research: StructuredResearchResult): Promise<void> {
    await this.ensureExists();

    const slug = this.slugify(research.question);
    const fileName = `structured-${slug}.md`;
    const filePath = path.join(this.entriesPath, fileName);

    const frontmatter = {
      title: `Structured Research: ${research.question}`,
      tags: ['structured-research', 'debate', 'analysis'],
      question: research.question,
      positionCount: research.positions.length,
      createdAt: research.createdAt,
    };

    let content = `# Structured Research: ${research.question}\n\n`;
    
    if (research.context) {
      content += `## Context\n\n${research.context}\n\n`;
    }

    content += `## Summary\n\n${research.summary}\n\n`;

    content += `## Positions (${research.positions.length})\n\n`;

    research.positions.forEach((position, index) => {
      content += `### ${index + 1}. ${position.position} (${position.stance.toUpperCase()})\n\n`;
      content += `**Strength**: ${position.strength}\n\n`;
      content += `**Sources**: ${position.sources.length}\n\n`;

      if (position.arguments.length > 0) {
        content += `#### Arguments\n\n`;
        position.arguments.forEach((arg, i) => {
          content += `${i + 1}. ${arg}\n`;
        });
        content += '\n';
      }

      if (position.sources.length > 0) {
        content += `#### Sources\n\n`;
        position.sources.forEach((source, i) => {
          content += `${i + 1}. [${source.title}](${source.url})\n`;
          if (source.snippet) {
            content += `   - ${source.snippet}\n`;
          }
        });
        content += '\n';
      }

      content += `---\n\n`;
    });

    const fileContent = matter.stringify(content, frontmatter);
    await fs.writeFile(filePath, fileContent);
  }

  /**
   * Save tree research results to knowledge base
   */
  async saveTreeResearch(research: TreeResearchResult, summary: string): Promise<void> {
    await this.ensureExists();

    const slug = this.slugify(research.rootQuestion);
    const fileName = `tree-${slug}.md`;
    const filePath = path.join(this.entriesPath, fileName);

    const frontmatter = {
      title: `Tree Research: ${research.rootQuestion}`,
      tags: ['tree-research', 'hierarchical', 'analysis'],
      rootQuestion: research.rootQuestion,
      totalNodes: research.totalNodes,
      maxDepthReached: research.maxDepthReached,
      conclusiveNodes: research.conclusiveNodes,
      openQuestionsCount: research.openQuestions.length,
      createdAt: research.createdAt,
    };

    // Use the generated summary
    const content = summary;

    const fileContent = matter.stringify(content, frontmatter);
    await fs.writeFile(filePath, fileContent);
  }

  /**
   * Link two entries together
   */
  async linkEntries(entry1Name: string, entry2Name: string): Promise<void> {
    await this.ensureExists();

    const entry1 = await this.getEntry(entry1Name);
    const entry2 = await this.getEntry(entry2Name);

    if (!entry1 || !entry2) {
      throw new Error('One or both entries not found');
    }

    // Check if link already exists using markdown link pattern
    const entry2FileName = entry2.path;
    // Escape special regex characters to prevent ReDoS
    const escapedFileName = entry2FileName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const linkPattern = new RegExp(`\\[([^\\]]+)\\]\\(\\.\\/${escapedFileName}\\)`);
    
    if (!linkPattern.test(entry1.content)) {
      // Read original file to preserve frontmatter
      const filePath = path.join(this.entriesPath, entry1.path);
      const originalContent = await fs.readFile(filePath, 'utf-8');
      const parsed = matter(originalContent);
      
      // Append link to content
      const updatedContent = parsed.content + `\n\n## Related\n\n- [${entry2.title}](./${entry2FileName})\n`;
      
      // Write back with preserved frontmatter
      const fileContent = matter.stringify(updatedContent, parsed.data);
      await fs.writeFile(filePath, fileContent);
    }
  }

  /**
   * Update the knowledge base index
   */
  async updateIndex(): Promise<void> {
    await this.ensureExists();

    const entries = await this.listEntries();
    const indexPath = path.join(this.basePath, 'index.md');

    let indexContent = `# Knowledge Base Index\n\n`;
    indexContent += `*Last updated: ${new Date().toISOString()}*\n\n`;
    indexContent += `Total entries: ${entries.length}\n\n`;

    // Group by tags
    const tagGroups: { [key: string]: KnowledgeEntry[] } = {};

    entries.forEach((entry) => {
      if (entry.tags && entry.tags.length > 0) {
        entry.tags.forEach((tag) => {
          if (!tagGroups[tag]) {
            tagGroups[tag] = [];
          }
          tagGroups[tag].push(entry);
        });
      } else {
        if (!tagGroups['untagged']) {
          tagGroups['untagged'] = [];
        }
        tagGroups['untagged'].push(entry);
      }
    });

    // Write index by topic/tag
    indexContent += `## By Topic\n\n`;

    for (const [tag, tagEntries] of Object.entries(tagGroups).sort()) {
      indexContent += `### ${tag}\n\n`;
      tagEntries.forEach((entry) => {
        indexContent += `- [${entry.title}](./entries/${entry.path})\n`;
      });
      indexContent += '\n';
    }

    // Write alphabetical list
    indexContent += `## Alphabetical\n\n`;
    entries.sort((a, b) => a.title.localeCompare(b.title)).forEach((entry) => {
      indexContent += `- [${entry.title}](./entries/${entry.path})\n`;
    });

    await fs.writeFile(indexPath, indexContent);
  }

  /**
   * Search within the knowledge base
   */
  async search(query: string): Promise<SearchResultEntry[]> {
    await this.ensureExists();

    const entries = await this.listEntries();
    const results: SearchResultEntry[] = [];
    const queryLower = query.toLowerCase();

    for (const entry of entries) {
      const titleMatch = entry.title.toLowerCase().includes(queryLower);
      const contentMatch = entry.content.toLowerCase().includes(queryLower);

      if (titleMatch || contentMatch) {
        // Find excerpt
        let excerpt = '';
        if (contentMatch) {
          const index = entry.content.toLowerCase().indexOf(queryLower);
          const start = Math.max(0, index - 50);
          const end = Math.min(entry.content.length, index + query.length + 50);
          excerpt = entry.content.substring(start, end);
        }

        results.push({
          title: entry.title,
          path: entry.path,
          excerpt,
          score: titleMatch ? 2 : 1,
        });
      }
    }

    // Sort by score
    results.sort((a, b) => (b.score || 0) - (a.score || 0));

    return results;
  }

  /**
   * Convert a string to a URL-friendly slug
   */
  private slugify(text: string): string {
    return text
      .toLowerCase()
      .replace(/[^\w\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/--+/g, '-')
      .trim();
  }
}
