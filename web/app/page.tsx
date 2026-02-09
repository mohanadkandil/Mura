"use client";

import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Send,
  Sparkles,
  Loader2,
  RotateCcw,
  ArrowRight,
  Globe,
  AlertCircle,
  Github
} from "lucide-react";
import Link from "next/link";
import { AgentNetwork, Agent } from "./components/AgentNetwork";
import { LogPanel, LogEntry } from "./components/LogPanel";
import { ResultCard } from "./components/ResultCard";
import { AgentDetailPanel } from "./components/AgentDetailPanel";
// Streaming is handled directly via fetch, not through api.ts

type Phase = "idle" | "input" | "discovery" | "quoting" | "compliance" | "logistics" | "complete" | "error";

const examplePrompts = [
  "Build me a racing drone for FPV competitions",
  "Source components for an IoT weather station",
  "Find parts for a custom mechanical keyboard",
];

// Map backend step phases to frontend phases
function mapPhase(phase: string): Phase {
  const phaseMap: Record<string, Phase> = {
    "discovery": "discovery",
    "quoting": "quoting",
    "quote": "quoting",
    "logistics": "logistics",
    "compliance": "compliance",
    "complete": "complete",
    "recommendation": "complete",
  };
  return phaseMap[phase.toLowerCase()] || "discovery";
}

// Agent type definitions for dynamic creation
type AgentTypeKey = "orchestrator" | "supplier" | "logistics" | "compliance";

interface AgentInfo {
  id: string;
  type: AgentTypeKey;
  name: string;
}

// Map backend agent names to frontend agent info
function getAgentInfo(agentName: string, supplierCount: { count: number }): AgentInfo {
  const lower = agentName.toLowerCase();

  if (lower.includes("orchestrator") || lower.includes("mura") || lower === "orchestrator") {
    return { id: "orchestrator", type: "orchestrator", name: "MURA Core" };
  }
  if (lower.includes("logistics") || lower === "logistics") {
    return { id: "logistics", type: "logistics", name: "Logistics Agent" };
  }
  if (lower.includes("compliance") || lower === "compliance") {
    return { id: "compliance", type: "compliance", name: "Compliance Agent" };
  }
  // Handle "no supplier found" case
  if (lower === "supplier-none") {
    return { id: "supplier-none", type: "supplier", name: "No Suppliers" };
  }
  if (lower.includes("supplier") || lower.includes("droneparts") || lower.includes("shenzhen") || lower.includes("techparts")) {
    // Extract supplier ID from the agent name (e.g., "supplier-droneparts-eu" -> "droneparts-eu")
    const supplierId = agentName.replace(/^supplier-/, "");

    // Create a readable name
    let name = supplierId;
    if (lower.includes("droneparts")) {
      name = "DroneParts EU";
    } else if (lower.includes("shenzhen")) {
      name = "ShenzhenTech";
    } else if (lower.includes("techparts")) {
      name = "TechParts Global";
    } else {
      supplierCount.count++;
      name = `Supplier ${supplierCount.count}`;
    }

    return { id: `supplier-${supplierId}`, type: "supplier", name };
  }

  // Default to orchestrator for unknown
  return { id: "orchestrator", type: "orchestrator", name: "MURA Core" };
}

// Initial state - only orchestrator visible
const initialAgents: Agent[] = [
  { id: "orchestrator", type: "orchestrator", name: "MURA Core", status: "idle" },
];

