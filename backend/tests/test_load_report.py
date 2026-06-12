"""
正式负载测试报告生成器
========================

对 MiniPlane 后端进行多负载等级的性能基准测试，生成结构化报告。

测试维度:
  负载等级:  空库 → 1K → 10K → 100K 任务
  并发等级:  1 → 10 → 50 → 100 并发用户
  操作类型:  任务列表查询 / 状态筛选 / 关键词搜索 / 状态变更 / 分页导航

报告输出: LOAD_TEST_REPORT.md
"""

import time
import random
import json
import statistics
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

# ── 测试参数 ─────────────────────────────────────────────────────
LOAD_LEVELS = [
    ("空库", 0),
    ("1K", 1_000),
    ("10K", 10_000),
    ("100K", 100_000),
]
CONCURRENCY_LEVELS = [1, 10, 50, 100]
BATCH_SIZE = 5000
REPORT_PATH = Path(__file__).resolve().parent.parent / "LOAD_TEST_REPORT.md"

pytestmark = pytest.mark.django_db


# ═══════════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════════

def _p(data, p_val):
    """百分位计算（线性插值）"""
    if not data:
        return 0.0
    k = (len(data) - 1) * p_val / 100.0
    f = int(k)
    c = k - f
    d = sorted(data)
    if f + 1 < len(d):
        return d[f] + c * (d[f + 1] - d[f])
    return float(d[f])


def _fmt_ms(seconds):
    """格式化为毫秒"""
    if seconds < 0.001:
        return f"{seconds*1_000_000:.0f}μs"
    elif seconds < 1:
        return f"{seconds*1000:.1f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    else:
        m, s = divmod(seconds, 60)
        return f"{int(m)}m{s:.0f}s"


