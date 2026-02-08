"""
PACT API - Supply Chain Agent Coordination Network

FastAPI backend providing:
- /procure - Full procurement workflow
- /quote - Get quotes from suppliers
- /logistics - Calculate shipping options
- /compliance - Check regulatory compliance
- /registry - Agent discovery
- /health - Health check

WebSocket support for real-time updates (TODO)
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, AsyncGenerator
import asyncio
import json

from agents.orchestrator import run_procurement, create_orchestrator, run_procurement_streaming
from agents.supplier_agent import create_supplier_agent
from agents.logistics_agent import (
    get_logistics_quote,
    get_multi_supplier_logistics,
    plan_logistics,
)
from agents.compliance_agent import (
    run_compliance_check,
    check_order_compliance,
    get_compliance_summary,
)
from agents.base import (
    load_supply_chain_data,
    get_demo_bom,
    create_all_supplier_facts,
)
from core.registry import registry
from core.protocol import AgentRole
from core.memory import memory
from core.rl import bandit, stats


# =============================================================================
# APP
# =============================================================================

app = FastAPI(
    title="PACT API",
    description="Supply Chain Agent Coordination Network - Where Agents Shake Hands",
    version="0.1.0",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# MODELS
# =============================================================================

class ProcurementRequest(BaseModel):
    """Request for full procurement workflow."""
    request: str = Field(..., description="Natural language request, e.g., 'Build me a racing drone'")
    budget: Optional[float] = Field(None, description="Budget constraint in EUR")
    deadline_days: int = Field(7, description="Delivery deadline in days")
    destination_region: str = Field("EU", description="Destination region (EU, US, Asia)")
    buyer_id: Optional[str] = Field(None, description="Buyer ID for personalization")


class QuoteRequest(BaseModel):
    """Request for supplier quote."""
    supplier_id: str = Field(..., description="Supplier ID, e.g., 'techparts-global'")
    items: list[dict] = Field(..., description="Items to quote, e.g., [{'part_name': 'brushless_motor', 'quantity': 4}]")
    deadline_days: Optional[int] = Field(None, description="Deadline constraint")
    discount_pct: Optional[float] = Field(None, description="Discount to request")


class LogisticsRequest(BaseModel):
    """Request for logistics calculation."""
    origin_region: str = Field(..., description="Origin region")
    destination_region: str = Field(..., description="Destination region")
    items: list[dict] = Field(..., description="Items to ship")
    deadline_days: Optional[int] = Field(None, description="Deadline constraint")


class ComplianceRequest(BaseModel):
    """Request for compliance check."""
    items: list[dict] = Field(..., description="Items with category")
    supplier_id: Optional[str] = Field(None, description="Supplier for certification check")
    destination_region: str = Field("EU", description="Destination region")
    transport_type: str = Field("air", description="Transport type (air, sea, ground)")


class DiscoveryRequest(BaseModel):
    """Request for agent discovery."""
    role: Optional[str] = Field(None, description="Agent role (SUPPLIER, LOGISTICS, COMPLIANCE)")
    capability: Optional[str] = Field(None, description="Required capability, e.g., 'propulsion'")
    region: Optional[str] = Field(None, description="Region filter")
    min_trust: float = Field(0.0, description="Minimum trust score")


# =============================================================================
# STARTUP
# =============================================================================

@app.on_event("startup")
async def startup():
    """Register all agents on startup."""
    # Register suppliers
    all_suppliers = create_all_supplier_facts()
    for supplier in all_suppliers:
        try:
            registry.register(supplier)
        except ValueError:
            pass  # Already registered

    memory.log_activity("PACT API started")


# =============================================================================
# HEALTH
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "PACT API",
        "tagline": "Where Agents Shake Hands",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "healthy",
        "agents_registered": len(registry._agents),
        "memory_active": True,
        "rl_active": True,
    }


# =============================================================================
# PROCUREMENT
# =============================================================================

@app.post("/procure")
async def procure(request: ProcurementRequest):
    """
    Run full procurement workflow.

    This is the main endpoint that orchestrates everything:
    1. Parses request → BOM
    2. Discovers suppliers
    3. Gets quotes in parallel
    4. Checks compliance
    5. Plans logistics
    6. Returns recommendation
    """
    try:
        result = run_procurement(
            request=request.request,
            budget=request.budget,
            deadline_days=request.deadline_days,
            destination_region=request.destination_region,
            buyer_id=request.buyer_id,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/procure/stream")
async def procure_stream(request: ProcurementRequest):
    """
    Stream procurement workflow with real-time updates via SSE.

    Each step is sent as a Server-Sent Event as it happens.
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            async for step in run_procurement_streaming(
                request=request.request,
                budget=request.budget,
                deadline_days=request.deadline_days,
                destination_region=request.destination_region,
                buyer_id=request.buyer_id,
            ):
                # SSE format: data: {json}\n\n
                yield f"data: {json.dumps(step)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# =============================================================================
