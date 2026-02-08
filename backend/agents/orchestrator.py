"""
Orchestrator Agent - Coordinates the entire supply chain workflow.

This is the brain of MURA. It:
1. Receives user intent (e.g., "Build me a racing drone")
2. Generates or uses a BOM
3. Discovers suppliers via registry
4. Sends RFQs in parallel to suppliers
5. Collects and compares quotes
6. Runs compliance checks
7. Plans logistics
8. Presents options to user with recommendations

Uses LangGraph for high-level orchestration with tools that call other agents.
"""

from typing import TypedDict, Annotated, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from agents.base import (
    load_supply_chain_data,
    get_demo_bom,
    get_llm,
    create_all_supplier_facts,
)
from agents.supplier_agent import create_supplier_agent
from agents.logistics_agent import (
    get_multi_supplier_logistics,
    plan_logistics,
    estimate_cargo_weight,
)
from agents.compliance_agent import run_compliance_check, check_order_compliance
from core.registry import AgentRegistry, registry
from core.protocol import AgentRole
from core.memory import memory
from core.rl import bandit


# =============================================================================
# STATE
# =============================================================================

class OrchestratorState(TypedDict):
    """State for the orchestrator workflow."""
    messages: Annotated[list, add_messages]

    # Input
    user_request: str
    budget: Optional[float]
    deadline_days: Optional[int]
    destination_region: str
    buyer_id: Optional[str]

    # BOM
    bom: Optional[dict]

    # Discovery
    discovered_suppliers: list[dict]

    # Quotes
    quotes: list[dict]

    # Compliance
    compliance_results: list[dict]

    # Logistics
    logistics_plan: Optional[dict]

    # Final recommendation
    recommendation: Optional[dict]

    # Status
    status: str
    error: Optional[str]

    # Steps tracking for frontend animation
    steps: list[dict]


# =============================================================================
# WORKFLOW STEPS
# =============================================================================

def initialize_workflow(state: OrchestratorState) -> dict:
    """Initialize the workflow with user request."""
    memory.log_activity(f"New request: {state.get('user_request', 'unknown')}")

    return {
        "status": "initialized",
        "discovered_suppliers": [],
        "quotes": [],
        "compliance_results": [],
        "steps": [{"phase": "discovery", "agent": "orchestrator", "message": f"Processing request: {state.get('user_request', 'unknown')[:100]}..."}],
    }


def generate_bom_with_llm(user_request: str) -> dict:
    """
    Use LLM to generate a Bill of Materials based on user request.

    Returns a BOM dict with product name and items list.
    """
    llm = get_llm(temperature=0)

    # Available parts from our actual suppliers
    available_parts = [
        # Drone parts
        "brushless_motor", "esc", "flight_controller", "carbon_frame", "battery",
        "propeller_set", "vtx", "camera", "receiver", "antenna", "gps_module",
        # Electronics
        "temperature_sensor", "humidity_sensor", "pressure_sensor", "esp32_module",
        "arduino_nano", "raspberry_pi_pico", "oled_display",
        # Motors
        "stepper_nema17", "stepper_nema23", "servo_mg996r", "dc_motor_12v",
        # Keyboard
        "cherry_mx_red", "cherry_mx_brown", "pbt_keycaps", "aluminum_case_60", "pcb_hotswap_60",
        # 3D Printing
        "pla_filament_1kg", "petg_filament_1kg", "hotend_v6", "heated_bed_300",
        # LED
        "led_strip_5050", "led_strip_ws2812b", "led_driver_100w",
        # Solar
        "solar_panel_100w", "mppt_controller_60a", "lifepo4_battery_100ah",
    ]

    available_categories = [
        "electronics", "propulsion", "frame", "power", "fpv", "sensors",
        "microcontrollers", "motors", "switches", "keycaps", "filament", "led", "solar"
    ]

    prompt = f"""You are a procurement assistant. Generate a Bill of Materials (BOM) for the following request:

"{user_request}"

Return ONLY valid JSON in this exact format (no markdown, no explanation):
{{
    "product": "Short product name (3-5 words)",
    "items": [
        {{
            "part_name": "component_key",
            "category": "category_name",
            "quantity": 1,
            "description": "Brief description"
        }}
    ]
}}

Rules:
- Generate 3-8 realistic components for the product
- IMPORTANT: Use these exact part names when applicable: {', '.join(available_parts[:20])}
- Categories should be one of: {', '.join(available_categories)}
- part_name should be lowercase with underscores
- quantity should be realistic (1-10 typically)
- For drones: use brushless_motor, esc, flight_controller, carbon_frame, battery, propeller_set, vtx, camera"""

    response = llm.invoke([HumanMessage(content=prompt)])

    try:
        # Parse the JSON response
        content = response.content.strip()
        # Remove markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        bom = json.loads(content)
        return bom
    except (json.JSONDecodeError, Exception) as e:
        # Fallback to a generic BOM based on request
        return {
            "product": user_request[:50],
            "items": [
                {"part_name": "main_component", "category": "electronics", "quantity": 1, "description": "Primary component"},
                {"part_name": "controller", "category": "electronics", "quantity": 1, "description": "Control unit"},
                {"part_name": "power_supply", "category": "power", "quantity": 1, "description": "Power source"},
                {"part_name": "housing", "category": "structural", "quantity": 1, "description": "Enclosure"},
            ]
        }