# ═══════════════════════════════════════════════════════════════════
# 正式负载测试
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.django_db(transaction=True)
class TestFormalLoadTest:
    """
    正式负载测试 — 多负载等级 × 多并发等级 × 多操作类型

    生成 LOAD_TEST_REPORT.md 到项目根目录。
    """

    _db_semaphore = threading.Semaphore(50)

    # ── 测试入口 ──────────────────────────────────────────────

    def test_full_load_report(self):
        """主入口：遍历所有负载等级 × 并发等级，收集性能数据"""
        print("\n" + "█" * 70)
        print("█  MiniPlane 正式负载测试 — 多维度性能基准")
        print("█" * 70)

        all_results = {}

        for load_label, task_count in LOAD_LEVELS:
            print(f"\n{'='*60}")
            print(f"  负载等级: {load_label} ({task_count:,} 任务)")
            print(f"{'='*60}")

            # 准备数据
            ctx = self._setup_load_level(task_count)

            level_results = {
                "load_level": load_label,
                "task_count": task_count,
                "setup_time": ctx["setup_time"],
                "concurrency_results": {},
            }

            for concurrency in CONCURRENCY_LEVELS:
                if task_count == 0 and concurrency > 10:
                    # 空库高并发无意义
                    continue
                if task_count > 10_000 and concurrency > 100:
                    continue

                print(f"\n  --- 并发={concurrency} ---")
                cr = self._run_concurrency_level(ctx, concurrency)
                level_results["concurrency_results"][concurrency] = cr

            # 清理输出当前等级的摘要
            self._print_level_summary(load_label, level_results)
            all_results[load_label] = level_results

        # 生成报告
        self._generate_report(all_results)
        print(f"\n  [OK] 报告已生成: {REPORT_PATH}")

    # ── 数据准备 ──────────────────────────────────────────────

    def _setup_load_level(self, task_count):
        """为指定负载等级准备测试数据"""
        from apps.workspaces.models import Workspace, WorkspaceMember
        from apps.projects.models import Project, ProjectMember
        from apps.tasks.models import Task, TaskStatus

        t0 = time.time()

        # 管理员
        admin = User.objects.create_superuser(
            email=f"load_admin_{task_count}@test.com",
            password="LoadTest123",
            name=f"Load Admin {task_count}",
        )

        # 工作空间
        ws = Workspace.objects.create(
            name=f"负载测试 {task_count}",
            slug=f"load-{task_count}",
            owner=admin,
        )
        WorkspaceMember.objects.create(workspace=ws, user=admin, role="admin")

        # 项目 + 状态
        proj = Project.objects.create(
            workspace=ws,
            name="负载测试项目",
            identifier=f"LOAD{task_count}",
        )
        ProjectMember.objects.create(project=proj, user=admin, role="admin")

        statuses = []
        for name, color, type_str, order in [
            ("Backlog", "#6b7280", "backlog", 0),
            ("待办", "#6366f1", "unstarted", 1),
            ("进行中", "#f59e0b", "started", 2),
            ("待评审", "#8b5cf6", "started", 3),
            ("已完成", "#10b981", "completed", 4),
            ("已取消", "#ef4444", "cancelled", 5),
        ]:
            statuses.append(TaskStatus.objects.create(
                project=proj, name=name, color=color, type=type_str, order=order,
            ))

        # 用户池
        assignees = [admin]
        for i in range(min(task_count // 100, 50) if task_count > 0 else 0):
            u = User.objects.create_user(
                email=f"load_u{task_count}_{i:03d}@test.com",
                password="Test123456",
                name=f"User {task_count}_{i:03d}",
            )
            WorkspaceMember.objects.create(workspace=ws, user=u, role="member")
            assignees.append(u)

        if not assignees:
            assignees = [admin]  # 空库时至少有一个

        # 批量创建任务
        if task_count > 0:
            priorities = ["urgent", "high", "medium", "low", "none"]
            task_batch = []
            for i in range(task_count):
                task_batch.append(Task(
                    project=proj,
                    status=statuses[i % len(statuses)],
                    title=f"LOAD-{i:06d}: 负载测试 #{i}",
                    description=f"负载等级 {task_count} 的第 {i} 条任务",
                    priority=priorities[i % len(priorities)],
                    assignee=assignees[i % len(assignees)],
                    created_by=admin,
                    order=float(i),
                ))
                if len(task_batch) >= BATCH_SIZE:
                    Task.objects.bulk_create(task_batch, batch_size=BATCH_SIZE)
                    task_batch = []
            if task_batch:
                Task.objects.bulk_create(task_batch)

        setup_time = time.time() - t0
        actual_count = Task.objects.filter(project=proj).count()

        return {
            "proj_id": str(proj.id),
            "status_ids": [str(s.id) for s in statuses],
            "assignee_ids": [str(u.id) for u in assignees],
            "admin": admin,
            "setup_time": setup_time,
            "actual_count": actual_count,
        }

    # ── 单并发等级测试 ────────────────────────────────────────

    def _run_concurrency_level(self, ctx, concurrency):
        """对指定并发等级执行多操作类型的性能测试"""
        results = {"concurrency": concurrency}

        # A) 任务列表查询
        results["list_query"] = self._benchmark_operation(
            ctx, concurrency,
            operation="list",
            label="列表查询",
        )

        # B) 状态筛选
        if ctx["status_ids"]:
            results["status_filter"] = self._benchmark_operation(
                ctx, concurrency,
                operation="status_filter",
                label="状态筛选",
                extra_params={"status": random.choice(ctx["status_ids"])},
            )

        # C) 关键词搜索
        if ctx["actual_count"] > 0:
            results["search"] = self._benchmark_operation(
                ctx, concurrency,
                operation="search",
                label="关键词搜索",
                extra_params={"search": f"LOAD-{random.randint(0, max(0, ctx['actual_count']-1)):06d}"},
            )

        # D) 组合筛选
        if ctx["status_ids"] and ctx["assignee_ids"]:
            results["combined_filter"] = self._benchmark_operation(
                ctx, concurrency,
                operation="combined",
                label="状态+负责人",
                extra_params={
                    "status": random.choice(ctx["status_ids"]),
                    "assignee": random.choice(ctx["assignee_ids"]),
                },
            )

        return results

    def _benchmark_operation(self, ctx, concurrency, operation, label, extra_params=None):
        """执行并发基准测试"""
        proj_id = ctx["proj_id"]
        url = f"/api/projects/{proj_id}/tasks/"

        def _worker():
            client = APIClient()
            client.force_authenticate(user=ctx["admin"])
            params = extra_params.copy() if extra_params else {}
            t0 = time.time()
            try:
                with TestFormalLoadTest._db_semaphore:
                    resp = client.get(url, params)
                    from django.db import connection
                    connection.close()
                elapsed = time.time() - t0
                return {
                    "elapsed": elapsed,
                    "status": resp.status_code,
                    "result_count": len(resp.json().get("data", [])),
                }
            except Exception as e:
                return {
                    "elapsed": time.time() - t0,
                    "status": 0,
                    "error": str(e),
                }

        results = []
        wall_t0 = time.time()
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(_worker) for _ in range(concurrency)]
            for f in as_completed(futures):
                results.append(f.result())
        wall_time = time.time() - wall_t0

        elapsed_times = sorted([r["elapsed"] for r in results])
        success = sum(1 for r in results if r["status"] == 200)
        errors = len(results) - success
        throughput = len(results) / wall_time if wall_time > 0 else 0

        return {
            "operation": operation,
            "label": label,
            "requests": len(results),
            "success": success,
            "errors": errors,
            "wall_time": wall_time,
            "throughput": throughput,
            "avg": statistics.mean(elapsed_times) if elapsed_times else 0,
            "min": min(elapsed_times) if elapsed_times else 0,
            "max": max(elapsed_times) if elapsed_times else 0,
            "p50": _p(elapsed_times, 50),
            "p90": _p(elapsed_times, 90),
            "p95": _p(elapsed_times, 95),
            "p99": _p(elapsed_times, 99),
            "std_dev": statistics.stdev(elapsed_times) if len(elapsed_times) >= 2 else 0,
        }

    # ── 摘要输出 ──────────────────────────────────────────────

    def _print_level_summary(self, load_label, level_results):
        print(f"\n  {'─'*55}")
        print(f"  {load_label} 摘要")
        for concurrency, cr in level_results["concurrency_results"].items():
            lq = cr.get("list_query", {})
            sf = cr.get("status_filter", {})
            print(f"    并发={concurrency:3d}: "
                  f"列表={_fmt_ms(lq.get('avg', 0))} "
                  f"P95={_fmt_ms(lq.get('p95', 0))} | "
                  f"筛选={_fmt_ms(sf.get('avg', 0))} "
                  f"P95={_fmt_ms(sf.get('p95', 0))}")
        print(f"  {'─'*55}")

    # ── 报告生成 ──────────────────────────────────────────────

    def _generate_report(self, all_results):
        """生成结构化 Markdown 报告"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        lines = []
        lines.append(f"# MiniPlane 正式负载测试报告\n")
        lines.append(f"> **测试时间**: {now}")
        lines.append(f"> **测试框架**: pytest + pytest-django + ThreadPoolExecutor")
        lines.append(f"> **数据库**: PostgreSQL 16 (Docker)")
        lines.append(f"> **测试环境**: Windows 11, Python 3.12, Django 6.0\n")
        lines.append("---\n")

        # ── 1. 测试概览 ──
        lines.append("## 一、测试概览\n")
        lines.append("| 负载等级 | 任务数 | 数据准备耗时 | 并发等级 | 全量列表P95 | 状态筛选P95 | 状态+负责人P95 | 搜索P95 | 吞吐量(qps) |")
        lines.append("|----------|--------|-------------|----------|------------|------------|---------------|---------|-------------|")

        for load_label, lr in all_results.items():
            for concurrency, cr in sorted(lr["concurrency_results"].items()):
                lq = cr.get("list_query", {})
                sf = cr.get("status_filter", {})
                cf = cr.get("combined_filter", {})
                sr = cr.get("search", {})
                tp = lq.get("throughput", 0)
                lines.append(
                    f"| {load_label} | {lr['task_count']:,} | "
                    f"{_fmt_ms(lr['setup_time'])} | "
                    f"{concurrency} | {_fmt_ms(lq.get('p95', 0))} | "
                    f"{_fmt_ms(sf.get('p95', 0))} | "
                    f"{_fmt_ms(cf.get('p95', 0))} | "
                    f"{_fmt_ms(sr.get('p95', 0))} | "
                    f"{tp:.1f} |"
                )

        lines.append("")

        # ── 2. 列表查询详解 ──
        lines.append("## 二、任务列表查询 — 多负载对比\n")
        lines.append("### P95 响应时间 (ms)\n")
        lines.append("| 负载\\并发 | 1 | 10 | 50 | 100 |")
        lines.append("|------------|----|----|----|-----|")

        for load_label, lr in all_results.items():
            row = f"| {load_label} ({lr['task_count']:,}) "
            for concurrency in CONCURRENCY_LEVELS:
                cr = lr["concurrency_results"].get(concurrency, {})
                lq = cr.get("list_query", {})
                if lq:
                    row += f"| {_fmt_ms(lq['p95'])} "
                else:
                    row += "| — "
            row += "|"
            lines.append(row)
        lines.append("")

        # ── 3. 吞吐量分析 ──
        lines.append("## 三、吞吐量分析 (requests/sec)\n")
        lines.append("| 负载\\并发 | 1 | 10 | 50 | 100 |")
        lines.append("|------------|----|----|----|-----|")

        for load_label, lr in all_results.items():
            row = f"| {load_label} ({lr['task_count']:,}) "
            for concurrency in CONCURRENCY_LEVELS:
                cr = lr["concurrency_results"].get(concurrency, {})
                lq = cr.get("list_query", {})
                if lq:
                    row += f"| {lq['throughput']:.1f} "
                else:
                    row += "| — "
            row += "|"
            lines.append(row)
        lines.append("")

        # ── 4. QS1 场景验证 (按状态+负责人筛选) ──
        lines.append("## 四、QS1 场景验证\n")
        lines.append("> **QS1 需求**: 100 并发用户按状态和负责人筛选 10 万条任务，P95 ≤ 2.0s\n")
        lines.append("| 指标 | 要求 | 实测 | 结果 |")
        lines.append("|------|------|------|------|")

        # QS1 场景: "按状态和负责人筛选" → combined_filter
        qs1_data = None
        if "100K" in all_results:
            cr = all_results["100K"]["concurrency_results"].get(100, {})
            cf = cr.get("combined_filter", {})
            sf = cr.get("status_filter", {})
            if cf:
                qs1_data = (cf, sf)

        if qs1_data:
            cf, sf = qs1_data
            cf_pass = cf["p95"] <= 2.0
            cf_err_pass = cf["errors"] == 0
            lines.append(f"| 状态+负责人筛选 P95 | ≤ 2.0s | {_fmt_ms(cf['p95'])} | {'✅' if cf_pass else '❌'} |")
            lines.append(f"| 状态+负责人筛选 错误率 | 0% | {cf['errors']}/{cf['requests']} | {'✅' if cf_err_pass else '❌'} |")
            lines.append(f"| 仅状态筛选 P95 | ≤ 2.0s | {_fmt_ms(sf['p95'])} | {'✅' if sf.get('p95', 99) <= 2.0 else '❌'} |")
            lines.append(f"| 仅状态筛选 成功率 | 100% | {sf.get('success', '?')}/{sf.get('requests', '?')} | {'✅' if sf.get('errors', 0) == 0 else '❌'} |")
        else:
            lines.append("| — | — | 未执行 | ⚠️ |")
        lines.append("")

        # ── 5. 瓶颈分析 ──
        lines.append("## 五、瓶颈分析\n")

        # 计算负载增长率
        growth_data = []
        for load_label, lr in all_results.items():
            cr = lr["concurrency_results"].get(1, {})
            lq = cr.get("list_query", {})
            if lq:
                growth_data.append((lr["task_count"], lq["avg"]))

        if len(growth_data) >= 2:
            lines.append("### 响应时间增长率\n")
            lines.append("| 负载变化 | 响应时间变化 | 增长倍数 |")
            lines.append("|----------|-------------|---------|")
            for i in range(1, len(growth_data)):
                prev_cnt, prev_time = growth_data[i - 1]
                curr_cnt, curr_time = growth_data[i]
                ratio = curr_time / prev_time if prev_time > 0 else float('inf')
                lines.append(
                    f"| {prev_cnt:,} → {curr_cnt:,} | "
                    f"{_fmt_ms(prev_time)} → {_fmt_ms(curr_time)} | "
                    f"{ratio:.1f}x |"
                )
            lines.append("")

        # ── 6. 结论与建议 ──
        lines.append("## 六、结论与建议\n")

        # QS1 场景: 按状态+负责人筛选 → combined_filter
        qs1_pass = True
        if "100K" in all_results:
            cr = all_results["100K"]["concurrency_results"].get(100, {})
            cf = cr.get("combined_filter", {})
            if cf and cf["p95"] > 2.0:
                qs1_pass = False

        if qs1_pass:
            lines.append("✅ **QS1 性能目标达成**: 100K 任务 / 100 并发下，状态+负责人筛选 P95 ≤ 2 秒。\n")
        else:
            lines.append("⚠️ **QS1 未达标**: 详见上表。建议：\n")
            lines.append("1. 检查数据库索引是否覆盖高频查询字段组合\n")
            lines.append("2. 考虑为 10 万+ 任务场景引入 Redis 缓存\n")
            lines.append("3. 增加 PostgreSQL `shared_buffers` 和 `effective_cache_size`\n")

        # 全量列表查询的独立分析
        worst_list = None
        for load_label, lr in all_results.items():
            for concurrency, cr in lr["concurrency_results"].items():
                lq = cr.get("list_query", {})
                if lq and lq["p95"] > 2.0:
                    if worst_list is None or lq["p95"] > worst_list["p95"]:
                        worst_list = {"load": load_label, "concurrency": concurrency, "p95": lq["p95"]}
        if worst_list:
            lines.append(f"\n> ⚠️ 全量列表查询（无筛选）在 {worst_list['load']}/{worst_list['concurrency']}并发 "
                         f"下 P95={_fmt_ms(worst_list['p95'])}，超出 2s。该场景不在 QS1 范围内，但建议关注。\n")

        lines.append("### 架构建议\n")
        lines.append("1. **索引优化**: 为 `(project, status, assignee)` 创建联合索引\n")
        lines.append("2. **缓存策略**: 高频查询结果缓存至 Redis，TTL 30s\n")
        lines.append("3. **连接池**: 配置 `CONN_MAX_AGE=60` 复用数据库连接\n")
        lines.append("4. **只读副本**: 100K+ 任务场景建议引入读副本分流查询\n")
        lines.append("5. **分页限制**: 限制 `page_size` 最大 50，防止深度分页拖垮数据库\n")

        # 写入文件
        report_content = "\n".join(lines)
        REPORT_PATH.write_text(report_content, encoding="utf-8")
        print(f"\n  [OK] 报告已写入: {REPORT_PATH} ({len(report_content)} 字符)")
