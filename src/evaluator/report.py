"""评测报告生成器 — 汇总评测结果生成结构化报告"""

from __future__ import annotations
from datetime import datetime
from collections import defaultdict

from src.models.evaluation import EvalReport, SingleResult, EvalStatus


class ReportGenerator:
    """将一组 SingleResult 汇总为 EvalReport，包含统计分析和归因摘要"""

    @staticmethod
    def generate(
        report_id: str,
        dataset_id: str,
        dataset_name: str,
        agent_type: str,
        model_name: str,
        results: list[SingleResult],
    ) -> EvalReport:
        if not results:
            return EvalReport(
                id=report_id,
                dataset_id=dataset_id,
                dataset_name=dataset_name,
                agent_type=agent_type,
                model_name=model_name,
                status=EvalStatus.COMPLETED,
            )

        # ── 基础统计 ──────────────────────────────────
        total = len(results)
        scores = [r.total_score for r in results]
        avg_score = sum(scores) / total if scores else 0.0
        avg_latency = sum(r.latency_ms for r in results) / total

        # 通过率（总分达到满分的 60%）
        max_possible = max(r.scores[0].max_score * len(r.scores) for r in results if r.scores) if results and any(r.scores for r in results) else 5.0
        pass_count = sum(1 for s in scores if s >= max_possible * 0.6)
        pass_rate = pass_count / total

        # ── 各维度平均分 ──────────────────────────────
        dim_scores: dict[str, list[float]] = defaultdict(list)
        for r in results:
            for ds in r.scores:
                dim_scores[ds.dimension].append(ds.score)
        dimension_avg = {
            dim: round(sum(vals) / len(vals), 2)
            for dim, vals in dim_scores.items()
        }

        # ── 归因统计 ──────────────────────────────────
        attr_summary: dict[str, int] = defaultdict(int)
        for r in results:
            if r.attribution_layer:
                attr_summary[r.attribution_layer.value] += 1

        report = EvalReport(
            id=report_id,
            dataset_id=dataset_id,
            dataset_name=dataset_name,
            agent_type=agent_type,
            model_name=model_name,
            status=EvalStatus.COMPLETED,
            total_cases=total,
            completed_cases=total,
            results=results,
            avg_score=round(avg_score, 2),
            dimension_avg=dimension_avg,
            pass_rate=round(pass_rate, 4),
            avg_latency_ms=round(avg_latency, 1),
            attribution_summary=dict(attr_summary),
            completed_at=datetime.now(),
        )
        return report

    @staticmethod
    def to_markdown(report: EvalReport) -> str:
        """将报告导出为 Markdown 格式"""
        lines = [
            f"# 评测报告: {report.dataset_name}",
            f"",
            f"**Agent 类型**: {report.agent_type}  ",
            f"**模型**: {report.model_name}  ",
            f"**评测时间**: {report.completed_at or report.created_at}  ",
            f"**用例总数**: {report.total_cases}  ",
            f"",
            f"## 汇总指标",
            f"",
            f"| 指标 | 值 |",
            f"|------|------|",
            f"| 平均分 | {report.avg_score} |",
            f"| 通过率 | {report.pass_rate:.1%} |",
            f"| 平均延迟 | {report.avg_latency_ms:.0f}ms |",
            f"",
            f"## 各维度得分",
            f"",
            f"| 维度 | 平均分 |",
            f"|------|--------|",
        ]
        for dim, avg in report.dimension_avg.items():
            lines.append(f"| {dim} | {avg} |")

        if report.attribution_summary:
            lines.extend([
                "",
                "## 归因分析统计",
                "",
                "| 归因层 | 问题数量 |",
                "|--------|----------|",
            ])
            for layer, count in report.attribution_summary.items():
                lines.append(f"| {layer} | {count} |")

        return "\n".join(lines)
