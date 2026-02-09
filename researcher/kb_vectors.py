"""Vector embedding and semantic search functions extracted from KnowledgeBase."""

import hashlib
from datetime import datetime


def _get_embedding_model(kb):
    """Lazy-load sentence-transformers model."""
    if kb._embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            kb._embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        except ImportError:
            raise RuntimeError("pip install sentence-transformers for vector search")
    return kb._embedding_model


def _embed_text(kb, text):
    """Embed text and return serialized float32 vector for sqlite-vec."""
    import struct
    model = _get_embedding_model(kb)
    embedding = model.encode(text, normalize_embeddings=True)
    return struct.pack(f'{len(embedding)}f', *embedding)


def _text_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def embed_entity(kb, entity_id):
    """Embed an entity's title+content into the vector index. Returns success."""
    if not kb._vec_available:
        return False
    entity = kb.get_entity(entity_id)
    if not entity:
        return False
    text = f"{entity['title']}. {entity.get('content', '')}"[:2000]
    text_h = _text_hash(text)

    existing = kb.conn.execute(
        "SELECT vec_rowid, text_hash FROM embedding_map WHERE source_table = 'entities' AND source_id = ?",
        (entity_id,)
    ).fetchone()
    if existing and existing['text_hash'] == text_h:
        return True

    vec = _embed_text(kb, text)
    now = kb._now()

    if existing:
        kb.conn.execute("UPDATE vec_embeddings SET embedding = ? WHERE rowid = ?",
                          (vec, existing['vec_rowid']))
        kb.conn.execute("UPDATE embedding_map SET text_hash = ?, embedded_at = ? WHERE vec_rowid = ?",
                          (text_h, now, existing['vec_rowid']))
    else:
        cursor = kb.conn.execute("INSERT INTO vec_embeddings (embedding) VALUES (?)", (vec,))
        rowid = cursor.lastrowid
        kb.conn.execute(
            "INSERT INTO embedding_map (vec_rowid, source_table, source_id, text_hash, embedded_at) "
            "VALUES (?, 'entities', ?, ?, ?)",
            (rowid, entity_id, text_h, now)
        )
    kb.conn.commit()
    return True


def embed_claim(kb, claim_id):
    """Embed a claim into the vector index. Returns success."""
    if not kb._vec_available:
        return False
    claim = kb.get_claim(claim_id)
    if not claim:
        return False
    text = claim['claim_text'][:1000]
    text_h = _text_hash(text)
    claim_id_str = str(claim_id)

    existing = kb.conn.execute(
        "SELECT vec_rowid, text_hash FROM embedding_map WHERE source_table = 'claims' AND source_id = ?",
        (claim_id_str,)
    ).fetchone()
    if existing and existing['text_hash'] == text_h:
        return True

    vec = _embed_text(kb, text)
    now = kb._now()

    if existing:
        kb.conn.execute("UPDATE vec_embeddings SET embedding = ? WHERE rowid = ?",
                          (vec, existing['vec_rowid']))
        kb.conn.execute("UPDATE embedding_map SET text_hash = ?, embedded_at = ? WHERE vec_rowid = ?",
                          (text_h, now, existing['vec_rowid']))
    else:
        cursor = kb.conn.execute("INSERT INTO vec_embeddings (embedding) VALUES (?)", (vec,))
        rowid = cursor.lastrowid
        kb.conn.execute(
            "INSERT INTO embedding_map (vec_rowid, source_table, source_id, text_hash, embedded_at) "
            "VALUES (?, 'claims', ?, ?, ?)",
            (rowid, claim_id_str, text_h, now)
        )
    kb.conn.commit()
    return True


def embed_all(kb):
    """Embed all entities and claims. Returns counts."""
    if not kb._vec_available:
        return {'error': 'sqlite-vec not available', 'entities': 0, 'claims': 0}
    entities = kb.conn.execute("SELECT id FROM entities").fetchall()
    claims = kb.conn.execute("SELECT id FROM claims WHERE is_atomic = 0").fetchall()
    e_count = sum(1 for e in entities if embed_entity(kb, e['id']))
    c_count = sum(1 for c in claims if embed_claim(kb, c['id']))
    return {'entities': e_count, 'claims': c_count}


