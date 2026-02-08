/**
 * MURA API Client
 * Connects frontend to Next.js API routes (which proxy to FastAPI backend)
 */

// =============================================================================
// TYPES
// =============================================================================

// ZTAA (Zero Trust Agentic Access) trust levels from NANDA
export type TrustLevel = "self_declared" | "peer_attested" | "authority_verified";

export interface Certification {
  authority: string;      // e.g., "ISO", "CE", "TUV"
  certification: string;  // e.g., "ISO 9001", "CE Marking"
  cert_id: string;        // Certificate ID
}

export interface TrustProfile {
  verified: boolean;
  trust_level: TrustLevel;           // ZTAA level
  reputation_score: number;          // 0.0 - 1.0
  total_transactions: number;
  successful_transactions: number;
  dispute_rate: number;
  peer_attestations: number;         // Number of vouching agents
}

export interface Agent {
  agent_id: string;
  name: string;
  role: "SUPPLIER" | "LOGISTICS" | "COMPLIANCE" | "ORCHESTRATOR";
  description?: string;
  region: string;
  country?: string;
  capabilities?: string[];
  avg_lead_time_days?: number;
  certifications?: Certification[];
  trust?: TrustProfile;
  endpoint?: string;
}

export interface Supplier {
  name: string;
  region: string;
  max_discount_pct: number;
  catalog_items: string[];
}

export interface ProcurementRequest {
  request: string;
  budget?: number;
  deadline_days?: number;
  destination_region?: string;
  buyer_id?: string;
}

export interface ProcurementResult {
  recommendation: {
    supplier: string;
    total_cost: number;
    shipping_cost: number;
    delivery_days: number;
    compliance_status: string;
  };
  bom: Array<{ part_name: string; quantity: number }>;
  quotes: Array<{
    supplier_id: string;
    total: number;
    items: unknown[];
  }>;
  logistics: unknown;
  compliance: unknown;
  steps: Array<{
    phase: string;
    agent: string;
    message: string;
  }>;
}

export interface DiscoveryRequest {
  role?: string;
  capability?: string;
  region?: string;
  min_trust?: number;
}

// =============================================================================
// API FUNCTIONS (calling Next.js API routes)
// =============================================================================

/**
 * Health check
 */
export async function checkHealth(): Promise<{ status: string; agents_registered: number }> {
  const res = await fetch("/api/health");
  if (!res.ok) throw new Error("API not available");
  return res.json();
}

/**
 * List all registered agents
 */
export async function listAgents(): Promise<Agent[]> {
  const res = await fetch("/api/registry/agents");
  if (!res.ok) throw new Error("Failed to fetch agents");
  return res.json();
}

/**
 * Get agent details
 */
export async function getAgent(agentId: string): Promise<Agent> {
  const res = await fetch(`/api/registry/agents/${agentId}`);
  if (!res.ok) throw new Error("Agent not found");
  return res.json();
}

/**
 * Discover agents by criteria
 */
export async function discoverAgents(request: DiscoveryRequest): Promise<Agent[]> {
  const res = await fetch("/api/registry/discover", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!res.ok) throw new Error("Discovery failed");
  return res.json();
}

/**
 * List suppliers with catalog info
 */
export async function listSuppliers(): Promise<Record<string, Supplier>> {
  const res = await fetch("/api/suppliers");
  if (!res.ok) throw new Error("Failed to fetch suppliers");
  return res.json();
}

/**
 * Run full procurement workflow
 */
export async function runProcurement(request: ProcurementRequest): Promise<ProcurementResult> {
  const res = await fetch("/api/procure", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ error: "Procurement failed" }));
    throw new Error(error.error || "Procurement failed");
  }
  return res.json();
}

/**
 * Get quote from supplier
 */
export async function getQuote(
  supplierId: string,
  items: Array<{ part_name: string; quantity: number }>,
  deadlineDays?: number
): Promise<{ supplier_id: string; discount_asked: number; response: string }> {
  const res = await fetch("/api/quote", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      supplier_id: supplierId,
      items,
      deadline_days: deadlineDays,
    }),
  });
  if (!res.ok) throw new Error("Quote request failed");
  return res.json();
}

/**
 * Calculate logistics
 */
export async function calculateLogistics(
  originRegion: string,
  destinationRegion: string,
  items: unknown[],
  deadlineDays?: number
): Promise<unknown> {
  const res = await fetch("/api/logistics", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      origin_region: originRegion,
      destination_region: destinationRegion,
      items,
      deadline_days: deadlineDays,
    }),
  });
  if (!res.ok) throw new Error("Logistics calculation failed");
  return res.json();
}

/**
 * Check compliance
 */
export async function checkCompliance(
  items: Array<{ category: string; [key: string]: unknown }>,
  destinationRegion: string,
  supplierId?: string,
  transportType: string = "air"
): Promise<unknown> {
  const res = await fetch("/api/compliance", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      items,
      supplier_id: supplierId,
      destination_region: destinationRegion,
      transport_type: transportType,
    }),
  });
  if (!res.ok) throw new Error("Compliance check failed");
  return res.json();
}

/**
 * Get RL insights
 */
export async function getRLInsights(): Promise<unknown> {
  const res = await fetch("/api/insights");
  if (!res.ok) throw new Error("Failed to fetch RL insights");
  return res.json();
}

/**
 * Get demo BOM
 */
export async function getDemoBOM(): Promise<Array<{ part_name: string; quantity: number; category: string }>> {
  const res = await fetch("/api/quote");
  if (!res.ok) throw new Error("Failed to fetch demo BOM");
  return res.json();
}
