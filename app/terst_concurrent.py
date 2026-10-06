"""
    并发压测示例：同一文件内演示两种调用方式（二选一运行，见文件末尾 CHAT_CLIENT_MODE）。

    1) JSON 非流式 — POST /chat
       - 响应 Content-Type: application/json，一次返回完整 body。
       - 客户端用 r.raise_for_status() 后 r.json() 即可。
       - 适合：接口对接、脚本、不关心打字机效果。

    2) SSE 流式 — POST /chat/stream
       - 响应 Content-Type: text/event-stream，正文为多段 data: ... 与结尾 data:[DONE]。
       - 不能用 r.json()；需按 SSE 事件读（本示例用 \\n\\n 切段，再合并 data: 行）。
       - 适合：聊天前端、边生成边展示；并发时单次也可能较慢，超时宜放宽。
    """

import asyncio
import httpx

BASE = "http://127.0.0.1:8001"
# 流式/多轮 LLM 可能很慢，并发时读超时适当加大；connect 单独限制便于快速发现「连不上」
TIMEOUT = httpx.Timeout(600.0, connect=15.0)


# ---------- 方式一：JSON（/chat）----------
async def send_request_json(
        client: httpx.AsyncClient, session_id: str, message: str
) -> dict:
    """
    非流式：服务端返回单个 JSON 对象（与 FastAPI 的 chatresponse 一致）。
    """
    r = await client.post(
        f"{BASE}/chat",
        json={"message": message, "session_id": session_id},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


# ---------- 方式二：SSE（/chat/stream）----------
async def send_request_sse(
        client: httpx.AsyncClient, session_id: str, message: str
) -> dict:
    """
    流式：响应为 SSE，不是整段 JSON。
    按事件解析：事件之间以空行（\\n\\n）分隔；同一事件内多行 data: 需拼接（正文含换行时不能用简单按行 if line.startswith("data:") 扫一遍就完事）。
    这里拼完后仍返回 dict，字段与 JSON 方式接近，便于共用下面的打印逻辑。
    """
    async with client.stream(
            "POST",
            f"{BASE}/chat/stream",
            json={"message": message, "session_id": session_id},
            timeout=TIMEOUT,
    ) as r:
        r.raise_for_status()
        buf = ""
        parts: list[str] = []
        async for piece in r.aiter_text():
            buf += piece
            while "\n\n" in buf:
                event, buf = buf.split("\n\n", 1)
                data_lines: list[str] = []
                for line in event.split("\n"):
                    if line.startswith("data:"):
                        data_lines.append(line[5:].lstrip())
                if not data_lines:
                    continue
                payload = "\n".join(data_lines)
                if payload.strip() == "[DONE]":
                    return {"session_id": session_id, "response": "".join(parts)}
                parts.append(payload)
        return {"session_id": session_id, "response": "".join(parts)}


# ---------- 入口：切换模式 ----------
# "json"：走 /chat； "sse"：走 /chat/stream（需服务端流式接口正常产出 data: 片段）
CHAT_CLIENT_MODE = "json"


async def main() -> None:
    sender = send_request_json if CHAT_CLIENT_MODE == "json" else send_request_sse
    mode_name = "JSON /chat" if CHAT_CLIENT_MODE == "json" else "SSE /chat/stream"
    print(f"开始并发发送 5 个请求（{mode_name}）…")

    async with httpx.AsyncClient() as client:
        tasks = [
            sender(client, f"user_{i}", f"介绍下深圳小吃，用户{i}")
            for i in range(5)
        ]
        results = await asyncio.gather(*tasks)

        for idx, res in enumerate(results):
            print(f"\n====== 用户 {idx + 1} 返回结果 ======")
            print(res)

if __name__ == "__main__":
    asyncio.run(main())


# import httpx
# import asyncio
#
# TIMEOUT=httpx.Timeout(600.0,connect=15.0)
# async def send_request(client:httpx.AsyncClient,message:str,session_id:str):
#     r=await client.post(
#         url="http://localhost:8001/chat",
#         json={"message":message,"session_id":session_id},
#         timeout=TIMEOUT
#     )
#     return r.json()
#
# async def main():
#     print("开始发送并发请求：")
#     async with httpx.AsyncClient() as client:
#         tasks=[send_request(client,f"介绍下深圳小吃，用户{i}"  ,f"user_{i}" )
#                for i in range(5)]
#         results=await asyncio.gather(*tasks)
#         for i,res in enumerate(results):
#             print(f"\n====== 用户 {i + 1} 返回结果 ======")
#             print(res)
