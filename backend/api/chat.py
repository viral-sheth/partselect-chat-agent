from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from db.database import get_db
from db.session_store import get_history, save_history
from agent.loop import run_agent, _sse
from schemas.chat import ChatRequest

import json

router = APIRouter()


@router.post("/chat")
async def chat(request: ChatRequest, db=Depends(get_db)):
    async def event_stream():
        history = await get_history(db, request.session_id)

        final_messages = history
        async for event in run_agent(
            message=request.message,
            history=history,
            session_id=request.session_id,
            db=db,
        ):
            yield event
            try:
                data = json.loads(event.removeprefix("data: ").strip())
                if data.get("type") == "done":
                    final_messages = data.get("final_messages", history)
            except Exception:
                pass

        await save_history(db, request.session_id, final_messages)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
