# Pipeline Manager Agent

## Overview

The **Pipeline Manager** is a meta-agent coordinator that orchestrates specialist agents through sequential chaining. Each agent's output becomes the input for the next agent, creating a processing pipeline where work flows through multiple stages of transformation and enrichment.

**Key Principle**: Some problems are best solved through a series of transformations, where each stage adds value, validates previous work, and prepares context for the next stage.

## Purpose

Coordinate specialist agents in a sequential workflow where the output of one agent directly informs and enables the work of the next agent, with automatic handoff management and context compression.

## How It Works

### 1. Pipeline Definition

Define a sequence of stages, each handled by a specialist agent:

```
Pipeline: "Feature Spec to Production"

Stage 1: Research (→ Researcher)
  Input: Feature idea
  Output: Best practices, patterns, alternatives
  ↓
Stage 2: Analysis (→ Code Analyzer)
  Input: Research findings + current codebase
  Output: Implementation feasibility, integration points, risks
  ↓
Stage 3: Decision (→ Decision Log)
  Input: Research + Analysis
  Output: Technology choices, architecture decisions, trade-offs documented
  ↓
Stage 4: Learning (→ Learning Path)
  Input: Decisions + implementation requirements
  Output: Team training plan, knowledge gaps, resources
  ↓
Stage 5: Validation (→ Code Analyzer)
  Input: All previous stages
  Output: Final review, risk assessment, go/no-go recommendation
```

### 2. Sequential Execution

Each stage:
- Receives compressed output from previous stage
- Executes its specialized task
- Produces summary output for next stage
- Validates that previous stage output is sufficient
- Can request re-execution of previous stage if input is inadequate

### 3. Context Handoff

Automatic management of context between stages:
- **Full context passed**: Each stage sees all previous stage outputs
- **Compression**: Summaries only (not full content) to manage context size
- **Validation**: Each stage validates it has what it needs
- **Handoff metadata**: Track what was passed, what was used

### 4. Pipeline Monitoring

Track progress through pipeline:
- Current stage
- Time in current stage
- Blockers and handoff issues
- Overall pipeline health

## Agent Metadata Schema

```json
{
  "type": "pipeline",
  "strategy": "sequential_chaining",
  "status": "defining|stage_N|completed|failed",
  "current_stage": 2,
  "total_stages": 5,
  "stages": [
    {
      "stage_num": 1,
      "name": "Research",
      "agent": "researcher",
      "status": "completed",
      "input_entity_id": null,
      "output_entity_id": "abc123",
      "duration_minutes": 15
    }
  ],
  "handoff_type": "full_context|compressed|delta_only",
  "validation_required": true
}
```

## Workflows

### Workflow 1: Research to Implementation Pipeline

**Goal**: "Research → Analyze → Decide → Train → Validate"

**Stage 1: Research Phase**

```bash
# Create pipeline
PIPELINE_ID=$(./kb-cli add-entity \
  "Pipeline: GraphQL Migration" \
  "Sequential pipeline from research to implementation readiness" \
  '{"type":"pipeline","status":"stage_1","current_stage":1,"total_stages":5,"validation_required":true}' \
  | jq -r '.id')

# Stage 1: Research
STAGE1_ID=$(./kb-cli add-entity \
  "Stage 1: Research GraphQL" \
  "Research GraphQL patterns, benefits, drawbacks, migration strategies" \
  '{"type":"pipeline_stage","stage_num":1,"parent_pipeline":"'$PIPELINE_ID'","agent":"researcher","status":"executing"}' \
  | jq -r '.id')

./kb-cli add-link $PIPELINE_ID $STAGE1_ID "stage"

# Execute stage 1
./kb-cli add-task \
  "Execute Stage 1: Research" \
  "@researcher conduct comprehensive research on GraphQL adoption, migration patterns, and trade-offs" \
  $STAGE1_ID \
  '{"priority":"high","agent":"researcher"}'

# Wait for completion
while [ "$(./kb-cli get-entity $STAGE1_ID | jq -r '.metadata.status')" != "completed" ]; do
  echo "Stage 1 in progress..."
  sleep 30
done

# Compress output for next stage
STAGE1_SUMMARY=$(./kb-cli export-entity $STAGE1_ID | head -100)
echo "Stage 1 complete. Output size: $(echo "$STAGE1_SUMMARY" | wc -c) chars"
```

**Stage 2: Analysis Phase (receives Stage 1 output)**

