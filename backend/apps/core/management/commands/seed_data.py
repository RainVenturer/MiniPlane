"""
演示数据填充命令 — 3 个团队

用法:
    python manage.py seed_data          # 创建演示数据
    python manage.py seed_data --clear  # 清除所有数据后重新创建

创建内容:
    - 16 个团队成员（分布在 3 个团队）
    - 3 个工作空间 + 3 个项目
    - 6 个迭代周期
    - 13 个功能模块
    - ~65 个任务（覆盖所有状态、优先级）
    - 子任务、评论
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import date, timedelta

User = get_user_model()

# 6 个默认状态名称 (与 views.py perform_create 一致)
STATUS_NAMES = ["Backlog", "待办", "进行中", "待评审", "已完成", "已取消"]
STATUS_TYPES = ["backlog", "unstarted", "started", "started", "completed", "cancelled"]
STATUS_COLORS = ["#6b7280", "#6366f1", "#f59e0b", "#8b5cf6", "#10b981", "#ef4444"]

# ═══════════════════════════════════════════════════════════════
# 三个团队的演示数据定义
# ═══════════════════════════════════════════════════════════════

TEAMS = [
    # ── 团队 1: MiniPlane 软件开发 ──────────────────────────────
    {
        "users": [
            {"email": "zhang@demo.com", "password": "Demo123456", "name": "张经理"},
            {"email": "li@demo.com",   "password": "Demo123456", "name": "李前端"},
            {"email": "wang@demo.com",  "password": "Demo123456", "name": "王后端"},
            {"email": "zhao@demo.com",  "password": "Demo123456", "name": "赵设计"},
            {"email": "chen@demo.com",  "password": "Demo123456", "name": "陈测试"},
            {"email": "liu@demo.com",   "password": "Demo123456", "name": "刘实习"},
        ],
        "workspace": {
            "name": "MiniPlane 开发团队",
            "slug": "miniplane",
            "desc": "轻量级团队项目协作工具的开发团队，覆盖产品、前端、后端、设计、测试。",
        },
        "project": {
            "name": "MiniPlane",
            "identifier": "MP",
            "desc": "轻量级团队项目协作与缺陷跟踪系统 — 工作空间、项目、任务、看板、迭代、评论、通知。",
        },
        "member_roles": ["admin", "member", "member", "member", "member", "guest"],
        "modules": [
            {"name": "用户认证模块", "desc": "注册、登录、JWT 鉴权、个人资料管理", "lead": 0},
            {"name": "任务管理模块", "desc": "任务 CRUD、状态流转、优先级、看板视图", "lead": 1},
            {"name": "项目管理模块", "desc": "工作空间、项目、成员管理、迭代规划", "lead": 2},
            {"name": "通知中心模块", "desc": "实时通知、WebSocket 推送、消息已读", "lead": 2},
            {"name": "文件服务模块", "desc": "附件上传下载、MinIO 对象存储", "lead": 2},
        ],
        "iterations": [
            {"name": "Sprint 1 — 核心功能", "desc": "用户认证、工作空间、项目管理、任务 CRUD",
             "start": date(2026, 6, 1), "end": date(2026, 6, 14), "active": False},
            {"name": "Sprint 2 — 协作功能", "desc": "评论、通知、文件上传、搜索筛选、统计面板",
             "start": date(2026, 6, 15), "end": date(2026, 6, 28), "active": True},
        ],
        "tasks": [
            ("用户注册页面开发", "进行中", "high", 1, 0, 0, "注册页面 UI 和前端表单验证，对接后端注册接口"),
            ("JWT 登录接口实现", "已完成", "high", 2, 0, 0, "基于 simplejwt 实现 Access + Refresh Token 双令牌机制"),
            ("RBAC 权限中间件", "待评审", "high", 2, 0, 0, "IsWorkspaceAdmin / IsProjectAdmin / IsTaskAssigneeOrProjectAdmin"),
            ("设计系统色板定义", "已完成", "medium", 3, 0, 1, "确定主色、辅助色、功能色，确保 WCAG AA 对比度"),
            ("工作空间设置页", "Backlog", "medium", 1, 1, 2, "工作空间名称、描述编辑 & 成员管理界面"),
            ("任务看板拖拽排序", "进行中", "urgent", 1, 0, 1, "基于 dnd-kit 实现看板视图拖拽，同步 order 到后端"),
            ("任务状态流转引擎", "已完成", "high", 2, 0, 1, "状态变更接口 + Activity 记录 + WebSocket 通知"),
            ("数据库查询性能优化", "待办", "urgent", 2, 1, 2, "复合索引 (project,status)/(project,assignee)，explain 验证"),
            ("附件上传组件", "进行中", "medium", 1, 1, 4, "拖拽上传 + 进度条 + 多文件支持，对接 MinIO 预签名 URL"),
            ("MinIO 存储集成", "已完成", "high", 2, 0, 4, "MinIO 客户端配置、文件上传下载、自动建 bucket"),
            ("迭代统计面板", "待办", "medium", 2, 1, 2, "迭代进度、燃尽图、任务完成率、成员工作量分布"),
            ("评论 @ 提及功能", "Backlog", "low", 2, 1, 3, "@用户名 自动高亮、被提及者收到推送通知"),
            ("WebSocket 实时通知", "待评审", "high", 2, 0, 3, "Django Channels + Redis Pub/Sub 实时推送未读通知数"),
            ("移动端响应式适配", "Backlog", "medium", 1, 1, 1, "看板移动端卡片滑动、导航菜单改为底部 Tab"),
            ("消息通知中心页面", "进行中", "medium", 1, 0, 3, "通知列表、未读/已读切换、全部标为已读、关联跳转"),
            ("全局搜索功能", "待办", "high", 2, 1, 1, "全文搜索任务标题、描述、评论，高亮匹配文本"),
            ("项目归档与恢复", "已完成", "low", 2, 1, 2, "is_archived 标记、归档/恢复 API、归档项目置灰"),
            ("前端 E2E 测试搭建", "待办", "medium", 4, 1, 1, "Playwright 关键路径: 注册→创建项目→创建任务→完成"),
            ("CI/CD Pipeline", "待办", "high", 2, 1, 2, "GitHub Actions: lint → test → build → deploy to staging"),
            ("用户头像上传裁剪", "Backlog", "low", 1, 1, 0, "上传自定义头像，cropper.js 裁剪后上传 MinIO"),
            ("API 文档自动生成", "已完成", "medium", 2, 0, 2, "drf-spectacular 集成，OpenAPI 3.0 + Swagger UI"),
            ("性能压测报告", "待评审", "high", 4, 0, 2, "100 并发 / 100K 任务 QS1 场景，P95 < 2s 目标验证"),
            ("忘记密码 / 重置密码流程", "Backlog", "medium", 0, 1, 0, "邮箱验证码 → 重置密码 → 发送成功通知"),
            ("任务标签系统", "Backlog", "low", 2, 1, 1, "自定义标签(bug/feature/improvement)，多标签筛选"),
            ("数据导出功能", "Backlog", "low", 0, 1, 2, "导出项目任务 CSV/Excel，迭代报告导出 PDF"),
            ("夜间模式切换", "Backlog", "low", 1, 1, 1, "全局主题切换，LocalStorage 持久化，CSS 变量驱动"),
            ("国际化 i18n 框架", "Backlog", "medium", 0, 1, 0, "react-i18next，中/英/日三语，语言包按模块拆分"),
            ("任务活动时间线", "进行中", "medium", 1, 0, 1, "任务详情页完整活动历史时间线，按操作类型筛选"),
            ("模块负责人统计", "已完成", "medium", 2, 0, 2, "模块维度统计：任务数、完成率、成员分布"),
            ("批量操作任务", "待办", "high", 2, 1, 1, "多选任务批量修改状态、优先级、负责人、迭代"),
        ],
        "subtasks": [
            (0, "注册表单 UI 布局", "high", 1),
            (0, "前端表单验证逻辑", "medium", 1),
            (0, "对接 POST /api/register/", "high", 1),
            (5, "看板列组件封装", "high", 1),
            (5, "拖拽状态同步 Hook", "urgent", 1),
            (5, "order 字段后端更新", "urgent", 2),
            (2, "IsWorkspaceAdmin 实现", "high", 2),
            (2, "IsTaskAssigneeOrProjectAdmin 实现", "high", 2),
            (2, "权限单元测试", "medium", 4),
            (9, "MinIO Docker 配置", "high", 2),
            (9, "预签名 URL 生成", "high", 2),
            (9, "上传大小限制 & 类型校验", "medium", 2),
            (14, "通知列表页面", "medium", 1),
            (14, "未读小红点组件", "low", 1),
            (14, "WebSocket 连接管理", "medium", 2),
        ],
        "comments": [
            (1, 0, "后端接口对接好了吗？前端这边注册页面快完成了。"),
            (1, 2, "已经好了，用 POST /api/auth/login/ ，返回 access + refresh token。"),
            (1, 1, "好的，我这边今天就对接。"),
            (5, 0, "拖拽排序是核心功能，这周能完成吗？"),
            (5, 1, "前端拖拽交互已经打通了，就差后端的 order 更新接口。"),
            (5, 2, "order 更新接口我来写，今天下午提交。"),
            (6, 3, "状态流转能不能加个确认弹窗？避免误操作。"),
            (6, 0, "可以，我在需求里补充一下交互细节。"),
            (7, 4, "加了索引之后，筛选查询从 800ms 降到 40ms，效果很明显。"),
            (7, 2, "👍 太好了，我接下来把全量列表的 explain 也跑一下。"),
            (12, 0, "通知系统要支持服务号通知吗？还是只做站内通知？"),
            (12, 2, "先做站内通知 + WebSocket 实时推送，后续可以扩展企业微信通知。"),
            (21, 4, "压测结果：P95=243ms，远低于 2s 目标，索引优化效果很好。"),
            (21, 0, "太好了！把这个结果更新到 TEST_REPORT.md，准备评审演示。"),
        ],
    },

    # ── 团队 2: ShopNow 电商平台 ──────────────────────────────
    {
        "users": [
            {"email": "sun@demo.com",   "password": "Demo123456", "name": "孙产品"},
            {"email": "zhou@demo.com",  "password": "Demo123456", "name": "周前端"},
            {"email": "wu@demo.com",    "password": "Demo123456", "name": "吴后端"},
            {"email": "zheng@demo.com", "password": "Demo123456", "name": "郑测试"},
            {"email": "feng@demo.com",  "password": "Demo123456", "name": "冯运维"},
        ],
        "workspace": {
            "name": "ShopNow 电商团队",
            "slug": "shopnow",
            "desc": "全渠道电商平台研发团队 — 商品、订单、支付、物流、营销五大业务线。",
        },
        "project": {
            "name": "ShopNow 电商平台",
            "identifier": "SN",
            "desc": "B2C 电商平台，支持商品管理、购物车、订单流转、微信支付、物流追踪、优惠券系统。",
        },
        "member_roles": ["admin", "member", "member", "member", "member"],
        "modules": [
            {"name": "商品中心", "desc": "商品 CRUD、SKU 管理、库存同步、类目树", "lead": 0},
            {"name": "订单中心", "desc": "下单、订单状态机、退款/退货、发票", "lead": 0},
            {"name": "支付网关", "desc": "微信支付、支付宝、银行卡，回调幂等处理", "lead": 2},
            {"name": "营销引擎", "desc": "优惠券、满减、秒杀、拼团规则引擎", "lead": 1},
        ],
        "iterations": [
            {"name": "Sprint 1 — 商品与订单", "desc": "商品 CRUD、SKU、下单流程、订单状态机",
             "start": date(2026, 6, 1), "end": date(2026, 6, 14), "active": False},
            {"name": "Sprint 2 — 支付与营销", "desc": "微信支付对接、优惠券、满减、秒杀",
             "start": date(2026, 6, 15), "end": date(2026, 6, 28), "active": True},
        ],
        "tasks": [
            ("商品列表页开发", "进行中", "high", 1, 0, 0, "商品卡片、分类筛选、搜索、分页加载"),
            ("SKU 库存管理接口", "已完成", "high", 2, 0, 0, "多规格 SKU 创建、库存增减、预警通知"),
            ("订单状态机设计", "已完成", "high", 0, 0, 1, "待付款→已付款→已发货→已收货→已完成/已退款"),
            ("购物车服务", "进行中", "urgent", 1, 0, 1, "加入购物车、修改数量、合并未登录购物车"),
            ("微信支付对接", "待评审", "urgent", 2, 1, 2, "JSAPI 支付、支付回调验签、订单状态同步"),
            ("退款流程实现", "待办", "high", 2, 1, 1, "原路退款、部分退款、退款审批、到账通知"),
            ("优惠券发放与核销", "进行中", "medium", 1, 1, 3, "后台发券、用户领券、下单核销、互斥规则"),
            ("秒杀活动页面", "Backlog", "high", 1, 1, 3, "限时秒杀倒计时、库存预扣、防超卖 Redis 锁"),
            ("物流追踪集成", "待办", "medium", 2, 1, 1, "对接顺丰/圆通 API，实时物流状态回传"),
            ("商品评价系统", "Backlog", "low", 1, 1, 0, "五星评分 + 文字+图片评价，评价审核"),
            ("商家后台管理端", "进行中", "high", 1, 0, 0, "商家入驻、商品上架、订单管理、数据看板"),
            ("全站搜索 ES 接入", "待办", "high", 2, 1, 0, "Elasticsearch 商品全文搜索、拼音搜索、同义词"),
            ("首页个性化推荐", "Backlog", "medium", 2, 1, 0, "基于用户行为协同过滤推荐，AB 实验框架"),
            ("移动端商品详情页", "进行中", "medium", 1, 0, 0, "轮播图、规格选择、立即购买、收藏"),
            ("API 网关限流", "待评审", "high", 4, 0, 2, "Token Bucket 限流、DDoS 防护、接口鉴权"),
            ("性能压测与调优", "待办", "urgent", 4, 1, 2, "双11 容量预估、全链路压测、慢 SQL 优化"),
        ],
        "subtasks": [
            (0, "商品卡片组件", "high", 1),
            (0, "分类侧边栏筛选", "medium", 1),
            (0, "商品搜索防抖", "medium", 1),
            (3, "购物车状态管理", "high", 1),
            (3, "未登录购物车合并", "high", 2),
            (4, "统一下单接口", "urgent", 2),
            (4, "支付回调验签", "urgent", 2),
        ],
        "comments": [
            (3, 0, "购物车数据存在 Redis 还是 PostgreSQL？"),
            (3, 2, "购物车存 Redis，下单后转存 PostgreSQL，避免丢数据。"),
            (4, 4, "微信支付回调签名验证必须严格，之前有个项目被刷过假回调。"),
            (4, 2, "收到，已经加了商户证书签名验证和 IP 白名单。"),
            (10, 1, "商家后台的商品管理是不是可以复用 C 端的商品列表组件？"),
            (10, 0, "可以，抽一个公共的商品表格组件，B 端和 C 端都用它。"),
            (14, 4, "API 网关的限流规则最好做成可视化的，方便运营调参数。"),
        ],
    },

    # ── 团队 3: FitLife 健身 App ──────────────────────────────
    {
        "users": [
            {"email": "qian@demo.com", "password": "Demo123456", "name": "钱经理"},
            {"email": "yang@demo.com", "password": "Demo123456", "name": "杨移动端"},
            {"email": "huang@demo.com","password": "Demo123456", "name": "黄后端"},
            {"email": "xu@demo.com",   "password": "Demo123456", "name": "许设计"},
            {"email": "zhu@demo.com",  "password": "Demo123456", "name": "朱测试"},
        ],
        "workspace": {
            "name": "FitLife 健身团队",
            "slug": "fitlife",
            "desc": "移动健身应用研发团队 — iOS/Android 客户端 + 后端服务 + AI 推荐引擎。",
        },
        "project": {
            "name": "FitLife 健身 App",
            "identifier": "FL",
            "desc": "智能健身伴侣 App — 训练计划、动作库、饮食记录、身体数据追踪、AI 教练推荐。",
        },
        "member_roles": ["admin", "member", "member", "member", "member"],
        "modules": [
            {"name": "训练计划模块", "desc": "个性化训练计划生成、日程管理、训练日历", "lead": 0},
            {"name": "动作库", "desc": "500+ 标准动作视频、分类标签、搜索", "lead": 3},
            {"name": "饮食记录模块", "desc": "食物数据库、热量计算、营养分析、拍照识别", "lead": 1},
            {"name": "AI 推荐引擎", "desc": "基于用户数据的训练计划推荐、强度调整", "lead": 2},
        ],
        "iterations": [
            {"name": "Sprint 1 — 基础功能", "desc": "注册登录、训练计划、动作库",
             "start": date(2026, 6, 1), "end": date(2026, 6, 14), "active": False},
            {"name": "Sprint 2 — 智能功能", "desc": "饮食记录、AI 推荐、数据看板",
             "start": date(2026, 6, 15), "end": date(2026, 6, 28), "active": True},
        ],
        "tasks": [
            ("用户注册与引导页", "已完成", "high", 1, 0, 0, "手机号注册、个人信息填写、健身目标选择引导"),
            ("训练计划生成器", "进行中", "urgent", 0, 0, 0, "根据用户目标/水平/时间自动生成周训练计划"),
            ("动作库视频播放器", "已完成", "high", 1, 0, 1, "动作视频播放、慢放、循环、进度条拖拽"),
            ("动作分类与搜索", "已完成", "medium", 1, 0, 1, "按肌群/器械/难度分类，关键词搜索"),
            ("训练日历组件", "进行中", "high", 1, 0, 0, "月视图日历、训练日标记、点击查看当日计划"),
            ("训练计时器", "待办", "medium", 1, 1, 1, "组间休息倒计时、训练总时长记录、语音播报"),
            ("饮食拍照识别", "进行中", "high", 2, 1, 2, "调用 OCR/视觉 API 识别食物并估算热量"),
            ("食物数据库建设", "已完成", "medium", 0, 1, 2, "常见食物热量表导入，支持搜索和自定义添加"),
            ("热量摄入分析图表", "待办", "medium", 1, 1, 2, "日/周/月热量趋势图，三大营养素占比饼图"),
            ("AI 训练推荐模型", "待办", "urgent", 2, 1, 3, "基于协同过滤+用户画像的训练计划推荐"),
            ("身体数据追踪页", "进行中", "medium", 1, 0, 0, "体重/体脂/围度记录、变化曲线、目标对比"),
            ("社交动态分享", "Backlog", "low", 1, 1, 0, "训练动态发布、图片分享、点赞评论"),
            ("推送通知系统", "待评审", "high", 2, 0, 3, "训练提醒推送、成就解锁通知、周报推送"),
            ("离线模式支持", "待办", "medium", 1, 1, 1, "核心功能离线可用、数据同步冲突解决"),
            ("Apple Watch 适配", "Backlog", "high", 1, 1, 0, "手表端训练记录、心率监测、震动提醒"),
            ("用户成就系统", "Backlog", "medium", 3, 1, 0, "连续训练天数、里程碑徽章、等级体系"),
            ("付费会员体系", "待办", "high", 2, 1, 0, "月度/年度订阅、IAP 内购、优惠活动"),
            ("数据隐私合规", "待评审", "high", 4, 0, 0, "GDPR/个人信息保护法合规、数据脱敏、删除账号"),
        ],
        "subtasks": [
            (1, "训练目标选择器", "high", 1),
            (1, "计划模板库设计", "high", 0),
            (1, "周计划自动排期算法", "urgent", 2),
            (2, "视频预加载策略", "medium", 1),
            (2, "手势控制播放进度", "low", 1),
            (6, "OCR API 选型对比", "high", 2),
            (6, "食物热量计算逻辑", "high", 2),
            (12, "FCM/APNs 推送集成", "high", 2),
            (12, "通知偏好设置页", "medium", 1),
        ],
        "comments": [
            (1, 0, "训练计划生成算法优先用规则引擎还是直接上 ML？"),
            (1, 2, "先用规则引擎快速上线，积累训练数据后再训推荐模型。"),
            (6, 1, "拍照识别的准确率怎么样？中餐菜式能识别吗？"),
            (6, 2, "目前用 GPT-4V API，中餐识别率大概 70%，需要持续优化。"),
            (6, 0, "先上线让用户手动纠正，纠正数据用来 fine-tune 模型。"),
            (9, 2, "推荐模型我先用协同过滤做 MVP，后面加用户画像特征。"),
            (9, 0, "可以，Sprint 3 再加上训练效果反馈闭环。"),
            (12, 4, "推送通知时间要考虑不同时区用户，别半夜推。"),
        ],
    },
]


class Command(BaseCommand):
    help = "填充演示数据到数据库，方便 UI 演示"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="清除所有现有数据后重新创建",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self._clear_all()

        # 用第一个团队的第一个用户邮箱做幂等检查
        first_email = TEAMS[0]["users"][0]["email"]
        if User.objects.filter(email=first_email).exists():
            self.stdout.write(self.style.WARNING(
                f"演示数据已存在 ({first_email})，跳过创建。"
            ))
            self.stdout.write("如需重新创建请先运行: python manage.py seed_data --clear")
            return

        # 创建全部团队
        for idx, team in enumerate(TEAMS):
            self.stdout.write(f"\n{'─' * 50}")
            self.stdout.write(f"  📦 团队 {idx + 1}/{len(TEAMS)}: {team['workspace']['name']}")
            self.stdout.write(f"{'─' * 50}")
            self._create_team(team)

        self.stdout.write(self.style.SUCCESS(f"\n✅ 全部 {len(TEAMS)} 个团队演示数据填充完成！"))
        self._print_summary()

    # ═══════════════════════════════════════════════════════
    # 单团队创建
    # ═══════════════════════════════════════════════════════

    def _create_team(self, team):
        users = self._create_users(team["users"])
        workspace = self._create_workspace(team["workspace"], users, team["member_roles"])
        project = self._create_project(team["project"], workspace, users, team["member_roles"])
        statuses = self._create_statuses(project)
        modules = self._create_modules(project, team["modules"], users)
        iterations = self._create_iterations(project, team["iterations"])
        tasks = self._create_tasks(project, team["tasks"], statuses, users, modules, iterations)
        self._create_subtasks(project, team.get("subtasks", []), tasks, statuses, users)
        self._create_comments(team.get("comments", []), tasks, users)

    # ═══════════════════════════════════════════════════════
    # 清除
    # ═══════════════════════════════════════════════════════

    def _clear_all(self):
        from apps.comments.models import Comment
        from apps.activities.models import Activity
        from apps.attachments.models import Attachment
        from apps.notifications.models import Notification
        from apps.tasks.models import Task, TaskStatus
        from apps.iterations.models import Iteration
        from apps.modules.models import Module
        from apps.projects.models import Project, ProjectMember
        from apps.workspaces.models import Workspace, WorkspaceMember

        self.stdout.write("正在清除现有数据...")
        models = [Comment, Activity, Attachment, Notification,
                  Task, TaskStatus, Iteration, Module,
                  ProjectMember, Project, WorkspaceMember, Workspace]
        for model in models:
            count, _ = model.objects.all().delete()
            if count:
                self.stdout.write(f"  删除 {model.__name__}: {count} 条")
        non_staff, _ = User.objects.filter(is_staff=False).delete()
        if non_staff:
            self.stdout.write(f"  删除 User: {non_staff} 条")
        self.stdout.write(self.style.SUCCESS("清除完成。\n"))

    # ═══════════════════════════════════════════════════════
    # 创建方法（纯函数式，无 self 状态依赖）
    # ═══════════════════════════════════════════════════════

    def _create_users(self, user_defs):
        users = []
        for u in user_defs:
            user, _ = User.objects.get_or_create(
                email=u["email"],
                defaults={"password": u["password"], "name": u["name"]},
            )
            if not user.check_password(u["password"]):
                user.set_password(u["password"])
                user.save()
            users.append(user)
        names = ", ".join(u.name for u in users)
        self.stdout.write(f"  ✅ 用户 ({len(users)}): {names}")
        return users

    def _create_workspace(self, ws_def, users, roles):
        from apps.workspaces.models import Workspace, WorkspaceMember

        ws, _ = Workspace.objects.get_or_create(
            slug=ws_def["slug"],
            defaults={
                "name": ws_def["name"],
                "description": ws_def["desc"],
                "owner": users[0],
            },
        )
        for user, role in zip(users, roles):
            WorkspaceMember.objects.get_or_create(
                workspace=ws, user=user,
                defaults={"role": role},
            )
        self.stdout.write(f"  ✅ 工作空间: {ws.name} (slug={ws.slug})")
        return ws

    def _create_project(self, proj_def, workspace, users, roles):
        from apps.projects.models import Project, ProjectMember

        proj, _ = Project.objects.get_or_create(
            workspace=workspace,
            identifier=proj_def["identifier"],
            defaults={
                "name": proj_def["name"],
                "description": proj_def["desc"],
            },
        )
        for user, role in zip(users, roles):
            ProjectMember.objects.get_or_create(
                project=proj, user=user,
                defaults={"role": role},
            )
        self.stdout.write(f"  ✅ 项目: {proj.name} ({proj.identifier})")
        return proj

    def _create_statuses(self, project):
        from apps.tasks.models import TaskStatus

        statuses = {}
        for i, (name, type_, color) in enumerate(
            zip(STATUS_NAMES, STATUS_TYPES, STATUS_COLORS)
        ):
            st, _ = TaskStatus.objects.get_or_create(
                project=project, name=name,
                defaults={"color": color, "type": type_, "order": i},
            )
            statuses[name] = st
        self.stdout.write(f"  ✅ 状态列: {list(statuses.keys())}")
        return statuses

    def _create_modules(self, project, mod_defs, users):
        from apps.modules.models import Module

        modules = []
        for mod in mod_defs:
            m, _ = Module.objects.get_or_create(
                project=project, name=mod["name"],
                defaults={
                    "description": mod["desc"],
                    "lead": users[mod["lead"]],
                },
            )
            modules.append(m)
        self.stdout.write(f"  ✅ 模块 ({len(modules)}): {[m.name for m in modules]}")
        return modules

    def _create_iterations(self, project, iter_defs):
        from apps.iterations.models import Iteration

        iterations = []
        for it in iter_defs:
            obj, _ = Iteration.objects.get_or_create(
                project=project, name=it["name"],
                defaults={
                    "description": it["desc"],
                    "start_date": it["start"],
                    "end_date": it["end"],
                    "is_active": it["active"],
                },
            )
            iterations.append(obj)
        self.stdout.write(f"  ✅ 迭代 ({len(iterations)}): {[i.name for i in iterations]}")
        return iterations

    def _create_tasks(self, project, task_defs, statuses, users, modules, iterations):
        from apps.tasks.models import Task

        task_objs = []
        now = timezone.now()
        for i, (title, status_name, priority, assignee_idx, iter_idx, mod_idx, desc) in enumerate(task_defs):
            created_at = now - timedelta(days=len(task_defs) - i, hours=i % 12)
            task = Task.objects.create(
                project=project,
                status=statuses[status_name],
                title=title,
                description=desc,
                priority=priority,
                assignee=users[assignee_idx],
                iteration=iterations[iter_idx],
                module=modules[mod_idx],
                created_by=users[assignee_idx],
                order=float(i * 100),
                created_at=created_at,
            )
            task_objs.append(task)

        # 统计分布
        from collections import Counter
        dist = Counter(t.status.name for t in task_objs)
        dist_str = ", ".join(f"{k}={v}" for k, v in dist.items())
        self.stdout.write(f"  ✅ 任务 ({len(task_objs)}): {dist_str}")
        return task_objs

    def _create_subtasks(self, project, sub_defs, tasks, statuses, users):
        from apps.tasks.models import Task

        for i, (parent_idx, title, priority, assignee_idx) in enumerate(sub_defs):
            parent = tasks[parent_idx]
            Task.objects.get_or_create(
                project=project, parent=parent, title=title,
                defaults={
                    "status": statuses["待办"],
                    "priority": priority,
                    "assignee": users[assignee_idx],
                    "created_by": users[assignee_idx],
                    "order": parent.order + 0.01 * (i + 1),
                },
            )
        if sub_defs:
            parents = len(set(s[0] for s in sub_defs))
            self.stdout.write(f"  ✅ 子任务 ({len(sub_defs)} 个 / {parents} 个父任务)")

    def _create_comments(self, comment_defs, tasks, users):
        from apps.comments.models import Comment

        for task_idx, author_idx, content in comment_defs:
            Comment.objects.get_or_create(
                task=tasks[task_idx],
                author=users[author_idx],
                content=content,
            )
        if comment_defs:
            parents = len(set(c[0] for c in comment_defs))
            self.stdout.write(f"  ✅ 评论 ({len(comment_defs)} 条 / {parents} 个任务)")

    # ═══════════════════════════════════════════════════════
    # 汇总
    # ═══════════════════════════════════════════════════════

    def _print_summary(self):
        from apps.workspaces.models import Workspace
        from apps.tasks.models import Task
        from apps.comments.models import Comment

        total_ws = Workspace.objects.filter(slug__in=[t["workspace"]["slug"] for t in TEAMS]).count()
        total_tasks = Task.objects.filter(project__identifier__in=[t["project"]["identifier"] for t in TEAMS]).count()
        total_comments = Comment.objects.filter(
            task__project__identifier__in=[t["project"]["identifier"] for t in TEAMS]
        ).count()

        self.stdout.write(f"""
┌────────────────────────────────────────────────────────┐
│                  🎯 演示数据总览                          │
├────────────────────────────────────────────────────────┤
│  团队 1: MiniPlane 开发团队                              │
│    登录: zhang@demo.com  →  li/wang/zhao/chen/liu      │
│    项目: MiniPlane (MP)                                 │
│                                                        │
│  团队 2: ShopNow 电商团队                                │
│    登录: sun@demo.com   →  zhou/wu/zheng/feng          │
│    项目: ShopNow 电商平台 (SN)                            │
│                                                        │
│  团队 3: FitLife 健身团队                                │
│    登录: qian@demo.com  →  yang/huang/xu/zhu           │
│    项目: FitLife 健身 App (FL)                           │
├────────────────────────────────────────────────────────┤
│  全部密码: Demo123456                                   │
│  工作空间: {total_ws} 个   任务总数: {total_tasks} 个   评论: {total_comments} 条       │
└────────────────────────────────────────────────────────┘
""")