def generate_bom(state: OrchestratorState) -> dict:
    """
    Generate BOM for the request using LLM.

    Uses GPT to parse user intent and generate appropriate components.
    """
    user_request = state.get("user_request", "")

    # Use LLM to generate dynamic BOM
    bom = generate_bom_with_llm(user_request)

    memory.log_activity(f"Generated BOM: {bom['product']} with {len(bom['items'])} items")
    steps = state.get("steps", [])
    steps.append({"phase": "discovery", "agent": "orchestrator", "message": f"Generated BOM: {bom['product']} with {len(bom.get('items', []))} components"})

    return {
        "bom": bom,
        "status": "bom_generated",
        "messages": [AIMessage(content=f"Generated BOM for {bom['product']} with {len(bom.get('items', []))} components.")],
        "steps": steps,
    }


def discover_suppliers(state: OrchestratorState) -> dict:
    """Discover relevant suppliers from registry."""
    bom = state.get("bom", {})
    deadline_days = state.get("deadline_days", 7)

    if not bom:
        return {"status": "error", "error": "No BOM available"}

    # Register all suppliers (in production, they'd self-register)
    all_suppliers = create_all_supplier_facts()
    for supplier in all_suppliers:
        try:
            registry.register(supplier)
        except ValueError:
            pass  # Already registered

    # Discover suppliers that can provide drone parts
    categories_needed = set(item.get("category") for item in bom.get("items", []))

    discovered = []
    for category in categories_needed:
        suppliers = registry.discover(
            role=AgentRole.SUPPLIER,
            capability=category,
        )
        for s in suppliers:
            if s.agent_id not in [d["agent_id"] for d in discovered]:
                discovered.append({
                    "agent_id": s.agent_id,
                    "name": s.name,
                    "region": s.region,
                    "capabilities": s.capabilities,
                    "trust_score": s.trust.reputation_score if s.trust else 0.5,
                })

    # Rank by deadline awareness
    if deadline_days:
        ranked = registry.rank_for_rfq(
            [registry.get(d["agent_id"]) for d in discovered],
            deadline_days=deadline_days,
        )
        discovered = [
            {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "region": agent.region,
                "score": score,
            }
            for agent, score in ranked
        ]

    memory.log_activity(f"Discovered {len(discovered)} suppliers")

    # Add steps for each discovered supplier
    steps = state.get("steps", [])
    steps.append({"phase": "discovery", "agent": "orchestrator", "message": f"Searching registry for capable suppliers..."})
    for supplier in discovered:
        steps.append({"phase": "discovery", "agent": f"supplier-{supplier['agent_id']}", "message": f"Found supplier: {supplier['name']} ({supplier['region']})"})

    return {
        "discovered_suppliers": discovered,
        "status": "suppliers_discovered",
        "messages": [AIMessage(content=f"Found {len(discovered)} suppliers capable of fulfilling the order.")],
        "steps": steps,
    }


