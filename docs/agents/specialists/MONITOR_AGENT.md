# Monitor Agent

A meta-cognitive oversight agent that tracks research tree health, detects anomalies, and prevents runaway agent proliferation.

## Purpose

With recursive spawning (max_depth=4, max_total=50), research trees can grow large. The Monitor Agent provides real-time visibility into tree structure, progress, and health — detecting stuck agents, imbalanced branches, and confidence stalls before they waste resources.

## When to Use

- During long-running research with multiple waves
- When recursive spawning creates deep trees
- When confidence isn't improving despite more agents
- To get a dashboard view of any research investigation

## Anomaly Detection

| Alert | Severity | What It Means |
|-------|----------|---------------|
| `empty_nodes` | Warning | Spawned entities with no content or claims |
| `deep_tree` | Info | Tree deeper than 3 levels — consider consolidation |
| `imbalanced_tree` | Info | One branch much larger than others |
| `confidence_stalled` | Warning | Confidence hasn't improved for 3+ iterations |

## CLI Usage

```bash
# Monitor a research tree
./kb-cli monitor <root_entity_id>
```

## Example Output

```json
{
  "root_entity_id": "abc123",
  "root_title": "Research: Tokamak Shielding",
  "tree_size": 12,
  "max_depth": 2,
  "total_claims": 107,
  "nodes_with_content": 9,
  "nodes_without_content": 3,
  "evaluation": {
    "confidence": 0.95,
    "iteration": 2,
    "status": "converged",
    "trajectory": [
      {"iteration": 1, "confidence": 0.70, "delta": 0.70},
      {"iteration": 2, "confidence": 0.95, "delta": 0.25}
    ],
    "stalled": false
  },
  "alerts": [
    {
      "type": "empty_nodes",
      "severity": "warning",
      "count": 3,
      "nodes": ["Sub-topic A", "Sub-topic B", "Sub-topic C"]
    }
  ],
  "alert_count": 1
}
```

## Integration with Evaluation Loop

The Monitor Agent complements the evaluation loop:

```
Evaluation: Is research quality sufficient? (confidence, gaps, contradictions)
Monitor: Is research process healthy? (tree structure, progress, anomalies)
```

### Automated Response to Alerts

```
empty_nodes (warning):
  → Check if agents failed or are still running
  → Re-spawn agents for empty nodes if needed

deep_tree (info):
  → Consider consolidating deep branches
  → Check spawn budget: ./kb-cli budget <entity_id>

imbalanced_tree (info):
  → Investigate why one branch grew disproportionately
  → May indicate scope creep in one research angle

confidence_stalled (warning):
  → Research may have hit diminishing returns
  → Consider declaring convergence or changing strategy
  → Check marginal-gain threshold settings
```

## Dashboard View

The Monitor provides the data needed for a research dashboard:

```
Research: Tokamak Shielding
├── Tree: 12 nodes, depth 2, 107 claims
├── Progress: 9/12 nodes complete (75%)
├── Confidence: 0.95 (converged ✓)
├── Alerts: 1 warning (3 empty nodes)
└── Status: Ready for synthesis
```

## Combining with Other Agents

The Monitor sits outside the research flow as an observer:

```
                    ┌─────────┐
                    │ Monitor │ ← observes everything
                    └────┬────┘
                         │
    ┌─────────┬──────────┼──────────┬──────────┐
    │Research │ Critic   │ Gap Det  │ Synth    │
    │ Agents  │ Agent    │  Agent   │ Agent    │
    └─────────┴──────────┴──────────┴──────────┘
```

The Monitor doesn't modify research — it reports on health so the coordinator (human or agent) can make informed decisions.
