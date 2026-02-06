# Code Analyzer Agent - Copilot-CLI Integration Guide

## Overview

The **Code Analyzer Agent** analyzes codebases to extract patterns, document architecture, identify technical debt, and suggest improvements. It uses the same knowledge base system as the Researcher agent to build interconnected documentation of code structure, decisions, and evolution.

## Use Cases

- **Architecture Documentation**: Map system architecture, component relationships, and data flows
- **Pattern Extraction**: Identify design patterns, anti-patterns, and coding conventions
- **Technical Debt Tracking**: Catalog debt items with severity, impact, and relationships
- **Onboarding Documentation**: Build knowledge graphs for new team members
- **Refactoring Planning**: Document refactoring opportunities with dependencies
- **API Documentation**: Extract and document API surfaces, contracts, and usage patterns
- **Dependency Analysis**: Map module dependencies and identify coupling issues

## Architecture

### Entity Types

1. **Components**: Classes, modules, packages, services
2. **Patterns**: Design patterns, anti-patterns, conventions
3. **Technical Debt**: Code smells, deprecated code, TODOs
4. **APIs**: Endpoints, interfaces, contracts
5. **Dependencies**: Module relationships, external libraries
6. **Decisions**: Architecture decisions and trade-offs

### Link Types

- `contains`: Package contains module, module contains class
- `depends_on`: Component A depends on component B
- `implements`: Class implements pattern
- `related_to`: General relationship between items
- `causes`: Debt item causes another issue
- `blocks`: Debt blocks feature or improvement

## Workflow 1: Architecture Documentation

### Goal
Document system architecture by analyzing codebase structure and relationships.

### Process

```bash
#!/bin/bash
# Architecture documentation workflow

# 1. Analyze entry points (main, server startup, etc.)
ENTRY_CONTENT=$(analyze_entry_points)
ENTRY_ID=$(./kb-cli add-entity \
    "System Entry Points" \
    "$ENTRY_CONTENT" \
    '{"type":"component","category":"entry_point","files":3}' | jq -r '.id')

# 2. Extract major components
for component in $(find_major_components); do
    COMP_CONTENT=$(analyze_component "$component")
    COMP_ID=$(./kb-cli add-entity \
        "Component: $component" \
        "$COMP_CONTENT" \
        "{\"type\":\"component\",\"loc\":$LOC,\"dependencies\":$DEPS}" | jq -r '.id')
    
    # Link to entry point if relevant
    ./kb-cli add-link "$ENTRY_ID" "$COMP_ID" "contains"
done

# 3. Map component relationships
for comp_pair in $(find_dependencies); do
    FROM_ID=$(get_entity_by_name "$comp_pair_from")
    TO_ID=$(get_entity_by_name "$comp_pair_to")
    ./kb-cli add-link "$FROM_ID" "$TO_ID" "depends_on"
done

# 4. Extract data flow patterns
DATA_FLOW=$(analyze_data_flow)
FLOW_ID=$(./kb-cli add-entity \
    "Data Flow Patterns" \
    "$DATA_FLOW" \
    '{"type":"pattern","category":"data_flow"}' | jq -r '.id')

# 5. Identify architectural patterns
for pattern in $(detect_patterns); do
    PATTERN_ID=$(./kb-cli add-entity \
        "Pattern: $pattern" \
        "$(describe_pattern $pattern)" \
        "{\"type\":\"pattern\",\"occurrences\":$COUNT}" | jq -r '.id')
    
    # Link components implementing this pattern
    for impl in $(find_implementations "$pattern"); do
        IMPL_ID=$(get_entity_by_name "$impl")
        ./kb-cli add-link "$IMPL_ID" "$PATTERN_ID" "implements"
    done
done

# 6. Generate architecture visualization
./kb-cli visualize > architecture.dot
dot -Tpng architecture.dot > architecture.png

# 7. Generate architecture summary
./kb-cli stats
echo "Architecture documented: $ENTITY_COUNT components, $LINK_COUNT relationships"
```

### Output Example

```
Entity: System Entry Points
- Type: component
- Files: 3 (server.js, cli.js, worker.js)
- Dependencies: 8 major components

Relationships:
- server.js → contains → Express Application
- Express Application → depends_on → Database Layer
- Database Layer → implements → Repository Pattern
```

## Workflow 2: Technical Debt Analysis

