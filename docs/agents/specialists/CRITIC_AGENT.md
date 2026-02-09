# Critic Agent

An adversarial review agent that challenges research claims, finds logical gaps, and detects bias before conclusions are finalized.

## Purpose

The Critic Agent provides **semantic review** — it reasons about whether conclusions follow from evidence, unlike structural reflection which only checks source counts and grades. It acts as a Devil's Advocate, actively searching for counter-evidence and identifying unsupported logical leaps.

## When to Use

- After a research wave completes and claims are collected
- Before finalizing synthesis or generating reports
- When confidence is high but counter-evidence hasn't been sought
- When claims contain quantitative assertions with few sources

## Capabilities

| Check | What It Detects | Severity |
|-------|----------------|----------|
| Circular reasoning | Claim A sources overlap with claim B text | High |
| Unsupported quantitative | Numbers with < 2 sources | Medium |
| Unexplored concepts | Terms mentioned only once | Low |
| Missing counter-evidence | All claims agree, no contested views | Medium |
| Source bias | All sources from ≤ 2 domains | Medium |
| Overconfidence | High confidence with few sources | Medium |

## CLI Usage

```bash
# Review a single entity (includes critique)
./kb-cli review <entity_id>

# Review an entire research tree
./kb-cli review <root_entity_id>  # use on root to review full tree
```

## Integration with Swarm Coordinator

After Wave N evaluation converges, run the Critic before synthesis:

```
Wave 1: Research agents collect claims
  ↓
Evaluation: Check convergence (confidence ≥ 0.80)
  ↓
Critic: ./kb-cli review <root_entity_id>  # review full tree
  ↓
If significant_concerns → spawn targeted agents to address issues
If passes_critique → proceed to synthesis
```

### Swarm Agent Prompt Integration

Add this to swarm agent instructions:

```
After collecting all claims, run the critic:
  ./kb-cli review <your_entity_id>

If the critique finds issues:
- 'potential_circular': Re-examine the circular claims. Find independent sources.
- 'unsupported_quantitative': Find additional sources for numerical claims.
- 'no_counter_evidence': Actively search for counter-arguments or limitations.
- 'source_bias': Search for sources from different domains/perspectives.
- 'overconfident': Downgrade confidence or find more supporting evidence.
```

## Verdicts

| Verdict | Meaning |
|---------|---------|
| `passes_critique` | No significant issues found |
| `minor_concerns` | 1+ medium issues, no high |
| `needs_attention` | 1 high or 3+ medium issues |
| `significant_concerns` | 2+ high severity issues |

## Example Output

```json
{
  "entity_id": "abc123",
  "total_claims": 12,
  "issues": [
    {
      "type": "no_counter_evidence",
      "severity": "medium",
      "detail": "All 12 claims agree — no counter-evidence sought"
    },
    {
      "type": "unsupported_quantitative",
      "severity": "medium",
      "claim_id": 45,
      "detail": "Quantitative claim with only 1 source(s): 35-60% thickness reduction..."
    }
  ],
  "verdict": "needs_attention"
}
```

## Combining with Other Agents

The Critic Agent works best in sequence with:
1. **Gap Detector** → finds what's missing
2. **Critic** → challenges what's there
3. **Quantitative Agent** → verifies the numbers
4. **Synthesizer** → produces the final output

This forms a natural Pipeline Manager flow for post-research quality assurance.
