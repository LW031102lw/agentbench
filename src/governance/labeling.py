"""数据标注 — 为评测数据建立统一的标签分类体系"""

from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, Field


class LabelCategory(str, Enum):
    """标签大类"""
    DOMAIN = "domain"           # 业务领域
    DIFFICULTY = "difficulty"   # 难度级别
    SCENARIO = "scenario"       # 使用场景
    QUALITY = "quality"         # 数据质量
    CUSTOM = "custom"           # 自定义标签


class Label(BaseModel):
    """标签定义"""
    name: str
    category: LabelCategory
    description: str = ""
    color: str = "#6366f1"


class LabelRegistry:
    """
    统一标签注册中心：管理所有评测数据的标签体系。
    确保不同评测批次使用一致的标签分类。
    """

    def __init__(self):
        self._labels: dict[str, Label] = {}
        self._init_default_labels()

    def _init_default_labels(self):
        """初始化默认标签体系"""
        defaults = [
            Label(name="通用对话", category=LabelCategory.DOMAIN, description="日常闲聊、常识问答"),
            Label(name="知识问答", category=LabelCategory.DOMAIN, description="需要专业知识的问题"),
            Label(name="代码生成", category=LabelCategory.DOMAIN, description="编程相关问题"),
            Label(name="数学推理", category=LabelCategory.DOMAIN, description="数学计算和推理"),
            Label(name="简单", category=LabelCategory.DIFFICULTY, description="基础问题，无需复杂推理"),
            Label(name="中等", category=LabelCategory.DIFFICULTY, description="需要一定推理能力"),
            Label(name="困难", category=LabelCategory.DIFFICULTY, description="需要多步推理或专业知识"),
            Label(name="单轮对话", category=LabelCategory.SCENARIO, description="单轮问答"),
            Label(name="多轮对话", category=LabelCategory.SCENARIO, description="多轮上下文依赖"),
            Label(name="工具调用", category=LabelCategory.SCENARIO, description="需要使用外部工具"),
            Label(name="高质量", category=LabelCategory.QUALITY, description="经过人工审核的高质量数据"),
            Label(name="待审核", category=LabelCategory.QUALITY, description="需要人工复核"),
        ]
        for label in defaults:
            self.register(label)

    def register(self, label: Label) -> None:
        """注册新标签"""
        key = f"{label.category.value}:{label.name}"
        self._labels[key] = label

    def get(self, name: str, category: LabelCategory | None = None) -> Label | None:
        """查询标签"""
        if category:
            key = f"{category.value}:{name}"
            return self._labels.get(key)
        # 模糊搜索
        for label in self._labels.values():
            if label.name == name:
                return label
        return None

    def list_all(self) -> list[Label]:
        """列出所有标签"""
        return list(self._labels.values())

    def list_by_category(self, category: LabelCategory) -> list[Label]:
        """按分类列出标签"""
        return [l for l in self._labels.values() if l.category == category]

    def tag_test_case(self, tags: list[str], label_names: list[str]) -> list[str]:
        """为用例打标签，返回合并后的标签列表"""
        validated = []
        for name in label_names:
            if self.get(name):
                validated.append(name)
            else:
                print(f"[LabelRegistry] 警告: 标签 '{name}' 未注册，已跳过")
        return list(set(tags + validated))
