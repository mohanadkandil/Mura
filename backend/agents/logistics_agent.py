"""
Logistics Agent - LLM-powered route optimization.

LangGraph agent that:
1. Receives shipping requests
2. Uses tools to look up carrier options
3. Reasons about best choice based on deadline, cost, reliability
4. Returns structured recommendation with explanation
"""

from typing import TypedDict, Annotated
from langchain_core.tools import tool
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

from agents.base import load_supply_chain_data, get_llm


# =============================================================================
# STATE
# =============================================================================

class LogisticsAgentState(TypedDict):
    """State for logistics agent."""
    messages: Annotated[list, add_messages]
    origin_region: str
    destination_region: str
    weight_kg: float
    deadline_days: int | None
    # Output
    recommendation: dict | None


# =============================================================================
# STRUCTURED OUTPUT
# =============================================================================

class ShippingRecommendation(BaseModel):
    """Structured output for shipping recommendation."""
    carrier: str = Field(description="Recommended carrier name")
    carrier_id: str = Field(description="Carrier ID for system use")
    transport_type: str = Field(description="air, sea, or ground")
    transit_days: int = Field(description="Expected transit time in days")
    cost: float = Field(description="Total shipping cost in EUR")
    meets_deadline: bool = Field(description="Whether this meets the deadline")
    reasoning: str = Field(description="Explanation of why this carrier was chosen")
    alternatives: list[dict] = Field(description="Other options considered", default=[])


# =============================================================================
# TOOLS
# =============================================================================

def create_logistics_tools():
    """Create tools for logistics agent."""

    @tool
    def list_carriers(origin_region: str, destination_region: str) -> dict:
        """
        List all carriers that can ship between two regions.

        Args:
            origin_region: Origin region (EU, US, Asia)
            destination_region: Destination region (EU, US, Asia)

        Returns:
            Available carriers with their capabilities
        """
        data = load_supply_chain_data()
        providers = data["logistics_providers"]

        available = []
        for provider_id, provider in providers.items():
            regions = provider["regions"]
            if origin_region in regions and destination_region in regions:
                available.append({
                    "carrier_id": provider_id,
                    "name": provider["name"],
                    "type": provider["type"],
                    "base_cost_eur": provider["base_cost"],
                    "cost_per_kg_eur": provider["cost_per_kg"],
                    "transit_days": provider["speed_days"],
                    "tracking": provider.get("tracking", False),
                })

        if not available:
            return {
                "error": f"No carriers available for {origin_region} → {destination_region}",
                "available_carriers": []
            }

        return {
            "route": f"{origin_region} → {destination_region}",
            "available_carriers": available
        }

    @tool
    def calculate_shipping_cost(carrier_id: str, weight_kg: float) -> dict:
        """
        Calculate total shipping cost for a carrier.

        Args:
            carrier_id: The carrier ID (e.g., 'dhl-express')
            weight_kg: Cargo weight in kilograms

        Returns:
            Cost breakdown
        """
        data = load_supply_chain_data()
        providers = data["logistics_providers"]

        if carrier_id not in providers:
            return {"error": f"Carrier '{carrier_id}' not found"}

        provider = providers[carrier_id]
        base_cost = provider["base_cost"]
        weight_cost = provider["cost_per_kg"] * weight_kg
        total_cost = base_cost + weight_cost

        return {
            "carrier_id": carrier_id,
            "carrier_name": provider["name"],
            "base_cost_eur": base_cost,
            "weight_cost_eur": round(weight_cost, 2),
            "total_cost_eur": round(total_cost, 2),
            "weight_kg": weight_kg,
            "transit_days": provider["speed_days"],
        }

    @tool
    def check_deadline_feasibility(carrier_id: str, deadline_days: int) -> dict:
        """
        Check if a carrier can meet the deadline.

        Args:
            carrier_id: The carrier ID
            deadline_days: Required delivery deadline in days

        Returns:
            Feasibility assessment
        """
        data = load_supply_chain_data()
        providers = data["logistics_providers"]

        if carrier_id not in providers:
            return {"error": f"Carrier '{carrier_id}' not found"}

        provider = providers[carrier_id]
        transit_days = provider["speed_days"]
        meets_deadline = transit_days <= deadline_days
        buffer_days = deadline_days - transit_days

        return {
            "carrier_id": carrier_id,
            "carrier_name": provider["name"],
            "transit_days": transit_days,
            "deadline_days": deadline_days,
            "meets_deadline": meets_deadline,
            "buffer_days": buffer_days if meets_deadline else None,
            "days_over": -buffer_days if not meets_deadline else None,
        }

    @tool
    def estimate_cargo_weight(items: list[dict]) -> dict:
        """
        Estimate cargo weight from a list of items.

        Args:
            items: List of items with part_name and quantity

        Returns:
            Weight estimate with breakdown
        """
        weight_map = {
            "brushless_motor": 0.05,
            "esc": 0.03,
            "flight_controller": 0.02,
            "carbon_frame": 0.15,
            "battery": 0.20,
            "propeller_set": 0.01,
            "vtx": 0.03,
            "camera": 0.03,
            "antenna": 0.01,
            "receiver": 0.01,
            "battery_strap": 0.02,
        }

        breakdown = []
        total_weight = 0.0

        for item in items:
            part = item.get("part_name", "unknown")
            qty = item.get("quantity", 1)
            unit_weight = weight_map.get(part, 0.05)
            item_weight = unit_weight * qty
            total_weight += item_weight
            breakdown.append({
                "part": part,
                "quantity": qty,
                "unit_weight_kg": unit_weight,
                "total_weight_kg": round(item_weight, 3),
            })

        # Add 20% for packaging
        packaging = total_weight * 0.2
        final_weight = total_weight + packaging

        return {
            "items_weight_kg": round(total_weight, 3),
            "packaging_kg": round(packaging, 3),
            "total_weight_kg": round(final_weight, 3),
            "breakdown": breakdown,
        }

    return [list_carriers, calculate_shipping_cost, check_deadline_feasibility, estimate_cargo_weight]


