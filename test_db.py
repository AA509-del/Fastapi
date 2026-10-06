import asyncio

from app import crud
from app.crud import delete_history
from app.database import engine, Base, AsyncSessionLocal


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        print("写入消息")
        msg1=await crud.save_message(db,"session_1","user","你好")
        msg2 = await crud.save_message(db, "session_1", "assistant", "想小孙")
        msg3 = await crud.save_message(db, "session_001", "assistant", "你好！有什么可以帮你？")
        print(f"写入成功{msg1.id[:8]}.../{msg2.id[:8]}../ {msg3.id[:8]}...")

        print("查询历史")
        history=await crud.get_history(db,"session_1")
        for msg in history:
            print(f"{msg.role}: {msg.content}")

        print("删除历史")
        count=await delete_history(db,"session_1")
        print(f"删除{count}条")

        history_after=await crud.get_history(db,"session_1")
        print(f"删除后查询：{len(history_after)}（应为0）")

asyncio.run(main())