export default function Home() {
  const [phase, setPhase] = useState<Phase>("input");
  const [request, setRequest] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [agents, setAgents] = useState<Agent[]>(initialAgents);
  const [discoveredAgents, setDiscoveredAgents] = useState<Set<string>>(new Set(["orchestrator"]));

  const [activeConnections, setActiveConnections] = useState<{ from: string; to: string }[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [showResult, setShowResult] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [recommendation, setRecommendation] = useState<{
    supplier: string;
    total: number;
    shipping: number;
    days: number;
    compliance: "passed" | "warning" | "failed";
    reasoning: string;
  } | null>(null);

  // Add a new agent to the network
  const addAgent = useCallback((agent: Agent) => {
    setDiscoveredAgents(prev => {
      if (prev.has(agent.id)) return prev;
      const next = new Set(prev);
      next.add(agent.id);
      return next;
    });
    setAgents(prev => {
      if (prev.find(a => a.id === agent.id)) return prev;
      return [...prev, agent];
    });
  }, []);

  const updateAgent = useCallback((id: string, updates: Partial<Agent>) => {
    setAgents(prev => prev.map(a => a.id === id ? { ...a, ...updates } : a));
  }, []);

  const addLog = useCallback((agent: string, message: string, type: LogEntry["type"] = "info", details?: string) => {
    const agentNames: Record<string, string> = {
      orchestrator: "MURA Orchestrator",
      "supplier-1": "Supplier Agent 1",
      "supplier-2": "Supplier Agent 2",
      "supplier-3": "Supplier Agent 3",
      logistics: "Logistics Agent",
      compliance: "Compliance Agent",
    };

    setLogs(prev => [...prev, {
      id: `${Date.now()}-${Math.random()}`,
      agent: agentNames[agent] || agent,
      message,
      type,
      timestamp: new Date(),
      details,
    }]);
  }, []);

  const runRealProcurement = useCallback(async () => {
    setIsProcessing(true);
    setPhase("discovery");
    setLogs([]);
    setShowResult(false);
    setError(null);

    // Reset to only orchestrator
    setAgents([{ id: "orchestrator", type: "orchestrator", name: "MURA Core", status: "thinking", thought: "Processing request..." }]);
    setDiscoveredAgents(new Set(["orchestrator"]));
    setActiveConnections([]);

    // Track supplier count for naming
    const supplierCount = { count: 0 };

    try {
      // Use streaming endpoint
      const response = await fetch("/api/procure/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          request: request,
          deadline_days: 14,
          destination_region: "EU",
        }),
      });

      if (!response.ok) {
        throw new Error("Streaming request failed");
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("No response body");
      }

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Process complete SSE messages
        const lines = buffer.split("\n");
        buffer = lines.pop() || ""; // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));

              if (data.type === "step") {
                const agentInfo = getAgentInfo(data.agent, supplierCount);
                const stepPhase = mapPhase(data.phase);

                setPhase(stepPhase);

                // Determine agent status from backend status field
                let agentStatus: "idle" | "thinking" | "success" | "warning" | "error" = "thinking";
                let logType: "info" | "thinking" | "success" | "warning" | "error" = "thinking";

                if (data.status === "error") {
                  agentStatus = "error";
                  logType = "error";
                } else if (data.status === "warning") {
                  agentStatus = "warning";
                  logType = "warning";
                } else if (data.status === "success") {
                  agentStatus = "success";
                  logType = "success";
                }

                // Add agent if not already in network
                addAgent({ ...agentInfo, status: "idle" });

                // Update agent with current thought and status
                setTimeout(() => {
                  updateAgent(agentInfo.id, {
                    status: agentStatus,
                    thought: data.message,
                  });

                  // Pass details if available (e.g., compliance assessment details)
                  addLog(agentInfo.id, data.message, logType, data.details);

                  if (agentInfo.id !== "orchestrator") {
                    setActiveConnections([{ from: "orchestrator", to: agentInfo.id }]);
                  }
                }, 50);
              } else if (data.type === "complete") {
                // Final result received
                const result = data.data;

                // Mark agents as successful, but preserve error/warning states
                setAgents(prev => prev.map(a => ({
                  ...a,
                  status: a.status === "error" ? "error" : a.status === "warning" ? "warning" : "success",
                  thought: undefined,
                })));

                addLog("orchestrator", "Procurement analysis complete!", "success");
                setActiveConnections([]);
                setPhase("complete");

                // Set recommendation
                if (result.recommendation) {
                  const complianceStatus = result.recommendation.compliance_status?.toLowerCase();
                  let compliance: "passed" | "warning" | "failed" = "passed";
                  if (complianceStatus?.includes("warning") || complianceStatus?.includes("review")) {
                    compliance = "warning";
                  } else if (complianceStatus?.includes("fail") || complianceStatus?.includes("block")) {
                    compliance = "failed";
                  }

                  const allOptions = result.recommendation.all_options || [];
                  const best = allOptions[0];

                  setRecommendation({
                    supplier: best?.supplier_name || result.recommendation.recommended_supplier || "Best Supplier",
                    total: best?.shipping_cost || 0,
                    shipping: best?.shipping_cost || 0,
                    days: best?.total_days || result.recommendation.critical_path_days || 7,
                    compliance,
                    reasoning: result.recommendation.recommendation_reason || "Selected based on optimal balance.",
                  });
                }

                setShowResult(true);
              } else if (data.type === "error") {
                throw new Error(data.message);
              }
            } catch (parseError) {
              console.error("Failed to parse SSE data:", parseError);
            }
          }
        }
      }
    } catch (err) {
      console.error("Procurement error:", err);
      setError(err instanceof Error ? err.message : "Procurement failed");
      setPhase("error");
      setAgents(prev => prev.map(a => ({ ...a, status: "idle" as const, thought: undefined })));
      addLog("orchestrator", `Error: ${err instanceof Error ? err.message : "Procurement failed"}`, "error");
    } finally {
      setIsProcessing(false);
    }
  }, [request, updateAgent, addLog, addAgent]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!request.trim() || isProcessing) return;
    runRealProcurement();
  };

  const handleReset = () => {
    setPhase("input");
    setIsProcessing(false);
    setLogs([]);
    setShowResult(false);
    setRecommendation(null);
    setActiveConnections([]);
    setError(null);
    setAgents(initialAgents);
    setDiscoveredAgents(new Set(["orchestrator"]));
  };

  return (
    <div className="min-h-screen" style={{ background: '#fef6e4' }}>
      {/* Header */}
      <header style={{ borderBottom: '2px solid #001858' }}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-4 flex items-center justify-between">
          <div className="flex items-center gap-2 sm:gap-3">
            <motion.div
              className="w-8 h-8 sm:w-10 sm:h-10 rounded-xl flex items-center justify-center"
              style={{
                background: '#f582ae',
                border: '2px solid #001858',
                boxShadow: '2px 2px 0 #001858',
              }}
              whileHover={{ scale: 1.05, rotate: 5 }}
            >
              <Sparkles className="w-4 h-4 sm:w-5 sm:h-5" style={{ color: '#001858' }} />
            </motion.div>
            <div>
              <h1 className="text-lg sm:text-xl font-bold" style={{ color: '#001858' }}>MURA</h1>
              <p className="text-xs hidden sm:block" style={{ color: '#172c66' }}>Supply Chain Agent Network</p>
            </div>
          </div>

          <div className="flex items-center gap-2 sm:gap-3">
            <Link
              href="/registry"
              className="flex items-center gap-1 sm:gap-2 text-xs sm:text-sm font-medium px-2 sm:px-4 py-1.5 sm:py-2 rounded-lg transition-all hover:-translate-y-0.5"
              style={{
                color: '#001858',
                border: '2px solid #001858',
              }}
            >
              <Globe className="w-3 h-3 sm:w-4 sm:h-4" />
              <span className="hidden sm:inline">Registry</span>
            </Link>
            <Link
              href="/docs"
              className="flex items-center gap-1 sm:gap-2 text-xs sm:text-sm font-medium px-2 sm:px-4 py-1.5 sm:py-2 rounded-lg transition-all hover:-translate-y-0.5"
              style={{
                color: '#001858',
                border: '2px solid #001858',
              }}
            >
              SDK
            </Link>
            <Link
              href="/about"
              className="flex items-center gap-1 sm:gap-2 text-xs sm:text-sm font-medium px-2 sm:px-4 py-1.5 sm:py-2 rounded-lg transition-all hover:-translate-y-0.5"
              style={{
                background: '#f582ae',
                color: '#001858',
                border: '2px solid #001858',
              }}
            >
              About
            </Link>
            <a
              href="https://github.com/mohanadkandil"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center w-8 h-8 sm:w-9 sm:h-9 rounded-lg transition-all hover:-translate-y-0.5"
              style={{
                background: '#001858',
                color: '#fef6e4',
                border: '2px solid #001858',
              }}
            >
              <Github className="w-4 h-4" />
            </a>

          {phase !== "input" && (
              <motion.button
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                onClick={handleReset}
                className="flex items-center gap-1 sm:gap-2 text-xs sm:text-sm font-semibold px-2 sm:px-4 py-1.5 sm:py-2 rounded-lg transition-transform hover:-translate-x-0.5 hover:-translate-y-0.5"
                style={{
                  color: '#001858',
                  border: '2px solid #001858',
                  boxShadow: '2px 2px 0 #001858',
                }}
              >
                <RotateCcw className="w-3 h-3 sm:w-4 sm:h-4" />
                <span className="hidden sm:inline">New Request</span>
              </motion.button>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-4 sm:py-8">
        <AnimatePresence mode="wait">
          {phase === "input" ? (
            <motion.div
              key="input"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="max-w-2xl mx-auto pt-8 sm:pt-16"
            >
              {/* Hero */}
              <div className="text-center mb-8 sm:mb-12">
                <motion.h2
                  className="text-2xl sm:text-4xl md:text-5xl font-bold mb-3 sm:mb-4 px-2"
                  style={{ color: '#001858' }}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  What do you need to procure?
                </motion.h2>
                <motion.p
                  className="text-sm sm:text-lg px-4"
                  style={{ color: '#172c66' }}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.1 }}
                >
                  Describe your requirements and let AI agents coordinate your supply chain
                </motion.p>
              </div>

              {/* Main Input */}
              <motion.form
                onSubmit={handleSubmit}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                <div
                  className="rounded-xl sm:rounded-2xl overflow-hidden"
                  style={{
                    background: '#fff',
                    border: '3px solid #001858',
                    boxShadow: '4px 4px 0 #001858',
                  }}
                >
                  <textarea
                    value={request}
                    onChange={(e) => setRequest(e.target.value)}
                    placeholder="Build me a racing drone for FPV competitions..."
                    className="w-full text-base sm:text-lg resize-none focus:outline-none p-4 sm:p-6 min-h-[120px] sm:min-h-[160px]"
                    style={{ color: '#001858', background: 'transparent' }}
                  />

                  {/* Bottom bar */}
                  <div
                    className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 px-4 sm:px-6 py-3 sm:py-4"
                    style={{ borderTop: '2px solid #001858', background: '#fef6e4' }}
                  >
                    <div className="flex flex-wrap gap-2 justify-center sm:justify-start">
                      {examplePrompts.map((prompt, i) => (
                        <button
                          key={i}
                          type="button"
                          onClick={() => setRequest(prompt)}
                          className="text-xs px-2 sm:px-3 py-1 sm:py-1.5 rounded-full font-medium transition-all hover:-translate-y-0.5"
                          style={{
                            background: request === prompt ? '#f582ae' : 'transparent',
                            border: '2px solid #001858',
                            color: '#001858',
                          }}
                        >
                          {prompt.split(' ').slice(0, 2).join(' ')}...
                        </button>
                      ))}
                    </div>

                    <motion.button
                      type="submit"
                      disabled={!request.trim()}
                      className="flex items-center justify-center gap-2 px-4 sm:px-6 py-2.5 sm:py-3 rounded-xl font-bold disabled:opacity-40 disabled:cursor-not-allowed"
                      style={{
                        background: '#f582ae',
                        color: '#001858',
                        border: '2px solid #001858',
                        boxShadow: '3px 3px 0 #001858',
                      }}
                      whileHover={{
                        x: -2,
                        y: -2,
                        boxShadow: '5px 5px 0 #001858',
                      }}
                      whileTap={{
                        x: 1,
                        y: 1,
                        boxShadow: '2px 2px 0 #001858',
                      }}
                    >
                      Start
                      <ArrowRight className="w-5 h-5" />
                    </motion.button>
                  </div>
                </div>
              </motion.form>

              {/* Subtle hint */}
              <motion.p
                className="text-center text-sm mt-6"
                style={{ color: '#172c66', opacity: 0.6 }}
                initial={{ opacity: 0 }}
                animate={{ opacity: 0.6 }}
                transition={{ delay: 0.5 }}
              >
                Press Enter or click Start to begin
              </motion.p>
            </motion.div>
          ) : (
            /* Agent Visualization */
            <motion.div
              key="visualization"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6"
            >
              {/* Request summary */}
              <div className="col-span-1 lg:col-span-3">
                <motion.div
                  className="rounded-xl px-4 sm:px-6 py-3 sm:py-4 flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-4"
                  style={{
                    background: '#fff',
                    border: '2px solid #001858',
                    boxShadow: '3px 3px 0 #001858',
                  }}
                  initial={{ opacity: 0, y: -20 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  <div className="flex-1">
                    <p className="font-semibold text-sm sm:text-base" style={{ color: '#001858' }}>{request}</p>
                  </div>
                  {isProcessing && (
                    <div className="flex items-center gap-2">
                      <Loader2 className="w-4 h-4 sm:w-5 sm:h-5 animate-spin" style={{ color: '#f582ae' }} />
                      <span className="text-xs sm:text-sm font-medium" style={{ color: '#001858' }}>Processing...</span>
                    </div>
                  )}
                  {phase === "error" && (
                    <div className="flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 sm:w-5 sm:h-5" style={{ color: '#ef4444' }} />
                      <span className="text-xs sm:text-sm font-medium" style={{ color: '#ef4444' }}>Error occurred</span>
                    </div>
                  )}
                </motion.div>
              </div>

              {/* Error message */}
              {error && (
                <div className="col-span-1 lg:col-span-3">
                  <motion.div
                    className="rounded-xl px-4 sm:px-6 py-3 sm:py-4"
                    style={{
                      background: '#fef2f2',
                      border: '2px solid #ef4444',
                    }}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                  >
                    <p className="text-xs sm:text-sm" style={{ color: '#dc2626' }}>
                      <strong>Error:</strong> {error}
                    </p>
                    <p className="text-xs mt-1" style={{ color: '#dc2626', opacity: 0.7 }}>
                      Please try again or check the connection
                    </p>
                  </motion.div>
                </div>
              )}

              {/* Agent network */}
              <div className="col-span-1 lg:col-span-2 order-2 lg:order-1">
                <motion.div
                  className="rounded-xl sm:rounded-2xl overflow-hidden"
                  style={{
                    border: '2px sm:border-3 solid #001858',
                    boxShadow: '4px 4px 0 #001858',
                  }}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.2 }}
                >
                  <AgentNetwork
                    agents={agents}
                    activeConnections={activeConnections}
                    phase={phase}
                    onAgentClick={(agent) => setSelectedAgent(agent)}
                  />
                </motion.div>

                <div className="mt-4 sm:mt-6">
                  <ResultCard recommendation={recommendation} visible={showResult} />
                </div>
              </div>

              {/* Log panel */}
              <div className="col-span-1 order-1 lg:order-2">
                <motion.div
                  className="h-[300px] sm:h-[400px] lg:h-[600px]"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 }}
                >
                  <LogPanel logs={logs} />
                </motion.div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* Agent Detail Panel */}
      {selectedAgent && (
        <AgentDetailPanel
          agent={selectedAgent}
          onClose={() => setSelectedAgent(null)}
          logs={logs}
        />
      )}
    </div>
  );
}
