# MiniPlane 项目架构文档

> **MiniPlane** — 轻量级团队项目协作与缺陷跟踪系统  
> 软件体系结构课程项目，基于 Plane 的简化实现  
> 最后更新: 2026-06-20

---

## 目录

1. [项目概述](#1-项目概述)
2. [技术栈总览](#2-技术栈总览)
3. [整体架构](#3-整体架构)
4. [数据模型](#4-数据模型)
5. [后端架构](#5-后端架构)
6. [前端架构](#6-前端架构)
7. [基础设施与部署](#7-基础设施与部署)
8. [API 设计](#8-api-设计)
9. [安全设计](#9-安全设计)
10. [测试体系](#10-测试体系)
11. [已知问题与限制](#11-已知问题与限制)

---

## 1. 项目概述

MiniPlane 是一个面向小型团队的轻量级项目协作与缺陷跟踪系统，提供从工作空间、项目、看板到任务管理的完整协作链路。核心功能包括：

- **多团队支持** — 工作空间隔离，每个工作空间包含多个项目
- **看板管理** — 自定义状态列，拖拽式任务流转
- **迭代管理** — Sprint 冲刺计划，燃尽图统计
- **模块管理** — 功能模块分类
- **任务协作** — 评论、附件、子任务、活动日志
- **实时通知** — WebSocket 推送任务分配、状态变更等通知
- **权限系统** — 工作空间/项目两级 RBAC 权限控制

---

## 2. 技术栈总览

| 层           | 技术                                                 | 用途                                |
| ------------ | ---------------------------------------------------- | ----------------------------------- |
| **前端**     | Next.js 16 (React 19) + TypeScript 5 + TailwindCSS 4 | SSR/SPA 混合架构                    |
| **后端**     | Django 5 + Django REST Framework + Daphne (ASGI)     | REST API + WebSocket                |
| **数据库**   | PostgreSQL 16                                        | 关系数据存储                        |
| **缓存**     | Redis 7                                              | 缓存、Celery Broker、Channels Layer |
| **文件存储** | MinIO (S3-compatible)                                | 附件存储                            |
| **消息队列** | Celery + Redis                                       | 异步任务处理                        |
| **反向代理** | Nginx 1.27                                           | 路由分发、静态资源缓存              |
| **容器化**   | Docker Compose                                       | 全栈编排部署                        |

### 包管理

| 环境 | 工具   |
| ---- | ------ |
| 后端 | `uv`   |
| 前端 | `pnpm` |

---

## 3. 整体架构

### 3.1 系统架构图

```
                         Internet (Port 80)
                              |
                         [nginx:1.27]
                        /       |       \
                  /api/*     /ws/*       /* (catch-all)
                      |         |           |
                [backend:8000]          [frontend:3000]
               Django 5 + Daphne       Next.js 16
               ASGI (HTTP + WS)        SSR + SPA
              /        |        \
         [db:5432] [redis:6379]  [minio:9000]
        PostgreSQL    Cache/        S3 Storage
                     Broker
                       |
                 [celery-worker]
                 异步任务处理
```

### 3.2 设计决策

| 决策           | 选择                         | 理由                                               |
| -------------- | ---------------------------- | -------------------------------------------------- |
| ASGI 服务器    | Daphne                       | 同时处理 HTTP 和 WebSocket，单进程部署             |
| WebSocket 鉴权 | JWT via Query Param          | 避免 cookies，适合无状态 API                       |
| 文件存储       | MinIO (S3 API)               | 兼容 S3 生态，易于扩展                             |
| API 统一响应   | APIRenderer                  | 所有响应包装为 `{success, data, message}` 格式     |
| 状态管理       | Zustand + React Query        | Zustand 管理客户端状态，React Query 管理服务端缓存 |
| 认证           | JWT (access 2h + refresh 7d) | 无状态，支持轮换与黑名单                           |

### 3.3 领域模型关系

```
Workspace 1──* Project
Workspace 1──* WorkspaceMember (User)
Project 1──* ProjectMember (User)
Project 1──* TaskStatus         ← 看板列
Project 1──* Task               ← 核心实体
Project 1──* Iteration          ← Sprint
Project 1──* Module             ← 功能模块
Task 1──* Comment
Task 1──* Attachment
Task ──1 Task (parent)          ← 子任务
Task 1──* Activity              ← 审计日志
User 1──* Notification
```

---

## 4. 数据模型

### 4.1 核心实体

| 实体                | 表名                         | 字段                                                      | 说明                               |
| ------------------- | ---------------------------- | ------------------------------------------------------------- | ---------------------------------- |
| **User**            | `accounts_user`              | id(UUID), email(unique), name, avatar                         | 自定义用户模型，email 作为登录标识 |
| **Workspace**       | `workspaces_workspace`       | id(UUID), name, slug(unique), owner                           | 顶层组织容器                       |
| **WorkspaceMember** | `workspaces_workspacemember` | workspace, user, role(admin/member/guest)                     | 多对多中间表                       |
| **Project**         | `projects_project`           | id(UUID), workspace, name, identifier, lead                   | 工作空间下的项目                   |
| **ProjectMember**   | `projects_projectmember`     | project, user, role(admin/member/viewer)                      | 多对多中间表                       |
| **TaskStatus**      | `tasks_taskstatus`           | project, name, color, order, type                             | 看板列，类型决定系统行为           |
| **Task**            | `tasks_task`                 | project, title, priority, status, assignee, iteration, module | 核心任务实体                       |
| **Iteration**       | `iterations_iteration`       | project, name, start_date, end_date, is_active                | Sprint 迭代                        |
| **Module**          | `modules_module`             | project, name, lead                                           | 功能模块分类                       |
| **Comment**         | `comments_comment`           | task, author, content                                         | 任务评论                           |
| **Attachment**      | `attachments_attachment`     | task, uploader, file, filename, size, mime_type               | 文件附件                           |
| **Notification**    | `notifications_notification` | recipient, actor, type, message, reference                    | 系统通知                           |
| **Activity**        | `activities_activity`        | task/project, actor, action, field, old/new_value             | 审计日志                           |

### 4.2 约束

- 所有实体使用 **UUID 主键**
- 中文 `verbose_name`（如 `"用户"`、`"任务"`）
- 外键删除策略：主要为 `CASCADE`，实体为 `PROTECT`（Workspace.owner, Task.status）或 `SET_NULL`（assignee, module, iteration）
- `Iteration.end_date` > `start_date`（检查约束）
- 唯一约束：`WorkspaceMember(workspace, user)`、`ProjectMember(project, user)`、`Project(workspace, identifier)`、`Module(project, name)`、`TaskStatus(project, name)`

### 4.3 TaskStatus 类型系统

| 类型        | 用途   | 默认列         |
| ----------- | ------ | -------------- |
| `backlog`   | 待办池 | Backlog        |
| `unstarted` | 未开始 | 待办           |
| `started`   | 进行中 | 进行中         |
| `completed` | 已完成 | 待评审、已完成 |
| `cancelled` | 已取消 | 已取消         |

项目创建时自动生成 6 个默认状态列。

---

## 5. 后端架构

### 5.1 应用结构

```
backend/
├── config/                  # Django 项目配置
│   ├── settings.py          # 全局设置
│   ├── urls.py              # URL 路由
│   ├── asgi.py              # ASGI 入口
│   ├── wsgi.py              # WSGI 入口
│   ├── celery.py            # Celery 配置
│   └── routing.py           # WebSocket 路由
├── apps/
│   ├── core/                # 基础框架
│   │   ├── renderers.py     # APIRenderer
│   │   ├── exceptions.py    # 异常处理
│   │   ├── permissions.py   # 权限类
│   │   ├── pagination.py    # 分页
│   │   ├── websocket.py     # WS JWT 工具
│   │   └── management/      # seed_data 命令
│   ├── accounts/            # 用户认证
│   ├── workspaces/          # 工作空间
│   ├── projects/            # 项目
│   ├── tasks/               # 任务 (核心)
│   ├── comments/            # 评论
│   ├── attachments/         # 附件
│   ├── iterations/          # 迭代
│   ├── modules/             # 模块
│   ├── notifications/       # 通知
│   ├── activities/          # 操作日志
│   └── statistics/          # 统计
├── tests/                   # 集成测试
└── manage.py
```

### 5.2 应用职责

| App               | 类型     | 视图                                       | URL 路径                                                                |
| ----------------- | -------- | ------------------------------------------ | ----------------------------------------------------------------------- |
| **core**          | 基础设施 | —                                          | —                                                                       |
| **accounts**      | 认证     | AuthViewSet (GenericViewSet)               | `/api/auth/register/`, `/login/`, `/me/`, `/change-password/`           |
| **workspaces**    | 核心业务 | WorkspaceViewSet (ModelViewSet)            | `/api/workspaces/` + members CRUD                                       |
| **projects**      | 核心业务 | ProjectViewSet (ModelViewSet)              | `/api/workspaces/{wsId}/projects/` + archive/restore/members            |
| **tasks**         | 核心业务 | TaskViewSet (ModelViewSet)                 | `/api/projects/{projId}/tasks/` + status/statuses/subtasks              |
| **comments**      | 辅助     | CommentViewSet (ModelViewSet)              | `/api/tasks/{taskId}/comments/`                                         |
| **attachments**   | 辅助     | AttachmentViewSet (ModelViewSet)           | `/api/tasks/{taskId}/attachments/`                                      |
| **iterations**    | 核心业务 | IterationViewSet (ModelViewSet)            | `/api/projects/{projId}/iterations/` + add_tasks                        |
| **modules**       | 核心业务 | ModuleViewSet (ModelViewSet)               | `/api/projects/{projId}/modules/`                                       |
| **notifications** | 辅助     | NotificationViewSet (ReadOnlyModelViewSet) | `/api/notifications/` + mark_read/read_all                              |
| **activities**    | 辅助     | ActivityViewSet (ReadOnlyModelViewSet)     | `/api/tasks/{taskId}/activities/`, `/api/projects/{projId}/activities/` |
| **statistics**    | 工具     | 函数视图                                   | `/api/projects/{pk}/statistics/`, `/api/iterations/{pk}/statistics/`    |

### 5.3 API 统一响应格式

所有响应通过 `APIRenderer` 包装：

**成功响应：**
```json
{
    "success": true,
    "data": { ... },
    "message": ""
}
```

**分页响应：**
```json
{
    "success": true,
    "data": [ ... ],
    "message": "",
    "pagination": {
        "page": 1,
        "page_size": 20,
        "total": 150,
        "total_pages": 8
    }
}
```

**错误响应：**
```json
{
    "success": false,
    "message": "邮箱或密码错误",
    "errors": {
        "email": ["该邮箱已注册"],
        "password": []
    }
}
```

### 5.4 认证与权限

| 组件             | 实现                                                                     |
| ---------------- | ------------------------------------------------------------------------ |
| **认证方式**     | JWT (SimpleJWT) — Access Token 2h + Refresh Token 7d                     |
| **Token 轮换**   | 启用，刷新时自动轮换并黑名单旧 Token                                     |
| **默认权限**     | `IsAuthenticated` (全局 DRF 设置)                                        |
| **公开端点**     | `register`、`login` — `AllowAny`                                         |
| **工作空间权限** | `IsWorkspaceAdmin` — 修改/删除；`IsWorkspaceMember` — 读                 |
| **项目权限**     | `IsProjectAdmin` — 修改/删除/归档；`IsProjectMember` — 读                |
| **任务权限**     | `IsTaskAssigneeOrProjectAdmin` — 修改/删除；`IsProjectMember` — 状态变更 |
| **对象级权限**   | Comment 仅作者可编辑；Notification 仅接收者可操作                        |

### 5.5 WebSocket 架构

| Consumer                 | 路径                       | 组                     | 功能                   |
| ------------------------ | -------------------------- | ---------------------- | ---------------------- |
| **NotificationConsumer** | `ws/notifications/`        | `user_{user.id}`       | 推送通知消息、标记已读 |
| **ProjectConsumer**      | `ws/projects/{projectId}/` | `project_{project.id}` | 看板拖动广播、项目事件 |

- 认证：JWT 通过 URL 查询参数传递 (`?token=xxx`)
- Channel Layer：基于 Redis (`channels_redis`)
- 连接生命周期：24h Nginx 超时

### 5.6 序列化器设计模式

每个 app 通常有两个序列化器：

- `*Serializer` — 带嵌套字段的读取序列化器（如 `assignee_name`、`status_color`）
- `*CreateSerializer` — 仅包含可写字段的创建序列化器，覆写 `create()` 注入上下文

序列化器：

| 序列化器                     | 特殊字段                                                        | 说明                                  |
| ---------------------------- | --------------------------------------------------------------- | ------------------------------------- |
| `TaskSerializer`             | `status_name`, `assignee_name`, `module_name`, `iteration_name` | 完整关系展开                          |
| `TaskListSerializer`         | 轻量版本                                                        | 列表视图优化                          |
| `TaskStatusChangeSerializer` | —                                                               | 原子性状态变更 + Activity 记录 + 通知 |
| `IterationSerializer`        | `task_count`, `completed_count`                                 | 迭代统计快捷属性                      |
| `ModuleSerializer`           | `lead_name`, `task_count`                                       | 模块统计                              |
| `ProjectSerializer`          | `lead_name`, `member_count`, `task_count`                       | 项目聚合信息                          |

### 5.7 异常处理

全局异常处理器 `custom_exception_handler`：
- 捕获 DRF 的 `ValidationError`、`AuthenticationFailed`、`PermissionDenied`、`NotFound` 等
- 统一格式化为 `{success, message, errors}`
- 递归提取第一条错误消息
- 兼容 `ListSerializer` 的非字段错误

### 5.8 分页

`StandardPagination` (PageNumberPagination)：
- 默认 20 条/页，最大 100 条
- 参数：`?page=1&page_size=20`
- 返回：`{results, page, page_size, count, total_pages}`

---

## 6. 前端架构

### 6.1 目录结构

```
frontend/src/
├── app/
│   ├── layout.tsx                   # 根布局 (dark mode, fonts)
│   ├── providers.tsx                # React Query + Auth 初始化
│   ├── globals.css                  # Tailwind v4 设计令牌
│   ├── page.tsx                     # / 首页 (重定向)
│   ├── login/page.tsx               # 登录页
│   ├── register/page.tsx            # 注册页
│   └── (authenticated)/             # 受保护路由组
│       ├── layout.tsx               # 认证布局 (Sidebar + TopBar)
│       ├── dashboard/page.tsx       # 工作空间列表
│       ├── workspaces/[wsId]/page.tsx  # 项目列表
│       ├── settings/page.tsx        # 用户设置
│       └── projects/[projId]/
│           ├── layout.tsx           # 项目子布局 (Tab 导航)
│           ├── page.tsx             # 看板视图 (304 行)
│           ├── list/page.tsx        # 列表视图
│           ├── iterations/page.tsx  # 迭代管理
│           ├── modules/page.tsx     # 模块管理
│           └── settings/page.tsx    # 项目设置 + 统计
├── components/
│   ├── layout/
│   │   ├── Sidebar.tsx              # 侧边栏 (240px)
│   │   └── TopBar.tsx               # 顶栏 (56px, 通知中心)
│   └── ui/
│       ├── Button.tsx               # 按钮 (4 变体 × 3 尺寸)
│       ├── Modal.tsx                # 弹窗 (ESC/遮罩关闭)
│       ├── Input.tsx                # 输入框 (带标签/错误)
│       ├── Badge.tsx                # 标签
│       ├── Avatar.tsx               # 头像 (图片/首字母)
│       └── Spinner.tsx              # 加载动画
├── lib/
│   ├── api.ts                       # Axios 实例 + 拦截器
│   ├── auth.ts                      # localStorage 认证持久化
│   ├── utils.ts                     # 工具 (cn, formatDate, timeAgo, priorityColor)
│   └── websocket.ts                 # WebSocket 客户端
├── stores/
│   ├── authStore.ts                 # 认证状态 (Zustand)
│   ├── appStore.ts                  # UI 状态 (侧边栏、详情面板)
│   └── notificationStore.ts         # 通知状态
└── types/index.ts                   # 全部 TypeScript 定义 (258 行)
```

### 6.2 页面路由与功能映射

| 路由                            | 页面      | 功能                       | 数据依赖                                        |
| ------------------------------- | --------- | -------------------------- | ----------------------------------------------- |
| `/`                             | 首页      | 自动重定向                 | authStore                                       |
| `/login`                        | 登录      | 双面板登录页               | POST `/auth/login/`                             |
| `/register`                     | 注册      | 注册+自动登录              | POST `/auth/register/`                          |
| `/dashboard`                    | 工作空间  | CRUD 工作空间              | GET `/workspaces/`                              |
| `/workspaces/[wsId]`            | 项目列表  | 项目 CRUD、成员管理、归档  | GET `/workspaces/{wsId}/projects/`, `/members/` |
| `/projects/[projId]`            | 看板      | 拖拽、筛选、创建任务/状态  | 多查询（项目、状态、迭代、模块、任务）          |
| `/projects/[projId]/list`       | 列表      | 表格视图                   | GET `/tasks/` (view=list)                       |
| `/projects/[projId]/iterations` | 迭代      | 迭代 CRUD、任务分配        | 迭代 + 任务列表                                 |
| `/projects/[projId]/modules`    | 模块      | 模块 CRUD、任务分配        | 模块 + 任务列表                                 |
| `/projects/[projId]/settings`   | 设置+统计 | 图表、成员、活动日志       | GET `/statistics/`                              |
| `/tasks/[taskId]`               | 任务详情  | 编辑、评论、附件、活动日志 | 任务 + 评论 + 附件 + 活动                       |
| `/settings`                     | 个人设置  | 修改姓名/密码              | PUT `/auth/me/`, POST `/auth/change-password/`  |

### 6.3 状态管理层

```
┌─────────────────────────────────────────────────┐
│                  React Query                      │
│  (服务端状态缓存，staleTime=30s，retry=1)          │
│  - 自动重新获取、缓存失效、乐观更新                 │
├─────────────────────────────────────────────────┤
│                 Zustand Stores                    │
│  ┌─────────────┐ ┌──────────┐ ┌────────────────┐ │
│  │  authStore   │ │ appStore │ │ notificationStore│
│  │  user        │ │ sidebar  │ │ notifications[] │
│  │  isAuth      │ │ taskId   │ │ unreadCount     │
│  │  login/logout│ │ toggle   │ │ add/markRead    │
│  └─────────────┘ └──────────┘ └────────────────┘ │
├─────────────────────────────────────────────────┤
│               localStorage                        │
│  access_token, refresh_token, user (JSON)         │
└─────────────────────────────────────────────────┘
```

### 6.4 API 客户端架构

Axios 拦截器链：

```
请求 → 1. 注入 Authorization: Bearer token
        2. 发送请求
        3. 收到响应
        4. 响应拦截器
            ├─ success: 解包 data (response.data = body.data)
            ├─ 401: 尝试刷新 Token
            │   ├─ 成功: 重放请求
            │   └─ 失败: 清除状态 → 重定向 /login
            └─ 403: GET 请求重定向 /dashboard
```

- 并发 401 请求排队（只刷新一次 Token）
- 刷新失败仅拒绝原始请求，不批量清除

### 6.5 WebSocket 客户端

```typescript
wsClient.connect(path)  // 单例模式
  ├─ 自动重连 (指数退避: 3s → 6s → 12s → ... → max 60s, 最多 10 次)
  ├─ 每次重连读取最新 token
  ├─ wsClient.on(action, handler)  // 订阅消息
  └─ wsClient.send(data)           // 发送 JSON
```

### 6.6 前端设计系统

基于 Tailwind CSS v4 CSS 配置，无传统 `tailwind.config.ts`：

| 令牌                | 值                    | 用途       |
| ------------------- | --------------------- | ---------- |
| `--color-accent`    | `#f59e0b` (amber)     | 主色调     |
| `--color-surface-0` | `#08080d`             | 最深层背景 |
| `--color-surface-1` | `#0f0f15`             | 基础背景   |
| `--color-surface-2` | `#14141f`             | 卡片背景   |
| `--color-surface-3` | `#1e1e2e`             | 高亮背景   |
| `--color-border`    | `#252530` / `#303045` | 边框       |
| `--color-fg`        | `#e4e4e7`             | 前景文本   |
| `--color-muted`     | `#71718a`             | 灰色文本   |

优先级颜色映射：`urgent→red`, `high→orange`, `medium→amber`, `low→green`

---

## 7. 基础设施与部署

### 7.1 Docker Compose 服务

| 服务          | 镜像                      | 端口                       | 依赖              |
| ------------- | ------------------------- | -------------------------- | ----------------- |
| db            | postgres:16-alpine        | 5432                       | —                 |
| redis         | redis:7-alpine            | 6379                       | —                 |
| minio         | minio/minio:latest        | 9000 (API), 9001 (Console) | —                 |
| minio-init    | minio/mc:latest           | —                          | minio (healthy)   |
| backend       | 自建 (uv+Daphne)          | 8000                       | db, redis, minio  |
| celery-worker | 同 backend 镜像           | —                          | redis, db         |
| frontend      | 自建 (Next.js standalone) | 3000                       | backend           |
| nginx         | nginx:1.27-alpine         | **80** (对外)              | frontend, backend |

### 7.2 Nginx 路由表

| 路径             | 目标                | 特殊配置                                     |
| ---------------- | ------------------- | -------------------------------------------- |
| `/_next/static/` | frontend:3000       | 缓存 1 年，immutable                         |
| `/static/`       | 本地 `/app/static/` | 缓存 30 天                                   |
| `/api/`          | backend:8000        | read_timeout 60s                             |
| `/media/`        | backend:8000        | —                                            |
| `/ws/`           | backend:8000        | HTTP/1.1, Upgrade, read_timeout 86400s (24h) |
| `/admin/`        | backend:8000        | —                                            |
| `/` (fallback)   | frontend:3000       | —                                            |

### 7.3 环境变量

| 变量                   | 默认值（Docker）      | 默认值（本地）           |
| ---------------------- | --------------------- | ------------------------ |
| `DEBUG`                | false                 | True                     |
| `SECRET_KEY`           | change-this...        | dev 密钥                 |
| `DB_HOST`              | db                    | localhost                |
| `REDIS_URL`            | redis://redis:6379/0  | redis://localhost:6379/0 |
| `CELERY_BROKER_URL`    | redis://redis:6379/1  | 同上                     |
| `MINIO_ENDPOINT`       | minio:9000            | localhost:9000           |
| `CORS_ALLOWED_ORIGINS` | http://localhost:5173 | http://localhost:3000    |
| `NGINX_PORT`           | 5173                  | —                        |

**重要：** `NEXT_PUBLIC_*` 变量在 Next.js 中是构建时注入（Docker build args），非运行时环境变量。Dockerfile 中声明为 `ARG` + `ENV`。

### 7.4 Dockerfile 策略

| 服务         | 策略   | 基础镜像         | 特点                                            |
| ------------ | ------ | ---------------- | ----------------------------------------------- |
| **backend**  | 单阶段 | python:3.12-slim | uv 二进制注入，`uv sync --frozen`               |
| **frontend** | 多阶段 | node:22-alpine   | deps → builder → runner，仅拷贝 standalone 产物 |

### 7.5 部署方式

```bash
# Docker 全栈部署
docker compose up -d

# 本地开发（启动中间件）
cd backend && docker compose up -d
cd backend && uv run daphne -b 0.0.0.0 -p 8000 config.asgi:application
cd frontend && pnpm dev

# 种子数据
docker compose exec backend uv run python manage.py seed_data
```

---

## 8. API 设计

### 8.1 URL 路由结构

```
api/
├── auth/              # 认证
│   ├── register/      POST
│   ├── login/         POST
│   ├── logout/        POST
│   ├── me/            GET, PUT
│   └── change-password/ POST
├── token/refresh/     POST
├── workspaces/        GET, POST
├── workspaces/{id}/   GET, PUT, DELETE
│   ├── members/       GET, POST
│   ├── members/{uid}/ PUT, DELETE
│   └── projects/      GET, POST
├── projects/{projId}/
│   ├── tasks/            GET, POST
│   ├── tasks/{pk}/       GET, PUT, PATCH, DELETE
│   │   ├── status/       PATCH
│   │   └── subtasks/     POST
│   ├── task-statuses/    GET, POST
│   ├── iterations/       GET, POST
│   ├── iterations/{pk}/  GET, PUT, DELETE
│   ├── modules/          GET, POST
│   ├── modules/{pk}/     GET, PUT, DELETE
│   └── statistics/       GET
├── tasks/{taskId}/
│   ├── comments/         GET, POST
│   ├── comments/{pk}/    PUT, DELETE
│   ├── attachments/      GET, POST
│   ├── attachments/{pk}/ DELETE
│   └── activities/       GET
├── notifications/        GET
│   ├── {pk}/             GET
│   ├── {pk}/read/        PATCH
│   └── read-all/         POST
└── docs/               Swagger UI
```

### 8.2 API 设计原则

- **嵌套路由**：资源按层级嵌套（workspace → project → task），URL 语义化
- **UUID 标识**：所有资源使用 UUID4 主键
- **自定义操作**：通过 `@action` 装饰器（如 `/status/`、 `/members/`、`/archive/`）
- **批量操作**：迭代的 `add_tasks/` 支持批量任务分配
- **ReadOnly 视图集**：通知和活动日志不可写（通过其他途径触发）

---

## 9. 安全设计

### 9.1 认证安全

| 措施             | 实现                                      |
| ---------------- | ----------------------------------------- |
| **密码存储**     | Django 默认 PBKDF2 (可配置 bcrypt/argon2) |
| **JWT 签名**     | HMAC-SHA256 (密钥需 ≥32 字节)             |
| **Token 黑名单** | SimpleJWT TokenBlacklist                  |
| **Token 轮换**   | 刷新时自动生成新令牌                      |
| **密码验证**     | 最小 6 位 (仅 `MinimumLengthValidator`)   |

### 9.2 授权模型

```
User
 ├── WorkspaceMember (workspace_id, user_id, role)
 │    ├── ADMIN    → 完全控制工作空间及子项目
 │    ├── MEMBER   → 读写工作空间内容
 │    └── GUEST    → 受限访问
 └── ProjectMember (project_id, user_id, role)
      ├── ADMIN    → 完全控制项目及所有任务
      ├── MEMBER   → 读写任务（不能删除项目）
      └── VIEWER   → 只读
```

### 9.3 安全测试结果

| 类别     | 测试项                            | 结果               |
| -------- | --------------------------------- | ------------------ |
| JWT 认证 | 缺失/无效/过期 Token              | ✅ 401              |
| 授权     | 跨工作空间/项目访问               | ✅ 403/404          |
| 输入校验 | SQL 注入、XSS、超长输入、空请求体 | ✅ 全部拒绝         |
| 密码安全 | 明文密码不返回、哈希存储          | ✅ 通过             |
| 任务权限 | 非负责人修改他人任务              | ⚠️ xfail (已知问题) |

---

## 10. 测试体系

### 10.1 测试概览

| 指标             | 数据              |
| ---------------- | ----------------- |
| 总测试数         | 294               |
| 通过             | 288               |
| 预期失败 (xfail) | 6                 |
| 实际失败         | 0                 |
| 通过率           | 100% (排除 xfail) |
| 执行时间         | ~110s             |

### 10.2 测试分布

| 测试集   | 位置                                                                            | 数量 | 类型 |
| -------- | ------------------------------------------------------------------------------- | ---- | ---- |
| 认证     | `tests/test_auth.py`                                                            | 15   | 集成 |
| 安全     | `tests/test_security.py`                                                        | 17   | 集成 |
| 工作空间 | `tests/test_workspaces.py`                                                      | 20   | 集成 |
| 项目     | `tests/test_projects.py`                                                        | 17   | 集成 |
| 任务     | `tests/test_tasks.py`                                                           | 26   | 集成 |
| 迭代     | `tests/test_iterations.py`                                                      | 13   | 集成 |
| 性能     | `tests/test_performance.py` + `test_qs1_performance.py` + `test_load_report.py` | 11   | 性能 |
| 故障恢复 | `tests/test_fault_recovery.py` + `test_fault_injection.py`                      | 35   | 容错 |
| 单元测试 | `apps/*/tests/`                                                                 | 130  | 单元 |

### 10.3 性能基准

| 操作                                | 目标   | 实际            |
| ----------------------------------- | ------ | --------------- |
| 登录                                | <500ms | <200ms          |
| 工作空间列表                        | <200ms | <200ms          |
| 任务列表                            | <200ms | <200ms          |
| 统计                                | <300ms | <300ms          |
| **QS1 高负载** (100并发 × 10万任务) | —      | P95 244ms–2.07s |

### 10.4 故障注入测试

覆盖 28 个恢复测试 + 7 个注入测试：

| 场景       | 测试点             |
| ---------- | ------------------ |
| 连接池耗尽 | 耗尽后正确处理     |
| 事务回滚   | 错误后数据一致性   |
| 并发写竞态 | 非阻塞写不覆盖     |
| 大批量回滚 | 500 条写入失败回滚 |
| 外键约束   | 级联删除保护       |
| 混沌工程   | 5 阶段综合故障演练 |

### 10.5 架构验证 (AD1-AD4)

| AD  | 测试           | 结果 |
| --- | -------------- | ---- |
| AD1 | 前后端分离     | ✅    |
| AD2 | Redis 缓存效果 | ✅    |
| AD3 | JWT + RBAC     | ✅    |
| AD4 | 文件持久化     | ✅    |

---

## 11. 已知问题与限制

### 11.1 当前已知问题

| #   | 严重度 | 描述                                                           | 状态  |
| --- | ------ | -------------------------------------------------------------- | ----- |
| 1   | **高** | `/api/iterations/{id}/` 缺少 `proj_id` 上下文时返回空 queryset | xfail |
| 2   | **中** | 项目标识符重复仅在数据库层报错 (500)，缺少序列化器校验         | xfail |
| 3   | **中** | 普通成员可以修改他人任务（缺少对象级权限检查）                 | xfail |
| 4   | **低** | JWT HMAC 密钥 29 字节 < 推荐 32 字节 (SHA256)                  | 警告  |

### 11.2 架构限制

| 限制               | 说明                                                     |
| ------------------ | -------------------------------------------------------- |
| **单进程 ASGI**    | Daphne 单进程处理 HTTP + WebSocket，大流量下可能成为瓶颈 |
| **附件大小**       | 上传限制 10MB（代码层面），MinIO 配置可调整但未暴露      |
| **搜索能力**       | 仅基于 `icontains` 的简单搜索，无全文检索引擎            |
| **WebSocket 鉴权** | Token 通过 URL 查询参数传递，日志中可能暴露              |
| **国际化**         | 仅支持中文界面和时区 (Asia/Shanghai)                     |
| **密码策略**       | 仅最小长度验证，无复杂度要求                             |

### 11.3 可优化方向

1. **全文搜索** — 引入 PostgreSQL `SearchVector` 或 Elasticsearch
2. **附件分片上传** — 支持大文件断点续传
3. **批量操作** — 看板批量移动、批量删除任务
4. **通知聚合** — 类似变更的通知合并
5. **WebSocket 认证** — 迁移至 Secure Cookie 或 Sec-WebSocket-Protocol
6. **前端测试** — 目前无前端单元/组件测试
7. **性能优化** — 数据库索引覆盖分析、N+1 查询检测
8. **缓存策略** — 增加 Redis 缓存热数据

---

## 附录

### A. 开发命令速查

```bash
# 后端
cd backend
uv sync                                    # 安装依赖
uv run python manage.py migrate            # 迁移数据库
uv run daphne -b 0.0.0.0 -p 8000 config.asgi:application  # 启动
uv run pytest                              # 运行测试
uv run pytest --cov=apps --cov-report=term-missing  # 带覆盖

# 前端
cd frontend
pnpm install                               # 安装依赖
pnpm dev                                   # 启动 (port 5173)
pnpm lint                                  # ESLint 检查
npx tsc --noEmit                           # TypeScript 检查

# Docker
docker compose up -d                       # 全栈启动
docker compose up -d --build frontend      # 重建前端
docker compose exec backend uv run python manage.py seed_data  # 种子数据
```

### B. 技术依赖

| 包                    | 最小版本 | 用途        |
| --------------------- | -------- | ----------- |
| django                | 5.0      | Web 框架    |
| djangorestframework   | 3.15     | REST API    |
| channels              | 4.1      | WebSocket   |
| daphne                | 4.1      | ASGI 服务器 |
| celery                | 5.3      | 异步任务    |
| next                  | 16.2.6   | React 框架  |
| zustand               | 5.x      | 状态管理    |
| @tanstack/react-query | 5.x      | 服务端缓存  |
| tailwindcss           | 4.x      | CSS 框架    |
| recharts              | 3.8.1    | 统计图表    |

### C. 文件大小统计

```
backend/
├── apps/          ~4500 行 Python
├── config/        ~600 行 Python
├── tests/         ~3500 行 Python
└── (其余)          ~500 行

frontend/
├── src/app/       ~2100 行 TSX
├── src/components/ ~350 行 TSX
├── src/lib/        ~280 行 TS
├── src/stores/     ~100 行 TS
└── src/types/      ~260 行 TS

基础设施:
├── docker-compose.yml  ~140 行
├── nginx/nginx.conf    ~60 行
└── Dockerfile (×2)     ~40 行

总计:              ~12000 行 (不含 venv/node_modules)
```
