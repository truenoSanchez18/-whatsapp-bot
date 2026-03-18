import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "conversations.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            phone TEXT PRIMARY KEY,
            name TEXT DEFAULT '',
            language TEXT DEFAULT 'es',
            intent_route TEXT DEFAULT '',
            need_or_motivation TEXT DEFAULT '',
            lead_temperature TEXT DEFAULT '',
            recommended_offer TEXT DEFAULT '',
            last_message_summary TEXT DEFAULT '',
            payment_link_sent INTEGER DEFAULT 0,
            human_handoff_requested INTEGER DEFAULT 0,
            follow_up_count INTEGER DEFAULT 0,
            conversation_status TEXT DEFAULT 'new',
            history TEXT DEFAULT '[]',
            created_at TEXT,
            updated_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_followups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT NOT NULL,
            followup_type TEXT NOT NULL,
            scheduled_at TEXT NOT NULL,
            sent INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()


def get_conversation(phone: str) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM conversations WHERE phone = ?", (phone,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return {
            "phone": phone,
            "name": "",
            "language": "es",
            "intent_route": "",
            "need_or_motivation": "",
            "lead_temperature": "",
            "recommended_offer": "",
            "last_message_summary": "",
            "payment_link_sent": False,
            "human_handoff_requested": False,
            "follow_up_count": 0,
            "conversation_status": "new",
            "history": [],
        }

    data = dict(row)
    data["history"] = json.loads(data["history"] or "[]")
    data["payment_link_sent"] = bool(data["payment_link_sent"])
    data["human_handoff_requested"] = bool(data["human_handoff_requested"])
    return data


def save_conversation(phone: str, state: dict):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()

    history_json = json.dumps(state.get("history", []), ensure_ascii=False)

    cursor.execute("""
        INSERT INTO conversations (
            phone, name, language, intent_route, need_or_motivation,
            lead_temperature, recommended_offer, last_message_summary,
            payment_link_sent, human_handoff_requested, follow_up_count,
            conversation_status, history, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(phone) DO UPDATE SET
            name=excluded.name,
            language=excluded.language,
            intent_route=excluded.intent_route,
            need_or_motivation=excluded.need_or_motivation,
            lead_temperature=excluded.lead_temperature,
            recommended_offer=excluded.recommended_offer,
            last_message_summary=excluded.last_message_summary,
            payment_link_sent=excluded.payment_link_sent,
            human_handoff_requested=excluded.human_handoff_requested,
            follow_up_count=excluded.follow_up_count,
            conversation_status=excluded.conversation_status,
            history=excluded.history,
            updated_at=excluded.updated_at
    """, (
        phone,
        state.get("name", ""),
        state.get("language", "es"),
        state.get("intent_route", ""),
        state.get("need_or_motivation", ""),
        state.get("lead_temperature", ""),
        state.get("recommended_offer", ""),
        state.get("last_message_summary", ""),
        1 if state.get("payment_link_sent") else 0,
        1 if state.get("human_handoff_requested") else 0,
        state.get("follow_up_count", 0),
        state.get("conversation_status", "new"),
        history_json,
        now,
        now,
    ))
    conn.commit()
    conn.close()


def schedule_followup(phone: str, followup_type: str, scheduled_at: datetime):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    cursor.execute("""
        INSERT INTO scheduled_followups (phone, followup_type, scheduled_at, sent, created_at)
        VALUES (?, ?, ?, 0, ?)
    """, (phone, followup_type, scheduled_at.isoformat(), now))
    conn.commit()
    conn.close()


def get_pending_followups(now: datetime) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM scheduled_followups
        WHERE sent = 0 AND scheduled_at <= ?
    """, (now.isoformat(),))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def mark_followup_sent(followup_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE scheduled_followups SET sent = 1 WHERE id = ?", (followup_id,))
    conn.commit()
    conn.close()
