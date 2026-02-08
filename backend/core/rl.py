"""
Reinforcement Learning for negotiation optimization.

Provides:
- NegotiationBandit: Multi-armed bandit for discount selection
- NegotiationStats: Track and analyze negotiation outcomes
"""

import json
import random
from pathlib import Path
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field, asdict


@dataclass
class NegotiationOutcome:
    """Record of a single negotiation."""
    supplier_id: str
    discount_asked: float
    discount_received: float
    decision: str  # ACCEPT, COUNTER, REJECT
    order_value: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class NegotiationBandit:
    """
    Multi-armed bandit for negotiation strategy.

    Each "arm" is a discount percentage to ask for.
    The bandit learns which discount works best for each supplier.

    Uses epsilon-greedy strategy:
    - With probability epsilon: explore (try random discount)
    - With probability 1-epsilon: exploit (use best known discount)
    """

    DISCOUNT_OPTIONS = [5, 10, 15, 20, 25]  # Arms

    def __init__(self, data_path: Optional[Path] = None):
        if data_path is None:
            data_path = Path(__file__).parent.parent / "memory" / "rl_bandit.json"

        self.data_path = data_path
        self.stats = self._load_stats()

    def _load_stats(self) -> dict:
        """Load stats from file or initialize empty."""
        if self.data_path.exists():
            return json.loads(self.data_path.read_text())
        return {}

    def _save_stats(self):
        """Persist stats to file."""
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        self.data_path.write_text(json.dumps(self.stats, indent=2))

    def choose_discount(
        self,
        supplier_id: str,
        epsilon: float = 0.1,
        context: dict = None
    ) -> tuple[float, str]:
        """
        Choose discount to ask for.

        Args:
            supplier_id: Which supplier we're negotiating with
            epsilon: Exploration rate (0.1 = 10% random exploration)
            context: Optional context (order size, urgency, etc.)

        Returns:
            (discount_to_ask, reasoning)
        """
        # Initialize supplier if not seen before
        if supplier_id not in self.stats:
            self.stats[supplier_id] = {
                discount: {"tries": 0, "total_received": 0, "successes": 0}
                for discount in self.DISCOUNT_OPTIONS
            }

        supplier_stats = self.stats[supplier_id]

        # Explore: random discount
        if random.random() < epsilon:
            discount = random.choice(self.DISCOUNT_OPTIONS)
            return discount, f"Exploring: trying {discount}%"

        # Exploit: use best known discount
        # Calculate average result for each discount
        best_discount = None
        best_avg = -1

        for discount, stats in supplier_stats.items():
            if stats["tries"] > 0:
                avg = stats["total_received"] / stats["tries"]
                if avg > best_avg:
                    best_avg = avg
                    best_discount = int(discount)

        if best_discount is None:
            # No data yet, start with middle option
            return 15, "No history, starting with 15%"

        tries = supplier_stats[str(best_discount)]["tries"]
        return best_discount, f"Best known: {best_discount}% (avg result: {best_avg:.1f}% from {tries} tries)"

    def record_outcome(
        self,
        supplier_id: str,
        discount_asked: float,
        discount_received: float,
        decision: str
    ):
        """
        Record negotiation outcome for learning.

        Args:
            supplier_id: Which supplier
            discount_asked: What we asked for
            discount_received: What we actually got
            decision: ACCEPT, COUNTER, or REJECT
        """
        if supplier_id not in self.stats:
            self.stats[supplier_id] = {
                discount: {"tries": 0, "total_received": 0, "successes": 0}
                for discount in self.DISCOUNT_OPTIONS
            }

        key = str(int(discount_asked))
        if key not in self.stats[supplier_id]:
            self.stats[supplier_id][key] = {"tries": 0, "total_received": 0, "successes": 0}

        stats = self.stats[supplier_id][key]
        stats["tries"] += 1
        stats["total_received"] += discount_received

        if decision == "ACCEPT":
            stats["successes"] += 1

        self._save_stats()

    def get_supplier_insights(self, supplier_id: str) -> dict:
        """
        Get learned insights about a supplier.

        Returns analysis like:
        {
            "best_discount_to_ask": 15,
            "expected_result": 8.0,
            "max_seen": 8,
            "recommendation": "Ask 15%, expect counter at 8%"
        }
        """
        if supplier_id not in self.stats:
            return {"status": "no_data", "recommendation": "No negotiation history"}

        supplier_stats = self.stats[supplier_id]

        # Find best performing discount
        best_discount = None
        best_avg = -1
        max_received = 0

        for discount, stats in supplier_stats.items():
            if stats["tries"] > 0:
                avg = stats["total_received"] / stats["tries"]
                if avg > best_avg:
                    best_avg = avg
                    best_discount = int(discount)
                # Track max ever received
                if stats["total_received"] > 0:
                    max_received = max(max_received, stats["total_received"] / stats["tries"])

        if best_discount is None:
            return {"status": "no_data", "recommendation": "No negotiation history"}

        total_negotiations = sum(s["tries"] for s in supplier_stats.values())

        return {
            "total_negotiations": total_negotiations,
            "best_discount_to_ask": best_discount,
            "expected_result": round(best_avg, 1),
            "max_seen": round(max_received, 1),
            "recommendation": f"Ask {best_discount}%, expect ~{best_avg:.0f}%"
        }

    def get_all_insights(self) -> dict:
        """Get insights for all suppliers."""
        return {
            supplier_id: self.get_supplier_insights(supplier_id)
            for supplier_id in self.stats
        }


class NegotiationStats:
    """
    Track detailed negotiation statistics.

    Provides analytics like:
    - Success rate by supplier
    - Average discount by order size
    - Trend over time
    """

    def __init__(self, data_path: Optional[Path] = None):
        if data_path is None:
            data_path = Path(__file__).parent.parent / "memory" / "negotiation_history.json"

        self.data_path = data_path
        self.history = self._load_history()

    def _load_history(self) -> list:
        """Load history from file."""
        if self.data_path.exists():
            return json.loads(self.data_path.read_text())
        return []

    def _save_history(self):
        """Persist history to file."""
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        self.data_path.write_text(json.dumps(self.history, indent=2))

    def record(self, outcome: NegotiationOutcome):
        """Record a negotiation outcome."""
        self.history.append(asdict(outcome))
        self._save_history()

    def get_supplier_stats(self, supplier_id: str) -> dict:
        """Get statistics for a specific supplier."""
        supplier_history = [h for h in self.history if h["supplier_id"] == supplier_id]

        if not supplier_history:
            return {"negotiations": 0}

        total = len(supplier_history)
        accepts = sum(1 for h in supplier_history if h["decision"] == "ACCEPT")
        avg_asked = sum(h["discount_asked"] for h in supplier_history) / total
        avg_received = sum(h["discount_received"] for h in supplier_history) / total
        total_value = sum(h["order_value"] for h in supplier_history)

        return {
            "negotiations": total,
            "accept_rate": round(accepts / total, 2),
            "avg_discount_asked": round(avg_asked, 1),
            "avg_discount_received": round(avg_received, 1),
            "total_order_value": round(total_value, 2),
            "total_savings": round(total_value * avg_received / 100, 2)
        }

    def get_all_stats(self) -> dict:
        """Get statistics for all suppliers."""
        suppliers = set(h["supplier_id"] for h in self.history)
        return {sid: self.get_supplier_stats(sid) for sid in suppliers}


# Singleton instances
bandit = NegotiationBandit()
stats = NegotiationStats()
