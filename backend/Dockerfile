# ── MiniPlane Backend Dockerfile ────────────────────────────────
# 多阶段构建
FROM python:3.12-slim AS builder

WORKDIR /app

# 安装 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 复制依赖文件
COPY pyproject.toml .python-version ./

# 安装依赖到虚拟环境
RUN uv sync --frozen --no-dev

# ── 运行阶段 ────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# 复制虚拟环境
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# 复制应用代码
COPY . .

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/docs/ || exit 1

EXPOSE 8000

# Daphne ASGI 服务器（支持 HTTP + WebSocket）
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"]
