"""
Base utilities shared by all agents.

This module provides:
- Shared state types for LangGraph
- Data loading utilities
- LLM factory
- A2A message helpers
"""

from dotenv import load_dotenv
load_dotenv()  

from typing import TypedDict, Annotated, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph.message import add_messages
from core.protocol import (
    AgentFacts,
    AgentRole,
    A2AMessage,
    MessageType,
    TrustProfile,
    Certification,
)
import json
from pathlib import Path


# =============================================================================
# STATE TYPES
# =============================================================================

class BaseAgentState(TypedDict):
    """Base state shared by all agents."""
    messages: Annotated[list, add_messages]
    agent_id: str
    agent_name: str


class SupplierAgentState(BaseAgentState):
    """State for supplier agents."""
    catalog: dict
    max_discount_pct: float
    region: str
    currency: str
    lead_time_days: int
    # Outputs
    quote: dict | None
    negotiation_result: dict | None


class LogisticsAgentState(BaseAgentState):
    """State for logistics agents."""
    routes: dict
    # Outputs
    logistics_plan: dict | None


class ComplianceAgentState(BaseAgentState):
    """State for compliance agents."""
    rules: dict
    # Outputs
    compliance_result: dict | None


# =============================================================================
# DATA LOADING
# =============================================================================

_cached_data: dict | None = None


def load_supply_chain_data() -> dict:
    """
    Load the shared mock data from JSON.
    Cached after first load.
    """
    global _cached_data
    if _cached_data is None:
        path = Path(__file__).parent.parent / "data" / "supply_chain_data.json"
        _cached_data = json.loads(path.read_text())
    return _cached_data


def get_supplier_data(supplier_id: str) -> dict:
    """Get data for a specific supplier."""
    data = load_supply_chain_data()
    if supplier_id not in data["suppliers"]:
        raise ValueError(f"Supplier '{supplier_id}' not found")
    return data["suppliers"][supplier_id]


def get_logistics_data() -> dict:
    """Get logistics providers data."""
    data = load_supply_chain_data()
    return data["logistics_providers"]


def get_compliance_rules() -> dict:
    """Get compliance rules data."""
    data = load_supply_chain_data()
    return data["compliance_rules"]


def get_demo_bom() -> dict:
    """Get fallback BOM for demo without GPT."""
    data = load_supply_chain_data()
    return data["demo_bom"]


# =============================================================================
# LLM FACTORY
# =============================================================================

def get_llm(
    model: str = "gpt-4o-mini",
    temperature: float = 0,
) -> ChatOpenAI:
    """
    Get a configured LLM instance.

    Args:
        model: Model name (gpt-4o-mini recommended for agents)
        temperature: 0 for deterministic, higher for creative

    Returns:
        Configured ChatOpenAI instance
    """
    return ChatOpenAI(model=model, temperature=temperature)

# =============================================================================
# A2A MESSAGE HELPERS
# =============================================================================

def create_a2a_message(
    from_agent: str,
    to_agent: str,
    message_type: MessageType,
    payload: dict,
    in_reply_to: str | None = None,
) -> A2AMessage:
    """
    Create a standardized A2A protocol message.

    Args:
        from_agent: Sender agent ID
        to_agent: Recipient agent ID
        message_type: Type of message (RFQ, QUOTATION, etc.)
        payload: Message payload data
        in_reply_to: Optional message ID this replies to

    Returns:
        A2AMessage instance
    """
    return A2AMessage(
        from_agent=from_agent,
        to_agent=to_agent,
        message_type=message_type,
        payload=payload,
        in_reply_to=in_reply_to,
    )


def rfq_message(
    from_agent: str,
    to_agent: str,
    items: list[dict],
    deadline_days: int | None = None,
    budget: float | None = None,
) -> A2AMessage:
    """Create an RFQ (Request for Quote) message."""
    payload = {"items": items}
    if deadline_days:
        payload["deadline_days"] = deadline_days
    if budget:
        payload["budget"] = budget

    return create_a2a_message(
        from_agent=from_agent,
        to_agent=to_agent,
        message_type=MessageType.RFQ,
        payload=payload,
    )


def quote_message(
    from_agent: str,
    to_agent: str,
    quote: dict,
    in_reply_to: str,
) -> A2AMessage:
    """Create a quotation response message."""
    return create_a2a_message(
        from_agent=from_agent,
        to_agent=to_agent,
        message_type=MessageType.QUOTATION,
        payload=quote,
        in_reply_to=in_reply_to,
    )


def negotiate_message(
    from_agent: str,
    to_agent: str,
    requested_discount_pct: float,
    reason: str = "",
    in_reply_to: str | None = None,
) -> A2AMessage:
    """Create a negotiation request message."""
    return create_a2a_message(
        from_agent=from_agent,
        to_agent=to_agent,
        message_type=MessageType.NEGOTIATE,
        payload={
            "requested_discount_pct": requested_discount_pct,
            "reason": reason,
        },
        in_reply_to=in_reply_to,
    )


