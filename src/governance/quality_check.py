"""数据质量校验 — 自动检测评测数据中的重复、缺失、异常"""

from __future__ import annotations
from pydantic import BaseModel, Field

from src.models.dataset import Dataset, TestCase


class QualityIssue(BaseModel):
    """质量问题记录"""
    case_id: str
    issue_type: str = Field(..., description="问题类型: duplicate / missing / anomaly / format")
    severity: str = Field("warning", description="严重程度: info / warning / error")
    description: str
    suggestion: str = ""


class QualityReport(BaseModel):
    """数据质量报告"""
    dataset_id: str
    dataset_name: str
    total_cases: int
    issues: list[QualityIssue] = Field(default_factory=list)
    pass_count: int = 0
    warning_count: int = 0
    error_count: int = 0

    @property
    def quality_score(self) -> float:
        """质量分 = 1 - (问题数 / 总用例数)，最低为 0"""
        if self.total_cases == 0:
            return 1.0
        return max(0.0, 1.0 - len(self.issues) / self.total_cases)


class QualityChecker:
    """
    数据质量校验器：自动检测评测数据中的各类质量问题。
    确保进入 Agent 评测系统的数据是可靠和可信的。
    """

    def check(self, dataset: Dataset) -> QualityReport:
        """对评测集执行完整的质量校验"""
        issues: list[QualityIssue] = []

        issues.extend(self._check_duplicates(dataset))
        issues.extend(self._check_missing(dataset))
        issues.extend(self._check_anomalies(dataset))
        issues.extend(self._check_format(dataset))

        report = QualityReport(
            dataset_id=dataset.id,
            dataset_name=dataset.name,
            total_cases=dataset.size,
            issues=issues,
            pass_count=sum(1 for c in dataset.test_cases
                         if not any(i.case_id == c.id for i in issues)),
            warning_count=sum(1 for i in issues if i.severity == "warning"),
            error_count=sum(1 for i in issues if i.severity == "error"),
        )
        return report

    def _check_duplicates(self, dataset: Dataset) -> list[QualityIssue]:
        """检测重复用例"""
        issues = []
        seen_inputs: dict[str, str] = {}
        for case in dataset.test_cases:
            normalized = case.input_text.strip().lower()
            if normalized in seen_inputs:
                issues.append(QualityIssue(
                    case_id=case.id,
                    issue_type="duplicate",
                    severity="warning",
                    description=f"与用例 {seen_inputs[normalized]} 的输入文本重复",
                    suggestion="建议合并或删除重复用例",
                ))
            else:
                seen_inputs[normalized] = case.id
        return issues

    def _check_missing(self, dataset: Dataset) -> list[QualityIssue]:
        """检测缺失字段"""
        issues = []
        for case in dataset.test_cases:
            if not case.input_text or not case.input_text.strip():
                issues.append(QualityIssue(
                    case_id=case.id,
                    issue_type="missing",
                    severity="error",
                    description="输入文本为空",
                    suggestion="请补充输入文本",
                ))
            if not case.category:
                issues.append(QualityIssue(
                    case_id=case.id,
                    issue_type="missing",
                    severity="info",
                    description="未设置分类标签",
                    suggestion="建议设置分类标签以便统计分析",
                ))
        return issues

    def _check_anomalies(self, dataset: Dataset) -> list[QualityIssue]:
        """检测异常数据"""
        issues = []
        lengths = [len(c.input_text) for c in dataset.test_cases]
        if not lengths:
            return issues

        avg_len = sum(lengths) / len(lengths)
        std_len = (sum((l - avg_len) ** 2 for l in lengths) / len(lengths)) ** 0.5

        for case in dataset.test_cases:
            text_len = len(case.input_text)
            # 检测极端长度（超过 3 个标准差）
            if std_len > 0 and abs(text_len - avg_len) > 3 * std_len:
                severity = "warning" if text_len > avg_len else "info"
                issues.append(QualityIssue(
                    case_id=case.id,
                    issue_type="anomaly",
                    severity=severity,
                    description=f"输入文本长度异常（{text_len} 字符，平均 {avg_len:.0f}）",
                    suggestion="请检查该用例是否合理",
                ))
        return issues

    def _check_format(self, dataset: Dataset) -> list[QualityIssue]:
        """检测格式问题"""
        issues = []
        for case in dataset.test_cases:
            # 检查是否包含特殊字符或编码问题
            if any(c in case.input_text for c in ["\x00", "\ufffd"]):
                issues.append(QualityIssue(
                    case_id=case.id,
                    issue_type="format",
                    severity="warning",
                    description="输入文本包含特殊字符或编码异常",
                    suggestion="建议清洗文本后重新导入",
                ))
        return issues
