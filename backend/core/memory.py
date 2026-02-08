"""
Memory system for supply chain agents.

Provides:
- Supplier memory (negotiation history, performance)
- Buyer memory (preferences, order history)
- Learned insights (patterns discovered over time)
- Session logs (daily activity)
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional


class SupplyChainMemory:
    """
    Persistent memory for supply chain agents.

    Structure:
        memory/
        ├── INSIGHTS.md              # Long-term learned patterns
        ├── suppliers/
        │   ├── techparts-global.md  # Per-supplier history
        │   └── shenzhen-tech.md
        ├── buyers/
        │   └── buyer-001.md         # Per-buyer preferences
        └── sessions/
            └── 2024-02-07.md        # Daily activity log
    """

    def __init__(self, workspace: Optional[Path] = None):
        if workspace is None:
            workspace = Path(__file__).parent.parent

        self.workspace = workspace
        self.memory_dir = workspace / "memory"
        self.suppliers_dir = self.memory_dir / "suppliers"
        self.buyers_dir = self.memory_dir / "buyers"
        self.sessions_dir = self.memory_dir / "sessions"

        # Ensure directories exist
        self._ensure_dirs()

    def _ensure_dirs(self):
        """Create memory directories if they don't exist."""
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.suppliers_dir.mkdir(parents=True, exist_ok=True)
        self.buyers_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    # =========================================================================
    # SUPPLIER MEMORY
    # =========================================================================

    def get_supplier_memory(self, supplier_id: str) -> str:
        """Get all memory about a supplier."""
        file = self.suppliers_dir / f"{supplier_id}.md"
        if file.exists():
            return file.read_text(encoding="utf-8")
        return ""

    def record_supplier_interaction(
        self,
        supplier_id: str,
        interaction_type: str,
        result: dict,
        notes: str = ""
    ):
        """
        Record an interaction with a supplier.

        Args:
            supplier_id: e.g., "techparts-global"
            interaction_type: "negotiation", "quote", "delivery", etc.
            result: Outcome data
            notes: Optional notes
        """
        file = self.suppliers_dir / f"{supplier_id}.md"

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        entry = f"""
### {timestamp} - {interaction_type.upper()}
- Result: {json.dumps(result, indent=2)}
- Notes: {notes}
"""

        if file.exists():
            content = file.read_text(encoding="utf-8") + entry
        else:
            header = f"# Supplier: {supplier_id}\n\n## Interaction History\n"
            content = header + entry

        file.write_text(content, encoding="utf-8")

    def record_negotiation(
        self,
        supplier_id: str,
        discount_asked: float,
        discount_received: float,
        decision: str,
        order_value: float
    ):
        """Convenience method for recording negotiations."""
        self.record_supplier_interaction(
            supplier_id=supplier_id,
            interaction_type="negotiation",
            result={
                "discount_asked": discount_asked,
                "discount_received": discount_received,
                "decision": decision,
                "order_value": order_value
            }
        )

    def record_delivery(
        self,
        supplier_id: str,
        order_id: str,
        expected_days: int,
        actual_days: int,
        quality_ok: bool
    ):
        """Record delivery performance."""
        on_time = actual_days <= expected_days

        self.record_supplier_interaction(
            supplier_id=supplier_id,
            interaction_type="delivery",
            result={
                "order_id": order_id,
                "expected_days": expected_days,
                "actual_days": actual_days,
                "on_time": on_time,
                "quality_ok": quality_ok
            },
            notes="Late delivery" if not on_time else ""
        )

    # =========================================================================
    # BUYER MEMORY
    # =========================================================================

    def get_buyer_memory(self, buyer_id: str) -> str:
        """Get all memory about a buyer."""
        file = self.buyers_dir / f"{buyer_id}.md"
        if file.exists():
            return file.read_text(encoding="utf-8")
        return ""

    def record_buyer_preference(self, buyer_id: str, preference: str, value: str):
        """
        Record a learned buyer preference.

        Example:
            record_buyer_preference("buyer-001", "preferred_region", "EU")
            record_buyer_preference("buyer-001", "price_sensitivity", "high")
        """
        file = self.buyers_dir / f"{buyer_id}.md"

        timestamp = datetime.now().strftime("%Y-%m-%d")
        entry = f"- [{timestamp}] {preference}: {value}\n"

        if file.exists():
            content = file.read_text(encoding="utf-8")
            # Check if preferences section exists
            if "## Preferences" not in content:
                content += "\n## Preferences\n"
            content += entry
        else:
            content = f"# Buyer: {buyer_id}\n\n## Preferences\n{entry}"

        file.write_text(content, encoding="utf-8")

    def record_buyer_order(self, buyer_id: str, order: dict):
        """Record a buyer's order."""
        file = self.buyers_dir / f"{buyer_id}.md"

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = f"""
### {timestamp} - ORDER
- Supplier: {order.get('supplier_id', 'unknown')}
- Items: {order.get('items', [])}
- Total: €{order.get('total', 0)}
- Deadline: {order.get('deadline_days', 'N/A')} days
"""

        if file.exists():
            content = file.read_text(encoding="utf-8")
            if "## Order History" not in content:
                content += "\n## Order History\n"
            content += entry
        else:
            content = f"# Buyer: {buyer_id}\n\n## Order History\n{entry}"

        file.write_text(content, encoding="utf-8")

    # =========================================================================
    # INSIGHTS (Long-term learned patterns)
    # =========================================================================

    def get_insights(self) -> str:
        """Get all learned insights."""
        file = self.memory_dir / "INSIGHTS.md"
        if file.exists():
            return file.read_text(encoding="utf-8")
        return ""

    def add_insight(self, insight: str, category: str = "general"):
        """
        Add a learned insight.

        Example:
            add_insight("ShenzhenTech always gives max 25% discount", "negotiation")
            add_insight("TechParts never goes above 8%", "negotiation")
        """
        file = self.memory_dir / "INSIGHTS.md"

        timestamp = datetime.now().strftime("%Y-%m-%d")
        entry = f"- [{timestamp}] [{category}] {insight}\n"

        if file.exists():
            content = file.read_text(encoding="utf-8") + entry
        else:
            content = "# Learned Insights\n\n" + entry

        file.write_text(content, encoding="utf-8")

    # =========================================================================
    # SESSION LOGS (Daily activity)
    # =========================================================================

    def get_today_log(self) -> str:
        """Get today's session log."""
        today = datetime.now().strftime("%Y-%m-%d")
        file = self.sessions_dir / f"{today}.md"
        if file.exists():
            return file.read_text(encoding="utf-8")
        return ""

    def log_activity(self, activity: str):
        """Log an activity to today's session."""
        today = datetime.now().strftime("%Y-%m-%d")
        file = self.sessions_dir / f"{today}.md"

        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"- {timestamp}: {activity}\n"

        if file.exists():
            content = file.read_text(encoding="utf-8") + entry
        else:
            content = f"# Session Log: {today}\n\n{entry}"

        file.write_text(content, encoding="utf-8")

    def get_recent_logs(self, days: int = 7) -> str:
        """Get logs from the last N days."""
        logs = []
        today = datetime.now().date()

        for i in range(days):
            date = today - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            file = self.sessions_dir / f"{date_str}.md"

            if file.exists():
                logs.append(file.read_text(encoding="utf-8"))

        return "\n\n---\n\n".join(logs)

    # =========================================================================
    # CONTEXT FOR AGENTS
    # =========================================================================

    def get_negotiation_context(self, supplier_id: str, buyer_id: str = None) -> str:
        """
        Get relevant memory context for a negotiation.

        This is injected into the agent's prompt.
        """
        parts = []

        # Supplier history
        supplier_mem = self.get_supplier_memory(supplier_id)
        if supplier_mem:
            parts.append(f"## Supplier History: {supplier_id}\n{supplier_mem}")

        # Buyer preferences
        if buyer_id:
            buyer_mem = self.get_buyer_memory(buyer_id)
            if buyer_mem:
                parts.append(f"## Buyer Context: {buyer_id}\n{buyer_mem}")

        # Key insights
        insights = self.get_insights()
        if insights:
            parts.append(f"## Key Insights\n{insights}")

        return "\n\n".join(parts) if parts else "No prior history."

    def get_proactive_suggestions(self, buyer_id: str) -> list[dict]:
        """
        Analyze buyer history and generate proactive suggestions.

        Returns list of suggestions like:
        [
            {"type": "cost_saving", "message": "Switch motors to ShenzhenTech, save 40%"},
            {"type": "risk", "message": "ShenzhenTech late 28% of time, consider backup"},
        ]
        """
        # This would analyze patterns in memory
        # For now, return based on static analysis
        # In production, this would query the memory files and compute insights

        suggestions = []

        buyer_mem = self.get_buyer_memory(buyer_id)

        # Example logic (would be more sophisticated in production)
        if "techparts" in buyer_mem.lower() and "motor" in buyer_mem.lower():
            suggestions.append({
                "type": "cost_saving",
                "message": "You've been ordering motors from TechParts at €45. ShenzhenTech offers same spec at €22 (51% savings).",
                "action": "Consider ShenzhenTech for non-urgent motor orders"
            })

        return suggestions


# Singleton instance
memory = SupplyChainMemory()