### Goal
Identify, categorize, and prioritize technical debt items with impact analysis.

### Process

```bash
#!/bin/bash
# Technical debt analysis workflow

# 1. Scan for code smells
for smell in $(run_linter | filter_issues); do
    SMELL_CONTENT=$(format_debt_item "$smell")
    SMELL_ID=$(./kb-cli add-entity \
        "Debt: $smell_title" \
        "$SMELL_CONTENT" \
        "{\"type\":\"debt\",\"severity\":\"$SEVERITY\",\"file\":\"$FILE\",\"line\":$LINE}" | jq -r '.id')
    
    # Create task for remediation
    ./kb-cli add-task \
        "Fix: $smell_title" \
        "Refactor $FILE:$LINE to address $smell" \
        "$SMELL_ID" \
        "{\"priority\":\"$PRIORITY\",\"effort\":\"$EFFORT\"}"
done

# 2. Find deprecated code usage
for deprecated in $(grep_deprecated_usage); do
    DEP_ID=$(./kb-cli add-entity \
        "Deprecated: $deprecated_api" \
        "Usage of deprecated $deprecated_api found in $usage_count locations" \
        "{\"type\":\"debt\",\"category\":\"deprecated\",\"count\":$usage_count}" | jq -r '.id')
    
    # Link to components using it
    for usage in $(find_usages "$deprecated_api"); do
        COMP_ID=$(get_component_for_file "$usage")
        ./kb-cli add-link "$COMP_ID" "$DEP_ID" "related_to"
    done
done

# 3. Analyze TODO/FIXME comments
for todo in $(grep_todos); do
    TODO_ID=$(./kb-cli add-entity \
        "TODO: $todo_summary" \
        "$todo_content" \
        "{\"type\":\"debt\",\"category\":\"todo\",\"file\":\"$file\"}" | jq -r '.id')
done

# 4. Calculate debt metrics
TOTAL_DEBT=$(./kb-cli list-entities | jq '[.[] | select(.metadata | fromjson | .type == "debt")] | length')
HIGH_PRIORITY=$(./kb-cli get-tasks pending | jq '[.[] | select(.metadata | fromjson | .priority == "high")] | length')

echo "Technical Debt Summary:"
echo "- Total items: $TOTAL_DEBT"
echo "- High priority: $HIGH_PRIORITY"
echo "- Estimated effort: $TOTAL_EFFORT person-days"

# 5. Generate debt report
./kb-cli stats
```

### Debt Severity Classification

**High Severity** (5 debt points):
- Security vulnerabilities
- Performance bottlenecks affecting users
- Data corruption risks
- Breaking changes needed

**Medium Severity** (3 debt points):
- Code duplication (>50 lines)
- Complex functions (cyclomatic complexity >10)
- Missing error handling
- Deprecated API usage

**Low Severity** (1 debt point):
- Style violations
- Missing comments
- TODO items without urgency
- Minor refactoring opportunities

## Workflow 3: API Documentation

### Goal
Extract and document API surfaces with usage examples and relationships.

### Process

```bash
#!/bin/bash
# API documentation workflow

# 1. Extract REST endpoints
for endpoint in $(parse_routes); do
    ENDPOINT_CONTENT=$(document_endpoint "$endpoint")
    ENDPOINT_ID=$(./kb-cli add-entity \
        "API: $method $path" \
        "$ENDPOINT_CONTENT" \
        "{\"type\":\"api\",\"method\":\"$method\",\"path\":\"$path\",\"auth\":\"$auth\"}" | jq -r '.id')
    
    # Link to implementing controller
    CONTROLLER_ID=$(get_controller_for_endpoint "$endpoint")
    ./kb-cli add-link "$ENDPOINT_ID" "$CONTROLLER_ID" "implemented_by"
done

# 2. Extract function signatures
for function in $(find_public_functions); do
    FUNC_CONTENT=$(document_function "$function")
    FUNC_ID=$(./kb-cli add-entity \
        "Function: $function_name" \
        "$FUNC_CONTENT" \
        "{\"type\":\"api\",\"category\":\"function\",\"params\":$param_count}" | jq -r '.id')
done

# 3. Find API usage patterns
for pattern in $(analyze_api_usage); do
    PATTERN_ID=$(./kb-cli add-entity \
        "Usage Pattern: $pattern_name" \
        "$pattern_description" \
        "{\"type\":\"pattern\",\"category\":\"api_usage\",\"frequency\":$count}" | jq -r '.id')
    
    # Link to relevant APIs
    for api in $(get_apis_in_pattern "$pattern"); do
        API_ID=$(get_entity_by_name "$api")
        ./kb-cli add-link "$PATTERN_ID" "$API_ID" "uses"
    done
done

# 4. Generate API documentation
./kb-cli export-entity "$ENDPOINT_ID" > docs/api-reference.md

# 5. Create OpenAPI spec from KB
generate_openapi_from_kb > openapi.yaml
```

