# Hierarchical Planner Agent

## Overview

The **Hierarchical Planner** is a meta-agent coordinator that orchestrates other agents through top-down recursive task decomposition. It breaks complex goals into hierarchies of subtasks, assigns them to specialist agents, monitors progress, and adapts the plan as needed.

**Key Principle**: Complex problems are best solved by decomposing them into progressively smaller, manageable subtasks until reaching atomic actions that specialist agents can execute.

## Purpose

Coordinate multiple specialist agents (Researcher, Code Analyzer, Learning Path, Decision Log) to accomplish complex, multi-faceted goals through systematic decomposition and delegation.

## How It Works

### 1. Goal Decomposition

The planner receives a high-level goal and recursively breaks it down:

```
Goal: "Migrate to Microservices Architecture"
├── Research Phase
│   ├── Research microservices patterns (→ Researcher)
│   ├── Research migration strategies (→ Researcher)
│   └── Research service boundaries (→ Researcher)
├── Analysis Phase
│   ├── Analyze current monolith structure (→ Code Analyzer)
│   ├── Identify technical debt blockers (→ Code Analyzer)
│   └── Map dependencies (→ Code Analyzer)
├── Planning Phase
│   ├── Design service boundaries (→ Decision Log)
│   ├── Choose technology stack (→ Decision Log)
│   └── Migration approach decision (→ Decision Log)
└── Enablement Phase
    ├── Team training curriculum (→ Learning Path)
    ├── DevOps skill requirements (→ Learning Path)
    └── Migration runbook creation (→ Learning Path)
```

### 2. Task Assignment

Each subtask is assigned to the most appropriate specialist agent based on:
- **Task type**: Research, analysis, learning, decision
- **Required expertise**: Domain knowledge needed
- **Dependencies**: What must complete first
- **Parallelization**: What can run simultaneously

### 3. Execution & Monitoring

The planner:
- Spawns specialist agents for leaf tasks
- Tracks completion status
- Collects compressed results (summaries only, not full context)
- Adapts plan based on findings
- Escalates blockers

### 4. Synthesis

Results from all subtasks are synthesized into:
- Coherent action plan
- Integrated knowledge graph
- Decision records with full context
- Risk assessment

## Agent Metadata Schema

```json
{
  "type": "plan",
  "strategy": "hierarchical",
  "goal": "High-level objective",
  "status": "planning|executing|completed|blocked",
  "depth": 0,
  "max_depth": 5,
  "parent_plan": null,
  "assigned_agent": null,
  "dependencies": [],
  "estimated_effort": "low|medium|high",
  "actual_effort": null,
  "blocker": null
}
```

## Workflows

### Workflow 1: Complex Feature Development

**Goal**: "Build GraphQL API with Real-time Subscriptions"

**Phase 1: Planning & Decomposition**

