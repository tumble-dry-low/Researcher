#!/bin/bash
# Meta-Agent Coordinators Quick Start
# Demonstrates all three coordination patterns

echo "==================================="
echo "Meta-Agent Coordinators Demo"
echo "==================================="
echo ""

# Ensure kb.db exists
if [ ! -f "kb.db" ]; then
  echo "Initializing knowledge base..."
  ./kb-cli add-entity "System Initialized" "KB created" '{"type":"system"}' > /dev/null
fi

echo "Choose a coordinator to demo:"
echo ""
echo "1. Hierarchical Planner - Top-down task decomposition"
echo "2. Swarm Coordinator - Parallel exploration with synthesis"
echo "3. Pipeline Manager - Sequential stage execution"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
  1)
    echo ""
    echo "=== Hierarchical Planner Demo ==="
    echo "Goal: Build GraphQL API Feature"
    echo ""
    
    # Create hierarchical plan
    PLAN_ID=$(./kb-cli add-entity \
      "Plan: Build GraphQL API" \
      "Top-level plan decomposed into phases" \
      '{"type":"plan","strategy":"hierarchical","max_depth":3,"status":"planning"}' \
      | jq -r '.id')
    
    echo "Created plan: $PLAN_ID"
    echo ""
    echo "Decomposing into phases..."
    
    # Phase 1: Research
    RESEARCH_ID=$(./kb-cli add-entity \
      "Phase 1: Research GraphQL" \
      "Research patterns, best practices, trade-offs" \
      '{"type":"plan","depth":1,"assigned_agent":"researcher","parent_plan":"'$PLAN_ID'"}' \
      | jq -r '.id')
    
    # Phase 2: Analysis
    ANALYSIS_ID=$(./kb-cli add-entity \
      "Phase 2: Analyze Current API" \
      "Assess migration complexity and integration points" \
      '{"type":"plan","depth":1,"assigned_agent":"code-analyzer","parent_plan":"'$PLAN_ID'","dependencies":["'$RESEARCH_ID'"]}' \
      | jq -r '.id')
    
    # Phase 3: Decision
    DECISION_ID=$(./kb-cli add-entity \
      "Phase 3: Technology Decisions" \
      "Document GraphQL server choice and architecture" \
      '{"type":"plan","depth":1,"assigned_agent":"decision-log","parent_plan":"'$PLAN_ID'","dependencies":["'$RESEARCH_ID'","'$ANALYSIS_ID'"]}' \
      | jq -r '.id')
    
    # Phase 4: Training
    TRAINING_ID=$(./kb-cli add-entity \
      "Phase 4: Team Training" \
      "Create GraphQL curriculum for team" \
      '{"type":"plan","depth":1,"assigned_agent":"learning-path","parent_plan":"'$PLAN_ID'","dependencies":["'$DECISION_ID'"]}' \
      | jq -r '.id')
    
    # Link hierarchy
    ./kb-cli add-link $PLAN_ID $RESEARCH_ID "decomposes_to" > /dev/null
    ./kb-cli add-link $PLAN_ID $ANALYSIS_ID "decomposes_to" > /dev/null
    ./kb-cli add-link $PLAN_ID $DECISION_ID "decomposes_to" > /dev/null
    ./kb-cli add-link $PLAN_ID $TRAINING_ID "decomposes_to" > /dev/null
    
    # Link dependencies
    ./kb-cli add-link $RESEARCH_ID $ANALYSIS_ID "blocks" > /dev/null
    ./kb-cli add-link $ANALYSIS_ID $DECISION_ID "informs" > /dev/null
    ./kb-cli add-link $DECISION_ID $TRAINING_ID "enables" > /dev/null
    
    echo "  ✓ Phase 1: Research (→ @researcher)"
    echo "  ✓ Phase 2: Analysis (→ @code-analyzer, depends on Phase 1)"
    echo "  ✓ Phase 3: Decision (→ @decision-log, depends on Phases 1-2)"
    echo "  ✓ Phase 4: Training (→ @learning-path, depends on Phase 3)"
    echo ""
    echo "Plan structure created!"
    echo "View: ./kb-cli get-entity $PLAN_ID"
    echo ""
    echo "Next steps:"
    echo "  1. Phases 1-4 would be recursively decomposed further"
    echo "  2. Leaf tasks assigned to specialist agents"
    echo "  3. Execution respects dependency graph"
    echo "  4. Progress tracked at each level"
    ;;
    
  2)
    echo ""
    echo "=== Swarm Coordinator Demo ==="
    echo "Question: Should we adopt GraphQL?"
    echo ""
    
    # Create swarm
    SWARM_ID=$(./kb-cli add-entity \
      "Swarm: GraphQL Adoption" \
      "Parallel exploration from multiple angles" \
      '{"type":"swarm","swarm_size":8,"time_limit_minutes":20,"status":"spawning"}' \
      | jq -r '.id')
    
    echo "Created swarm: $SWARM_ID"
    echo "Spawning 8 agents to explore in parallel..."
    echo ""
    
    # Spawn diverse exploration agents
    ANGLES=(
      "researcher:GraphQL benefits and success stories"
      "researcher:GraphQL drawbacks and production challenges"
      "researcher:GraphQL vs REST performance comparison"
      "code-analyzer:Current REST API complexity and pain points"
      "code-analyzer:Team GraphQL expertise assessment"
      "decision-log:Past API technology decisions and outcomes"
      "learning-path:GraphQL learning curve analysis"
      "researcher:GraphQL migration strategies and effort"
    )
    
    AGENT_COUNT=1
    for angle in "${ANGLES[@]}"; do
      IFS=':' read -r agent query <<< "$angle"
      
      AGENT_ID=$(./kb-cli add-entity \
        "Explore: $query" \
        "Swarm member $AGENT_COUNT" \
        '{"type":"exploration","parent_swarm":"'$SWARM_ID'","agent":"'$agent'","status":"spawned"}' \
        | jq -r '.id')
      
      ./kb-cli add-link $SWARM_ID $AGENT_ID "spawns" > /dev/null
      
      echo "  ✓ Agent $AGENT_COUNT: @$agent explores '$query'"
      AGENT_COUNT=$((AGENT_COUNT + 1))
    done
    
    echo ""
    echo "All 8 agents spawned!"
    echo ""
    echo "Next steps:"
    echo "  1. All agents execute in parallel (time-boxed: 20min)"
    echo "  2. Coordinator monitors completion (80% threshold)"
    echo "  3. Findings synthesized to identify consensus"
    echo "  4. Contradictions flagged for resolution"
    echo "  5. Gaps identified and follow-up tasks created"
    echo ""
    echo "View swarm: ./kb-cli get-entity $SWARM_ID"
    ;;
    
  3)
    echo ""
    echo "=== Pipeline Manager Demo ==="
    echo "Pipeline: Feature Specification to Implementation"
    echo ""
    
    # Create pipeline
    PIPELINE_ID=$(./kb-cli add-entity \
      "Pipeline: GraphQL Feature Delivery" \
      "Research → Analyze → Decide → Train → Validate" \
      '{"type":"pipeline","strategy":"sequential_chaining","total_stages":5,"status":"stage_1","current_stage":1}' \
      | jq -r '.id')
    
    echo "Created pipeline: $PIPELINE_ID"
    echo "Creating 5 sequential stages..."
    echo ""
    
    # Stage 1
    STAGE1_ID=$(./kb-cli add-entity \
      "Stage 1: Research GraphQL" \
      "Comprehensive research on GraphQL patterns and best practices" \
      '{"type":"pipeline_stage","stage_num":1,"parent_pipeline":"'$PIPELINE_ID'","agent":"researcher","status":"ready"}' \
      | jq -r '.id')
    ./kb-cli add-link $PIPELINE_ID $STAGE1_ID "stage" > /dev/null
    echo "  Stage 1: Research (→ @researcher)"
    echo "    Input: None (first stage)"
    echo "    Output: Research findings → Stage 2"
    echo ""
    
    # Stage 2
    STAGE2_ID=$(./kb-cli add-entity \
      "Stage 2: Analyze Current API" \
      "Analyze existing codebase considering research findings" \
      '{"type":"pipeline_stage","stage_num":2,"parent_pipeline":"'$PIPELINE_ID'","agent":"code-analyzer","status":"waiting","input_entity":"'$STAGE1_ID'"}' \
      | jq -r '.id')
    ./kb-cli add-link $PIPELINE_ID $STAGE2_ID "stage" > /dev/null
    ./kb-cli add-link $STAGE1_ID $STAGE2_ID "feeds" > /dev/null
    echo "  Stage 2: Analysis (→ @code-analyzer)"
    echo "    Input: Stage 1 output"
    echo "    Output: Feasibility analysis → Stage 3"
    echo ""
    
    # Stage 3
    STAGE3_ID=$(./kb-cli add-entity \
      "Stage 3: Document Decisions" \
      "Create ADRs for technology and architecture choices" \
      '{"type":"pipeline_stage","stage_num":3,"parent_pipeline":"'$PIPELINE_ID'","agent":"decision-log","status":"waiting","input_entity":"'$STAGE2_ID'"}' \
      | jq -r '.id')
    ./kb-cli add-link $PIPELINE_ID $STAGE3_ID "stage" > /dev/null
    ./kb-cli add-link $STAGE2_ID $STAGE3_ID "feeds" > /dev/null
    echo "  Stage 3: Decision (→ @decision-log)"
    echo "    Input: Stages 1-2 output"
    echo "    Output: Decision records → Stage 4"
    echo ""
    
    # Stage 4
    STAGE4_ID=$(./kb-cli add-entity \
      "Stage 4: Team Training Plan" \
      "Create curriculum based on decisions and requirements" \
      '{"type":"pipeline_stage","stage_num":4,"parent_pipeline":"'$PIPELINE_ID'","agent":"learning-path","status":"waiting","input_entity":"'$STAGE3_ID'"}' \
      | jq -r '.id')
    ./kb-cli add-link $PIPELINE_ID $STAGE4_ID "stage" > /dev/null
    ./kb-cli add-link $STAGE3_ID $STAGE4_ID "feeds" > /dev/null
    echo "  Stage 4: Training (→ @learning-path)"
    echo "    Input: Stages 1-3 output"
    echo "    Output: Training plan → Stage 5"
    echo ""
    
    # Stage 5
    STAGE5_ID=$(./kb-cli add-entity \
      "Stage 5: Final Validation" \
      "Review all outputs and provide go/no-go recommendation" \
      '{"type":"pipeline_stage","stage_num":5,"parent_pipeline":"'$PIPELINE_ID'","agent":"code-analyzer","status":"waiting","input_entity":"'$STAGE4_ID'"}' \
      | jq -r '.id')
    ./kb-cli add-link $PIPELINE_ID $STAGE5_ID "stage" > /dev/null
    ./kb-cli add-link $STAGE4_ID $STAGE5_ID "feeds" > /dev/null
    echo "  Stage 5: Validation (→ @code-analyzer)"
    echo "    Input: All previous stages"
    echo "    Output: Final recommendation"
    echo ""
    
    echo "Pipeline structure created!"
    echo ""
    echo "Execution flow:"
    echo "  Stage 1 executes → produces output"
    echo "  Stage 2 receives Stage 1 output → executes → produces output"
    echo "  Stage 3 receives Stages 1-2 output → executes → produces output"
    echo "  ... and so on ..."
    echo ""
    echo "Each stage validates previous output before proceeding."
    echo "View pipeline: ./kb-cli get-entity $PIPELINE_ID"
    ;;
    
  *)
    echo "Invalid choice. Please run again and enter 1, 2, or 3."
    exit 1
    ;;
esac

echo ""
echo "==================================="
echo "Demo complete!"
echo ""
echo "Explore the knowledge base:"
echo "  ./kb-cli stats"
echo "  ./kb-cli list-entities"
echo "  ./kb-cli visualize"
echo "==================================="