def semantic_search(kb, query, limit=10, source_table=None):
    """Search by semantic similarity using vector embeddings."""
    if not kb._vec_available:
        return [{'id': e['id'], 'title': e['title'], 'score': 1.0, 'source': 'entities', 'method': 'fts5_fallback'}
                for e in kb.search_entities(query)[:limit]]

    vec = _embed_text(kb, query)
    rows = kb.conn.execute(
        "SELECT rowid, distance FROM vec_embeddings WHERE embedding MATCH ? ORDER BY distance LIMIT ?",
        (vec, limit * 2)
    ).fetchall()

    results = []
    for row in rows:
        mapping = kb.conn.execute(
            "SELECT source_table, source_id FROM embedding_map WHERE vec_rowid = ?",
            (row['rowid'],)
        ).fetchone()
        if not mapping:
            continue
        if source_table and mapping['source_table'] != source_table:
            continue

        result = {
            'source': mapping['source_table'],
            'distance': round(row['distance'], 4),
            'score': round(1.0 - row['distance'], 4),
            'method': 'vector'
        }
        if mapping['source_table'] == 'entities':
            entity = kb.get_entity(mapping['source_id'])
            if entity:
                result.update({'id': entity['id'], 'title': entity['title'],
                               'content': entity['content'][:200] if entity.get('content') else ''})
        elif mapping['source_table'] == 'claims':
            claim = kb.get_claim(int(mapping['source_id']))
            if claim:
                result.update({'id': claim['id'], 'claim_text': claim['claim_text'],
                               'evidence_grade': claim['evidence_grade'], 'confidence': claim['confidence']})
        results.append(result)
        if len(results) >= limit:
            break
    return results


def hybrid_search(kb, query, limit=10, source_table=None):
    """Reciprocal Rank Fusion of FTS5 keyword search + vector similarity search."""
    k = 60

    # FTS5 keyword results
    fts_results = {}
    if source_table in (None, 'entities'):
        for rank, entity in enumerate(kb.search_entities(query)):
            fts_results[('entities', entity['id'])] = rank + 1
    if source_table in (None, 'claims'):
        try:
            rows = kb.conn.execute(
                "SELECT claim_id, rank FROM claims_fts WHERE claims_fts MATCH ? ORDER BY rank LIMIT ?",
                (query, limit * 2)
            ).fetchall()
            for rank, row in enumerate(rows):
                fts_results[('claims', str(row['claim_id']))] = rank + 1
        except Exception:
            pass

    # Vector results
    vec_results = {}
    if kb._vec_available:
        for rank, r in enumerate(semantic_search(kb, query, limit * 2, source_table)):
            key = (r['source'], str(r.get('id', '')))
            vec_results[key] = rank + 1

    # RRF fusion
    all_keys = set(fts_results.keys()) | set(vec_results.keys())
    scored = []
    for key in all_keys:
        fts_rank = fts_results.get(key, limit * 3)
        vec_rank = vec_results.get(key, limit * 3)
        rrf_score = 1.0 / (k + fts_rank) + 1.0 / (k + vec_rank)
        scored.append((key, rrf_score))
    scored.sort(key=lambda x: x[1], reverse=True)

    results = []
    for (src_table, src_id), rrf_score in scored[:limit]:
        result = {'source': src_table, 'rrf_score': round(rrf_score, 6), 'method': 'hybrid'}
        if src_table == 'entities':
            entity = kb.get_entity(src_id)
            if entity:
                result.update({'id': entity['id'], 'title': entity['title'],
                               'content': entity['content'][:200] if entity.get('content') else ''})
        elif src_table == 'claims':
            claim = kb.get_claim(int(src_id))
            if claim:
                result.update({'id': claim['id'], 'claim_text': claim['claim_text'],
                               'evidence_grade': claim.get('evidence_grade'), 'confidence': claim.get('confidence')})
        results.append(result)
    return results