```bash
# Create root plan
PLAN_ID=$(./kb-cli add \
  "Plan: GraphQL API with Real-time Subscriptions" \
  "Top-level plan for feature development" \
  '{"type":"plan","strategy":"hierarchical","status":"planning","depth":0,"max_depth":4}' \
  | jq -r '.id')

# Decompose into major phases
RESEARCH_ID=$(./kb-cli add \
  "Research: GraphQL Best Practices" \
  "Research GraphQL patterns, real-time subscriptions, and WebSocket handling" \
  '{"type":"plan","strategy":"hierarchical","status":"planning","depth":1,"assigned_agent":"researcher","parent_plan":"'$PLAN_ID'"}' \
  | jq -r '.id')

ANALYSIS_ID=$(./kb-cli add \
  "Analysis: Current API Architecture" \
  "Analyze existing REST API, identify migration path, assess technical debt" \
  '{"type":"plan","strategy":"hierarchical","status":"planning","depth":1,"assigned_agent":"code-analyzer","parent_plan":"'$PLAN_ID'","dependencies":["'$RESEARCH_ID'"]}' \
  | jq -r '.id')

DECISION_ID=$(./kb-cli add \
  "Decision: Technology Stack" \
  "Choose GraphQL server library, subscription transport, caching strategy" \
  '{"type":"plan","strategy":"hierarchical","status":"planning","depth":1,"assigned_agent":"decision-log","parent_plan":"'$PLAN_ID'","dependencies":["'$RESEARCH_ID'","'$ANALYSIS_ID'"]}' \
  | jq -r '.id')

LEARNING_ID=$(./kb-cli add \
  "Learning: Team Enablement" \
  "Create training materials for GraphQL development and subscription patterns" \
  '{"type":"plan","strategy":"hierarchical","status":"planning","depth":1,"assigned_agent":"learning-path","parent_plan":"'$PLAN_ID'","dependencies":["'$DECISION_ID'"]}' \
  | jq -r '.id')

# Link plan hierarchy
./kb-cli link $PLAN_ID $RESEARCH_ID "decomposes_to"
./kb-cli link $PLAN_ID $ANALYSIS_ID "decomposes_to"
./kb-cli link $PLAN_ID $DECISION_ID "decomposes_to"
./kb-cli link $PLAN_ID $LEARNING_ID "decomposes_to"

# Link dependencies
./kb-cli link $RESEARCH_ID $ANALYSIS_ID "blocks"
./kb-cli link $ANALYSIS_ID $DECISION_ID "informs"
./kb-cli link $DECISION_ID $LEARNING_ID "enables"
```

**Phase 2: Execute Research (Depth 1)**

```bash
# Further decompose research phase
PATTERNS_ID=$(./kb-cli add \
  "Research: Query Patterns" \
  "Schema design, resolver patterns, N+1 problem solutions" \
  '{"type":"plan","depth":2,"assigned_agent":"researcher","parent_plan":"'$RESEARCH_ID'","status":"executing"}' \
  | jq -r '.id')

SUBSCRIPTIONS_ID=$(./kb-cli add \
  "Research: Real-time Subscriptions" \
  "WebSocket protocols, GraphQL subscriptions, server-sent events comparison" \
  '{"type":"plan","depth":2,"assigned_agent":"researcher","parent_plan":"'$RESEARCH_ID'","status":"executing"}' \
  | jq -r '.id')

PERFORMANCE_ID=$(./kb-cli add \
  "Research: Performance Optimization" \
  "Caching strategies, DataLoader pattern, query complexity analysis" \
  '{"type":"plan","depth":2,"assigned_agent":"researcher","parent_plan":"'$RESEARCH_ID'","status":"executing"}' \
  | jq -r '.id')

# These can execute in parallel - spawn as background tasks
./kb-cli add-task \
  "Execute: Research Query Patterns" \
  "@researcher research 'GraphQL query patterns best practices schema design resolver N+1 solutions'" \
  $PATTERNS_ID \
  '{"priority":"high","agent":"researcher","parallel":true}'

./kb-cli add-task \
  "Execute: Research Subscriptions" \
  "@researcher research 'GraphQL subscriptions WebSocket real-time protocols comparison'" \
  $SUBSCRIPTIONS_ID \
  '{"priority":"high","agent":"researcher","parallel":true}'

./kb-cli add-task \
  "Execute: Research Performance" \
  "@researcher research 'GraphQL performance caching DataLoader query complexity'" \
  $PERFORMANCE_ID \
  '{"priority":"high","agent":"researcher","parallel":true}'
```

**Phase 3: Monitor & Collect Results**

