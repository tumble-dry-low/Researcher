"""Domain expert profile functions extracted from KnowledgeBase."""


DOMAIN_PROFILES = {
    'physics': {
        'role': 'Domain Expert: Physics',
        'goal': 'Provide rigorous physics analysis with mathematical backing',
        'backstory': 'PhD-level physicist specializing in condensed matter and nuclear physics',
        'knowledge_keywords': ['energy', 'force', 'quantum', 'nuclear', 'thermal', 'radiation', 'particle'],
        'verification_focus': ['unit_consistency', 'conservation_laws', 'order_of_magnitude'],
    },
    'materials_science': {
        'role': 'Domain Expert: Materials Science',
        'goal': 'Evaluate materials properties, fabrication feasibility, and TRL assessments',
        'backstory': 'Materials scientist with expertise in advanced ceramics, metals, and composites',
        'knowledge_keywords': ['material', 'alloy', 'ceramic', 'composite', 'strength', 'hardness', 'fabrication'],
        'verification_focus': ['property_ranges', 'fabrication_feasibility', 'trl_accuracy'],
    },
    'engineering': {
        'role': 'Domain Expert: Engineering',
        'goal': 'Assess practical implementation, scalability, and system integration',
        'backstory': 'Systems engineer with experience in complex engineering projects',
        'knowledge_keywords': ['design', 'system', 'integration', 'scale', 'manufacturing', 'reliability'],
        'verification_focus': ['practical_constraints', 'scalability', 'cost_estimates'],
    },
    'economics': {
        'role': 'Domain Expert: Economics & Policy',
        'goal': 'Analyze cost-benefit, market dynamics, and policy implications',
        'backstory': 'Economist specializing in technology policy and industrial economics',
        'knowledge_keywords': ['cost', 'market', 'policy', 'investment', 'economic', 'regulatory', 'price'],
        'verification_focus': ['cost_accuracy', 'market_size', 'policy_feasibility'],
    },
    'computer_science': {
        'role': 'Domain Expert: Computer Science',
        'goal': 'Evaluate algorithms, architectures, and computational approaches',
        'backstory': 'CS researcher specializing in AI/ML systems, distributed computing, and software architecture',
        'knowledge_keywords': ['algorithm', 'model', 'architecture', 'performance', 'complexity', 'optimization', 'data'],
        'verification_focus': ['algorithmic_correctness', 'complexity_claims', 'benchmark_validity'],
    },
}


def get_domain_profile(kb, domain):
    """Get a domain expert profile by name."""
    return DOMAIN_PROFILES.get(domain)


def match_domain_expert(kb, text):
    """Match text to relevant domain expert profiles, ranked by relevance."""
    text_lower = text.lower()
    scored = []
    for domain, profile in DOMAIN_PROFILES.items():
        score = sum(1 for kw in profile['knowledge_keywords'] if kw in text_lower)
        if score > 0:
            scored.append({
                'domain': domain,
                'score': score,
                'role': profile['role'],
                'goal': profile['goal'],
                'verification_focus': profile['verification_focus']
            })
    scored.sort(key=lambda x: x['score'], reverse=True)
    return scored


def domain_review(kb, entity_id, domain):
    """Apply domain-specific review to an entity's claims."""
    profile = get_domain_profile(kb, domain)
    if not profile:
        return {"error": f"unknown domain: {domain}"}

    claims = kb.list_claims(entity_id=entity_id)
    relevant = []
    irrelevant = []

    for c in claims:
        text_lower = c['claim_text'].lower()
        match_score = sum(1 for kw in profile['knowledge_keywords'] if kw in text_lower)
        if match_score > 0:
            relevant.append({
                'claim_id': c['id'],
                'claim_text': c['claim_text'][:120],
                'relevance_score': match_score,
                'grade': c['evidence_grade'],
                'confidence': c.get('confidence', 0)
            })
        else:
            irrelevant.append(c['id'])

    relevant.sort(key=lambda x: x['relevance_score'], reverse=True)

    return {
        'entity_id': entity_id,
        'domain': domain,
        'expert_role': profile['role'],
        'relevant_claims': len(relevant),
        'irrelevant_claims': len(irrelevant),
        'verification_focus': profile['verification_focus'],
        'claims': relevant,
        'prompt_context': (
            f"You are a {profile['role']}. {profile['backstory']}. "
            f"Your goal: {profile['goal']}. "
            f"Focus verification on: {', '.join(profile['verification_focus'])}."
        )
    }
