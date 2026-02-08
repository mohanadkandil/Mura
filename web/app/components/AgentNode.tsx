"use client";

import { motion, AnimatePresence, PanInfo } from "framer-motion";
import { RefObject } from "react";
import {
  Truck,
  Shield,
  Brain,
  Package,
  Check,
  Loader2,
  AlertTriangle,
  GripVertical
} from "lucide-react";

export type AgentStatus = "idle" | "thinking" | "success" | "warning" | "error";

export type AgentType = "orchestrator" | "supplier" | "logistics" | "compliance";

interface AgentNodeProps {
  id: string;
  type: AgentType;
  name: string;
  status: AgentStatus;
  thought?: string;
  position: { x: number; y: number };
  delay?: number;
  draggable?: boolean;
  onDrag?: (info: { offset: { x: number; y: number } }) => void;
  onDragEnd?: (info: { point: { x: number; y: number }; offset: { x: number; y: number } }) => void;
  containerRef?: RefObject<HTMLDivElement | null>;
  onClick?: () => void;
}

const agentConfig = {
  orchestrator: {
    icon: Brain,
    bg: "#f582ae",
    size: 100,
  },
  supplier: {
    icon: Package,
    bg: "#8bd3dd",
    size: 80,
  },
  logistics: {
    icon: Truck,
    bg: "#f59e0b",
    size: 80,
  },
  compliance: {
    icon: Shield,
    bg: "#f3d2c1",
    size: 80,
  },
};

const statusConfig = {
  idle: { ring: false, pulse: false },
  thinking: { ring: true, pulse: true },
  success: { ring: false, pulse: false },
  warning: { ring: false, pulse: false },
  error: { ring: false, pulse: false },
};