```bash
# Wait for research tasks to complete
while [ $(./kb-cli tasks pending | jq -r '. | map(select(.entity_id == "'$RESEARCH_ID'")) | length') -gt 0 ]; do
  echo "Waiting for research tasks to complete..."
  sleep 30
  
  # Check for blockers
  BLOCKER=$(./kb-cli get $RESEARCH_ID | jq -r '.metadata.blocker // empty')
  if [ ! -z "$BLOCKER" ]; then
    echo "Blocker detected: $BLOCKER"
    # Planner adapts: spawn resolution task or escalate
    break
  fi
done

# Collect compressed results (summaries only)
PATTERNS_SUMMARY=$(./kb-cli export $PATTERNS_ID | head -50)
SUBSCRIPTIONS_SUMMARY=$(./kb-cli export $SUBSCRIPTIONS_ID | head -50)
PERFORMANCE_SUMMARY=$(./kb-cli export $PERFORMANCE_ID | head -50)

# Mark research phase complete
./kb-cli update $RESEARCH_ID \
  "Research Phase Complete" \
  "$(cat <<EOF
# Research Summary

## Query Patterns
$PATTERNS_SUMMARY

## Subscriptions
$SUBSCRIPTIONS_SUMMARY

## Performance
$PERFORMANCE_SUMMARY

## Key Findings
- Schema-first design recommended
- WebSocket transport for subscriptions
- DataLoader pattern essential for N+1
- Redis caching for query results
EOF
)" \
  '{"status":"completed","actual_effort":"medium"}'
```

**Phase 4: Proceed to Next Phase**

```bash
# Research complete, now execute analysis
# Similar decomposition for Code Analyzer tasks...
```

### Workflow 2: Emergency Incident Response

**Goal**: "Resolve Production Database Performance Issue"

**Rapid Decomposition for Time-Critical Scenarios**

```bash
# Create incident plan with higher urgency
INCIDENT_ID=$(./kb-cli add \
  "Incident: DB Performance Degradation" \
  "Production database queries timing out, affecting 40% of users" \
  '{"type":"plan","strategy":"hierarchical","status":"executing","priority":"critical","max_depth":3}' \
  | jq -r '.id')

# Parallel investigation tracks
ANALYZE_ID=$(./kb-cli add \
  "Analyze: Query Performance" \
  "Identify slow queries, missing indexes, lock contention" \
  '{"type":"plan","depth":1,"assigned_agent":"code-analyzer","parent_plan":"'$INCIDENT_ID'","status":"executing"}' \
  | jq -r '.id')

RESEARCH_ID=$(./kb-cli add \
  "Research: Known Issues" \
  "Search for similar incidents, database version bugs, common remedies" \
  '{"type":"plan","depth":1,"assigned_agent":"researcher","parent_plan":"'$INCIDENT_ID'","status":"executing"}' \
  | jq -r '.id')

# Execute immediately in parallel
./kb-cli add-task "Analyze slow queries" \
  "@code-analyzer analyze database logs and identify performance bottlenecks" \
  $ANALYZE_ID '{"priority":"critical","parallel":true}'

./kb-cli add-task "Research similar incidents" \
  "@researcher search for 'database performance degradation similar incidents solutions'" \
  $RESEARCH_ID '{"priority":"critical","parallel":true}'

# Quick monitoring loop (5-minute checkpoints for critical incidents)
for i in {1..12}; do
  sleep 300  # 5 minutes
  
  # Check if root cause identified
  ANALYSIS_STATUS=$(./kb-cli get $ANALYZE_ID | jq -r '.metadata.status')
  if [ "$ANALYSIS_STATUS" == "completed" ]; then
    # Found issue - create decision record
    DECISION_ID=$(./kb-cli add \
      "Decision: Immediate Mitigation" \
      "$(./kb-cli export $ANALYZE_ID | head -100)" \
      '{"type":"plan","depth":1,"assigned_agent":"decision-log","parent_plan":"'$INCIDENT_ID'","status":"completed"}' \
      | jq -r '.id')
    
    echo "Root cause identified and documented: $DECISION_ID"
    break
  fi
done
```

### Workflow 3: Multi-Month Strategic Initiative

**Goal**: "Platform Modernization Program"

**Long-running Program with Quarterly Milestones**

