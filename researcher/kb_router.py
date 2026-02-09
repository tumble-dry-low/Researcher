"""Task routing functions extracted from KnowledgeBase. Zero DB dependency — pure functions."""

import re


COORDINATOR_PROFILES = {
    'hierarchical_planner': {
        'dependency_density': 0.8,
        'parallelizability': 0.3,
        'uncertainty': 0.4,
        'decomposability': 1.0,
        'scope': 0.9,
    },
    'swarm_coordinator': {
        'dependency_density': 0.1,
        'parallelizability': 1.0,
        'uncertainty': 1.0,
        'decomposability': 0.3,
        'scope': 0.7,
    },
    'pipeline_manager': {
        'dependency_density': 1.0,
        'parallelizability': 0.1,
        'uncertainty': 0.2,
        'decomposability': 0.5,
        'scope': 0.6,
    },
}


def extract_task_features(kb, description, metadata=None):
    """Extract 5 task feature dimensions from a description for coordinator routing."""
    text = description.lower()
    meta = metadata or {}

    dep_signals = len(re.findall(r'\b(after|then|once|depends on|requires|before|following|prerequisite)\b', text))
    dependency_density = min(1.0, dep_signals * 0.2)

    par_signals = len(re.findall(r'\b(all|simultaneously|each|independently|parallel|every|multiple|diverse)\b', text))
    parallelizability = min(1.0, par_signals * 0.15)

    unc_signals = len(re.findall(r'\b(should we|explore|investigate|what if|compare|options|might|could|uncertain|unknown|possible)\b', text))
    unc_signals += text.count('?') * 2
    uncertainty = min(1.0, unc_signals * 0.15)

    words = len(text.split())
    sub_signals = len(re.findall(r'\b(phase|stage|step|part|component|module|section|layer|aspect)\b', text))
    decomposability = min(1.0, (words / 200) * 0.3 + sub_signals * 0.15)

    domain_words = set(re.findall(r'\b(research|analysis|decision|learning|code|security|cost|design|test|deploy|data|infra)\b', text))
    scope = min(1.0, len(domain_words) * 0.15)

    features = {
        'dependency_density': meta.get('dependency_density', dependency_density),
        'parallelizability': meta.get('parallelizability', parallelizability),
        'uncertainty': meta.get('uncertainty', uncertainty),
        'decomposability': meta.get('decomposability', decomposability),
        'scope': meta.get('scope', scope),
    }
    return {k: round(v, 3) for k, v in features.items()}


def route_task(kb, description, metadata=None):
    """Route a task to the best coordinator based on extracted features."""
    features = extract_task_features(kb, description, metadata)

    scores = {}
    for coord, profile in COORDINATOR_PROFILES.items():
        score = sum(features[dim] * profile[dim] for dim in features)
        scores[coord] = round(score, 4)

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    best = ranked[0][0]
    best_score = ranked[0][1]
    second_score = ranked[1][1] if len(ranked) > 1 else 0

    margin = best_score - second_score
    confidence = min(1.0, 0.5 + margin * 2)

    config = _suggest_config(best, features)

    return {
        'recommended': best,
        'confidence': round(confidence, 3),
        'scores': dict(ranked),
        'features': features,
        'config': config,
        'reasoning': _routing_reasoning(best, features, ranked)
    }


def _suggest_config(coordinator, features):
    """Suggest coordinator-specific configuration based on task features."""
    if coordinator == 'swarm_coordinator':
        size = max(4, min(15, int(6 + features['uncertainty'] * 5 + features['scope'] * 4)))
        return {
            'swarm_size': size,
            'consensus_threshold': 0.6 if features['uncertainty'] > 0.5 else 0.7,
            'max_waves': 3 if features['uncertainty'] > 0.7 else 2,
        }
    elif coordinator == 'hierarchical_planner':
        depth = max(2, min(6, int(2 + features['decomposability'] * 3 + features['scope'] * 2)))
        return {
            'max_depth': depth,
            'parallel_within_levels': features['parallelizability'] > 0.3,
        }
    elif coordinator == 'pipeline_manager':
        stages = max(2, min(7, int(2 + features['dependency_density'] * 3 + features['decomposability'] * 2)))
        return {
            'stages': stages,
            'allow_stage_retry': features['uncertainty'] > 0.3,
        }
    return {}


def _routing_reasoning(best, features, ranked):
    """Generate brief reasoning for routing decision."""
    top_features = sorted(features.items(), key=lambda x: x[1], reverse=True)[:2]
    drivers = ' and '.join(f"{k.replace('_', ' ')} ({v:.2f})" for k, v in top_features)
    return f"Selected {best.replace('_', ' ')} driven by {drivers}. Margin: {ranked[0][1] - ranked[1][1]:.3f}"
