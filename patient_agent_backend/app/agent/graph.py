"""LangGraph 图定义与构建"""

from langgraph.graph import END, StateGraph

from app.agent.nodes import agent, guard_in, guard_out, handoff, should_continue
from app.agent.prompts import build_patient_system_prompt
from app.agent.state import AgentState
from app import tools as tools_module

# 缓存编译后的图
_compiled_graph = None


def build_graph(tools: list | None = None, system_prompt: str | None = None) -> StateGraph:
    """构建 Agent 状态图"""
    graph = StateGraph(AgentState)
    active_tools = tools if tools is not None else tools_module.ALL_TOOLS
    active_prompt = system_prompt or build_patient_system_prompt()

    # 异步包装：将 agent 节点与工具绑定（内部处理工具调用循环）
    async def agent_with_tools(state):
        return await agent(state, active_tools, active_prompt)

    # 添加节点
    graph.add_node("guard_in", guard_in)
    graph.add_node("agent", agent_with_tools)
    graph.add_node("guard_out", guard_out)
    graph.add_node("handoff", handoff)

    # 设置入口
    graph.set_entry_point("guard_in")

    # 添加边：agent 内部处理工具调用，只需判断是否需要转人工
    graph.add_edge("guard_in", "agent")
    graph.add_conditional_edges(
        "agent",
        should_continue,
        {
            "handoff": "handoff",
            "end": "guard_out",
        },
    )
    graph.add_edge("guard_out", END)
    graph.add_edge("handoff", END)

    return graph


def compile_graph(
    *,
    tools: list | None = None,
    system_prompt: str | None = None,
    channel: str = "patient",
    clinician_context=None,
):
    """编译并返回可执行的 Agent 图（带缓存）"""
    global _compiled_graph
    if tools is not None or system_prompt is not None or channel != "patient" or clinician_context is not None:
        return build_graph(tools=tools, system_prompt=system_prompt).compile()
    if _compiled_graph is None:
        graph = build_graph()
        _compiled_graph = graph.compile()
    return _compiled_graph


def reset_graph():
    """重置编译缓存（工具变更后调用）"""
    global _compiled_graph
    _compiled_graph = None