```bash
# Create program-level plan (12-month initiative)
PROGRAM_ID=$(./kb-cli add \
  "Program: Platform Modernization" \
  "Comprehensive modernization: architecture, technology stack, team capabilities" \
  '{"type":"plan","strategy":"hierarchical","status":"planning","max_depth":6,"duration":"12 months","milestones":["Q1","Q2","Q3","Q4"]}' \
  | jq -r '.id')

# Q1: Assessment & Planning
Q1_ID=$(./kb-cli add \
  "Q1 Milestone: Assessment" \
  "Current state analysis, gap analysis, roadmap creation" \
  '{"type":"plan","depth":1,"parent_plan":"'$PROGRAM_ID'","milestone":"Q1","status":"planning"}' \
  | jq -r '.id')

# Q1 decomposes further
Q1_RESEARCH=$(./kb-cli add "Research: Modern Architecture Patterns" "..." \
  '{"type":"plan","depth":2,"parent_plan":"'$Q1_ID'","assigned_agent":"researcher"}' | jq -r '.id')

Q1_ANALYSIS=$(./kb-cli add "Analysis: Technical Debt Assessment" "..." \
  '{"type":"plan","depth":2,"parent_plan":"'$Q1_ID'","assigned_agent":"code-analyzer"}' | jq -r '.id')

# Q2-Q4: Similar decomposition...

# Track at program level
./kb-cli add-task "Review Q1 Progress" \
  "Coordinator reviews Q1 milestone completion and adjusts Q2 plan" \
  $PROGRAM_ID \
  '{"scheduled_date":"2026-04-01","agent":"hierarchical-planner","review":true}'
```

## Key Patterns

### Pattern 1: Dependency Management

```bash
# Task A must complete before Task B starts
./kb-cli link $TASK_A_ID $TASK_B_ID "blocks"

# Before executing Task B, verify dependencies
BLOCKED=$(./kb-cli links $TASK_B_ID | jq -r '.[] | select(.link_type == "blocks") | .id')
for DEP in $BLOCKED; do
  STATUS=$(./kb-cli get $DEP | jq -r '.metadata.status')
  if [ "$STATUS" != "completed" ]; then
    echo "Dependency $DEP not complete, cannot start Task B"
    exit 1
  fi
done
```

### Pattern 2: Effort Estimation & Tracking

```bash
# Estimate before execution
./kb-cli add "Research: Topic X" "..." \
  '{"estimated_effort":"high","estimated_hours":40}'

# Track actual effort
START_TIME=$(date +%s)
# ... execute task ...
END_TIME=$(date +%s)
ACTUAL_HOURS=$(( ($END_TIME - $START_TIME) / 3600 ))

./kb-cli update $TASK_ID "..." "..." \
  "{\"actual_effort\":\"high\",\"actual_hours\":$ACTUAL_HOURS}"

# Learn from estimation errors for future planning
ACCURACY=$(echo "scale=2; $ACTUAL_HOURS / 40" | bc)
echo "Estimation accuracy: $ACCURACY"
```

### Pattern 3: Dynamic Replanning

```bash
# If a subtask reveals unexpected complexity
TASK_STATUS=$(./kb-cli get $TASK_ID | jq -r '.metadata.status')
if [ "$TASK_STATUS" == "blocked" ]; then
  # Extract blocker reason
  BLOCKER=$(./kb-cli get $TASK_ID | jq -r '.metadata.blocker')
  
  # Planner creates new subtask to resolve blocker
  UNBLOCK_ID=$(./kb-cli add \
    "Unblock: $BLOCKER" \
    "Resolve blocker for $TASK_ID" \
    '{"type":"plan","depth":'$((DEPTH+1))',"parent_plan":"'$PLAN_ID'","priority":"high"}' \
    | jq -r '.id')
  
  # Link as prerequisite
  ./kb-cli link $UNBLOCK_ID $TASK_ID "unblocks"
fi
```

### Pattern 4: Progress Reporting