```bash
# Stage 2: Code Analysis
STAGE2_ID=$(./kb-cli add-entity \
  "Stage 2: Analyze Current API" \
  "Analyze existing REST API architecture and assess GraphQL migration feasibility" \
  '{"type":"pipeline_stage","stage_num":2,"parent_pipeline":"'$PIPELINE_ID'","agent":"code-analyzer","status":"executing","input_entity":"'$STAGE1_ID'"}' \
  | jq -r '.id')

./kb-cli add-link $PIPELINE_ID $STAGE2_ID "stage"
./kb-cli add-link $STAGE1_ID $STAGE2_ID "feeds"

# Pass Stage 1 output as context to Stage 2
./kb-cli add-task \
  "Execute Stage 2: Analysis" \
  "$(cat <<EOF
@code-analyzer

Context from Stage 1 (Research):
$STAGE1_SUMMARY

Your Task:
Analyze our current REST API implementation considering the GraphQL research above.
Identify:
1. Migration complexity
2. Integration points
3. Technical risks
4. Effort estimates

Return summary in 1000 chars.
EOF
)" \
  $STAGE2_ID \
  '{"priority":"high","agent":"code-analyzer","input_from":"'$STAGE1_ID'"}'

# Wait for completion with validation
while [ "$(./kb-cli get-entity $STAGE2_ID | jq -r '.metadata.status')" != "completed" ]; do
  sleep 30
done

# Validate Stage 2 output
STAGE2_CONTENT=$(./kb-cli get-entity $STAGE2_ID | jq -r '.content')
if [ ${#STAGE2_CONTENT} -lt 100 ]; then
  echo "ERROR: Stage 2 output insufficient, requesting re-execution"
  ./kb-cli update-entity $STAGE2_ID "" "" '{"status":"failed","error":"insufficient_output"}'
  exit 1
fi

STAGE2_SUMMARY=$(./kb-cli export-entity $STAGE2_ID | head -100)
```

**Stage 3-5: Similar Pattern**

```bash
# Stage 3: Decision (gets Stage 1 + Stage 2)
CONTEXT="Stage 1: $STAGE1_SUMMARY\n\nStage 2: $STAGE2_SUMMARY"
# ... execute with combined context ...

# Stage 4: Learning Path (gets Stage 1 + 2 + 3)
# Stage 5: Final Validation (gets all previous)
```

### Workflow 2: Data Processing Pipeline

**Goal**: "Raw Data → Cleaned → Analyzed → Documented"

```bash
# Create data pipeline
PIPELINE_ID=$(./kb-cli add-entity \
  "Pipeline: User Behavior Analysis" \
  "Process raw logs through analysis pipeline" \
  '{"type":"pipeline","total_stages":4,"data_pipeline":true}' \
  | jq -r '.id')

# Stage 1: Data Collection (Researcher gathers data sources)
STAGE1_ID=$(./kb-cli add-entity \
  "Stage 1: Identify Data Sources" \
  "..." \
  '{"type":"pipeline_stage","stage_num":1,"agent":"researcher"}' | jq -r '.id')

# Stage 2: Data Analysis (Code Analyzer processes data)
STAGE2_ID=$(./kb-cli add-entity \
  "Stage 2: Analyze Patterns" \
  "..." \
  '{"type":"pipeline_stage","stage_num":2,"agent":"code-analyzer","input_entity":"'$STAGE1_ID'"}' | jq -r '.id')

# Stage 3: Insight Documentation (Decision Log documents findings)
STAGE3_ID=$(./kb-cli add-entity \
  "Stage 3: Document Insights" \
  "..." \
  '{"type":"pipeline_stage","stage_num":3,"agent":"decision-log","input_entity":"'$STAGE2_ID'"}' | jq -r '.id')

# Stage 4: Action Plan (Learning Path creates enablement plan)
STAGE4_ID=$(./kb-cli add-entity \
  "Stage 4: Create Action Plan" \
  "..." \
  '{"type":"pipeline_stage","stage_num":4,"agent":"learning-path","input_entity":"'$STAGE3_ID'"}' | jq -r '.id')

# Link pipeline stages
./kb-cli add-link $STAGE1_ID $STAGE2_ID "feeds"
./kb-cli add-link $STAGE2_ID $STAGE3_ID "feeds"
./kb-cli add-link $STAGE3_ID $STAGE4_ID "feeds"
```

### Workflow 3: Review Pipeline with Validation

**Goal**: "Document → Review → Revise → Approve"

```bash
# Quality assurance pipeline
PIPELINE_ID=$(./kb-cli add-entity \
  "Pipeline: Documentation QA" \
  "Multi-stage review process with validation gates" \
  '{"type":"pipeline","total_stages":4,"validation_gates":true}' \
  | jq -r '.id')

# Stage 1: Draft (Researcher creates initial doc)
# Stage 2: Technical Review (Code Analyzer validates accuracy)
# Stage 3: Revisions (Researcher incorporates feedback)
# Stage 4: Final Approval (Decision Log records approval)

# Each stage validates previous output before proceeding
```

## Key Patterns

### Pattern 1: Context Compression

```bash
# Each stage compresses output for next stage
function compress_output() {
  local entity_id=$1
  local max_chars=${2:-1000}
  
  # Get full content
  local full_content=$(./kb-cli get-entity $entity_id | jq -r '.content')
  
  # Compress (in production, use LLM to summarize)
  local summary=$(echo "$full_content" | head -c $max_chars)
  
  # Store summary in metadata for next stage
  ./kb-cli update-entity $entity_id "" "" \
    "{\"summary\":\"$summary\",\"full_content_length\":${#full_content}}"
  
  echo "$summary"
}

# Stage hands off to next stage
COMPRESSED=$(compress_output $STAGE_ID 1000)
# Pass $COMPRESSED to next stage as input
```

