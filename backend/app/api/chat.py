from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from ..models.request import ChatRequest
from ..services.analytics import run_agent
from ..db.queries import get_sessions, get_messages
from ..middleware.auth import get_current_user

router = APIRouter()


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest, user_id: str = Depends(get_current_user)):
    async def generate():
        async for chunk in run_agent(req.query, user_id, req.session_id):
            yield chunk

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )


@router.get("/chat/sessions")
async def list_sessions(user_id: str = Depends(get_current_user)):
    sessions = await get_sessions(user_id)
    result = []
    for s in sessions:
        row = {}
        for k, v in s.items():
            if hasattr(v, "hex"):
                row[k] = str(v)
            elif hasattr(v, "isoformat"):
                row[k] = v.isoformat()
            else:
                row[k] = v
        result.append(row)
    return {"sessions": result}


@router.get("/chat/sessions/{session_id}/messages")
async def get_session_messages(session_id: str, user_id: str = Depends(get_current_user)):
    messages = await get_messages(session_id)
    result = []
    for m in messages:
        row = {}
        for k, v in m.items():
            if hasattr(v, "hex"):          # UUID
                row[k] = str(v)
            elif hasattr(v, "isoformat"):  # datetime
                row[k] = v.isoformat()
            else:
                row[k] = v                 # str, int, dict (response_json) — pass through as-is
        result.append(row)
    return {"messages": result}