```bash
# Generate progress report for plan
PLAN_ID=$1

# Count subtasks by status
TOTAL=$(./kb-cli links $PLAN_ID | jq -r '. | length')
COMPLETED=$(./kb-cli links $PLAN_ID | \
  jq -r '.[] | select(.metadata.status == "completed") | .id' | wc -l)
IN_PROGRESS=$(./kb-cli links $PLAN_ID | \
  jq -r '.[] | select(.metadata.status == "executing") | .id' | wc -l)
BLOCKED=$(./kb-cli links $PLAN_ID | \
  jq -r '.[] | select(.metadata.status == "blocked") | .id' | wc -l)

PERCENT_COMPLETE=$(echo "scale=0; 100 * $COMPLETED / $TOTAL" | bc)

echo "Plan Progress: $PERCENT_COMPLETE% ($COMPLETED/$TOTAL tasks)"
echo "  In Progress: $IN_PROGRESS"
echo "  Blocked: $BLOCKED"

# Update plan metadata
./kb-cli update $PLAN_ID "..." "..." \
  "{\"progress\":$PERCENT_COMPLETE,\"completed\":$COMPLETED,\"total\":$TOTAL}"
```

## Integration with Specialist Agents

### Researcher Agent

```bash
# Planner delegates research subtask
./kb-cli add-task \
  "Research: ${TOPIC}" \
  "@researcher research '${TOPIC} ${KEYWORDS}'" \
  $TASK_ID \
  '{"agent":"researcher","return_summary":true,"max_length":500}'
```

### Code Analyzer Agent

```bash
# Planner delegates analysis subtask
./kb-cli add-task \
  "Analyze: ${COMPONENT}" \
  "@code-analyzer analyze ${FILE_PATH} and document architecture" \
  $TASK_ID \
  '{"agent":"code-analyzer","git_hash":"'$(git rev-parse HEAD)'"}'
```

### Learning Path Agent

```bash
# Planner delegates curriculum creation
./kb-cli add-task \
  "Create Learning Path: ${SKILL}" \
  "@learning create curriculum for '${SKILL}' with prerequisites" \
  $TASK_ID \
  '{"agent":"learning-path","target_audience":"team","duration":"2 weeks"}'
```

### Decision Log Agent

```bash
# Planner delegates decision documentation
./kb-cli add-task \
  "Document Decision: ${DECISION}" \
  "@decision-log document decision '${DECISION}' with alternatives and rationale" \
  $TASK_ID \
  '{"agent":"decision-log","status":"accepted","review_date":"'$(date -d '+6 months' +%Y-%m-%d)'"}'
```

## Advantages of Hierarchical Planning

✅ **Clear Structure**: Explicit parent-child relationships show decomposition
✅ **Dependency Tracking**: Easy to identify what must complete first
✅ **Progress Visibility**: Percentage complete at each level
✅ **Effort Estimation**: Learn from historical data to improve future estimates
✅ **Adaptability**: Can replan subtrees without affecting rest of hierarchy
✅ **Accountability**: Each subtask has a clear owner (assigned agent)
✅ **Parallel Execution**: Sibling tasks with no dependencies run simultaneously

## When to Use Hierarchical Planner

**Best For**:
- Complex, multi-phase projects
- Goals with clear decomposition paths
- Situations requiring careful dependency management
- Long-running initiatives with milestones
- Programs requiring progress tracking and reporting

**Not Ideal For**:
- Highly exploratory problems with unknown structure
- Tasks requiring emergent strategy
- Simple linear workflows (use Pipeline Manager instead)
- Problems requiring broad solution space exploration (use Swarm Coordinator instead)

## Example: Complete Implementation Script

