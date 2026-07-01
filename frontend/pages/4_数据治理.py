"""数据治理页 — 标签管理、质量校验、统计口径"""

import streamlit as st
import requests

st.title("📦 数据治理")

# ── 标签体系 ───────────────────────────────────────────
st.header("标签体系")

try:
    resp = requests.get("http://localhost:8000/api/governance/labels")
    labels = resp.json() if resp.ok else []
except Exception:
    labels = []

if labels:
    # 按分类展示标签
    categories = {}
    for label in labels:
        cat = label.get("category", "unknown")
        categories.setdefault(cat, []).append(label)

    for cat, cat_labels in categories.items():
        with st.expander(f"{cat} 类标签 ({len(cat_labels)} 个)"):
            for label in cat_labels:
                st.markdown(f"- **{label['name']}**: {label.get('description', '')}")
else:
    st.info("加载标签体系需要后端服务运行中")

# ── 数据质量校验 ──────────────────────────────────────
st.header("数据质量校验")

try:
    resp = requests.get("http://localhost:8000/api/datasets/")
    datasets = resp.json() if resp.ok else []
except Exception:
    datasets = []

if datasets:
    ds_options = {d["id"]: d["name"] for d in datasets}
    selected_ds = st.selectbox("选择评测集", list(ds_options.keys()),
                               format_func=lambda x: ds_options[x])
    if st.button("执行质量校验"):
        with st.spinner("校验中..."):
            try:
                resp = requests.get(f"http://localhost:8000/api/governance/quality/{selected_ds}")
                if resp.ok:
                    report = resp.json()
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("质量分", f"{report.get('quality_score', 0):.0%}")
                    col2.metric("总用例", report.get("total_cases", 0))
                    col3.metric("警告", report.get("warning_count", 0))
                    col4.metric("错误", report.get("error_count", 0))

                    issues = report.get("issues", [])
                    if issues:
                        st.subheader("问题详情")
                        import pandas as pd
                        df = pd.DataFrame([
                            {
                                "用例ID": i["case_id"],
                                "类型": i["issue_type"],
                                "级别": i["severity"],
                                "描述": i["description"],
                                "建议": i["suggestion"],
                            }
                            for i in issues
                        ])
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.success("数据质量良好，未发现问题！")
            except Exception as e:
                st.error(f"校验失败: {e}")
else:
    st.info("暂无评测集，请先创建评测集")

# ── 统计口径 ──────────────────────────────────────────
st.header("统计口径管理")

st.markdown("""
统一的统计口径确保不同评测批次的指标计算方式一致，避免因计算方式差异导致的对比偏差。
""")

try:
    resp = requests.get("http://localhost:8000/api/governance/metrics")
    metrics = resp.json() if resp.ok else []
except Exception:
    metrics = []

if metrics:
    for m in metrics:
        with st.expander(f"{m['display_name']} ({m['name']})"):
            st.write(f"**说明**: {m['description']}")
            st.write(f"**公式**: `{m['formula']}`")
            if m.get("unit"):
                st.write(f"**单位**: {m['unit']}")
