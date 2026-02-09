"""Report generation functions extracted from KnowledgeBase."""

import json
from datetime import datetime


def generate_report(kb, entity_id, include_children=True):
    """Generate a structured report with inline citations from an entity tree."""
    entity = kb._require_entity(entity_id)
    if entity is None:
        return None

    # Collect all related entities (children, stages, etc.)
    all_entities = [entity]
    if include_children:
        children = kb.get_links_from(entity_id)
        all_entities.extend([kb.get_entity(c['id']) for c in children if kb.get_entity(c['id'])])
        # One more level deep
        for child in children:
            grandchildren = kb.get_links_from(child['id'])
            all_entities.extend([kb.get_entity(gc['id']) for gc in grandchildren if kb.get_entity(gc['id'])])

    # Collect all entity IDs
    entity_ids = [e['id'] for e in all_entities if e]

    # Get all claims for these entities
    all_claims = []
    for eid in entity_ids:
        all_claims.extend(kb.list_claims(entity_id=eid))

    # Batch-load all claim-source mappings (avoids N+1)
    source_map = {}  # source_id -> source + ref number
    ref_counter = 1
    claim_source_map = {}
    if all_claims:
        claim_ids = [c['id'] for c in all_claims]
        placeholders = ','.join('?' * len(claim_ids))
        rows = kb.conn.execute(f"""
            SELECT cs.claim_id, s.* FROM sources s
            JOIN claim_sources cs ON s.id = cs.source_id
            WHERE cs.claim_id IN ({placeholders})
        """, claim_ids).fetchall()
        for r in rows:
            sid = r['id']
            if sid not in source_map:
                source_map[sid] = {k: r[k] for k in r.keys() if k != 'claim_id'}
                source_map[sid]['ref'] = ref_counter
                ref_counter += 1
            claim_source_map.setdefault(r['claim_id'], []).append(sid)

    # Build report
    report = f"# {entity['title']}\n\n"
    report += f"*Generated: {kb._now()[:10]}*\n\n"

    # Summary
    if entity.get('content'):
        report += f"## Summary\n\n{entity['content']}\n\n"

    # Claims by grade
    if all_claims:
        strong = [c for c in all_claims if c['evidence_grade'] == 'strong']
        moderate = [c for c in all_claims if c['evidence_grade'] == 'moderate']
        weak = [c for c in all_claims if c['evidence_grade'] == 'weak']
        contested = [c for c in all_claims if c['evidence_grade'] == 'contested']

        if strong:
            report += "## Key Findings (Strong Evidence)\n\n"
            for c in strong:
                refs = _format_refs(claim_source_map.get(c['id'], []), source_map)
                report += f"- {c['claim_text']} {refs}\n"
            report += "\n"

        if moderate:
            report += "## Supporting Findings (Moderate Evidence)\n\n"
            for c in moderate:
                refs = _format_refs(claim_source_map.get(c['id'], []), source_map)
                report += f"- {c['claim_text']} {refs}\n"
            report += "\n"

        if contested:
            report += "## Contested Claims\n\n"
            for c in contested:
                refs = _format_refs(claim_source_map.get(c['id'], []), source_map)
                report += f"- ⚠️ {c['claim_text']} {refs}\n"
            report += "\n"

        if weak:
            report += "## Preliminary Findings (Weak Evidence)\n\n"
            for c in weak:
                refs = _format_refs(claim_source_map.get(c['id'], []), source_map)
                report += f"- {c['claim_text']} {refs}\n"
            report += "\n"

    # Children sections
    if include_children:
        children = kb.get_links_from(entity_id)
        for child in children:
            child_entity = kb.get_entity(child['id'])
            if child_entity and child_entity.get('content'):
                report += f"## {child_entity['title']}\n\n"
                report += f"{child_entity['content']}\n\n"

    # References
    if source_map:
        report += "## References\n\n"
        for sid, src in sorted(source_map.items(), key=lambda x: x[1]['ref']):
            title = src.get('title') or src.get('domain', 'Unknown')
            cred = src.get('credibility', 0)
            cred_label = '★★★' if cred >= 0.8 else '★★' if cred >= 0.6 else '★'
            report += f"[{src['ref']}] {title} — {src['url']} (credibility: {cred_label} {cred:.2f})\n"

    # Confidence summary
    if all_claims:
        avg_conf = sum(c['confidence'] for c in all_claims) / len(all_claims)
        report += f"\n---\n*{len(all_claims)} claims, {len(source_map)} sources, avg confidence: {avg_conf:.2f}*\n"

    return report


