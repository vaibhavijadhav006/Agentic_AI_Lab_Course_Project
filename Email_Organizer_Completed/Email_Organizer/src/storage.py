import json
import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "email_memory.db"
)


class MemoryStore:
    """Persistent email analysis, drafts, memory retrieval, calendar, and audit store."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self._lock = threading.Lock()
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        self._create_tables()
        self._seed_institutional_knowledge()

    def _create_tables(self):
        with self._lock:
            self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS emails (
                id TEXT PRIMARY KEY,
                sender TEXT,
                subject TEXT,
                body TEXT,
                received_at TEXT,
                category TEXT,
                priority TEXT,
                urgency_score INTEGER,
                action_items TEXT,
                follow_up_date TEXT,
                reply_required INTEGER,
                reason TEXT
            );

            CREATE TABLE IF NOT EXISTS drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id TEXT,
                recipient TEXT,
                subject TEXT,
                body TEXT,
                status TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                approved_at DATETIME
            );

            CREATE TABLE IF NOT EXISTS memory_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT,
                value TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT,
                action TEXT,
                email_id TEXT,
                status TEXT,
                details TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS research_dossiers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id TEXT,
                topic TEXT,
                findings TEXT,
                citations TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS calendar_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id TEXT,
                title TEXT,
                event_date TEXT,
                event_time TEXT,
                description TEXT,
                status TEXT DEFAULT 'SCHEDULED',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """)
            self.conn.commit()

            # Schema migration: ensure approved_at column exists in drafts
            try:
                self.conn.execute("ALTER TABLE drafts ADD COLUMN approved_at DATETIME")
                self.conn.commit()
            except sqlite3.OperationalError:
                pass

    def _seed_institutional_knowledge(self):
        """Seed institutional context notes for deep research and memory retrieval."""
        seeds = [
            (
                "policy:placement_registration_deadline",
                "College Placement Cell Rule: All final-year students must complete corporate drive registration 24 hours prior to drive start. Failure to register results in automatic de-listing from Tier-1 recruiter drives."
            ),
            (
                "curriculum:data_structures_assignment",
                "Course CS301 (Data Structures): Assignment 2 requires graph traversal implementation. The syllabus specifies Breadth-First Search (BFS) for shortest path routing and Depth-First Search (DFS) for topological sort component."
            ),
            (
                "guideline:project_progress_review",
                "College Academic Council: Project milestone reviews require a standard two-page progress report covering methodology, current sprint deliverables, and test coverage submitted 48 hours in advance."
            ),
            (
                "admin:department_meeting_protocol",
                "CS Department Bylaws: All faculty and student representatives must acknowledge minutes within 3 business days. Action items from minutes are tracked in quarterly department reviews."
            ),
            (
                "governance:email_safety_policy",
                "Campus Information Security Policy: Never transmit unencrypted student credentials, passwords, or personal identity numbers via email drafts. All outbound communications require human verification."
            )
        ]
        with self._lock:
            cursor = self.conn.cursor()
            for key, value in seeds:
                cursor.execute("SELECT id FROM memory_notes WHERE key = ?", (key,))
                if not cursor.fetchone():
                    cursor.execute("INSERT INTO memory_notes (key, value) VALUES (?, ?)", (key, value))
            self.conn.commit()

    def save_analysis(
        self,
        email: Dict[str, Any],
        analysis: Dict[str, Any]
    ):
        with self._lock:
            self.conn.execute("""
            INSERT OR REPLACE INTO emails
            (id, sender, subject, body, received_at, category, priority,
             urgency_score, action_items, follow_up_date, reply_required, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                email["id"],
                email["sender"],
                email["subject"],
                email["body"],
                email["received_at"],
                analysis["category"],
                analysis["priority"],
                analysis["urgency_score"],
                json.dumps(analysis["action_items"]),
                analysis.get("follow_up_date"),
                int(analysis["reply_required"]),
                analysis.get("reason", "")
            ))
            self.conn.commit()

    def save_draft(self, draft: Dict[str, Any]):
        with self._lock:
            cursor = self.conn.execute("""
            INSERT INTO drafts
            (email_id, recipient, subject, body, status)
            VALUES (?, ?, ?, ?, ?)
            """, (
                draft["email_id"],
                draft.get("to", draft.get("recipient", "")),
                draft["subject"],
                draft["body"],
                draft.get("status", "PENDING_APPROVAL")
            ))
            self.conn.commit()
            return {
                "status": "saved",
                "draft_id": cursor.lastrowid,
                "email_id": draft["email_id"]
            }

    def update_draft_status(self, identifier: str, status: str = "APPROVED") -> bool:
        """Update draft status by email_id or integer draft ID."""
        with self._lock:
            # Check if identifier is integer id or email_id
            if identifier.isdigit():
                cursor = self.conn.execute(
                    "UPDATE drafts SET status = ?, approved_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (status, int(identifier))
                )
            else:
                cursor = self.conn.execute(
                    "UPDATE drafts SET status = ?, approved_at = CURRENT_TIMESTAMP WHERE email_id = ?",
                    (status, identifier)
                )
            self.conn.commit()
            return cursor.rowcount > 0

    def get_draft(self, identifier: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            if identifier.isdigit():
                row = self.conn.execute("SELECT * FROM drafts WHERE id = ?", (int(identifier),)).fetchone()
            else:
                row = self.conn.execute("SELECT * FROM drafts WHERE email_id = ? ORDER BY id DESC LIMIT 1", (identifier,)).fetchone()
            return dict(row) if row else None

    def get_all_drafts(self) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self.conn.execute("SELECT * FROM drafts ORDER BY id ASC").fetchall()
            return [dict(r) for r in rows]

    def save_memory(self, key: str, value: str):
        with self._lock:
            self.conn.execute(
                "INSERT INTO memory_notes (key, value) VALUES (?, ?)",
                (key, value)
            )
            self.conn.commit()
            return {
                "key": key,
                "value": value,
                "status": "saved"
            }

    def save_calendar_event(
        self,
        email_id: str,
        title: str,
        event_date: str,
        event_time: str,
        description: str
    ) -> Dict[str, Any]:
        with self._lock:
            cursor = self.conn.execute("""
            INSERT INTO calendar_events (email_id, title, event_date, event_time, description)
            VALUES (?, ?, ?, ?, ?)
            """, (email_id, title, event_date, event_time, description))
            self.conn.commit()
            return {
                "event_id": cursor.lastrowid,
                "email_id": email_id,
                "title": title,
                "status": "SCHEDULED"
            }

    def list_calendar_events(self) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self.conn.execute("SELECT * FROM calendar_events ORDER BY id ASC").fetchall()
            return [dict(r) for r in rows]

    def save_audit_entry(self, agent_name: str, action: str, email_id: Optional[str], status: str, details: Dict[str, Any]):
        with self._lock:
            self.conn.execute(
                "INSERT INTO audit_logs (agent_name, action, email_id, status, details) VALUES (?, ?, ?, ?, ?)",
                (agent_name, action, email_id or "GLOBAL", status, json.dumps(details))
            )
            self.conn.commit()

    def save_research_entry(self, email_id: str, topic: str, findings: str, citations: List[str]):
        with self._lock:
            self.conn.execute(
                "INSERT INTO research_dossiers (email_id, topic, findings, citations) VALUES (?, ?, ?, ?)",
                (email_id, topic, findings, json.dumps(citations))
            )
            self.conn.commit()

    def get_email(self, email_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            row = self.conn.execute("SELECT * FROM emails WHERE id = ?", (email_id,)).fetchone()
            if row:
                d = dict(row)
                try:
                    d["action_items"] = json.loads(d["action_items"])
                except Exception:
                    pass
                return d
            return None

    def get_all_emails(self) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self.conn.execute("SELECT * FROM emails ORDER BY id ASC").fetchall()
            results = []
            for r in rows:
                d = dict(r)
                try:
                    d["action_items"] = json.loads(d["action_items"])
                except Exception:
                    pass
                results.append(d)
            return results

    def search(
        self,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search analysed emails and saved memory notes."""
        terms = [
            term.lower()
            for term in query.split()
            if len(term) >= 3
        ]

        if not terms or limit <= 0:
            return []

        # Search analysed emails
        email_clauses = []
        email_params = []

        for term in terms:
            email_clauses.append("""
                (
                    LOWER(subject) LIKE ?
                    OR LOWER(body) LIKE ?
                    OR LOWER(sender) LIKE ?
                )
            """)
            like = f"%{term}%"
            email_params.extend([like, like, like])

        email_sql = f"""
        SELECT id, sender, subject, body, received_at, category,
               priority, urgency_score, action_items, follow_up_date,
               reply_required, reason
        FROM emails
        WHERE {" OR ".join(email_clauses)}
        ORDER BY received_at DESC
        LIMIT ?
        """
        email_params.append(limit)

        with self._lock:
            email_rows = self.conn.execute(
                email_sql,
                email_params
            ).fetchall()

            results = []
            for row in email_rows:
                item = dict(row)
                item["source"] = "email"
                results.append(item)

            # Search saved memory notes
            note_clauses = []
            note_params = []

            for term in terms:
                note_clauses.append(
                    "(LOWER(key) LIKE ? OR LOWER(value) LIKE ?)"
                )
                like = f"%{term}%"
                note_params.extend([like, like])

            note_sql = f"""
            SELECT id, key, value, created_at
            FROM memory_notes
            WHERE {" OR ".join(note_clauses)}
            ORDER BY created_at DESC
            LIMIT ?
            """
            note_params.append(limit)

            note_rows = self.conn.execute(
                note_sql,
                note_params
            ).fetchall()

            for row in note_rows:
                note = dict(row)
                results.append({
                    "id": f"MEM-{note['id']}",
                    "sender": "Saved Memory",
                    "subject": note["key"],
                    "body": note["value"],
                    "note": note["value"],
                    "priority": "MEMORY",
                    "source": "memory_note",
                    "created_at": note["created_at"]
                })

        return results[:limit]

    def pending_drafts(self) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self.conn.execute("""
                SELECT * FROM drafts
                WHERE status = 'PENDING_APPROVAL'
                ORDER BY created_at DESC
            """).fetchall()
            return [dict(row) for row in rows]

    def get_audit_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self.conn.execute(
                "SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?",
                (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    def close(self):
        with self._lock:
            self.conn.close()