## Integration with Copilot-CLI

### Custom Agent Definition

Create `.github/agents/code-analyzer.md`:

```markdown
# Code Analyzer Agent

You are a code analysis expert that documents codebases systematically.

## Your Role

1. Analyze code structure and extract components
2. Identify architectural patterns and design decisions
3. Document technical debt with impact analysis
4. Extract and document APIs
5. Map dependencies and relationships
6. Maintain knowledge base of code insights

## Tools Available

- `./kb-cli`: Knowledge base management
- Code analysis tools: grep, ast-parser, linters
- Git history for evolution tracking

## Workflow

1. Start with entry points and work outward
2. Create entity for each significant component
3. Link entities with appropriate relationship types
4. Identify patterns and anti-patterns
5. Track technical debt items
6. Generate visualizations and reports

## Entity Types

- component: Classes, modules, services
- pattern: Design patterns found in code
- debt: Technical debt items
- api: Endpoints, interfaces
- dependency: External libraries, internal modules

## Success Criteria

- Complete component map with relationships
- All patterns documented with examples
- Technical debt cataloged and prioritized
- Architecture visualization generated
- Onboarding documentation complete
```

### Bash Script Example

```bash
#!/bin/bash
# full_codebase_analysis.sh

set -e

echo "Starting comprehensive codebase analysis..."

# Initialize KB if needed
if [ ! -f "kb.db" ]; then
    ./kb-cli add-entity "Analysis Root" "Codebase analysis started" '{"type":"meta"}'
fi

# Phase 1: Structure Analysis
echo "Phase 1: Analyzing structure..."
analyze_structure() {
    # Find all source files
    SOURCE_FILES=$(find src -type f -name "*.js" -o -name "*.ts")
    
    for file in $SOURCE_FILES; do
        # Extract module info
        MODULE_NAME=$(basename "$file" .js)
        LOC=$(wc -l < "$file")
        COMPLEXITY=$(calculate_complexity "$file")
        
        # Add to KB
        ./kb-cli add-entity \
            "Module: $MODULE_NAME" \
            "File: $file\nLines: $LOC\nComplexity: $COMPLEXITY" \
            "{\"type\":\"component\",\"file\":\"$file\",\"loc\":$LOC}"
    done
}

# Phase 2: Dependency Analysis
echo "Phase 2: Analyzing dependencies..."
analyze_dependencies() {
    # Parse imports/requires
    for file in $(find src -type f); do
        FILE_ID=$(get_entity_for_file "$file")
        
        # Extract dependencies
        DEPS=$(extract_dependencies "$file")
        for dep in $DEPS; do
            DEP_ID=$(get_entity_by_name "$dep")
            if [ -n "$DEP_ID" ]; then
                ./kb-cli add-link "$FILE_ID" "$DEP_ID" "depends_on"
            fi
        done
    done
}

# Phase 3: Pattern Detection
echo "Phase 3: Detecting patterns..."
detect_patterns() {
    # Singleton pattern
    SINGLETONS=$(grep -r "static getInstance" src | wc -l)
    if [ $SINGLETONS -gt 0 ]; then
        ./kb-cli add-entity \
            "Pattern: Singleton" \
            "Found $SINGLETONS singleton implementations" \
            "{\"type\":\"pattern\",\"occurrences\":$SINGLETONS}"
    fi
    
    # Factory pattern
    FACTORIES=$(grep -r "create.*Factory" src | wc -l)
    if [ $FACTORIES -gt 0 ]; then
        ./kb-cli add-entity \
            "Pattern: Factory" \
            "Found $FACTORIES factory implementations" \
            "{\"type\":\"pattern\",\"occurrences\":$FACTORIES}"
    fi
}

# Phase 4: Technical Debt
echo "Phase 4: Identifying technical debt..."
analyze_debt() {
    # Find TODOs
    TODOS=$(grep -rn "TODO\|FIXME\|HACK" src)
    TODO_COUNT=$(echo "$TODOS" | wc -l)
    
    ./kb-cli add-entity \
        "Technical Debt Summary" \
        "Found $TODO_COUNT TODO/FIXME items\n\n$TODOS" \
        "{\"type\":\"debt\",\"category\":\"todos\",\"count\":$TODO_COUNT}"
    
    # Large functions
    LARGE_FUNCS=$(find_large_functions src)
    for func in $LARGE_FUNCS; do
        ./kb-cli add-entity \
            "Debt: Large Function - $func" \
            "Function $func exceeds complexity threshold" \
            "{\"type\":\"debt\",\"severity\":\"medium\"}"
    done
}

# Execute phases
analyze_structure
analyze_dependencies
detect_patterns
analyze_debt

# Generate report
echo "\n=== Analysis Complete ==="
./kb-cli stats

# Generate visualization
./kb-cli visualize > codebase-graph.dot
echo "Visualization saved to codebase-graph.dot"
echo "Generate PNG: dot -Tpng codebase-graph.dot > codebase-graph.png"
```

