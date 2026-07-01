# AgentBench 知识库示例文档

本文档用于 RAG Agent 评测的知识库测试。

## 产品介绍

AgentBench 是一个面向大语言模型 Agent 的自动化评测平台。它支持三种类型的 Agent 评测：Prompt Agent（纯提示词驱动）、RAG Agent（检索增强生成）和 Tool Agent（工具调用）。

## 核心功能

### 评测集管理
评测集是评测的基础。AgentBench 支持手动录入、JSON 批量导入等方式创建评测集，每个评测用例包含输入文本、期望输出、分类标签和难度等级。

### 多维度评分
AgentBench 使用 LLM-as-Judge 机制进行自动评分，评测维度包括准确性、安全性、流畅性、任务完成度和幻觉检测。每个维度都有详细的 1-5 分评分标准。

### 归因分析
当评测发现问题时，AgentBench 会自动进行三层归因分析：Prompt 层（指令设计问题）、RAG 层（检索召回问题）、Tool 层（工具调用问题）。

### 数据治理
AgentBench 提供统一标签体系、数据质量校验和统计口径管理，确保评测数据的可靠性和一致性。

## 技术架构

AgentBench 使用 FastAPI 作为后端框架，LangChain 进行 Agent 编排，ChromaDB 作为向量数据库，Langfuse 提供可观测性追踪，Streamlit 构建前端看板。

## 常见问题

Q: AgentBench 支持哪些 LLM？
A: 通过 OpenAI 兼容接口，支持 GPT-4、GPT-4o、DeepSeek、Qwen 等主流模型。

Q: 评测集支持什么格式？
A: 目前支持 JSON 格式导入，CSV 格式正在开发中。

Q: Langfuse 是必须的吗？
A: 不是必须的。Langfuse 用于可观测性追踪，可以关闭。但建议开启以获得完整的 Trace 分析能力。
