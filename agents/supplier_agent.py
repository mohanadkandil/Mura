from typing import Annotated
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from agents.base import (
    SupplierAgentState,
    get_supplier_data,
    get_supplier_system_prompt,
    get_llm,
)
from agents.tools.catalog_tools import create_catalog_tools

def create_supplier_agent(supplier_id: str):
    """Factory function that creates a LangGraph agent for a specific supplier."""

    # Load this supplier's data
    supplier_data = get_supplier_data(supplier_id)
    catalog = supplier_data["catalog"]
    max_discount = supplier_data["max_discount_pct"]

    tools = create_catalog_tools(catalog, max_discount)
    llm = get_llm(model="gpt-4o-mini", temperature=0)
    llm_with_tools = llm.bind_tools(tools)

    system_prompt = get_supplier_system_prompt(
        supplier_name=supplier_data["name"],
        catalog_parts=list(catalog.keys()),
        region=supplier_data["region"],
        lead_time=supplier_data["avg_lead_time_days"],
        max_discount=max_discount,
    )

    # Nodes

    def agent(state: SupplierAgentState):
        """LLM reasoning node."""
        messages = state["messages"]

        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=system_prompt)] + messages

        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    tool_node = ToolNode(tools)

    # Edges
    def should_continue(state: SupplierAgentState):
        """Check if LLM wants to use tools or is done."""
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        
        return END
    
    # Build graph 
    graph = StateGraph(SupplierAgentState)
    graph.add_node("agent", agent)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")
    return graph.compile()