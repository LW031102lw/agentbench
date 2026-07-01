"""RAG Agent — 基于检索增强生成的 Agent，用于评测 RAG 管线效果"""

from __future__ import annotations
import time
from pathlib import Path

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.settings import OPENAI_API_KEY, OPENAI_BASE_URL, KB_DIR
from src.agents.base_agent import BaseAgent
from src.models.agent_config import AgentConfig
from src.models.evaluation import SingleResult

RAG_SYSTEM_PROMPT = """你是一个专业的知识库问答助手。请根据以下检索到的上下文回答用户问题。

规则：
1. 只使用提供的上下文信息回答问题
2. 如果上下文中没有相关信息，明确告知用户"根据现有知识库无法回答该问题"
3. 引用上下文时标注来源
4. 不要编造上下文中不存在的信息

--- 检索到的上下文 ---
{context}
--- 上下文结束 ---"""


class RAGAgent(BaseAgent):
    """
    RAG Agent：先从知识库检索相关文档片段，再结合检索结果生成回答。
    用于评测检索召回质量、上下文相关性、幻觉率等 RAG 特有指标。
    """

    def __init__(self, config: AgentConfig | None = None):
        if config is None:
            config = AgentConfig(agent_type="rag")
        super().__init__(config)
        self.embeddings = OpenAIEmbeddings(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL,
        )
        self.vectorstore = self._init_vectorstore()

    def _init_vectorstore(self) -> Chroma:
        """初始化向量数据库，加载知识库文档"""
        kb_path = self.config.knowledge_base_path or str(KB_DIR)
        persist_dir = str(Path(kb_path) / "chroma_db")

        # 如果已有持久化数据，直接加载
        if Path(persist_dir).exists():
            return Chroma(
                persist_directory=persist_dir,
                embedding_function=self.embeddings,
            )

        # 否则从文档目录加载
        docs = self._load_documents(kb_path)
        if docs:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.config.chunk_size,
                chunk_overlap=50,
            )
            chunks = splitter.split_documents(docs)
            return Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=persist_dir,
            )

        # 无文档时创建空向量库
        return Chroma(
            embedding_function=self.embeddings,
            persist_directory=persist_dir,
        )

    def _load_documents(self, kb_path: str) -> list:
        """加载知识库文档（支持 .txt / .md）"""
        from langchain_community.document_loaders import DirectoryLoader, TextLoader

        path = Path(kb_path)
        if not path.exists():
            return []

        loaders = []
        for ext in ["*.txt", "*.md"]:
            loaders.append(
                DirectoryLoader(str(path), glob=ext, loader_cls=TextLoader)
            )

        docs = []
        for loader in loaders:
            try:
                docs.extend(loader.load())
            except Exception:
                continue
        return docs

    async def run(self, input_text: str, test_case_id: str = "") -> SingleResult:
        trace = self._create_trace(input_text, test_case_id)
        trace_id = trace.id if trace else None

        # 1. 检索相关文档
        retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": self.config.top_k},
        )
        retrieved_docs = await retriever.ainvoke(input_text)
        context = "\n\n".join([doc.page_content for doc in retrieved_docs])

        # 记录检索 span
        if trace:
            trace.span(
                name="rag-retrieval",
                input={"query": input_text, "top_k": self.config.top_k},
                output={"num_docs": len(retrieved_docs),
                        "docs": [{"content": d.page_content[:200], "source": d.metadata.get("source", "")}
                                 for d in retrieved_docs]},
            )

        # 2. 构造 Prompt 并调用 LLM
        prompt = ChatPromptTemplate.from_messages([
            ("system", RAG_SYSTEM_PROMPT),
            ("human", "{question}"),
        ])
        chain = prompt | self.llm

        start = time.perf_counter()
        response = await chain.ainvoke({"context": context, "question": input_text})
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        agent_output = response.content
        token_usage = {
            "prompt_tokens": response.usage_metadata.get("input_tokens", 0) if response.usage_metadata else 0,
            "completion_tokens": response.usage_metadata.get("output_tokens", 0) if response.usage_metadata else 0,
            "total_tokens": response.usage_metadata.get("total_tokens", 0) if response.usage_metadata else 0,
        }

        # 3. 记录生成 span
        if trace:
            trace.span(
                name="rag-generation",
                input={"context": context[:500], "question": input_text},
                output=agent_output,
                metadata={"latency_ms": elapsed_ms, **token_usage},
            )

        # 4. 构造结果（附带检索元数据供归因分析使用）
        result = self._build_base_result(
            test_case_id=test_case_id,
            input_text=input_text,
            agent_output=agent_output,
            latency_ms=elapsed_ms,
            token_usage=token_usage,
            trace_id=trace_id,
        )
        # 将检索信息存入 metadata，供 RAG 归因分析使用
        result.metadata = {
            "retrieved_docs": [d.page_content for d in retrieved_docs],
            "num_retrieved": len(retrieved_docs),
            "context": context,
        }
        return result
