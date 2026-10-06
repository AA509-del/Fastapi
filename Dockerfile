# 基于官方 Python 3.11 精简镜像，体积小、适合部署
FROM python:3.11-slim

# 容器内日志立即输出到 stdout/stderr，便于 docker logs 查看
ENV PYTHONUNBUFFERED=1
# 不在镜像内生成 .pyc，减少无关文件
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# 先复制依赖清单并安装（文件必须存在于构建上下文中，不能用不存在的 /tmp/requirements.txt）
COPY requirements.txt .
RUN pip install --no-cache-dir  -r requirements.txt

# 再复制应用源码
COPY . .

EXPOSE 8000

# 监听 0.0.0.0 才能从宿主机通过端口映射访问
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
