"""结果看板 — 评测报告可视化"""

import streamlit as st
import requests

st.title("📊 评测结果看板")

# 获取报告列表
try:
    resp = requests.get("http://localhost:8000/api/evaluations/reports")
    reports = resp.json() if resp.ok else []
except Exception:
    reports = []
    st.warning("无法连接后端服务，请确保 FastAPI 已启动 (uvicorn src.main:app)")

if not reports:
    st.info("暂无评测报告。请先在「评测配置」页面创建评测集并执行评测。")
else:
    # 报告选择
    report_options = {
        r["id"]: f"{r['dataset_name']} ({r['agent_type']}) - {r['created_at'][:19]}"
        for r in reports
    }
    selected = st.selectbox("选择评测报告", list(report_options.keys()),
                            format_func=lambda x: report_options[x])

    if selected:
        # 获取报告详情
        resp = requests.get(f"http://localhost:8000/api/evaluations/reports/{selected}")
        report = resp.json() if resp.ok else None

        if report:
            # 核心指标卡片
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("平均得分", f"{report.get('avg_score', 0):.2f}")
            col2.metric("通过率", f"{report.get('pass_rate', 0):.1%}")
            col3.metric("用例总数", report.get("total_cases", 0))
            col4.metric("平均延迟", f"{report.get('avg_latency_ms', 0):.0f}ms")

            # 各维度得分
            st.subheader("各维度得分")
            dim_avg = report.get("dimension_avg", {})
            if dim_avg:
                import pandas as pd
                df = pd.DataFrame([
                    {"维度": k, "平均分": v} for k, v in dim_avg.items()
                ])
                st.bar_chart(df.set_index("维度"))

            # 归因统计
            st.subheader("归因分析统计")
            attr_summary = report.get("attribution_summary", {})
            if attr_summary:
                col1, col2, col3 = st.columns(3)
                col1.metric("Prompt 层问题", attr_summary.get("prompt", 0))
                col2.metric("RAG 层问题", attr_summary.get("rag", 0))
                col3.metric("Tool 层问题", attr_summary.get("tool", 0))

            # 详细结果表
            st.subheader("详细评测结果")
            results = report.get("results", [])
            if results:
                import pandas as pd
                detail_df = pd.DataFrame([
                    {
                        "用例ID": r["test_case_id"],
                        "输入": r["input_text"][:50] + "...",
                        "得分": r["total_score"],
                        "延迟(ms)": r["latency_ms"],
                        "归因": r.get("attribution_layer") or "-",
                    }
                    for r in results
                ])
                st.dataframe(detail_df, use_container_width=True)
