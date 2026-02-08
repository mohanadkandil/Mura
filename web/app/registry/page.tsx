"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import {
  Search,
  Filter,
  Package,
  Truck,
  Shield,
  Brain,
  Globe,
  Star,
  Circle,
  Plus,
  ArrowLeft,
  Sparkles,
  Check,
  Clock,
  Zap,
  Loader2,
  AlertCircle,
  RefreshCw,
  Award,
  Users,
  ShieldCheck,
  BadgeCheck,
  FileCheck
} from "lucide-react";
import { listAgents, Agent, TrustLevel, Certification } from "../lib/api";

type AgentType = "orchestrator" | "supplier" | "logistics" | "compliance";

interface DisplayAgent {
  id: string;
  name: string;
  type: AgentType;
  description: string;
  capabilities: string[];
  regions: string[];
  country: string;
  status: "online" | "offline" | "busy";
  // NANDA AgentFacts
  certifications: Certification[];
  // ZTAA Trust Profile
  trustLevel: TrustLevel;
  reputationScore: number;
  totalTransactions: number;
  successfulTransactions: number;
  disputeRate: number;
  peerAttestations: number;
  verified: boolean;
  // Display helpers
  responseTime: string;
}

// Map backend role to frontend type
function roleToType(role: string): AgentType {
  switch (role.toUpperCase()) {
    case "SUPPLIER": return "supplier";
    case "LOGISTICS": return "logistics";
    case "COMPLIANCE": return "compliance";
    case "ORCHESTRATOR": return "orchestrator";
    default: return "supplier";
  }
}

// Convert backend Agent to display format with full NANDA data
function agentToDisplay(agent: Agent): DisplayAgent {
  return {
    id: agent.agent_id,
    name: agent.name,
    type: roleToType(agent.role),
    description: agent.description || `${agent.role} agent for ${agent.region}`,
    capabilities: agent.capabilities || [],
    regions: [agent.region],
    country: agent.country || "",
    status: "online",
    // NANDA AgentFacts
    certifications: agent.certifications || [],
    // ZTAA Trust Profile
    trustLevel: agent.trust?.trust_level || "self_declared",
    reputationScore: agent.trust?.reputation_score || 0.5,
    totalTransactions: agent.trust?.total_transactions || 0,
    successfulTransactions: agent.trust?.successful_transactions || 0,
    disputeRate: agent.trust?.dispute_rate || 0,
    peerAttestations: agent.trust?.peer_attestations || 0,
    verified: agent.trust?.verified || false,
    responseTime: agent.avg_lead_time_days ? `${agent.avg_lead_time_days}d` : "< 5s",
  };
}

// ZTAA Trust Level display config
const trustLevelConfig: Record<TrustLevel, { label: string; color: string; icon: typeof ShieldCheck; description: string }> = {
  self_declared: {
    label: "Self-Declared",
    color: "#94a3b8",
    icon: Shield,
    description: "Agent claims capabilities (unverified)"
  },
  peer_attested: {
    label: "Peer-Attested",
    color: "#f59e0b",
    icon: Users,
    description: "Vouched by other agents in the network"
  },
  authority_verified: {
    label: "Authority-Verified",
    color: "#22c55e",
    icon: BadgeCheck,
    description: "Certified by official authority"
  }
};

const typeConfig = {
  orchestrator: { icon: Brain, color: "#f582ae", label: "Orchestrator" },
  supplier: { icon: Package, color: "#8bd3dd", label: "Supplier" },
  logistics: { icon: Truck, color: "#f59e0b", label: "Logistics" },
  compliance: { icon: Shield, color: "#f3d2c1", label: "Compliance" }
};

const statusConfig = {
  online: { color: "#22c55e", label: "Online" },
  offline: { color: "#94a3b8", label: "Offline" },
  busy: { color: "#f59e0b", label: "Busy" }
};

