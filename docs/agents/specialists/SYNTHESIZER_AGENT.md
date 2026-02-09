# Synthesizer Agent

A STORM-style 3-phase synthesis agent that transforms raw research claims into structured, audience-adapted output.

## Purpose

Separates **research** from **writing**. Research agents collect claims and evidence; the Synthesizer produces polished output. Based on Stanford's STORM architecture (Outliner → Writer → Editor).

## When to Use

- After research converges and critique passes
- When producing reports for different audiences
- When raw `generate_report()` output needs more structure
- When claims need to be organized into thematic sections

## Three Phases

### Phase 1: Outliner
Groups claims into themes automatically:
- Performance, Cost, Feasibility, Comparison, Mechanism, Limitation, Evidence
- Sorts by confidence within each theme
- Identifies which themes have strong vs weak evidence

### Phase 2: Writer
Structures each theme into a section with:
- Claims ordered by confidence (strongest first)
- Inline citation references `[1]`, `[2]`
- Source reference map for bibliography

### Phase 3: Editor
Adapts output for target audience:

| Audience | Detail | Jargon | Citations |
|----------|--------|--------|-----------|
| `technical` | Full | Yes | Yes |
| `executive` | Summary only | No | No |
| `general` | Moderate | No | Yes |

## CLI Usage

```bash
# Technical synthesis (default)
./kb-cli report <entity_id> synthesize

# Executive summary
./kb-cli report <entity_id> synthesize executive

# General audience
./kb-cli report <entity_id> synthesize general
```

## Integration with Research Pipeline

```
Research Swarm → Evaluation Loop → Critic Review → Synthesizer
                                                      ↓
                                              Structured Output
                                              ├── Themes with claims
                                              ├── Citation references
                                              └── Audience-adapted text
```

### In a Pipeline Manager Flow

```bash
# Stage 1: Research
./kb-cli spawn $root "Research: Topic X" "..." swarm_coordinator

# Stage 2: Quality Assurance (full review includes critique, quantities, gaps)
./kb-cli review $entity_id

# Stage 3: Synthesis
./kb-cli report $entity_id synthesize
./kb-cli report $entity_id synthesize executive
```

## Output Structure

```json
{
  "entity_id": "abc123",
  "title": "Research Topic",
  "audience": "technical",
  "sections": [
    {
      "theme": "Performance",
      "claim_count": 5,
      "avg_confidence": 0.82,
      "claims": [
        {
          "text": "Method X achieves 35% improvement over baseline",
          "grade": "strong",
          "confidence": 0.92,
          "refs": "[1], [3]"
        }
      ]
    }
  ],
  "child_sections": [...],
  "total_references": 12,
  "references": {"1": {"title": "...", "url": "..."}}
}
```

## Theme Detection

Claims are auto-categorized by keyword matching:

| Theme | Keywords |
|-------|----------|
| Performance | speed, latency, throughput, efficiency |
| Cost | price, expensive, budget, economic |
| Feasibility | practical, possible, TRL, readiness |
| Comparison | versus, better, alternative, traditional |
| Mechanism | process, method, technique, approach |
| Limitation | challenge, problem, barrier, cannot |
| Evidence | study, experiment, demonstrated, showed |
