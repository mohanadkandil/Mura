"use client";

import { motion } from "framer-motion";
import { useEffect, useState } from "react";

interface ConnectionLineProps {
  from: { x: number; y: number };
  to: { x: number; y: number };
  active?: boolean;
  color?: string;
  delay?: number;
}

export function ConnectionLine({
  from,
  to,
  active = false,
  color = "#001858",
  delay = 0
}: ConnectionLineProps) {
  const [particles, setParticles] = useState<number[]>([]);

  // Calculate line properties
  const dx = to.x - from.x;
  const dy = to.y - from.y;
  const length = Math.sqrt(dx * dx + dy * dy);
  const angle = Math.atan2(dy, dx) * (180 / Math.PI);

  useEffect(() => {
    if (active) {
      // Generate particles when active
      const interval = setInterval(() => {
        setParticles(prev => {
          const newParticles = [...prev, Date.now()];
          // Keep only last 5 particles
          return newParticles.slice(-5);
        });
      }, 300);
      return () => clearInterval(interval);
    } else {
      setParticles([]);
    }
  }, [active]);

  return (
    <div
      className="absolute pointer-events-none"
      style={{
        left: from.x,
        top: from.y,
        width: length,
        height: 3,
        transformOrigin: "0 50%",
        transform: `rotate(${angle}deg)`,
      }}
    >
      {/* Base line - dashed when inactive */}
      <motion.div
        className="absolute inset-0 rounded-full"
        style={{
          background: active ? color : 'transparent',
          borderBottom: active ? 'none' : `2px dashed #001858`,
        }}
        initial={{ scaleX: 0 }}
        animate={{ scaleX: 1 }}
        transition={{ duration: 0.5, delay }}
      />

      {/* Active solid line */}
      {active && (
        <motion.div
          className="absolute inset-0 rounded-full"
          style={{
            background: color,
            height: 3,
          }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
        />
      )}

      {/* Flowing particles */}
      {particles.map((id) => (
        <motion.div
          key={id}
          className="absolute top-1/2 -translate-y-1/2 rounded-full"
          style={{
            width: 12,
            height: 12,
            background: '#f582ae',
            border: '2px solid #001858',
            boxShadow: '2px 2px 0 #001858',
          }}
          initial={{ left: 0, opacity: 1, scale: 1 }}
          animate={{ left: length - 12, opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, ease: "easeInOut" }}
          onAnimationComplete={() => {
            setParticles(prev => prev.filter(p => p !== id));
          }}
        />
      ))}
    </div>
  );
}
