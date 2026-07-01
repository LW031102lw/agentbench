# AgentBench — AI Agent 智能评测平台

> 面向大语言模型 Agent 的自动化评测平台，支持评测维度定义、自动化批量评测、Prompt/RAG/Tool 多层归因分析、数据治理与 Langfuse 可观测性集成。

## 功能特性

- **评测集管理** — 手动录入、JSON 批量导入、评测维度自定义、版本管理
- **三类 Agent 评测** — Prompt Agent、RAG Agent（检索增强）、Tool Agent（工具调用）
- **LLM-as-Judge 自动评分** — 多维度评分（准确性、安全性、流畅性、任务完成度、幻觉检测）
- **自动化评测流水线** — 批量并行执行、进度回调、A/B 对比实验
- **三层归因分析** — Prompt 层（指令/Prompt注入）、RAG 层（召回率/幻觉）、Tool 层（工具选择/SQL生成）
- **数据治理** — 统一标签体系、数据质量校验（重复/缺失/异常检测）、统计口径管理
- **可观测性** — Langfuse 全链路 Trace 追踪、Span 级分析、指标自动上报

## 技术栈

| 层次 | 技术 |
|------|------|
| 后端 | FastAPI + Pydantic |
| Agent 编排 | LangChain + LangChain-OpenAI |
| 向量数据库 | ChromaDB |
| 可观测性 | Langfuse |
| 前端 | Streamlit + Plotly |
| 数据处理 | Pandas |
| LLM | OpenAI API (兼容 DeepSeek/智谱等) |

## 快速开始

### 1. 安装依赖

```bash
git clone https://github.com/yourname/agentbench.git
cd agentbench
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 API Key
```

需要配置：
- `OPENAI_API_KEY` — OpenAI 或其他兼容 API 的密钥
- `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` — Langfuse 平台密钥（可选，用于可观测性）

### 3. 启动后端

```bash
python -m uvicorn src.main:app --reload --port 8000
```

API 文档访问：http://localhost:8000/docs

### 4. 启动前端

```bash
streamlit run frontend/app.py
```

前端看板访问：http://localhost:8501

### 5. 使用示例

```python
import asyncio
from src.pipeline import EvalPipeline
from src.models.agent_config import AgentConfig
from src.models.dataset import Dataset, TestCase

# 创建评测集
dataset = Dataset(
    id="test_001",
    name="通用对话评测",
    test_cases=[
        TestCase(id="1", input_text="什么是机器学习？", expected_output="..."),
        TestCase(id="2", input_text="写一个快排算法", expected_output="..."),
    ],
)

# 配置并运行评测
config = AgentConfig(agent_type="prompt", model_name="gpt-4o-mini")
pipeline = EvalPipeline(agent_config=config)

report = asyncio.run(pipeline.run(dataset))
print(f"平均分: {report.avg_score}, 通过率: {report.pass_rate:.1%}")
```

## 项目结构

```
agentbench/
├── src/
│   ├── main.py              # FastAPI 入口
│   ├── models/              # 数据模型
│   ├── agents/              # Agent 实现（Prompt/RAG/Tool）
│   ├── evaluator/           # 评测维度和评分器
│   ├── pipeline/            # 自动化评测流水线
│   ├── attribution/         # 三层归因分析引擎
│   ├── governance/          # 数据治理
│   ├── integrations/        # Langfuse 集成
│   └── api/routes/          # API 路由
├── frontend/                # Streamlit 前端
├── data/                    # 评测数据和知识库
├── tests/                   # 测试用例
└── config/                  # 配置文件
```

## 开发计划

- [x] Phase 1: 基础框架 + 评测集管理
- [x] Phase 2: Agent 编排 + 评测核心
- [x] Phase 3: 归因分析 + 数据治理
- [ ] Phase 4: 在线评测 + Docker 部署 + 完善测试

## License

MIT
