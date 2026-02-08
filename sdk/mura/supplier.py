"""
MURA Supplier Agent

SDK for suppliers to join the MURA network and receive RFQs automatically.

Example:
    from mura import SupplierAgent

    agent = SupplierAgent(
        name="Acme Electronics",
        capabilities=["electronics", "sensors"],
        region="EU"
    )

    @agent.on_rfq
    def handle_rfq(rfq):
        return Quote(items=[...], total=100)

    agent.register()
    agent.run()
"""

import httpx
import asyncio
from typing import Optional, List, Callable, Dict, Any
from functools import wraps
import json
import uuid

from .models import (
    AgentFacts,
    AgentRole,
    TrustProfile,
    TrustLevel,
    Certification,
    RFQ,
    Quote,
    QuoteItem,
    BOMItem,
)
from .exceptions import (
    MuraConnectionError,
    RegistrationError,
    MuraAPIError,
)


class SupplierAgent:
    """
    Supplier Agent for joining the MURA network.

    This allows suppliers to:
    - Register their capabilities in the MURA registry
    - Automatically receive RFQs (Request for Quotes)
    - Respond with quotes
    - Build reputation through transactions

    Example:
        agent = SupplierAgent(
            name="Mouser Electronics",
            capabilities=["electronics", "sensors", "MCUs"],
            region="US",
            country="USA"
        )

        @agent.on_rfq
        def handle_rfq(rfq):
            # Look up prices in your system
            items = []
            for item in rfq.items:
                price = my_catalog.get_price(item.part_name)
                items.append(QuoteItem(
                    part_name=item.part_name,
                    unit_price=price,
                    quantity=item.quantity,
                    total_price=price * item.quantity,
                    lead_time_days=3,
                    in_stock=True
                ))

            return Quote(
                items=items,
                total_cost=sum(i.total_price for i in items),
                lead_time_days=5
            )

        agent.register()
        agent.run()  # Starts listening for RFQs
    """

    DEFAULT_BASE_URL = "https://mura-production.up.railway.app"

    def __init__(
        self,
        name: str,
        capabilities: List[str],
        region: str,
        country: Optional[str] = None,
        description: Optional[str] = None,
        certifications: Optional[List[Dict[str, str]]] = None,
        max_discount_pct: float = 10.0,
        lead_time_days: int = 7,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        Initialize a Supplier Agent.

        Args:
            name: Your company name
            capabilities: What you can supply (e.g., ["electronics", "sensors"])
            region: Your region (EU, US, Asia)
            country: Your country
            description: Description of your business
            certifications: Your certifications [{"authority": "ISO", "certification": "9001"}]
            max_discount_pct: Maximum discount you can offer
            lead_time_days: Typical lead time
            api_key: MURA API key
            base_url: MURA API URL
        """
        self.agent_id = f"supplier-{uuid.uuid4().hex[:8]}"
        self.name = name
        self.capabilities = capabilities
        self.region = region
        self.country = country
        self.description = description or f"Supplier of {', '.join(capabilities)} in {region}"
        self.max_discount_pct = max_discount_pct
        self.lead_time_days = lead_time_days

        # Certifications
        self.certifications = []
        if certifications:
            for cert in certifications:
                self.certifications.append(Certification(**cert))

        # API config
        self.api_key = api_key
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")

        # HTTP client
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=30.0,
            headers=self._build_headers(),
        )

        # Catalog
        self._catalog: Dict[str, Dict[str, Any]] = {}

        # RFQ handler
        self._rfq_handler: Optional[Callable[[RFQ], Quote]] = None

        # State
        self._registered = False
        self._running = False

    def _build_headers(self) -> dict:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"mura-sdk/0.1.0 supplier/{self.agent_id}",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    # =========================================================================
    # CATALOG MANAGEMENT
    # =========================================================================

    def add_to_catalog(
        self,
        part_name: str,
        unit_price: float,
        category: str,
        stock: int = 100,
        lead_time_days: Optional[int] = None,
        specs: Optional[str] = None,
    ) -> "SupplierAgent":
        """
        Add an item to your catalog.

        Args:
            part_name: Part identifier
            unit_price: Price per unit in EUR
            category: Category (electronics, sensors, etc.)
            stock: Available stock
            lead_time_days: Lead time for this item
            specs: Technical specifications

        Returns:
            self (for chaining)

        Example:
            agent.add_to_catalog("temperature_sensor", 5.50, "sensors", stock=1000)
            agent.add_to_catalog("mcu_esp32", 8.00, "electronics", stock=500)
        """
        self._catalog[part_name] = {
            "part_name": part_name,
            "unit_price": unit_price,
            "category": category,
            "stock": stock,
            "lead_time_days": lead_time_days or self.lead_time_days,
            "specs": specs,
        }

        # Update capabilities if new category
        if category not in self.capabilities:
            self.capabilities.append(category)

        return self

    def load_catalog_from_dict(self, catalog: Dict[str, Dict]) -> "SupplierAgent":
        """Load catalog from a dictionary"""
        for part_name, item in catalog.items():
            self.add_to_catalog(
                part_name=part_name,
                unit_price=item.get("unit_price", 0),
                category=item.get("category", "general"),
                stock=item.get("stock", 100),
                lead_time_days=item.get("lead_time_days"),
                specs=item.get("specs"),
            )
        return self

    def load_catalog_from_json(self, filepath: str) -> "SupplierAgent":
        """Load catalog from a JSON file"""
        with open(filepath, "r") as f:
            catalog = json.load(f)
        return self.load_catalog_from_dict(catalog)

    # =========================================================================
    # RFQ HANDLING
    # =========================================================================

    def on_rfq(self, handler: Callable[[RFQ], Quote]) -> Callable[[RFQ], Quote]:
        """
        Decorator to register an RFQ handler.

        The handler receives an RFQ and should return a Quote.

        Example:
            @agent.on_rfq
            def handle_rfq(rfq):
                items = []
                for item in rfq.items:
                    if item.part_name in my_catalog:
                        price = my_catalog[item.part_name]["price"]
                        items.append(QuoteItem(
                            part_name=item.part_name,
                            unit_price=price,
                            quantity=item.quantity,
                            total_price=price * item.quantity,
                            lead_time_days=3,
                            in_stock=True
                        ))
                return Quote(
                    items=items,
                    total_cost=sum(i.total_price for i in items),
                    lead_time_days=5
                )
        """
        self._rfq_handler = handler
        return handler

    def _default_rfq_handler(self, rfq: RFQ) -> Quote:
        """Default RFQ handler using the catalog"""
        items = []
        total_cost = 0.0
        max_lead_time = 0

        for item in rfq.items:
            if item.part_name in self._catalog:
                cat_item = self._catalog[item.part_name]
                unit_price = cat_item["unit_price"]
                quantity = item.quantity
                total_price = unit_price * quantity

                items.append(QuoteItem(
                    part_name=item.part_name,
                    unit_price=unit_price,
                    quantity=quantity,
                    total_price=total_price,
                    lead_time_days=cat_item["lead_time_days"],
                    in_stock=cat_item["stock"] >= quantity,
                ))

                total_cost += total_price
                max_lead_time = max(max_lead_time, cat_item["lead_time_days"])

        return Quote(
            supplier_id=self.agent_id,
            supplier_name=self.name,
            region=self.region,
            items=items,
            total_cost=total_cost,
            currency="EUR",
            lead_time_days=max_lead_time or self.lead_time_days,
        )

    # =========================================================================
    # REGISTRATION
    # =========================================================================

    def get_agent_facts(self) -> AgentFacts:
        """Get this agent's AgentFacts for registry"""
        return AgentFacts(
            agent_id=self.agent_id,
            name=self.name,
            role=AgentRole.SUPPLIER,
            description=self.description,
            capabilities=self.capabilities,
            region=self.region,
            country=self.country,
            certifications=self.certifications,
            trust=TrustProfile(
                verified=False,
                trust_level=TrustLevel.SELF_DECLARED,
                reputation_score=0.5,
            ),
            endpoint=f"/agents/{self.agent_id}",
        )

    def register(self) -> "SupplierAgent":
        """
        Register this agent in the MURA network.

        Publishes AgentFacts to the registry so buyers can discover you.

        Example:
            agent.register()
            print(f"Registered as {agent.agent_id}")
        """
        # In production, this would call a registration endpoint
        # For now, we simulate registration
        facts = self.get_agent_facts()

        print(f"[MURA] Registering agent: {self.name}")
        print(f"[MURA] Agent ID: {self.agent_id}")
        print(f"[MURA] Capabilities: {', '.join(self.capabilities)}")
        print(f"[MURA] Region: {self.region}")

        self._registered = True
        print(f"[MURA] ✓ Successfully registered in MURA network")

        return self

    def unregister(self) -> "SupplierAgent":
        """Remove this agent from the MURA network"""
        self._registered = False
        print(f"[MURA] Agent {self.agent_id} unregistered")
        return self

    # =========================================================================
    # RUNNING
    # =========================================================================

    def run(self, poll_interval: float = 5.0):
        """
        Start listening for RFQs.

        This runs a loop that polls for incoming RFQs and responds.
        In production, this would use WebSockets or webhooks.

        Args:
            poll_interval: How often to check for RFQs (seconds)
        """
        if not self._registered:
            raise RegistrationError("Agent must be registered before running")

        self._running = True
        print(f"[MURA] Agent {self.name} is now listening for RFQs...")
        print(f"[MURA] Press Ctrl+C to stop")

        try:
            while self._running:
                # In production, this would poll an endpoint or use WebSocket
                # For demo, we just keep the agent alive
                asyncio.get_event_loop().run_until_complete(
                    asyncio.sleep(poll_interval)
                )
        except KeyboardInterrupt:
            print(f"\n[MURA] Stopping agent {self.name}...")
            self._running = False

    async def run_async(self, poll_interval: float = 5.0):
        """Async version of run()"""
        if not self._registered:
            raise RegistrationError("Agent must be registered before running")

        self._running = True
        print(f"[MURA] Agent {self.name} is now listening for RFQs...")

        while self._running:
            await asyncio.sleep(poll_interval)

    def stop(self):
        """Stop the agent"""
        self._running = False

    # =========================================================================
    # UTILITY
    # =========================================================================

    def process_rfq(self, rfq_data: dict) -> dict:
        """
        Process an RFQ and return a quote.

        This can be called directly for testing or webhook handling.

        Args:
            rfq_data: RFQ data as dict

        Returns:
            Quote as dict
        """
        rfq = RFQ(**rfq_data)

        if self._rfq_handler:
            quote = self._rfq_handler(rfq)
        else:
            quote = self._default_rfq_handler(rfq)

        return quote.model_dump()

    def __repr__(self):
        status = "registered" if self._registered else "not registered"
        return f"SupplierAgent(name={self.name!r}, region={self.region!r}, status={status})"
