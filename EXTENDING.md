# Extending the Research Agent

This document provides guidance on how to extend the research agent scaffolding with additional capabilities.

## Overview

The research agent is built with a modular architecture that makes it easy to add new features:

- **Web Search Integration**: Connect to real search APIs
- **LLM Integration**: Add AI-powered analysis and summarization
- **Vector Database**: Enable semantic search
- **Additional Data Sources**: Integrate with APIs, databases, etc.

## Adding Web Search APIs

The `WebSearcher` class in `src/research/web-searcher.ts` is currently a scaffold. To integrate a real search API:

### Option 1: Google Custom Search

```typescript
import axios from 'axios';

export class WebSearcher {
  private apiKey: string;
  private searchEngineId: string;

  constructor() {
    this.apiKey = process.env.GOOGLE_API_KEY || '';
    this.searchEngineId = process.env.GOOGLE_SEARCH_ENGINE_ID || '';
  }

  async search(query: string, numResults: number = 5): Promise<SearchResult[]> {
    const url = 'https://www.googleapis.com/customsearch/v1';
    const params = {
      key: this.apiKey,
      cx: this.searchEngineId,
      q: query,
      num: numResults,
    };

    const response = await axios.get(url, { params });
    return response.data.items.map((item: any) => ({
      title: item.title,
      url: item.link,
      snippet: item.snippet,
      source: 'Google',
    }));
  }
}
```

### Option 2: SerpAPI

```bash
npm install serpapi
```

```typescript
import { getJson } from 'serpapi';

export class WebSearcher {
  async search(query: string, numResults: number = 5): Promise<SearchResult[]> {
    const response = await getJson({
      engine: "google",
      api_key: process.env.SERPAPI_KEY,
      q: query,
      num: numResults,
    });

    return response.organic_results.map((result: any) => ({
      title: result.title,
      url: result.link,
      snippet: result.snippet,
      source: 'SerpAPI',
    }));
  }
}
```

## Adding LLM Integration

You can enhance the `ResearchAgent` to use LLMs for better analysis and summarization:

### Using OpenAI

```bash
npm install openai
```

```typescript
import OpenAI from 'openai';

export class ResearchAgent {
  private openai: OpenAI;

  constructor() {
    this.openai = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY,
    });
  }

  private async generateSummary(topic: string, findings: string[]): Promise<string> {
    const prompt = `Summarize the following research findings about "${topic}":\n\n${findings.join('\n')}`;
    
    const completion = await this.openai.chat.completions.create({
      model: "gpt-4",
      messages: [
        { role: "system", content: "You are a research assistant that creates concise summaries." },
        { role: "user", content: prompt }
      ],
    });

    return completion.choices[0].message.content || '';
  }

  private async extractRelatedTopics(sources: SearchResult[]): Promise<string[]> {
    const content = sources.map(s => s.snippet).join('\n');
    const prompt = `Extract 5-10 related topics from this content:\n\n${content}`;
    
    const completion = await this.openai.chat.completions.create({
      model: "gpt-4",
      messages: [{ role: "user", content: prompt }],
    });

    const topics = completion.choices[0].message.content?.split('\n').map(t => t.trim()) || [];
    return topics.filter(t => t.length > 0);
  }
}
```

## Adding Vector Database Support

To enable semantic search, integrate a vector database like Pinecone or Weaviate:

### Using Pinecone

```bash
npm install @pinecone-database/pinecone
```

```typescript
import { Pinecone } from '@pinecone-database/pinecone';
import OpenAI from 'openai';

export class VectorKnowledgeBase extends KnowledgeBase {
  private pinecone: Pinecone;
  private openai: OpenAI;
  private indexName: string = 'research-kb';

  constructor(basePath: string = './knowledge-base') {
    super(basePath);
    this.pinecone = new Pinecone({
      apiKey: process.env.PINECONE_API_KEY || '',
    });
    this.openai = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY,
    });
  }

  async saveResearch(research: ResearchResult): Promise<void> {
    // Save to markdown
    await super.saveResearch(research);

    // Generate embedding
    const text = `${research.topic}\n${research.summary}\n${research.findings.join('\n')}`;
    const embedding = await this.generateEmbedding(text);

    // Store in vector DB
    const index = this.pinecone.index(this.indexName);
    await index.upsert([{
      id: this.slugify(research.topic),
      values: embedding,
      metadata: {
        title: research.topic,
        summary: research.summary,
        createdAt: research.createdAt,
      },
    }]);
  }

  async semanticSearch(query: string, topK: number = 5): Promise<SearchResultEntry[]> {
    const embedding = await this.generateEmbedding(query);
    const index = this.pinecone.index(this.indexName);
    
    const results = await index.query({
      vector: embedding,
      topK,
      includeMetadata: true,
    });

    return results.matches.map(match => ({
      title: match.metadata?.title as string,
      path: `${this.slugify(match.metadata?.title as string)}.md`,
      excerpt: match.metadata?.summary as string,
      score: match.score,
    }));
  }

  private async generateEmbedding(text: string): Promise<number[]> {
    const response = await this.openai.embeddings.create({
      model: "text-embedding-ada-002",
      input: text,
    });
    return response.data[0].embedding;
  }
}
```

