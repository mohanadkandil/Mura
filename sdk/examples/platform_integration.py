"""
Example: How platforms like Comena, Asklio integrate with MURA

This shows how a procurement platform can use MURA as their
supply chain infrastructure layer.
"""

import asyncio
from mura import MuraClient, AgentRole

# =============================================================================
# BASIC USAGE
# =============================================================================

def basic_procurement():
    """Simple one-liner procurement"""

    # Initialize client with your API key
    client = MuraClient(api_key="mura_live_xxx")

    # Run full procurement workflow
    result = client.procure(
        request="500 temperature sensors for industrial monitoring",
        budget=5000,
        deadline_days=14,
        destination_region="EU"
    )

    # Get the recommendation
    print(f"Recommended supplier: {result.recommendation.recommended_supplier}")
    print(f"Total cost: €{result.recommendation.all_options[0].total_cost}")
    print(f"Delivery in: {result.recommendation.critical_path_days} days")

    # Access all quotes
    for quote in result.quotes:
        print(f"  - {quote.supplier_name}: €{quote.total_cost}")


# =============================================================================
# STREAMING (for real-time UI updates)
# =============================================================================

async def streaming_procurement():
    """Stream procurement with live updates (for UI progress)"""

    client = MuraClient(api_key="mura_live_xxx")

    # Stream gives you step-by-step updates
    async for step in client.procure_stream(
        request="Build me a racing drone",
        budget=1000,
        destination_region="EU"
    ):
        agent = step.get("agent", "system")
        message = step.get("message", "")
        print(f"[{agent}] {message}")

        # You can update your UI here in real-time
        # e.g., update_progress_bar(step)


# =============================================================================
# ADVANCED: Use individual services
# =============================================================================

def advanced_usage():
    """Use MURA services individually for more control"""

    client = MuraClient(api_key="mura_live_xxx")

    # 1. Discover suppliers
    suppliers = client.registry.discover(
        role=AgentRole.SUPPLIER,
        capability="electronics",
        region="EU",
        min_trust=0.8  # Only trusted suppliers
    )
    print(f"Found {len(suppliers)} suppliers")

    # 2. Get quotes from specific suppliers
    for supplier in suppliers[:3]:  # Top 3
        quote = client.quotes.get_quote(
            supplier_id=supplier.agent_id,
            items=[
                {"part_name": "temperature_sensor", "quantity": 100},
                {"part_name": "humidity_sensor", "quantity": 50}
            ]
        )
        print(f"{supplier.name}: €{quote['total_cost']}")

    # 3. Check compliance
    compliance = client.compliance.check(
        items=[
            {"part_name": "battery_li_ion", "category": "electronics"}
        ],
        destination_region="EU",
        transport_type="air"
    )
    print(f"Compliance: {compliance['status']}")

    # 4. Plan logistics
    logistics = client.logistics.plan(
        origin_region="Asia",
        destination_region="EU",
        items=[{"weight_kg": 5, "volume_m3": 0.01}],
        deadline_days=7
    )
    print(f"Shipping: {logistics['provider']} - €{logistics['shipping_cost']}")


# =============================================================================
# REAL-WORLD: Comena Integration Example
# =============================================================================

class ComenaBackend:
    """
    Example of how Comena would integrate MURA into their platform.

    Comena is a manufacturing procurement platform that helps
    companies source components for their products.
    """

    def __init__(self):
        # MURA handles all the supply chain complexity
        self.mura = MuraClient(
            api_key="mura_live_xxx",
            base_url="https://api.mura.dev"
        )

    def handle_customer_rfq(self, customer_request: dict):
        """When a Comena customer submits an RFQ"""

        # Let MURA handle the entire workflow
        result = self.mura.procure(
            request=customer_request["description"],
            budget=customer_request.get("budget"),
            deadline_days=customer_request.get("deadline", 14),
            destination_region=customer_request.get("region", "EU"),
        )

        # Transform MURA result to Comena's format
        return {
            "rfq_id": customer_request["id"],
            "status": "quotes_received",
            "recommended_supplier": result.recommendation.recommended_supplier,
            "options": [
                {
                    "supplier": opt.supplier_name,
                    "price": opt.total_cost,
                    "delivery_days": opt.total_days,
                    "compliance": "passed" if opt.compliance_passed else "issues"
                }
                for opt in result.recommendation.all_options
            ],
            "bom": [
                {"part": item.part_name, "qty": item.quantity}
                for item in result.bom.items
            ] if result.bom else []
        }

    async def stream_to_websocket(self, ws, customer_request):
        """Stream live updates to customer's browser"""

        async for step in self.mura.procure_stream(
            request=customer_request["description"],
            budget=customer_request.get("budget"),
        ):
            # Send to customer's WebSocket
            await ws.send_json({
                "type": "procurement_update",
                "agent": step.get("agent"),
                "message": step.get("message"),
                "progress": step.get("progress", 0)
            })


# =============================================================================
# RUN EXAMPLES
# =============================================================================

if __name__ == "__main__":
    print("=== Basic Procurement ===")
    # basic_procurement()  # Uncomment to run

    print("\n=== Streaming ===")
    # asyncio.run(streaming_procurement())  # Uncomment to run

    print("\n=== Advanced Usage ===")
    # advanced_usage()  # Uncomment to run

    print("\nExamples ready - uncomment to run with a real MURA server")
