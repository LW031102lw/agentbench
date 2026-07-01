"""自动化评测流水线 — 批量执行评测、评分、归因分析、报告生成"""

from __future__ import annotations
import asyncio
import uuid
from datetime import datetime

from src.agents import create_agent, BaseAgent
from src.evaluator.scorers import LLMDimensionScorer
from src.evaluator.dimensions import get_dimensions_for_agent
from src.evaluator.report import ReportGenerator
from src.attribution import AttributionEngine
from src.models.dataset import Dataset, TestCase
from src.models.evaluation import SingleResult, EvalReport, EvalStatus
from src.models.agent_config import AgentConfig


class EvalPipeline:
    """
    自动化评测流水线：评测集加载 → Agent 批量执行 → 多维度评分 → 归因分析 → 报告生成。
    支持并行执行和进度回调。
    """

    def __init__(
        self,
        agent_config: AgentConfig,
        scorer_model: str = "gpt-4o-mini",
        concurrency: int = 5,
    ):
        self.agent_config = agent_config
        self.agent: BaseAgent = create_agent(agent_config.agent_type.value, agent_config)
        self.scorer = LLMDimensionScorer(model=scorer_model)
        self.attribution = AttributionEngine()
        self.dimensions = get_dimensions_for_agent(agent_config.agent_type.value)
        self.concurrency = concurrency
        self._results: list[SingleResult] = []

    async def run(
        self,
        dataset: Dataset,
        on_progress: callable | None = None,
    ) -> EvalReport:
        """
        执行完整评测流水线。

        Args:
            dataset: 评测集
            on_progress: 进度回调 (completed, total)

        Returns:
            EvalReport 评测报告
        """
        self._results = []
        report_id = str(uuid.uuid4())[:8]
        semaphore = asyncio.Semaphore(self.concurrency)

        async def process_case(case: TestCase) -> SingleResult:
            async with semaphore:
                result = await self._evaluate_single(case)
                self._results.append(result)
                if on_progress:
                    on_progress(len(self._results), len(dataset.test_cases))
                return result

        # 批量并行执行
        tasks = [process_case(case) for case in dataset.test_cases]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 过滤掉异常
        valid_results = [r for r in results if isinstance(r, SingleResult)]

        # 生成报告
        report = ReportGenerator.generate(
            report_id=report_id,
            dataset_id=dataset.id,
            dataset_name=dataset.name,
            agent_type=self.agent_config.agent_type.value,
            model_name=self.agent_config.model_name,
            results=valid_results,
        )
        return report

    async def _evaluate_single(self, case: TestCase) -> SingleResult:
        """对单条用例执行：Agent 推理 → 多维度评分 → 归因分析"""

        # 1. Agent 推理
        result = await self.agent.run(case.input_text, test_case_id=case.id)
        result.expected_output = case.expected_output

        # 2. 多维度评分
        scores = await self.scorer.score_all(
            input_text=case.input_text,
            agent_output=result.agent_output,
            dimensions=self.dimensions,
            expected_output=case.expected_output,
            context=getattr(result, "metadata", None),
        )
        result.scores = scores

        # 3. 计算加权总分
        total_weight = sum(d.weight for d in self.dimensions)
        weighted_sum = 0.0
        for ds in scores:
            dim_def = next((d for d in self.dimensions if d.name == ds.dimension), None)
            if dim_def:
                weighted_sum += (ds.score / ds.max_score) * dim_def.weight
        result.total_score = round((weighted_sum / total_weight) * 5.0, 2) if total_weight else 0.0

        # 4. 归因分析（仅对低分用例触发）
        if result.total_score < 3.0:
            layer, detail = await self.attribution.analyze(
                input_text=case.input_text,
                agent_output=result.agent_output,
                agent_type=self.agent_config.agent_type.value,
                expected_output=case.expected_output,
                metadata=getattr(result, "metadata", None),
            )
            result.attribution_layer = layer
            result.attribution_detail = detail

        return result
