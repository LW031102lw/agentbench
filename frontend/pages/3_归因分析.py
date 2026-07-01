"""归因分析页 — 多层根因定位可视化"""

import streamlit as st
import requests

st.title("🔍 多层归因分析")

st.markdown("""
当评测发现问题时，AgentBench 会自动在三个层面进行根因定位：
- **Prompt 层** — 指令清晰度、角色定义、上下文缺失、Prompt 注入
- **RAG 层** — 检索召回率、上下文相关性、幻觉检测
- **Tool 层** — 工具选择、参数构造、SQL 生成、API 调用
""")

# ── 单条归因分析 ───────────────────────────────────────
st.header("单条归因分析")

with st.form("attribution_form"):
    col1, col2 = st.columns(2)
    with col1:
        input_text = st.text_area("用户输入", placeholder="输入用户问题...")
        agent_type = st.selectbox("Agent 类型", ["prompt", "rag", "tool"])
    with col2:
        agent_output = st.text_area("Agent 输出", placeholder="粘贴 Agent 的回答...")
        expected_output = st.text_input("期望输出（可选）")

    submitted = st.form_submit_button("执行归因分析")

if submitted and input_text and agent_output:
    with st.spinner("正在分析..."):
        try:
            resp = requests.post("http://localhost:8000/api/attribution/analyze", json={
                "input_text": input_text,
                "agent_output": agent_output,
                "agent_type": agent_type,
                "expected_output": expected_output or None,
            })
            if resp.ok:
                result = resp.json()
                layer = result.get("attribution_layer")
                detail = result.get("detail", "")

                if layer:
                    layer_names = {"prompt": "Prompt 层", "rag": "RAG 层", "tool": "Tool 层"}
                    layer_colors = {"prompt": "🟡", "rag": "🔵", "tool": "🟣"}
                    icon = layer_colors.get(layer, "⚪")
                    st.warning(f"{icon} 归因结果: **{layer_names.get(layer, layer)}**")
                    st.info(detail)
                else:
                    st.success("未发现明显的可归因问题")
                    if detail:
                        st.info(detail)
            else:
                st.error(f"分析失败: {resp.text}")
        except Exception as e:
            st.error(f"请求失败: {e}")

# ── 报告归因汇总 ──────────────────────────────────────
st.header("评测报告归因汇总")

try:
    resp = requests.get("http://localhost:8000/api/evaluations/reports")
    reports = resp.json() if resp.ok else []
except Exception:
    reports = []

if reports:
    report_options = {r["id"]: f"{r['dataset_name']} ({r['agent_type']})" for r in reports}
    selected = st.selectbox("选择评测报告", list(report_options.keys()),
                            format_func=lambda x: report_options[x], key="attr_report")
    if selected:
        try:
            resp = requests.get(f"http://localhost:8000/api/attribution/report/{selected}/summary")
            if resp.ok:
                summary = resp.json()
                st.write(f"**问题用例总数**: {summary.get('total_issues', 0)}")

                details = summary.get("details", [])
                if details:
                    import pandas as pd
                    df = pd.DataFrame(details)
                    st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"获取归因汇总失败: {e}")
else:
    st.info("暂无评测报告")
