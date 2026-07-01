"""AgentBench 前端看板 — Streamlit 主页面"""

import streamlit as st

st.set_page_config(
    page_title="AgentBench - AI Agent 评测平台",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🔬 AgentBench — AI Agent 智能评测平台")

st.markdown("""
### 平台简介

AgentBench 是一个面向大语言模型 Agent 的自动化评测平台，提供完整的评测能力：

- **评测集管理** — 创建、导入、版本管理评测数据集
- **自动化评测** — 基于 LangChain 的 Prompt / RAG / Tool 三类 Agent 评测管线
- **多层归因分析** — Prompt 层、RAG 层、Tool 层三层根因定位
- **数据治理** — 统一标签体系、数据质量校验、统计口径管理
- **可观测性** — Langfuse 全链路追踪和指标上报

### 快速开始

1. 在左侧导航栏进入 **评测配置** 页面创建评测集
2. 配置 Agent 参数后启动评测
3. 在 **结果看板** 查看评测报告和可视化分析
4. 对低分用例在 **归因分析** 页面定位根因
5. 在 **数据治理** 页面管理标签和数据质量
""")

# 系统状态
col1, col2, col3, col4 = st.columns(4)
col1.metric("API 状态", "🟢 正常")
col2.metric("Langfuse", "🟢 已连接")
col3.metric("评测集数量", "0")
col4.metric("评测报告", "0")
