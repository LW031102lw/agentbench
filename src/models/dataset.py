"""评测集数据模型"""

from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class TestCase(BaseModel):
    """单条评测用例"""
    id: str = Field(..., description="用例唯一标识")
    input_text: str = Field(..., description="输入文本/用户问题")
    expected_output: Optional[str] = Field(None, description="期望输出（可选）")
    category: str = Field("general", description="分类标签")
    difficulty: DifficultyLevel = Field(DifficultyLevel.MEDIUM, description="难度等级")
    metadata: dict = Field(default_factory=dict, description="扩展元数据")
    tags: list[str] = Field(default_factory=list, description="标签列表")


class EvalDimension(BaseModel):
    """评测维度定义"""
    name: str = Field(..., description="维度名称，如 accuracy / safety / fluency")
    weight: float = Field(1.0, description="权重（用于加权总分）")
    scoring_rubric: str = Field("", description="评分标准说明")
    max_score: float = Field(5.0, description="该维度的满分值")


class Dataset(BaseModel):
    """评测集"""
    id: str = Field(..., description="评测集 ID")
    name: str = Field(..., description="评测集名称")
    description: str = Field("", description="描述")
    version: str = Field("1.0.0", description="版本号")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    test_cases: list[TestCase] = Field(default_factory=list)
    dimensions: list[EvalDimension] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    @property
    def size(self) -> int:
        return len(self.test_cases)


class DatasetImportRequest(BaseModel):
    """导入评测集请求"""
    name: str
    description: str = ""
    format: str = Field("json", description="导入格式: json / csv")
    content: str = Field(..., description="文件内容（JSON 或 CSV 文本）")
