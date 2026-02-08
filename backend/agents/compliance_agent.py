"""
Compliance Agent - LLM-powered regulatory compliance checking.

LangGraph agent that:
1. Receives order details (items, destination, transport)
2. Uses tools to look up applicable regulations
3. Reasons about compliance requirements
4. Returns structured assessment with explanations
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

class ComplianceAgentState(TypedDict):
    """State for compliance agent."""
    messages: Annotated[list, add_messages]
    items: list[dict]
    destination_region: str
    transport_type: str
    supplier_id: str | None
    # Output
    assessment: dict | None


# =============================================================================
# STRUCTURED OUTPUT
# =============================================================================

class ComplianceIssue(BaseModel):
    """A single compliance issue."""
    rule: str = Field(description="Name of the regulation")
    severity: str = Field(description="blocker, warning, or info")
    item: str = Field(description="Which item this applies to")
    description: str = Field(description="What the issue is")
    required_action: str = Field(description="What needs to be done")


class ComplianceAssessment(BaseModel):
    """Structured compliance assessment."""
    passed: bool = Field(description="Whether order passes compliance")
    summary: str = Field(description="Brief summary of compliance status")
    blockers: list[ComplianceIssue] = Field(description="Issues that must be resolved", default=[])
    warnings: list[ComplianceIssue] = Field(description="Issues to be aware of", default=[])
    certifications_required: list[str] = Field(description="Required certifications", default=[])
    reasoning: str = Field(description="Explanation of the assessment")


# =============================================================================
# TOOLS
# =============================================================================

def create_compliance_tools():
    """Create tools for compliance agent."""

    @tool
    def get_regulations_for_region(region: str) -> dict:
        """
        Get all regulations applicable to a destination region.

        Args:
            region: Destination region (EU, US, Asia)

        Returns:
            Applicable regulations with details
        """
        data = load_supply_chain_data()
        rules = data["compliance_rules"]

        applicable = {}
        for rule_id, rule in rules.items():
            rule_region = rule.get("region", "global")
            if rule_region == "global" or rule_region == region:
                applicable[rule_id] = {
                    "name": rule["name"],
                    "region": rule_region,
                    "applies_to_categories": rule.get("required_for", []),
                    "description": rule["description"],
                    "restrictions": rule.get("restrictions", []),
                    "thresholds": {
                        k: v for k, v in rule.items()
                        if k not in ["name", "region", "required_for", "description", "restrictions"]
                    }
                }

        return {
            "region": region,
            "regulations_count": len(applicable),
            "regulations": applicable
        }

    @tool
    def check_ce_requirement(item_category: str, supplier_id: str | None = None) -> dict:
        """
        Check CE marking requirements for an item category.

        Args:
            item_category: Category like 'electronics', 'power', 'fpv'
            supplier_id: Optional supplier to check certifications

        Returns:
            CE requirement details
        """
        data = load_supply_chain_data()
        ce_rule = data["compliance_rules"].get("CE", {})
        required_categories = ce_rule.get("required_for", [])

        requires_ce = item_category in required_categories

        # Check if supplier has CE
        supplier_has_ce = False
        if supplier_id and supplier_id in data["suppliers"]:
            supplier = data["suppliers"][supplier_id]
            certs = supplier.get("certifications", [])
            supplier_has_ce = any(c.get("certification") == "CE" for c in certs)

        return {
            "item_category": item_category,
            "requires_ce": requires_ce,
            "supplier_id": supplier_id,
            "supplier_has_ce": supplier_has_ce,
            "compliant": not requires_ce or supplier_has_ce,
            "action_needed": "Verify CE conformity or use CE-certified supplier" if requires_ce and not supplier_has_ce else None
        }

    @tool
    def check_battery_regulations(transport_type: str, battery_count: int = 1) -> dict:
        """
        Check lithium battery shipping regulations.

        Args:
            transport_type: 'air', 'sea', or 'ground'
            battery_count: Number of batteries being shipped

        Returns:
            Battery shipping compliance details
        """
        data = load_supply_chain_data()
        battery_rule = data["compliance_rules"].get("battery_shipping", {})

        issues = []
        certifications_needed = ["UN38.3"]

        # Air freight has stricter rules
        if transport_type == "air":
            issues.append({
                "severity": "info",
                "issue": "Lithium batteries cannot ship on passenger aircraft",
                "action": "Ensure carrier uses cargo aircraft"
            })

            if battery_count > 2:
                issues.append({
                    "severity": "warning",
                    "issue": f"Shipping {battery_count} batteries may require dangerous goods declaration",
                    "action": "Check carrier DG requirements for quantities > 2"
                })

        return {
            "transport_type": transport_type,
            "battery_count": battery_count,
            "certifications_required": certifications_needed,
            "restrictions": battery_rule.get("restrictions", []),
            "issues": issues,
            "recommendation": "Ground or sea transport recommended for multiple batteries" if battery_count > 2 and transport_type == "air" else None
        }

    @tool
    def check_rf_power_limits(power_mw: int, region: str) -> dict:
        """
        Check RF transmission power against regional limits.

        Args:
            power_mw: Transmitter power in milliwatts
            region: Destination region

        Returns:
            RF compliance assessment
        """
        data = load_supply_chain_data()
        rf_rule = data["compliance_rules"].get("rf_regulations", {})

        if region == "EU":
            max_power = rf_rule.get("max_power_mw", 25)
            exceeds_limit = power_mw > max_power

            return {
                "region": region,
                "device_power_mw": power_mw,
                "legal_limit_mw": max_power,
                "exceeds_limit": exceeds_limit,
                "severity": "blocker" if exceeds_limit else "ok",
                "action": f"Device must be set to {max_power}mW or below, OR operator needs ham radio license" if exceeds_limit else None
            }

        return {
            "region": region,
            "device_power_mw": power_mw,
            "note": "RF limits vary by region - verify local regulations",
            "severity": "info"
        }

    @tool
    def check_drone_registration(total_weight_grams: int, region: str) -> dict:
        """
        Check drone registration requirements.

        Args:
            total_weight_grams: Total drone weight in grams
            region: Destination region

        Returns:
            Registration requirements
        """
        data = load_supply_chain_data()
        drone_rule = data["compliance_rules"].get("drone_registration", {})

        if region == "EU":
            threshold = drone_rule.get("weight_threshold_g", 250)
            requires_registration = total_weight_grams > threshold

            return {
                "region": region,
                "drone_weight_g": total_weight_grams,
                "threshold_g": threshold,
                "requires_registration": requires_registration,
                "severity": "info" if requires_registration else "ok",
                "action": "Register with national aviation authority before flight" if requires_registration else None
            }

        return {
            "region": region,
            "drone_weight_g": total_weight_grams,
            "note": "Check local drone registration requirements"
        }

    @tool
    def get_supplier_certifications(supplier_id: str) -> dict:
        """
        Get all certifications held by a supplier.

        Args:
            supplier_id: The supplier ID

        Returns:
            List of supplier certifications
        """
        data = load_supply_chain_data()

        if supplier_id not in data["suppliers"]:
            return {"error": f"Supplier '{supplier_id}' not found"}

        supplier = data["suppliers"][supplier_id]
        certs = supplier.get("certifications", [])

        return {
            "supplier_id": supplier_id,
            "supplier_name": supplier["name"],
            "region": supplier["region"],
            "certifications": certs,
            "certification_count": len(certs)
        }

    return [
        get_regulations_for_region,
        check_ce_requirement,
        check_battery_regulations,
        check_rf_power_limits,
        check_drone_registration,
        get_supplier_certifications,
    ]


# =============================================================================
# SYSTEM PROMPT
# =============================================================================

COMPLIANCE_SYSTEM_PROMPT = """You are a regulatory compliance agent for EU supply chain operations.

