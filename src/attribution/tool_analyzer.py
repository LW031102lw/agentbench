"""Tool 层归因分析 — 检测工具调用相关问题"""

from __future__ import annotations

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from config.settings import OPENAI_API_KEY, OPENAI_BASE_URL

TOOL_ANALYSIS_SYSTEM = """你是一个 AI Agent 工具调用专家，负责分析 Agent 输出质量问题是否由工具调用环节导致。

请分析以下情况，重点检查：
1. 工具选择：是否选择了正确的工具
2. 参数构造：工具参数是否正确、完整
3. SQL 生成：如涉及数据库查询，SQL 是否正确
4. API 调用：API 调用格式是否规范
5. 遗漏调用：是否应该调用工具但没有调用

输出格式：
{"is_tool_issue": true/false, "tool_selection": "correct/incorrect/missing", "param_accuracy": "high/medium/low", "analysis": "分析内容", "suggestion": "优化建议"}"""


class ToolAnalyzer:
    """Tool 层归因分析器"""

    def __init__(self, model: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(
            model=model, temperature=0.0,
            api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL,
        )

    async def analyze(
        self,
        input_text: str,
        agent_output: str,
        metadata: dict | None = None,
    ) -> str:
        """
        分析问题是否由工具调用导致。
        metadata 中应包含 tool_calls 信息。
        """
        if not metadata:
            return ""

        tool_calls = metadata.get("tool_calls", [])
        num_calls = metadata.get("num_tool_calls", 0)

        import json
        user_msg_parts = [
            f"用户问题：{input_text}",
            f"Agent 输出：{agent_output}",
            f"工具调用次数：{num_calls}",
        ]
        if tool_calls:
            user_msg_parts.append(
                f"工具调用详情：{json.dumps(tool_calls, ensure_ascii=False)}"
            )
        else:
            user_msg_parts.append("未发生工具调用")

        response = await self.llm.ainvoke([
            SystemMessage(content=TOOL_ANALYSIS_SYSTEM),
            HumanMessage(content="\n\n".join(user_msg_parts)),
        ])

        try:
            text = response.content.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            data = json.loads(text)
            if data.get("is_tool_issue"):
                parts = [
                    f"[Tool层问题]",
                    f"工具选择: {data.get('tool_selection', 'N/A')}",
                    f"参数准确性: {data.get('param_accuracy', 'N/A')}",
                    f"分析: {data.get('analysis', '')}",
                    f"优化建议: {data.get('suggestion', '')}",
                ]
                return "\n".join(parts)
        except (json.JSONDecodeError, KeyError):
            pass

        return ""