## Best Practices

1. **Incremental Analysis**: Start with high-level structure, drill down as needed
2. **Consistent Naming**: Use prefixes (Module:, Pattern:, API:, Debt:) for clarity
3. **Rich Metadata**: Include LOC, complexity, file paths, line numbers
4. **Link Everything**: Components to patterns, debt to components, APIs to implementations
5. **Track Evolution**: Re-run analysis periodically to track changes
6. **Prioritize Debt**: Use severity levels and impact analysis
7. **Visualize**: Generate graphs to communicate architecture
8. **Automate**: Run analysis in CI/CD pipeline

## Example Output

After running analysis:

```bash
$ ./kb-cli stats
{
  "entities": 127,
  "links": 245,
  "pending_tasks": 18,
  "completed_tasks": 3,
  "entities_by_type": {
    "component": 45,
    "pattern": 8,
    "debt": 32,
    "api": 28,
    "dependency": 14
  },
  "completion_rate": 14.3
}

$ ./kb-cli list-entities 5
[
  {"id": "a1b2c3d4", "title": "Module: UserService", "type": "component"},
  {"id": "e5f6g7h8", "title": "Pattern: Repository", "type": "pattern"},
  {"id": "i9j0k1l2", "title": "API: POST /users", "type": "api"},
  {"id": "m3n4o5p6", "title": "Debt: Large function handleRequest", "type": "debt"},
  {"id": "q7r8s9t0", "title": "Dependency: express", "type": "dependency"}
]
```

## Keeping Analysis Fresh: Staleness Detection

### The Challenge

Code analysis becomes outdated when code changes. The information isn't useful if it's no longer true.

### Solution: Git Hash Tracking + Auto-Invalidation

Track which code each entity analyzes and detect when it changes.

#### Pattern 1: Git Hash Tracking (Recommended)

Store git commit hash when analyzing code:

```bash
#!/bin/bash
# Analyze with git tracking

FILE_PATH="src/auth/AuthService.js"
GIT_HASH=$(git rev-parse HEAD:$FILE_PATH)
ANALYSIS_CONTENT=$(analyze_file "$FILE_PATH")

ENTITY_ID=$(./kb-cli add-entity \
    "Component: AuthService" \
    "$ANALYSIS_CONTENT" \
    "{\"type\":\"component\",\"file\":\"$FILE_PATH\",\"git_hash\":\"$GIT_HASH\",\"analyzed_at\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" | jq -r '.id')

echo "Analyzed $FILE_PATH at commit $GIT_HASH"
```

#### Pattern 2: Staleness Detection Workflow

Check if analysis is outdated before using it:

