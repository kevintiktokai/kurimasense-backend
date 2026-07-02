"""
Chat sessions API — the backend for the LLM-style AI advisor UI
(history sidebar, new chat, resume past chats).

Sessions are personal data (user-scoped, like chat_logs — no tenant dimension).
Messages continue to live in chat_logs; `chat_logs.session_id` joins them to a
session, with a `field_context_id` fallback for rows written before the session
column existed. The send/stream endpoints in app.py already accept `session_id`;
`ConversationMemory.add_message` persists it and auto-titles the session from
the first user message.
"""

from fastapi import APIRouter, Depends, HTTPException
from psycopg2.extras import RealDictCursor

from database import get_db_connection
from deps import verify_token

router = APIRouter(prefix="/chat/sessions", tags=["chat-sessions"])


def _conn_or_503():
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return conn


@router.get("")
def list_sessions(user_id: str = Depends(verify_token)):
    """Caller's sessions, most recently active first, with a preview snippet."""
    conn = _conn_or_503()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT s.id::text, s.title, s.created_at, s.updated_at,
                   (SELECT COUNT(*) FROM chat_logs l WHERE l.session_id = s.id) AS message_count,
                   (SELECT l.content FROM chat_logs l
                    WHERE l.session_id = s.id ORDER BY l.created_at DESC LIMIT 1) AS last_message
            FROM chat_sessions s
            WHERE s.user_id = %s
            ORDER BY s.updated_at DESC
            LIMIT 100
        """, (user_id,))
        rows = cur.fetchall()
        cur.close()
        return [
            {
                "id": r["id"],
                "title": r["title"] or "New chat",
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                "updated_at": r["updated_at"].isoformat() if r["updated_at"] else None,
                "message_count": r["message_count"],
                "preview": (r["last_message"] or "")[:120],
            }
            for r in rows
        ]
    finally:
        conn.close()


@router.post("")
def create_session(payload: dict = None, user_id: str = Depends(verify_token)):
    title = (payload or {}).get("title") or "New chat"
    conn = _conn_or_503()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "INSERT INTO chat_sessions (user_id, title) VALUES (%s, %s) RETURNING id::text, title, created_at",
            (user_id, title[:120]),
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
        return {
            "id": row["id"],
            "title": row["title"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        }
    finally:
        conn.close()


def _assert_owner(cur, session_id: str, user_id: str):
    cur.execute(
        "SELECT 1 FROM chat_sessions WHERE id = %s::uuid AND user_id = %s",
        (session_id, user_id),
    )
    if not cur.fetchone():
        raise HTTPException(status_code=404, detail="Session not found")


@router.get("/{session_id}/messages")
def get_session_messages(session_id: str, user_id: str = Depends(verify_token)):
    """Full message list for one session, chronological."""
    conn = _conn_or_503()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        _assert_owner(cur, session_id, user_id)
        cur.execute("""
            SELECT role, content, created_at
            FROM chat_logs
            WHERE user_id = %s
              AND (session_id = %s::uuid OR field_context_id = %s)
            ORDER BY created_at ASC
            LIMIT 500
        """, (user_id, session_id, session_id))
        rows = cur.fetchall()
        cur.close()
        return [
            {
                "role": r["role"],
                "content": r["content"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            }
            for r in rows
        ]
    finally:
        conn.close()


@router.patch("/{session_id}")
def rename_session(session_id: str, payload: dict, user_id: str = Depends(verify_token)):
    title = (payload or {}).get("title", "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="title required")
    conn = _conn_or_503()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        _assert_owner(cur, session_id, user_id)
        cur.execute(
            "UPDATE chat_sessions SET title = %s, updated_at = NOW() WHERE id = %s::uuid AND user_id = %s",
            (title[:120], session_id, user_id),
        )
        conn.commit()
        cur.close()
        return {"status": "success", "id": session_id, "title": title[:120]}
    finally:
        conn.close()


@router.delete("/{session_id}")
def delete_session(session_id: str, user_id: str = Depends(verify_token)):
    """Delete a session and its messages."""
    conn = _conn_or_503()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        _assert_owner(cur, session_id, user_id)
        cur.execute(
            "DELETE FROM chat_logs WHERE user_id = %s AND (session_id = %s::uuid OR field_context_id = %s)",
            (user_id, session_id, session_id),
        )
        n = cur.rowcount
        cur.execute(
            "DELETE FROM chat_sessions WHERE id = %s::uuid AND user_id = %s",
            (session_id, user_id),
        )
        conn.commit()
        cur.close()
        return {"status": "success", "deleted_messages": n}
    finally:
        conn.close()