def _format_refs(source_ids, source_map):
    """Format citation references from pre-loaded source IDs."""
    refs = [str(source_map[sid]['ref']) for sid in source_ids if sid in source_map]
    return '[' + ','.join(refs) + ']' if refs else ''


def generate_outline(kb, entity_id):
    """Generate a hierarchical report outline from entity tree with evidence strength."""
    entity = kb._require_entity(entity_id)
    if entity is None:
        return None

    sections = []

    # Summary section
    claims = kb.list_claims(entity_id=entity_id)
    strong = [c for c in claims if c['evidence_grade'] == 'strong']
    moderate = [c for c in claims if c['evidence_grade'] == 'moderate']

    sections.append({
        'title': 'Executive Summary',
        'level': 1,
        'entity_id': entity_id,
        'claims': len(claims),
        'strong': len(strong),
        'evidence_strength': 'strong' if len(strong) > len(claims) * 0.5 else 'moderate' if len(moderate) + len(strong) > len(claims) * 0.5 else 'weak'
    })

    # Child sections
    children = kb.get_links_from(entity_id)
    for child in children:
        child_entity = kb.get_entity(child['id'])
        if not child_entity:
            continue

        child_claims = kb.list_claims(entity_id=child['id'])
        child_strong = [c for c in child_claims if c['evidence_grade'] == 'strong']
        child_mod = [c for c in child_claims if c['evidence_grade'] == 'moderate']
        child_contested = [c for c in child_claims if c['evidence_grade'] == 'contested']

        section = {
            'title': child_entity['title'],
            'level': 2,
            'entity_id': child['id'],
            'link_type': child.get('link_type', 'related'),
            'claims': len(child_claims),
            'strong': len(child_strong),
            'contested': len(child_contested),
            'evidence_strength': 'strong' if len(child_strong) > len(child_claims) * 0.5 else 'moderate' if (len(child_mod) + len(child_strong)) > len(child_claims) * 0.5 else 'contested' if child_contested else 'weak',
            'subsections': []
        }

        # Grandchildren
        grandchildren = kb.get_links_from(child['id'])
        for gc in grandchildren:
            gc_entity = kb.get_entity(gc['id'])
            if not gc_entity:
                continue
            gc_claims = kb.list_claims(entity_id=gc['id'])
            section['subsections'].append({
                'title': gc_entity['title'],
                'level': 3,
                'entity_id': gc['id'],
                'claims': len(gc_claims)
            })

        sections.append(section)

    return {
        'root_entity': entity_id,
        'root_title': entity['title'],
        'sections': sections,
        'total_sections': len(sections),
        'total_subsections': sum(len(s.get('subsections', [])) for s in sections)
    }