### Pattern 2: Validation Gates

```bash
# Each stage validates it can proceed
function validate_input() {
  local stage_id=$1
  local input_entity=$2
  
  # Get input
  local input=$(./kb-cli get-entity $input_entity | jq -r '.metadata.summary // .content')
  
  # Check sufficiency (simplified validation)
  if [ ${#input} -lt 100 ]; then
    echo "ERROR: Input insufficient for stage $stage_id"
    
    # Mark current stage as blocked
    ./kb-cli update-entity $stage_id "" "" \
      '{"status":"blocked","blocker":"insufficient_input","needs_reexecution":"'$input_entity'"}'
    
    return 1
  fi
  
  # Check for required information (would use LLM in production)
  local required_terms=("analysis" "findings" "recommendations")
  for term in "${required_terms[@]}"; do
    if ! echo "$input" | grep -qi "$term"; then
      echo "WARNING: Input missing expected term: $term"
    fi
  done
  
  return 0
}

# Before executing stage, validate input
if ! validate_input $STAGE2_ID $STAGE1_ID; then
  echo "Re-executing previous stage with additional guidance"
  # ... re-execute ...
fi
```

### Pattern 3: Delta Handoff (Incremental)

```bash
# Instead of passing full context each time, pass only new information

# Stage 1 produces output A
# Stage 2 receives A, produces output B (delta on top of A)
# Stage 3 receives A+B (but only new info from B), produces output C

function create_delta_handoff() {
  local prev_stage=$1
  local current_stage=$2
  
  # Mark what was already provided
  local prev_output=$(./kb-cli get-entity $prev_stage | jq -r '.metadata.summary')
  
  # Current stage tracks what's new
  ./kb-cli update-entity $current_stage "" "" \
    '{"input_entities":["'$prev_stage'"],"handoff_type":"delta","previous_context_length":'${#prev_output}'}'
}
```

### Pattern 4: Pipeline Rollback

```bash
# If a stage fails validation, roll back and re-execute
function rollback_stage() {
  local failed_stage=$1
  local pipeline_id=$2
  
  echo "Stage $failed_stage failed validation, rolling back"
  
  # Find previous stage
  local prev_stage=$(./kb-cli get-links-to $failed_stage | \
    jq -r '.[] | select(.link_type == "feeds") | .id' | head -1)
  
  if [ -z "$prev_stage" ]; then
    echo "No previous stage to rollback to"
    return 1
  fi
  
  # Mark current stage as rolled back
  ./kb-cli update-entity $failed_stage "" "" \
    '{"status":"rolled_back","rollback_time":"'$(date -Iseconds)'"}'
  
  # Re-execute previous stage with additional guidance
  ./kb-cli add-task \
    "Re-execute: Previous Stage" \
    "Previous execution insufficient, re-running with more specific guidance" \
    $prev_stage \
    '{"priority":"high","re_execution":true}'
  
  # Update pipeline status
  local failed_stage_num=$(./kb-cli get-entity $failed_stage | jq -r '.metadata.stage_num')
  ./kb-cli update-entity $pipeline_id "" "" \
    '{"status":"stage_'$(($failed_stage_num-1))'","current_stage":'$(($failed_stage_num-1))'}'
}
```

## Workflows

### Workflow 1: Standard Research-to-Decision Pipeline

**Goal**: Complete analysis pipeline for a technical decision