```bash
#!/bin/bash
# hierarchical_planner.sh - Execute a hierarchical plan

PLAN_ID=$1
MAX_PARALLEL=${2:-5}  # Max parallel tasks

function decompose_task() {
  local task_id=$1
  local depth=$2
  local max_depth=$3
  
  # Check if atomic (no further decomposition needed)
  local agent=$(./kb-cli get $task_id | jq -r '.metadata.assigned_agent // empty')
  if [ ! -z "$agent" ]; then
    # Atomic task - execute
    execute_task $task_id $agent
    return
  fi
  
  # Check depth limit
  if [ $depth -ge $max_depth ]; then
    echo "Max depth reached for $task_id, marking as atomic"
    return
  fi
  
  # Get subtasks
  local subtasks=$(./kb-cli links $task_id | \
    jq -r '.[] | select(.link_type == "decomposes_to") | .id')
  
  if [ -z "$subtasks" ]; then
    echo "No subtasks for $task_id, needs decomposition"
    return
  fi
  
  # Recursively process subtasks
  for subtask in $subtasks; do
    decompose_task $subtask $(($depth + 1)) $max_depth
  done
}

function execute_task() {
  local task_id=$1
  local agent=$2
  
  echo "Executing task $task_id with agent $agent"
  
  # Get task details
  local task_data=$(./kb-cli get $task_id)
  local title=$(echo "$task_data" | jq -r '.title')
  
  # Create execution task
  ./kb-cli add-task \
    "Execute: $title" \
    "@$agent execute task $task_id" \
    $task_id \
    '{"priority":"high","agent":"'$agent'"}'
  
  # Mark as executing
  ./kb-cli update $task_id "" "" '{"status":"executing"}'
}

function monitor_progress() {
  local plan_id=$1
  
  while true; do
    # Check completion
    local pending=$(./kb-cli tasks pending | \
      jq -r '. | map(select(.metadata.plan_id == "'$plan_id'")) | length')
    
    if [ $pending -eq 0 ]; then
      echo "All tasks complete"
      break
    fi
    
    echo "Pending tasks: $pending"
    sleep 60
  done
}

# Main execution
echo "Starting hierarchical plan: $PLAN_ID"
MAX_DEPTH=$(./kb-cli get $PLAN_ID | jq -r '.metadata.max_depth // 5')

decompose_task $PLAN_ID 0 $MAX_DEPTH
monitor_progress $PLAN_ID

echo "Plan execution complete"
```

## Best Practices

1. **Keep Depth Reasonable**: 3-5 levels max. Deeper hierarchies become hard to manage.

2. **Atomic Tasks at Leaves**: Ensure leaf tasks are executable by a single specialist agent.

3. **Explicit Dependencies**: Always link dependencies with "blocks" or "requires" links.

4. **Summary-Only Results**: Each subtask returns compressed summary (500-1000 chars), not full context.

5. **Progress Checkpoints**: Monitor and report progress at each level regularly.

6. **Adaptive Replanning**: If subtask reveals complexity, dynamically add new subtasks.

7. **Parallel Where Possible**: Execute independent sibling tasks in parallel.

8. **Clear Ownership**: Each task assigned to exactly one agent.

9. **Historical Learning**: Track estimated vs actual effort to improve future planning.

10. **Escalation Path**: Define how blockers are handled (create unblocking tasks or escalate to human).

## Evaluation Loops: Evaluate → Replan

The Hierarchical Planner supports **evaluation loops** — after completing a phase, it evaluates whether findings change the plan, then replans if needed. This prevents executing a stale plan when early phases reveal unexpected information.

### How It Works

```
Goal: "Migrate to Microservices"
├── Phase 1: Research ──────────────────── EXECUTE
│   └── Result: "Monolith has 47 circular deps"
├── ★ EVALUATE (iteration 1) ★             
│   ├── Confidence: 0.4 (low — unexpected complexity)
│   ├── Gaps: ["dependency resolution strategy"]
│   ├── Decision: LOOP → replan Phase 2
│   └── Rationale: Original Phase 2 assumed clean boundaries
├── Phase 2: Analysis (REPLANNED) ──────── EXECUTE
│   └── Result: "Strangler fig pattern viable for 3 services"
├── ★ EVALUATE (iteration 2) ★
│   ├── Confidence: 0.75
│   ├── Gaps: []
│   ├── Decision: CONVERGE
│   └── Rationale: Clear path identified
├── Phase 3: Decision ──────────────────── EXECUTE
└── Phase 4: Training ──────────────────── EXECUTE
```

