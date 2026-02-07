from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid

class MessageType(str, Enum):
    RFQ = "rfq"
    QUOTATION = "quotation"
    NEGOTIATE = "negotiate"
    COUNTER = "counter"
    ACCEPT = "accept"
    REJECT = "reject"
    LOGISTICS_REQUEST = "logistics_request"
    LOGISTICS_PLAN = "logistics_plan"   
    COMPLIANCE_CHECK = "compliance_check"
    COMPLIANCE_RESULT = "compliance_result"
    DISRUPTION_ALERT = "disruption_alert"
    BOM_GENERATED = "bom_generated"
    EXECUTION_PLAN = "execution_plan"
    STATUS_UPDATE = "status_update"

class AgentRole(str, Enum):
    BUYER = "buyer"
    SUPPLIER = "supplier"
    LOGISTICS = "logistics"
    COMPLIANCE = "compliance"
    ORCHESTRATOR = "orchestrator"

class Certification(BaseModel):
    authority: str
    certification: str 
    cert_id: str = ""
    valid_until: str = ""

class TrustProfile(BaseModel):
    verified: bool = False
    reputation_score: float = Field(default=0.5, ge=0.0, le=1.0)
    total_transactions: int = 0
    dispute_rate: float = 0.0

class AgentFacts(BaseModel):
    agent_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str
    role: AgentRole
    description: str = ""
    capabilities: list[str] = []
    region: str = ""
    country: str = ""
    currency: str = "EUR"
    avg_lead_time_days: int = 7
    certifications: list[Certification] = []
    trust: TrustProfile = TrustProfile()
    endpoint: str = ""

class A2AMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:12])
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    from_agent: str
    to_agent: str
    message_type: MessageType
    payload: dict = {}
    in_reply_to: Optional[str] = None

class BOMItem(BaseModel):
    part_name: str
    quantity: int
    specs: str = ""
    category: str = ""

class BillOfMaterials(BaseModel):
    product: str
    intent: str
    budget: float = 0.0
    currency: str = "EUR"
    deadline: str = ""
    delivery_location: str = ""
    items: list[BOMItem] = []

class QuoteItem(BaseModel):
    part_name: str
    unit_price: float
    quantity: int
    total_price: float = 0.0
    lead_time_days: int = 0
    in_stock: bool = True

class Quote(BaseModel):
    supplier_name: str
    items: list[QuoteItem] = []
    total_cost: float = 0.0
    currency: str = "EUR"
    shipping_origin: str = ""

class LogisticsPlan(BaseModel):
    provider: str
    routes: list[dict] = []
    total_cost: float = 0.0
    estimated_arrival: str = ""

class ComplianceResult(BaseModel):
    overall_status: str = "PASS"
    checks: list[dict] = []
    warnings: list[str] = []

class ExecutionPlan(BaseModel):
    status: str = "READY"
    intent: str = ""
    total_cost: float = 0.0
    budget: float = 0.0
    orders: list[dict] = []
    logistics: dict = {}
    compliance: dict = {}
    agents_involved: int = 0
    messages_exchanged: int = 0