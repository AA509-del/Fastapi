# 旅游助手 API（LangGraph + FastAPI）

异步 AI 旅游助手：提供非流式 `/chat` 与流式 `/chat/stream`，使用 LangGraph + 智谱 GLM。SQLite 保存会话 checkpoint，PostgreSQL 保存聊天历史，Redis 缓存回答。

## 接口文档（本地）

启动服务后访问：

- **Swagger UI**：<http://127.0.0.1:8000/docs>
- **ReDoc**：<http://127.0.0.1:8000/redoc>

（若启动时使用 `--port 8001`，将地址中的端口改为 `8001`。）

## 环境要求

- Python 3.10+
- 已安装依赖：`pip install -r requirements.txt`
- PostgreSQL 和 Redis（可通过 Docker Compose 启动）

## 配置说明（`.env`）

复制 `.env.example` 为 `.env`，按表填写：

| 变量 | 说明 |
|------|------|
| `ZHIPU_API_KEY` 或 `ZHIPUAI_API_KEY` | 智谱 API Key，**必填**（二选一，与 `app/config.py` 一致） |
| `SENIVERSE_API_KEY` 或 `SENIVERSE_KEY` | 心知天气 Key；不填时天气工具会提示未配置 |
| `OPENAI_API_KEY` | 预留，可留空 |
| `DB_PATH` | Checkpoint 数据库路径，默认 `checkpointer.db` |
| `DATABASE_URL` | PostgreSQL 异步连接地址 |
| `REDIS_URL` | Redis 连接地址 |
| `PORT` | 文档默认端口说明用；实际以启动命令为准 |

配置由 `app/config.py`（pydantic-settings）加载，**请勿将 `.env` 提交到 Git**。

## Docker Compose 启动

复制 `.env.example` 为 `.env`，填写智谱 Key，然后运行：

```bash
docker compose up --build
```

接口文档位于 <http://127.0.0.1:8002/docs>。Compose 会同时启动 PostgreSQL 和 Redis。

## 本地 Python 启动

先启动 PostgreSQL 和 Redis，并在 `.env` 中设置它们的连接地址。在项目根目录（与 `app/` 同级）安装依赖并启动：

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

指定端口示例：

```bash
uvicorn app.main:app --reload --port 8001
```

## 健康检查与聊天

- `GET /health` → `{"status":"OK"}`
- `POST /chat` → JSON：`message`、`session_id`
- `POST /chat/stream` → SSE（`text/event-stream`）

## 项目结构

```text
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI、lifespan、中间件与异常处理
│   ├── config.py            # pydantic-settings
│   ├── database.py          # PostgreSQL 连接
│   ├── models.py            # 聊天历史模型
│   ├── crud.py              # 聊天历史操作
│   ├── cache.py             # Redis 缓存
│   ├── routers/
│   │   └── chat.py          # /chat、/chat/stream
│   └── services/
│       └── agent.py         # LangGraph Agent
├── alembic/                 # 数据库迁移
├── .env                     # 本地密钥（不提交）
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .gitignore
└── README.md
```

## 上传 GitHub

提交 `.env.example`，不要提交 `.env`、`*.db`、SQLite 的 `-wal`/`-shm` 文件或本地缓存目录；这些文件已列入 `.gitignore`。如果曾在别处公开过 API Key，请先在服务商后台轮换。
