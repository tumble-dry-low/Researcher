# Quantitative Agent

A numerical verification agent that checks quantities, units, statistical claims, and cross-references numerical values across claims.

## Purpose

LLMs score only 0.57-0.58 F1 on numerical claim verification. The Quantitative Agent applies structured checks that catch errors LLMs miss: unit impossibilities, magnitude implausibility, missing uncertainty bounds, and contradicting numbers.

## When to Use

- After research collects claims with numerical values
- Before synthesis when quantitative accuracy matters
- For domains with precise measurements (physics, engineering, economics)
- When claims cite specific percentages, temperatures, energies, or multipliers

## Checks Performed

| Check | What It Catches | Example |
|-------|----------------|---------|
| Impossible values | Negative Kelvin, negative energy | `-50K` |
| Implausible values | Extreme temperatures, huge multipliers | `50000°C`, `10000x` |
| Suspicious percentages | >100% where inappropriate | `250% efficiency` |
| Missing uncertainty | Numbers without error bars or ranges | `exactly 3.65 MA/cm²` |
| Numerical disagreement | Same quantity, conflicting values | `35%` vs `60%` for same metric |

### Supported Units

Temperature (°C, °F, K), Pressure (GPa, MPa, Pa), Energy (eV, MeV, keV, GeV),
Length (nm, μm, mm, cm, m, km, fm, pm), Mass (kg, g, mg, μg),
Power (W, kW, MW, GW, TW), Radiation (dpa), Multipliers (x, ×, fold, times),
Percentages (%), and more.

## CLI Usage

```bash
# Check all numerical claims for an entity (included in full review)
./kb-cli review <entity_id>
```

## Example Output

```json
{
  "entity_id": "abc123",
  "claims_checked": 8,
  "total_claims": 15,
  "issues": [
    {
      "type": "missing_uncertainty",
      "severity": "low",
      "claim_id": 45,
      "detail": "Numerical claim without uncertainty bounds: nano-B4C achieves 50% shielding im..."
    },
    {
      "type": "numerical_disagreement",
      "severity": "medium",
      "claim_ids": [42, 48],
      "detail": "35% vs 60% (1.7x difference)"
    }
  ],
  "issue_count": 2,
  "high_severity": 0
}
```

## Integration with Quality Pipeline

The Quantitative Agent fits naturally after the Critic and before Synthesis:

```
Research → Critic (semantic review) → Quantitative (numerical review) → Synthesis
```

### Automated Remediation

When numerical issues are found:
- `impossible_value` → Flag claim as contested, investigate
- `implausible_value` → Verify against additional sources
- `missing_uncertainty` → Note in metadata, add caveat to synthesis
- `numerical_disagreement` → Investigate both claims, determine which is correct

## Combining with Domain Experts

For domain-specific numerical validation, pair with a Domain Expert:

```bash
# First: general quantitative check (included in full review)
./kb-cli review <entity_id>

# Then: domain-specific review (e.g., physics expert checks units)
./kb-cli expert review <entity_id> physics
```
