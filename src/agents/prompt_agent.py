"""Prompt Agent — 纯 Prompt 驱动的 Agent，用于评测 Prompt 工程效果"""

from __future__ import annotations
import time

from langchain_core.messages import SystemMessage, HumanMessage

from src.agents.base_agent import BaseAgent
from src.models.agent_config import AgentConfig
from src.models.evaluation import SingleResult

DEFAULT_SYSTEM_PROMPT = """你是一个专业的AI助手。请准确、简洁、有条理地回答用户的问题。
如果不确定答案，请诚实说明，不要编造信息。"""


class PromptAgent(BaseAgent):
    """
    纯 Prompt Agent：不使用外部知识库或工具，仅依靠系统提示词和 LLM 能力回答问题。
    适用于测试不同 Prompt 模板对输出质量的影响。
    """

    def __init__(self, config: AgentConfig | None = None):
        if config is None:
            config = AgentConfig(
                agent_type="prompt",
                system_prompt=DEFAULT_SYSTEM_PROMPT,
            )
        super().__init__(config)
        self.system_prompt = config.system_prompt or DEFAULT_SYSTEM_PROMPT

    async def run(self, input_text: str, test_case_id: str = "") -> SingleResult:
        # 1. 创建 Langfuse trace
        trace = self._create_trace(input_text, test_case_id)
        trace_id = trace.id if trace else None

        # 2. 构造消息并调用 LLM
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=input_text),
        ]

        start = time.perf_counter()
        response = await self.llm.ainvoke(messages)
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        agent_output = response.content
        token_usage = {
            "prompt_tokens": response.usage_metadata.get("input_tokens", 0) if response.usage_metadata else 0,
            "completion_tokens": response.usage_metadata.get("output_tokens", 0) if response.usage_metadata else 0,
            "total_tokens": response.usage_metadata.get("total_tokens", 0) if response.usage_metadata else 0,
        }

        # 3. 记录 Langfuse span
        if trace:
            trace.span(
                name="prompt-agent-invoke",
                input={"messages": [{"role": "system", "content": self.system_prompt},
                                    {"role": "user", "content": input_text}]},
                output=agent_output,
                metadata={"latency_ms": elapsed_ms, **token_usage},
            )

        # 4. 构造结果
        return self._build_base_result(
            test_case_id=test_case_id,
            input_text=input_text,
            agent_output=agent_output,
            latency_ms=elapsed_ms,
            token_usage=token_usage,
            trace_id=trace_id,
        )