def accept_message(
    from_agent: str,
    to_agent: str,
    final_quote: dict,
    in_reply_to: str,
) -> A2AMessage:
    """Create an acceptance message."""
    return create_a2a_message(
        from_agent=from_agent,
        to_agent=to_agent,
        message_type=MessageType.ACCEPT,
        payload=final_quote,
        in_reply_to=in_reply_to,
    )


def counter_message(
    from_agent: str,
    to_agent: str,
    counter_offer: dict,
    in_reply_to: str,
) -> A2AMessage:
    """Create a counter-offer message."""
    return create_a2a_message(
        from_agent=from_agent,
        to_agent=to_agent,
        message_type=MessageType.COUNTER,
        payload=counter_offer,
        in_reply_to=in_reply_to,
    )


def reject_message(
    from_agent: str,
    to_agent: str,
    reason: str,
    in_reply_to: str,
) -> A2AMessage:
    """Create a rejection message."""
    return create_a2a_message(
        from_agent=from_agent,
        to_agent=to_agent,
        message_type=MessageType.REJECT,
        payload={"reason": reason},
        in_reply_to=in_reply_to,
    )


# =============================================================================
# AGENT FACTS HELPERS
# =============================================================================

def create_supplier_facts(supplier_id: str) -> AgentFacts:
    """
    Create AgentFacts for a supplier from the mock data.

    Args:
        supplier_id: Key in suppliers dict (e.g., "techparts-global")

    Returns:
        AgentFacts instance ready for registry
    """
    data = get_supplier_data(supplier_id)
    trust_data = data.get("trust", {})

    return AgentFacts(
        agent_id=supplier_id,
        name=data["name"],
        role=AgentRole.SUPPLIER,
        description=f"Supplier based in {data['region']}",
        capabilities=list(data["catalog"].keys()),
        region=data["region"],
        country=data.get("country", ""),
        currency=data.get("currency", "EUR"),
        avg_lead_time_days=data.get("avg_lead_time_days", 7),
        certifications=[
            Certification(**cert) for cert in data.get("certifications", [])
        ],
        trust=TrustProfile(
            verified=trust_data.get("verified", False),
            reputation_score=trust_data.get("reputation_score", 0.5),
            total_transactions=trust_data.get("total_transactions", 0),
            dispute_rate=trust_data.get("dispute_rate", 0.0),
        ),
        endpoint=f"/agents/{supplier_id}",
    )


def create_all_supplier_facts() -> list[AgentFacts]:
    """Create AgentFacts for all suppliers in mock data."""
    data = load_supply_chain_data()
    return [
        create_supplier_facts(supplier_id)
        for supplier_id in data["suppliers"].keys()
    ]


# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

def get_supplier_system_prompt(
    supplier_name: str,
    catalog_parts: list[str],
    region: str,
    lead_time: int,
    max_discount: float,
) -> str:
    """Generate system prompt for a supplier agent."""
    parts_list = ", ".join(catalog_parts[:10])
    if len(catalog_parts) > 10:
        parts_list += f" (+{len(catalog_parts) - 10} more)"

    return f"""You are {supplier_name}, a supplier agent in a B2B supply chain network.

YOUR IDENTITY:
- Name: {supplier_name}
- Region: {region}
- Typical lead time: {lead_time} days
- Maximum discount you can offer: {max_discount}%

YOUR CATALOG INCLUDES:
{parts_list}

YOUR ROLE:
1. Receive RFQ (Request for Quote) messages
2. Look up requested parts in your catalog using the lookup_part tool
3. Check stock availability using check_stock tool
4. Calculate quotes using calculate_quote tool
5. Handle negotiations using evaluate_discount tool

GUIDELINES:
- Be professional and concise
- If a part is not in your catalog, clearly state it's unavailable
- Always use the tools to look up real data - never make up prices
- For negotiations, always use evaluate_discount to check your discount policy

When you have gathered all information, provide a clear structured response."""


def get_logistics_system_prompt() -> str:
    """Generate system prompt for logistics agent."""
    return """You are a logistics coordination agent in a B2B supply chain network.

YOUR ROLE:
1. Receive logistics requests with origin, destination, and cargo details
2. Calculate optimal shipping routes
3. Consider speed vs cost tradeoffs
4. Account for deadline constraints

AVAILABLE CARRIERS:
- DHL Express: Air freight, 3 days, premium pricing
- Maersk Shipping: Sea freight, 21 days, economical
- EU Ground Express: Ground transport, 5 days, EU only

Provide clear routing recommendations with cost breakdowns."""


def get_compliance_system_prompt() -> str:
    """Generate system prompt for compliance agent."""
    return """You are a regulatory compliance agent for EU supply chain operations.

YOUR ROLE:
1. Review orders for regulatory compliance
2. Check CE marking requirements for electronics
3. Verify battery shipping regulations (UN38.3)
4. Check RF transmission power limits for FPV equipment
5. Flag any compliance issues or required certifications

REGULATIONS YOU ENFORCE:
- CE Marking: Required for electronics sold in EU
- Lithium Battery: UN38.3 certification, <100Wh, no passenger aircraft
- RF Regulations: 25mW max for unlicensed 5.8GHz transmission
- Drone Registration: Required for drones >250g

Be thorough but practical. Flag real issues, not theoretical ones."""
