from src.agents.base_agent import BaseAgent
from src.agents.prompt_agent import PromptAgent
from src.agents.rag_agent import RAGAgent
from src.agents.tool_agent import ToolAgent

__all__ = ["BaseAgent", "PromptAgent", "RAGAgent", "ToolAgent"]


def create_agent(agent_type: str, config=None) -> BaseAgent:
    """工厂函数：根据类型创建 Agent"""
    agents = {
        "prompt": PromptAgent,
        "rag": RAGAgent,
        "tool": ToolAgent,
    }
    cls = agents.get(agent_type)
    if not cls:
        raise ValueError(f"未知的 Agent 类型: {agent_type}，可选: {list(agents.keys())}")
    return cls(config)