export function AgentNode({
  id,
  type,
  name,
  status,
  thought,
  position,
  delay = 0,
  draggable = false,
  onDrag,
  onDragEnd,
  containerRef,
  onClick
}: AgentNodeProps) {
  const config = agentConfig[type];
  const Icon = config.icon;
  const statusCfg = statusConfig[status];

  const handleDrag = (_: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
    onDrag?.({ offset: info.offset });
  };

  const handleDragEnd = (_: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
    onDragEnd?.({ point: info.point, offset: info.offset });
  };

  return (
    <motion.div
      className="absolute flex flex-col items-center select-none"
      style={{
        left: position.x,
        top: position.y,
        cursor: draggable ? 'grab' : 'default',
        zIndex: status === 'thinking' ? 20 : 10,
      }}
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{
        type: "spring",
        stiffness: 200,
        damping: 20,
        delay
      }}
      drag={draggable}
      dragMomentum={false}
      dragElastic={0}
      dragConstraints={containerRef}
      onDrag={handleDrag}
      onDragEnd={handleDragEnd}
      whileDrag={{ cursor: 'grabbing', scale: 1.05, zIndex: 100 }}
    >
      {/* Thought bubble */}
      <AnimatePresence>
        {thought && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.8 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.8 }}
            className="absolute -top-20 left-1/2 -translate-x-1/2 w-52 z-30 pointer-events-none"
          >
            <div
              className="rounded-xl px-3 py-2 text-xs relative"
              style={{
                background: '#fef6e4',
                border: '2px solid #001858',
                boxShadow: '3px 3px 0 #001858',
                color: '#172c66'
              }}
            >
              <div className="flex items-start gap-2">
                {status === "thinking" && (
                  <Loader2 className="w-3 h-3 mt-0.5 animate-spin flex-shrink-0" style={{ color: '#f582ae' }} />
                )}
                {status === "success" && (
                  <Check className="w-3 h-3 mt-0.5 flex-shrink-0" style={{ color: '#22c55e' }} />
                )}
                {status === "warning" && (
                  <AlertTriangle className="w-3 h-3 mt-0.5 flex-shrink-0" style={{ color: '#f59e0b' }} />
                )}
                <span className="leading-tight font-medium">{thought}</span>
              </div>
            </div>
            {/* Bubble pointer */}
            <div
              className="absolute left-1/2 -translate-x-1/2 -bottom-2 w-4 h-4 rotate-45"
              style={{
                background: '#fef6e4',
                borderRight: '2px solid #001858',
                borderBottom: '2px solid #001858',
              }}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Pulse rings */}
      {statusCfg.ring && (
        <>
          <motion.div
            className="absolute rounded-full pointer-events-none"
            style={{
              width: config.size + 30,
              height: config.size + 30,
              border: `3px solid ${config.bg}`,
            }}
            animate={{
              scale: [1, 1.6],
              opacity: [0.8, 0],
            }}
            transition={{
              duration: 1.5,
              repeat: Infinity,
              ease: "easeOut",
            }}
          />
          <motion.div
            className="absolute rounded-full pointer-events-none"
            style={{
              width: config.size + 30,
              height: config.size + 30,
              border: `3px solid ${config.bg}`,
            }}
            animate={{
              scale: [1, 1.6],
              opacity: [0.8, 0],
            }}
            transition={{
              duration: 1.5,
              repeat: Infinity,
              ease: "easeOut",
              delay: 0.5,
            }}
          />
        </>
      )}

      {/* Main node */}
      <motion.div
        className="relative rounded-full flex items-center justify-center cursor-pointer"
        style={{
          width: config.size,
          height: config.size,
          background: config.bg,
          border: '3px solid #001858',
          boxShadow: status === "thinking"
            ? `5px 5px 0 #001858`
            : `4px 4px 0 #001858`,
        }}
        animate={statusCfg.pulse ? {
          scale: [1, 1.05, 1],
        } : {}}
        transition={{
          duration: 1.5,
          repeat: statusCfg.pulse ? Infinity : 0,
          ease: "easeInOut",
        }}
        onClick={(e) => {
          e.stopPropagation();
          onClick?.();
        }}
        whileHover={{ scale: 1.08 }}
      >
        {/* Drag indicator */}
        {draggable && (
          <div className="absolute -top-1 -left-1 opacity-50">
            <GripVertical className="w-4 h-4" style={{ color: '#001858' }} />
          </div>
        )}

        {/* Status overlay */}
        {status === "success" && (
          <motion.div
            className="absolute inset-0 rounded-full"
            style={{ background: 'rgba(34, 197, 94, 0.2)' }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          />
        )}
        {status === "warning" && (
          <motion.div
            className="absolute inset-0 rounded-full"
            style={{ background: 'rgba(245, 158, 11, 0.2)' }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          />
        )}

        {/* Icon */}
        <Icon
          style={{ color: '#001858' }}
          size={config.size * 0.4}
          strokeWidth={2}
        />

        {/* Status indicator */}
        <motion.div
          className="absolute -bottom-1 -right-1 w-7 h-7 rounded-full flex items-center justify-center"
          style={{
            background: status === "thinking" ? "#8bd3dd" :
              status === "success" ? "#22c55e" :
              status === "warning" ? "#f59e0b" :
              status === "error" ? "#ef4444" :
              "#f3d2c1",
            border: '2px solid #001858',
            boxShadow: '2px 2px 0 #001858',
          }}
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
        >
          {status === "thinking" && (
            <Loader2 className="w-3 h-3 animate-spin" style={{ color: '#001858' }} />
          )}
          {status === "success" && (
            <Check className="w-3 h-3" style={{ color: '#fff' }} />
          )}
          {status === "warning" && (
            <AlertTriangle className="w-3 h-3" style={{ color: '#001858' }} />
          )}
        </motion.div>
      </motion.div>

      {/* Name label */}
      <motion.div
        className="mt-3 text-sm font-semibold pointer-events-none"
        style={{ color: '#001858' }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: delay + 0.2 }}
      >
        {name}
      </motion.div>
    </motion.div>
  );
}
