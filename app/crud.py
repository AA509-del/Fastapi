import uuid
from datetime import datetime, timezone

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChatHistory


async def save_message(db:AsyncSession,session_id:str,role:str,content:str)->ChatHistory:
    msg=ChatHistory(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role=role,
        content=content,
        created_at=datetime.now(timezone.utc),
    )

    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg

async def get_history(db:AsyncSession,session_id:str,limit:int=20)->list[ChatHistory]:
    result=await db.execute(
        select(ChatHistory).where(ChatHistory.session_id==session_id)
        .order_by(desc(ChatHistory.created_at)).limit(limit)
    )

    rows=result.scalars().all()
    return list(reversed(rows))

async def delete_history(db:AsyncSession,session_id:str)->int:
    result=await db.execute(
        select(ChatHistory).where(ChatHistory.session_id==session_id)
    )

    rows=result.scalars().all()
    count=len(rows)
    for row in rows:
        await db.delete(row)

    await db.commit()
    return count

async def update_message(
    db: AsyncSession,
    session_id: str,          # 根据哪一条消息的id去修改
    content: str,     # 要更新成什么内容
) -> ChatHistory | None:
    """
    根据消息id更新消息内容
    返回更新后的ORM对象；找不到记录返回None
    """
    # 方式1：先查出来对象，再改属性（ORM对象方式，适合少量字段更新）
    result = await db.execute(
        select(ChatHistory).where(ChatHistory.session_id == session_id)
    )
    msg = result.scalars().first()

    if msg is None:
        # 找不到这条记录，直接返回None
        return None

    # 在内存修改对象的属性
    msg.content = content
    # 可以继续改别的字段：msg.role = "xxx"

    await db.commit()
    await db.refresh(msg)   # 刷新，拿到数据库最新状态
    return msg