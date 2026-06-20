# MiniPlane — 轻量级团队项目协作与缺陷跟踪系统

> 软件体系结构课程项目 | 基于 [Plane](https://github.com/makeplane/plane) 的简化实现

## 技术栈

| 层       | 技术                                               |
| -------- | -------------------------------------------------- |
| 前端     | Next.js 16 (React 19) + TypeScript + TailwindCSS 4 |
| 后端     | Django 5 + Django REST Framework                   |
| 数据库   | PostgreSQL 16（开发可用 SQLite）                   |
| 缓存     | Redis 7                                            |
| 文件存储 | MinIO (S3 兼容)                                    |
| 消息队列 | Celery + Redis                                     |
| 实时通信 | Django Channels + WebSocket                        |
| 包管理   | 后端 uv / 前端 pnpm                                |

## 项目结构

```
SoftwareArchitecture/
├── README.md                 ← 你在这里
├── docker-compose.yml        ← 全栈一键部署
├── .env                      ← Docker 环境变量
├── docs/                     ← T1-T4 课程文档
├── backend/                  ← Django 后端
│   ├── pyproject.toml
│   ├── manage.py
│   ├── Dockerfile
│   ├── .env.example
│   ├── config/               ← Django 配置
│   └── apps/                 ← 11 个 Django App
└── frontend/                 ← Next.js 前端
    ├── package.json
    ├── next.config.ts
    ├── Dockerfile
    └── src/
        ├── app/              ← 13 条路由
        ├── components/       ← UI 组件
        ├── lib/              ← API 客户端/工具
        ├── stores/           ← Zustand 状态
        └── types/            ← TypeScript 类型
```

---

## 方式一：Docker 全栈一键部署（推荐）

### 前置要求

| 工具           | 版本 | 检查命令           |
| -------------- | ---- | ------------------ |
| Docker Desktop | 最新 | `docker --version` |

### 启动

```bash
# 在项目根目录
docker compose up -d
```

首次启动会自动构建后端和前端镜像（约 3-5 分钟）。

| 服务          | 端口        | 说明                               |
| ------------- | ----------- | ---------------------------------- |
| frontend      | 5173        | Next.js 前端                       |
| backend       | 8000        | Django + Daphne (HTTP + WebSocket) |
| db            | 5432        | PostgreSQL 16                      |
| redis         | 6379        | 缓存 + 队列 + Channel Layers       |
| minio         | 9000 / 9001 | 对象存储 (API / Console)           |
| celery-worker | —           | 异步任务                           |

### 初始化数据库

```bash
docker compose exec backend uv run python manage.py migrate
docker compose exec backend uv run python manage.py createsuperuser
```

### 访问

- 前端：http://localhost:5173
- API 文档：http://localhost:8000/api/docs/
- MinIO Console：http://localhost:9001 (minioadmin / minioadmin)

### 停止

```bash
docker compose down
# 如需清除数据卷: docker compose down -v
```

---

## 方式二：本地开发（中间件用 Docker，前后端本地跑）

### 前置要求

| 工具           | 版本   | 检查命令           |
| -------------- | ------ | ------------------ |
| Docker Desktop | 最新   | `docker --version` |
| Python         | ≥ 3.12 | `python --version` |
| uv             | 最新   | `uv --version`     |
| Node.js        | ≥ 18   | `node --version`   |
| pnpm           | 最新   | `pnpm --version`   |

### 1. 启动中间件

```bash
cd backend
docker compose up -d
# 启动 PostgreSQL:5432, Redis:6379, MinIO:9000
```

### 2. 启动后端

```bash
cd backend
uv sync
uv run python manage.py migrate
uv run daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

### 3. 启动前端

```bash
cd frontend
pnpm install
pnpm dev -p 5173
```

访问 http://localhost:5173 开始使用

---

## 环境变量

参考 `backend/.env.example`：

```ini
DEBUG=True
SECRET_KEY=your-secret-key
DB_NAME=miniplane
DB_USER=miniplane
DB_PASSWORD=miniplane
DB_HOST=localhost
DB_PORT=5432
REDIS_URL=redis://localhost:6379/0
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=miniplane-attachments
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

前端通过 `NEXT_PUBLIC_API_URL` 指定后端地址（默认 `http://localhost:8000/api`）。

---

## 常见问题

**Q: 前端页面空白/数据不显示？**
A: 确保后端已启动在 8000 端口，并检查浏览器控制台网络请求。

**Q: WebSocket 通知不工作？**
A: 开发模式使用 `runserver` 不支持 WebSocket，需用 Daphne 启动：
```bash
uv run daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

**Q: Docker 端口冲突？**
A: 修改 `docker-compose.yml` 中的端口映射，或将本地服务先停止。
