"""Spawn budget and context functions extracted from KnowledgeBase."""


def check_spawn_budget(kb, entity_id, max_depth=8, max_total=400):
    """Check if an agent can spawn sub-agents from this entity."""
    # Walk up parent links to find depth
    depth = 0
    current = entity_id
    root = entity_id
    visited = {entity_id}
    while True:
        parents = kb.conn.execute(
            "SELECT from_id FROM links WHERE to_id = ? AND link_type IN ('child', 'wave', 'spawned')",
            (current,)
        ).fetchall()
        if not parents:
            root = current
            break
        parent_id = parents[0]['from_id']
        if parent_id in visited:
            root = current
            break
        visited.add(parent_id)
        current = parent_id
        depth += 1

    total = _count_tree(kb, root)

    can_spawn = depth < max_depth and total < max_total
    remaining_depth = max(0, max_depth - depth)
    remaining_budget = max(0, max_total - total)

    return {
        'can_spawn': can_spawn,
        'current_depth': depth,
        'max_depth': max_depth,
        'remaining_depth': remaining_depth,
        'total_in_tree': total,
        'max_total': max_total,
        'remaining_budget': remaining_budget,
        'root_id': root,
        'reason': (
            f"Depth {depth}/{max_depth}, tree size {total}/{max_total}"
            if can_spawn else
            f"{'Depth limit reached' if depth >= max_depth else 'Budget exhausted'}: "
            f"depth {depth}/{max_depth}, tree size {total}/{max_total}"
        )
    }


def _count_tree(kb, root_id):
    """Count all entities reachable from root via child/wave/spawned links."""
    count = 1
    visited = {root_id}
    queue = [root_id]
    while queue:
        current = queue.pop(0)
        children = kb.conn.execute(
            "SELECT to_id FROM links WHERE from_id = ? AND link_type IN ('child', 'wave', 'spawned')",
            (current,)
        ).fetchall()
        for row in children:
            child_id = row['to_id']
            if child_id not in visited:
                visited.add(child_id)
                queue.append(child_id)
                count += 1
    return count


def record_spawn(kb, parent_id, title, content="", agent_type="researcher",
                 metadata=None, max_depth=8, max_total=400):
    """Record a sub-agent spawn in the KB (bookkeeping only)."""
    budget = check_spawn_budget(kb, parent_id, max_depth, max_total)

    if not budget['can_spawn']:
        return {
            'spawned': False,
            'reason': budget['reason'],
            'budget': budget
        }

    meta = metadata or {}
    meta['assigned_agent'] = agent_type
    meta['depth'] = budget['current_depth'] + 1
    meta['parent_id'] = parent_id
    meta['root_id'] = budget['root_id']

    entity_id = kb.add_entity(title, content, metadata=meta)
    kb.add_link(parent_id, entity_id, 'spawned')

    kb.add_trace(parent_id, 'spawn', 0,
        f"Spawned sub-agent '{agent_type}' for: {title} "
        f"(depth {meta['depth']}, tree size {budget['total_in_tree'] + 1})")

    return {
        'spawned': True,
        'entity_id': entity_id,
        'depth': meta['depth'],
        'budget': {
            'remaining_depth': budget['remaining_depth'] - 1,
            'remaining_budget': budget['remaining_budget'] - 1,
            'root_id': budget['root_id']
        }
    }


def get_spawn_context(kb, entity_id):
    """Get context for a spawned sub-agent."""
    entity = kb._require_entity(entity_id)
    if entity is None:
        return {'error': f'Entity {entity_id} not found'}

    parents = kb.get_links_to(entity_id)
    parent_summaries = []
    for p in parents:
        if p.get('link_type') in ('child', 'wave', 'spawned'):
            parent_summaries.append({
                'id': p['id'],
                'title': p['title'],
                'content': p['content'][:500] if p.get('content') else ''
            })

    siblings = []
    for p in parents:
        children = kb.get_links_from(p['id'])
        for c in children:
            if c['id'] != entity_id and c.get('link_type') in ('child', 'wave', 'spawned'):
                siblings.append({
                    'id': c['id'],
                    'title': c['title'],
                    'status': c.get('metadata', {}).get('status', 'unknown')
                })

    claims = kb.list_claims(entity_id=entity_id)
    budget = check_spawn_budget(kb, entity_id)

    return {
        'entity': {
            'id': entity['id'],
            'title': entity['title'],
            'content': entity['content'],
            'metadata': entity['metadata']
        },
        'parents': parent_summaries,
        'siblings': siblings,
        'claims_so_far': len(claims),
        'can_spawn': budget['can_spawn'],
        'spawn_budget': budget
    }