```bash
#!/bin/bash
# pipeline_manager.sh - Execute standard pipeline

TOPIC=$1

# Create pipeline
PIPELINE_ID=$(./kb-cli add-entity \
  "Pipeline: $TOPIC Analysis" \
  "Research → Analyze → Decide → Learn" \
  '{"type":"pipeline","strategy":"sequential_chaining","total_stages":4,"status":"stage_1"}' \
  | jq -r '.id')

echo "Created pipeline: $PIPELINE_ID"

# ========================================
# STAGE 1: RESEARCH
# ========================================
echo "=== Stage 1: Research ==="

STAGE1_ID=$(./kb-cli add-entity \
  "Stage 1: Research $TOPIC" \
  "Comprehensive research phase" \
  '{"type":"pipeline_stage","stage_num":1,"parent_pipeline":"'$PIPELINE_ID'","agent":"researcher","status":"executing"}' \
  | jq -r '.id')

./kb-cli add-link $PIPELINE_ID $STAGE1_ID "stage"

# Execute research
./kb-cli add-task \
  "Research: $TOPIC" \
  "@researcher research '$TOPIC' including benefits, drawbacks, alternatives, case studies" \
  $STAGE1_ID \
  '{"agent":"researcher","return_summary":true,"max_length":1000}'

# Wait for completion
while [ "$(./kb-cli get-entity $STAGE1_ID | jq -r '.metadata.status')" != "completed" ]; do
  sleep 20
  echo "  Stage 1 in progress..."
done

# Compress output
STAGE1_OUTPUT=$(./kb-cli export-entity $STAGE1_ID | head -80)
echo "  Stage 1 complete. Output: ${#STAGE1_OUTPUT} chars"

# ========================================
# STAGE 2: ANALYSIS
# ========================================
echo "=== Stage 2: Code Analysis ==="

STAGE2_ID=$(./kb-cli add-entity \
  "Stage 2: Analyze Implementation" \
  "Analyze current codebase considering research findings" \
  '{"type":"pipeline_stage","stage_num":2,"parent_pipeline":"'$PIPELINE_ID'","agent":"code-analyzer","status":"executing","input_entity":"'$STAGE1_ID'"}' \
  | jq -r '.id')

./kb-cli add-link $PIPELINE_ID $STAGE2_ID "stage"
./kb-cli add-link $STAGE1_ID $STAGE2_ID "feeds"

# Update pipeline status
./kb-cli update-entity $PIPELINE_ID "" "" '{"status":"stage_2","current_stage":2}'

# Execute with context from Stage 1
./kb-cli add-task \
  "Analyze: Implementation" \
  "$(cat <<EOF
@code-analyzer

CONTEXT FROM STAGE 1 (Research):
$STAGE1_OUTPUT

YOUR TASK:
Analyze our current codebase to assess implementation of findings from Stage 1.
Identify:
1. Integration points
2. Technical challenges
3. Effort estimate
4. Risk assessment

Return summary in 1000 chars.
EOF
)" \
  $STAGE2_ID \
  '{"agent":"code-analyzer","input_from":"'$STAGE1_ID'"}'

# Wait for completion
while [ "$(./kb-cli get-entity $STAGE2_ID | jq -r '.metadata.status')" != "completed" ]; do
  sleep 20
  echo "  Stage 2 in progress..."
done

# Validate output
STAGE2_OUTPUT=$(./kb-cli export-entity $STAGE2_ID | head -80)
if [ ${#STAGE2_OUTPUT} -lt 100 ]; then
  echo "  ERROR: Stage 2 output insufficient"
  rollback_stage $STAGE2_ID $PIPELINE_ID
  exit 1
fi

echo "  Stage 2 complete. Output: ${#STAGE2_OUTPUT} chars"

# ========================================
# STAGE 3: DECISION
# ========================================
echo "=== Stage 3: Document Decision ==="

STAGE3_ID=$(./kb-cli add-entity \
  "Stage 3: Decision Documentation" \
  "Document final decision with full context from research and analysis" \
  '{"type":"pipeline_stage","stage_num":3,"parent_pipeline":"'$PIPELINE_ID'","agent":"decision-log","status":"executing"}' \
  | jq -r '.id')

./kb-cli add-link $PIPELINE_ID $STAGE3_ID "stage"
./kb-cli add-link $STAGE2_ID $STAGE3_ID "feeds"

./kb-cli update-entity $PIPELINE_ID "" "" '{"status":"stage_3","current_stage":3}'

# Pass accumulated context
./kb-cli add-task \
  "Decision: Document" \
  "$(cat <<EOF
@decision-log

ACCUMULATED CONTEXT:

Stage 1 (Research):
$STAGE1_OUTPUT

Stage 2 (Analysis):
$STAGE2_OUTPUT

YOUR TASK:
Document the decision about $TOPIC using ADR format.
Include:
1. Decision statement
2. Context (from stages 1-2)
3. Alternatives considered
4. Rationale
5. Consequences expected

Return summary in 1000 chars.
EOF
)" \
  $STAGE3_ID \
  '{"agent":"decision-log","input_from":["'$STAGE1_ID'","'$STAGE2_ID'"]}'

# Wait for completion
while [ "$(./kb-cli get-entity $STAGE3_ID | jq -r '.metadata.status')" != "completed" ]; do
  sleep 20
  echo "  Stage 3 in progress..."
done

STAGE3_OUTPUT=$(./kb-cli export-entity $STAGE3_ID | head -80)
echo "  Stage 3 complete. Output: ${#STAGE3_OUTPUT} chars"

# ========================================
# STAGE 4: LEARNING PATH
# ========================================
echo "=== Stage 4: Team Enablement ==="

STAGE4_ID=$(./kb-cli add-entity \
  "Stage 4: Training Plan" \
  "Create team training plan based on decision and implementation requirements" \
  '{"type":"pipeline_stage","stage_num":4,"parent_pipeline":"'$PIPELINE_ID'","agent":"learning-path","status":"executing"}' \
  | jq -r '.id')

./kb-cli add-link $PIPELINE_ID $STAGE4_ID "stage"
./kb-cli add-link $STAGE3_ID $STAGE4_ID "feeds"

./kb-cli update-entity $PIPELINE_ID "" "" '{"status":"stage_4","current_stage":4}'

./kb-cli add-task \
  "Learning: Create Training" \
  "$(cat <<EOF
@learning-path

ACCUMULATED CONTEXT:
$STAGE1_OUTPUT
$STAGE2_OUTPUT
$STAGE3_OUTPUT

YOUR TASK:
Create team training plan for implementing the decision from Stage 3.
Include:
1. Skills needed
2. Current team gaps
3. Learning resources
4. Training timeline

Return summary in 1000 chars.
EOF
)" \
  $STAGE4_ID \
  '{"agent":"learning-path"}'

# Wait for final stage
while [ "$(./kb-cli get-entity $STAGE4_ID | jq -r '.metadata.status')" != "completed" ]; do
  sleep 20
  echo "  Stage 4 in progress..."
done

STAGE4_OUTPUT=$(./kb-cli export-entity $STAGE4_ID | head -80)
echo "  Stage 4 complete. Output: ${#STAGE4_OUTPUT} chars"

# ========================================
# PIPELINE COMPLETE
# ========================================
./kb-cli update-entity $PIPELINE_ID "" "" '{"status":"completed"}'

echo "========================================="
echo "Pipeline complete: $PIPELINE_ID"
echo "  Stage 1 (Research): $STAGE1_ID"
echo "  Stage 2 (Analysis): $STAGE2_ID"
echo "  Stage 3 (Decision): $STAGE3_ID"
echo "  Stage 4 (Learning): $STAGE4_ID"
echo ""
echo "View full pipeline: ./kb-cli visualize"
```