```bash
#!/bin/bash
# check_staleness.sh - Detect outdated analysis

echo "Checking for stale analysis..."

# Get all component entities
COMPONENTS=$(./kb-cli list-entities | jq -r '.[] | select((.metadata | fromjson).type == "component")')

STALE_COUNT=0

for component in $(echo "$COMPONENTS" | jq -r '.id'); do
    ENTITY=$(./kb-cli get-entity "$component")
    
    FILE=$(echo "$ENTITY" | jq -r '.metadata | fromjson | .file')
    STORED_HASH=$(echo "$ENTITY" | jq -r '.metadata | fromjson | .git_hash')
    
    if [ -f "$FILE" ]; then
        CURRENT_HASH=$(git rev-parse HEAD:$FILE 2>/dev/null || echo "not_in_git")
        
        if [ "$STORED_HASH" != "$CURRENT_HASH" ]; then
            echo "⚠️  STALE: $FILE (stored: ${STORED_HASH:0:7}, current: ${CURRENT_HASH:0:7})"
            
            # Create task to re-analyze
            ./kb-cli add-task \
                "Re-analyze $FILE" \
                "Code has changed since last analysis. Old hash: $STORED_HASH, New hash: $CURRENT_HASH" \
                "$component" \
                "{\"priority\":\"high\",\"type\":\"staleness\"}"
            
            ((STALE_COUNT++))
        fi
    else
        echo "⚠️  DELETED: $FILE"
        # Mark as historical
        ./kb-cli update-entity "$component" \
            "$(echo "$ENTITY" | jq -r '.title')" \
            "$(echo "$ENTITY" | jq -r '.content')\n\n**[HISTORICAL]** File no longer exists" \
            "{\"status\":\"historical\",\"deleted_at\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}"
    fi
done

echo "\nStaleness check complete:"
echo "- Stale entities: $STALE_COUNT"
echo "- Tasks created for re-analysis"
```

#### Pattern 3: Auto-Refresh Workflow

Automatically refresh stale entities:

```bash
#!/bin/bash
# auto_refresh.sh - Re-analyze stale components

# Get staleness tasks
STALE_TASKS=$(./kb-cli get-tasks pending | jq -r '.[] | select((.metadata | fromjson).type == "staleness")')

for task_id in $(echo "$STALE_TASKS" | jq -r '.id'); do
    TASK=$(./kb-cli get-task "$task_id")
    ENTITY_ID=$(echo "$TASK" | jq -r '.entity_id')
    
    # Get entity details
    ENTITY=$(./kb-cli get-entity "$ENTITY_ID")
    FILE=$(echo "$ENTITY" | jq -r '.metadata | fromjson | .file')
    
    echo "Re-analyzing $FILE..."
    
    # Perform fresh analysis
    NEW_CONTENT=$(analyze_file "$FILE")
    NEW_HASH=$(git rev-parse HEAD:$FILE)
    
    # Update entity with fresh data
    ./kb-cli update-entity "$ENTITY_ID" \
        "$(echo "$ENTITY" | jq -r '.title')" \
        "$NEW_CONTENT" \
        "{\"type\":\"component\",\"file\":\"$FILE\",\"git_hash\":\"$NEW_HASH\",\"analyzed_at\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"refreshed\":true}"
    
    # Mark task as completed
    ./kb-cli update-task "$task_id" "completed"
    
    echo "✓ Updated $FILE"
done

echo "\nAuto-refresh complete"
```

#### Pattern 4: Differential Analysis

Track evolution by linking old and new analysis:

```bash
#!/bin/bash
# differential_analysis.sh - Track code evolution

FILE_PATH="src/auth/AuthService.js"
OLD_ENTITY_ID=$(find_entity_for_file "$FILE_PATH")

if [ -n "$OLD_ENTITY_ID" ]; then
    # Perform fresh analysis
    NEW_CONTENT=$(analyze_file "$FILE_PATH")
    NEW_HASH=$(git rev-parse HEAD:$FILE_PATH)
    
    # Create new entity
    NEW_ENTITY_ID=$(./kb-cli add-entity \
        "Component: AuthService (v2)" \
        "$NEW_CONTENT" \
        "{\"type\":\"component\",\"file\":\"$FILE_PATH\",\"git_hash\":\"$NEW_HASH\",\"version\":2}" | jq -r '.id')
    
    # Link old to new with "supersedes" relationship
    ./kb-cli add-link "$NEW_ENTITY_ID" "$OLD_ENTITY_ID" "supersedes"
    
    # Mark old as historical
    ./kb-cli update-entity "$OLD_ENTITY_ID" \
        "Component: AuthService (v1)" \
        "$(get_entity_content $OLD_ENTITY_ID)\n\n**[HISTORICAL]** Superseded by newer analysis" \
        "{\"status\":\"historical\",\"superseded_by\":\"$NEW_ENTITY_ID\"}"
    
    # Generate diff summary
    CHANGES=$(git diff $OLD_HASH $NEW_HASH -- "$FILE_PATH" | diffstat)
    echo "Changes detected: $CHANGES"
fi
```

