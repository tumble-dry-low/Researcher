"""Quality review and QA functions extracted from KnowledgeBase."""

import re


def review(kb, entity_id, depth='full'):
    """Unified review: combines reflect, critique, gaps, and quantities.

    depth='quick': structural checks only (fast)
    depth='full':  structural + semantic + gaps + quantities (thorough)
    """
    entity = kb._require_entity(entity_id)
    if entity is None:
        return {"error": "entity not found"}

    result = {
        'entity_id': entity_id,
        'entity_title': entity.get('title', ''),
        'depth': depth,
        'sections': {},
    }
    all_issues = []

    # ── Structural reflection (always) ──────────────────────────
    claims = kb.list_claims(entity_id=entity_id)
    sources = kb.list_sources(entity_id=entity_id)

    reflect_issues = []

    # Check: claims without sources
    unsourced = [c for c in claims if c['source_count'] == 0]
    if unsourced:
        reflect_issues.append({
            'type': 'unsourced_claims',
            'severity': 'high',
            'count': len(unsourced),
            'claims': [c['claim_text'][:80] for c in unsourced]
        })

    # Check: weak claims
    weak = [c for c in claims if c['evidence_grade'] == 'weak']
    if len(weak) > len(claims) * 0.5 and claims:
        reflect_issues.append({
            'type': 'majority_weak_evidence',
            'severity': 'medium',
            'detail': f"{len(weak)}/{len(claims)} claims have weak evidence"
        })

    # Check: contested claims unresolved
    contested = [c for c in claims if c['evidence_grade'] == 'contested']
    if contested:
        reflect_issues.append({
            'type': 'unresolved_contradictions',
            'severity': 'high',
            'count': len(contested),
            'claims': [c['claim_text'][:80] for c in contested]
        })

    # Check: low source diversity (all from same domain)
    if sources:
        domains = set()
        for s in sources:
            d = s.get('domain', '')
            if d:
                domains.add(d)
        if len(domains) <= 1 and len(sources) > 1:
            reflect_issues.append({
                'type': 'low_source_diversity',
                'severity': 'medium',
                'detail': f"All {len(sources)} sources from domain: {domains.pop() if domains else 'unknown'}"
            })

    # Check: no high-credibility sources
    high_cred = [s for s in sources if s.get('credibility', 0) >= 0.8]
    if not high_cred and sources:
        reflect_issues.append({
            'type': 'no_high_credibility_sources',
            'severity': 'medium',
            'detail': f"Best source credibility: {max(s.get('credibility', 0) for s in sources):.2f}"
        })

    # Check: children without claims
    children = kb.get_links_from(entity_id)
    empty_children = []
    for child in children:
        child_claims = kb.list_claims(entity_id=child['id'])
        if not child_claims:
            empty_children.append(child['title'][:60])
    if empty_children:
        reflect_issues.append({
            'type': 'unexplored_angles',
            'severity': 'low',
            'detail': f"{len(empty_children)} child entities have no claims",
            'entities': empty_children
        })

    # Reflection verdict
    high_issues = len([i for i in reflect_issues if i['severity'] == 'high'])
    med_issues = len([i for i in reflect_issues if i['severity'] == 'medium'])

    if high_issues > 0:
        reflect_verdict = 'needs_work'
    elif med_issues > 1:
        reflect_verdict = 'acceptable_with_caveats'
    else:
        reflect_verdict = 'solid'

    result['sections']['structural'] = {
        'verdict': reflect_verdict,
        'issues': reflect_issues,
        'claim_count': len(claims),
        'source_count': len(sources),
    }
    all_issues.extend(reflect_issues)

    if depth == 'full':
        # ── Semantic critique ───────────────────────────────────
        critique_issues = []

        if claims:
            # 1. Circular reasoning detection
            claim_texts = {c['id']: c['claim_text'].lower() for c in claims}
            for c in claims:
                c_sources = kb.conn.execute("""
                    SELECT s.snippet FROM sources s
                    JOIN claim_sources cs ON s.id = cs.source_id
                    WHERE cs.claim_id = ?
                """, (c['id'],)).fetchall()
                for src in c_sources:
                    snippet = (src['snippet'] or '').lower()
                    for other_id, other_text in claim_texts.items():
                        if other_id != c['id'] and len(other_text) > 30:
                            other_words = set(other_text.split())
                            snippet_words = set(snippet.split())
                            overlap = len(other_words & snippet_words) / max(len(other_words), 1)
                            if overlap > 0.6:
                                critique_issues.append({
                                    'type': 'potential_circular',
                                    'severity': 'high',
                                    'claim_id': c['id'],
                                    'related_claim_id': other_id,
                                    'detail': f'Claim {c["id"]} source overlaps {overlap:.0%} with claim {other_id}'
                                })

            # 2. Unsupported quantitative claims
            for c in claims:
                has_numbers = bool(re.search(r'\d+\.?\d*\s*(%|x|×|fold|times|order)', c['claim_text']))
                source_count = c.get('source_count', 0)
                if has_numbers and source_count < 2:
                    critique_issues.append({
                        'type': 'unsupported_quantitative',
                        'severity': 'medium',
                        'claim_id': c['id'],
                        'detail': f'Quantitative claim with only {source_count} source(s): {c["claim_text"][:80]}'
                    })

            # 3. Logical gap detection
            all_text = ' '.join(c['claim_text'] for c in claims).lower()
            for c in claims:
                concepts = re.findall(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', c['claim_text'])
                for concept in concepts:
                    if all_text.count(concept.lower()) <= 1:
                        critique_issues.append({
                            'type': 'unexplored_concept',
                            'severity': 'low',
                            'claim_id': c['id'],
                            'detail': f'Concept "{concept}" mentioned only once — may need investigation'
                        })

            # 4. Missing counter-evidence
            grades = [c['evidence_grade'] for c in claims]
            if 'contested' not in grades and len(claims) > 5:
                critique_issues.append({
                    'type': 'no_counter_evidence',
                    'severity': 'medium',
                    'detail': f'All {len(claims)} claims agree — no counter-evidence sought'
                })

            # 5. Confidence-evidence mismatch
            for c in claims:
                conf = c.get('confidence', 0) or 0
                source_count = c.get('source_count', 0)
                if conf > 0.8 and source_count <= 1:
                    critique_issues.append({
                        'type': 'overconfident',
                        'severity': 'medium',
                        'claim_id': c['id'],
                        'detail': f'High confidence ({conf:.2f}) with only {source_count} source(s)'
                    })

        # Critique verdict
        critique_issues = [i for i in critique_issues
                         if i['type'] not in ('source_bias',)]

        high_c = sum(1 for i in critique_issues if i['severity'] == 'high')
        med_c = sum(1 for i in critique_issues if i['severity'] == 'medium')

        if high_c >= 2:
            critique_verdict = 'significant_concerns'
        elif high_c >= 1 or med_c >= 3:
            critique_verdict = 'needs_attention'
        elif med_c >= 1:
            critique_verdict = 'minor_concerns'
        else:
            critique_verdict = 'passes_critique' if claims else 'no_claims'

        # Log trace
        kb.add_trace(entity_id, 'critique', 99,
            f'Critique: {len(critique_issues)} issues ({high_c} high, {med_c} med). Verdict: {critique_verdict}')

        result['sections']['critique'] = {
            'verdict': critique_verdict,
            'issues': critique_issues,
        }
        all_issues.extend(critique_issues)

        # ── Gap detection ───────────────────────────────────────
        gap_issues = []

        # 1. Coverage gaps
        content = (entity.get('content') or '').lower()
        claim_text_all = ' '.join(c['claim_text'].lower() for c in claims)

        content_words = re.findall(r'\b([a-z]{4,})\b', content)
        claim_words = set(re.findall(r'\b([a-z]{4,})\b', claim_text_all))

        uncovered = [w for w in set(content_words) if w not in claim_words
                     and content_words.count(w) >= 2
                     and w not in ('this', 'that', 'with', 'have', 'from', 'they',
                                   'been', 'their', 'will', 'about', 'could', 'would',
                                   'should', 'which', 'these', 'those', 'more', 'also',
                                   'than', 'each', 'into', 'some', 'such', 'most')]
        if uncovered:
            gap_issues.append({
                'type': 'uncovered_topics',
                'severity': 'medium',
                'topics': uncovered[:10],
                'detail': f'{len(uncovered)} topics mentioned in content but not in claims'
            })

        # 2. Question gaps
        question_markers = re.findall(r'(?:whether|if|how|why|when|what)\s+[^.]{10,50}', claim_text_all)
        for q in question_markers[:5]:
            gap_issues.append({
                'type': 'implicit_question',
                'severity': 'low',
                'detail': f'Implicit question in claims: "{q.strip()[:80]}"'
            })

        # 3. Assumption gaps
        assumption_markers = ['assuming', 'given that', 'if we assume', 'typically',
                            'generally', 'usually', 'it is known that', 'obviously']
        for c in claims:
            text_lower = c['claim_text'].lower()
            for marker in assumption_markers:
                if marker in text_lower:
                    gap_issues.append({
                        'type': 'unverified_assumption',
                        'severity': 'medium',
                        'claim_id': c['id'],
                        'detail': f'Assumption "{marker}" in: {c["claim_text"][:80]}'
                    })

        # 4. Perspective gaps
        from researcher.kb_analysis import discover_perspectives
        perspectives = discover_perspectives(kb, entity.get('title', ''))
        covered_perspectives = set()
        for c in claims:
            text_lower = c['claim_text'].lower()
            for p in perspectives.get('perspectives', []):
                if any(kw in text_lower for kw in p.get('keywords', [])):
                    covered_perspectives.add(p['name'])

        all_perspectives = set(p['name'] for p in perspectives.get('perspectives', []))
        missing = all_perspectives - covered_perspectives
        if missing:
            gap_issues.append({
                'type': 'missing_perspectives',
                'severity': 'medium',
                'perspectives': list(missing)[:5],
                'detail': f'{len(missing)} perspectives not covered: {", ".join(list(missing)[:3])}'
            })

        # 5. Weak coverage
        thin = []
        for child in children:
            child_claims = kb.list_claims(entity_id=child['id'])
            if 0 < len(child_claims) < 3:
                child_entity = kb.get_entity(child['id'])
                if child_entity:
                    thin.append(f'{child_entity["title"][:40]} ({len(child_claims)} claims)')
        if thin:
            gap_issues.append({
                'type': 'thin_coverage',
                'severity': 'medium',
                'subtopics': thin,
                'detail': f'{len(thin)} sub-entities have < 3 claims'
            })

        # Priority-sort
        severity_order = {'high': 0, 'medium': 1, 'low': 2}
        gap_issues.sort(key=lambda g: severity_order.get(g['severity'], 3))

        gap_issues = [g for g in gap_issues if g['type'] not in ('empty_subtopics',)]

        gap_suggested = [
            f"Investigate: {g['detail'][:60]}" for g in gap_issues if g['severity'] in ('high', 'medium')
        ][:5]

        result['sections']['gaps'] = {
            'total_gaps': len(gap_issues),
            'gaps': gap_issues,
            'suggested_actions': gap_suggested,
        }
        all_issues.extend([{'type': g['type'], 'severity': g['severity'],
                           'detail': g.get('detail', '')} for g in gap_issues])

        # ── Quantitative verification ───────────────────────────
        quant_issues = []
        quant_checked = 0

        for c in claims:
            text = c['claim_text']

            numbers = re.findall(
                r'(\d+\.?\d*)\s*(%%|%|°C|°F|K|GPa|MPa|Pa|eV|MeV|keV|GeV|'
                r'nm|μm|mm|cm|m|km|fm|pm|'
                r'kg|g|mg|μg|'
                r'W|kW|MW|GW|TW|'
                r'A|mA|T|'
                r'Hz|kHz|MHz|GHz|'
                r'dpa|mol|wt|at|ppm|ppb|'
                r'x|×|fold|times)',
                text
            )

            if not numbers:
                continue
            quant_checked += 1

            for value_str, unit in numbers:
                try:
                    value = float(value_str)
                except ValueError:
                    continue

                if unit in ('°C', '°F', 'K'):
                    if unit == 'K' and value < 0:
                        quant_issues.append({
                            'type': 'impossible_value',
                            'severity': 'high',
                            'claim_id': c['id'],
                            'detail': f'Negative Kelvin temperature: {value}K'
                        })
                    elif unit == '°C' and value > 10000:
                        quant_issues.append({
                            'type': 'implausible_value',
                            'severity': 'medium',
                            'claim_id': c['id'],
                            'detail': f'Extremely high temperature: {value}°C'
                        })

                if unit in ('%', '%%'):
                    if value > 100 and 'improvement' not in text.lower() and 'increase' not in text.lower():
                        quant_issues.append({
                            'type': 'suspicious_percentage',
                            'severity': 'low',
                            'claim_id': c['id'],
                            'detail': f'Percentage > 100%: {value}% (may be valid for improvement metrics)'
                        })

                if unit in ('eV', 'MeV', 'keV', 'GeV'):
                    if value < 0:
                        quant_issues.append({
                            'type': 'impossible_value',
                            'severity': 'high',
                            'claim_id': c['id'],
                            'detail': f'Negative energy: {value} {unit}'
                        })

                if unit in ('x', '×', 'fold', 'times'):
                    if value > 1000:
                        quant_issues.append({
                            'type': 'extreme_multiplier',
                            'severity': 'medium',
                            'claim_id': c['id'],
                            'detail': f'Very large multiplier: {value}{unit}'
                        })

            has_number = bool(numbers)
            has_uncertainty = bool(re.search(r'±|plus or minus|error|uncertainty|confidence interval|range|approximately|~|≈', text, re.I))
            if has_number and not has_uncertainty and c.get('evidence_grade') != 'strong':
                quant_issues.append({
                    'type': 'missing_uncertainty',
                    'severity': 'low',
                    'claim_id': c['id'],
                    'detail': f'Numerical claim without uncertainty bounds: {text[:80]}'
                })

        # Cross-reference contradicting numbers
        num_claims = [(c, re.findall(r'(\d+\.?\d*)\s*(%|°C|K|x|×)', c['claim_text'])) for c in claims]
        for i, (c1, nums1) in enumerate(num_claims):
            for j, (c2, nums2) in enumerate(num_claims):
                if j <= i:
                    continue
                words1 = set(c1['claim_text'].lower().split())
                words2 = set(c2['claim_text'].lower().split())
                overlap = len(words1 & words2) / max(len(words1 | words2), 1)
                if overlap > 0.3 and nums1 and nums2:
                    for v1, u1 in nums1:
                        for v2, u2 in nums2:
                            if u1 == u2:
                                try:
                                    ratio = float(v1) / float(v2) if float(v2) != 0 else 999
                                    if ratio > 3 or ratio < 0.33:
                                        quant_issues.append({
                                            'type': 'numerical_disagreement',
                                            'severity': 'medium',
                                            'claim_ids': [c1['id'], c2['id']],
                                            'detail': f'{v1}{u1} vs {v2}{u2} ({ratio:.1f}x difference)'
                                        })
                                except ValueError:
                                    pass

        result['sections']['quantitative'] = {
            'claims_checked': quant_checked,
            'issues': quant_issues,
        }
        all_issues.extend(quant_issues)

    # Overall verdict
    high = sum(1 for i in all_issues if i.get('severity') == 'high')
    med = sum(1 for i in all_issues if i.get('severity') == 'medium')

    if high >= 2:
        verdict = 'significant_concerns'
    elif high >= 1 or med >= 3:
        verdict = 'needs_attention'
    elif med >= 1:
        verdict = 'minor_concerns'
    elif all_issues:
        verdict = 'minor_notes'
    else:
        verdict = 'clean'

    result['total_issues'] = len(all_issues)
    result['high_severity'] = high
    result['medium_severity'] = med
    result['verdict'] = verdict

    return result


def qa(kb, entity_id, n_samples=5, search_fn=None):
    """Unified quality assurance: self-consistency grading + SAFE verification."""
    claims = kb.list_claims(entity_id=entity_id)

    # ── Self-consistency grading ────────────────────────────────
    from researcher.kb_verify import grade_claim_sc, verify_claim
    sc_results = []
    grade_changes = 0
    for c in claims:
        old_grade = c['evidence_grade']
        r = grade_claim_sc(kb, c['id'], n_samples=n_samples)
        if 'error' not in r:
            sc_results.append(r)
            if r['majority_grade'] != old_grade:
                grade_changes += 1

    if sc_results:
        sc_result = {
            'total_graded': len(sc_results),
            'grade_changes': grade_changes,
            'avg_agreement': round(sum(r['agreement'] for r in sc_results) / len(sc_results), 3),
            'avg_confidence': round(sum(r['final_confidence'] for r in sc_results) / len(sc_results), 3),
        }
    else:
        sc_result = {'total_graded': 0, 'grade_changes': 0, 'avg_agreement': 0, 'avg_confidence': 0}

    # ── SAFE verification ───────────────────────────────────────
    verify_results = []
    for c in claims:
        v = verify_claim(kb, c['id'], search_fn=search_fn)
        if 'error' not in v:
            verify_results.append(v)

    if verify_results:
        avg_fact = sum(r['factuality_score'] for r in verify_results) / len(verify_results)
        verified = sum(1 for r in verify_results if r['verified_atoms'] > 0)
        verify_result = {
            'total_verified': len(verify_results),
            'externally_verified': verified,
            'avg_factuality': round(avg_fact, 3),
            'min_factuality': round(min(r['factuality_score'] for r in verify_results), 3),
        }
    else:
        verify_result = {'total_verified': 0, 'externally_verified': 0, 'avg_factuality': 0, 'min_factuality': 0}

    return {
        'entity_id': entity_id,
        'grading': sc_result,
        'verification': verify_result,
    }
