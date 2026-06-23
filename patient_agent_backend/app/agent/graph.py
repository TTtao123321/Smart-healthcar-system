"""LangGraph 图定义与构建"""

from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from app.agent.nodes import agent, guard_in, guard_out, handoff, should_continue
from app.agent.state import AgentState
from app import tools as tools_module

# 缓存编译后的图
_compiled_graph = None


def build_graph() -> StateGraph:
    """构建 Agent 状态图"""
    graph = StateGraph(AgentState)

    # 异步包装：将 agent 节点与工具绑定
    async def agent_with_tools(state):
        return await agent(state, tools_module.ALL_TOOLS)

    # 添加节点
    graph.add_node("guard_in", guard_in)
    graph.add_node("agent", agent_with_tools)
    graph.add_node("tools", ToolNode(tools_module.ALL_TOOLS))
    graph.add_node("guard_out", guard_out)
    graph.add_node("handoff", handoff)

    # 设置入口
    graph.set_entry_point("guard_in")

    # 添加边
    graph.add_edge("guard_in", "agent")
    graph.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "handoff": "handoff",
            "end": "guard_out",
        },
    )
    graph.add_edge("tools", "guard_out")
    graph.add_edge("guard_out", END)
    graph.add_edge("handoff", END)

    return graph


def compile_graph():
    """编译并返回可执行的 Agent 图（带缓存）"""
    global _compiled_graph
    if _compiled_graph is None:
        graph = build_graph()
        _compiled_graph = graph.compile()
    return _compiled_graph


def reset_graph():
    """重置编译缓存（工具变更后调用）"""
    global _compiled_graph
    _compiled_graph = None