### Workflow 4: Iterative Refinement Pipeline

**Goal**: "Draft → Review → Refine → Review → Finalize"

```bash
# Pipeline with feedback loops
PIPELINE_ID=$(./kb-cli add-entity \
  "Pipeline: Document Refinement" \
  "Iterative improvement through review cycles" \
  '{"type":"pipeline","total_stages":5,"max_iterations":3,"current_iteration":1}' \
  | jq -r '.id')

# Stage 1: Draft (Researcher creates initial version)
DRAFT_ID=$(./kb-cli add-entity "Draft" "..." '{"stage_num":1}' | jq -r '.id')

# Stage 2: Review (Code Analyzer reviews for technical accuracy)
REVIEW1_ID=$(./kb-cli add-entity "Review: Technical" "..." '{"stage_num":2,"input_entity":"'$DRAFT_ID'"}' | jq -r '.id')
./kb-cli add-link $DRAFT_ID $REVIEW1_ID "feeds"

# Check if revision needed
NEEDS_REVISION=$(./kb-cli get-entity $REVIEW1_ID | jq -r '.metadata.needs_revision // false')

if [ "$NEEDS_REVISION" == "true" ]; then
  # Stage 3: Revise (Researcher incorporates feedback)
  REVISION_ID=$(./kb-cli add-entity "Revision: Draft v2" "..." \
    '{"stage_num":3,"input_entities":["'$DRAFT_ID'","'$REVIEW1_ID'"]}' | jq -r '.id')
  ./kb-cli add-link $REVIEW1_ID $REVISION_ID "requires_revision"
  
  # Stage 4: Review again
  REVIEW2_ID=$(./kb-cli add-entity "Review: Final" "..." \
    '{"stage_num":4,"input_entity":"'$REVISION_ID'"}' | jq -r '.id')
  ./kb-cli add-link $REVISION_ID $REVIEW2_ID "feeds"
fi

# Stage 5: Finalize
FINAL_ID=$(./kb-cli add-entity "Finalized Document" "..." '{"stage_num":5}' | jq -r '.id')
```

## Handoff Types

### Full Context Handoff

```bash
# Pass everything to next stage
function full_context_handoff() {
  local pipeline_id=$1
  local current_stage_num=$2
  
  # Collect all previous stage outputs
  local context=""
  for i in $(seq 1 $(($current_stage_num - 1))); do
    local stage=$(./kb-cli get-links-from $pipeline_id | \
      jq -r '.[] | select(.metadata.stage_num == '$i') | .id' | head -1)
    
    local summary=$(./kb-cli get-entity $stage | jq -r '.metadata.summary')
    context="$context\n\nStage $i:\n$summary"
  done
  
  echo "$context"
}
```

### Compressed Context Handoff

```bash
# Pass only summaries
function compressed_handoff() {
  local prev_stage=$1
  local max_chars=500
  
  local summary=$(./kb-cli export-entity $prev_stage | head -c $max_chars)
  echo "$summary"
}
```

### Delta-Only Handoff

```bash
# Pass only new information, reference previous stages by ID
function delta_handoff() {
  local prev_stage=$1
  local current_stage=$2
  
  # Current stage gets reference to previous stage
  ./kb-cli update-entity $current_stage "" "" \
    '{"input_entity_id":"'$prev_stage'","handoff_type":"delta"}'
  
  # Agent fetches previous content only if needed
  echo "Input available from: $prev_stage (fetch with ./kb-cli get-entity)"
}
```

## Integration with Specialist Agents

### Stage Execution Template

