# Domain Expert Agent

A pluggable domain specialization template that creates expert-persona agents via system prompts + RAG, without fine-tuning.

## Purpose

When researching fusion shielding, a "nuclear physics expert" prompt produces better claims than a generic researcher. The Domain Expert Agent is not a single agent but a **template system** for creating domain-specialized agents on demand. Based on CrewAI's role-goal-backstory pattern (80% task, 20% persona).

## Built-in Domain Profiles

| Domain | Role | Verification Focus |
|--------|------|-------------------|
| `physics` | PhD-level physicist | Unit consistency, conservation laws, order of magnitude |
| `materials_science` | Materials scientist | Property ranges, fabrication feasibility, TRL accuracy |
| `engineering` | Systems engineer | Practical constraints, scalability, cost estimates |
| `economics` | Technology economist | Cost accuracy, market size, policy feasibility |
| `computer_science` | CS/AI researcher | Algorithmic correctness, complexity claims, benchmarks |

## CLI Usage

```bash
# List available domain profiles
./kb-cli expert list

# Match a topic to relevant experts
./kb-cli expert match "neutron shielding materials for tokamak fusion reactors"

# Apply domain-specific review to an entity
./kb-cli expert review <entity_id> physics

# Apply multiple domain reviews
./kb-cli expert review <entity_id> materials_science
./kb-cli expert review <entity_id> engineering
```

## Adding Custom Profiles

In Python:

```python
from kb import KnowledgeBase
kb = KnowledgeBase()

kb.add_domain_profile('nuclear_engineering', {
    'role': 'Domain Expert: Nuclear Engineering',
    'goal': 'Evaluate nuclear reactor design, neutronics, and radiation transport',
    'backstory': 'Nuclear engineer with 20 years experience in reactor design and shielding',
    'knowledge_keywords': ['neutron', 'reactor', 'shielding', 'fission', 'fusion', 'breeding', 'criticality'],
    'verification_focus': ['neutronics_accuracy', 'dose_calculations', 'material_activation']
})
```

## Domain Review Output

```json
{
  "entity_id": "abc123",
  "domain": "physics",
  "expert_role": "Domain Expert: Physics",
  "relevant_claims": 8,
  "irrelevant_claims": 4,
  "verification_focus": ["unit_consistency", "conservation_laws", "order_of_magnitude"],
  "claims": [
    {
      "claim_id": 42,
      "claim_text": "De Broglie wavelength of 14.1 MeV neutron is ~7.6 fm",
      "relevance_score": 3,
      "grade": "strong",
      "confidence": 0.92
    }
  ],
  "prompt_context": "You are a Domain Expert: Physics. PhD-level physicist specializing in condensed matter and nuclear physics. Your goal: Provide rigorous physics analysis with mathematical backing. Focus verification on: unit_consistency, conservation_laws, order_of_magnitude."
}
```

## Integration with Research Pipeline

### Auto-matching During Research

When routing a task, auto-detect relevant domain experts:

```bash
# 1. Route the task
./kb-cli route "Research neutron shielding for compact tokamaks"

# 2. Match domain experts
./kb-cli expert match "neutron shielding for compact tokamaks"
# → Returns: physics (score 3), materials_science (score 2), engineering (score 1)

# 3. Include domain expert context in agent prompts
./kb-cli expert review <entity_id> physics
# → Returns prompt_context to inject into agent system prompt
```

### In Swarm Coordinator

Assign domain expert personas to specific swarm agents:

```
Swarm for "Tokamak Shielding":
  Agent 1: Generic researcher → Neutron optics fundamentals
  Agent 2: Physics expert → Wave-particle duality at MeV energies
  Agent 3: Materials science expert → Nanostructured absorbers
  Agent 4: Engineering expert → Fabrication feasibility
  Agent 5: Economics expert → Cost comparison with conventional shielding
```

## prompt_context Field

The `domain_review()` method returns a `prompt_context` string that can be injected directly into any agent's system prompt to give it domain expertise. This is the key mechanism — no fine-tuning needed, just prompt engineering with structured context.
