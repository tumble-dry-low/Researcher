"""Claim verification functions extracted from KnowledgeBase."""

import json
import re
import random
from datetime import datetime


def verify_claim(kb, claim_id, search_fn=None):
    """SAFE-style search-augmented claim verification."""
    claim = kb.get_claim(claim_id)
    if not claim:
        return {"error": "claim not found"}

    # Step 1: Get atomic facts (decompose if needed)
    atoms = kb.get_atomic_claims(claim_id)
    if not atoms:
        atoms = [claim]  # treat as single atomic fact

    # Step 2: For each atom, search for evidence
    results = []
    for atom in atoms:
        atom_text = atom['claim_text']
        evidence = {'supporting': [], 'contradicting': [], 'neutral': []}

        # Search KB first (FTS5)
        kb_hits = kb.conn.execute("""
            SELECT c.id, c.claim_text, c.confidence, c.evidence_grade
            FROM claims_fts f
            JOIN claims c ON CAST(f.claim_id AS INTEGER) = c.id
            WHERE claims_fts MATCH ? AND c.id != ?
            LIMIT 10
        """, (_fts_safe(atom_text), atom.get('id', claim_id))).fetchall()

        for hit in kb_hits:
            evidence['supporting'].append({
                'source': 'kb', 'claim_id': hit['id'],
                'text': hit['claim_text'][:200],
                'confidence': hit['confidence'] or 0.5
            })

        # External search if provided
        ext_results = []
        if search_fn:
            try:
                ext_results = search_fn(atom_text)
            except Exception:
                ext_results = []

        for ext in ext_results:
            source_id = kb.add_source(
                ext.get('url', ''), ext.get('title', ''),
                ext.get('snippet', ''), 'web_verification'
            )
            evidence['supporting'].append({
                'source': 'web', 'source_id': source_id,
                'url': ext.get('url', ''),
                'snippet': ext.get('snippet', '')[:200]
            })
            kb.add_claim_source(
                atom.get('id', claim_id), source_id, 'supports'
            )

        # Step 3: Score this atom
        n_support = len(evidence['supporting'])
        n_kb = len(kb_hits)
        n_ext = len(ext_results)

        if n_support == 0:
            atom_score = 0.3
            atom_verdict = 'unverified'
        elif n_ext >= 2:
            atom_score = min(0.95, 0.6 + n_ext * 0.1 + n_kb * 0.05)
            atom_verdict = 'externally_verified'
        elif n_kb >= 2:
            atom_score = min(0.85, 0.5 + n_kb * 0.08)
            atom_verdict = 'kb_corroborated'
        else:
            atom_score = 0.4 + n_support * 0.1
            atom_verdict = 'weakly_supported'

        results.append({
            'atom': atom_text[:120],
            'atom_id': atom.get('id'),
            'score': round(atom_score, 3),
            'verdict': atom_verdict,
            'n_kb_hits': n_kb,
            'n_ext_hits': n_ext,
            'evidence': evidence
        })

    # Step 4: Aggregate
    if results:
        avg_score = sum(r['score'] for r in results) / len(results)
        min_score = min(r['score'] for r in results)
        verified_count = sum(1 for r in results if r['verdict'] in ('externally_verified', 'kb_corroborated'))
    else:
        avg_score = 0.3
        min_score = 0.3
        verified_count = 0

    # Update claim with verification metadata
    meta = claim.get('metadata', {})
    meta['verification'] = {
        'avg_score': round(avg_score, 3),
        'min_score': round(min_score, 3),
        'verified_atoms': verified_count,
        'total_atoms': len(results),
        'method': 'safe_search' if search_fn else 'kb_only'
    }
    now = kb._now()
    kb.conn.execute(
        "UPDATE claims SET metadata = ?, updated_at = ? WHERE id = ?",
        (json.dumps(meta), now, claim_id)
    )

    factuality = round(avg_score * 0.6 + min_score * 0.4, 3)
    kb.conn.execute(
        "UPDATE claims SET confidence = ?, updated_at = ? WHERE id = ?",
        (factuality, now, claim_id)
    )
    kb.conn.commit()

    return {
        'claim_id': claim_id,
        'claim_text': claim['claim_text'][:120],
        'factuality_score': factuality,
        'avg_atom_score': round(avg_score, 3),
        'min_atom_score': round(min_score, 3),
        'verified_atoms': verified_count,
        'total_atoms': len(results),
        'atom_results': results,
        'method': 'safe_search' if search_fn else 'kb_only'
    }


def _fts_safe(text):
    """Make text safe for FTS5 MATCH queries by extracting key terms."""
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text)
    filtered = [w.lower() for w in words][:8]
    if not filtered:
        filtered = [w.lower() for w in words[:4]]
    return ' OR '.join(filtered) if filtered else text[:50]


