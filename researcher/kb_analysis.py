"""Analysis functions extracted from KnowledgeBase."""

import json
import re
import sqlite3
from datetime import datetime, timedelta


def check_contradictions(kb, entity_id=None):
    """Find claims that are contradicted by sources."""
    query = """
        SELECT c.id as claim_id, c.claim_text, c.entity_id, c.evidence_grade, c.confidence,
               cs.relationship, s.id as source_id, s.url, s.title as source_title, s.credibility
        FROM claims c
        JOIN claim_sources cs ON c.id = cs.claim_id
        JOIN sources s ON cs.source_id = s.id
        WHERE cs.relationship IN ('contradicts', 'refutes')
    """
    params = []
    if entity_id:
        query += " AND c.entity_id = ?"
        params.append(entity_id)
    query += " ORDER BY s.credibility DESC"

    rows = kb.conn.execute(query, params).fetchall()
    return [{k: r[k] for k in r.keys()} for r in rows]


def check_corroboration(kb, entity_id=None):
    """Score how well-corroborated each claim is."""
    query = """
        SELECT c.id, c.claim_text, c.entity_id, c.evidence_grade, c.confidence,
               COUNT(CASE WHEN cs.relationship IN ('supports','confirms') THEN 1 END) as supporting_sources,
               COUNT(CASE WHEN cs.relationship IN ('contradicts','refutes') THEN 1 END) as contradicting_sources,
               AVG(CASE WHEN cs.relationship IN ('supports','confirms') THEN s.credibility END) as avg_support_credibility,
               AVG(CASE WHEN cs.relationship IN ('contradicts','refutes') THEN s.credibility END) as avg_contradict_credibility
        FROM claims c
        LEFT JOIN claim_sources cs ON c.id = cs.claim_id
        LEFT JOIN sources s ON cs.source_id = s.id
    """
    params = []
    if entity_id:
        query += " WHERE c.entity_id = ?"
        params.append(entity_id)
    query += " GROUP BY c.id ORDER BY supporting_sources DESC"

    rows = kb.conn.execute(query, params).fetchall()
    results = []
    for r in rows:
        n_sup = r['supporting_sources'] or 0
        n_con = r['contradicting_sources'] or 0
        avg_sup = r['avg_support_credibility'] or 0
        avg_con = r['avg_contradict_credibility'] or 0

        if n_sup + n_con == 0:
            corroboration = 0.0
        else:
            corroboration = round((n_sup * avg_sup - n_con * avg_con) / (n_sup + n_con), 3)

        results.append({
            'claim_id': r['id'],
            'claim_text': r['claim_text'],
            'entity_id': r['entity_id'],
            'evidence_grade': r['evidence_grade'],
            'supporting_sources': n_sup,
            'contradicting_sources': n_con,
            'corroboration_score': corroboration,
            'confidence': r['confidence']
        })
    return results


def apply_confidence_decay(kb, days_threshold=30, decay_rate=0.02):
    """Decay confidence on claims older than threshold."""
    if days_threshold <= 0:
        days_threshold = 1
    cutoff = (datetime.utcnow() - timedelta(days=days_threshold)).isoformat()

    rows = kb.conn.execute(
        "SELECT id, claim_text, confidence, created_at FROM claims WHERE created_at < ? AND status = 'active'",
        (cutoff,)
    ).fetchall()

    affected = []
    for row in rows:
        created = datetime.fromisoformat(row['created_at'])
        age_days = (datetime.utcnow() - created).days
        periods = (age_days - days_threshold) // days_threshold + 1
        new_conf = max(0.1, round(row['confidence'] * ((1 - decay_rate) ** periods), 3))

        if new_conf < row['confidence']:
            kb.conn.execute(
                "UPDATE claims SET confidence = ? WHERE id = ?",
                (new_conf, row['id'])
            )
            affected.append({
                'claim_id': row['id'],
                'claim_text': row['claim_text'][:80],
                'old_confidence': row['confidence'],
                'new_confidence': new_conf,
                'age_days': age_days
            })

    kb.conn.commit()
    return affected