export default function RegistryPage() {
  const [search, setSearch] = useState("");
  const [filterType, setFilterType] = useState<AgentType | "all">("all");
  const [selectedAgent, setSelectedAgent] = useState<DisplayAgent | null>(null);
  const [agents, setAgents] = useState<DisplayAgent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch agents from API
  useEffect(() => {
    async function fetchAgents() {
      setLoading(true);
      setError(null);
      try {
        const data = await listAgents();
        setAgents(data.map(agentToDisplay));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch agents");
      } finally {
        setLoading(false);
      }
    }
    fetchAgents();
  }, []);

  const filteredAgents = agents.filter(agent => {
    const matchesSearch = agent.name.toLowerCase().includes(search.toLowerCase()) ||
      agent.description.toLowerCase().includes(search.toLowerCase()) ||
      agent.capabilities.some(c => c.toLowerCase().includes(search.toLowerCase()));
    const matchesType = filterType === "all" || agent.type === filterType;
    return matchesSearch && matchesType;
  });

  const agentCounts = {
    all: agents.length,
    supplier: agents.filter(a => a.type === "supplier").length,
    logistics: agents.filter(a => a.type === "logistics").length,
    compliance: agents.filter(a => a.type === "compliance").length,
    orchestrator: agents.filter(a => a.type === "orchestrator").length,
  };

  const handleRetry = () => {
    setLoading(true);
    setError(null);
    listAgents()
      .then(data => setAgents(data.map(agentToDisplay)))
      .catch(err => setError(err instanceof Error ? err.message : "Failed to fetch agents"))
      .finally(() => setLoading(false));
  };

  return (
    <div className="min-h-screen" style={{ background: '#fef6e4' }}>
      {/* Header */}
      <header style={{ borderBottom: '2px solid #001858' }}>
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="flex items-center gap-2 text-sm font-medium hover:opacity-70 transition-opacity" style={{ color: '#001858' }}>
              <ArrowLeft className="w-4 h-4" />
              Back
            </Link>
            <div className="w-px h-6" style={{ background: '#001858' }} />
            <div className="flex items-center gap-3">
              <motion.div
                className="w-10 h-10 rounded-xl flex items-center justify-center"
                style={{
                  background: '#8bd3dd',
                  border: '2px solid #001858',
                  boxShadow: '2px 2px 0 #001858',
                }}
              >
                <Globe className="w-5 h-5" style={{ color: '#001858' }} />
              </motion.div>
              <div>
                <h1 className="text-xl font-bold" style={{ color: '#001858' }}>Agent Registry</h1>
                <p className="text-xs" style={{ color: '#172c66' }}>
                  {loading ? "Loading..." : `${agents.length} agents published`}
                </p>
              </div>
            </div>
          </div>

          <motion.button
            className="flex items-center gap-2 px-4 py-2 rounded-xl font-semibold text-sm"
            style={{
              background: '#f582ae',
              color: '#001858',
              border: '2px solid #001858',
              boxShadow: '3px 3px 0 #001858',
            }}
            whileHover={{ x: -2, y: -2, boxShadow: '5px 5px 0 #001858' }}
            whileTap={{ x: 1, y: 1, boxShadow: '2px 2px 0 #001858' }}
          >
            <Plus className="w-4 h-4" />
            Register Agent
          </motion.button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Search and Filter */}
        <div className="flex gap-4 mb-8">
          <div
            className="flex-1 flex items-center gap-3 px-4 py-3 rounded-xl"
            style={{
              background: '#fff',
              border: '2px solid #001858',
            }}
          >
            <Search className="w-5 h-5" style={{ color: '#172c66' }} />
            <input
              type="text"
              placeholder="Search agents by name, capability, or description..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="flex-1 bg-transparent focus:outline-none text-sm"
              style={{ color: '#001858' }}
            />
          </div>
        </div>

        {/* Type Filter Tabs */}
        <div className="flex gap-2 mb-8 overflow-x-auto pb-2">
          {(["all", "supplier", "logistics", "compliance", "orchestrator"] as const).map((type) => {
            const isActive = filterType === type;
            const config = type === "all" ? null : typeConfig[type];
            const Icon = config?.icon || Filter;

            return (
              <button
                key={type}
                onClick={() => setFilterType(type)}
                className="flex items-center gap-2 px-4 py-2 rounded-xl font-medium text-sm whitespace-nowrap transition-all"
                style={{
                  background: isActive ? (config?.color || '#f582ae') : '#fff',
                  color: '#001858',
                  border: '2px solid #001858',
                  boxShadow: isActive ? '3px 3px 0 #001858' : 'none',
                }}
              >
                <Icon className="w-4 h-4" />
                {type === "all" ? "All Agents" : config?.label}
                <span
                  className="px-1.5 py-0.5 rounded-full text-xs"
                  style={{
                    background: isActive ? '#fff' : '#f3d2c1',
                    color: '#001858'
                  }}
                >
                  {agentCounts[type]}
                </span>
              </button>
            );
          })}
        </div>

        {/* Loading State */}
        {loading && (
          <div className="text-center py-16">
            <Loader2 className="w-12 h-12 mx-auto mb-4 animate-spin" style={{ color: '#f582ae' }} />
            <p className="font-medium" style={{ color: '#001858' }}>Loading agents...</p>
            <p className="text-sm mt-1" style={{ color: '#172c66', opacity: 0.6 }}>Connecting to registry</p>
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div className="text-center py-16">
            <div
              className="inline-flex items-center justify-center w-16 h-16 rounded-full mb-4"
              style={{ background: '#f3d2c1', border: '2px solid #001858' }}
            >
              <AlertCircle className="w-8 h-8" style={{ color: '#001858' }} />
            </div>
            <p className="font-medium mb-2" style={{ color: '#001858' }}>{error}</p>
            <p className="text-sm mb-6" style={{ color: '#172c66', opacity: 0.6 }}>Make sure the backend is running</p>
            <motion.button
              onClick={handleRetry}
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl font-semibold"
              style={{
                background: '#f582ae',
                color: '#001858',
                border: '2px solid #001858',
                boxShadow: '3px 3px 0 #001858',
              }}
              whileHover={{ x: -2, y: -2, boxShadow: '5px 5px 0 #001858' }}
              whileTap={{ x: 1, y: 1, boxShadow: '2px 2px 0 #001858' }}
            >
              <RefreshCw className="w-4 h-4" />
              Retry
            </motion.button>
          </div>
        )}

        {/* Agents Grid */}
        {!loading && !error && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <AnimatePresence mode="popLayout">
              {filteredAgents.map((agent, index) => {
                const config = typeConfig[agent.type];
                const status = statusConfig[agent.status];
                const Icon = config.icon;

                return (
                  <motion.div
                    key={agent.id}
                    layout
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    transition={{ delay: index * 0.05 }}
                    className="rounded-2xl p-5 cursor-pointer transition-all hover:-translate-x-1 hover:-translate-y-1"
                    style={{
                      background: '#fff',
                      border: '2px solid #001858',
                      boxShadow: '4px 4px 0 #001858',
                    }}
                    onClick={() => setSelectedAgent(agent)}
                    whileHover={{ boxShadow: '6px 6px 0 #001858' }}
                  >
                    {/* Header */}
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div
                          className="w-12 h-12 rounded-xl flex items-center justify-center"
                          style={{
                            background: config.color,
                            border: '2px solid #001858',
                          }}
                        >
                          <Icon className="w-6 h-6" style={{ color: '#001858' }} />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="font-bold" style={{ color: '#001858' }}>{agent.name}</h3>
                          </div>
                          <div className="flex items-center gap-1 mt-1">
                            <span
                              className="text-xs px-2 py-0.5 rounded-full"
                              style={{ background: config.color, color: '#001858' }}
                            >
                              {config.label}
                            </span>
                            {agent.country && (
                              <span className="text-xs" style={{ color: '#172c66' }}>
                                {agent.country}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        <Circle
                          className="w-2 h-2"
                          style={{ fill: status.color, color: status.color }}
                        />
                        <span className="text-xs" style={{ color: status.color }}>{status.label}</span>
                      </div>
                    </div>

                    {/* ZTAA Trust Level Badge */}
                    {(() => {
                      const trustConfig = trustLevelConfig[agent.trustLevel];
                      const TrustIcon = trustConfig.icon;
                      return (
                        <div
                          className="flex items-center gap-2 px-3 py-2 rounded-lg mb-3"
                          style={{
                            background: `${trustConfig.color}15`,
                            border: `1px solid ${trustConfig.color}`,
                          }}
                        >
                          <TrustIcon className="w-4 h-4" style={{ color: trustConfig.color }} />
                          <div className="flex-1">
                            <span className="text-xs font-bold" style={{ color: trustConfig.color }}>
                              {trustConfig.label}
                            </span>
                            {agent.peerAttestations > 0 && (
                              <span className="text-xs ml-2" style={{ color: '#172c66' }}>
                                ({agent.peerAttestations} attestations)
                              </span>
                            )}
                          </div>
                          <span className="text-xs font-bold" style={{ color: '#001858' }}>
                            {(agent.reputationScore * 100).toFixed(0)}%
                          </span>
                        </div>
                      );
                    })()}

                    {/* Certifications */}
                    {agent.certifications.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-3">
                        {agent.certifications.slice(0, 3).map((cert, i) => (
                          <span
                            key={i}
                            className="flex items-center gap-1 text-xs px-2 py-1 rounded-lg"
                            style={{ background: '#22c55e20', color: '#166534', border: '1px solid #22c55e' }}
                          >
                            <FileCheck className="w-3 h-3" />
                            {cert.certification}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Capabilities */}
                    <div className="flex flex-wrap gap-1 mb-3">
                      {agent.capabilities.slice(0, 3).map((cap, i) => (
                        <span
                          key={i}
                          className="text-xs px-2 py-1 rounded-lg"
                          style={{ background: '#fef6e4', color: '#001858', border: '1px solid #001858' }}
                        >
                          {cap}
                        </span>
                      ))}
                      {agent.capabilities.length > 3 && (
                        <span className="text-xs px-2 py-1" style={{ color: '#172c66' }}>
                          +{agent.capabilities.length - 3} more
                        </span>
                      )}
                    </div>

                    {/* Stats Row */}
                    <div className="flex items-center justify-between pt-3" style={{ borderTop: '1px solid #e5e5e5' }}>
                      <div className="flex items-center gap-1" title="Successful transactions">
                        <Zap className="w-3 h-3" style={{ color: '#22c55e' }} />
                        <span className="text-xs font-semibold" style={{ color: '#001858' }}>
                          {agent.successfulTransactions}/{agent.totalTransactions}
                        </span>
                      </div>
                      <div className="flex items-center gap-1 text-xs" title="Dispute rate" style={{ color: agent.disputeRate > 0.05 ? '#ef4444' : '#172c66' }}>
                        <AlertCircle className="w-3 h-3" />
                        {(agent.disputeRate * 100).toFixed(1)}%
                      </div>
                      <div className="flex items-center gap-1 text-xs" style={{ color: '#172c66' }}>
                        <Clock className="w-3 h-3" />
                        {agent.responseTime}
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>
        )}

        {!loading && !error && filteredAgents.length === 0 && (
          <div className="text-center py-16">
            <Package className="w-12 h-12 mx-auto mb-4" style={{ color: '#172c66', opacity: 0.3 }} />
            <p className="font-medium" style={{ color: '#172c66' }}>No agents found</p>
            <p className="text-sm mt-1" style={{ color: '#172c66', opacity: 0.6 }}>Try adjusting your search or filters</p>
          </div>
        )}
      </main>

      {/* Agent Detail Modal */}
      <AnimatePresence>
        {selectedAgent && (
          <motion.div
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div
              className="absolute inset-0"
              style={{ background: 'rgba(0, 24, 88, 0.6)' }}
              onClick={() => setSelectedAgent(null)}
            />
            <motion.div
              className="relative w-full max-w-lg rounded-2xl p-6 max-h-[80vh] overflow-y-auto"
              style={{
                background: '#fef6e4',
                border: '3px solid #001858',
                boxShadow: '8px 8px 0 #001858',
              }}
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
            >
              {/* Close */}
              <button
                onClick={() => setSelectedAgent(null)}
                className="absolute top-4 right-4 w-8 h-8 rounded-lg flex items-center justify-center"
                style={{ background: '#f3d2c1', border: '2px solid #001858' }}
              >
                <span style={{ color: '#001858' }}>×</span>
              </button>

              {/* Header */}
              <div className="flex items-center gap-4 mb-6">
                <div
                  className="w-16 h-16 rounded-xl flex items-center justify-center"
                  style={{
                    background: typeConfig[selectedAgent.type].color,
                    border: '3px solid #001858',
                    boxShadow: '3px 3px 0 #001858',
                  }}
                >
                  {(() => {
                    const Icon = typeConfig[selectedAgent.type].icon;
                    return <Icon className="w-8 h-8" style={{ color: '#001858' }} />;
                  })()}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-xl font-bold" style={{ color: '#001858' }}>{selectedAgent.name}</h3>
                    {selectedAgent.verified && (
                      <span className="text-xs px-2 py-0.5 rounded-full flex items-center gap-1" style={{ background: '#22c55e', color: '#fff' }}>
                        <Check className="w-3 h-3" /> Verified
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs px-2 py-0.5 rounded-full" style={{ background: typeConfig[selectedAgent.type].color, color: '#001858' }}>
                      {typeConfig[selectedAgent.type].label}
                    </span>
                    <span className="flex items-center gap-1 text-xs" style={{ color: statusConfig[selectedAgent.status].color }}>
                      <Circle className="w-2 h-2" style={{ fill: 'currentColor' }} />
                      {statusConfig[selectedAgent.status].label}
                    </span>
                  </div>
                </div>
              </div>

              {/* Description */}
              <p className="text-sm mb-4" style={{ color: '#172c66' }}>{selectedAgent.description}</p>

              {/* ZTAA Trust Level - Prominent Display */}
              {(() => {
                const trustConfig = trustLevelConfig[selectedAgent.trustLevel];
                const TrustIcon = trustConfig.icon;
                return (
                  <div
                    className="rounded-xl p-4 mb-4"
                    style={{
                      background: `${trustConfig.color}10`,
                      border: `2px solid ${trustConfig.color}`,
                    }}
                  >
                    <div className="flex items-center gap-3 mb-2">
                      <div
                        className="w-10 h-10 rounded-full flex items-center justify-center"
                        style={{ background: trustConfig.color }}
                      >
                        <TrustIcon className="w-5 h-5" style={{ color: '#fff' }} />
                      </div>
                      <div>
                        <h4 className="font-bold" style={{ color: trustConfig.color }}>
                          {trustConfig.label}
                        </h4>
                        <p className="text-xs" style={{ color: '#172c66' }}>
                          {trustConfig.description}
                        </p>
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-2 mt-3">
                      <div className="text-center">
                        <span className="text-lg font-bold" style={{ color: '#001858' }}>
                          {(selectedAgent.reputationScore * 100).toFixed(0)}%
                        </span>
                        <p className="text-xs" style={{ color: '#172c66' }}>Reputation</p>
                      </div>
                      <div className="text-center">
                        <span className="text-lg font-bold" style={{ color: '#001858' }}>
                          {selectedAgent.peerAttestations}
                        </span>
                        <p className="text-xs" style={{ color: '#172c66' }}>Attestations</p>
                      </div>
                      <div className="text-center">
                        <span className="text-lg font-bold" style={{ color: selectedAgent.disputeRate > 0.05 ? '#ef4444' : '#22c55e' }}>
                          {(selectedAgent.disputeRate * 100).toFixed(1)}%
                        </span>
                        <p className="text-xs" style={{ color: '#172c66' }}>Disputes</p>
                      </div>
                    </div>
                  </div>
                );
              })()}

              {/* Transaction Stats */}
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="rounded-xl p-3" style={{ background: '#fff', border: '2px solid #001858' }}>
                  <div className="flex items-center gap-2 mb-1">
                    <Zap className="w-4 h-4" style={{ color: '#22c55e' }} />
                    <span className="text-lg font-bold" style={{ color: '#001858' }}>
                      {selectedAgent.successfulTransactions}
                    </span>
                  </div>
                  <p className="text-xs" style={{ color: '#172c66' }}>Successful Transactions</p>
                </div>
                <div className="rounded-xl p-3" style={{ background: '#fff', border: '2px solid #001858' }}>
                  <div className="flex items-center gap-2 mb-1">
                    <Clock className="w-4 h-4" style={{ color: '#f59e0b' }} />
                    <span className="text-lg font-bold" style={{ color: '#001858' }}>
                      {selectedAgent.responseTime}
                    </span>
                  </div>
                  <p className="text-xs" style={{ color: '#172c66' }}>Avg Lead Time</p>
                </div>
              </div>

              {/* Certifications */}
              {selectedAgent.certifications.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-bold mb-3 flex items-center gap-2" style={{ color: '#001858' }}>
                    <Award className="w-4 h-4" />
                    Certifications
                  </h4>
                  <div className="space-y-2">
                    {selectedAgent.certifications.map((cert, i) => (
                      <div
                        key={i}
                        className="flex items-center gap-3 p-2 rounded-lg"
                        style={{ background: '#22c55e15', border: '1px solid #22c55e' }}
                      >
                        <FileCheck className="w-4 h-4" style={{ color: '#22c55e' }} />
                        <div className="flex-1">
                          <span className="text-sm font-medium" style={{ color: '#001858' }}>
                            {cert.certification}
                          </span>
                          <span className="text-xs ml-2" style={{ color: '#172c66' }}>
                            by {cert.authority}
                          </span>
                        </div>
                        {cert.cert_id && (
                          <span className="text-xs" style={{ color: '#172c66' }}>
                            #{cert.cert_id}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Capabilities */}
              {selectedAgent.capabilities.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-bold mb-3" style={{ color: '#001858' }}>Capabilities</h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedAgent.capabilities.map((cap, i) => (
                      <span
                        key={i}
                        className="text-xs px-3 py-1.5 rounded-lg"
                        style={{ background: '#fff', color: '#001858', border: '2px solid #001858' }}
                      >
                        {cap}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Regions */}
              <div className="mb-4">
                <h4 className="text-sm font-bold mb-3" style={{ color: '#001858' }}>Coverage</h4>
                <div className="flex gap-2">
                  {selectedAgent.regions.map((region, i) => (
                    <span
                      key={i}
                      className="flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg"
                      style={{ background: '#8bd3dd', color: '#001858', border: '2px solid #001858' }}
                    >
                      <Globe className="w-3 h-3" />
                      {region}
                      {selectedAgent.country && ` (${selectedAgent.country})`}
                    </span>
                  ))}
                </div>
              </div>

              {/* Action */}
              <motion.button
                className="w-full flex items-center justify-center gap-2 py-3 rounded-xl font-bold"
                style={{
                  background: '#f582ae',
                  color: '#001858',
                  border: '2px solid #001858',
                  boxShadow: '3px 3px 0 #001858',
                }}
                whileHover={{ x: -2, y: -2, boxShadow: '5px 5px 0 #001858' }}
                whileTap={{ x: 1, y: 1, boxShadow: '2px 2px 0 #001858' }}
              >
                <Sparkles className="w-4 h-4" />
                Use This Agent
              </motion.button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
