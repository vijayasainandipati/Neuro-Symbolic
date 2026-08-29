"""
Local SQLite Store-and-Forward Message Store for Offline P2P Relay.
Provides deduplication, persistent offline storage, and delivery tracking on individual nodes.
"""

import sqlite3
from typing import List, Dict, Any, Optional
from p2p.protocol.message import P2PMessage


class LocalMeshStore:
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                type TEXT,
                priority TEXT,
                issuer TEXT,
                timestamp TEXT,
                ttl INTEGER,
                hop_count INTEGER,
                location TEXT,
                message TEXT,
                signature TEXT,
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                relayed_count INTEGER DEFAULT 0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relay_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT,
                target_node TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def has_seen(self, message_id: str) -> bool:
        """Returns True if message has already been received, preventing infinite mesh loops."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM messages WHERE id = ?", (message_id,))
        return cursor.fetchone() is not None

    def save_message(self, msg: P2PMessage) -> bool:
        """Stores a new message locally if not already seen."""
        if self.has_seen(msg.id):
            return False

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO messages (id, type, priority, issuer, timestamp, ttl, hop_count, location, message, signature)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            msg.id, msg.type, msg.priority, msg.issuer, msg.timestamp,
            msg.ttl, msg.hop_count, msg.location, msg.message, msg.signature
        ))
        self.conn.commit()
        return True

    def get_pending_relays(self) -> List[P2PMessage]:
        """Returns valid messages that still have TTL > 0 ready to be forwarded."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM messages WHERE ttl > 0")
        rows = cursor.fetchall()
        return [P2PMessage(
            id=r["id"],
            type=r["type"],
            priority=r["priority"],
            issuer=r["issuer"],
            timestamp=r["timestamp"],
            ttl=r["ttl"],
            hop_count=r["hop_count"],
            location=r["location"],
            message=r["message"],
            signature=r["signature"]
        ) for r in rows]

    def log_relay(self, message_id: str, target_node: str):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO relay_log (message_id, target_node) VALUES (?, ?)
        """, (message_id, target_node))
        cursor.execute("""
            UPDATE messages SET relayed_count = relayed_count + 1 WHERE id = ?
        """, (message_id,))
        self.conn.commit()

    def get_all_messages(self) -> List[P2PMessage]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM messages ORDER BY received_at DESC")
        return [P2PMessage(
            id=r["id"],
            type=r["type"],
            priority=r["priority"],
            issuer=r["issuer"],
            timestamp=r["timestamp"],
            ttl=r["ttl"],
            hop_count=r["hop_count"],
            location=r["location"],
            message=r["message"],
            signature=r["signature"]
        ) for r in cursor.fetchall()]

    def get_stats(self) -> Dict[str, Any]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM messages")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM messages WHERE priority = 'CRITICAL'")
        critical = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM relay_log")
        relayed = cursor.fetchone()[0]
        return {
            "total_stored": total,
            "critical_count": critical,
            "relay_events": relayed
        }
