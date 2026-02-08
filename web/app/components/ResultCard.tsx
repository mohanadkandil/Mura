"use client";

import { motion } from "framer-motion";
import {
  CheckCircle,
  Package,
  Truck,
  Clock,
  DollarSign,
  AlertTriangle,
  ArrowRight
} from "lucide-react";

interface ResultCardProps {
  recommendation: {
    supplier: string;
    total: number;
    shipping: number;
    days: number;
    compliance: "passed" | "warning" | "failed";
    reasoning: string;
  } | null;
  visible: boolean;
}

export function ResultCard({ recommendation, visible }: ResultCardProps) {
  if (!recommendation) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 50, scale: 0.9 }}
      animate={visible ? { opacity: 1, y: 0, scale: 1 } : { opacity: 0, y: 50, scale: 0.9 }}
      transition={{ type: "spring", stiffness: 200, damping: 20 }}
      className="rounded-2xl p-6 max-w-2xl mx-auto"
      style={{
        background: '#fef6e4',
        border: '3px solid #001858',
        boxShadow: '6px 6px 0 #001858',
      }}
    >
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <motion.div
          className="w-14 h-14 rounded-full flex items-center justify-center"
          style={{
            background: '#22c55e',
            border: '3px solid #001858',
            boxShadow: '3px 3px 0 #001858',
          }}
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2, type: "spring" }}
        >
          <CheckCircle className="w-7 h-7" style={{ color: '#fff' }} />
        </motion.div>
        <div>
          <h3 className="text-xl font-bold" style={{ color: '#001858' }}>Recommendation Ready</h3>
          <p className="text-sm" style={{ color: '#172c66' }}>Best option found for your request</p>
        </div>
      </div>

      {/* Main recommendation */}
      <motion.div
        className="rounded-xl p-5 mb-6"
        style={{
          background: '#8bd3dd',
          border: '2px solid #001858',
          boxShadow: '3px 3px 0 #001858',
        }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
      >
        <div className="flex items-center gap-2 mb-4">
          <Package className="w-5 h-5" style={{ color: '#001858' }} />
          <span className="text-lg font-bold" style={{ color: '#001858' }}>{recommendation.supplier}</span>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div
            className="text-center p-3 rounded-lg"
            style={{ background: '#fef6e4', border: '2px solid #001858' }}
          >
            <div className="text-2xl font-bold" style={{ color: '#001858' }}>
              EUR{recommendation.total}
            </div>
            <div className="text-xs flex items-center justify-center gap-1 mt-1" style={{ color: '#172c66' }}>
              <DollarSign className="w-3 h-3" /> Total Cost
            </div>
          </div>
          <div
            className="text-center p-3 rounded-lg"
            style={{ background: '#fef6e4', border: '2px solid #001858' }}
          >
            <div className="text-2xl font-bold" style={{ color: '#001858' }}>
              EUR{recommendation.shipping}
            </div>
            <div className="text-xs flex items-center justify-center gap-1 mt-1" style={{ color: '#172c66' }}>
              <Truck className="w-3 h-3" /> Shipping
            </div>
          </div>
          <div
            className="text-center p-3 rounded-lg"
            style={{ background: '#fef6e4', border: '2px solid #001858' }}
          >
            <div className="text-2xl font-bold" style={{ color: '#001858' }}>
              {recommendation.days}
            </div>
            <div className="text-xs flex items-center justify-center gap-1 mt-1" style={{ color: '#172c66' }}>
              <Clock className="w-3 h-3" /> Days
            </div>
          </div>
        </div>
      </motion.div>

      {/* Compliance status */}
      <motion.div
        className="flex items-center gap-2 px-4 py-3 rounded-xl mb-4"
        style={{
          background: recommendation.compliance === "passed" ? '#22c55e' :
            recommendation.compliance === "warning" ? '#f59e0b' : '#ef4444',
          border: '2px solid #001858',
          boxShadow: '2px 2px 0 #001858',
        }}
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.4 }}
      >
        {recommendation.compliance === "passed" ? (
          <CheckCircle className="w-5 h-5" style={{ color: '#fff' }} />
        ) : (
          <AlertTriangle className="w-5 h-5" style={{ color: '#001858' }} />
        )}
        <span className="text-sm font-semibold" style={{ color: recommendation.compliance === "passed" ? '#fff' : '#001858' }}>
          Compliance: {recommendation.compliance === "passed" ? "All checks passed" : "Review required"}
        </span>
      </motion.div>

      {/* Reasoning */}
      <motion.div
        className="text-sm leading-relaxed mb-6 p-4 rounded-xl"
        style={{
          background: '#f3d2c1',
          border: '2px solid #001858',
          color: '#172c66',
        }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
      >
        <span className="font-bold" style={{ color: '#001858' }}>Why: </span>
        {recommendation.reasoning}
      </motion.div>

      {/* Actions */}
      <motion.div
        className="flex gap-3"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
      >
        <button
          className="flex-1 py-4 px-6 rounded-xl font-bold flex items-center justify-center gap-2 transition-transform hover:-translate-x-0.5 hover:-translate-y-0.5 active:translate-x-0.5 active:translate-y-0.5"
          style={{
            background: '#f582ae',
            color: '#001858',
            border: '3px solid #001858',
            boxShadow: '4px 4px 0 #001858',
          }}
        >
          Accept & Order
          <ArrowRight className="w-5 h-5" />
        </button>
        <button
          className="px-6 py-4 rounded-xl font-semibold transition-colors"
          style={{
            background: 'transparent',
            color: '#001858',
            border: '2px solid #001858',
          }}
        >
          Compare All
        </button>
      </motion.div>
    </motion.div>
  );
}
