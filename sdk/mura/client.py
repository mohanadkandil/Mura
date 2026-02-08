"""
MURA Client

SDK for platforms (like Asklio, Comena) to use MURA as procurement infrastructure.

Example:
    from mura import MuraClient

    client = MuraClient(api_key="mura_live_xxx")
    result = client.procure("500 temperature sensors", budget=5000, region="EU")
"""

import httpx
from typing import Optional, List, AsyncGenerator
import json

from .models import (
    ProcurementRequest,
    ProcurementResult,
    DiscoveryRequest,
    AgentFacts,
    Quote,
    ComplianceResult,
    LogisticsPlan,
    AgentRole,
)
from .exceptions import (
    MuraAPIError,
    MuraConnectionError,
    MuraAuthenticationError,
    MuraTimeoutError,
    NoSuppliersFoundError,
)


class MuraClient:
    """
    MURA Client for platforms to use supply chain infrastructure.

    This client allows platforms like Asklio, Comena, etc. to:
    - Run procurement workflows (discover, quote, comply, ship)
    - Discover agents in the network
    - Get quotes from suppliers
    - Check compliance
    - Plan logistics

    Example:
        client = MuraClient(api_key="mura_live_xxx")

        # Simple procurement
        result = client.procure("Build me a racing drone")

        # With options
        result = client.procure(
            "500 temperature sensors",
            budget=5000,
            deadline_days=14,
            destination_region="EU"
        )

        print(result.recommendation.recommended_supplier)
    """

    DEFAULT_BASE_URL = "https://mura-production.up.railway.app"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 120.0,
    ):
        """
        Initialize MURA client.

        Args:
            api_key: Your MURA API key (get one at https://mura.dev)
            base_url: MURA API base URL (default: production)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout

        # HTTP client
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers=self._build_headers(),
        )

        # Async client (lazy initialized)
        self._async_client: Optional[httpx.AsyncClient] = None

        # Sub-clients
        self.registry = RegistryClient(self)
        self.quotes = QuoteClient(self)
        self.compliance = ComplianceClient(self)
        self.logistics = LogisticsClient(self)

    def _build_headers(self) -> dict:
        """Build request headers"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "mura-sdk/0.1.0",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _get_async_client(self) -> httpx.AsyncClient:
        """Get or create async client"""
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers=self._build_headers(),
            )
        return self._async_client

    def _handle_response(self, response: httpx.Response) -> dict:
        """Handle API response"""
        if response.status_code == 401:
            raise MuraAuthenticationError("Invalid API key")
        if response.status_code == 404:
            raise MuraAPIError("Resource not found", status_code=404)
        if response.status_code >= 400:
            try:
                error_data = response.json()
                message = error_data.get("detail", "API error")
            except:
                message = response.text
            raise MuraAPIError(message, status_code=response.status_code)

        return response.json()

    # =========================================================================
    # MAIN PROCUREMENT
    # =========================================================================

    def procure(
        self,
        request: str,
        budget: Optional[float] = None,
        deadline_days: int = 7,
        destination_region: str = "EU",
        buyer_id: Optional[str] = None,
    ) -> ProcurementResult:
        """
        Run full procurement workflow.

        This is the main method - it handles everything:
        1. Generates BOM from your request
        2. Discovers relevant suppliers
        3. Gets quotes in parallel
        4. Checks compliance
        5. Plans logistics
        6. Returns recommendation

        Args:
            request: Natural language request (e.g., "500 temperature sensors")
            budget: Optional budget constraint in EUR
            deadline_days: Delivery deadline (default: 7 days)
            destination_region: Where to ship (EU, US, Asia)
            buyer_id: Optional buyer ID for personalization

        Returns:
            ProcurementResult with quotes, compliance, logistics, and recommendation

        Example:
            result = client.procure(
                "Build me a racing drone",
                budget=1000,
                deadline_days=14,
                destination_region="EU"
            )

            print(f"Recommended: {result.recommendation.recommended_supplier}")
            print(f"Best price: €{result.recommendation.all_options[0].total_cost}")
        """
        try:
            response = self._client.post(
                "/procure",
                json={
                    "request": request,
                    "budget": budget,
                    "deadline_days": deadline_days,
                    "destination_region": destination_region,
                    "buyer_id": buyer_id,
                }
            )
            data = self._handle_response(response)
            return ProcurementResult(**data)

        except httpx.ConnectError:
            raise MuraConnectionError(f"Failed to connect to MURA at {self.base_url}")
        except httpx.TimeoutException:
            raise MuraTimeoutError("Procurement request timed out")

    async def procure_async(
        self,
        request: str,
        budget: Optional[float] = None,
        deadline_days: int = 7,
        destination_region: str = "EU",
        buyer_id: Optional[str] = None,
    ) -> ProcurementResult:
        """Async version of procure()"""
        client = self._get_async_client()

        try:
            response = await client.post(
                "/procure",
                json={
                    "request": request,
                    "budget": budget,
                    "deadline_days": deadline_days,
                    "destination_region": destination_region,
                    "buyer_id": buyer_id,
                }
            )
            data = self._handle_response(response)
            return ProcurementResult(**data)

        except httpx.ConnectError:
            raise MuraConnectionError(f"Failed to connect to MURA at {self.base_url}")
        except httpx.TimeoutException:
            raise MuraTimeoutError("Procurement request timed out")

    async def procure_stream(
        self,
        request: str,
        budget: Optional[float] = None,
        deadline_days: int = 7,
        destination_region: str = "EU",
        buyer_id: Optional[str] = None,
    ) -> AsyncGenerator[dict, None]:
        """
        Stream procurement with real-time updates.

        Yields step-by-step updates as the procurement progresses.
        Useful for showing live progress in UI.

        Example:
            async for step in client.procure_stream("500 sensors"):
                print(f"{step['agent']}: {step['message']}")
        """
        client = self._get_async_client()

        async with client.stream(
            "POST",
            "/procure/stream",
            json={
                "request": request,
                "budget": budget,
                "deadline_days": deadline_days,
                "destination_region": destination_region,
                "buyer_id": buyer_id,
            }
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        yield data
                    except json.JSONDecodeError:
                        continue

    # =========================================================================
    # HEALTH CHECK
    # =========================================================================

    def health(self) -> dict:
        """Check if MURA network is healthy"""
        try:
            response = self._client.get("/health")
            return self._handle_response(response)
        except httpx.ConnectError:
            raise MuraConnectionError(f"Failed to connect to MURA at {self.base_url}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._client.close()
        if self._async_client:
            # Note: async client should be closed in async context
            pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._client.close()
        if self._async_client:
            await self._async_client.aclose()


# =============================================================================
# SUB-CLIENTS
# =============================================================================

class RegistryClient:
    """Client for agent registry operations"""

    def __init__(self, client: MuraClient):
        self._client = client

    def list_agents(self) -> List[AgentFacts]:
        """List all agents in the registry"""
        response = self._client._client.get("/registry/agents")
        data = self._client._handle_response(response)
        return [AgentFacts(**agent) for agent in data]

    def get_agent(self, agent_id: str) -> AgentFacts:
        """Get a specific agent by ID"""
        response = self._client._client.get(f"/registry/agents/{agent_id}")
        data = self._client._handle_response(response)
        return AgentFacts(**data)

    def discover(
        self,
        role: Optional[AgentRole] = None,
        capability: Optional[str] = None,
        region: Optional[str] = None,
        min_trust: float = 0.0,
    ) -> List[AgentFacts]:
        """
        Discover agents matching criteria.

        Args:
            role: Filter by role (supplier, logistics, compliance)
            capability: Filter by capability (e.g., "electronics", "PCB")
            region: Filter by region (EU, US, Asia)
            min_trust: Minimum trust score (0-1)

        Returns:
            List of matching agents

        Example:
            suppliers = client.registry.discover(
                role=AgentRole.SUPPLIER,
                capability="electronics",
                region="EU",
                min_trust=0.8
            )
        """
        response = self._client._client.post(
            "/registry/discover",
            json={
                "role": role.value if role else None,
                "capability": capability,
                "region": region,
                "min_trust": min_trust,
            }
        )
        data = self._client._handle_response(response)
        return [AgentFacts(**agent) for agent in data]


class QuoteClient:
    """Client for quote operations"""

    def __init__(self, client: MuraClient):
        self._client = client

    def get_quote(
        self,
        supplier_id: str,
        items: List[dict],
        deadline_days: Optional[int] = None,
    ) -> dict:
        """
        Get a quote from a specific supplier.

        Args:
            supplier_id: Supplier agent ID
            items: List of items to quote [{"part_name": "x", "quantity": 1}]
            deadline_days: Optional deadline constraint

        Returns:
            Quote response from supplier
        """
        response = self._client._client.post(
            "/quote",
            json={
                "supplier_id": supplier_id,
                "items": items,
                "deadline_days": deadline_days,
            }
        )
        return self._client._handle_response(response)


class ComplianceClient:
    """Client for compliance checking"""

    def __init__(self, client: MuraClient):
        self._client = client

    def check(
        self,
        items: List[dict],
        destination_region: str = "EU",
        supplier_id: Optional[str] = None,
        transport_type: str = "air",
    ) -> dict:
        """
        Check compliance for items.

        Args:
            items: Items to check [{"part_name": "x", "category": "electronics"}]
            destination_region: Destination (EU, US, Asia)
            supplier_id: Optional supplier for cert check
            transport_type: Shipping method (air, sea, ground)

        Returns:
            Compliance assessment
        """
        response = self._client._client.post(
            "/compliance",
            json={
                "items": items,
                "destination_region": destination_region,
                "supplier_id": supplier_id,
                "transport_type": transport_type,
            }
        )
        return self._client._handle_response(response)

    def get_rules(self) -> dict:
        """Get all compliance rules"""
        response = self._client._client.get("/compliance/rules")
        return self._client._handle_response(response)


class LogisticsClient:
    """Client for logistics operations"""

    def __init__(self, client: MuraClient):
        self._client = client

    def plan(
        self,
        origin_region: str,
        destination_region: str,
        items: List[dict],
        deadline_days: Optional[int] = None,
    ) -> dict:
        """
        Plan logistics for shipment.

        Args:
            origin_region: Origin region
            destination_region: Destination region
            items: Items to ship
            deadline_days: Optional deadline

        Returns:
            Logistics plan with carrier options
        """
        response = self._client._client.post(
            "/logistics",
            json={
                "origin_region": origin_region,
                "destination_region": destination_region,
                "items": items,
                "deadline_days": deadline_days,
            }
        )
        return self._client._handle_response(response)

    def get_providers(self) -> dict:
        """Get all logistics providers"""
        response = self._client._client.get("/logistics/providers")
        return self._client._handle_response(response)