YOUR ROLE:
1. Review orders for regulatory compliance
2. Check applicable regulations based on destination region
3. Identify compliance issues (blockers, warnings, informational)
4. Recommend required certifications and actions

REGULATIONS YOU ENFORCE:
- CE Marking: Required for electronics/power/FPV items sold in EU
- Lithium Battery: UN38.3 certification required, air freight restrictions
- RF Regulations: 25mW max for unlicensed 5.8GHz transmission in EU
- Drone Registration: Required for drones >250g in EU

SEVERITY LEVELS:
- BLOCKER: Must be resolved before order can proceed
- WARNING: Should be addressed but not a hard stop
- INFO: Good to know, no action required

AVAILABLE TOOLS:
- get_regulations_for_region: Get all applicable regulations
- check_ce_requirement: Check CE marking needs
- check_battery_regulations: Check battery shipping rules
- check_rf_power_limits: Check RF transmission limits
- check_drone_registration: Check registration requirements
- get_supplier_certifications: Check what certs a supplier has

GUIDELINES:
- Check ALL relevant regulations for the items
- Be thorough but practical - flag real issues, not theoretical ones
- Clearly explain what action is needed for each issue
- Always specify the severity level
- For FPV/VTX items, check the power specs for RF compliance

Provide a clear assessment with:
1. Overall pass/fail status
2. Any blockers that must be resolved
3. Warnings to be aware of
4. Required certifications"""


# =============================================================================
# AGENT
# =============================================================================

def create_compliance_agent():
    """Create a LangGraph compliance agent."""
    tools = create_compliance_tools()
    llm = get_llm()
    llm_with_tools = llm.bind_tools(tools)

    def agent(state: ComplianceAgentState) -> dict:
        """The agent node - calls LLM with tools."""
        messages = state["messages"]

        # Add system prompt if not present
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=COMPLIANCE_SYSTEM_PROMPT)] + list(messages)

        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: ComplianceAgentState) -> str:
        """Decide whether to continue tool use or end."""
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END

    # Build graph
    tool_node = ToolNode(tools)

    graph = StateGraph(ComplianceAgentState)
    graph.add_node("agent", agent)
    graph.add_node("tools", tool_node)

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def run_compliance_check(
    items: list[dict],
    destination_region: str = "EU",
    transport_type: str = "air",
    supplier_id: str | None = None,
    is_complete_drone: bool = True,
) -> dict:
    """
    Run compliance check using LLM agent.

    Args:
        items: List of items with part_name, category, quantity
        destination_region: Destination region
        transport_type: Shipping method (air, sea, ground)
        supplier_id: Optional supplier for certification check
        is_complete_drone: Whether this is a complete drone build

    Returns:
        Compliance assessment
    """
    agent = create_compliance_agent()

    # Build items description
    items_text = "\n".join(
        f"- {item.get('quantity', 1)}x {item.get('part_name', 'unknown')} (category: {item.get('category', 'unknown')})"
        + (f" - specs: {item.get('specs', '')}" if item.get('specs') else "")
        for item in items
    )

    request = f"""Please check regulatory compliance for this order:

