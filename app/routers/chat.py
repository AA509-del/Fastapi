from fastapi import APIRouter, Depends
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache import get_cached_answer, set_cached_answer
# 数据库相关
from app.database import get_db
from app import crud
from app.services.agent import run_agent, run_agent_stream

router = APIRouter(prefix="/chat", tags=["chat"])

# 请求/响应模型
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

class ChatResponse(BaseModel):
    response: str
    session_id: str
    from_cache: bool = False


# class ChatResponse(BaseModel):
#     response: str
#     session_id: str
# @router.post("", summary="发送消息给AI", description="发送问题，获取AI回答，支持会话记忆", response_model=ChatResponse)
# async def chat(req: ChatRequest):
#     reply = await run_agent(req.message, req.session_id)
#     return ChatResponse(response=reply, session_id=req.session_id)


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):
    # 1. 查缓存（带 session_id）
    cached = await get_cached_answer(req.session_id, req.message)
    if cached:
        return ChatResponse(
            response=cached,
            session_id=req.session_id,
            from_cache=True,
        )

    # 2. 未命中：调 Agent
    reply = await run_agent(req.message, req.session_id)

    # 3. 写缓存（带 session_id）
    await set_cached_answer(req.session_id, req.message, reply)

    return ChatResponse(
        response=reply,
        session_id=req.session_id,
        from_cache=False,
    )

@router.post("/stream", summary="流式输出接口")
async def chat_stream(req: ChatRequest):
    return StreamingResponse(
        run_agent_stream(req.message, req.session_id),
        media_type="text/event-stream"
    )



@router.post("/save_message",response_model=ChatResponse)
async def save_message(req:ChatRequest,db:AsyncSession=Depends(get_db)):
    await crud.save_message(db,req.session_id,"user",req.message)
    # history=await crud.get_history(db,req.session_id,limit=10)
    # history_text="\n".join( f"{m.role}:{m.content}"  for m in history[:-1])

    r=await run_agent(req.message,req.session_id)

    await crud.save_message(db,req.session_id,"assistant",r)
    return ChatResponse(response=r,session_id=req.session_id)


@router.get("save_message/history/{session_id}")
async def get_history(session_id:str,db:AsyncSession=Depends(get_db),limit:int=20):
    history=await crud.get_history(db, session_id=session_id, limit=limit)
    return {
        "session_id":session_id,
        "count":len(history),
        "message":[{"role":m.role,"content":m.content,"time":m.created_at.isoformat() }  for m in history]
    }

@router.delete("save_message/history/{session_id}")
async def clear_history(session_id,db:AsyncSession=Depends(get_db)):
    count=await crud.delete_history(db,session_id)
    return {f"deleted:{count} session_id:{session_id}"}