# =============================================================================
# SYSTEM PROMPT
# =============================================================================

LOGISTICS_SYSTEM_PROMPT = """You are a logistics optimization agent for a B2B supply chain network.

YOUR ROLE:
1. Receive shipping requests with origin, destination, cargo, and deadline
2. Use your tools to find available carriers and calculate costs
3. Analyze trade-offs between speed, cost, and reliability
4. Recommend the best shipping option with clear reasoning

DECISION CRITERIA (in order of priority):
1. DEADLINE - Must meet the deadline if possible
2. COST - Among options that meet deadline, prefer cheaper
3. RELIABILITY - Consider tracking and carrier reputation

AVAILABLE TOOLS:
- list_carriers: Find carriers that serve the route
- calculate_shipping_cost: Get exact cost for a carrier
- check_deadline_feasibility: Verify if carrier meets deadline
- estimate_cargo_weight: Calculate weight from items list

GUIDELINES:
- Always check ALL available carriers before recommending
- Calculate costs for each viable option
- Explain WHY you chose the recommended carrier
- If no carrier meets the deadline, recommend the fastest and explain the delay
- Be specific with numbers (costs, days, weights)

When you have analyzed all options, provide your recommendation with:
1. The chosen carrier and why
2. Total cost and transit time
3. Whether it meets the deadline
4. Alternative options considered"""


# =============================================================================
# AGENT
# =============================================================================