#### Pattern 5: Time-Based Staleness

Mark entities as stale after N days:

```bash
#!/bin/bash
# time_based_staleness.sh

MAX_AGE_DAYS=30
CUTOFF_DATE=$(date -u -d "$MAX_AGE_DAYS days ago" +%Y-%m-%dT%H:%M:%SZ)

echo "Finding entities older than $MAX_AGE_DAYS days (before $CUTOFF_DATE)..."

ALL_ENTITIES=$(./kb-cli list-entities)

for entity_id in $(echo "$ALL_ENTITIES" | jq -r '.[] | select((.metadata | fromjson).analyzed_at?) | .id'); do
    ENTITY=$(./kb-cli get-entity "$entity_id")
    ANALYZED_AT=$(echo "$ENTITY" | jq -r '.metadata | fromjson | .analyzed_at')
    
    if [[ "$ANALYZED_AT" < "$CUTOFF_DATE" ]]; then
        TITLE=$(echo "$ENTITY" | jq -r '.title')
        echo "STALE: $TITLE (analyzed $ANALYZED_AT)"
        
        # Add refresh task
        ./kb-cli add-task \
            "Refresh: $TITLE" \
            "Entity is >$MAX_AGE_DAYS days old, may be outdated" \
            "$entity_id" \
            "{\"priority\":\"medium\",\"type\":\"staleness\",\"reason\":\"age\"}"
    fi
done
```

### Best Practices for Freshness

1. **Track at Creation**: Always include `git_hash` and `analyzed_at` in metadata
2. **Regular Checks**: Run staleness detection daily or on PR merges
3. **Prioritize Updates**: Refresh high-traffic components first
4. **Keep History**: Use "supersedes" links to track evolution
5. **Automate**: Integrate staleness detection into CI/CD
6. **Set Thresholds**: Different components may have different freshness requirements
7. **File Watchers**: Use git hooks or file watchers for real-time updates
8. **Batch Updates**: Refresh multiple stale entities in parallel

### Integration with CI/CD

```yaml
# .github/workflows/code-analysis-freshness.yml
name: Check Code Analysis Freshness

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight

jobs:
  check-staleness:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
        with:
          fetch-depth: 0  # Full history for git hashes
      
      - name: Check for stale analysis
        run: |
          ./check_staleness.sh > staleness-report.txt
          cat staleness-report.txt
      
      - name: Auto-refresh stale entities
        run: |
          ./auto_refresh.sh
      
      - name: Commit updated KB
        run: |
          git config user.name "Analysis Bot"
          git config user.email "bot@example.com"
          git add kb.db
          git commit -m "chore: refresh stale code analysis" || true
          git push || true
```

### Staleness Metadata Schema

Recommended metadata structure:

```json
{
  "type": "component",
  "file": "src/auth/AuthService.js",
  "git_hash": "abc123def456",
  "analyzed_at": "2026-02-06T04:00:00Z",
  "refreshed": false,
  "status": "current",
  "version": 1,
  "superseded_by": null,
  "max_age_days": 30
}
```

## Tips for Effective Analysis

1. **Start Small**: Analyze one module thoroughly before expanding
2. **Use AST Parsers**: For accurate code structure analysis (tree-sitter, babel-parser)
3. **Leverage Git**: Use `git log` to understand component evolution
4. **Document Decisions**: Create entities for architectural decision records (ADRs)
5. **Track Metrics**: LOC, complexity, test coverage per component
6. **Identify Hotspots**: Files with frequent changes may need refactoring
7. **Map Data Flow**: Track how data moves through the system
8. **Security Analysis**: Flag potential security issues as high-priority debt
9. **Keep Fresh**: Implement staleness detection and auto-refresh workflows
10. **Track Evolution**: Use differential analysis to document how code changes over time

This agent transforms codebases into structured knowledge, making architecture visible and technical debt manageable. With staleness detection, the analysis stays fresh and useful as code evolves.
