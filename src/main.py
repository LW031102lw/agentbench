"""AgentBench — FastAPI 主入口"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import datasets, evaluations, attribution, governance

app = FastAPI(
    title="AgentBench API",
    description="AI Agent 智能评测平台 — 自动化评测、多层归因分析、数据治理",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 注册路由 ──────────────────────────────────────────
app.include_router(datasets.router, prefix="/api/datasets", tags=["评测集管理"])
app.include_router(evaluations.router, prefix="/api/evaluations", tags=["评测执行"])
app.include_router(attribution.router, prefix="/api/attribution", tags=["归因分析"])
app.include_router(governance.router, prefix="/api/governance", tags=["数据治理"])


@app.get("/")
async def root():
    return {
        "name": "AgentBench",
        "version": "1.0.0",
        "description": "AI Agent 智能评测平台",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
