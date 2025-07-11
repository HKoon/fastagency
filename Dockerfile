FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖（包括PostgreSQL客户端）
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY pyproject.toml .

# 安装Python依赖（包括数据库相关）
RUN pip install --no-cache-dir -e . && \
    pip install --no-cache-dir \
    psycopg2-binary \
    sqlalchemy \
    asyncpg \
    uvicorn[standard]

# 复制应用代码
COPY . .

# 创建非root用户
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# 暴露端口（Railway会自动设置PORT环境变量）
EXPOSE $PORT

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# 启动命令（使用自定义启动脚本）
CMD ["python", "start_railway.py"]