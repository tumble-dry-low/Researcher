"""Decision framework (MCDA) functions extracted from KnowledgeBase."""

import json
from datetime import datetime


def add_decision(kb, title, criteria, alternatives, entity_id=None, weights=None):
    """Create a structured decision with criteria and alternatives. Returns decision ID."""
    now = kb._now()

    if not weights:
        w = 1.0 / len(criteria)
        weights = {c['name']: round(w, 4) for c in criteria}

    cursor = kb.conn.execute(
        "INSERT INTO decisions (entity_id, title, criteria, alternatives, weights, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (entity_id, title, json.dumps(criteria), json.dumps(alternatives),
         json.dumps(weights), now, now)
    )
    kb.conn.commit()
    return cursor.lastrowid


def score_alternatives(kb, decision_id, scores):
    """Score alternatives against criteria. Auto-computes weighted recommendation."""
    row = kb.conn.execute("SELECT * FROM decisions WHERE id = ?", (decision_id,)).fetchone()
    if not row:
        return {"error": "decision not found"}

    weights = json.loads(row['weights'])
    criteria = json.loads(row['criteria'])

    results = {}
    for alt, alt_scores in scores.items():
        weighted = 0.0
        for c in criteria:
            cname = c['name']
            if cname in alt_scores and cname in weights:
                weighted += alt_scores[cname] * weights[cname]
        results[alt] = round(weighted, 4)

    if results:
        recommendation = max(results, key=results.get)
        sorted_alts = sorted(results.items(), key=lambda x: x[1], reverse=True)
        margin = sorted_alts[0][1] - sorted_alts[1][1] if len(sorted_alts) > 1 else 1.0

        if margin < 0.05:
            rationale = f"Very close: {sorted_alts[0][0]} ({sorted_alts[0][1]:.3f}) vs {sorted_alts[1][0]} ({sorted_alts[1][1]:.3f}). Consider sensitivity analysis."
        else:
            rationale = f"Clear winner: {recommendation} ({results[recommendation]:.3f}), margin {margin:.3f} over next best."
    else:
        recommendation = None
        rationale = "No alternatives scored."

    now = kb._now()
    kb.conn.execute(
        "UPDATE decisions SET scores = ?, recommendation = ?, rationale = ?, status = 'scored', updated_at = ? WHERE id = ?",
        (json.dumps(scores), recommendation, rationale, now, decision_id)
    )
    kb.conn.commit()

    return {
        'decision_id': decision_id,
        'weighted_scores': results,
        'ranking': [{'alternative': a, 'score': s} for a, s in sorted(results.items(), key=lambda x: x[1], reverse=True)],
        'recommendation': recommendation,
        'rationale': rationale
    }


def sensitivity_analysis(kb, decision_id, perturbation=0.1):
    """Check how sensitive the recommendation is to weight changes."""
    row = kb.conn.execute("SELECT * FROM decisions WHERE id = ?", (decision_id,)).fetchone()
    if not row:
        return {"error": "decision not found"}

    weights = json.loads(row['weights'])
    scores = json.loads(row['scores'])
    criteria = json.loads(row['criteria'])
    original_rec = row['recommendation']

    if not scores:
        return {"error": "decision not yet scored"}

    flips = []
    for c in criteria:
        cname = c['name']
        for direction in [-perturbation, perturbation]:
            test_weights = dict(weights)
            test_weights[cname] = max(0, min(1, test_weights[cname] + direction))
            total = sum(test_weights.values())
            if total > 0:
                test_weights = {k: v / total for k, v in test_weights.items()}

            results = {}
            for alt, alt_scores in scores.items():
                weighted = sum(alt_scores.get(cn, 0) * test_weights.get(cn, 0) for cn in [cr['name'] for cr in criteria])
                results[alt] = round(weighted, 4)

            new_rec = max(results, key=results.get) if results else None
            if new_rec != original_rec:
                flips.append({
                    'criterion': cname,
                    'weight_change': round(direction, 3),
                    'original': original_rec,
                    'flipped_to': new_rec,
                    'new_scores': results
                })

    return {
        'decision_id': decision_id,
        'original_recommendation': original_rec,
        'perturbation': perturbation,
        'is_robust': len(flips) == 0,
        'flips': flips,
        'vulnerability': f"{len(flips)} flips out of {len(criteria) * 2} perturbations"
    }


def get_decision(kb, decision_id):
    """Get a decision by ID."""
    row = kb.conn.execute("SELECT * FROM decisions WHERE id = ?", (decision_id,)).fetchone()
    if not row:
        return None
    d = {k: row[k] for k in row.keys()}
    for field in ('criteria', 'alternatives', 'scores', 'weights'):
        d[field] = json.loads(d[field])
    return d
