"""统计口径管理 — 确保评测指标计算方式一致"""

from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, Field

from src.models.evaluation import EvalReport


class MetricType(str, Enum):
    AVG_SCORE = "avg_score"
    PASS_RATE = "pass_rate"
    DIMENSION_AVG = "dimension_avg"
    AVG_LATENCY = "avg_latency"
    ATTRIBUTION_DIST = "attribution_distribution"


class MetricDefinition(BaseModel):
    """指标定义 — 统一统计口径"""
    name: MetricType
    display_name: str
    description: str
    formula: str = Field(..., description="计算公式说明")
    unit: str = ""


# ── 标准指标定义 ──────────────────────────────────────

STANDARD_METRICS: list[MetricDefinition] = [
    MetricDefinition(
        name=MetricType.AVG_SCORE,
        display_name="平均得分",
        description="所有评测用例加权总分的算术平均值",
        formula="sum(total_score) / count(cases)",
    ),
    MetricDefinition(
        name=MetricType.PASS_RATE,
        display_name="通过率",
        description="总分达到满分 60% 以上的用例占比",
        formula="count(score >= max_score * 0.6) / count(cases)",
    ),
    MetricDefinition(
        name=MetricType.DIMENSION_AVG,
        display_name="维度平均分",
        description="各评测维度的平均得分",
        formula="sum(dimension_score) / count(cases) per dimension",
    ),
    MetricDefinition(
        name=MetricType.AVG_LATENCY,
        display_name="平均延迟",
        description="Agent 响应时间的算术平均值",
        formula="sum(latency_ms) / count(cases)",
        unit="ms",
    ),
    MetricDefinition(
        name=MetricType.ATTRIBUTION_DIST,
        display_name="归因分布",
        description="问题用例在各归因层的分布比例",
        formula="count(layer) / count(issues) per layer",
    ),
]


class StatisticsManager:
    """
    统计口径管理器：
    - 确保不同评测批次的指标计算方式一致
    - 提供标准化的指标查询和对比功能
    - 记录数据血缘（哪个评测集 → 哪个报告 → 哪些指标）
    """

    def __init__(self):
        self.metrics = {m.name: m for m in STANDARD_METRICS}
        self._history: list[dict] = []  # 评测历史（用于对比分析）

    def get_metric_definition(self, name: MetricType) -> MetricDefinition | None:
        return self.metrics.get(name)

    def list_metrics(self) -> list[MetricDefinition]:
        return list(self.metrics.values())

    def record_report(self, report: EvalReport) -> None:
        """记录评测报告，用于后续的跨批次对比"""
        entry = {
            "report_id": report.id,
            "dataset_id": report.dataset_id,
            "dataset_name": report.dataset_name,
            "agent_type": report.agent_type,
            "model_name": report.model_name,
            "avg_score": report.avg_score,
            "pass_rate": report.pass_rate,
            "dimension_avg": report.dimension_avg,
            "avg_latency_ms": report.avg_latency_ms,
            "attribution_summary": report.attribution_summary,
            "completed_at": str(report.completed_at),
        }
        self._history.append(entry)

    def compare_reports(self, report_a: EvalReport, report_b: EvalReport) -> dict:
        """对比两份评测报告的核心指标差异"""
        return {
            "avg_score_diff": round(report_b.avg_score - report_a.avg_score, 2),
            "pass_rate_diff": round(report_b.pass_rate - report_a.pass_rate, 4),
            "avg_latency_diff": round(report_b.avg_latency_ms - report_a.avg_latency_ms, 1),
            "dimension_diff": {
                dim: round(
                    report_b.dimension_avg.get(dim, 0) - report_a.dimension_avg.get(dim, 0), 2
                )
                for dim in set(report_a.dimension_avg) | set(report_b.dimension_avg)
            },
        }

    def get_history(self) -> list[dict]:
        return self._history
