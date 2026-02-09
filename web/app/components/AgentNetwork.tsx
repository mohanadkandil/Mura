"use client";

import { motion } from "framer-motion";
import { useState, useRef, useCallback, useMemo, useEffect } from "react";
import { AgentNode, AgentStatus, AgentType } from "./AgentNode";
import { ConnectionLine } from "./ConnectionLine";
import { Move } from "lucide-react";

export interface Agent {
  id: string;
  type: AgentType;
  name: string;
  status: AgentStatus;
  thought?: string;
}

interface AgentNetworkProps {
  agents: Agent[];
  activeConnections: { from: string; to: string }[];
  phase: "idle" | "input" | "discovery" | "quoting" | "compliance" | "logistics" | "complete" | "error";
  onAgentClick?: (agent: Agent) => void;
}

// Calculate dynamic positions based on agents and container size
function calculatePositions(agents: Agent[], isMobile: boolean = false): Record<string, { x: number; y: number }> {
  const positions: Record<string, { x: number; y: number }> = {};

  // Adjust base positions for mobile
  const centerX = isMobile ? 150 : 400;
  const baseY = isMobile ? 60 : 80;
  const supplierY = isMobile ? 180 : 280;
  const bottomY = isMobile ? 300 : 450;
  const maxWidth = isMobile ? 320 : 800;

  const BASE_POSITIONS: Record<string, { x: number; y: number }> = {
    orchestrator: { x: centerX, y: baseY },
    logistics: { x: isMobile ? 80 : 250, y: bottomY },
    compliance: { x: isMobile ? 220 : 550, y: bottomY },
  };

  // Count suppliers to distribute them evenly
  const suppliers = agents.filter(a => a.type === "supplier");
  const supplierCount = suppliers.length;

  agents.forEach((agent) => {
    if (BASE_POSITIONS[agent.id]) {
      positions[agent.id] = BASE_POSITIONS[agent.id];
    } else if (agent.type === "supplier") {
      // Distribute suppliers in a row/grid
      const supplierIndex = suppliers.findIndex(s => s.id === agent.id);
      if (isMobile) {
        // Grid layout for mobile (2 columns)
        const col = supplierIndex % 2;
        const row = Math.floor(supplierIndex / 2);
        positions[agent.id] = {
          x: col === 0 ? 80 : 220,
          y: supplierY + row * 80,
        };
      } else {
        const spacing = maxWidth / (supplierCount + 1);
        positions[agent.id] = {
          x: spacing * (supplierIndex + 1) - 40,
          y: supplierY,
        };
      }
    } else if (agent.type === "logistics") {
      positions[agent.id] = BASE_POSITIONS.logistics;
    } else if (agent.type === "compliance") {
      positions[agent.id] = BASE_POSITIONS.compliance;
    } else {
      // Default position for unknown types
      positions[agent.id] = { x: centerX, y: supplierY };
    }
  });

  return positions;
}

