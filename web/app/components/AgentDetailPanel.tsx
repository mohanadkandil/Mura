"use client";

import { motion, AnimatePresence } from "framer-motion";
import {
  X,
  Brain,
  Package,
  Truck,
  Shield,
  CheckCircle,
  AlertTriangle,
  Clock,
  Loader2,
  MessageSquare,
  Zap
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import { AgentType, AgentStatus } from "./AgentNode";

interface AgentDetailPanelProps {
  agent: {
    id: string;
    type: AgentType;
    name: string;
    status: AgentStatus;
    thought?: string;
  } | null;
  onClose: () => void;
  logs: Array<{
    agent: string;
    message: string;
    type: string;
    timestamp: Date;
    details?: string;
  }>;
}

const agentDescriptions: Record<AgentType, { title: string; description: string }> = {
  orchestrator: {
    title: "MURA Orchestrator",
    description: "Central coordinator managing the procurement workflow"
  },
  supplier: {
    title: "Supplier Agent",
    description: "Manages catalog, pricing, and inventory for quote generation"
  },
  logistics: {
    title: "Logistics Agent",
    description: "Optimizes shipping routes and carrier selection"
  },
  compliance: {
    title: "Compliance Agent",
    description: "Verifies regional regulations and certifications"
  }
};

const iconMap = {
  orchestrator: Brain,
  supplier: Package,
  logistics: Truck,
  compliance: Shield
};

const colorMap = {
  orchestrator: "#f582ae",
  supplier: "#8bd3dd",
  logistics: "#f59e0b",
  compliance: "#f3d2c1"
};

export function AgentDetailPanel({ agent, onClose, logs }: AgentDetailPanelProps) {
  if (!agent) return null;

  const Icon = iconMap[agent.type];
  const color = colorMap[agent.type];
  const info = agentDescriptions[agent.type];

  // Filter logs for this agent - match by agent name containing the agent id
  const agentLogs = logs.filter(log => {
    const logAgentLower = log.agent.toLowerCase();
    const agentIdLower = agent.id.toLowerCase();
    const agentNameLower = agent.name.toLowerCase();

    // Match by ID or name
    return logAgentLower.includes(agentIdLower) ||
           logAgentLower.includes(agentNameLower) ||
           agentNameLower.includes(logAgentLower.split(' ')[0]);
  });

  return (
    <AnimatePresence>
      <motion.div
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
      >
        {/* Backdrop */}
        <motion.div
          className="absolute inset-0"
          style={{ background: 'rgba(0, 24, 88, 0.6)' }}
          onClick={onClose}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        />

        {/* Panel */}
        <motion.div
          className="relative w-full max-w-2xl rounded-2xl p-6 max-h-[85vh] overflow-y-auto"
          style={{
            background: '#fef6e4',
            border: '3px solid #001858',
            boxShadow: '8px 8px 0 #001858',
          }}
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 20 }}
          transition={{ type: "spring", damping: 25 }}
        >
          {/* Close button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 w-8 h-8 rounded-lg flex items-center justify-center transition-transform hover:scale-110"
            style={{
              background: '#f3d2c1',
              border: '2px solid #001858',
            }}
          >
            <X className="w-4 h-4" style={{ color: '#001858' }} />
          </button>

          {/* Header */}
          <div className="flex items-center gap-4 mb-6">
            <div
              className="w-16 h-16 rounded-full flex items-center justify-center"
              style={{
                background: color,
                border: '3px solid #001858',
                boxShadow: '3px 3px 0 #001858',
              }}
            >
              <Icon className="w-8 h-8" style={{ color: '#001858' }} />
            </div>
            <div className="flex-1">
              <h3 className="text-xl font-bold" style={{ color: '#001858' }}>{agent.name}</h3>
              <p className="text-sm" style={{ color: '#172c66' }}>{info.description}</p>
              <div className="flex items-center gap-2 mt-1">
                {agent.status === "thinking" && (
                  <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full" style={{ background: '#8bd3dd', color: '#001858' }}>
                    <Loader2 className="w-3 h-3 animate-spin" />
                    Processing
                  </span>
                )}
                {agent.status === "success" && (
                  <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full" style={{ background: '#22c55e', color: '#fff' }}>
                    <CheckCircle className="w-3 h-3" />
                    Complete
                  </span>
                )}
                {agent.status === "warning" && (
                  <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full" style={{ background: '#f59e0b', color: '#001858' }}>
                    <AlertTriangle className="w-3 h-3" />
                    Review Needed
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Current thought */}
          {agent.thought && (
            <div
              className="rounded-xl p-4 mb-6 flex items-start gap-3"
              style={{
                background: color,
                border: '2px solid #001858',
              }}
            >
              <Zap className="w-5 h-5 mt-0.5 flex-shrink-0" style={{ color: '#001858' }} />
              <div>
                <p className="text-xs font-bold mb-1" style={{ color: '#001858' }}>Current Action</p>
                <p className="text-sm font-medium" style={{ color: '#001858' }}>{agent.thought}</p>
              </div>
            </div>
          )}

          {/* Activity Log */}
          <div className="mb-4">
            <div className="flex items-center gap-2 mb-3">
              <MessageSquare className="w-4 h-4" style={{ color: '#f582ae' }} />
              <h4 className="text-sm font-bold" style={{ color: '#001858' }}>Activity Log</h4>
              <span className="text-xs px-2 py-0.5 rounded-full" style={{ background: '#f3d2c1', color: '#001858' }}>
                {agentLogs.length} events
              </span>
            </div>

            {agentLogs.length > 0 ? (
              <div className="space-y-2">
                {agentLogs.map((log, i) => (
                  <motion.div
                    key={i}
                    className="rounded-xl p-3"
                    style={{
                      background: '#fff',
                      border: '2px solid #001858',
                    }}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                  >
                    <div className="flex items-start gap-3">
                      <div
                        className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold"
                        style={{
                          background: color,
                          border: '2px solid #001858',
                          color: '#001858'
                        }}
                      >
                        {i + 1}
                      </div>
                      <div className="flex-1">
                        <p className="text-sm" style={{ color: '#001858' }}>{log.message}</p>
                        {log.details && (
                          <div
                            className="mt-2 p-3 rounded-lg text-xs prose prose-sm max-w-none"
                            style={{
                              background: '#f3d2c1',
                              color: '#001858',
                              border: '1px solid #001858'
                            }}
                          >
                            <ReactMarkdown
                              components={{
                                h1: ({ children }) => <h1 className="text-sm font-bold mb-2 mt-0" style={{ color: '#001858' }}>{children}</h1>,
                                h2: ({ children }) => <h2 className="text-sm font-bold mb-2 mt-2" style={{ color: '#001858' }}>{children}</h2>,
                                h3: ({ children }) => <h3 className="text-xs font-bold mb-1 mt-2" style={{ color: '#001858' }}>{children}</h3>,
                                h4: ({ children }) => <h4 className="text-xs font-semibold mb-1 mt-2" style={{ color: '#001858' }}>{children}</h4>,
                                p: ({ children }) => <p className="text-xs mb-2 leading-relaxed" style={{ color: '#172c66' }}>{children}</p>,
                                ul: ({ children }) => <ul className="text-xs list-disc pl-4 mb-2 space-y-1">{children}</ul>,
                                ol: ({ children }) => <ol className="text-xs list-decimal pl-4 mb-2 space-y-1">{children}</ol>,
                                li: ({ children }) => <li className="text-xs" style={{ color: '#172c66' }}>{children}</li>,
                                strong: ({ children }) => <strong className="font-bold" style={{ color: '#001858' }}>{children}</strong>,
                                em: ({ children }) => <em className="italic">{children}</em>,
                              }}
                            >
                              {log.details}
                            </ReactMarkdown>
                          </div>
                        )}
                        <p className="text-xs mt-1" style={{ color: '#172c66', opacity: 0.6 }}>
                          {log.timestamp.toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            ) : (
              <div
                className="rounded-xl p-6 text-center"
                style={{
                  background: '#fff',
                  border: '2px solid #001858',
                }}
              >
                <Clock className="w-8 h-8 mx-auto mb-2" style={{ color: '#172c66', opacity: 0.3 }} />
                <p className="text-sm" style={{ color: '#172c66' }}>No activity yet</p>
                <p className="text-xs mt-1" style={{ color: '#172c66', opacity: 0.6 }}>
                  Events will appear here as the agent processes
                </p>
              </div>
            )}
          </div>

          {/* Status Summary */}
          {agent.status === "success" && agentLogs.length > 0 && (
            <div
              className="rounded-xl p-4 flex items-start gap-3"
              style={{
                background: '#22c55e',
                border: '2px solid #001858',
              }}
            >
              <CheckCircle className="w-5 h-5 mt-0.5 flex-shrink-0" style={{ color: '#fff' }} />
              <div>
                <p className="text-xs font-bold mb-1" style={{ color: '#fff' }}>Completed</p>
                <p className="text-sm font-medium" style={{ color: '#fff' }}>
                  {agentLogs[agentLogs.length - 1]?.message || "Agent finished processing"}
                </p>
              </div>
            </div>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
