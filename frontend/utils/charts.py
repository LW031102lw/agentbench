"""图表工具 — 为 Streamlit 前端提供可视化图表"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def create_score_distribution_chart(results: list[dict]) -> go.Figure:
    """创建分数分布直方图"""
    scores = [r["total_score"] for r in results]
    fig = px.histogram(
        x=scores,
        nbins=10,
        title="评测分数分布",
        labels={"x": "得分", "y": "用例数量"},
        color_discrete_sequence=["#6366f1"],
    )
    fig.update_layout(bargap=0.05)
    return fig


def create_dimension_radar_chart(dim_avg: dict[str, float], max_score: float = 5.0) -> go.Figure:
    """创建各维度雷达图"""
    dimensions = list(dim_avg.keys())
    scores = [dim_avg[d] for d in dimensions]

    fig = go.Figure(data=go.Scatterpolar(
        r=scores + [scores[0]],
        theta=dimensions + [dimensions[0]],
        fill="toself",
        name="当前评测",
        line_color="#6366f1",
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, max_score])),
        title="各评测维度雷达图",
    )
    return fig


def create_attribution_pie_chart(attribution_summary: dict[str, int]) -> go.Figure:
    """创建归因分布饼图"""
    if not attribution_summary:
        return go.Figure().add_annotation(text="无归因数据", showarrow=False)

    labels = list(attribution_summary.keys())
    values = list(attribution_summary.values())
    color_map = {"prompt": "#f59e0b", "rag": "#3b82f6", "tool": "#8b5cf6"}

    fig = px.pie(
        names=labels,
        values=values,
        title="问题归因分布",
        color=labels,
        color_discrete_map=color_map,
    )
    return fig


def create_latency_box_plot(results: list[dict]) -> go.Figure:
    """创建延迟分布箱线图"""
    df = pd.DataFrame([
        {"agent_type": r["agent_type"], "latency_ms": r["latency_ms"]}
        for r in results
    ])
    fig = px.box(
        df,
        x="agent_type",
        y="latency_ms",
        title="各 Agent 类型延迟分布",
        labels={"agent_type": "Agent 类型", "latency_ms": "延迟 (ms)"},
        color="agent_type",
        color_discrete_map={"prompt": "#6366f1", "rag": "#3b82f6", "tool": "#8b5cf6"},
    )
    return fig


def create_comparison_bar_chart(reports: list[dict]) -> go.Figure:
    """创建多报告对比柱状图"""
    data = []
    for r in reports:
        for dim, score in r.get("dimension_avg", {}).items():
            data.append({
                "报告": f"{r['dataset_name']} ({r['agent_type']})",
                "维度": dim,
                "平均分": score,
            })
    if not data:
        return go.Figure().add_annotation(text="无对比数据", showarrow=False)

    df = pd.DataFrame(data)
    fig = px.bar(
        df,
        x="报告",
        y="平均分",
        color="维度",
        barmode="group",
        title="评测报告对比",
    )
    return fig
