"""Agent 基类 — 所有评测 Agent 的抽象父类"""

from __future__ import annotations
import time
from abc import ABC, abstractmethod
from typing import Optional

from langchain_openai import ChatOpenAI

from config.settings import OPENAI_API_KEY, OPENAI_BASE_URL
from src.models.agent_config import AgentConfig, AgentType
from src.models.evaluation import SingleResult
from src.integrations.langfuse_client import get_langfuse_client


class BaseAgent(ABC):
    """
    Agent 基类：封装 LLM 调用、Langfuse 追踪、结果收集的通用逻辑。
    子类只需实现 build_chain() 即可。
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self.llm = ChatOpenAI(
            model=config.model_name,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL,
        )
        self.langfuse = get_langfuse_client() if config.enable_tracing else None

    @property
    def agent_type(self) -> str:
        return self.config.agent_type.value

    @abstractmethod
    async def run(self, input_text: str, test_case_id: str = "") -> SingleResult:
        """
        执行一次 Agent 推理，返回 SingleResult。
        子类需实现具体的推理逻辑。
        """
        ...

    def _create_trace(self, input_text: str, test_case_id: str):
        """创建 Langfuse trace（如启用）"""
        if not self.langfuse:
            return None
        return self.langfuse.trace(
            name=f"eval-{self.agent_type}",
            input=input_text,
            metadata={
                "agent_type": self.agent_type,
                "model": self.config.model_name,
                "test_case_id": test_case_id,
            },
        )

    def _build_base_result(
        self,
        test_case_id: str,
        input_text: str,
        agent_output: str,
        latency_ms: int,
        token_usage: dict,
        trace_id: Optional[str] = None,
    ) -> SingleResult:
        """构造基础结果对象，供子类补充评分"""
        return SingleResult(
            test_case_id=test_case_id,
            agent_type=self.agent_type,
            input_text=input_text,
            agent_output=agent_output,
            latency_ms=latency_ms,
            token_usage=token_usage,
            trace_id=trace_id,
        )
