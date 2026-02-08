"""
MURA SDK - Supply Chain Agent Coordination Network

SDK for platforms and suppliers to integrate with the MURA network.

For Platforms (like Asklio, Comena):
    from mura import MuraClient

    client = MuraClient(api_key="mura_live_xxx")
    result = client.procure("500 temperature sensors", budget=5000)

For Suppliers:
    from mura import SupplierAgent

    agent = SupplierAgent(
        name="Acme Electronics",
        capabilities=["electronics", "sensors"],
        region="EU"
    )
    agent.register()
    agent.run()
"""

from .client import (
    MuraClient,
    RegistryClient,
    QuoteClient,
    ComplianceClient,
    LogisticsClient,
)
from .supplier import SupplierAgent
from .models import (
    # Enums
    TrustLevel,
    AgentRole,
    QuoteStatus,
    ComplianceStatus,
    # Agent Facts
    Certification,
    TrustProfile,
    AgentFacts,
    # Procurement
    BOMItem,
    BillOfMaterials,
    QuoteItem,
    Quote,
    ComplianceIssue,
    ComplianceResult,
    LogisticsPlan,
    SupplierOption,
    Recommendation,
    # Requests/Responses
    ProcurementRequest,
    ProcurementResult,
    DiscoveryRequest,
    RFQ,
)
from .exceptions import (
    MuraError,
    MuraAPIError,
    MuraConnectionError,
    MuraAuthenticationError,
    MuraValidationError,
    MuraTimeoutError,
    NoSuppliersFoundError,
    ComplianceError,
    QuoteError,
    RegistrationError,
)

__version__ = "0.1.0"
__all__ = [
    # Main clients
    "MuraClient",
    "SupplierAgent",
    # Sub-clients
    "RegistryClient",
    "QuoteClient",
    "ComplianceClient",
    "LogisticsClient",
    # Enums
    "TrustLevel",
    "AgentRole",
    "QuoteStatus",
    "ComplianceStatus",
    # Models
    "Certification",
    "TrustProfile",
    "AgentFacts",
    "BOMItem",
    "BillOfMaterials",
    "QuoteItem",
    "Quote",
    "ComplianceIssue",
    "ComplianceResult",
    "LogisticsPlan",
    "SupplierOption",
    "Recommendation",
    "ProcurementRequest",
    "ProcurementResult",
    "DiscoveryRequest",
    "RFQ",
    # Exceptions
    "MuraError",
    "MuraAPIError",
    "MuraConnectionError",
    "MuraAuthenticationError",
    "MuraValidationError",
    "MuraTimeoutError",
    "NoSuppliersFoundError",
    "ComplianceError",
    "QuoteError",
    "RegistrationError",
]