def _get_single_quote(supplier: dict, items: list, deadline_days: int, budget: float) -> dict:
    """Get quote from a single supplier. Used for parallel execution."""
    supplier_id = supplier["agent_id"]

    try:
        # Get RL-suggested discount to ask for
        discount_ask, rl_reason = bandit.choose_discount(supplier_id)

        # Load supplier catalog to calculate prices
        supplier_data = load_supply_chain_data()["suppliers"].get(supplier_id, {})
        catalog = supplier_data.get("catalog", {})

        # Create supplier agent
        agent = create_supplier_agent(supplier_id)

        # Build RFQ message
        rfq_parts = [f"- {item['quantity']}x {item['part_name']}" for item in items]
        rfq_text = f"""I need a quote for the following parts:
{chr(10).join(rfq_parts)}

Deadline: {deadline_days} days
{"Budget: €" + str(budget) if budget else ""}

I'd like to request a {discount_ask}% discount on this order.
{rl_reason}"""

        # Run the supplier agent
        result = agent.invoke({
            "messages": [HumanMessage(content=rfq_text)],
            "agent_id": supplier_id,
            "agent_name": supplier["name"],
            "catalog": {},  # Will be loaded by agent
            "max_discount_pct": 0,  # Will be loaded
            "region": supplier.get("region", ""),
            "currency": "EUR",
            "lead_time_days": 7,
            "quote": None,
            "negotiation_result": None,
        })

        # Extract response
        final_message = result["messages"][-1]
        response_text = final_message.content if hasattr(final_message, "content") else str(final_message)

        # Calculate total cost from catalog
        total_cost = 0.0
        quoted_items = []
        for item in items:
            part_name = item.get("part_name", "")
            category = item.get("category", "")
            quantity = item.get("quantity", 1)

            # Try exact match first
            matched_key = None
            if part_name in catalog:
                matched_key = part_name
            else:
                # Try partial match on part_name or category
                for cat_key, cat_item in catalog.items():
                    cat_category = cat_item.get("category", "")
                    # Match by category or if part name contains catalog key or vice versa
                    if (cat_category == category or
                        part_name in cat_key or
                        cat_key in part_name or
                        any(word in cat_key for word in part_name.split("_"))):
                        matched_key = cat_key
                        break

            if matched_key:
                unit_price = catalog[matched_key].get("unit_price", 0)
                item_total = unit_price * quantity
                total_cost += item_total
                quoted_items.append({
                    "part_name": catalog[matched_key].get("part_name", matched_key),
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "total": item_total,
                })

        # Apply estimated discount
        estimated_discount = min(discount_ask * 0.6, supplier_data.get("max_discount_pct", 10))
        discount_amount = total_cost * (estimated_discount / 100)
        final_total = total_cost - discount_amount

        # Record for RL learning
        bandit.record_outcome(
            supplier_id=supplier_id,
            discount_asked=discount_ask,
            discount_received=estimated_discount,
            decision="COUNTER",
        )

        memory.log_activity(f"Got quote from {supplier['name']}: €{final_total:.2f}")

        return {
            "supplier_id": supplier_id,
            "supplier_name": supplier["name"],
            "region": supplier.get("region"),
            "items": quoted_items,
            "subtotal": total_cost,
            "discount_pct": estimated_discount,
            "discount_amount": discount_amount,
            "total": final_total,
            "discount_asked": discount_ask,
            "response": response_text,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        return {
            "supplier_id": supplier_id,
            "supplier_name": supplier.get("name", supplier_id),
            "error": str(e),
        }


def request_quotes(state: OrchestratorState) -> dict:
    """Request quotes from discovered suppliers IN PARALLEL."""
    bom = state.get("bom", {})
    discovered = state.get("discovered_suppliers", [])
    deadline_days = state.get("deadline_days", 7)
    budget = state.get("budget")

    if not discovered:
        return {"status": "error", "error": "No suppliers discovered"}

    items = bom.get("items", [])
    quotes = []

    # Run quote requests in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=len(discovered)) as executor:
        # Submit all quote requests
        future_to_supplier = {
            executor.submit(_get_single_quote, supplier, items, deadline_days, budget): supplier
            for supplier in discovered
        }

        # Collect results as they complete
        for future in as_completed(future_to_supplier):
            quote = future.result()
            quotes.append(quote)

    # Add steps for each quote
    steps = state.get("steps", [])
    for quote in quotes:
        if "error" not in quote:
            supplier_name = quote.get("supplier_name", quote.get("supplier_id", "Unknown"))
            total = quote.get("total", 0)
            steps.append({"phase": "quoting", "agent": f"supplier-{quote.get('supplier_id', 'unknown')}", "message": f"{supplier_name} quote: €{total:.2f}"})
        else:
            steps.append({"phase": "quoting", "agent": f"supplier-{quote.get('supplier_id', 'unknown')}", "message": f"Quote failed: {quote.get('error', 'Unknown error')}"})

    return {
        "quotes": quotes,
        "status": "quotes_received",
        "messages": [AIMessage(content=f"Received {len([q for q in quotes if 'error' not in q])} quotes from suppliers.")],
        "steps": steps,
    }


def check_compliance(state: OrchestratorState) -> dict:
    """Run compliance checks on quotes."""
    quotes = state.get("quotes", [])
    destination = state.get("destination_region", "EU")

    compliance_results = []

    for quote in quotes:
        if "error" in quote:
            continue

        items = quote.get("items", [])
        supplier_id = quote.get("supplier_id")

        result = run_compliance_check(
            items=items,
            supplier_id=supplier_id,
            destination_region=destination,
            transport_type="air",  # Default to air for speed
        )

        # Parse the assessment text to determine pass/fail
        assessment = result.get("assessment", "")
        assessment_lower = assessment.lower()

        # Determine if passed based on assessment content
        has_blockers = "blocker" in assessment_lower or "blocked" in assessment_lower or "not compliant" in assessment_lower
        passed = result.get("status") == "success" and not has_blockers

        compliance_results.append({
            "supplier_id": supplier_id,
            "passed": passed,
            "summary": assessment[:500] if assessment else "Compliance check completed",
            "blockers": 1 if has_blockers else 0,
            "warnings": 1 if "warning" in assessment_lower else 0,
            "certifications_required": [],
        })

    memory.log_activity(f"Compliance check: {sum(1 for r in compliance_results if r['passed'])}/{len(compliance_results)} passed")

    # Add steps for compliance
    steps = state.get("steps", [])
    steps.append({"phase": "compliance", "agent": "compliance", "message": f"Checking {destination} regulations for {len(compliance_results)} suppliers..."})
    for result in compliance_results:
        status = "Passed" if result["passed"] else "Issues found"
        steps.append({"phase": "compliance", "agent": "compliance", "message": f"{result['supplier_id']}: {status}"})

    return {
        "compliance_results": compliance_results,
        "status": "compliance_checked",
        "steps": steps,
    }


def plan_delivery(state: OrchestratorState) -> dict:
    """Plan logistics for delivery."""
    quotes = state.get("quotes", [])
    destination = state.get("destination_region", "EU")
    deadline_days = state.get("deadline_days", 7)

    # Filter to valid quotes
    valid_quotes = [q for q in quotes if "error" not in q]

    if not valid_quotes:
        return {
            "logistics_plan": {"error": "No valid quotes to plan logistics for"},
            "status": "logistics_failed",
        }

    # Get multi-supplier logistics plan
    logistics_plan = get_multi_supplier_logistics(
        supplier_quotes=valid_quotes,
        destination_region=destination,
        deadline_days=deadline_days,
    )

    # Calculate critical path from per-supplier plans
    per_supplier = logistics_plan.get("per_supplier", [])
    if per_supplier:
        # Try to get estimated_days, fall back to deadline_days
        days_list = [
            p.get("estimated_days") or p.get("deadline_days") or deadline_days or 7
            for p in per_supplier
        ]
        critical_path_days = max(days_list) if days_list else (deadline_days or 7)
    else:
        critical_path_days = deadline_days or 7

    logistics_plan["critical_path_days"] = critical_path_days

    memory.log_activity(f"Logistics planned: {critical_path_days} days critical path")

    # Add steps for logistics
    steps = state.get("steps", [])
    steps.append({"phase": "logistics", "agent": "logistics", "message": f"Analyzing shipping routes to {destination}..."})
    for plan in per_supplier:
        supplier_name = plan.get("supplier_name", plan.get("supplier_id", "Unknown"))
        origin = plan.get("origin_region", "Unknown")
        steps.append({"phase": "logistics", "agent": "logistics", "message": f"{supplier_name}: {origin} → {destination}"})
    steps.append({"phase": "logistics", "agent": "logistics", "message": f"Critical path: {critical_path_days} days"})

    return {
        "logistics_plan": logistics_plan,
        "status": "logistics_planned",
        "steps": steps,
    }


def generate_recommendation(state: OrchestratorState) -> dict:
    """Generate final recommendation."""
    quotes = state.get("quotes", [])
    compliance = state.get("compliance_results", [])
    logistics = state.get("logistics_plan", {})
    budget = state.get("budget")
    deadline_days = state.get("deadline_days", 7)
    buyer_id = state.get("buyer_id")

    # Score each option
    scored_options = []

    for quote in quotes:
        if "error" in quote:
            continue

        supplier_id = quote["supplier_id"]

        # Get compliance result
        comp = next(
            (c for c in compliance if c["supplier_id"] == supplier_id),
            {"passed": False, "blockers": 99}
        )

        # Get logistics for this supplier
        supplier_logistics = next(
            (l for l in logistics.get("per_supplier", []) if l["supplier_id"] == supplier_id),
            {}
        )

        # Calculate score (higher is better)
        score = 0

        # Compliance (must pass)
        if comp["passed"]:
            score += 30
        else:
            score -= comp["blockers"] * 10

        # Deadline (critical)
        total_days = supplier_logistics.get("total_days", 999)
        if deadline_days and total_days <= deadline_days:
            score += 25
        elif deadline_days:
            score -= (total_days - deadline_days) * 5

        # Trust score
        trust = next(
            (s.get("score", 0.5) for s in state.get("discovered_suppliers", []) if s["agent_id"] == supplier_id),
            0.5
        )
        score += trust * 20

        # Region preference (EU suppliers for EU destination)
        if quote.get("region") == state.get("destination_region"):
            score += 10

        scored_options.append({
            "supplier_id": supplier_id,
            "supplier_name": quote["supplier_name"],
            "score": score,
            "compliance_passed": comp["passed"],
            "total_days": total_days,
            "meets_deadline": total_days <= (deadline_days or 999),
            "shipping_cost": supplier_logistics.get("shipping_cost", 0),
        })

    # Sort by score
    scored_options.sort(key=lambda x: x["score"], reverse=True)

    # Generate recommendation
    if scored_options:
        best = scored_options[0]
        recommendation = {
            "recommended_supplier": best["supplier_id"],
            "recommendation_reason": generate_recommendation_text(best, deadline_days),
            "all_options": scored_options,
            "total_shipping_cost": logistics.get("total_shipping_cost", 0),
            "meets_deadline": logistics.get("meets_deadline", False),
            "critical_path_days": logistics.get("critical_path_days", 0),
        }
    else:
        recommendation = {
            "recommended_supplier": None,
            "recommendation_reason": "No suppliers could fulfill the order.",
            "all_options": [],
        }

    # Log insights
    if buyer_id and scored_options:
        memory.add_insight(
            f"For {state.get('user_request', 'unknown')}: Best option is {scored_options[0]['supplier_name']}",
            category="recommendation",
        )

    # Add steps for recommendation
    steps = state.get("steps", [])
    steps.append({"phase": "complete", "agent": "orchestrator", "message": "Analyzing all options..."})
    if scored_options:
        best = scored_options[0]
        steps.append({"phase": "complete", "agent": "orchestrator", "message": f"Recommended: {best['supplier_name']} (score: {best['score']:.0f})"})

    return {
        "recommendation": recommendation,
        "status": "complete",
        "messages": [AIMessage(content=format_recommendation(recommendation))],
        "steps": steps,
    }


def generate_recommendation_text(option: dict, deadline_days: int) -> str:
    """Generate human-readable recommendation reason."""
    reasons = []

    if option["compliance_passed"]:
        reasons.append("passes all compliance checks")
    else:
        reasons.append("has compliance issues that need resolution")

    if option["meets_deadline"]:
        reasons.append(f"delivers in {option['total_days']} days (within {deadline_days}-day deadline)")
    else:
        reasons.append(f"delivers in {option['total_days']} days (exceeds {deadline_days}-day deadline)")

    if option["score"] > 50:
        reasons.append("has high trust score")

    return f"{option['supplier_name']} is recommended because it " + " and ".join(reasons) + "."


def format_recommendation(rec: dict) -> str:
    """Format recommendation for display."""
    if not rec.get("recommended_supplier"):
        return "Unable to find suppliers that meet your requirements."

    lines = [
        f"**Recommended: {rec.get('recommendation_reason')}**",
        "",
        f"Total shipping cost: €{rec.get('total_shipping_cost', 0):.2f}",
        f"Critical path: {rec.get('critical_path_days', 0)} days",
        f"Meets deadline: {'✅ Yes' if rec.get('meets_deadline') else '❌ No'}",
        "",
        "**All Options (ranked):**",
    ]

    for i, opt in enumerate(rec.get("all_options", [])[:5], 1):
        status = "✅" if opt["compliance_passed"] and opt["meets_deadline"] else "⚠️"
        lines.append(f"{i}. {status} {opt['supplier_name']} (score: {opt['score']:.0f}, {opt['total_days']} days)")

    return "\n".join(lines)


# =============================================================================
# GRAPH
# =============================================================================

def create_orchestrator():
    """Create the orchestrator workflow graph."""
    graph = StateGraph(OrchestratorState)

    # Add nodes
    graph.add_node("initialize", initialize_workflow)
    graph.add_node("generate_bom", generate_bom)
    graph.add_node("discover_suppliers", discover_suppliers)
    graph.add_node("request_quotes", request_quotes)
    graph.add_node("check_compliance", check_compliance)
    graph.add_node("plan_delivery", plan_delivery)
    graph.add_node("generate_recommendation", generate_recommendation)

    # Define flow
    graph.set_entry_point("initialize")
    graph.add_edge("initialize", "generate_bom")
    graph.add_edge("generate_bom", "discover_suppliers")
    graph.add_edge("discover_suppliers", "request_quotes")
    graph.add_edge("request_quotes", "check_compliance")
    graph.add_edge("check_compliance", "plan_delivery")
    graph.add_edge("plan_delivery", "generate_recommendation")
    graph.add_edge("generate_recommendation", END)

    return graph.compile()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def run_procurement(
    request: str,
    budget: Optional[float] = None,
    deadline_days: int = 7,
    destination_region: str = "EU",
    buyer_id: Optional[str] = None,
) -> dict:
    """
    Run full procurement workflow.

    Args:
        request: User's natural language request
        budget: Optional budget constraint
        deadline_days: Delivery deadline
        destination_region: Destination region
        buyer_id: Optional buyer ID for personalization

    Returns:
        Complete procurement result
    """
    orchestrator = create_orchestrator()

    result = orchestrator.invoke({
        "messages": [HumanMessage(content=request)],
        "user_request": request,
        "budget": budget,
        "deadline_days": deadline_days,
        "destination_region": destination_region,
        "buyer_id": buyer_id,
        "bom": None,
        "discovered_suppliers": [],
        "quotes": [],
        "compliance_results": [],
        "logistics_plan": None,
        "recommendation": None,
        "status": "starting",
        "error": None,
        "steps": [],
    })

    return {
        "status": result["status"],
        "bom": result.get("bom"),
        "suppliers_found": len(result.get("discovered_suppliers", [])),
        "quotes_received": len([q for q in result.get("quotes", []) if "error" not in q]),
        "compliance": result.get("compliance_results"),
        "logistics": result.get("logistics_plan"),
        "recommendation": result.get("recommendation"),
        "steps": result.get("steps", []),
        "messages": [m.content for m in result.get("messages", []) if hasattr(m, "content")],
    }


async def run_procurement_streaming(
    request: str,
    budget: Optional[float] = None,
    deadline_days: int = 7,
    destination_region: str = "EU",
    buyer_id: Optional[str] = None,
):
    """
    Stream procurement workflow with real-time step updates.

    Yields steps as they happen for SSE streaming.
    """
    import asyncio

    # Initialize state
    state = {
        "messages": [HumanMessage(content=request)],
        "user_request": request,
        "budget": budget,
        "deadline_days": deadline_days,
        "destination_region": destination_region,
        "buyer_id": buyer_id,
        "bom": None,
        "discovered_suppliers": [],
        "quotes": [],
        "compliance_results": [],
        "logistics_plan": None,
        "recommendation": None,
        "status": "starting",
        "error": None,
        "steps": [],
    }

    # Step 1: Initialize
    yield {"type": "step", "phase": "discovery", "agent": "orchestrator", "message": f"Processing request: {request[:80]}..."}
    await asyncio.sleep(0.1)

    # Step 2: Generate BOM
    yield {"type": "step", "phase": "discovery", "agent": "orchestrator", "message": "Generating Bill of Materials..."}
    await asyncio.sleep(0.1)

    bom_result = generate_bom(state)
    state.update(bom_result)
    bom = state.get("bom", {})

    yield {"type": "step", "phase": "discovery", "agent": "orchestrator", "message": f"BOM ready: {bom.get('product', 'Unknown')} with {len(bom.get('items', []))} components"}
    await asyncio.sleep(0.1)

    # Step 3: Discover suppliers
    yield {"type": "step", "phase": "discovery", "agent": "orchestrator", "message": "Searching registry for suppliers..."}
    await asyncio.sleep(0.1)

    discover_result = discover_suppliers(state)
    state.update(discover_result)
    discovered = state.get("discovered_suppliers", [])

    # Handle no suppliers found
    if not discovered:
        yield {
            "type": "step",
            "phase": "discovery",
            "agent": "supplier-none",
            "message": "No suppliers found in registry for these components",
            "status": "error"
        }
        await asyncio.sleep(0.2)
    else:
        # Yield each discovered supplier
        for supplier in discovered:
            yield {
                "type": "step",
                "phase": "discovery",
                "agent": f"supplier-{supplier['agent_id']}",
                "message": f"Found: {supplier['name']} ({supplier.get('region', 'Unknown')})",
                "status": "success"
            }
            await asyncio.sleep(0.2)

    # Step 4: Request quotes
    yield {"type": "step", "phase": "quoting", "agent": "orchestrator", "message": f"Requesting quotes from {len(discovered)} suppliers..."}
    await asyncio.sleep(0.1)

    quotes_result = request_quotes(state)
    state.update(quotes_result)
    quotes = state.get("quotes", [])

    # Yield each quote
    for quote in quotes:
        if "error" not in quote:
            supplier_name = quote.get("supplier_name", quote.get("supplier_id", "Unknown"))
            total = quote.get("total", 0)
            yield {
                "type": "step",
                "phase": "quoting",
                "agent": f"supplier-{quote.get('supplier_id', 'unknown')}",
                "message": f"{supplier_name}: €{total:.2f}",
                "status": "success"
            }
        else:
            yield {
                "type": "step",
                "phase": "quoting",
                "agent": f"supplier-{quote.get('supplier_id', 'unknown')}",
                "message": f"Quote failed: {quote.get('error', 'Unknown error')[:50]}",
                "status": "error"
            }
        await asyncio.sleep(0.3)

    # Step 5: Compliance checks
    yield {"type": "step", "phase": "compliance", "agent": "compliance", "message": f"Checking {destination_region} regulations..."}
    await asyncio.sleep(0.1)

    compliance_result = check_compliance(state)
    state.update(compliance_result)
    compliance_results = state.get("compliance_results", [])

    for result in compliance_results:
        passed = result.get("passed", False)
        blockers = result.get("blockers", 0)
        warnings = result.get("warnings", 0)
        summary = result.get("summary", "")

        if passed:
            status_msg = "Compliant"
        else:
            issues = []
            if blockers > 0:
                issues.append(f"{blockers} blocker(s)")
            if warnings > 0:
                issues.append(f"{warnings} warning(s)")
            status_msg = f"Issues: {', '.join(issues)}" if issues else "Review needed"

        yield {
            "type": "step",
            "phase": "compliance",
            "agent": "compliance",
            "message": f"{result.get('supplier_id', 'Unknown')}: {status_msg}",
            "details": summary[:300] if summary else None,
            "status": "success" if passed else "warning" if warnings > 0 else "error"
        }
        await asyncio.sleep(0.3)

    # Step 6: Logistics planning
    yield {"type": "step", "phase": "logistics", "agent": "logistics", "message": f"Analyzing shipping routes to {destination_region}..."}
    await asyncio.sleep(0.1)

    logistics_result = plan_delivery(state)
    state.update(logistics_result)
    logistics_plan = state.get("logistics_plan", {})

    for plan in logistics_plan.get("per_supplier", []):
        supplier_name = plan.get("supplier_name", plan.get("supplier_id", "Unknown"))
        origin = plan.get("origin_region", "Unknown")
        yield {
            "type": "step",
            "phase": "logistics",
            "agent": "logistics",
            "message": f"{supplier_name}: {origin} → {destination_region}"
        }
        await asyncio.sleep(0.2)

    critical_days = logistics_plan.get("critical_path_days", deadline_days)
    yield {"type": "step", "phase": "logistics", "agent": "logistics", "message": f"Critical path: {critical_days} days"}
    await asyncio.sleep(0.1)

    # Step 7: Generate recommendation
    yield {"type": "step", "phase": "complete", "agent": "orchestrator", "message": "Analyzing options and generating recommendation..."}
    await asyncio.sleep(0.1)

    rec_result = generate_recommendation(state)
    state.update(rec_result)
    recommendation = state.get("recommendation", {})

    if recommendation.get("recommended_supplier"):
        all_options = recommendation.get("all_options", [])
        if all_options:
            best = all_options[0]
            yield {
                "type": "step",
                "phase": "complete",
                "agent": "orchestrator",
                "message": f"Recommended: {best.get('supplier_name', 'Unknown')} (score: {best.get('score', 0):.0f})"
            }

    # Final result
    await asyncio.sleep(0.2)
    yield {
        "type": "complete",
        "data": {
            "status": state.get("status", "complete"),
            "bom": state.get("bom"),
            "suppliers_found": len(discovered),
            "quotes_received": len([q for q in quotes if "error" not in q]),
            "compliance": compliance_results,
            "logistics": logistics_plan,
            "recommendation": recommendation,
        }
    }


# Singleton orchestrator
orchestrator = create_orchestrator()
