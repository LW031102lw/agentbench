"""Prompt 层归因分析 — 检测 prompt 设计问题"""

from __future__ import annotations

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from config.settings import OPENAI_API_KEY, OPENAI_BASE_URL

PROMPT_ANALYSIS_SYSTEM = """你是一个 Prompt 工程专家，负责分析 Agent 输出质量问题是否由 Prompt 设计导致。

请分析以下情况，判断问题是否属于 Prompt 层原因，并给出优化建议。

常见的 Prompt 层问题：
1. 指令不清晰：系统提示词缺少具体约束或输出格式要求
2. 角色定义不足：缺少领域专家角色设定
3. 上下文缺失：没有提供足够的背景信息
4. Prompt 注入风险：用户输入可能覆盖系统指令
5. 输出格式未约束：未指定输出格式导致回答散乱

如果判断是 Prompt 层问题，请输出具体分析和优化建议。
如果不是，输出空字符串。

输出格式：
{"is_prompt_issue": true/false, "analysis": "分析内容", "suggestion": "优化建议"}"""


class PromptAnalyzer:
    """Prompt 层归因分析器"""

    def __init__(self, model: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(
            model=model, temperature=0.0,
            api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL,
        )

    async def analyze(
        self,
        input_text: str,
        agent_output: str,
        expected_output: str | None = None,
    ) -> str:
        """
        分析问题是否由 Prompt 设计导致。
        返回分析详情字符串，如果不是 Prompt 问题则返回空字符串。
        """
        user_msg = f"用户输入：{input_text}\n\nAgent 输出：{agent_output}"
        if expected_output:
            user_msg += f"\n\n期望输出：{expected_output}"

        response = await self.llm.ainvoke([
            SystemMessage(content=PROMPT_ANALYSIS_SYSTEM),
            HumanMessage(content=user_msg),
        ])

        import json
        try:
            text = response.content.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            data = json.loads(text)
            if data.get("is_prompt_issue"):
                analysis = data.get("analysis", "")
                suggestion = data.get("suggestion", "")
                return f"[Prompt层问题] {analysis}\n优化建议: {suggestion}"
        except (json.JSONDecodeError, KeyError):
            pass

        return ""
