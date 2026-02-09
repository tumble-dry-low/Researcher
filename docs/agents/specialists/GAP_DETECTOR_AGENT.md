# Gap Detector Agent

A meta-cognitive agent that identifies missing research angles, unanswered questions, unverified assumptions, and coverage blind spots.

## Purpose

Goes beyond our keyword-based gap detection to perform **semantic gap analysis**. Identifies what the research *should* cover but doesn't, what questions are implied but not answered, and what assumptions are made but not verified.

## When to Use

- After initial research waves to plan Wave 2 targets
- Before declaring convergence — ensures nothing important is missed
- When Thompson sampling needs better gap targets
- When research feels complete but confidence is still low

## Gap Types Detected

| Gap Type | What It Finds | Severity |
|----------|--------------|----------|
| `uncovered_topics` | Terms in entity content not covered by claims | Medium |
| `implicit_question` | Questions embedded in claim text (how, why, whether) | Low |
| `unverified_assumption` | Claims using "assuming", "typically", "generally" | Medium |
| `missing_perspectives` | Standard perspectives not represented in claims | Medium |
| `empty_subtopics` | Sub-entities with zero claims | High |
| `thin_coverage` | Sub-entities with < 3 claims | Medium |

## CLI Usage

```bash
# Detect gaps for a single entity (included in full review)
./kb-cli review <entity_id>
```

## Example Output

```json
{
  "entity_id": "abc123",
  "total_gaps": 4,
  "high_severity": 1,
  "gaps": [
    {
      "type": "empty_subtopics",
      "severity": "high",
      "subtopics": ["Energy-Selective Neutron Filtering"],
      "detail": "1 sub-entities have no claims"
    },
    {
      "type": "missing_perspectives",
      "severity": "medium",
      "perspectives": ["ethical", "economic"],
      "detail": "2 perspectives not covered: ethical, economic"
    }
  ],
  "suggested_actions": [
    "Investigate: 1 sub-entities have no claims",
    "Investigate: 2 perspectives not covered: ethical, economic"
  ]
}
```

## Integration with Thompson Sampling

Gap Detector output feeds directly into Thompson sampling for prioritized investigation:

```
1. ./kb-cli review <entity_id>
   → Identifies gaps with severity rankings

2. Register gaps as topics for Thompson sampling:
   ./kb-cli gaps register <eval_id> '{"gap1": "topic1", "gap2": "topic2"}'

3. Thompson sampling selects highest-priority gaps:
   ./kb-cli gaps select <eval_id> 3

4. Spawn targeted agents to fill selected gaps:
   ./kb-cli spawn <parent_id> "Fill gap: <topic>" "..."
```

## Integration with Evaluation Loop

```
Wave 1: Research agents collect claims
  ↓
Evaluation: Check convergence
  ↓
Gap Detection: ./kb-cli review <root_entity_id>
  ↓
If high-severity gaps:
  → Spawn targeted Wave 2 agents to fill gaps
  → Feed gaps into Thompson sampling
If no significant gaps:
  → Proceed to Critic → Synthesis
```

## Combining with Perspective Discovery

The Gap Detector uses `discover_perspectives()` to check for missing standard perspectives. The standard perspectives checked include:
- Technical, Economic, Social, Environmental, Legal/Regulatory
- Historical, Comparative, Ethical, Risk/Safety
- Implementation, Scalability, User/Stakeholder

## Suggested Actions

The output includes `suggested_actions` — a prioritized list of investigation targets derived from high and medium severity gaps. These can be used directly as spawn prompts for targeted research agents.
