"use client";

import { motion } from "framer-motion";
import { ArrowLeft, Github, Linkedin, Coffee, Zap, Brain } from "lucide-react";
import Link from "next/link";

export default function AboutPage() {
  return (
    <div className="min-h-screen" style={{ background: "#fef6e4" }}>
      {/* Header */}
      <header style={{ borderBottom: "2px solid #001858" }}>
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <Link
            href="/"
            className="flex items-center gap-2 text-sm font-medium px-4 py-2 rounded-lg transition-all hover:-translate-y-0.5"
            style={{
              color: "#001858",
              border: "2px solid #001858",
            }}
          >
            <ArrowLeft className="w-4 h-4" />
            Back to MURA
          </Link>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-12 sm:py-20">
        {/* Hero Card */}
        <motion.div
          className="rounded-2xl sm:rounded-3xl p-6 sm:p-10 text-center"
          style={{
            background: "#f3d2c1",
            border: "3px solid #001858",
            boxShadow: "6px 6px 0 #001858",
          }}
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          {/* Photo */}
          <motion.div
            className="mb-6"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
          >
            <div
              className="w-32 h-32 sm:w-40 sm:h-40 mx-auto rounded-full overflow-hidden"
              style={{
                border: "4px solid #001858",
                boxShadow: "4px 4px 0 #001858",
              }}
            >
              <img
                src="/founder.jpg"
                alt="Mo Kandil"
                className="w-full h-full object-cover"
              />
            </div>
          </motion.div>

          {/* Name & Title */}
          <motion.h1
            className="text-2xl sm:text-4xl font-bold mb-2"
            style={{ color: "#001858" }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
          >
            Mo k
          </motion.h1>

          <motion.div
            className="inline-block rounded-full px-4 py-2 mb-6"
            style={{
              background: "#f582ae",
              border: "2px solid #001858",
              boxShadow: "2px 2px 0 #001858",
            }}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.4 }}
          >
            <p
              className="text-sm sm:text-base font-bold"
              style={{ color: "#001858" }}
            >
              Chief Supply Chain Officer
            </p>
          </motion.div>

          {/* Funny Tagline */}
          <motion.div
            className="rounded-xl px-6 py-4 mb-8 max-w-md mx-auto"
            style={{
              background: "#8bd3dd",
              border: "2px solid #001858",
              boxShadow: "3px 3px 0 #001858",
            }}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.5 }}
          >
            <p
              className="text-base sm:text-lg font-bold"
              style={{ color: "#001858" }}
            >
              Hacked this in 7 hours
            </p>
            <p className="text-sm" style={{ color: "#172c66" }}>
              (approximately 20 vibecodes)
            </p>
          </motion.div>

          {/* Bio */}
          <motion.div
            className="max-w-lg mx-auto space-y-4 text-left"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
          >
            <div
              className="rounded-xl p-4"
              style={{ background: "#fef6e4", border: "2px solid #001858" }}
            >
              <div className="flex items-start gap-3">
                <Brain
                  className="w-5 h-5 mt-0.5 flex-shrink-0"
                  style={{ color: "#f582ae" }}
                />
                <p
                  className="text-sm sm:text-base"
                  style={{ color: "#172c66" }}
                >
                  Student @{" "}
                  <strong style={{ color: "#001858" }}>TU Munich</strong>,
                  pursuing Computer Science & minor in Entrepreneurship.
                  Probably debugging code instead of attending lectures!
                </p>
              </div>
            </div>

            <div
              className="rounded-xl p-4"
              style={{ background: "#fef6e4", border: "2px solid #001858" }}
            >
              <div className="flex items-start gap-3">
                <Coffee
                  className="w-5 h-5 mt-0.5 flex-shrink-0"
                  style={{ color: "#f582ae" }}
                />
                <p
                  className="text-sm sm:text-base"
                  style={{ color: "#172c66" }}
                >
                  Runs on <strong style={{ color: "#001858" }}>Matcha</strong>,{" "}
                  <strong style={{ color: "#001858" }}>koshari</strong>, and an
                  unhealthy amount of Claude API credits.
                </p>
              </div>
            </div>

            <div
              className="rounded-xl p-4"
              style={{ background: "#fef6e4", border: "2px solid #001858" }}
            >
              <div className="flex items-start gap-3">
                <Zap
                  className="w-5 h-5 mt-0.5 flex-shrink-0"
                  style={{ color: "#f582ae" }}
                />
                <p
                  className="text-sm sm:text-base"
                  style={{ color: "#172c66" }}
                >
                  Built MURA for{" "}
                  <strong style={{ color: "#001858" }}>
                    HackNation Feb 2026
                  </strong>
                  . May or may not have tested this during a Systems Programming
                  lecture.
                </p>
              </div>
            </div>
          </motion.div>

          {/* Social Links */}
          <motion.div
            className="flex justify-center gap-4 mt-8"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7 }}
          >
            <a
              href="https://github.com/mohanadkandil"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-4 py-2 rounded-xl font-semibold transition-transform hover:-translate-y-1"
              style={{
                background: "#001858",
                color: "#fef6e4",
                border: "2px solid #001858",
                boxShadow: "3px 3px 0 #f582ae",
              }}
            >
              <Github className="w-4 h-4" />
              GitHub
            </a>
            <a
              href="https://linkedin.com/in/mohanadkandil"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-4 py-2 rounded-xl font-semibold transition-transform hover:-translate-y-1"
              style={{
                background: "#8bd3dd",
                color: "#001858",
                border: "2px solid #001858",
                boxShadow: "3px 3px 0 #001858",
              }}
            >
              <Linkedin className="w-4 h-4" />
              LinkedIn
            </a>
          </motion.div>
        </motion.div>

        {/* Fun Footer */}
        <motion.p
          className="text-center text-sm mt-8"
          style={{ color: "#172c66", opacity: 0.6 }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 0.6 }}
          transition={{ delay: 0.8 }}
        >
          If this breaks, just refresh. It is a hackathon project after all.
        </motion.p>
      </main>
    </div>
  );
}