### Evaluate-Replan Pattern

```bash
#!/bin/bash
# evaluate_and_replan.sh — Hierarchical Planner with evaluation loops

PLAN_ID=$1
MAX_EVAL_ITERATIONS=${2:-5}

# Create evaluation tracker
EVAL_ID=$(./kb-cli add-eval $PLAN_ID $MAX_EVAL_ITERATIONS \
  '{"min_confidence":0.7,"max_gaps":2,"max_contradictions":0}' \
  | jq -r '.eval_id')

echo "Plan: $PLAN_ID, Eval: $EVAL_ID"

# Get phases in dependency order
PHASES=$(./kb-cli links $PLAN_ID | \
  jq -r '.[] | select(.link_type == "decomposes_to") | .id')

ITERATION=1
ACCUMULATED_FINDINGS=""

for phase_id in $PHASES; do
  # Execute phase
  PHASE_DATA=$(./kb-cli get $phase_id)
  AGENT=$(echo "$PHASE_DATA" | jq -r '.metadata.assigned_agent')
  echo "=== Executing Phase: $(echo "$PHASE_DATA" | jq -r '.title') ==="
  
  # ... execute phase with agent ...
  PHASE_OUTPUT=$(./kb-cli export $phase_id | head -80)
  ACCUMULATED_FINDINGS="$ACCUMULATED_FINDINGS\n$PHASE_OUTPUT"
  
  # ★ EVALUATE after each phase ★
  echo "--- Evaluating (iteration $ITERATION) ---"
  
  # Assess confidence, gaps, contradictions from findings
  # (In production, use LLM to analyze findings against original goal)
  GAPS=$(identify_gaps "$ACCUMULATED_FINDINGS")
  CONTRADICTIONS=$(identify_contradictions "$ACCUMULATED_FINDINGS")
  CONFIDENCE=$(assess_confidence "$ACCUMULATED_FINDINGS")
  
  # Update evaluation state
  ./kb-cli update-eval $EVAL_ID \
    '{"confidence":'$CONFIDENCE',"gaps":'$GAPS',"contradictions":'$CONTRADICTIONS',"iteration":'$ITERATION'}'
  
  # Check convergence
  CONVERGENCE=$(./kb-cli converged $EVAL_ID)
  CONVERGED=$(echo "$CONVERGENCE" | jq -r '.converged')
  
  if [ "$CONVERGED" == "true" ]; then
    echo "✓ Converged: $(echo "$CONVERGENCE" | jq -r '.reason')"
    ./kb-cli update-eval $EVAL_ID '{"status":"converged","decision":"converge"}'
    # Continue to next phase without replanning
  else
    echo "✗ Not converged: $(echo "$CONVERGENCE" | jq -r '.reason')"
    
    # REPLAN: Modify remaining phases based on findings
    REMAINING_PHASES=$(get_remaining_phases $PLAN_ID $phase_id)
    
    for remaining_id in $REMAINING_PHASES; do
      # Adjust scope, add sub-tasks, or change agent assignment
      ./kb-cli update $remaining_id "" \
        "REPLANNED (eval iteration $ITERATION): Adjusted based on: $(echo "$CONVERGENCE" | jq -r '.reason')" \
        '{"replanned_at_iteration":'$ITERATION'}'
    done
    
    # Optionally add new phases to address gaps
    for gap in $(echo "$GAPS" | jq -r '.[]'); do
      GAP_PHASE=$(./kb-cli add \
        "Gap Fill: $gap" \
        "Added by evaluation loop iteration $ITERATION to address gap" \
        '{"type":"plan","parent_plan":"'$PLAN_ID'","added_by_eval":'$ITERATION'}' \
        | jq -r '.id')
      ./kb-cli link $PLAN_ID $GAP_PHASE "decomposes_to"
    done
    
    ./kb-cli update-eval $EVAL_ID '{"decision":"loop","rationale":"Replanned remaining phases"}'
    ITERATION=$((ITERATION + 1))
  fi
done

# Final evaluation
FINAL=$(./kb-cli converged $EVAL_ID)
echo ""
echo "=== Plan Complete ==="
echo "Iterations: $ITERATION"
echo "Final confidence: $(echo "$FINAL" | jq -r '.confidence')"
echo "Remaining gaps: $(echo "$FINAL" | jq -r '.gaps | length')"
```

