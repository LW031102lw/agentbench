"""归因分析 API"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.attribution import AttributionEngine
from src.models.evaluation import AttributionLayer

router = APIRouter()
engine = AttributionEngine()

# 引用评测报告存储
from src.api.routes.evaluations import _reports


class AttributionRequest(BaseModel):
    input_text: str
    agent_output: str
    agent_type: str = "prompt"
    expected_output: str | None = None


@router.post("/analyze", summary="执行单条归因分析")
async def analyze(req: AttributionRequest):
    layer, detail = await engine.analyze(
        input_text=req.input_text,
        agent_output=req.agent_output,
        agent_type=req.agent_type,
        expected_output=req.expected_output,
    )
    return {
        "attribution_layer": layer.value if layer else None,
        "detail": detail,
    }


@router.get("/report/{report_id}/summary", summary="获取评测报告的归因汇总")
async def get_attribution_summary(report_id: str):
    report = _reports.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="评测报告不存在")

    # 收集所有有归因信息的用例
    attributed = [
        {
            "test_case_id": r.test_case_id,
            "input": r.input_text[:100],
            "score": r.total_score,
            "layer": r.attribution_layer.value if r.attribution_layer else None,
            "detail": r.attribution_detail[:200],
        }
        for r in report.results
        if r.attribution_layer
    ]

    return {
        "report_id": report_id,
        "total_issues": len(attributed),
        "summary": report.attribution_summary,
        "details": attributed,
    }
