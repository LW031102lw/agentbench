"""评分器 — LLM-as-Judge 自动评分 + 人工评分接口"""

from __future__ import annotations
import json

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from config.settings import OPENAI_API_KEY, OPENAI_BASE_URL
from src.models.dataset import EvalDimension
from src.models.evaluation import DimensionScore

JUDGE_SYSTEM_PROMPT = """你是一个专业的 AI 输出评测专家。请根据给定的评分标准，对 AI 的回答进行打分。

评分要求：
1. 严格按照评分标准打分，不要偏高或偏低
2. 给出分数的同时，简要说明评分理由
3. 以 JSON 格式输出结果

输出格式（严格遵循）：
{"score": <分数>, "reasoning": "<评分理由>"}"""


class LLMDimensionScorer:
    """
    基于 LLM-as-Judge 的自动评分器。
    使用一个独立的 LLM 来对 Agent 输出进行多维度评分。
    """

    def __init__(self, model: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(
            model=model,
            temperature=0.0,
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL,
        )

    async def score(
        self,
        input_text: str,
        agent_output: str,
        dimension: EvalDimension,
        expected_output: str | None = None,
        context: dict | None = None,
    ) -> DimensionScore:
        """对单个维度进行评分"""
        user_prompt = self._build_judge_prompt(
            input_text, agent_output, dimension, expected_output, context
        )

        response = await self.llm.ainvoke([
            SystemMessage(content=JUDGE_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ])

        return self._parse_score(response.content, dimension)

    async def score_all(
        self,
        input_text: str,
        agent_output: str,
        dimensions: list[EvalDimension],
        expected_output: str | None = None,
        context: dict | None = None,
    ) -> list[DimensionScore]:
        """对多个维度逐一评分"""
        scores = []
        for dim in dimensions:
            s = await self.score(input_text, agent_output, dim, expected_output, context)
            scores.append(s)
        return scores

    def _build_judge_prompt(
        self,
        input_text: str,
        agent_output: str,
        dimension: EvalDimension,
        expected_output: str | None,
        context: dict | None,
    ) -> str:
        """构建评分用的 user prompt"""
        parts = [
            f"【用户输入】\n{input_text}",
            f"【Agent 输出】\n{agent_output}",
        ]
        if expected_output:
            parts.append(f"【期望输出】\n{expected_output}")
        if context:
            parts.append(f"【附加上下文】\n{json.dumps(context, ensure_ascii=False)[:1000]}")
        parts.extend([
            f"【评测维度】{dimension.name}",
            f"【评分标准】\n{dimension.scoring_rubric}",
            f"【满分】{dimension.max_score}",
            "请严格按照 JSON 格式输出评分结果。",
        ])
        return "\n\n".join(parts)

    def _parse_score(self, raw: str, dimension: EvalDimension) -> DimensionScore:
        """解析 LLM 返回的评分 JSON"""
        try:
            # 尝试提取 JSON 块
            text = raw.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            data = json.loads(text)
            score = float(data.get("score", 0))
            reasoning = data.get("reasoning", "")
        except (json.JSONDecodeError, ValueError, KeyError):
            # 解析失败时给 0 分并记录
            score = 0.0
            reasoning = f"评分解析失败，原始输出: {raw[:200]}"

        return DimensionScore(
            dimension=dimension.name,
            score=min(score, dimension.max_score),
            max_score=dimension.max_score,
            reasoning=reasoning,
        )


class ManualScorer:
    """
    人工评分接口 — 提供评分数据结构的封装，
    实际评分值由前端或 API 传入。
    """

    @staticmethod
    def create_score(
        dimension_name: str,
        score: float,
        max_score: float = 5.0,
        reasoning: str = "",
    ) -> DimensionScore:
        return DimensionScore(
            dimension=dimension_name,
            score=score,
            max_score=max_score,
            reasoning=reasoning,
        )
