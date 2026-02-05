import fs from 'fs-extra';
import path from 'path';
import chalk from 'chalk';

interface InitOptions {
  path: string;
}

export async function initCommand(options: InitOptions): Promise<void> {
  const kbPath = path.resolve(options.path);

  try {
    // Create knowledge base directory structure
    await fs.ensureDir(kbPath);
    await fs.ensureDir(path.join(kbPath, 'entries'));
    await fs.ensureDir(path.join(kbPath, 'assets'));

    // Create config file
    const config = {
      name: 'Research Knowledge Base',
      createdAt: new Date().toISOString(),
      version: '1.0.0',
      settings: {
        indexEnabled: true,
        autoLink: true,
      },
    };

    await fs.writeJSON(path.join(kbPath, 'config.json'), config, { spaces: 2 });

    // Create README
    const readme = `# Research Knowledge Base

This knowledge base was initialized on ${new Date().toISOString()}.

## Structure

- \`entries/\` - Markdown files for research entries
- \`assets/\` - Images, documents, and other assets
- \`index.md\` - Main index of all entries
- \`config.json\` - Configuration file

## Usage

Use the \`researcher\` CLI to manage this knowledge base:

- \`researcher search <query>\` - Search the web
- \`researcher research <topic>\` - Perform deep research
- \`researcher knowledge list\` - List all entries
- \`researcher knowledge view <entry>\` - View an entry
- \`researcher knowledge index\` - Update the index

## Links

Entries can link to each other using standard markdown links:
\`\`\`markdown
See also: [Related Topic](./related-topic.md)
\`\`\`
`;

    await fs.writeFile(path.join(kbPath, 'README.md'), readme);

    // Create initial index
    const index = `# Knowledge Base Index

*Last updated: ${new Date().toISOString()}*

## Entries

(No entries yet)

## Topics

(No topics yet)
`;

    await fs.writeFile(path.join(kbPath, 'index.md'), index);

    console.log(chalk.green('✓ Knowledge base initialized at'), chalk.cyan(kbPath));
    console.log(chalk.gray('  Structure:'));
    console.log(chalk.gray('    - entries/'));
    console.log(chalk.gray('    - assets/'));
    console.log(chalk.gray('    - index.md'));
    console.log(chalk.gray('    - config.json'));
    console.log(chalk.gray('    - README.md'));
  } catch (error) {
    console.error(chalk.red('✗ Error initializing knowledge base:'), error);
    process.exit(1);
  }
}
