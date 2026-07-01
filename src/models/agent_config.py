"""Agent 配置模型"""

from __future__ import annotations
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AgentType(str, Enum):
    PROMPT = "prompt"
    RAG = "rag"
    TOOL = "tool"


class AgentConfig(BaseModel):
    """Agent 运行配置"""
    agent_type: AgentType = Field(AgentType.PROMPT)
    model_name: str = Field("gpt-4o-mini", description="使用的 LLM 模型")
    temperature: float = Field(0.0, description="温度（评测场景建议 0）")
    max_tokens: int = Field(2048)
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    # RAG 相关
    knowledge_base_path: Optional[str] = Field(None, description="知识库路径")
    top_k: int = Field(3, description="RAG 检索 top-K")
    chunk_size: int = Field(500, description="文档切分大小")
    # Tool 相关
    tools: list[dict] = Field(default_factory=list, description="可用工具定义")
    # Langfuse
    enable_tracing: bool = Field(True, description="是否启用 Langfuse 追踪")