def synthesize_entity(kb, entity_id, audience='technical'):
    """STORM-style 3-phase synthesis: Outline -> Draft -> Edit."""
    entity = kb._require_entity(entity_id)
    if entity is None:
        return {"error": "entity not found"}

    claims = kb.list_claims(entity_id=entity_id)
    children = kb.get_links_from(entity_id)

    # Phase 1: Outline — group claims into themes
    themes = {}
    for c in claims:
        text = c['claim_text'].lower()
        theme = 'general'
        theme_keywords = {
            'performance': ['performance', 'speed', 'latency', 'throughput', 'efficiency', 'faster', 'slower'],
            'cost': ['cost', 'price', 'expensive', 'cheap', 'budget', 'economic'],
            'feasibility': ['feasible', 'practical', 'possible', 'impossible', 'trl', 'readiness'],
            'comparison': ['compared', 'versus', 'better', 'worse', 'alternative', 'traditional'],
            'mechanism': ['mechanism', 'works', 'process', 'method', 'technique', 'approach'],
            'limitation': ['limitation', 'challenge', 'problem', 'difficulty', 'barrier', 'cannot'],
            'evidence': ['study', 'experiment', 'measured', 'demonstrated', 'showed', 'found'],
        }
        for t, keywords in theme_keywords.items():
            if any(kw in text for kw in keywords):
                theme = t
                break
        themes.setdefault(theme, []).append(c)

    # Phase 2: Draft — structure by theme with citations
    sections = []
    source_refs = {}
    ref_counter = 1

    for theme_name, theme_claims in themes.items():
        theme_claims.sort(key=lambda c: c.get('confidence', 0) or 0, reverse=True)

        section_claims = []
        for c in theme_claims:
            claim_sources = kb.conn.execute("""
                SELECT s.id, s.title, s.url FROM sources s
                JOIN claim_sources cs ON s.id = cs.source_id
                WHERE cs.claim_id = ?
            """, (c['id'],)).fetchall()

            refs = []
            for s in claim_sources:
                if s['id'] not in source_refs:
                    source_refs[s['id']] = {'ref': ref_counter, 'title': s['title'], 'url': s['url']}
                    ref_counter += 1
                refs.append(source_refs[s['id']]['ref'])

            ref_str = ', '.join(f'[{r}]' for r in refs) if refs else ''
            section_claims.append({
                'text': c['claim_text'],
                'grade': c['evidence_grade'],
                'confidence': c.get('confidence', 0),
                'refs': ref_str
            })

        sections.append({
            'theme': theme_name.replace('_', ' ').title(),
            'claim_count': len(section_claims),
            'avg_confidence': sum(c['confidence'] or 0 for c in section_claims) / max(len(section_claims), 1),
            'claims': section_claims
        })

    # Phase 3: Edit — audience adaptation
    audience_config = {
        'technical': {'detail': 'full', 'jargon': True, 'citations': True},
        'executive': {'detail': 'summary', 'jargon': False, 'citations': False},
        'general': {'detail': 'moderate', 'jargon': False, 'citations': True},
    }
    config = audience_config.get(audience, audience_config['technical'])

    child_sections = []
    for child in children:
        child_entity = kb.get_entity(child['id'])
        if child_entity and child_entity.get('content'):
            child_sections.append({
                'title': child_entity['title'],
                'content': child_entity['content'][:500] if config['detail'] == 'summary' else child_entity['content']
            })

    return {
        'entity_id': entity_id,
        'title': entity.get('title', ''),
        'audience': audience,
        'sections': sections,
        'child_sections': child_sections,
        'total_claims': len(claims),
        'total_themes': len(sections),
        'total_references': len(source_refs),
        'references': {str(v['ref']): {'title': v['title'], 'url': v['url']} for v in source_refs.values()},
        'config': config
    }


def export_entity_markdown(kb, entity_id):
    """Export an entity as markdown with frontmatter."""
    entity = kb._require_entity(entity_id)
    if entity is None:
        return None

    links_from = kb.get_links_from(entity_id)
    links_to = kb.get_links_to(entity_id)

    md = f"""---
id: {entity['id']}
title: {entity['title']}
created_at: {entity['created_at']}
updated_at: {entity['updated_at']}
metadata: {json.dumps(entity['metadata'])}
---

# {entity['title']}

{entity['content']}

"""

    if links_from:
        md += "\n## Linked Entities\n\n"
        for link in links_from:
            md += f"- [{link['title']}](./{link['id']}.md) ({link['link_type']})\n"

    if links_to:
        md += "\n## Referenced By\n\n"
        for link in links_to:
            md += f"- [{link['title']}](./{link['id']}.md) ({link['link_type']})\n"

    return md
