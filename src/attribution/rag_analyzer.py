"""RAG 层归因分析 — 检测检索召回和上下文相关性问题"""

from __future__ import annotations

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from config.settings import OPENAI_API_KEY, OPENAI_BASE_URL

RAG_ANALYSIS_SYSTEM = """你是一个 RAG（检索增强生成）专家，负责分析 Agent 输出质量问题是否由检索环节导致。

请分析以下情况，重点检查：
1. 检索召回率：是否检索到了与问题相关的文档
2. 上下文相关性：检索到的内容是否真正有用
3. 幻觉检测：模型是否编造了不在上下文中的信息
4. 知识库覆盖度：知识库是否包含了回答问题所需的信息

输出格式：
{"is_rag_issue": true/false, "retrieval_quality": "检索质量评估", "hallucination_risk": "low/medium/high", "analysis": "分析内容", "suggestion": "优化建议"}"""


class RAGAnalyzer:
    """RAG 层归因分析器"""

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
        分析问题是否由 RAG 检索环节导致。
        metadata 中应包含 retrieved_docs、context 等检索信息。
        """
        if not metadata:
            return ""

        retrieved_docs = metadata.get("retrieved_docs", [])
        context = metadata.get("context", "")
        num_retrieved = metadata.get("num_retrieved", 0)

        user_msg_parts = [
            f"用户问题：{input_text}",
            f"Agent 输出：{agent_output}",
            f"检索到 {num_retrieved} 个文档片段",
        ]
        if context:
            user_msg_parts.append(f"检索上下文（截取前500字）：{context[:500]}")
        if retrieved_docs:
            user_msg_parts.append(
                f"各文档片段摘要：{[d[:100] for d in retrieved_docs[:3]]}"
            )

        response = await self.llm.ainvoke([
            SystemMessage(content=RAG_ANALYSIS_SYSTEM),
            HumanMessage(content="\n\n".join(user_msg_parts)),
        ])

        import json
        try:
            text = response.content.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            data = json.loads(text)
            if data.get("is_rag_issue"):
                parts = [
                    f"[RAG层问题]",
                    f"检索质量: {data.get('retrieval_quality', 'N/A')}",
                    f"幻觉风险: {data.get('hallucination_risk', 'N/A')}",
                    f"分析: {data.get('analysis', '')}",
                    f"优化建议: {data.get('suggestion', '')}",
                ]
                return "\n".join(parts)
        except (json.JSONDecodeError, KeyError):
            pass

        return ""
