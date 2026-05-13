"""
SQLite-backed conversation session store (replaces Redis for free stack).
"""
from typing import List
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from .models import ConversationSession

MAX_HISTORY_TURNS = 20


async def get_history(db: AsyncSession, session_id: str) -> List[dict]:
    result = await db.execute(
        select(ConversationSession).where(ConversationSession.session_id == session_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        return []
    history = row.history or []
    # Keep last MAX_HISTORY_TURNS messages (each turn = 2 messages)
    return history[-(MAX_HISTORY_TURNS * 2):]


async def save_history(db: AsyncSession, session_id: str, history: List[dict]):
    truncated = history[-(MAX_HISTORY_TURNS * 2):]
    result = await db.execute(
        select(ConversationSession).where(ConversationSession.session_id == session_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        db.add(ConversationSession(
            session_id=session_id,
            history=truncated,
            updated_at=datetime.utcnow(),
        ))
    else:
        row.history = truncated
        row.updated_at = datetime.utcnow()
    await db.commit()
