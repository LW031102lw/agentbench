"""数据治理 API"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.governance.labeling import LabelRegistry
from src.governance.quality_check import QualityChecker
from src.governance.statistics import StatisticsManager

router = APIRouter()

label_registry = LabelRegistry()
quality_checker = QualityChecker()
stats_manager = StatisticsManager()

from src.api.routes.datasets import _datasets


@router.get("/labels", summary="获取标签体系")
async def list_labels(category: str | None = None):
    if category:
        from src.governance.labeling import LabelCategory
        cat = LabelCategory(category)
        return label_registry.list_by_category(cat)
    return label_registry.list_all()


@router.get("/quality/{dataset_id}", summary="数据质量校验")
async def check_quality(dataset_id: str):
    dataset = _datasets.get(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="评测集不存在")
    report = quality_checker.check(dataset)
    return report


@router.get("/metrics", summary="获取指标定义（统计口径）")
async def list_metrics():
    return stats_manager.list_metrics()


@router.get("/statistics/history", summary="评测历史统计")
async def get_history():
    return stats_manager.get_history()


@router.get("/statistics/compare", summary="对比两份评测报告")
async def compare_reports(report_a_id: str, report_b_id: str):
    from src.api.routes.evaluations import _reports
    a = _reports.get(report_a_id)
    b = _reports.get(report_b_id)
    if not a or not b:
        raise HTTPException(status_code=404, detail="评测报告不存在")
    return stats_manager.compare_reports(a, b)
