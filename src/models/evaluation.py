"""评测结果数据模型"""

from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class EvalStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AttributionLayer(str, Enum):
    PROMPT = "prompt"
    RAG = "rag"
    TOOL = "tool"


class DimensionScore(BaseModel):
    """单维度评分"""
    dimension: str = Field(..., description="维度名称")
    score: float = Field(..., description="得分")
    max_score: float = Field(5.0)
    reasoning: str = Field("", description="评分理由（LLM-as-Judge 输出）")


class SingleResult(BaseModel):
    """单条评测结果"""
    test_case_id: str
    agent_type: str = Field(..., description="Agent 类型: prompt / rag / tool")
    input_text: str
    agent_output: str
    expected_output: Optional[str] = None
    scores: list[DimensionScore] = Field(default_factory=list)
    total_score: float = 0.0
    latency_ms: int = Field(0, description="响应耗时（毫秒）")
    token_usage: dict = Field(default_factory=dict, description="token 用量 {prompt, completion, total}")
    trace_id: Optional[str] = Field(None, description="Langfuse trace ID")
    attribution_layer: Optional[AttributionLayer] = Field(None, description="如有问题，归因到哪一层")
    attribution_detail: str = Field("", description="归因分析详情")
    created_at: datetime = Field(default_factory=datetime.now)


class EvalReport(BaseModel):
    """评测报告"""
    id: str
    dataset_id: str
    dataset_name: str
    agent_type: str
    model_name: str = "gpt-4o-mini"
    status: EvalStatus = EvalStatus.PENDING
    total_cases: int = 0
    completed_cases: int = 0
    results: list[SingleResult] = Field(default_factory=list)
    # 汇总统计
    avg_score: float = 0.0
    dimension_avg: dict[str, float] = Field(default_factory=dict)
    pass_rate: float = Field(0.0, description="通过率（总分 >= 60% 视为通过）")
    avg_latency_ms: float = 0.0
    # 归因统计
    attribution_summary: dict[str, int] = Field(
        default_factory=dict,
        description="归因层统计 {prompt: N, rag: N, tool: N}",
    )
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
