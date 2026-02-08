"""
Example: How suppliers join the MURA network

This shows how electronics distributors, manufacturers, etc.
can join MURA to automatically receive RFQs and respond with quotes.
"""

from mura import SupplierAgent, Quote, QuoteItem

# =============================================================================
# BASIC: Join the network with a catalog
# =============================================================================

def basic_supplier():
    """Simple supplier with a product catalog"""

    # Create your agent
    agent = SupplierAgent(
        name="Acme Electronics",
        capabilities=["electronics", "sensors", "MCUs"],
        region="EU",
        country="Germany",
        description="Premium electronic components distributor"
    )

    # Add products to your catalog
    agent.add_to_catalog("temperature_sensor", unit_price=5.50, category="sensors", stock=1000)
    agent.add_to_catalog("humidity_sensor", unit_price=4.20, category="sensors", stock=500)
    agent.add_to_catalog("esp32_mcu", unit_price=8.00, category="MCUs", stock=2000)
    agent.add_to_catalog("arduino_nano", unit_price=12.00, category="MCUs", stock=800)

    # Register in MURA network
    agent.register()

    # Start listening for RFQs (auto-responds using catalog)
    print(f"Agent {agent.name} is ready!")
    agent.run()


# =============================================================================
# ADVANCED: Custom RFQ handling
# =============================================================================

def advanced_supplier():
    """Supplier with custom pricing logic"""

    agent = SupplierAgent(
        name="TechParts GmbH",
        capabilities=["electronics", "connectors", "cables"],
        region="EU",
        country="Germany",
        certifications=[
            {"authority": "ISO", "certification": "9001"},
            {"authority": "ISO", "certification": "14001"},
        ],
        max_discount_pct=15.0,
    )

    # Custom RFQ handler for dynamic pricing
    @agent.on_rfq
    def handle_rfq(rfq):
        """Custom logic for handling RFQs"""

        items = []
        total_cost = 0.0

        for item in rfq.items:
            # Look up in your inventory system
            price = get_price_from_erp(item.part_name)
            stock = check_inventory(item.part_name)

            if price is None:
                continue  # Skip items we don't have

            # Volume discounts
            if item.quantity >= 1000:
                price *= 0.85  # 15% discount
            elif item.quantity >= 100:
                price *= 0.92  # 8% discount

            item_total = price * item.quantity
            total_cost += item_total

            items.append(QuoteItem(
                part_name=item.part_name,
                unit_price=price,
                quantity=item.quantity,
                total_price=item_total,
                lead_time_days=3 if stock >= item.quantity else 14,
                in_stock=stock >= item.quantity
            ))

        return Quote(
            supplier_id=agent.agent_id,
            supplier_name=agent.name,
            region=agent.region,
            items=items,
            total_cost=total_cost,
            currency="EUR",
            lead_time_days=max(i.lead_time_days for i in items) if items else 7
        )

    agent.register()
    agent.run()


def get_price_from_erp(part_name: str) -> float:
    """Mock ERP lookup - replace with your system"""
    prices = {
        "temperature_sensor": 5.50,
        "humidity_sensor": 4.20,
        "connector_usb_c": 0.80,
        "cable_usb_1m": 2.50,
    }
    return prices.get(part_name)


def check_inventory(part_name: str) -> int:
    """Mock inventory check - replace with your system"""
    inventory = {
        "temperature_sensor": 5000,
        "humidity_sensor": 2000,
        "connector_usb_c": 10000,
        "cable_usb_1m": 500,
    }
    return inventory.get(part_name, 0)


# =============================================================================
# LOAD CATALOG FROM FILE
# =============================================================================

def supplier_from_json():
    """Load catalog from JSON file"""

    agent = SupplierAgent(
        name="MegaParts Inc",
        capabilities=["electronics"],
        region="US",
    )

    # Load from JSON file
    # catalog.json format:
    # {
    #   "esp32": {"unit_price": 8.0, "category": "MCUs", "stock": 1000},
    #   "sensor_temp": {"unit_price": 5.5, "category": "sensors", "stock": 500}
    # }
    agent.load_catalog_from_json("catalog.json")

    agent.register()
    agent.run()


# =============================================================================
# REAL-WORLD: Mouser Electronics Example
# =============================================================================

class MouserAgent:
    """
    Example of how a large distributor like Mouser would integrate.

    In reality, this would connect to Mouser's inventory and pricing APIs.
    """

    def __init__(self):
        self.agent = SupplierAgent(
            name="Mouser Electronics",
            capabilities=[
                "electronics",
                "semiconductors",
                "passives",
                "connectors",
                "sensors",
                "MCUs",
                "power",
                "RF"
            ],
            region="US",  # HQ, but ships worldwide
            country="USA",
            certifications=[
                {"authority": "ISO", "certification": "9001:2015"},
                {"authority": "AS", "certification": "9120B"},
                {"authority": "ITAR", "certification": "Registered"},
            ],
            description="World's largest selection of electronic components",
            max_discount_pct=20.0,
        )

        # Register the custom handler
        self.agent.on_rfq(self.handle_rfq)

    def handle_rfq(self, rfq):
        """Handle RFQ by querying Mouser's API"""

        items = []
        total = 0.0

        for item in rfq.items:
            # In production: call Mouser's real API
            result = self.search_mouser_api(item.part_name)

            if result:
                items.append(QuoteItem(
                    part_name=item.part_name,
                    unit_price=result["price"],
                    quantity=item.quantity,
                    total_price=result["price"] * item.quantity,
                    lead_time_days=result["lead_time"],
                    in_stock=result["stock"] > 0
                ))
                total += result["price"] * item.quantity

        return Quote(
            supplier_id=self.agent.agent_id,
            supplier_name=self.agent.name,
            region=self.agent.region,
            items=items,
            total_cost=total,
            currency="USD",
            lead_time_days=max((i.lead_time_days for i in items), default=7)
        )

    def search_mouser_api(self, part_name: str) -> dict:
        """
        Mock Mouser API call.

        In production, use:
        https://api.mouser.com/api/v1/search/partnumber
        """
        # Mock response
        return {
            "price": 5.50,
            "stock": 10000,
            "lead_time": 1,
            "manufacturer": "Texas Instruments"
        }

    def run(self):
        self.agent.register()
        self.agent.run()


# =============================================================================
# RUN EXAMPLES
# =============================================================================

if __name__ == "__main__":
    print("=== Basic Supplier ===")
    # basic_supplier()  # Uncomment to run

    print("\n=== Advanced Supplier ===")
    # advanced_supplier()  # Uncomment to run

    print("\n=== Mouser Example ===")
    # MouserAgent().run()  # Uncomment to run

    print("\nExamples ready - uncomment to run with a real MURA server")
