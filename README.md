# MiniPlane — 轻量级团队项目协作与缺陷跟踪系统

> 软件体系结构课程项目 | 基于 [Plane](https://github.com/makeplane/plane) 的简化实现

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | Next.js 16 (React 19) + TypeScript + TailwindCSS 4 |
| 后端 | Django 5 + Django REST Framework |
| 数据库 | PostgreSQL 16（开发可用 SQLite） |
| 缓存 | Redis 7 |
| 文件存储 | MinIO (S3 兼容) |
| 消息队列 | Celery + Redis |
| 实时通信 | Django Channels + WebSocket |
| 包管理 | 后端 uv / 前端 pnpm |

## 项目结构

```
SoftwareArchitecture/
├── README.md                 ← 你在这里
├── docs/                     ← T1-T4 课程文档
├── backend/                  ← Django 后端
│   ├── pyproject.toml
│   ├── manage.py
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── .env.example
│   ├── config/               ← Django 配置
│   └── apps/                 ← 11 个 Django App
└── frontend/                 ← Next.js 前端
    ├── package.json
    ├── next.config.ts
    └── src/
        ├── app/              ← 13 条路由
        ├── components/       ← UI 组件
        ├── hooks/            ← 自定义 Hooks
        ├── lib/              ← API 客户端/工具
        ├── stores/           ← Zustand 状态
        └── types/            ← TypeScript 类型
```

---

## 快速开始

### 前置要求

| 工具 | 版本 | 检查命令 |
|------|------|----------|
| Docker Desktop | 最新 | `docker --version` |
| Python | ≥ 3.12 | `python --version` |
| uv | 最新 | `uv --version` |
| Node.js | ≥ 18 | `node --version` |
| pnpm | 最新 | `pnpm --version` |

### 1. 启动中间件（Docker）

```bash
cd backend
docker compose up -d
```

这会启动三个服务：

| 服务 | 端口 | 用途 |
|------|------|------|
| PostgreSQL 16 | 5432 | 主数据库 |
| Redis 7 | 6379 | 缓存 + WebSocket Channel Layers |
| MinIO | 9000 / 9001 | 文件存储 (S3) |

### 2. 启动后端

```bash
cd backend

# 安装 Python 依赖
uv sync

# 初始化数据库
uv run python manage.py migrate

# 启动 (Daphne ASGI — 支持 HTTP + WebSocket)
uv run daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

后端启动后访问：
- Swagger API 文档：http://localhost:8000/api/docs/
- Django Admin：http://localhost:8000/admin/（需先 `createsuperuser`）

### 3. 启动前端

打开**新终端**：

```bash
cd frontend
pnpm install
pnpm dev -p 5173
```

访问 http://localhost:5173 开始使用。

### 4. 使用流程

1. 打开 http://localhost:5173 → 点击「注册」
2. 创建账号后登录 → 进入仪表盘
3. 点击「创建工作空间」
4. 进入工作空间 → 「创建项目」→ 自动生成 6 列看板
5. 「创建任务」→ 拖拽卡片 → 点击查看详情 → 评论/附件/编辑

---

## API 端点概览

```
认证:
  POST /api/auth/register/      注册
  POST /api/auth/login/         登录
  POST /api/auth/logout/        登出
  GET  /api/auth/me/            当前用户
  PUT  /api/auth/me/            更新资料
  POST /api/auth/change-password/  修改密码

工作空间:
  GET  /api/workspaces/         我的工作空间
  POST /api/workspaces/         创建工作空间
  GET  /api/workspaces/{id}/    详情
  PUT  /api/workspaces/{id}/    编辑
  DELETE /api/workspaces/{id}/  删除
  GET  /api/workspaces/{id}/members/  成员列表
  POST /api/workspaces/{id}/members/  添加成员
  PUT  /api/workspaces/{id}/members/{uid}/  修改角色
  DELETE /api/workspaces/{id}/members/{uid}/  移除

项目:
  GET  /api/workspaces/{ws_id}/projects/  项目列表
  POST /api/workspaces/{ws_id}/projects/  创建项目
  GET  /api/projects/{id}/       详情
  PUT  /api/projects/{id}/       编辑
  DELETE /api/projects/{id}/     删除
  POST /api/projects/{id}/archive/   归档
  POST /api/projects/{id}/restore/   恢复

任务:
  GET  /api/projects/{proj_id}/tasks/     任务列表
  POST /api/projects/{proj_id}/tasks/     创建任务
  GET  /api/tasks/{id}/                   详情
  PUT  /api/tasks/{id}/                   编辑
  DELETE /api/tasks/{id}/                 删除
  PATCH /api/tasks/{id}/status/           变更状态
  POST /api/tasks/{id}/subtasks/          创建子任务
  GET  /api/projects/{proj_id}/task-statuses/  状态列

评论:
  GET  /api/tasks/{task_id}/comments/  列表
  POST /api/tasks/{task_id}/comments/  发表
  PUT  /api/comments/{id}/             编辑
  DELETE /api/comments/{id}/           删除

附件:
  GET  /api/tasks/{task_id}/attachments/  列表
  POST /api/tasks/{task_id}/attachments/  上传
  DELETE /api/attachments/{id}/           删除

迭代:
  GET  /api/projects/{proj_id}/iterations/  列表
  POST /api/projects/{proj_id}/iterations/  创建
  GET  /api/iterations/{id}/                详情
  PUT  /api/iterations/{id}/                编辑
  DELETE /api/iterations/{id}/              删除
  POST /api/iterations/{id}/tasks/          添加任务

模块:
  GET  /api/projects/{proj_id}/modules/  列表
  POST /api/projects/{proj_id}/modules/  创建
  GET  /api/modules/{id}/                详情
  PUT  /api/modules/{id}/                编辑
  DELETE /api/modules/{id}/              删除

统计:
  GET  /api/projects/{id}/statistics/     项目统计
  GET  /api/iterations/{id}/statistics/   迭代统计

通知:
  GET  /api/notifications/               列表
  PATCH /api/notifications/{id}/read/    标记已读
  POST /api/notifications/read-all/      全部已读

操作日志:
  GET  /api/tasks/{id}/activities/       任务日志
  GET  /api/projects/{id}/activities/    项目日志

WebSocket:
  ws://host/ws/notifications/?token=<jwt>    实时通知
  ws://host/ws/projects/{id}/?token=<jwt>    项目协作
```

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

**Q: 后端启动报数据库连接错误？**
A: 设置 `USE_SQLITE=true` 使用 SQLite 开发，无需安装 PostgreSQL。

**Q: 前端页面空白/数据不显示？**
A: 确保后端已启动在 8000 端口，并检查浏览器控制台网络请求。

**Q: WebSocket 通知不工作？**
A: 开发模式使用 `runserver` 不支持 WebSocket，需用 Daphne 启动：
```bash
uv run daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

**Q: Docker 端口冲突？**
A: 修改 `docker-compose.yml` 中的端口映射，或将本地服务先停止。
