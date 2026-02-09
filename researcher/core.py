#!/usr/bin/env python3
"""
Minimal Knowledge Base with automatic management.
Agents just add entities, links, and tasks - system manages the rest.
"""

import sqlite3
import json
import uuid
import random
import re
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

class KnowledgeBase:
    """Minimal KB with entities, links, and task backlog."""
    
    def __init__(self, db_path: str = "knowledge-base/kb.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        # Enable WAL for concurrent read+write and faster writes
        self.conn.execute("PRAGMA journal_mode=WAL")
        # Enforce foreign key constraints (CASCADE, SET NULL)
        self.conn.execute("PRAGMA foreign_keys=ON")
        # Balanced durability — safe with WAL
        self.conn.execute("PRAGMA synchronous=NORMAL")
        # Load sqlite-vec extension if available
        self._vec_available = False
        try:
            import sqlite_vec
            sqlite_vec.load(self.conn)
            self._vec_available = True
        except (ImportError, Exception):
            pass
        self._embedding_model = None
        self._init_tables()
    
    def _init_tables(self):
        """Create tables if they don't exist."""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS entities (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT,
                metadata TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_id TEXT NOT NULL,
                to_id TEXT NOT NULL,
                link_type TEXT DEFAULT 'related',
                created_at TEXT NOT NULL,
                FOREIGN KEY(from_id) REFERENCES entities(id) ON DELETE CASCADE,
                FOREIGN KEY(to_id) REFERENCES entities(id) ON DELETE CASCADE,
                UNIQUE(from_id, to_id, link_type)
            );
            
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'pending',
                entity_id TEXT,
                metadata TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(entity_id) REFERENCES entities(id) ON DELETE SET NULL
            );
            
            CREATE INDEX IF NOT EXISTS idx_links_from ON links(from_id);
            CREATE INDEX IF NOT EXISTS idx_links_to ON links(to_id);
            CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
            CREATE INDEX IF NOT EXISTS idx_tasks_entity ON tasks(entity_id);
            
            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_id TEXT NOT NULL,
                iteration INTEGER DEFAULT 1,
                max_iterations INTEGER DEFAULT 5,
                status TEXT DEFAULT 'evaluating',
                confidence REAL DEFAULT 0.0,
                gaps TEXT DEFAULT '[]',
                contradictions TEXT DEFAULT '[]',
                convergence_criteria TEXT DEFAULT '{}',
                confidence_history TEXT DEFAULT '[]',
                gap_thompson_params TEXT DEFAULT '{}',
                decision TEXT,
                rationale TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(parent_id) REFERENCES entities(id) ON DELETE CASCADE
            );
            
            CREATE INDEX IF NOT EXISTS idx_evaluations_parent ON evaluations(parent_id);
            CREATE INDEX IF NOT EXISTS idx_evaluations_status ON evaluations(status);
            
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                title TEXT,
                domain TEXT,
                snippet TEXT,
                credibility REAL DEFAULT 0.5,
                source_type TEXT DEFAULT 'web',
                accessed_at TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                UNIQUE(url)
            );
            
            CREATE TABLE IF NOT EXISTS claims (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                claim_text TEXT NOT NULL,
                entity_id TEXT,
                evidence_grade TEXT DEFAULT 'ungraded',
                confidence REAL DEFAULT 0.5,
                status TEXT DEFAULT 'active',
                metadata TEXT DEFAULT '{}',
                created_at TEXT NOT NULL,
                FOREIGN KEY(entity_id) REFERENCES entities(id) ON DELETE SET NULL
            );
            
            CREATE TABLE IF NOT EXISTS claim_sources (
                claim_id INTEGER NOT NULL,
                source_id INTEGER NOT NULL,
                relationship TEXT DEFAULT 'supports',
                PRIMARY KEY(claim_id, source_id),
                FOREIGN KEY(claim_id) REFERENCES claims(id) ON DELETE CASCADE,
                FOREIGN KEY(source_id) REFERENCES sources(id) ON DELETE CASCADE
            );
            
            CREATE INDEX IF NOT EXISTS idx_sources_domain ON sources(domain);
            CREATE INDEX IF NOT EXISTS idx_sources_credibility ON sources(credibility);
            CREATE INDEX IF NOT EXISTS idx_claims_entity ON claims(entity_id);
            CREATE INDEX IF NOT EXISTS idx_claims_status ON claims(status);
            CREATE INDEX IF NOT EXISTS idx_claims_grade ON claims(evidence_grade);
            
            CREATE TABLE IF NOT EXISTS traces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id TEXT,
                step_num INTEGER DEFAULT 1,
                action TEXT NOT NULL,
                input TEXT,
                output TEXT,
                reasoning TEXT,
                tool_used TEXT,
                duration_ms INTEGER,
                created_at TEXT NOT NULL,
                FOREIGN KEY(entity_id) REFERENCES entities(id) ON DELETE CASCADE
            );
            
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id TEXT,
                title TEXT NOT NULL,
                criteria TEXT DEFAULT '[]',
                alternatives TEXT DEFAULT '[]',
                scores TEXT DEFAULT '{}',
                weights TEXT DEFAULT '{}',
                recommendation TEXT,
                rationale TEXT,
                status TEXT DEFAULT 'draft',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(entity_id) REFERENCES entities(id) ON DELETE SET NULL
            );
            
            CREATE INDEX IF NOT EXISTS idx_traces_entity ON traces(entity_id);
            CREATE INDEX IF NOT EXISTS idx_decisions_entity ON decisions(entity_id);
            CREATE INDEX IF NOT EXISTS idx_decisions_status ON decisions(status);
        """)
        # FTS5 virtual table for full-text search with porter stemming
        self.conn.executescript("""
            CREATE VIRTUAL TABLE IF NOT EXISTS entities_fts USING fts5(
                title, content, entity_id UNINDEXED,
                tokenize='porter unicode61'
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS claims_fts USING fts5(
                claim_text, claim_id UNINDEXED,
                tokenize='porter unicode61'
            );
        """)
        # sqlite-vec tables (only if extension loaded)
        if self._vec_available:
            try:
                self.conn.execute("SELECT rowid FROM vec_embeddings LIMIT 0")
            except sqlite3.OperationalError:
                self.conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS vec_embeddings USING vec0(embedding float[384])")
            self.conn.executescript("""
                CREATE TABLE IF NOT EXISTS embedding_map (
                    vec_rowid INTEGER PRIMARY KEY,
                    source_table TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    text_hash TEXT,
                    embedded_at TEXT NOT NULL,
                    UNIQUE(source_table, source_id)
                );
                CREATE INDEX IF NOT EXISTS idx_embedding_map_source
                    ON embedding_map(source_table, source_id);
            """)
        self.conn.commit()
        # Populate FTS indexes from existing data if empty
        self._sync_fts_indexes()

    # ── Helper abstractions ─────────────────────────────────────────────

    def _now(self):
        """Timestamp helper — single source for UTC ISO timestamps."""
        return datetime.utcnow().isoformat()

    def _require_entity(self, entity_id):
        """Guard helper — returns entity dict or None."""
        return self.get_entity(entity_id)

    def _walk_tree(self, root_id, visitor_fn):
        """Generic BFS tree walker over child/wave/spawned links.
        Calls visitor_fn(entity_id, depth) at each node. Returns collected results."""
        results = []
        visited = {root_id}
        queue = [(root_id, 0)]
        while queue:
            current, depth = queue.pop(0)
            result = visitor_fn(current, depth)
            if result is not None:
                results.append(result)
            children = self.conn.execute(
                "SELECT to_id FROM links WHERE from_id = ? AND link_type IN ('child', 'wave', 'spawned')",
                (current,)
            ).fetchall()
            for row in children:
                child_id = row['to_id']
                if child_id not in visited:
                    visited.add(child_id)
                    queue.append((child_id, depth + 1))
        return results

    def _fts_query(self, table, query, limit=20):
        """Unified FTS search with LIKE fallback.
        table: 'entities' or 'claims'. Returns list of sqlite3.Row."""
        if table == 'entities':
            try:
                return self.conn.execute("""
                    SELECT e.* FROM entities e
                    JOIN entities_fts f ON f.entity_id = e.id
                    WHERE entities_fts MATCH ?
                    ORDER BY rank LIMIT ?
                """, (query, limit)).fetchall()
            except sqlite3.OperationalError:
                search_term = f"%{query}%"
                return self.conn.execute("""
                    SELECT * FROM entities
                    WHERE title LIKE ? OR content LIKE ?
                    ORDER BY created_at DESC LIMIT ?
                """, (search_term, search_term, limit)).fetchall()
        elif table == 'claims':
            try:
                return self.conn.execute("""
                    SELECT c.* FROM claims c
                    JOIN claims_fts f ON CAST(f.claim_id AS INTEGER) = c.id
                    WHERE claims_fts MATCH ?
                    ORDER BY rank LIMIT ?
                """, (query, limit)).fetchall()
            except sqlite3.OperationalError:
                search_term = f"%{query}%"
                return self.conn.execute("""
                    SELECT * FROM claims
                    WHERE claim_text LIKE ?
                    ORDER BY created_at DESC LIMIT ?
                """, (search_term, limit)).fetchall()
        return []

    def _entity_claims_children(self, entity_id):
        """Common preamble: get entity, claims, and children in one call.
        Returns (entity, claims, children) or (None, [], [])."""
        entity = self.get_entity(entity_id)
        if not entity:
            return None, [], []
        claims = self.list_claims(entity_id=entity_id)
        children = self.get_links_from(entity_id)
        return entity, claims, children

    def _sync_fts_indexes(self):
        """Rebuild FTS indexes from existing data if they're empty."""
        fts_count = self.conn.execute("SELECT COUNT(*) FROM entities_fts").fetchone()[0]
        entity_count = self.conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
        if entity_count > 0 and fts_count == 0:
            rows = self.conn.execute("SELECT id, title, content FROM entities").fetchall()
            for r in rows:
                self.conn.execute(
                    "INSERT INTO entities_fts (title, content, entity_id) VALUES (?, ?, ?)",
                    (r['title'], r['content'], r['id'])
                )
        fts_count = self.conn.execute("SELECT COUNT(*) FROM claims_fts").fetchone()[0]
        claim_count = self.conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
        if claim_count > 0 and fts_count == 0:
            rows = self.conn.execute("SELECT id, claim_text FROM claims").fetchall()
            for r in rows:
                self.conn.execute(
                    "INSERT INTO claims_fts (claim_text, claim_id) VALUES (?, ?)",
                    (r['claim_text'], str(r['id']))
                )
        self.conn.commit()
    
    def add_entity(
        self, 
        title: str, 
        content: str = "", 
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add an entity (research note). Returns entity ID."""
        entity_id = str(uuid.uuid4())[:12]
        now = self._now()
        meta_json = json.dumps(metadata or {})
        
        self.conn.execute(
            "INSERT INTO entities (id, title, content, metadata, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (entity_id, title, content, meta_json, now, now)
        )
        # Update FTS index
        self.conn.execute(
            "INSERT INTO entities_fts (title, content, entity_id) VALUES (?, ?, ?)",
            (title, content, entity_id)
        )
        self.conn.commit()
        return entity_id
    
    def update_entity(
        self, 
        entity_id: str, 
        title: Optional[str] = None,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Update an existing entity."""
        updates = []
        params = []
        
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        if content is not None:
            updates.append("content = ?")
            params.append(content)
        if metadata is not None:
            updates.append("metadata = ?")
            params.append(json.dumps(metadata))
        
        if updates:
            updates.append("updated_at = ?")
            params.append(self._now())
            params.append(entity_id)
            
            query = f"UPDATE entities SET {', '.join(updates)} WHERE id = ?"
            self.conn.execute(query, params)
            # Update FTS index
            if title is not None or content is not None:
                entity = self.get_entity(entity_id)
                if entity:
                    self.conn.execute(
                        "DELETE FROM entities_fts WHERE entity_id = ?", (entity_id,)
                    )
                    self.conn.execute(
                        "INSERT INTO entities_fts (title, content, entity_id) VALUES (?, ?, ?)",
                        (entity['title'], entity['content'], entity_id)
                    )
            self.conn.commit()
    
    def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get an entity by ID."""
        row = self.conn.execute(
            "SELECT * FROM entities WHERE id = ?", (entity_id,)
        ).fetchone()
        
        if row:
            return {
                'id': row['id'],
                'title': row['title'],
                'content': row['content'],
                'metadata': json.loads(row['metadata']),
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            }
        return None
    
    def add_link(
        self, 
        from_id: str, 
        to_id: str, 
        link_type: str = "related"
    ) -> Optional[int]:
        """Add a link between entities. Returns link ID or None if already exists."""
        try:
            cursor = self.conn.execute(
                "INSERT INTO links (from_id, to_id, link_type, created_at) "
                "VALUES (?, ?, ?, ?)",
                (from_id, to_id, link_type, self._now())
            )
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Link already exists
            return None
    
    def get_links_from(self, entity_id: str) -> List[Dict[str, Any]]:
        """Get all entities linked FROM this entity."""
        rows = self.conn.execute("""
            SELECT e.*, l.link_type
            FROM entities e
            JOIN links l ON e.id = l.to_id
            WHERE l.from_id = ?
        """, (entity_id,)).fetchall()
        
        return [
            {
                'id': row['id'],
                'title': row['title'],
                'content': row['content'],
                'metadata': json.loads(row['metadata']),
                'link_type': row['link_type']
            }
            for row in rows
        ]
    
    def get_links_to(self, entity_id: str) -> List[Dict[str, Any]]:
        """Get all entities that link TO this entity."""
        rows = self.conn.execute("""
            SELECT e.*, l.link_type
            FROM entities e
            JOIN links l ON e.id = l.from_id
            WHERE l.to_id = ?
        """, (entity_id,)).fetchall()
        
        return [
            {
                'id': row['id'],
                'title': row['title'],
                'content': row['content'],
                'metadata': json.loads(row['metadata']),
                'link_type': row['link_type']
            }
            for row in rows
        ]
    
    def add_task(
        self,
        title: str,
        description: str = "",
        entity_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """Add a task to the backlog. Returns task ID."""
        now = self._now()
        meta_json = json.dumps(metadata or {})
        
        cursor = self.conn.execute(
            "INSERT INTO tasks (title, description, entity_id, metadata, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (title, description, entity_id, meta_json, now, now)
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def update_task_status(self, task_id: int, status: str):
        """Update task status (pending, in_progress, completed, cancelled)."""
        self.conn.execute(
            "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?",
            (status, self._now(), task_id)
        )
        self.conn.commit()
    
    def get_tasks(
        self, 
        status: Optional[str] = None,
        entity_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get tasks, optionally filtered by status and/or entity."""
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        if entity_id:
            query += " AND entity_id = ?"
            params.append(entity_id)
        
        query += " ORDER BY created_at DESC"
        
        rows = self.conn.execute(query, params).fetchall()
        return [
            {
                'id': row['id'],
                'title': row['title'],
                'description': row['description'],
                'status': row['status'],
                'entity_id': row['entity_id'],
                'metadata': json.loads(row['metadata']),
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            }
            for row in rows
        ]
    
    def search_entities(self, query: str) -> List[Dict[str, Any]]:
        """Full-text search across entity titles and content using FTS5."""
        try:
            rows = self.conn.execute("""
                SELECT e.* FROM entities e
                JOIN entities_fts f ON f.entity_id = e.id
                WHERE entities_fts MATCH ?
                ORDER BY rank
            """, (query,)).fetchall()
        except sqlite3.OperationalError:
            # Fallback to LIKE if FTS fails (special chars, etc.)
            search_term = f"%{query}%"
            rows = self.conn.execute("""
                SELECT * FROM entities 
                WHERE title LIKE ? OR content LIKE ?
                ORDER BY created_at DESC
            """, (search_term, search_term)).fetchall()
        
        return [
            {
                'id': row['id'],
                'title': row['title'],
                'content': row['content'][:200] + '...' if len(row['content']) > 200 else row['content'],
                'metadata': json.loads(row['metadata'])
            }
            for row in rows
        ]
    
    def list_entities(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """List all entities, optionally limited."""
        query = "SELECT * FROM entities ORDER BY created_at DESC"
        if limit:
            query += f" LIMIT {limit}"
        
        rows = self.conn.execute(query).fetchall()
        return [
            {
                'id': row['id'],
                'title': row['title'],
                'content': row['content'][:100] + '...' if len(row['content']) > 100 else row['content'],
                'metadata': json.loads(row['metadata']),
                'created_at': row['created_at']
            }
            for row in rows
        ]
    
    def get_stats(self) -> Dict[str, int]:
        """Get knowledge base statistics."""
        entity_count = self.conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
        link_count = self.conn.execute("SELECT COUNT(*) FROM links").fetchone()[0]
        task_count = self.conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        pending_tasks = self.conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE status = 'pending'"
        ).fetchone()[0]
        completed_tasks = self.conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE status = 'completed'"
        ).fetchone()[0]
        source_count = self.conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
        claim_count = self.conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
        strong_claims = self.conn.execute(
            "SELECT COUNT(*) FROM claims WHERE evidence_grade = 'strong'"
        ).fetchone()[0]
        contested_claims = self.conn.execute(
            "SELECT COUNT(*) FROM claims WHERE evidence_grade = 'contested'"
        ).fetchone()[0]
        trace_count = self.conn.execute("SELECT COUNT(*) FROM traces").fetchone()[0]
        decision_count = self.conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
        
        return {
            'entities': entity_count,
            'links': link_count,
            'tasks': task_count,
            'pending_tasks': pending_tasks,
            'completed_tasks': completed_tasks,
            'sources': source_count,
            'claims': claim_count,
            'strong_claims': strong_claims,
            'contested_claims': contested_claims,
            'traces': trace_count,
            'decisions': decision_count
        }
    
    def add_evaluation(
        self,
        parent_id: str,
        max_iterations: int = 5,
        convergence_criteria: Optional[Dict[str, Any]] = None
    ) -> int:
        """Add an evaluation loop tracker for a plan/swarm/pipeline. Returns eval ID."""
        now = self._now()
        default_criteria = {
            "min_confidence": 0.7,
            "max_gaps": 2,
            "max_contradictions": 0,
            "marginal_gain_threshold": 0.02,
            "marginal_gain_patience": 2
        }
        if convergence_criteria:
            default_criteria.update(convergence_criteria)
        criteria = json.dumps(default_criteria)
        cursor = self.conn.execute(
            "INSERT INTO evaluations (parent_id, max_iterations, convergence_criteria, "
            "confidence_history, gap_thompson_params, created_at, updated_at) "
            "VALUES (?, ?, ?, '[]', '{}', ?, ?)",
            (parent_id, max_iterations, criteria, now, now)
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def get_evaluation(self, eval_id: int) -> Optional[Dict[str, Any]]:
        """Get an evaluation by ID."""
        row = self.conn.execute(
            "SELECT * FROM evaluations WHERE id = ?", (eval_id,)
        ).fetchone()
        if row:
            return {
                'id': row['id'],
                'parent_id': row['parent_id'],
                'iteration': row['iteration'],
                'max_iterations': row['max_iterations'],
                'status': row['status'],
                'confidence': row['confidence'],
                'gaps': json.loads(row['gaps']),
                'contradictions': json.loads(row['contradictions']),
                'convergence_criteria': json.loads(row['convergence_criteria']),
                'confidence_history': json.loads(row['confidence_history'] or '[]'),
                'gap_thompson_params': json.loads(row['gap_thompson_params'] or '{}'),
                'decision': row['decision'],
                'rationale': row['rationale'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            }
        return None
    
    def get_evaluations_for(self, parent_id: str) -> List[Dict[str, Any]]:
        """Get all evaluations for a parent entity."""
        rows = self.conn.execute(
            "SELECT * FROM evaluations WHERE parent_id = ? ORDER BY iteration DESC",
            (parent_id,)
        ).fetchall()
        return [
            {
                'id': row['id'],
                'parent_id': row['parent_id'],
                'iteration': row['iteration'],
                'status': row['status'],
                'confidence': row['confidence'],
                'gaps': json.loads(row['gaps']),
                'contradictions': json.loads(row['contradictions']),
                'decision': row['decision'],
                'rationale': row['rationale']
            }
            for row in rows
        ]
    
    def update_evaluation(
        self,
        eval_id: int,
        confidence: Optional[float] = None,
        gaps: Optional[List[str]] = None,
        contradictions: Optional[List[str]] = None,
        decision: Optional[str] = None,
        rationale: Optional[str] = None,
        status: Optional[str] = None,
        iteration: Optional[int] = None,
        gap_results: Optional[Dict[str, float]] = None
    ):
        """Update an evaluation. Tracks confidence history for marginal-gain stopping.
        
        Args:
            gap_results: Optional dict mapping gap topic -> confidence_delta achieved.
                         Used to update Thompson sampling params for each gap.
        """
        updates = []
        params = []
        
        # Track confidence history for marginal-gain stopping
        if confidence is not None:
            updates.append("confidence = ?")
            params.append(confidence)
            # Append to confidence_history
            ev = self.get_evaluation(eval_id)
            if ev:
                history = ev.get('confidence_history', [])
                history.append({
                    'iteration': ev['iteration'],
                    'confidence': confidence,
                    'delta': confidence - (history[-1]['confidence'] if history else 0.0)
                })
                updates.append("confidence_history = ?")
                params.append(json.dumps(history))
        if gaps is not None:
            updates.append("gaps = ?")
            params.append(json.dumps(gaps))
        if contradictions is not None:
            updates.append("contradictions = ?")
            params.append(json.dumps(contradictions))
        if decision is not None:
            updates.append("decision = ?")
            params.append(decision)
        if rationale is not None:
            updates.append("rationale = ?")
            params.append(rationale)
        if status is not None:
            updates.append("status = ?")
            params.append(status)
        if iteration is not None:
            updates.append("iteration = ?")
            params.append(iteration)
        
        # Update Thompson sampling parameters for gap topics
        if gap_results is not None:
            ev = ev if (confidence is not None and ev) else self.get_evaluation(eval_id)
            if ev:
                thompson = ev.get('gap_thompson_params', {})
                for topic, delta in gap_results.items():
                    if topic not in thompson:
                        thompson[topic] = {'alpha': 1.0, 'beta': 1.0, 'attempts': 0, 'total_gain': 0.0}
                    thompson[topic]['attempts'] += 1
                    thompson[topic]['total_gain'] += delta
                    # Treat delta > threshold as "success", else "failure"
                    threshold = ev['convergence_criteria'].get('marginal_gain_threshold', 0.02)
                    if delta >= threshold:
                        thompson[topic]['alpha'] += 1.0
                    else:
                        thompson[topic]['beta'] += 1.0
                updates.append("gap_thompson_params = ?")
                params.append(json.dumps(thompson))
        
        if updates:
            updates.append("updated_at = ?")
            params.append(self._now())
            params.append(eval_id)
            query = f"UPDATE evaluations SET {', '.join(updates)} WHERE id = ?"
            self.conn.execute(query, params)
            self.conn.commit()
    
    def check_convergence(self, eval_id: int) -> Dict[str, Any]:
        """Check if evaluation meets convergence criteria. Returns verdict.
        
        Includes marginal-gain stopping: stops early when confidence delta
        plateaus below threshold for `patience` consecutive iterations.
        """
        ev = self.get_evaluation(eval_id)
        if not ev:
            return {"converged": False, "reason": "evaluation not found"}
        
        criteria = ev['convergence_criteria']
        min_conf = criteria.get('min_confidence', 0.7)
        max_gaps = criteria.get('max_gaps', 2)
        max_contradictions = criteria.get('max_contradictions', 0)
        mg_threshold = criteria.get('marginal_gain_threshold', 0.02)
        mg_patience = criteria.get('marginal_gain_patience', 2)
        
        # Hard stop: max iterations
        if ev['iteration'] >= ev['max_iterations']:
            return {"converged": True, "reason": "max_iterations_reached", "forced": True}
        
        # Marginal-gain stopping: check if recent deltas are all below threshold
        history = ev.get('confidence_history', [])
        marginal_gain_stop = False
        if len(history) >= mg_patience:
            recent_deltas = [h['delta'] for h in history[-mg_patience:]]
            if all(abs(d) < mg_threshold for d in recent_deltas):
                marginal_gain_stop = True
        
        # Standard criteria
        gaps_ok = len(ev['gaps']) <= max_gaps
        contradictions_ok = len(ev['contradictions']) <= max_contradictions
        confidence_ok = ev['confidence'] >= min_conf
        
        converged = gaps_ok and contradictions_ok and confidence_ok
        reasons = []
        if not confidence_ok:
            reasons.append(f"confidence {ev['confidence']:.2f} < {min_conf}")
        if not gaps_ok:
            reasons.append(f"gaps {len(ev['gaps'])} > {max_gaps}")
        if not contradictions_ok:
            reasons.append(f"contradictions {len(ev['contradictions'])} > {max_contradictions}")
        
        # Early stop on marginal gain plateau (even if not all criteria met)
        if marginal_gain_stop and not converged:
            recent_deltas = [h['delta'] for h in history[-mg_patience:]]
            return {
                "converged": True,
                "reason": f"marginal_gain_plateau: last {mg_patience} deltas {recent_deltas} all < {mg_threshold}",
                "forced": True,
                "marginal_gain_stop": True,
                "confidence": ev['confidence'],
                "gaps": ev['gaps'],
                "contradictions": ev['contradictions'],
                "iteration": ev['iteration'],
                "max_iterations": ev['max_iterations'],
                "confidence_history": history
            }
        
        return {
            "converged": converged,
            "reason": "all criteria met" if converged else "; ".join(reasons),
            "confidence": ev['confidence'],
            "gaps": ev['gaps'],
            "contradictions": ev['contradictions'],
            "iteration": ev['iteration'],
            "max_iterations": ev['max_iterations'],
            "confidence_history": history,
            "marginal_gain_stop": False
        }
    
    def select_next_gaps(
        self,
        eval_id: int,
        n: int = 3,
        exploration_bonus: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Select which gaps to investigate next using Thompson sampling.
        
        Uses Beta(α,β) posterior sampling to balance exploration (under-investigated
        gaps with high uncertainty) vs exploitation (gaps that have historically
        yielded the highest confidence gains).
        
        Args:
            eval_id: Evaluation ID to select gaps for.
            n: Number of gaps to select (top-n by Thompson sample).
            exploration_bonus: Added to β prior to increase exploration (0.0 = neutral).
        
        Returns:
            List of dicts with 'topic', 'thompson_score', 'alpha', 'beta', 'attempts'.
            Ordered by descending Thompson sample score.
        """
        ev = self.get_evaluation(eval_id)
        if not ev:
            return []
        
        gaps = ev.get('gaps', [])
        if not gaps:
            return []
        
        thompson = ev.get('gap_thompson_params', {})
        scored_gaps = []
        
        for topic in gaps:
            params = thompson.get(topic, {'alpha': 1.0, 'beta': 1.0, 'attempts': 0, 'total_gain': 0.0})
            alpha = params['alpha']
            beta_param = params['beta'] + exploration_bonus
            # Thompson sample: draw from Beta(α, β) posterior
            score = random.betavariate(max(alpha, 0.01), max(beta_param, 0.01))
            scored_gaps.append({
                'topic': topic,
                'thompson_score': round(score, 4),
                'alpha': alpha,
                'beta': params['beta'],
                'attempts': params['attempts'],
                'total_gain': params.get('total_gain', 0.0),
                'expected_value': round(alpha / (alpha + params['beta']), 4)
            })
        
        # Sort by Thompson sample (stochastic ranking)
        scored_gaps.sort(key=lambda x: x['thompson_score'], reverse=True)
        return scored_gaps[:n]
    
    def register_gap_topics(self, eval_id: int, topics: List[str]):
        """Initialize Thompson sampling priors for a set of gap topics.
        
        Call this when gaps are first identified to set up Beta(1,1) uniform priors.
        Existing topics are not overwritten.
        """
        ev = self.get_evaluation(eval_id)
        if not ev:
            return
        thompson = ev.get('gap_thompson_params', {})
        for topic in topics:
            if topic not in thompson:
                thompson[topic] = {'alpha': 1.0, 'beta': 1.0, 'attempts': 0, 'total_gain': 0.0}
        self.conn.execute(
            "UPDATE evaluations SET gap_thompson_params = ?, updated_at = ? WHERE id = ?",
            (json.dumps(thompson), self._now(), eval_id)
        )
        self.conn.commit()
    
    # ── Domain credibility heuristics ──────────────────────────────────

    DOMAIN_CREDIBILITY = {
        # Tier 1: Primary academic / institutional (0.9-1.0)
        'nature.com': 0.95, 'science.org': 0.95, 'sciencedirect.com': 0.93,
        'arxiv.org': 0.88, 'pubmed.ncbi.nlm.nih.gov': 0.92, 'nih.gov': 0.92,
        'ieee.org': 0.90, 'acm.org': 0.90, 'springer.com': 0.88,
        'wiley.com': 0.88, 'pnas.org': 0.93, 'cell.com': 0.93,
        'iopscience.iop.org': 0.90, 'academic.oup.com': 0.90,
        'nationalmaglab.org': 0.88, 'link.springer.com': 0.88,
        'physicsworld.com': 0.80, 'scitechdaily.com': 0.65,
        'gov': 0.85, 'edu': 0.82,
        # Tier 2: Quality journalism / encyclopedic (0.7-0.85)
        'reuters.com': 0.82, 'apnews.com': 0.82, 'bbc.com': 0.78,
        'nytimes.com': 0.78, 'theguardian.com': 0.75, 'economist.com': 0.80,
        'wikipedia.org': 0.72, 'britannica.com': 0.78,
        'technologyreview.com': 0.78, 'ans.org': 0.80,
        'home.cern': 0.92, 'cern.ch': 0.92, 'indico.cern.ch': 0.90,
        # Tier 3: Tech / industry (0.6-0.75)
        'github.com': 0.70, 'stackoverflow.com': 0.68,
        'arstechnica.com': 0.72, 'wired.com': 0.68,
        'cfs.energy': 0.72, 'iter.org': 0.82,
        # Tier 4: Blogs / unknown (0.3-0.5)
        'medium.com': 0.45, 'substack.com': 0.45,
        'reddit.com': 0.35, 'quora.com': 0.35,
    }

    # Delegated constants (defined in extracted modules)
    from researcher.kb_router import COORDINATOR_PROFILES
    from researcher.kb_domains import DOMAIN_PROFILES

    def _score_domain(self, url: str) -> float:
        """Score a URL's domain credibility. Returns 0.0-1.0."""
        from urllib.parse import urlparse
        try:
            domain = urlparse(url).netloc.lower().replace('www.', '')
        except Exception:
            return 0.4
        # Exact match
        if domain in self.DOMAIN_CREDIBILITY:
            return self.DOMAIN_CREDIBILITY[domain]
        # TLD match (.gov, .edu)
        tld = domain.split('.')[-1]
        if tld in self.DOMAIN_CREDIBILITY:
            return self.DOMAIN_CREDIBILITY[tld]
        # Partial match (e.g., 'something.nature.com')
        for known, score in self.DOMAIN_CREDIBILITY.items():
            if domain.endswith('.' + known):
                return score
        return 0.5  # Unknown domain default

    # ── Source management ───────────────────────────────────────────────

    def add_source(
        self,
        url: str,
        title: str = "",
        snippet: str = "",
        source_type: str = "web",
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """Add a source. Auto-scores domain credibility. Returns source ID."""
        from urllib.parse import urlparse
        try:
            domain = urlparse(url).netloc.lower().replace('www.', '')
        except Exception:
            domain = "unknown"
        
        credibility = self._score_domain(url)
        now = self._now()
        meta_json = json.dumps(metadata or {})
        
        try:
            cursor = self.conn.execute(
                "INSERT INTO sources (url, title, domain, snippet, credibility, source_type, accessed_at, metadata) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (url, title, domain, snippet, credibility, source_type, now, meta_json)
            )
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # URL already exists — update and return existing
            row = self.conn.execute("SELECT id FROM sources WHERE url = ?", (url,)).fetchone()
            if title:
                self.conn.execute("UPDATE sources SET title = ?, snippet = ?, accessed_at = ? WHERE url = ?",
                                  (title, snippet, now, url))
                self.conn.commit()
            return row['id']
    
    def get_source(self, source_id: int) -> Optional[Dict[str, Any]]:
        """Get a source by ID."""
        row = self.conn.execute("SELECT * FROM sources WHERE id = ?", (source_id,)).fetchone()
        if row:
            return {k: row[k] for k in row.keys()}
        return None
    
    def list_sources(self, entity_id: Optional[str] = None, min_credibility: float = 0.0) -> List[Dict[str, Any]]:
        """List sources, optionally filtered by entity (via claims) and minimum credibility."""
        if entity_id:
            rows = self.conn.execute("""
                SELECT DISTINCT s.* FROM sources s
                JOIN claim_sources cs ON s.id = cs.source_id
                JOIN claims c ON cs.claim_id = c.id
                WHERE c.entity_id = ? AND s.credibility >= ?
                ORDER BY s.credibility DESC
            """, (entity_id, min_credibility)).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM sources WHERE credibility >= ? ORDER BY credibility DESC",
                (min_credibility,)
            ).fetchall()
        return [{k: row[k] for k in row.keys()} for row in rows]

    # ── Claim management ────────────────────────────────────────────────

    EVIDENCE_GRADES = {
        'strong':     {'min_sources': 3, 'min_avg_credibility': 0.7, 'confidence': 0.9},
        'moderate':   {'min_sources': 2, 'min_avg_credibility': 0.5, 'confidence': 0.7},
        'weak':       {'min_sources': 1, 'min_avg_credibility': 0.3, 'confidence': 0.4},
        'ungraded':   {'min_sources': 0, 'min_avg_credibility': 0.0, 'confidence': 0.3},
        'contested':  {'min_sources': 0, 'min_avg_credibility': 0.0, 'confidence': 0.2},
    }

    def add_claim(
        self,
        claim_text: str,
        entity_id: Optional[str] = None,
        source_ids: Optional[List[int]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """Add a claim. Optionally link to sources. Auto-grades evidence. Returns claim ID."""
        now = self._now()
        meta_json = json.dumps(metadata or {})
        
        cursor = self.conn.execute(
            "INSERT INTO claims (claim_text, entity_id, metadata, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (claim_text, entity_id, meta_json, now, now)
        )
        claim_id = cursor.lastrowid
        
        # Update FTS index
        self.conn.execute(
            "INSERT INTO claims_fts (claim_text, claim_id) VALUES (?, ?)",
            (claim_text, str(claim_id))
        )
        
        # Link sources
        if source_ids:
            for sid in source_ids:
                try:
                    self.conn.execute(
                        "INSERT INTO claim_sources (claim_id, source_id) VALUES (?, ?)",
                        (claim_id, sid)
                    )
                except sqlite3.IntegrityError:
                    pass
        
        self.conn.commit()
        # Auto-grade
        self._grade_claim(claim_id)
        return claim_id
    
    def add_claim_source(self, claim_id: int, source_id: int, relationship: str = "supports") -> bool:
        """Link a source to a claim. Re-grades the claim. Returns success."""
        try:
            self.conn.execute(
                "INSERT INTO claim_sources (claim_id, source_id, relationship) VALUES (?, ?, ?)",
                (claim_id, source_id, relationship)
            )
            self.conn.commit()
            self._grade_claim(claim_id)
            return True
        except sqlite3.IntegrityError:
            return False
    
    def _grade_claim(self, claim_id: int):
        """Auto-grade a claim based on its linked sources."""
        rows = self.conn.execute("""
            SELECT s.credibility, cs.relationship FROM sources s
            JOIN claim_sources cs ON s.id = cs.source_id
            WHERE cs.claim_id = ?
        """, (claim_id,)).fetchall()
        
        supporting = [r['credibility'] for r in rows if r['relationship'] in ('supports', 'confirms')]
        contradicting = [r['credibility'] for r in rows if r['relationship'] in ('contradicts', 'refutes')]
        
        n_support = len(supporting)
        n_contradict = len(contradicting)
        
        if n_contradict > 0 and n_support > 0:
            grade = 'contested'
            confidence = 0.2 + (0.3 * (n_support / (n_support + n_contradict)))
        elif n_support == 0:
            grade = 'ungraded'
            confidence = 0.3
        else:
            avg_cred = sum(supporting) / n_support
            if n_support >= 3 and avg_cred >= 0.7:
                grade = 'strong'
                confidence = min(0.95, 0.7 + (n_support * 0.05) + (avg_cred * 0.1))
            elif n_support >= 2 and avg_cred >= 0.5:
                grade = 'moderate'
                confidence = 0.5 + (n_support * 0.05) + (avg_cred * 0.1)
            else:
                grade = 'weak'
                confidence = 0.3 + (avg_cred * 0.15)
        
        self.conn.execute(
            "UPDATE claims SET evidence_grade = ?, confidence = ?, updated_at = ? WHERE id = ?",
            (grade, round(confidence, 3), self._now(), claim_id)
        )
        self.conn.commit()
        # If this is an atomic child, re-grade the composite parent
        row = self.conn.execute("SELECT parent_claim_id FROM claims WHERE id = ?", (claim_id,)).fetchone()
        if row and row['parent_claim_id']:
            self._grade_composite_claim(row['parent_claim_id'])
    
    # ── Atomic Claim Decomposition ──────────────────────────────────────

    def _claim_complexity(self, text: str) -> Dict[str, Any]:
        """Score how complex a claim is. Higher = more likely to need decomposition."""
        words = text.split()
        conjunctions = len(re.findall(r'\b(and|also|additionally|furthermore|moreover)\b', text, re.I))
        semicolons = text.count(';')
        sentences = len(re.findall(r'[.!?]+\s', text)) + 1
        numerics = len(re.findall(r'\d+\.?\d*\s*(%|°|MW|GW|km|m\b|kg|ton|year|eV|keV|MeV)', text))
        relative_clauses = len(re.findall(r'\b(which|that|where|when|while|whereas)\b', text, re.I))

        score = (conjunctions * 1.0 + semicolons * 1.5 + relative_clauses * 0.8
                 + max(0, sentences - 1) * 1.2 + max(0, numerics - 1) * 0.7
                 + max(0, (len(words) - 25) / 20) * 0.5)

        return {
            'score': round(score, 2),
            'conjunctions': conjunctions,
            'semicolons': semicolons,
            'sentences': sentences,
            'numerics': numerics,
            'word_count': len(words),
            'needs_decomposition': score > 1.5
        }

    def _heuristic_decompose(self, text: str) -> List[str]:
        """Fast rule-based decomposition: split on semicolons and independent 'and' clauses."""
        parts = []
        # Split on semicolons first
        segments = re.split(r'\s*;\s*', text)
        for seg in segments:
            seg = seg.strip().rstrip('.')
            if not seg:
                continue
            # Split on 'and' connecting independent clauses (has subject+verb on both sides)
            and_parts = re.split(r',?\s+and\s+(?=[A-Z])', seg)
            if len(and_parts) > 1:
                parts.extend(p.strip().rstrip('.') for p in and_parts if p.strip())
            else:
                parts.append(seg)
        # Ensure each part is self-contained enough
        return [p for p in parts if len(p.split()) >= 3]

    def decompose_claim(self, claim_id: int, method: str = 'auto') -> List[int]:
        """Decompose a claim into atomic sub-claims.
        
        method: 'auto' (heuristic, complexity-gated), 'heuristic', or 'none'
        Returns list of atomic claim IDs. Empty if claim is already atomic/singleton.
        Idempotent: returns existing atomic IDs if already decomposed.
        """
        claim = self.get_claim(claim_id)
        if not claim:
            return []

        # Idempotency: if already decomposed, return existing atomic IDs
        existing = self.conn.execute(
            "SELECT id FROM claims WHERE parent_claim_id = ? AND is_atomic = 1", (claim_id,)
        ).fetchall()
        if existing:
            return [r['id'] for r in existing]

        text = claim['claim_text']
        complexity = self._claim_complexity(text)

        if method == 'none':
            self.conn.execute("UPDATE claims SET claim_type = 'singleton' WHERE id = ?", (claim_id,))
            self.conn.commit()
            return []

        if not complexity['needs_decomposition']:
            self.conn.execute("UPDATE claims SET claim_type = 'singleton' WHERE id = ?", (claim_id,))
            self.conn.commit()
            return []

        # Decompose
        parts = self._heuristic_decompose(text)
        if len(parts) <= 1:
            self.conn.execute("UPDATE claims SET claim_type = 'singleton' WHERE id = ?", (claim_id,))
            self.conn.commit()
            return []

        # Mark parent as composite
        self.conn.execute(
            "UPDATE claims SET claim_type = 'composite' WHERE id = ?", (claim_id,))

        # Create atomic children, inheriting parent's entity and sources
        atomic_ids = []
        now = self._now()
        parent_sources = self.conn.execute(
            "SELECT source_id, relationship FROM claim_sources WHERE claim_id = ?",
            (claim_id,)
        ).fetchall()

        for part in parts:
            cursor = self.conn.execute(
                "INSERT INTO claims (claim_text, entity_id, metadata, parent_claim_id, claim_type, is_atomic, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, 'atomic', 1, ?, ?)",
                (part, claim.get('entity_id'), json.dumps({'decomposed_from': claim_id}), claim_id, now, now)
            )
            atomic_id = cursor.lastrowid
            # Copy parent's source links to atomic child
            for src in parent_sources:
                try:
                    self.conn.execute(
                        "INSERT INTO claim_sources (claim_id, source_id, relationship) VALUES (?, ?, ?)",
                        (atomic_id, src['source_id'], src['relationship'])
                    )
                except sqlite3.IntegrityError:
                    pass
            # FTS
            self.conn.execute(
                "INSERT INTO claims_fts (claim_text, claim_id) VALUES (?, ?)",
                (part, str(atomic_id))
            )
            atomic_ids.append(atomic_id)

        self.conn.commit()
        # Grade each atomic child, then composite parent
        for aid in atomic_ids:
            self._grade_claim(aid)
        self._grade_composite_claim(claim_id)
        return atomic_ids

    def _grade_composite_claim(self, claim_id: int):
        """FActScore-style rollup: supported_atoms / total_atoms."""
        children = self.conn.execute(
            "SELECT id, evidence_grade, confidence FROM claims WHERE parent_claim_id = ? AND is_atomic = 1",
            (claim_id,)
        ).fetchall()
        if not children:
            return

        total = len(children)
        supported = sum(1 for c in children if c['evidence_grade'] in ('strong', 'moderate'))
        factscore = supported / total if total > 0 else 0
        avg_child_conf = sum(c['confidence'] for c in children) / total

        if factscore >= 0.9:
            grade = 'strong'
        elif factscore >= 0.6:
            grade = 'moderate'
        elif factscore >= 0.3:
            grade = 'weak'
        else:
            grade = 'contested'

        confidence = round(factscore * 0.6 + avg_child_conf * 0.4, 3)

        # Store factscore in metadata
        meta_row = self.conn.execute("SELECT metadata FROM claims WHERE id = ?", (claim_id,)).fetchone()
        meta = json.loads(meta_row['metadata'] or '{}') if meta_row else {}
        meta['factscore'] = round(factscore, 3)
        meta['atomic_count'] = total
        meta['supported_count'] = supported

        self.conn.execute(
            "UPDATE claims SET evidence_grade = ?, confidence = ?, metadata = ?, updated_at = ? WHERE id = ?",
            (grade, confidence, json.dumps(meta), self._now(), claim_id)
        )
        self.conn.commit()

    def get_atomic_claims(self, parent_claim_id: int) -> List[Dict[str, Any]]:
        """Get atomic sub-claims of a composite claim."""
        rows = self.conn.execute(
            "SELECT * FROM claims WHERE parent_claim_id = ? AND is_atomic = 1 ORDER BY id",
            (parent_claim_id,)
        ).fetchall()
        results = []
        for row in rows:
            c = {k: row[k] for k in row.keys()}
            c['metadata'] = json.loads(c['metadata'])
            results.append(c)
        return results
    
    def get_claim(self, claim_id: int) -> Optional[Dict[str, Any]]:
        """Get a claim with its sources."""
        row = self.conn.execute("SELECT * FROM claims WHERE id = ?", (claim_id,)).fetchone()
        if not row:
            return None
        claim = {k: row[k] for k in row.keys()}
        claim['metadata'] = json.loads(claim['metadata'])
        # Attach sources
        sources = self.conn.execute("""
            SELECT s.*, cs.relationship FROM sources s
            JOIN claim_sources cs ON s.id = cs.source_id
            WHERE cs.claim_id = ?
        """, (claim_id,)).fetchall()
        claim['sources'] = [{k: r[k] for k in r.keys()} for r in sources]
        return claim
    
    def list_claims(
        self,
        entity_id: Optional[str] = None,
        grade: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List claims with optional filters."""
        query = """
            SELECT c.*, COUNT(cs.source_id) as source_count
            FROM claims c
            LEFT JOIN claim_sources cs ON c.id = cs.claim_id
            WHERE 1=1
        """
        params = []
        if entity_id:
            query += " AND c.entity_id = ?"
            params.append(entity_id)
        if grade:
            query += " AND c.evidence_grade = ?"
            params.append(grade)
        if status:
            query += " AND c.status = ?"
            params.append(status)
        query += " GROUP BY c.id ORDER BY c.confidence DESC"
        
        rows = self.conn.execute(query, params).fetchall()
        results = []
        for row in rows:
            c = {k: row[k] for k in row.keys()}
            c['metadata'] = json.loads(c['metadata'])
            results.append(c)
        return results

    def verify_claim(self, claim_id: int, search_fn=None) -> Dict[str, Any]:
        """SAFE-style search-augmented claim verification."""
        from researcher.kb_verify import verify_claim
        return verify_claim(self, claim_id, search_fn)

    def _fts_safe(self, text: str) -> str:
        """Make text safe for FTS5 MATCH queries."""
        from researcher.kb_verify import _fts_safe
        return _fts_safe(text)

    def grade_claim_sc(self, claim_id: int, n_samples: int = 5) -> Dict[str, Any]:
        """Self-consistency sampling for claim grading."""
        from researcher.kb_verify import grade_claim_sc
        return grade_claim_sc(self, claim_id, n_samples)

    def extract_quotes(self, source_id: int) -> Dict[str, Any]:
        """FRONT pattern: Extract quotable snippets from a source."""
        from researcher.kb_verify import extract_quotes
        return extract_quotes(self, source_id)

    def claim_from_quote(self, quote_text: str, source_id: int,
                         entity_id: Optional[str] = None, claim_text: Optional[str] = None) -> Dict[str, Any]:
        """FRONT pattern: Create a grounded claim from a specific quote."""
        from researcher.kb_verify import claim_from_quote
        return claim_from_quote(self, quote_text, source_id, entity_id, claim_text)

    def check_contradictions(self, entity_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Find claims that are contradicted by sources."""
        from researcher.kb_analysis import check_contradictions
        return check_contradictions(self, entity_id)

    def check_corroboration(self, entity_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Score how well-corroborated each claim is."""
        from researcher.kb_analysis import check_corroboration
        return check_corroboration(self, entity_id)

    def apply_confidence_decay(self, days_threshold: int = 30, decay_rate: float = 0.02) -> List[Dict[str, Any]]:
        """Decay confidence on claims older than threshold."""
        from researcher.kb_analysis import apply_confidence_decay
        return apply_confidence_decay(self, days_threshold, decay_rate)

    def find_prior_research(self, query: str, min_confidence: float = 0.4) -> Dict[str, Any]:
        """Search existing KB for relevant prior entities and claims."""
        from researcher.kb_analysis import find_prior_research
        return find_prior_research(self, query, min_confidence)

    def generate_report(self, entity_id: str, include_children: bool = True) -> Optional[str]:
        """Generate a structured report with inline citations."""
        from researcher.kb_reports import generate_report
        return generate_report(self, entity_id, include_children)

    def _format_refs(self, source_ids: List[int], source_map: Dict) -> str:
        """Format citation references."""
        from researcher.kb_reports import _format_refs
        return _format_refs(source_ids, source_map)

    def add_trace(
        self,
        entity_id: str,
        action: str,
        input_text: str = "",
        output_text: str = "",
        reasoning: str = "",
        tool_used: str = "",
        duration_ms: int = 0
    ) -> int:
        """Log a reasoning trace step. Returns trace ID."""
        # Auto-increment step_num per entity
        row = self.conn.execute(
            "SELECT COALESCE(MAX(step_num), 0) FROM traces WHERE entity_id = ?",
            (entity_id,)
        ).fetchone()
        step_num = row[0] + 1
        
        now = self._now()
        cursor = self.conn.execute(
            "INSERT INTO traces (entity_id, step_num, action, input, output, reasoning, tool_used, duration_ms, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (entity_id, step_num, action, input_text, output_text, reasoning, tool_used, duration_ms, now)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_traces(self, entity_id: str) -> List[Dict[str, Any]]:
        """Get all trace steps for an entity, ordered by step."""
        rows = self.conn.execute(
            "SELECT * FROM traces WHERE entity_id = ? ORDER BY step_num",
            (entity_id,)
        ).fetchall()
        return [{k: r[k] for k in r.keys()} for r in rows]

    def get_trace_summary(self, entity_id: str) -> str:
        """Get a compact reasoning trace summary for an entity."""
        traces = self.get_traces(entity_id)
        if not traces:
            return "No traces recorded."
        lines = []
        for t in traces:
            line = f"  {t['step_num']}. [{t['action']}]"
            if t['tool_used']:
                line += f" via {t['tool_used']}"
            if t['reasoning']:
                line += f" — {t['reasoning'][:120]}"
            lines.append(line)
        return f"Trace ({len(traces)} steps):\n" + "\n".join(lines)

    def discover_perspectives(self, topic: str) -> Dict[str, Any]:
        """Discover research perspectives from existing KB entities."""
        from researcher.kb_analysis import discover_perspectives
        return discover_perspectives(self, topic)

    def extract_task_features(self, description: str, metadata: Optional[Dict] = None) -> Dict[str, float]:
        """Extract task feature dimensions for coordinator routing."""
        from researcher.kb_router import extract_task_features
        return extract_task_features(self, description, metadata)

    def route_task(self, description: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Route a task to the best coordinator."""
        from researcher.kb_router import route_task
        return route_task(self, description, metadata)

    def _suggest_config(self, coordinator: str, features: Dict[str, float]) -> Dict[str, Any]:
        """Suggest coordinator-specific configuration."""
        from researcher.kb_router import _suggest_config
        return _suggest_config(coordinator, features)

    def _routing_reasoning(self, best: str, features: Dict, ranked: list) -> str:
        """Generate brief reasoning for routing decision."""
        from researcher.kb_router import _routing_reasoning
        return _routing_reasoning(best, features, ranked)

    def add_decision(self, title: str, criteria: List[Dict[str, Any]],
                     alternatives: List[str], entity_id: Optional[str] = None,
                     weights: Optional[Dict[str, float]] = None) -> int:
        """Create a structured decision. Returns decision ID."""
        from researcher.kb_decisions import add_decision
        return add_decision(self, title, criteria, alternatives, entity_id, weights)

    def score_alternatives(self, decision_id: int, scores: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """Score alternatives against criteria."""
        from researcher.kb_decisions import score_alternatives
        return score_alternatives(self, decision_id, scores)

    def sensitivity_analysis(self, decision_id: int, perturbation: float = 0.1) -> Dict[str, Any]:
        """Check how sensitive the recommendation is to weight changes."""
        from researcher.kb_decisions import sensitivity_analysis
        return sensitivity_analysis(self, decision_id, perturbation)

    def get_decision(self, decision_id: int) -> Optional[Dict[str, Any]]:
        """Get a decision by ID."""
        from researcher.kb_decisions import get_decision
        return get_decision(self, decision_id)

    def generate_outline(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Generate a hierarchical report outline."""
        from researcher.kb_reports import generate_outline
        return generate_outline(self, entity_id)

    def export_entity_markdown(self, entity_id: str) -> Optional[str]:
        """Export an entity as markdown with frontmatter."""
        from researcher.kb_reports import export_entity_markdown
        return export_entity_markdown(self, entity_id)

    def visualize_graph(self, format: str = "dot") -> str:
        """Generate a visualization of the knowledge graph."""
        if format == "dot":
            # GraphViz DOT format
            output = "digraph KnowledgeBase {\n"
            output += '  node [shape=box, style=rounded];\n\n'
            
            # Add nodes
            entities = self.list_entities()
            for entity in entities:
                label = entity['title'].replace('"', '\\"')[:50]
                output += f'  "{entity["id"]}" [label="{label}"];\n'
            
            # Add edges
            output += "\n"
            links = self.conn.execute("SELECT * FROM links").fetchall()
            for link in links:
                output += f'  "{link["from_id"]}" -> "{link["to_id"]}" [label="{link["link_type"]}"];\n'
            
            output += "}\n"
            return output
        
        elif format == "json":
            # JSON graph format
            entities = self.list_entities()
            links = self.conn.execute("SELECT * FROM links").fetchall()
            
            return json.dumps({
                'nodes': [{'id': e['id'], 'title': e['title']} for e in entities],
                'edges': [
                    {
                        'from': link['from_id'],
                        'to': link['to_id'],
                        'type': link['link_type']
                    }
                    for link in links
                ]
            }, indent=2)
        
        else:
            return f"Unknown format: {format}"
    
    def check_spawn_budget(self, entity_id: str, max_depth: int = 8, max_total: int = 400) -> Dict[str, Any]:
        """Check if an agent can spawn sub-agents from this entity."""
        from researcher.kb_spawn import check_spawn_budget
        return check_spawn_budget(self, entity_id, max_depth, max_total)

    def _count_tree(self, root_id: str) -> int:
        """Count all entities reachable from root."""
        from researcher.kb_spawn import _count_tree
        return _count_tree(self, root_id)

    def record_spawn(self, parent_id: str, title: str, content: str = "",
                     agent_type: str = "researcher", metadata: Optional[Dict[str, Any]] = None,
                     max_depth: int = 8, max_total: int = 400) -> Dict[str, Any]:
        """Record a sub-agent spawn in the KB."""
        from researcher.kb_spawn import record_spawn
        return record_spawn(self, parent_id, title, content, agent_type, metadata, max_depth, max_total)

    def get_spawn_context(self, entity_id: str) -> Dict[str, Any]:
        """Get context for a spawned sub-agent."""
        from researcher.kb_spawn import get_spawn_context
        return get_spawn_context(self, entity_id)

    @property
    def embedding_model(self):
        """Lazy-load sentence-transformers model."""
        from researcher.kb_vectors import _get_embedding_model
        return _get_embedding_model(self)

    def _embed_text(self, text: str) -> bytes:
        """Embed text and return serialized float32 vector."""
        from researcher.kb_vectors import _embed_text
        return _embed_text(self, text)

    def _text_hash(self, text: str) -> str:
        from researcher.kb_vectors import _text_hash
        return _text_hash(text)

    def embed_entity(self, entity_id: str) -> bool:
        """Embed an entity into the vector index."""
        from researcher.kb_vectors import embed_entity
        return embed_entity(self, entity_id)

    def embed_claim(self, claim_id: int) -> bool:
        """Embed a claim into the vector index."""
        from researcher.kb_vectors import embed_claim
        return embed_claim(self, claim_id)

    def embed_all(self) -> Dict[str, int]:
        """Embed all entities and claims."""
        from researcher.kb_vectors import embed_all
        return embed_all(self)

    def semantic_search(self, query: str, limit: int = 10, source_table: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search by semantic similarity."""
        from researcher.kb_vectors import semantic_search
        return semantic_search(self, query, limit, source_table)

    def hybrid_search(self, query: str, limit: int = 10, source_table: Optional[str] = None) -> List[Dict[str, Any]]:
        """Reciprocal Rank Fusion hybrid search."""
        from researcher.kb_vectors import hybrid_search
        return hybrid_search(self, query, limit, source_table)

    def synthesize_entity(self, entity_id: str, audience: str = 'technical') -> Dict[str, Any]:
        """STORM-style 3-phase synthesis."""
        from researcher.kb_reports import synthesize_entity
        return synthesize_entity(self, entity_id, audience)

    def monitor_tree(self, root_entity_id: str) -> Dict[str, Any]:
        """Monitor a research tree: track progress, detect anomalies."""
        entity = self._require_entity(root_entity_id)
        if entity is None:
            return {"error": "entity not found"}

        children = self.get_links_from(root_entity_id)

        def walk_tree(eid, depth=0):
            nodes = []
            e = self.get_entity(eid)
            if not e:
                return nodes
            claims = self.list_claims(entity_id=eid)
            traces = self.conn.execute(
                "SELECT * FROM traces WHERE entity_id = ? ORDER BY created_at DESC LIMIT 1",
                (eid,)
            ).fetchone()
            last_activity = traces['created_at'] if traces else e['updated_at']
            nodes.append({
                'entity_id': eid,
                'title': e['title'][:50],
                'depth': depth,
                'claim_count': len(claims),
                'has_content': bool(e.get('content')),
                'last_activity': last_activity,
                'created_at': e['created_at']
            })
            for child in self.get_links_from(eid):
                if child.get('link_type') in ('child', 'wave', 'spawned'):
                    nodes.extend(walk_tree(child['id'], depth + 1))
            return nodes

        all_nodes = walk_tree(root_entity_id)
        alerts = []

        empty_nodes = [n for n in all_nodes if n['claim_count'] == 0 and not n['has_content'] and n['depth'] > 0]
        if empty_nodes:
            alerts.append({'type': 'empty_nodes', 'severity': 'warning',
                          'count': len(empty_nodes), 'nodes': [n['title'] for n in empty_nodes[:5]]})

        max_depth = max(n['depth'] for n in all_nodes) if all_nodes else 0
        if max_depth > 3:
            alerts.append({'type': 'deep_tree', 'severity': 'info', 'max_depth': max_depth,
                          'detail': f'Tree has {max_depth} levels — consider consolidation'})

        if children:
            child_sizes = []
            for child in children:
                subtree = walk_tree(child['id'])
                child_sizes.append((child['title'][:30], len(subtree)))
            if child_sizes:
                sizes = [s for _, s in child_sizes]
                avg_size = sum(sizes) / len(sizes)
                max_size = max(sizes)
                if max_size > avg_size * 3 and avg_size > 1:
                    alerts.append({'type': 'imbalanced_tree', 'severity': 'info',
                                  'detail': f'Largest branch ({max_size} nodes) is {max_size/avg_size:.1f}x average ({avg_size:.0f})'})

        evals = self.conn.execute(
            "SELECT * FROM evaluations WHERE parent_id = ? ORDER BY id DESC LIMIT 1",
            (root_entity_id,)
        ).fetchone()
        eval_info = None
        if evals:
            history = json.loads(evals['confidence_history'] or '[]')
            eval_info = {
                'confidence': evals['confidence'], 'iteration': evals['iteration'],
                'status': evals['status'],
                'trajectory': history[-5:] if history else [],
                'stalled': len(history) >= 3 and all(
                    abs(h.get('delta', 0)) < 0.02 for h in history[-3:]
                ) if history else False
            }
            if eval_info['stalled']:
                alerts.append({'type': 'confidence_stalled', 'severity': 'warning',
                              'detail': f'Confidence stalled at {evals["confidence"]:.2f} for {len(history)} iterations'})

        total_claims = sum(n['claim_count'] for n in all_nodes)
        nodes_with_content = sum(1 for n in all_nodes if n['has_content'])
        return {
            'root_entity_id': root_entity_id, 'root_title': entity.get('title', ''),
            'tree_size': len(all_nodes), 'max_depth': max_depth,
            'total_claims': total_claims, 'nodes_with_content': nodes_with_content,
            'nodes_without_content': len(all_nodes) - nodes_with_content,
            'evaluation': eval_info, 'alerts': alerts, 'alert_count': len(alerts),
            'nodes': all_nodes
        }

    def review(self, entity_id: str, depth: str = 'full') -> Dict[str, Any]:
        """Unified review: structural + semantic + gaps + quantities."""
        from researcher.kb_quality import review
        return review(self, entity_id, depth)

    def qa(self, entity_id: str, n_samples: int = 5, search_fn=None) -> Dict[str, Any]:
        """Unified quality assurance: SC grading + SAFE verification."""
        from researcher.kb_quality import qa
        return qa(self, entity_id, n_samples, search_fn)

    def get_domain_profile(self, domain: str) -> Optional[Dict[str, Any]]:
        """Get a domain expert profile by name."""
        from researcher.kb_domains import get_domain_profile
        return get_domain_profile(self, domain)

    def match_domain_expert(self, text: str) -> List[Dict[str, Any]]:
        """Match text to relevant domain expert profiles."""
        from researcher.kb_domains import match_domain_expert
        return match_domain_expert(self, text)

    def domain_review(self, entity_id: str, domain: str) -> Dict[str, Any]:
        """Apply domain-specific review to an entity's claims."""
        from researcher.kb_domains import domain_review
        return domain_review(self, entity_id, domain)

    def close(self):
        """Close database connection."""
        self.conn.close()


# Example usage
if __name__ == "__main__":
    kb = KnowledgeBase()
    
    # Add some entities
    node1 = kb.add_entity(
        title="Should we use cloud storage?",
        content="Research question about cloud storage adoption.",
        metadata={"type": "question", "depth": 0}
    )
    
    node2 = kb.add_entity(
        title="Security concerns with cloud storage",
        content="Researching encryption, data sovereignty, compliance...",
        metadata={"type": "research", "depth": 1}
    )
    
    # Link them
    kb.add_link(node1, node2, "child")
    
    # Add a task for future research
    task_id = kb.add_task(
        title="Research encryption standards",
        description="Deep dive into encryption methods used by major cloud providers",
        entity_id=node2,
        metadata={"priority": "high"}
    )
    
    # Query
    print("Entity:", kb.get_entity(node1))
    print("Links from node1:", kb.get_links_from(node1))
    print("Pending tasks:", kb.get_tasks(status="pending"))
    
    kb.close()