### When to Evaluate

| Trigger | Action |
|---------|--------|
| Phase completes | Evaluate findings vs plan assumptions |
| Unexpected complexity found | Replan remaining phases |
| New dependencies discovered | Add blocking links, reorder |
| Confidence drops below threshold | Spawn additional research phases |
| Max iterations reached | Escalate to human with findings summary |

## Conclusion

The Hierarchical Planner provides systematic, traceable orchestration of complex goals through recursive decomposition. It excels at structured problems with clear dependency chains and enables effective coordination of multiple specialist agents toward a unified objective.

For exploratory problems or broad solution space exploration, consider the **Swarm Coordinator**. For linear sequential workflows, consider the **Pipeline Manager**.

## Recursive Agent Spawning

Specialist agents assigned to leaf tasks in the plan can themselves become sub-planners, decomposing their task further and spawning sub-agents. This enables the plan tree to grow organically based on discovered complexity.

### How It Works

```
Plan: "Evaluate fusion reactor materials"
├── Research Phase (researcher)
│   ├── HTS Magnets (researcher) — assigned agent discovers 3 sub-questions
│   │   ├── REBCO manufacturing (spawned researcher, depth 3)
│   │   ├── Bi-2212 cost analysis (spawned researcher, depth 3)
│   │   └── Comparison pipeline (spawned pipeline_manager, depth 3)
│   │       ├── Stage 1: Gather properties
│   │       └── Stage 2: Score & rank
│   └── Neutron Shielding (researcher) — single-level, sufficient
├── Analysis Phase (code-analyzer)
└── Decision Phase (decision-log)
```

### Integration with Plan Tracking

```python
from kb import KnowledgeBase
kb = KnowledgeBase()

# Leaf agent checks if it should decompose further
budget = kb.check_spawn_budget(my_task_id, max_depth=5, max_total=50)

if budget['can_spawn'] and task_is_complex:
    # Spawn sub-tasks, each linked to parent with 'spawned' edge
    sub1 = kb.spawn_sub_entity(my_task_id,
        'REBCO manufacturing processes',
        'Research current REBCO tape manufacturing and scaling challenges',
        agent_type='researcher')
    
    sub2 = kb.spawn_sub_entity(my_task_id,
        'Bi-2212 cost trajectory',
        'Analyze Bi-2212 cost trends and production scaling',
        agent_type='researcher')
    
    # Spawn a sub-coordinator for comparison
    sub3 = kb.spawn_sub_entity(my_task_id,
        'Pipeline: Compare HTS candidates',
        'Sequential comparison pipeline',
        agent_type='pipeline_manager')
else:
    # Budget exhausted or task is atomic — research directly
    pass
```

### Depth-Aware Replanning

When a leaf task spawns sub-agents, the planner's evaluate→replan loop should account for the expanded tree:

```python
# After sub-agents complete, reflect on the expanded subtree
reflection = kb.reflect_on_entity(my_task_id)
# Checks: unsourced claims, weak evidence, contradictions across all children

# Get spawn context to see sibling progress
ctx = kb.get_spawn_context(my_task_id)
# Informs replanning: which siblings are done, what gaps remain
```

See the **Swarm Coordinator** doc for the full recursive spawning prompt template, budget enforcement details, and cross-coordinator spawning patterns.