def find_prior_research(kb, query, min_confidence=0.4):
    """Search existing KB for relevant prior entities and claims using FTS5."""
    fts_query = ' OR '.join(query.split())

    try:
        entities = kb.conn.execute("""
            SELECT e.id, e.title, e.content, e.metadata, e.created_at
            FROM entities e
            JOIN entities_fts f ON f.entity_id = e.id
            WHERE entities_fts MATCH ?
            ORDER BY rank LIMIT 10
        """, (fts_query,)).fetchall()
    except sqlite3.OperationalError:
        search_term = f"%{query}%"
        entities = kb.conn.execute("""
            SELECT id, title, content, metadata, created_at FROM entities
            WHERE (title LIKE ? OR content LIKE ?)
            ORDER BY updated_at DESC LIMIT 10
        """, (search_term, search_term)).fetchall()

    try:
        claims = kb.conn.execute("""
            SELECT c.id, c.claim_text, c.evidence_grade, c.confidence, c.entity_id
            FROM claims c
            JOIN claims_fts f ON CAST(f.claim_id AS INTEGER) = c.id
            WHERE claims_fts MATCH ? AND c.confidence >= ? AND c.status = 'active'
            ORDER BY c.confidence DESC LIMIT 20
        """, (fts_query, min_confidence)).fetchall()
    except sqlite3.OperationalError:
        search_term = f"%{query}%"
        claims = kb.conn.execute("""
            SELECT c.id, c.claim_text, c.evidence_grade, c.confidence, c.entity_id
            FROM claims c
            WHERE c.claim_text LIKE ? AND c.confidence >= ? AND c.status = 'active'
            ORDER BY c.confidence DESC LIMIT 20
        """, (search_term, min_confidence)).fetchall()

    return {
        'query': query,
        'prior_entities': [
            {'id': e['id'], 'title': e['title'],
             'content_preview': (e['content'] or '')[:200],
             'created_at': e['created_at']}
            for e in entities
        ],
        'prior_claims': [
            {'id': c['id'], 'claim_text': c['claim_text'],
             'grade': c['evidence_grade'], 'confidence': c['confidence'],
             'entity_id': c['entity_id']}
            for c in claims
        ],
        'entity_count': len(entities),
        'claim_count': len(claims)
    }


def discover_perspectives(kb, topic):
    """Discover research perspectives from existing KB entities on a topic."""
    search_term = f"%{topic}%"
    entities = kb.conn.execute("""
        SELECT id, title, content, metadata FROM entities
        WHERE (title LIKE ? OR content LIKE ?)
        ORDER BY updated_at DESC LIMIT 20
    """, (search_term, search_term)).fetchall()

    existing_angles = set()
    entity_angles = []
    for e in entities:
        meta = json.loads(e['metadata'] or '{}')
        angle = meta.get('angle', '')
        if angle:
            existing_angles.add(angle)
            entity_angles.append({'id': e['id'], 'title': e['title'], 'angle': angle})

    claims = kb.conn.execute("""
        SELECT c.claim_text, c.evidence_grade, c.entity_id FROM claims c
        JOIN entities e ON c.entity_id = e.id
        WHERE (e.title LIKE ? OR e.content LIKE ? OR c.claim_text LIKE ?)
        AND c.status = 'active'
        ORDER BY c.confidence DESC LIMIT 30
    """, (search_term, search_term, search_term)).fetchall()

    standard_perspectives = [
        'technical_feasibility', 'economic_analysis', 'risk_assessment',
        'competitive_landscape', 'historical_context', 'future_projections',
        'stakeholder_impact', 'regulatory_environment', 'implementation_challenges',
        'alternative_approaches', 'environmental_impact', 'scalability'
    ]

    covered = set()
    for angle in existing_angles:
        angle_lower = angle.lower()
        for sp in standard_perspectives:
            if any(word in angle_lower for word in sp.split('_')):
                covered.add(sp)

    uncovered = [p for p in standard_perspectives if p not in covered]

    return {
        'topic': topic,
        'existing_entities': len(entities),
        'existing_angles': list(existing_angles),
        'entity_angles': entity_angles[:10],
        'existing_claims': len(claims),
        'strong_claims': len([c for c in claims if c['evidence_grade'] in ('strong', 'moderate')]),
        'suggested_perspectives': uncovered[:6],
        'coverage_ratio': f"{len(covered)}/{len(standard_perspectives)}"
    }
