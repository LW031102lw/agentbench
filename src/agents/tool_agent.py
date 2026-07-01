"""Tool Agent — 带工具调用能力的 Agent，用于评测 API/SQL 生成能力"""

from __future__ import annotations
import json
import time

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from src.agents.base_agent import BaseAgent
from src.models.agent_config import AgentConfig
from src.models.evaluation import SingleResult

# ── 预定义工具集（示例） ─────────────────────────────
SAMPLE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_database",
            "description": "在数据库中搜索符合条件的记录，返回匹配的行",
            "parameters": {
                "type": "object",
                "properties": {
                    "table": {"type": "string", "description": "表名"},
                    "condition": {"type": "string", "description": "SQL WHERE 条件"},
                    "limit": {"type": "integer", "description": "返回条数上限", "default": 10},
                },
                "required": ["table", "condition"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "call_weather_api",
            "description": "查询指定城市的实时天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称"},
                    "date": {"type": "string", "description": "日期，格式 YYYY-MM-DD，默认今天"},
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "执行数学计算并返回结果",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "数学表达式，如 '2 + 3 * 4'"},
                },
                "required": ["expression"],
            },
        },
    },
]

TOOL_SYSTEM_PROMPT = """你是一个智能助手，可以使用以下工具来帮助用户：
- search_database: 搜索数据库记录
- call_weather_api: 查询天气
- calculate: 执行数学计算

当用户的问题需要使用工具时，请正确选择工具并构造参数。
如果不需要工具，直接回答即可。"""


class ToolAgent(BaseAgent):
    """
    Tool Agent：具有工具调用能力的 Agent，可执行函数调用（Function Calling）。
    用于评测：工具选择正确性、参数构造准确性、SQL 生成质量等。
    """

    def __init__(self, config: AgentConfig | None = None):
        if config is None:
            config = AgentConfig(agent_type="tool")
        super().__init__(config)
        self.tools = config.tools if config.tools else SAMPLE_TOOLS
        # 使用支持 tool calling 的 LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools) if self.tools else self.llm

    async def run(self, input_text: str, test_case_id: str = "") -> SingleResult:
        trace = self._create_trace(input_text, test_case_id)
        trace_id = trace.id if trace else None

        messages = [
            SystemMessage(content=TOOL_SYSTEM_PROMPT),
            HumanMessage(content=input_text),
        ]

        start = time.perf_counter()
        response = await self.llm_with_tools.ainvoke(messages)
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        # 解析工具调用
        tool_calls_info = []
        agent_output = response.content or ""

        if hasattr(response, "tool_calls") and response.tool_calls:
            for tc in response.tool_calls:
                tool_calls_info.append({
                    "tool_name": tc.get("name", ""),
                    "arguments": tc.get("args", {}),
                    "call_id": tc.get("id", ""),
                })
            # 如果有工具调用，将调用详情作为输出的一部分
            agent_output = (
                f"{agent_output}\n\n[Tool Calls]: {json.dumps(tool_calls_info, ensure_ascii=False)}"
            )

        token_usage = {
            "prompt_tokens": response.usage_metadata.get("input_tokens", 0) if response.usage_metadata else 0,
            "completion_tokens": response.usage_metadata.get("output_tokens", 0) if response.usage_metadata else 0,
            "total_tokens": response.usage_metadata.get("total_tokens", 0) if response.usage_metadata else 0,
        }

        # 记录 Langfuse span
        if trace:
            trace.span(
                name="tool-agent-invoke",
                input={"messages": messages, "tools": self.tools},
                output={"content": agent_output, "tool_calls": tool_calls_info},
                metadata={"latency_ms": elapsed_ms, "num_tool_calls": len(tool_calls_info), **token_usage},
            )

        result = self._build_base_result(
            test_case_id=test_case_id,
            input_text=input_text,
            agent_output=agent_output,
            latency_ms=elapsed_ms,
            token_usage=token_usage,
            trace_id=trace_id,
        )
        result.metadata = {
            "tool_calls": tool_calls_info,
            "num_tool_calls": len(tool_calls_info),
        }
        return result
