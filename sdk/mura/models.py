"""
MURA SDK Models

Data models for the MURA Supply Chain Agent Network.
Based on NANDA (MIT Media Lab) concepts: AgentFacts, Trust Profiles, A2A Protocol.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


# =============================================================================
# ENUMS
# =============================================================================

class TrustLevel(str, Enum):
    """ZTAA (Zero Trust Agentic Access) trust levels from NANDA"""
    SELF_DECLARED = "self_declared"
    PEER_ATTESTED = "peer_attested"
    AUTHORITY_VERIFIED = "authority_verified"


class AgentRole(str, Enum):
    """Types of agents in the MURA network"""
    SUPPLIER = "supplier"
    LOGISTICS = "logistics"
    COMPLIANCE = "compliance"
    BUYER = "buyer"


class QuoteStatus(str, Enum):
    """Status of a quote"""
    PENDING = "pending"
    RECEIVED = "received"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ComplianceStatus(str, Enum):
    """Compliance check result"""
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"


# =============================================================================
# AGENT FACTS (NANDA Concept)
# =============================================================================

class Certification(BaseModel):
    """A certification held by an agent"""
    authority: str = Field(..., description="Certifying authority (e.g., ISO, CE, TUV)")
    certification: str = Field(..., description="Certification name (e.g., ISO 9001)")
    cert_id: Optional[str] = Field(None, description="Certificate ID")
    valid_until: Optional[str] = Field(None, description="Expiration date")


class TrustProfile(BaseModel):
    """ZTAA Trust Profile for an agent"""
    verified: bool = Field(False, description="Platform verified")
    trust_level: TrustLevel = Field(TrustLevel.SELF_DECLARED, description="ZTAA level")
    reputation_score: float = Field(0.5, ge=0.0, le=1.0, description="0-1 reputation")
    total_transactions: int = Field(0, description="Total completed transactions")
    successful_transactions: int = Field(0, description="Successful transactions")
    dispute_rate: float = Field(0.0, description="Rate of disputes")
    peer_attestations: int = Field(0, description="Number of peer attestations")


class AgentFacts(BaseModel):
    """
    Agent's identity card in the MURA network (NANDA concept).
    Published to registry for discovery by other agents.
    """
    agent_id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Display name")
    role: AgentRole = Field(..., description="Agent role")
    description: Optional[str] = Field(None, description="What this agent does")
    capabilities: List[str] = Field(default_factory=list, description="What the agent can provide")
    region: str = Field(..., description="Operating region (EU, US, Asia)")
    country: Optional[str] = Field(None, description="Country")
    certifications: List[Certification] = Field(default_factory=list)
    trust: TrustProfile = Field(default_factory=TrustProfile)
    endpoint: Optional[str] = Field(None, description="API endpoint")


# =============================================================================
# PROCUREMENT MODELS
# =============================================================================

class BOMItem(BaseModel):
    """A single item in a Bill of Materials"""
    part_name: str = Field(..., description="Part identifier")
    quantity: int = Field(1, description="Quantity needed")
    category: Optional[str] = Field(None, description="Part category")
    description: Optional[str] = Field(None, description="Part description")
    specs: Optional[str] = Field(None, description="Technical specifications")


class BillOfMaterials(BaseModel):
    """Bill of Materials for a product"""
    product: str = Field(..., description="Product name")
    items: List[BOMItem] = Field(default_factory=list)


class QuoteItem(BaseModel):
    """A quoted item from a supplier"""
    part_name: str
    unit_price: float
    quantity: int
    total_price: float
    lead_time_days: int
    in_stock: bool = True


class Quote(BaseModel):
    """Quote from a supplier"""
    supplier_id: str
    supplier_name: str
    region: str
    items: List[QuoteItem] = Field(default_factory=list)
    total_cost: float
    currency: str = "EUR"
    lead_time_days: int
    valid_until: Optional[datetime] = None
    discount_applied: float = 0.0


class ComplianceIssue(BaseModel):
    """A compliance issue found during checking"""
    rule: str = Field(..., description="Regulation name")
    severity: str = Field(..., description="blocker, warning, or info")
    item: Optional[str] = Field(None, description="Affected item")
    description: str = Field(..., description="Issue description")
    required_action: str = Field(..., description="What needs to be done")


class ComplianceResult(BaseModel):
    """Result of compliance checking"""
    status: ComplianceStatus
    summary: str
    blockers: List[ComplianceIssue] = Field(default_factory=list)
    warnings: List[ComplianceIssue] = Field(default_factory=list)
    certifications_required: List[str] = Field(default_factory=list)


class LogisticsPlan(BaseModel):
    """Logistics/shipping plan"""
    provider: str
    origin_region: str
    destination_region: str
    estimated_days: int
    shipping_cost: float
    currency: str = "EUR"
    tracking_available: bool = True


class SupplierOption(BaseModel):
    """A scored supplier option in the recommendation"""
    supplier_id: str
    supplier_name: str
    score: float
    total_cost: float
    shipping_cost: float
    total_days: int
    compliance_passed: bool
    meets_deadline: bool


class Recommendation(BaseModel):
    """Final recommendation from procurement"""
    recommended_supplier: Optional[str]
    recommendation_reason: str
    all_options: List[SupplierOption] = Field(default_factory=list)
    total_shipping_cost: float = 0.0
    critical_path_days: int = 0
    meets_deadline: bool = False


# =============================================================================
# API REQUEST/RESPONSE
# =============================================================================

class ProcurementRequest(BaseModel):
    """Request to run procurement"""
    request: str = Field(..., description="Natural language request")
    budget: Optional[float] = Field(None, description="Budget in EUR")
    deadline_days: int = Field(7, description="Delivery deadline")
    destination_region: str = Field("EU", description="Destination region")
    buyer_id: Optional[str] = Field(None, description="Buyer ID for personalization")


class ProcurementResult(BaseModel):
    """Complete procurement result"""
    status: str
    bom: Optional[BillOfMaterials] = None
    suppliers_found: int = 0
    quotes_received: int = 0
    quotes: List[Quote] = Field(default_factory=list)
    compliance: Optional[ComplianceResult] = None
    logistics: Optional[LogisticsPlan] = None
    recommendation: Optional[Recommendation] = None
    steps: List[Dict[str, Any]] = Field(default_factory=list)


class DiscoveryRequest(BaseModel):
    """Request to discover agents"""
    role: Optional[AgentRole] = None
    capability: Optional[str] = None
    region: Optional[str] = None
    min_trust: float = Field(0.0, ge=0.0, le=1.0)


# =============================================================================
# RFQ (Request for Quote) - A2A Protocol
# =============================================================================

class RFQ(BaseModel):
    """Request for Quote (A2A Protocol message)"""
    rfq_id: str
    buyer_id: str
    items: List[BOMItem]
    deadline_days: Optional[int] = None
    budget: Optional[float] = None
    destination_region: str = "EU"
    timestamp: datetime = Field(default_factory=datetime.now)
