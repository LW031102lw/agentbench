"""评测执行 API"""

from __future__ import annotations
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.models.agent_config import AgentConfig, AgentType
from src.pipeline.eval_pipeline import EvalPipeline
from src.models.evaluation import EvalReport

router = APIRouter()

# 存储评测报告
_reports: dict[str, EvalReport] = {}

# 引用 datasets 路由中的内存存储（实际项目中应使用依赖注入）
from src.api.routes.datasets import _datasets


class EvalRunRequest(BaseModel):
    dataset_id: str
    agent_type: str = "prompt"
    model_name: str = "gpt-4o-mini"
    temperature: float = 0.0
    concurrency: int = 5


@router.post("/run", summary="执行评测")
async def run_evaluation(req: EvalRunRequest):
    dataset = _datasets.get(req.dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="评测集不存在")

    config = AgentConfig(
        agent_type=req.agent_type,
        model_name=req.model_name,
        temperature=req.temperature,
    )

    pipeline = EvalPipeline(
        agent_config=config,
        concurrency=req.concurrency,
    )

    report = await pipeline.run(dataset)
    _reports[report.id] = report

    return {
        "report_id": report.id,
        "status": report.status.value,
        "total_cases": report.total_cases,
        "avg_score": report.avg_score,
        "pass_rate": report.pass_rate,
    }


@router.get("/reports", summary="获取所有评测报告")
async def list_reports():
    return [
        {
            "id": r.id,
            "dataset_name": r.dataset_name,
            "agent_type": r.agent_type,
            "avg_score": r.avg_score,
            "pass_rate": r.pass_rate,
            "status": r.status.value,
            "created_at": str(r.created_at),
        }
        for r in _reports.values()
    ]


@router.get("/reports/{report_id}", summary="获取评测报告详情")
async def get_report(report_id: str):
    report = _reports.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="评测报告不存在")
    return report
