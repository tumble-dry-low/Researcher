#!/usr/bin/env python3
"""
Minimal Knowledge Base with automatic management.
Agents just add entities, links, and tasks - system manages the rest.
"""

import sqlite3
import json
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

class KnowledgeBase:
    """Minimal KB with entities, links, and task backlog."""
    
    def __init__(self, db_path: str = "knowledge-base/kb.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Access columns by name
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
        """)
        self.conn.commit()
    
    def add_entity(
        self, 
        title: str, 
        content: str = "", 
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add an entity (research note). Returns entity ID."""
        entity_id = str(uuid.uuid4())[:8]
        now = datetime.utcnow().isoformat()
        meta_json = json.dumps(metadata or {})
        
        self.conn.execute(
            "INSERT INTO entities (id, title, content, metadata, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (entity_id, title, content, meta_json, now, now)
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
            params.append(datetime.utcnow().isoformat())
            params.append(entity_id)
            
            query = f"UPDATE entities SET {', '.join(updates)} WHERE id = ?"
            self.conn.execute(query, params)
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
                (from_id, to_id, link_type, datetime.utcnow().isoformat())
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
        now = datetime.utcnow().isoformat()
        meta_json = json.dumps(metadata or {})
        
        cursor = self.conn.execute(
            "INSERT INTO tasks (title, description, entity_id, metadata, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (title, description, entity_id, meta_json, now, now)
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Get a task by ID."""
        row = self.conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        
        if row:
            return {
                'id': row['id'],
                'title': row['title'],
                'description': row['description'],
                'status': row['status'],
                'entity_id': row['entity_id'],
                'metadata': json.loads(row['metadata']),
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            }
        return None
    
    def update_task_status(self, task_id: int, status: str):
        """Update task status (pending, in_progress, completed, cancelled)."""
        self.conn.execute(
            "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?",
            (status, datetime.utcnow().isoformat(), task_id)
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
        """Simple full-text search across titles and content."""
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
        
        return {
            'entities': entity_count,
            'links': link_count,
            'tasks': task_count,
            'pending_tasks': pending_tasks,
            'completed_tasks': completed_tasks
        }
    
    def export_entity_markdown(self, entity_id: str) -> Optional[str]:
        """Export an entity as markdown with frontmatter."""
        entity = self.get_entity(entity_id)
        if not entity:
            return None
        
        # Get links
        links_from = self.get_links_from(entity_id)
        links_to = self.get_links_to(entity_id)
        
        # Build markdown
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
