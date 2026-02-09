"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Bot, CheckCircle, AlertTriangle, Loader2, Info } from "lucide-react";
import { useEffect, useRef } from "react";

export interface LogEntry {
  id: string;
  agent: string;
  message: string;
  type: "info" | "thinking" | "success" | "warning" | "error";
  timestamp: Date;
  details?: string;  // Optional detailed information (e.g., compliance assessment)
}

interface LogPanelProps {
  logs: LogEntry[];
}

export function LogPanel({ logs }: LogPanelProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  const getIcon = (type: LogEntry["type"]) => {
    switch (type) {
      case "thinking":
        return <Loader2 className="w-4 h-4 animate-spin" style={{ color: '#f582ae' }} />;
      case "success":
        return <CheckCircle className="w-4 h-4" style={{ color: '#22c55e' }} />;
      case "warning":
        return <AlertTriangle className="w-4 h-4" style={{ color: '#f59e0b' }} />;
      case "error":
        return <AlertTriangle className="w-4 h-4" style={{ color: '#ef4444' }} />;
      default:
        return <Info className="w-4 h-4" style={{ color: '#8bd3dd' }} />;
    }
  };

  const getAgentColor = (agent: string) => {
    if (agent.includes("Orchestrator")) return "#f582ae";
    if (agent.includes("Supplier") || agent.includes("Parts")) return "#8bd3dd";
    if (agent.includes("Logistics")) return "#f59e0b";
    if (agent.includes("Compliance")) return "#f3d2c1";
    return "#172c66";
  };

  return (
    <div
      className="rounded-xl sm:rounded-2xl overflow-hidden h-full flex flex-col"
      style={{
        background: '#fef6e4',
        border: '2px solid #001858',
        boxShadow: '3px 3px 0 #001858',
      }}
    >
      <div
        className="px-3 sm:px-4 py-2 sm:py-3 flex items-center gap-2"
        style={{
          borderBottom: '2px solid #001858',
          background: '#f3d2c1',
        }}
      >
        <Bot className="w-4 h-4 sm:w-5 sm:h-5" style={{ color: '#001858' }} />
        <span className="text-xs sm:text-sm font-bold" style={{ color: '#001858' }}>Agent Activity</span>
        <span
          className="text-[10px] sm:text-xs ml-auto px-1.5 sm:px-2 py-0.5 rounded-full font-medium"
          style={{
            background: '#8bd3dd',
            color: '#001858',
            border: '1px solid #001858',
          }}
        >
          {logs.length}
        </span>
      </div>

      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-2 sm:p-4 space-y-2 sm:space-y-3"
      >
        <AnimatePresence mode="popLayout">
          {logs.map((log) => (
            <motion.div
              key={log.id}
              initial={{ opacity: 0, x: -20, height: 0 }}
              animate={{ opacity: 1, x: 0, height: "auto" }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
              className="flex gap-2 sm:gap-3 p-2 sm:p-3 rounded-lg sm:rounded-xl"
              style={{
                background: '#fff',
                border: '2px solid #001858',
                boxShadow: '2px 2px 0 #001858',
              }}
            >
              <div className="flex-shrink-0 mt-0.5">
                {getIcon(log.type)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-baseline gap-1 sm:gap-2 flex-wrap">
                  <span
                    className="text-[10px] sm:text-xs font-bold"
                    style={{ color: getAgentColor(log.agent) }}
                  >
                    {log.agent}
                  </span>
                  <span className="text-[9px] sm:text-[10px]" style={{ color: '#172c66', opacity: 0.6 }}>
                    {log.timestamp.toLocaleTimeString()}
                  </span>
                </div>
                <p className="text-xs sm:text-sm mt-0.5 leading-relaxed" style={{ color: '#172c66' }}>
                  {log.message}
                </p>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {logs.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-sm" style={{ color: '#172c66' }}>
            <Bot className="w-10 h-10 mb-3" style={{ color: '#8bd3dd' }} />
            <p className="font-medium">Waiting for agent activity...</p>
          </div>
        )}
      </div>
    </div>
  );
}