```bash
function execute_stage() {
  local stage_id=$1
  local agent=$2
  local input_entity=$3  # Previous stage output
  
  # Get input context
  local context=""
  if [ ! -z "$input_entity" ]; then
    context=$(./kb-cli get-entity $input_entity | jq -r '.metadata.summary // .content' | head -c 1000)
  fi
  
  # Execute stage with agent
  ./kb-cli add-task \
    "Execute Stage" \
    "$(cat <<EOF
@$agent

$([ ! -z "$context" ] && echo "CONTEXT FROM PREVIOUS STAGE:
$context

")YOUR TASK:
$(./kb-cli get-entity $stage_id | jq -r '.content')

Return summary for next stage (max 1000 chars).
EOF
)" \
    $stage_id \
    '{"agent":"'$agent'","input_entity":"'$input_entity'"}'
  
  # Monitor
  while [ "$(./kb-cli get-entity $stage_id | jq -r '.metadata.status')" != "completed" ]; do
    echo "  Stage executing..."
    sleep 15
  done
  
  # Extract output for next stage
  local output=$(./kb-cli export-entity $stage_id | head -80)
  ./kb-cli update-entity $stage_id "" "" '{"summary":"'"$output"'"}'
  
  echo "  Stage complete"
}
```

## Advantages of Pipeline Manager

✅ **Clear Flow**: Explicit sequential progression, easy to understand
✅ **Context Accumulation**: Each stage builds on all previous stages
✅ **Validation Gates**: Each stage validates previous work before proceeding
✅ **Traceability**: Can trace decision back through all inputs
✅ **Incremental Progress**: Pipeline can be paused and resumed at any stage
✅ **Quality Assurance**: Multiple validation points catch issues early
✅ **Specialization**: Each stage uses the most appropriate agent type
✅ **Simple Orchestration**: No complex dependency management needed

## When to Use Pipeline Manager

**Best For**:
- Linear workflows with clear sequence
- Processes requiring validation between steps
- Workflows where each stage enriches previous output
- Quality assurance and review processes
- Data transformation pipelines
- Document creation with multiple review cycles
- Problems where order matters

**Not Ideal For**:
- Tasks that can run fully in parallel (use Swarm Coordinator)
- Complex dependencies between subtasks (use Hierarchical Planner)
- Exploratory problems with no clear sequence
- Problems requiring broad solution space exploration

## Specialized Pipeline Types

### Type 1: Validation Pipeline

```bash
# Create → Validate → Fix → Validate → Approve

# Multiple validation stages catch different issue types
PIPELINE_ID=$(./kb-cli add-entity \
  "Pipeline: Multi-Stage Validation" \
  "..." \
  '{"type":"pipeline","validation_pipeline":true}' | jq -r '.id')

# Stage 1: Create content (Researcher)
# Stage 2: Technical validation (Code Analyzer)
# Stage 3: Fix issues (Researcher)
# Stage 4: Quality validation (Code Analyzer)
# Stage 5: Approval (Decision Log)
```

### Type 2: Enrichment Pipeline

```bash
# Start simple → Add detail → Add context → Add cross-references

# Each stage adds more information
PIPELINE_ID=$(./kb-cli add-entity \
  "Pipeline: Progressive Enrichment" \
  "..." \
  '{"type":"pipeline","enrichment_pipeline":true}' | jq -r '.id')

# Stage 1: Basic research (Researcher - breadth)
# Stage 2: Deep analysis (Researcher - depth)
# Stage 3: Code examples (Code Analyzer)
# Stage 4: Related concepts (Learning Path)
# Stage 5: Historical decisions (Decision Log)
```

### Type 3: Transformation Pipeline

```bash
# Transform format/structure at each stage

# Raw data → Structured → Analyzed → Documented → Published
PIPELINE_ID=$(./kb-cli add-entity \
  "Pipeline: Data Transformation" \
  "..." \
  '{"type":"pipeline","transformation_pipeline":true}' | jq -r '.id')
```

## Pipeline Patterns

### Pattern: Fan-Out, Fan-In within Stage

```bash
# A single stage can internally use multiple agents, then continue pipeline

# Stage 2 uses both Code Analyzer AND Researcher in parallel
STAGE2_ID=$(./kb-cli add-entity "Stage 2: Multi-Agent Analysis" "..." '{"stage_num":2}' | jq -r '.id')

# Fan out
ANALYSIS_A=$(./kb-cli add-entity "Analysis A" "..." '{"parent_stage":"'$STAGE2_ID'"}' | jq -r '.id')
ANALYSIS_B=$(./kb-cli add-entity "Analysis B" "..." '{"parent_stage":"'$STAGE2_ID'"}' | jq -r '.id')

# Both execute in parallel
# ... wait for both ...

# Fan in: Combine results before continuing pipeline
COMBINED=$(combine_results $ANALYSIS_A $ANALYSIS_B)
./kb-cli update-entity $STAGE2_ID "$COMBINED" "$COMBINED" '{"status":"completed"}'

# Continue to Stage 3
```

### Pattern: Conditional Branching

