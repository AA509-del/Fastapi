import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from starlette.responses import JSONResponse

from app.config import settings
from app.routers import chat
from app.services import agent as agent_module
import logging

# 👇 PostgreSQL
from app.database import engine, Base
from app import models  # Register tables before create_all.

logger = logging.getLogger("uvicorn")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # AsyncSqliteSaver 必须在应用运行期间一直存活；若此处 async with 过早结束，检查点会关闭，
    # 再次 ainvoke 时 aiosqlite 易出现 RuntimeError: threads can only be started once
    async with AsyncSqliteSaver.from_conn_string(settings.db_path) as memory:
        agent_module.agent_app = agent_module.graph.compile(checkpointer=memory)

        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ PostgreSQL 初始化成功")
        except Exception as e:
            logger.error(f"PostgreSQL 初始化失败：{e}")

        yield

    # Sqlite 检查点已关闭后，再释放 SQLAlchemy 连接池
    await engine.dispose()

app = FastAPI(
    title="FastAPI + LangGraph 聊天接口示例",
    version="1.0.0",
    lifespan=lifespan,
    description="基于智谱 GLM 的聊天接口，包含天气、示例景点推荐和预算计算工具"
)

@app.middleware("http")
async def log_requests(request:Request,call_next):
    start_time=time.time()
    response=await call_next(request)
    use_time=(time.time()-start_time) * 1000
    logger.info(
        f"{request.method}{request.url.path}|"
        f"状态码：{response.status_code} | 耗时：{use_time:.0f}ms"
    )
    return response

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request:Request,exc):
    return JSONResponse(
        status_code=422,
        content={
            "error":"参数错误",
            "detail":exc.errors()
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request:Request,exc:Exception):
    logger.error(f"全局异常：{str(exc)}",exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error":"服务内部错误，请稍后重试"}
    )

app.include_router(chat.router)

@app.get("/health")
def health():
    return {"status":"OK"}