DESTINATION: {destination_region}
TRANSPORT: {transport_type}
{"SUPPLIER: " + supplier_id if supplier_id else "SUPPLIER: Not specified"}
COMPLETE DRONE BUILD: {"Yes" if is_complete_drone else "No"}

ITEMS:
{items_text}

Please check all applicable regulations and provide a compliance assessment."""

    result = agent.invoke({
        "messages": [HumanMessage(content=request)],
        "items": items,
        "destination_region": destination_region,
        "transport_type": transport_type,
        "supplier_id": supplier_id,
        "assessment": None,
    })

    # Extract final response
    final_message = result["messages"][-1]
    response_text = final_message.content if hasattr(final_message, "content") else str(final_message)

    return {
        "status": "success",
        "destination_region": destination_region,
        "transport_type": transport_type,
        "assessment": response_text,
    }


def check_order_compliance(
    quote: dict,
    destination_region: str = "EU",
    transport_type: str = "air",
) -> dict:
    """
    Check compliance for a quote (convenience wrapper).

    Args:
        quote: Quote dict with items and supplier_id
        destination_region: Destination region
        transport_type: Shipping method

    Returns:
        Compliance result
    """
    items = quote.get("items", [])
    supplier_id = quote.get("supplier_id")

    return run_compliance_check(
        items=items,
        supplier_id=supplier_id,
        destination_region=destination_region,
        transport_type=transport_type,
    )


def get_compliance_summary(
    items: list[dict],
    destination_region: str = "EU",
) -> str:
    """
    Get a human-readable compliance summary.

    Args:
        items: List of items
        destination_region: Destination region

    Returns:
        Compliance summary text
    """
    result = run_compliance_check(
        items=items,
        destination_region=destination_region,
    )
    return result.get("assessment", "Unable to generate compliance summary.")