```bash
# Pipeline can branch based on stage output

# Stage 2 completes
STAGE2_OUTPUT=$(./kb-cli get-entity $STAGE2_ID | jq -r '.content')

# Check condition (simplified - would use LLM)
if echo "$STAGE2_OUTPUT" | grep -qi "high risk"; then
  # Branch to risk mitigation sub-pipeline
  echo "High risk detected, branching to mitigation pipeline"
  
  MITIGATION_PIPELINE=$(./kb-cli add-entity \
    "Sub-Pipeline: Risk Mitigation" \
    "..." \
    '{"type":"pipeline","parent_pipeline":"'$PIPELINE_ID'","branch_condition":"high_risk"}' \
    | jq -r '.id')
  
  # ... execute mitigation stages ...
  
  # Resume main pipeline after mitigation
else
  # Continue normal flow to Stage 3
  echo "Low risk, continuing normal pipeline"
fi
```

### Pattern: Checkpoint and Resume

```bash
# Save pipeline state for resumption later

function save_checkpoint() {
  local pipeline_id=$1
  local current_stage=$2
  
  # Mark as checkpointed
  ./kb-cli update-entity $pipeline_id "" "" \
    '{"status":"checkpointed","checkpoint_stage":'$current_stage',"checkpoint_time":"'$(date -Iseconds)'"}'
  
  echo "Pipeline checkpointed at stage $current_stage"
}

function resume_from_checkpoint() {
  local pipeline_id=$1
  
  # Get checkpoint info
  local checkpoint_stage=$(./kb-cli get-entity $pipeline_id | jq -r '.metadata.checkpoint_stage')
  
  echo "Resuming pipeline from stage $checkpoint_stage"
  
  # Find stage entity
  local stage_id=$(./kb-cli get-links-from $pipeline_id | \
    jq -r '.[] | select(.metadata.stage_num == '$checkpoint_stage') | .id' | head -1)
  
  # Resume execution
  # ... continue pipeline from this stage ...
}

# Usage
save_checkpoint $PIPELINE_ID 3
# ... later ...
resume_from_checkpoint $PIPELINE_ID
```

## Complete Implementation Example

```python
#!/usr/bin/env python3
# pipeline_manager.py

import sys
import time
import json
from kb import KnowledgeBase

class PipelineManager:
    def __init__(self, name, stages):
        self.kb = KnowledgeBase()
        self.name = name
        self.stages = stages  # List of (agent_type, task_description)
        self.pipeline_id = None
        self.stage_ids = []
        
    def create_pipeline(self):
        """Initialize pipeline structure"""
        self.pipeline_id = self.kb.add_entity(
            f"Pipeline: {self.name}",
            f"Sequential pipeline with {len(self.stages)} stages",
            {
                "type": "pipeline",
                "total_stages": len(self.stages),
                "status": "stage_1",
                "current_stage": 1
            }
        )
        
        # Create stage entities
        for i, (agent, task) in enumerate(self.stages, 1):
            stage_id = self.kb.add_entity(
                f"Stage {i}: {task}",
                task,
                {
                    "type": "pipeline_stage",
                    "stage_num": i,
                    "parent_pipeline": self.pipeline_id,
                    "agent": agent,
                    "status": "pending"
                }
            )
            self.stage_ids.append(stage_id)
            self.kb.add_link(self.pipeline_id, stage_id, "stage")
            
            # Link to previous stage
            if i > 1:
                self.kb.add_link(self.stage_ids[i-2], stage_id, "feeds")
        
        print(f"Created pipeline: {self.pipeline_id}")
        return self.pipeline_id
    
    def execute_stage(self, stage_num, input_context=None):
        """Execute a single stage"""
        stage_id = self.stage_ids[stage_num - 1]
        stage_data = self.kb.get_entity(stage_id)
        agent = stage_data['metadata']['agent']
        task = stage_data['content']
        
        print(f"\n=== Executing Stage {stage_num}/{len(self.stages)} ===")
        print(f"  Agent: {agent}")
        print(f"  Task: {task[:60]}...")
        
        # Update status
        self.kb.update_entity(stage_id, None, None, {"status": "executing"})
        self.kb.update_entity(self.pipeline_id, None, None, {
            "current_stage": stage_num,
            "status": f"stage_{stage_num}"
        })
        
        # Build context
        context_text = ""
        if input_context:
            context_text = f"CONTEXT FROM PREVIOUS STAGES:\n{input_context}\n\n"
        
        # Create task
        self.kb.add_task(
            f"Execute Stage {stage_num}",
            f"@{agent}\n\n{context_text}YOUR TASK:\n{task}\n\nReturn summary in 1000 chars.",
            stage_id,
            {"agent": agent, "return_summary": True}
        )
        
        # Wait for completion (simplified - in production, use proper async)
        timeout = 300  # 5 minutes
        start = time.time()
        while time.time() - start < timeout:
            stage_data = self.kb.get_entity(stage_id)
            if stage_data['metadata'].get('status') == 'completed':
                break
            time.sleep(10)
            print("  Stage in progress...")
        
        # Get output
        output = self.kb.get_entity(stage_id)['content'][:1000]  # Compressed
        
        # Update metadata
        self.kb.update_entity(stage_id, None, None, {
            "status": "completed",
            "summary": output,
            "duration_seconds": int(time.time() - start)
        })
        
        print(f"  Stage {stage_num} complete")
        return output
    
    def execute_pipeline(self):
        """Execute entire pipeline sequentially"""
        print(f"Starting pipeline: {self.name}")
        print(f"Total stages: {len(self.stages)}")
        
        accumulated_context = ""
        
        for i in range(1, len(self.stages) + 1):
            # Execute stage with accumulated context
            output = self.execute_stage(i, accumulated_context)
            
            # Validate output
            if len(output) < 100:
                print(f"ERROR: Stage {i} output insufficient")
                self.kb.update_entity(self.pipeline_id, None, None, {
                    "status": "failed",
                    "failed_stage": i,
                    "error": "insufficient_output"
                })
                return False
            
            # Accumulate context for next stage
            accumulated_context += f"\n\n=== Stage {i} Output ===\n{output}"
            
            # Optionally compress if getting too large
            if len(accumulated_context) > 5000:
                # Keep only last 3 stages
                accumulated_context = "\n\n".join(accumulated_context.split("\n\n")[-3:])
        
        # Mark pipeline complete
        self.kb.update_entity(self.pipeline_id, None, None, {
            "status": "completed",
            "completion_time": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        
        print(f"\nPipeline complete: {self.pipeline_id}")
        print(f"  All {len(self.stages)} stages executed successfully")
        return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ./pipeline_manager.py <pipeline_name>")
        sys.exit(1)
    
    name = sys.argv[1]
    
    # Define pipeline stages
    stages = [
        ("researcher", "Research topic comprehensively"),
        ("code-analyzer", "Analyze implementation feasibility"),
        ("decision-log", "Document decision with rationale"),
        ("learning-path", "Create team training plan")
    ]
    
    # Execute
    manager = PipelineManager(name, stages)
    manager.create_pipeline()
    success = manager.execute_pipeline()
    
    sys.exit(0 if success else 1)
```

