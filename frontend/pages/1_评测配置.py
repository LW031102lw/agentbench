"""评测配置页 — 创建评测集、配置 Agent 参数"""

import streamlit as st
import requests
import json

st.title("📋 评测配置")

# ── 评测集管理 ─────────────────────────────────────────
st.header("评测集管理")

with st.expander("创建评测集", expanded=True):
    name = st.text_input("评测集名称", placeholder="如: 通用对话评测 v1")
    description = st.text_area("描述", placeholder="评测集的用途和说明")

    col1, col2 = st.columns(2)
    with col1:
        import_format = st.selectbox("导入方式", ["手动录入", "JSON 导入"])
    with col2:
        difficulty = st.selectbox("默认难度", ["easy", "medium", "hard"])

    if import_format == "JSON 导入":
        json_input = st.text_area(
            "粘贴 JSON 数据",
            placeholder='[{"input_text": "你好", "expected_output": "你好！", "category": "通用对话"}]',
            height=200,
        )
        if st.button("导入评测集"):
            if not name:
                st.error("请输入评测集名称")
            else:
                payload = {
                    "name": name,
                    "description": description,
                    "format": "json",
                    "content": json_input,
                }
                try:
                    resp = requests.post("http://localhost:8000/api/datasets/import", json=payload)
                    if resp.ok:
                        data = resp.json()
                        st.success(f"导入成功！ID: {data['id']}，共 {data['size']} 条用例")
                    else:
                        st.error(f"导入失败: {resp.text}")
                except Exception as e:
                    st.error(f"请求失败: {e}")

    elif import_format == "手动录入":
        st.info("请输入评测用例：")
        num_cases = st.number_input("用例数量", min_value=1, max_value=50, value=5)
        cases = []
        for i in range(int(num_cases)):
            with st.container():
                st.markdown(f"**用例 {i+1}**")
                c1, c2 = st.columns(2)
                input_text = c1.text_input(f"输入", key=f"input_{i}")
                expected = c2.text_input(f"期望输出", key=f"expected_{i}")
                cases.append({"input_text": input_text, "expected_output": expected})

        if st.button("创建评测集"):
            dataset = {
                "id": "",
                "name": name,
                "description": description,
                "test_cases": [
                    {
                        "id": f"case_{i+1}",
                        "input_text": c["input_text"],
                        "expected_output": c["expected_output"],
                        "category": "general",
                    }
                    for i, c in enumerate(cases) if c["input_text"]
                ],
            }
            try:
                resp = requests.post("http://localhost:8000/api/datasets/", json=dataset)
                if resp.ok:
                    st.success("评测集创建成功！")
                else:
                    st.error(resp.text)
            except Exception as e:
                st.error(f"请求失败: {e}")

# ── Agent 配置 ─────────────────────────────────────────
st.header("Agent 配置")
col1, col2, col3 = st.columns(3)
with col1:
    agent_type = st.selectbox("Agent 类型", ["prompt", "rag", "tool"])
with col2:
    model_name = st.selectbox("模型", ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"])
with col3:
    temperature = st.slider("Temperature", 0.0, 1.0, 0.0, 0.1)

st.info(f"当前配置: {agent_type} Agent | 模型: {model_name} | 温度: {temperature}")