export function AgentNetwork({ agents, activeConnections, phase, onAgentClick }: AgentNetworkProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isMobile, setIsMobile] = useState(false);

  // Check if mobile on mount and resize
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 640);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Calculate base positions based on current agents and screen size
  const basePositions = useMemo(() => calculatePositions(agents, isMobile), [agents, isMobile]);

  const [positions, setPositions] = useState<Record<string, { x: number; y: number }>>(basePositions);
  const [dragOffsets, setDragOffsets] = useState<Record<string, { x: number; y: number }>>({});

  // Update positions when agents change or screen size changes
  useEffect(() => {
    setPositions(prev => {
      const newPositions = { ...basePositions };
      // Preserve drag offsets for existing agents (only on desktop)
      if (!isMobile) {
        Object.keys(dragOffsets).forEach(id => {
          if (newPositions[id] && dragOffsets[id]) {
            newPositions[id] = {
              x: basePositions[id].x + dragOffsets[id].x,
              y: basePositions[id].y + dragOffsets[id].y,
            };
          }
        });
      }
      return newPositions;
    });
  }, [basePositions, dragOffsets, isMobile]);

  // Get node center for connection lines
  const getNodeCenter = useCallback((id: string, type: AgentType) => {
    const pos = positions[id] || basePositions[id] || { x: 400, y: 280 };
    const size = type === "orchestrator" ? 100 : 80;
    return {
      x: pos.x + size / 2,
      y: pos.y + size / 2,
    };
  }, [positions, basePositions]);

  // Handle drag end for a node
  const handleDragEnd = useCallback((id: string, info: { point: { x: number; y: number }; offset: { x: number; y: number } }) => {
    setDragOffsets(prev => ({
      ...prev,
      [id]: {
        x: (prev[id]?.x || 0) + info.offset.x,
        y: (prev[id]?.y || 0) + info.offset.y,
      }
    }));
  }, []);

  // Handle drag for real-time updates
  const handleDrag = useCallback((id: string, info: { offset: { x: number; y: number } }) => {
    setPositions(prev => ({
      ...prev,
      [id]: {
        x: (basePositions[id]?.x || 400) + (dragOffsets[id]?.x || 0) + info.offset.x,
        y: (basePositions[id]?.y || 280) + (dragOffsets[id]?.y || 0) + info.offset.y,
      }
    }));
  }, [basePositions, dragOffsets]);

  return (
    <div
      ref={containerRef}
      className="relative w-full h-[400px] sm:h-[500px] lg:h-[600px] overflow-hidden"
      style={{ background: '#fef6e4' }}
    >
      {/* Background grid */}
      <div
        className="absolute inset-0"
        style={{
          backgroundImage: `
            linear-gradient(to right, #001858 1px, transparent 1px),
            linear-gradient(to bottom, #001858 1px, transparent 1px)
          `,
          backgroundSize: isMobile ? "30px 30px" : "50px 50px",
          opacity: 0.05,
        }}
      />

      {/* Decorative circles - hide on mobile */}
      {!isMobile && (
        <>
          <motion.div
            className="absolute rounded-full pointer-events-none"
            style={{
              width: 200,
              height: 200,
              background: 'rgba(139, 211, 221, 0.15)',
              left: 50,
              top: 100,
            }}
            animate={{
              scale: [1, 1.1, 1],
            }}
            transition={{
              duration: 4,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          />
          <motion.div
            className="absolute rounded-full pointer-events-none"
            style={{
              width: 150,
              height: 150,
              background: 'rgba(245, 130, 174, 0.15)',
              right: 80,
              bottom: 150,
            }}
            animate={{
              scale: [1, 1.15, 1],
            }}
            transition={{
              duration: 5,
              repeat: Infinity,
              ease: "easeInOut",
              delay: 1,
            }}
          />
        </>
      )}

      {/* Drag hint - hide on mobile */}
      {!isMobile && (
        <motion.div
          className="absolute top-4 right-4 flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium"
          style={{
            background: '#8bd3dd',
            border: '2px solid #001858',
            color: '#001858',
          }}
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <Move className="w-3 h-3" />
          Drag nodes to rearrange
        </motion.div>
      )}

      {/* Draw connections */}
      {agents.map((agent) => {
        if (agent.id === "orchestrator") return null;

        const fromPos = getNodeCenter("orchestrator", "orchestrator");
        const toPos = getNodeCenter(agent.id, agent.type);
        const isActive = activeConnections.some(
          (c) => (c.from === "orchestrator" && c.to === agent.id) ||
                 (c.from === agent.id && c.to === "orchestrator")
        );

        return (
          <ConnectionLine
            key={`conn-${agent.id}`}
            from={fromPos}
            to={toPos}
            active={isActive}
            color="#001858"
            delay={0.3}
          />
        );
      })}

      {/* Render agents */}
      {agents.map((agent, index) => (
        <AgentNode
          key={agent.id}
          id={agent.id}
          type={agent.type}
          name={agent.name}
          status={agent.status}
          thought={agent.thought}
          position={positions[agent.id] || basePositions[agent.id] || { x: 400, y: 280 }}
          delay={index * 0.1}
          draggable={true}
          onDrag={(info) => handleDrag(agent.id, info)}
          onDragEnd={(info) => handleDragEnd(agent.id, info)}
          containerRef={containerRef}
          onClick={() => onAgentClick?.(agent)}
        />
      ))}

      {/* Phase indicator */}
      <motion.div
        className="absolute bottom-2 sm:bottom-4 left-1/2 -translate-x-1/2"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div
          className="rounded-full px-4 sm:px-6 py-1.5 sm:py-2 text-xs sm:text-sm font-semibold"
          style={{
            background: '#f3d2c1',
            border: '2px solid #001858',
            boxShadow: '2px 2px 0 #001858',
            color: '#001858',
          }}
        >
          <span style={{ color: '#172c66' }}>Phase: </span>
          <span className="capitalize">{phase}</span>
        </div>
      </motion.div>
    </div>
  );
}