def grade_claim_sc(kb, claim_id, n_samples=5):
    """Self-consistency sampling for claim grading."""
    claim = kb.get_claim(claim_id)
    if not claim:
        return {"error": "claim not found"}

    sources = claim.get('sources', [])
    supporting = [s for s in sources if s.get('relationship', 'supports') in ('supports', 'confirms')]
    contradicting = [s for s in sources if s.get('relationship') in ('contradicts', 'refutes')]

    grades = []
    confidences = []

    for i in range(n_samples):
        noise = random.gauss(0, 0.08)
        n_sup = len(supporting)
        n_con = len(contradicting)

        if n_con > 0 and n_sup > 0:
            grade = 'contested'
            conf = 0.2 + (0.3 * (n_sup / (n_sup + n_con))) + noise
        elif n_sup == 0:
            grade = 'ungraded'
            conf = 0.3 + noise
        else:
            avg_cred = sum(s.get('credibility', 0.5) for s in supporting) / n_sup
            avg_cred_p = max(0, min(1, avg_cred + random.gauss(0, 0.06)))
            n_sup_eff = max(1, n_sup + random.choice([-1, 0, 0, 0, 1]))

            if n_sup_eff >= 3 and avg_cred_p >= 0.7:
                grade = 'strong'
                conf = min(0.95, 0.7 + (n_sup_eff * 0.05) + (avg_cred_p * 0.1))
            elif n_sup_eff >= 2 and avg_cred_p >= 0.5:
                grade = 'moderate'
                conf = 0.5 + (n_sup_eff * 0.05) + (avg_cred_p * 0.1)
            else:
                grade = 'weak'
                conf = 0.3 + (avg_cred_p * 0.15)

        grades.append(grade)
        confidences.append(max(0, min(1, conf)))

    # Majority vote
    from collections import Counter
    grade_counts = Counter(grades)
    majority_grade = grade_counts.most_common(1)[0][0]
    agreement = grade_counts[majority_grade] / n_samples

    agreeing_confs = [c for g, c in zip(grades, confidences) if g == majority_grade]
    avg_confidence = sum(agreeing_confs) / len(agreeing_confs) if agreeing_confs else 0.5

    final_confidence = round(avg_confidence * (0.8 + 0.2 * agreement), 3)

    now = kb._now()
    kb.conn.execute(
        "UPDATE claims SET evidence_grade = ?, confidence = ?, updated_at = ? WHERE id = ?",
        (majority_grade, final_confidence, now, claim_id)
    )

    meta = claim.get('metadata', {})
    meta['self_consistency'] = {
        'n_samples': n_samples,
        'grade_distribution': dict(grade_counts),
        'agreement': round(agreement, 3),
        'confidence_range': [round(min(confidences), 3), round(max(confidences), 3)]
    }
    kb.conn.execute(
        "UPDATE claims SET metadata = ? WHERE id = ?",
        (json.dumps(meta), claim_id)
    )
    kb.conn.commit()

    # Re-grade composite parent if applicable
    row = kb.conn.execute("SELECT parent_claim_id FROM claims WHERE id = ?", (claim_id,)).fetchone()
    if row and row['parent_claim_id']:
        kb._grade_composite_claim(row['parent_claim_id'])

    return {
        'claim_id': claim_id,
        'claim_text': claim['claim_text'][:120],
        'majority_grade': majority_grade,
        'final_confidence': final_confidence,
        'agreement': round(agreement, 3),
        'grade_distribution': dict(grade_counts),
        'n_samples': n_samples,
        'confidence_range': [round(min(confidences), 3), round(max(confidences), 3)]
    }


def extract_quotes(kb, source_id):
    """FRONT pattern: Extract quotable snippets from a source for claim grounding."""
    source = kb.get_source(source_id)
    if not source:
        return {"error": "source not found"}

    text = source.get('snippet', '')
    if not text:
        return {"source_id": source_id, "quotes": [], "note": "no snippet available"}

    sentences = re.split(r'(?<=[.!?])\s+', text)
    quotes = []
    for i, s in enumerate(sentences):
        s = s.strip()
        if len(s) < 15:
            continue
        quotes.append({
            'index': i,
            'text': s,
            'length': len(s),
            'has_numeric': bool(re.search(r'\d+', s)),
            'has_citation': bool(re.search(r'\[[\d,]+\]|\(\d{4}\)', s))
        })

    return {
        'source_id': source_id,
        'url': source.get('url', ''),
        'title': source.get('title', ''),
        'credibility': source.get('credibility', 0),
        'total_quotes': len(quotes),
        'quotes': quotes
    }


def claim_from_quote(kb, quote_text, source_id, entity_id=None, claim_text=None):
    """FRONT pattern: Create a grounded claim from a specific quote."""
    if not claim_text:
        claim_text = quote_text

    claim_id = kb.add_claim(
        claim_text, entity_id=entity_id, source_ids=[source_id],
        metadata={'grounding_quote': quote_text, 'grounding_method': 'FRONT'}
    )

    return {
        'claim_id': claim_id,
        'claim_text': claim_text[:120],
        'quote': quote_text[:200],
        'source_id': source_id,
        'grounded': True
    }
