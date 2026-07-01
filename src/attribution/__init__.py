"""多层归因分析引擎 — 自动定位 Agent 失败根因"""

from __future__ import annotations

from src.attribution.prompt_analyzer import PromptAnalyzer
from src.attribution.rag_analyzer import RAGAnalyzer
from src.attribution.tool_analyzer import ToolAnalyzer
from src.models.evaluation import AttributionLayer


class AttributionEngine:
    """
    多层归因分析引擎：当评测发现问题时，自动在三个层面进行根因定位。

    分析优先级：
    1. Tool 层 — 检查工具调用是否成功
    2. RAG 层 — 检查检索召回和上下文相关性
    3. Prompt 层 — 检查 prompt 设计和指令清晰度

    输出：归因层 + 详细分析说明 + 优化建议
    """

    def __init__(self):
        self.prompt_analyzer = PromptAnalyzer()
        self.rag_analyzer = RAGAnalyzer()
        self.tool_analyzer = ToolAnalyzer()

    async def analyze(
        self,
        input_text: str,
        agent_output: str,
        agent_type: str,
        expected_output: str | None = None,
        metadata: dict | None = None,
    ) -> tuple[AttributionLayer | None, str]:
        """
        执行归因分析，返回 (归因层, 分析详情)。
        如果无法定位到特定层，返回 (None, 通用分析)。
        """
        issues: list[tuple[AttributionLayer, str, float]] = []

        # 1. Tool 层分析（仅对 Tool Agent）
        if agent_type == "tool" and metadata:
            tool_issues = await self.tool_analyzer.analyze(
                input_text, agent_output, metadata
            )
            if tool_issues:
                issues.append((AttributionLayer.TOOL, tool_issues, 0.8))

        # 2. RAG 层分析（仅对 RAG Agent）
        if agent_type == "rag" and metadata:
            rag_issues = await self.rag_analyzer.analyze(
                input_text, agent_output, metadata
            )
            if rag_issues:
                issues.append((AttributionLayer.RAG, rag_issues, 0.7))

        # 3. Prompt 层分析（通用）
        prompt_issues = await self.prompt_analyzer.analyze(
            input_text, agent_output, expected_output
        )
        if prompt_issues:
            issues.append((AttributionLayer.PROMPT, prompt_issues, 0.5))

        if not issues:
            return None, "未发现明显的可归因问题，可能是模型本身能力不足或评测标准过严。"

        # 返回置信度最高的归因结果
        issues.sort(key=lambda x: x[2], reverse=True)
        best = issues[0]
        return best[0], best[1]
