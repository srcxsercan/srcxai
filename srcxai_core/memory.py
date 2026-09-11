"""
Persistent Memory and Context Management
Handles long-term memory, conversation history, and context persistence
"""

import sqlite3
import json
import os
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import hashlib


class MemoryManager:
    """Manages persistent memory for SRCXAI"""
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = str(Path.home() / "srcxai_memory.db")
        
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._initialize_db()
    
    def _initialize_db(self):
        """Initialize database schema"""
        cursor = self.conn.cursor()
        
        # Conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        ''')
        
        # Context table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS context (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                category TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tasks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                result TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME
            )
        ''')
        
        # Knowledge base table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                tags TEXT,
                embedding BLOB,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # System state table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # File operations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_operations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                operation TEXT NOT NULL,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN DEFAULT TRUE
            )
        ''')
        
        self.conn.commit()
    
    def add_conversation_message(self, session_id: str, role: str, content: str, 
                                 metadata: Optional[Dict] = None):
        """Add a message to conversation history"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO conversations (session_id, role, content, metadata)
            VALUES (?, ?, ?, ?)
        ''', (session_id, role, content, json.dumps(metadata) if metadata else None))
        self.conn.commit()
    
    def get_conversation_history(self, session_id: str, limit: Optional[int] = None) -> List[Dict]:
        """Get conversation history for a session"""
        cursor = self.conn.cursor()
        query = 'SELECT role, content, timestamp, metadata FROM conversations WHERE session_id = ? ORDER BY timestamp'
        if limit:
            query += f' LIMIT {limit}'
        
        cursor.execute(query, (session_id,))
        rows = cursor.fetchall()
        
        return [{
            'role': row[0],
            'content': row[1],
            'timestamp': row[2],
            'metadata': json.loads(row[3]) if row[3] else None
        } for row in rows]
    
    def set_context(self, key: str, value: Any, category: Optional[str] = None):
        """Store context information"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO context (key, value, category, timestamp)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (key, json.dumps(value), category))
        self.conn.commit()
    
    def get_context(self, key: str) -> Optional[Any]:
        """Retrieve context information"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT value FROM context WHERE key = ?', (key,))
        row = cursor.fetchone()
        
        if row:
            return json.loads(row[0])
        return None
    
    def get_all_context(self, category: Optional[str] = None) -> Dict[str, Any]:
        """Get all context, optionally filtered by category"""
        cursor = self.conn.cursor()
        if category:
            cursor.execute('SELECT key, value FROM context WHERE category = ?', (category,))
        else:
            cursor.execute('SELECT key, value FROM context')
        
        rows = cursor.fetchall()
        return {row[0]: json.loads(row[1]) for row in rows}
    
    def add_task(self, task: str) -> int:
        """Add a new task"""
        cursor = self.conn.cursor()
        cursor.execute('INSERT INTO tasks (task, status) VALUES (?, ?)', (task, 'pending'))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_task(self, task_id: int, status: str, result: Optional[str] = None):
        """Update task status and result"""
        cursor = self.conn.cursor()
        if result:
            cursor.execute('''
                UPDATE tasks SET status = ?, result = ?, completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, result, task_id))
        else:
            cursor.execute('UPDATE tasks SET status = ? WHERE id = ?', (status, task_id))
        self.conn.commit()
    
    def get_pending_tasks(self) -> List[Dict]:
        """Get all pending tasks"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, task, timestamp FROM tasks WHERE status = "pending"')
        rows = cursor.fetchall()
        
        return [{
            'id': row[0],
            'task': row[1],
            'timestamp': row[2]
        } for row in rows]
    
    def add_knowledge(self, title: str, content: str, tags: Optional[List[str]] = None):
        """Add knowledge to the knowledge base"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO knowledge (title, content, tags)
            VALUES (?, ?, ?)
        ''', (title, content, json.dumps(tags) if tags else None))
        self.conn.commit()
    
    def search_knowledge(self, query: str) -> List[Dict]:
        """Search knowledge base"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT title, content, tags, timestamp FROM knowledge
            WHERE title LIKE ? OR content LIKE ?
        ''', (f'%{query}%', f'%{query}%'))
        
        rows = cursor.fetchall()
        return [{
            'title': row[0],
            'content': row[1],
            'tags': json.loads(row[2]) if row[2] else [],
            'timestamp': row[3]
        } for row in rows]
    
    def set_system_state(self, key: str, value: Any):
        """Store system state"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO system_state (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (key, json.dumps(value)))
        self.conn.commit()
    
    def get_system_state(self, key: str) -> Optional[Any]:
        """Retrieve system state"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT value FROM system_state WHERE key = ?', (key,))
        row = cursor.fetchone()
        
        if row:
            return json.loads(row[0])
        return None
    
    def log_file_operation(self, file_path: str, operation: str, content: Optional[str] = None, 
                          success: bool = True):
        """Log file operations for tracking"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO file_operations (file_path, operation, content, success)
            VALUES (?, ?, ?, ?)
        ''', (file_path, operation, content, success))
        self.conn.commit()
    
    def get_file_history(self, file_path: str) -> List[Dict]:
        """Get operation history for a file"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT operation, content, timestamp, success FROM file_operations
            WHERE file_path = ? ORDER BY timestamp
        ''', (file_path,))
        
        rows = cursor.fetchall()
        return [{
            'operation': row[0],
            'content': row[1],
            'timestamp': row[2],
            'success': row[3]
        } for row in rows]
    
    def create_session_id(self) -> str:
        """Create a unique session ID"""
        return hashlib.md5(str(time.time()).encode()).hexdigest()
    
    def cleanup_old_data(self, days: int = 30):
        """Clean up old data to manage database size"""
        cursor = self.conn.cursor()
        
        # Clean old conversations
        cursor.execute('''
            DELETE FROM conversations WHERE timestamp < datetime('now', ?)
        ''', (f'-{days} days',))
        
        # Clean old file operations
        cursor.execute('''
            DELETE FROM file_operations WHERE timestamp < datetime('now', ?)
        ''', (f'-{days} days',))
        
        self.conn.commit()
    
    def export_memory(self, export_path: str):
        """Export memory to JSON file"""
        cursor = self.conn.cursor()
        
        export_data = {
            'conversations': [],
            'context': {},
            'tasks': [],
            'knowledge': [],
            'system_state': {}
        }
        
        # Export conversations
        cursor.execute('SELECT * FROM conversations')
        for row in cursor.fetchall():
            export_data['conversations'].append({
                'id': row[0],
                'session_id': row[1],
                'role': row[2],
                'content': row[3],
                'timestamp': row[4],
                'metadata': json.loads(row[5]) if row[5] else None
            })
        
        # Export context
        cursor.execute('SELECT * FROM context')
        for row in cursor.fetchall():
            export_data['context'][row[1]] = json.loads(row[2])
        
        # Export tasks
        cursor.execute('SELECT * FROM tasks')
        for row in cursor.fetchall():
            export_data['tasks'].append({
                'id': row[0],
                'task': row[1],
                'status': row[2],
                'result': row[3],
                'timestamp': row[4],
                'completed_at': row[5]
            })
        
        # Export knowledge
        cursor.execute('SELECT * FROM knowledge')
        for row in cursor.fetchall():
            export_data['knowledge'].append({
                'id': row[0],
                'title': row[1],
                'content': row[2],
                'tags': json.loads(row[3]) if row[3] else [],
                'timestamp': row[4]
            })
        
        # Export system state
        cursor.execute('SELECT * FROM system_state')
        for row in cursor.fetchall():
            export_data['system_state'][row[1]] = json.loads(row[2])
        
        with open(export_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
    
    def close(self):
        """Close database connection"""
        self.conn.close()