def create_logistics_agent():
    """Create a LangGraph logistics agent."""
    tools = create_logistics_tools()
    llm = get_llm()
    llm_with_tools = llm.bind_tools(tools)

    def agent(state: LogisticsAgentState) -> dict:
        """The agent node - calls LLM with tools."""
        messages = state["messages"]

        # Add system prompt if not present
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=LOGISTICS_SYSTEM_PROMPT)] + list(messages)

        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: LogisticsAgentState) -> str:
        """Decide whether to continue tool use or end."""
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END

    # Build graph
    tool_node = ToolNode(tools)

    graph = StateGraph(LogisticsAgentState)
    graph.add_node("agent", agent)
    graph.add_node("tools", tool_node)

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def plan_logistics(
    origin_region: str,
    destination_region: str,
    items: list[dict],
    deadline_days: int | None = None,
) -> dict:
    """
    Get logistics recommendation using LLM agent.

    Args:
        origin_region: Where goods ship from
        destination_region: Where goods ship to
        items: List of items with part_name and quantity
        deadline_days: Deadline constraint

    Returns:
        Agent's recommendation
    """
    agent = create_logistics_agent()

    # Build request message
    items_text = "\n".join(
        f"- {item.get('quantity', 1)}x {item.get('part_name', 'unknown')}"
        for item in items
    )

    request = f"""Please find the best shipping option for this request:

ORIGIN: {origin_region}
DESTINATION: {destination_region}
{"DEADLINE: " + str(deadline_days) + " days" if deadline_days else "NO DEADLINE"}

CARGO:
{items_text}

Please analyze all carriers, calculate costs, and recommend the best option."""

    result = agent.invoke({
        "messages": [HumanMessage(content=request)],
        "origin_region": origin_region,
        "destination_region": destination_region,
        "weight_kg": 0,  # Agent will calculate
        "deadline_days": deadline_days,
        "recommendation": None,
    })

    # Extract final response
    final_message = result["messages"][-1]
    response_text = final_message.content if hasattr(final_message, "content") else str(final_message)

    return {
        "status": "success",
        "origin": origin_region,
        "destination": destination_region,
        "deadline_days": deadline_days,
        "recommendation": response_text,
    }


# For backwards compatibility with orchestrator
def get_logistics_quote(*args, **kwargs):
    """Backwards compatible wrapper."""
    return plan_logistics(*args, **kwargs)


def get_multi_supplier_logistics(
    supplier_quotes: list[dict],
    destination_region: str,
    deadline_days: int | None = None,
) -> dict:
    """
    Get logistics plan for multiple suppliers.

    Args:
        supplier_quotes: List of quotes with supplier_id and items
        destination_region: Final destination
        deadline_days: Deadline constraint

    Returns:
        Combined logistics plan
    """
    data = load_supply_chain_data()
    suppliers = data["suppliers"]

    plans = []

    for quote in supplier_quotes:
        supplier_id = quote.get("supplier_id")
        items = quote.get("items", [])

        if supplier_id not in suppliers:
            continue

        supplier = suppliers[supplier_id]
        origin_region = supplier["region"]

        # Get logistics recommendation for this supplier
        plan = plan_logistics(
            origin_region=origin_region,
            destination_region=destination_region,
            items=items,
            deadline_days=deadline_days,
        )

        plans.append({
            "supplier_id": supplier_id,
            "supplier_name": supplier["name"],
            "origin_region": origin_region,
            "total_days": deadline_days or 7,  # Default estimate
            "shipping_cost": 50.0,  # Default shipping cost
            **plan,
        })

    return {
        "destination": destination_region,
        "deadline_days": deadline_days,
        "per_supplier": plans,
    }


def estimate_cargo_weight(items: list[dict]) -> float:
    """Utility function for weight estimation."""
    weight_map = {
        "brushless_motor": 0.05,
        "esc": 0.03,
        "flight_controller": 0.02,
        "carbon_frame": 0.15,
        "battery": 0.20,
        "propeller_set": 0.01,
        "vtx": 0.03,
        "camera": 0.03,
        "antenna": 0.01,
        "receiver": 0.01,
        "battery_strap": 0.02,
    }

    total_weight = 0.0
    for item in items:
        part = item.get("part_name", "")
        qty = item.get("quantity", 1)
        weight = weight_map.get(part, 0.05)
        total_weight += weight * qty

    return round(total_weight * 1.2, 2)  # +20% for packaging