## Adding Additional Commands

To add new commands to the CLI, create a new file in `src/commands/` and register it in `src/cli.ts`:

```typescript
// src/commands/export.ts
export async function exportCommand(format: string, options: any): Promise<void> {
  // Implementation
}

// src/cli.ts
import { exportCommand } from './commands/export';

program
  .command('export <format>')
  .description('Export knowledge base to different formats')
  .option('-o, --output <path>', 'Output path')
  .action(exportCommand);
```

## Environment Variables

Create a `.env` file for API keys and configuration:

```bash
# Web Search
GOOGLE_API_KEY=your_key_here
GOOGLE_SEARCH_ENGINE_ID=your_id_here
SERPAPI_KEY=your_key_here

# LLM
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# Vector Database
PINECONE_API_KEY=your_key_here
PINECONE_ENVIRONMENT=your_env_here
```

Load them using `dotenv`:

```bash
npm install dotenv
```

```typescript
import dotenv from 'dotenv';
dotenv.config();
```

## Adding Web Scraping

To fetch and analyze full web pages:

```bash
npm install cheerio axios
```

```typescript
import axios from 'axios';
import * as cheerio from 'cheerio';

export class WebScraper {
  async fetchPage(url: string): Promise<string> {
    const response = await axios.get(url);
    const $ = cheerio.load(response.data);
    
    // Remove scripts, styles, etc.
    $('script, style, nav, footer').remove();
    
    // Extract main content
    const content = $('main, article, .content').text();
    return content.trim();
  }

  async extractLinks(url: string): Promise<string[]> {
    const response = await axios.get(url);
    const $ = cheerio.load(response.data);
    
    const links: string[] = [];
    $('a[href]').each((_, element) => {
      const href = $(element).attr('href');
      if (href) links.push(href);
    });
    
    return links;
  }
}
```

## Testing

Add tests using Jest:

```bash
npm install --save-dev jest ts-jest @types/jest
```

```typescript
// __tests__/knowledge-base.test.ts
import { KnowledgeBase } from '../src/knowledge-base/knowledge-base';

describe('KnowledgeBase', () => {
  let kb: KnowledgeBase;

  beforeEach(() => {
    kb = new KnowledgeBase('/tmp/test-kb');
  });

  test('should list entries', async () => {
    const entries = await kb.listEntries();
    expect(Array.isArray(entries)).toBe(true);
  });

  // More tests...
});
```

## Deployment

### As a Global CLI Tool

```bash
npm run build
npm link
```

### As a Package

Publish to npm:

```bash
npm publish
```

Users can then install:

```bash
npm install -g researcher
```

## Best Practices

1. **Error Handling**: Always handle API failures gracefully
2. **Rate Limiting**: Implement rate limiting for API calls
3. **Caching**: Cache search results to reduce API usage
4. **Configuration**: Make everything configurable via environment variables
5. **Logging**: Add comprehensive logging for debugging
6. **Documentation**: Keep documentation up to date as you add features

## Future Ideas

- **Knowledge Graph Visualization**: Use D3.js or similar to visualize connections
- **Export Formats**: PDF, HTML, Notion, Obsidian
- **Collaborative Features**: Sync knowledge bases across teams
- **Browser Extension**: Save research directly from the browser
- **Scheduled Research**: Automatically research topics on a schedule
- **Citation Management**: Integration with Zotero or similar tools
- **Multi-language Support**: Research in multiple languages
- **Audio/Video Research**: Transcribe and research multimedia content

## Resources

- [Commander.js Documentation](https://github.com/tj/commander.js)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Pinecone Documentation](https://docs.pinecone.io)
- [SerpAPI Documentation](https://serpapi.com/docs)
- [Markdown-it Documentation](https://markdown-it.github.io)