# QUOTES
# =============================================================================

@app.post("/quote")
async def get_quote(request: QuoteRequest):
    """
    Get a quote from a specific supplier.

    Uses the LangGraph supplier agent to negotiate.
    """
    try:
        from langchain_core.messages import HumanMessage

        # Get RL suggestion if no discount specified
        if request.discount_pct is None:
            discount_ask, reason = bandit.choose_discount(request.supplier_id)
        else:
            discount_ask = request.discount_pct
            reason = "User specified"

        # Create supplier agent
        agent = create_supplier_agent(request.supplier_id)

        # Build RFQ
        items_text = "\n".join(
            f"- {item.get('quantity', 1)}x {item['part_name']}"
            for item in request.items
        )
        rfq = f"""Quote request:
{items_text}

{"Deadline: " + str(request.deadline_days) + " days" if request.deadline_days else ""}
Requesting {discount_ask}% discount. ({reason})"""

        # Run agent
        result = agent.invoke({
            "messages": [HumanMessage(content=rfq)],
            "agent_id": request.supplier_id,
            "agent_name": request.supplier_id,
            "catalog": {},
            "max_discount_pct": 0,
            "region": "",
            "currency": "EUR",
            "lead_time_days": 7,
            "quote": None,
            "negotiation_result": None,
        })

        response = result["messages"][-1].content

        return {
            "supplier_id": request.supplier_id,
            "discount_asked": discount_ask,
            "rl_reason": reason,
            "response": response,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/quote/demo")
async def demo_bom():
    """Get the demo BOM for testing."""
    return get_demo_bom()


# =============================================================================
# LOGISTICS
# =============================================================================

@app.post("/logistics")
async def calculate_logistics(request: LogisticsRequest):
    """Calculate shipping options using LLM agent."""
    result = plan_logistics(
        origin_region=request.origin_region,
        destination_region=request.destination_region,
        items=request.items,
        deadline_days=request.deadline_days,
    )
    # LLM agent returns natural language recommendation
    return result


@app.get("/logistics/providers")
async def list_logistics_providers():
    """List all logistics providers."""
    data = load_supply_chain_data()
    return data["logistics_providers"]


# =============================================================================
# COMPLIANCE
# =============================================================================

@app.post("/compliance")
async def check_compliance_endpoint(request: ComplianceRequest):
    """Run compliance check using LLM agent."""
    result = run_compliance_check(
        items=request.items,
        supplier_id=request.supplier_id,
        destination_region=request.destination_region,
        transport_type=request.transport_type,
    )
    # LLM agent returns natural language assessment
    return result


@app.get("/compliance/rules")
async def list_compliance_rules():
    """List all compliance rules."""
    data = load_supply_chain_data()
    return data["compliance_rules"]


# =============================================================================
# REGISTRY
# =============================================================================

@app.post("/registry/discover")
async def discover_agents(request: DiscoveryRequest):
    """Discover agents matching criteria."""
    role = None
    if request.role:
        try:
            role = AgentRole(request.role.upper())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid role: {request.role}")

    agents = registry.discover(
        role=role,
        capability=request.capability,
        region=request.region,
        min_trust=request.min_trust,
    )

    return [
        {
            "agent_id": a.agent_id,
            "name": a.name,
            "role": a.role.value,
            "region": a.region,
            "capabilities": a.capabilities,
            "trust_score": a.trust.reputation_score if a.trust else None,
        }
        for a in agents
    ]


@app.get("/registry/agents")
async def list_agents():
    """
    List all registered agents with full AgentFacts.

    Returns NANDA-compliant agent data including:
    - Identity (agent_id, name, role)
    - Capabilities
    - Certifications
    - ZTAA Trust Profile (trust level, reputation, attestations)
    """
    return [
        {
            "agent_id": a.agent_id,
            "name": a.name,
            "role": a.role.value,
            "description": a.description,
            "region": a.region,
            "country": a.country,
            "capabilities": a.capabilities,
            "avg_lead_time_days": a.avg_lead_time_days,
            "certifications": [
                {
                    "authority": c.authority,
                    "certification": c.certification,
                    "cert_id": c.cert_id,
                }
                for c in a.certifications
            ] if a.certifications else [],
            "trust": {
                "verified": a.trust.verified,
                "trust_level": a.trust.trust_level.value if hasattr(a.trust, 'trust_level') else "self_declared",
                "reputation_score": a.trust.reputation_score,
                "total_transactions": a.trust.total_transactions,
                "successful_transactions": getattr(a.trust, 'successful_transactions', a.trust.total_transactions),
                "dispute_rate": a.trust.dispute_rate,
                "peer_attestations": getattr(a.trust, 'peer_attestations', 0),
            } if a.trust else None,
            "endpoint": a.endpoint,
        }
        for a in registry._agents.values()
    ]


@app.get("/registry/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get a specific agent."""
    agent = registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

    return {
        "agent_id": agent.agent_id,
        "name": agent.name,
        "role": agent.role.value,
        "description": agent.description,
        "region": agent.region,
        "country": agent.country,
        "capabilities": agent.capabilities,
        "avg_lead_time_days": agent.avg_lead_time_days,
        "trust": {
            "verified": agent.trust.verified,
            "reputation_score": agent.trust.reputation_score,
            "total_transactions": agent.trust.total_transactions,
            "dispute_rate": agent.trust.dispute_rate,
        } if agent.trust else None,
    }


# =============================================================================
# RL / INSIGHTS
# =============================================================================

@app.get("/insights/rl")
async def get_rl_insights():
    """Get RL-learned negotiation insights."""
    return bandit.get_all_insights()


@app.get("/insights/rl/{supplier_id}")
async def get_supplier_rl_insights(supplier_id: str):
    """Get RL insights for a specific supplier."""
    return bandit.get_supplier_insights(supplier_id)


@app.get("/insights/stats")
async def get_negotiation_stats():
    """Get negotiation statistics."""
    return stats.get_all_stats()


# =============================================================================
# DATA
# =============================================================================

@app.get("/data/suppliers")
async def list_suppliers():
    """List all suppliers with catalog info."""
    data = load_supply_chain_data()
    return {
        supplier_id: {
            "name": s["name"],
            "region": s["region"],
            "max_discount_pct": s["max_discount_pct"],
            "catalog_items": list(s["catalog"].keys()),
        }
        for supplier_id, s in data["suppliers"].items()
    }


@app.get("/data/suppliers/{supplier_id}/catalog")
async def get_supplier_catalog(supplier_id: str):
    """Get a supplier's catalog."""
    data = load_supply_chain_data()
    if supplier_id not in data["suppliers"]:
        raise HTTPException(status_code=404, detail=f"Supplier not found: {supplier_id}")
    return data["suppliers"][supplier_id]["catalog"]


@app.get("/data/buyers/{buyer_id}")
async def get_buyer_profile(buyer_id: str):
    """Get buyer profile and analytics."""
    data = load_supply_chain_data()
    if buyer_id not in data.get("buyers", {}):
        raise HTTPException(status_code=404, detail=f"Buyer not found: {buyer_id}")
    return data["buyers"][buyer_id]


# =============================================================================
# MEMORY
# =============================================================================

@app.get("/memory/insights")
async def get_memory_insights():
    """Get learned insights from memory."""
    return {"insights": memory.get_insights()}


@app.get("/memory/logs")
async def get_recent_logs(days: int = 7):
    """Get recent activity logs."""
    return {"logs": memory.get_recent_logs(days)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
