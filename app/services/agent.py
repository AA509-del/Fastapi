import sqlite3
from langchain_community.chat_models import ChatZhipuAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import add_messages, StateGraph,END
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel
from typing import Annotated, Optional, Any
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, BaseMessage
from langchain_core.tools import tool
import requests
import os
import asyncio

from app.config import settings

load_dotenv()

# ------------------------------
# 工具 1：天气（修复：返回字符串！）
# ------------------------------
@tool
def get_weather(city: str) -> str:
    """查询城市天气"""
    if not settings.seniverse_api_key:
        return "天气服务未配置 SENIVERSE_API_KEY"
    try:
        url = "https://api.seniverse.com/v3/weather/now.json"
        params = {
            "location": city,
            "key": settings.seniverse_api_key,
            "language": "zh-Hans",
            "unit": "c",
        }
        r = requests.get(url, params=params, timeout=15)
        data = r.json()
        result = data["results"][0]
        city_name = result["location"]["name"]
        weather_text = result["now"]["text"]
        temperature = result["now"]["temperature"]
        last_update = result["last_update"]
        return f"城市：{city_name}\n天气：{weather_text}\n温度：{temperature}℃\n更新：{last_update.replace('T', ' ')[:16]}"
    except Exception as e:
        return f"天气查询失败：{str(e)}"

# ------------------------------
# 工具 2：景点推荐
# ------------------------------
@tool
def recommend_attractions(city: str) -> str:
    """推荐城市热门景点"""
    spots = {"北京": "长城", "深圳": "世界之窗"}
    return f"{city}推荐景点：{spots.get(city, '未知')}"

# ------------------------------
# 工具 3：预算计算
# ------------------------------
@tool
def calculate_budget(day: int, price_every_day: int) -> str:
    """预算游玩几天的花费"""
    total = day * price_every_day
    return f"游玩{day}天，预计总花费：{total}元"

tools = [get_weather, recommend_attractions, calculate_budget]

# ------------------------------
# 状态（统一大小写，避免错误）
# ------------------------------
class AgentState(BaseModel):
    messages: Annotated[list[BaseMessage], add_messages]

# ------------------------------
# LLM（显式传入密钥：与 app.config 一致，支持 ZHIPU_API_KEY / ZHIPUAI_API_KEY，避免仅认环境变量名 ZHIPUAI_API_KEY）
# ------------------------------
llm = ChatZhipuAI(
    model="glm-4.7",
    temperature=0.1,
    zhipuai_api_key=settings.zhipu_api_key,
).bind_tools(tools)

def call_llm(state: AgentState):
    print("🤖 LLM 思考中...")
    res = llm.invoke(state.messages)
    return {"messages": [res]}

# ------------------------------
# 构建图
# ------------------------------
graph = StateGraph(AgentState)
graph.add_node("llm", call_llm)
graph.add_node("tools", ToolNode(tools))
graph.set_entry_point("llm")
graph.add_conditional_edges("llm", tools_condition)
graph.add_edge("tools", "llm")

# ------------------------------
# 同步：记忆存储
# ------------------------------
# conn = sqlite3.connect("checkpointer.db", check_same_thread=False)
# memory = SqliteSaver(conn)
# agent_app = graph.compile(checkpointer=memory)  # 改名避免和 FastAPI app 冲突！


agent_app:Optional[Any]=None

async def run_agent(message:str,session_id:str):
    if  agent_app is None:
        raise RuntimeError("Agent 未初始化：请用 uvicorn 启动以执行 lifespan")
    config={"configurable":{"thread_id":session_id}}
    res= await agent_app.ainvoke(
        {"messages":[HumanMessage(content=message)]},
        config=config
    )
    return res["messages"][-1].content

async def run_agent_stream(message:str,session_id:str):
    if  agent_app is None:
        raise RuntimeError("Agent 未初始化：请用 uvicorn 启动以执行 lifespan")
    config={"configurable":{"thread_id":session_id}}
    async for chunk in agent_app.astream({"messages":[HumanMessage(content=message)]},
        config=config):
        if "llm" in chunk:
            content=chunk["llm"]["messages"][0].content
            if content:
                yield f"data:{content}\n\n"

                await asyncio.sleep(0.5)

    yield "data:[DONE]\n\n"
