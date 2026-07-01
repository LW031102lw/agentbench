"""Langfuse 可观测性集成 — 追踪、指标上报、对比实验"""

from __future__ import annotations
from functools import lru_cache

from langfuse import Langfuse

from config.settings import LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST


@lru_cache(maxsize=1)
def get_langfuse_client() -> Langfuse | None:
    """获取全局 Langfuse 客户端（单例）"""
    if not LANGFUSE_PUBLIC_KEY or not LANGFUSE_SECRET_KEY:
        return None
    try:
        return Langfuse(
            public_key=LANGFUSE_PUBLIC_KEY,
            secret_key=LANGFUSE_SECRET_KEY,
            host=LANGFUSE_HOST,
        )
    except Exception as e:
        print(f"[Langfuse] 初始化失败: {e}")
        return None


def report_eval_score(
    trace_id: str,
    name: str,
    value: float,
    comment: str = "",
) -> None:
    """将评测分数作为 Score 上报到 Langfuse"""
    client = get_langfuse_client()
    if not client or not trace_id:
        return
    try:
        client.score(
            trace_id=trace_id,
            name=name,
            value=value,
            comment=comment,
        )
    except Exception as e:
        print(f"[Langfuse] 上报分数失败: {e}")


def report_eval_metadata(
    trace_id: str,
    metadata: dict,
) -> None:
    """为指定 trace 补充元数据"""
    client = get_langfuse_client()
    if not client or not trace_id:
        return
    try:
        client.trace(id=trace_id, metadata=metadata)
    except Exception as e:
        print(f"[Langfuse] 上报元数据失败: {e}")


def flush():
    """确保所有未发送的事件都已上报"""
    client = get_langfuse_client()
    if client:
        client.flush()