## Best Practices

1. **Keep Stages Focused**: Each stage should have a single clear responsibility.

2. **Compress Context**: Limit accumulated context to ~5000 chars total to manage memory.

3. **Validate Between Stages**: Each stage validates previous output before proceeding.

4. **Time Box Stages**: Set maximum execution time for each stage.

5. **Checkpointing**: Save state after each stage for resumability.

6. **Error Handling**: Define rollback or retry strategies for failed stages.

7. **Context Windows**: Be mindful of accumulating context size - compress or use references.

8. **Agent Specialization**: Each stage uses the most appropriate agent type.

9. **Handoff Documentation**: Clearly document what each stage expects as input and provides as output.

10. **Pipeline Versioning**: Track pipeline definitions in KB to evolve them over time.

## Comparison with Other Coordinators

| Aspect | Hierarchical Planner | Swarm Coordinator | **Pipeline Manager** |
|--------|---------------------|-------------------|---------------------|
| Decomposition | Top-down, recursive | Parallel, emergent | **Sequential, staged** |
| Execution | Sequential (respects deps) | Fully parallel | **Strictly sequential** |
| Best For | Clear goals, known structure | Uncertain problems | **Linear workflows** |
| Parallelism | Limited (within levels) | Maximum | **None** |
| Adaptability | Replan subtrees | Emergent strategy | **Pipeline modification** |
| Overhead | Medium (dependency tracking) | Low (fire and forget) | **Low** |
| Results | Structured hierarchy | Synthesized consensus | **Final output** |
| Context Management | Distributed | Independent | **Accumulated** |
| Validation | At leaves | At synthesis | **At every stage** |

## Advanced Pipeline Patterns

### Conditional Pipelines

```bash
# Pipeline branches based on intermediate results

# Stage 1-2 always execute
# Stage 3a OR 3b based on Stage 2 output
# Stage 4 consolidates whichever path was taken

if [ condition ]; then
  execute_stage 3a
else
  execute_stage 3b
fi
execute_stage 4  # Continues from either path
```

### Parallel Sub-Pipelines

```bash
# Fork pipeline into parallel sub-pipelines, then merge

# Stages 1-2: Sequential
# Stage 3: Forks into 3a, 3b, 3c (parallel sub-pipelines)
# Stage 4: Merges all three results
# Stages 5-6: Continue sequentially

# This combines pipeline + swarm patterns
```

### Streaming Pipelines

```bash
# Don't wait for full stage completion, stream partial results

# Stage 1 produces results incrementally
# Stage 2 starts processing as soon as Stage 1 has partial output
# Good for large datasets or long-running stages
```

## Conclusion

The Pipeline Manager provides clean, traceable orchestration through sequential stage execution. It excels at linear workflows where each stage enriches and validates the previous stage's output. The accumulated context pattern ensures that final stages have full visibility into all decisions and analysis that came before.

For problems requiring parallel exploration, use the **Swarm Coordinator**. For complex problems with interdependent subtasks, use the **Hierarchical Planner**.
