from typing import Optional
from core.protocol import AgentFacts, AgentRole


class AgentRegistry:
    """
    NANDA-style agent registry. A phonebook for agents.
    In-memory dict — no database needed for hackathon.
    """

    def __init__(self):
        self._agents: dict[str, AgentFacts] = {}

    def register(self, agent: AgentFacts) -> str:
        """Register agent, return agent_id."""
        self._agents[agent.agent_id] = agent
        return agent.agent_id

    def get(self, agent_id: str) -> Optional[AgentFacts]:
        """Lookup agent by ID."""
        return self._agents.get(agent_id)

    def unregister(self, agent_id: str) -> bool:
        """Remove agent from registry."""
        if agent_id in self._agents:
            del self._agents[agent_id]
            return True
        return False

    def get_all(self) -> list[AgentFacts]:
        """Return all registered agents."""
        return list(self._agents.values())

    def discover(
        self,
        role: Optional[AgentRole] = None,
        capability: Optional[str] = None,
        region: Optional[str] = None,
        min_trust: float = 0.0,
    ) -> list[AgentFacts]:
        """
        Search agents by criteria, ranked by trust score.

        Ranking formula from spec:
        trust(35%) × capability_match(40%) × speed(15%) × reliability(10%)

        Simplified for discovery: just rank by reputation_score descending.
        """
        results = []

        for agent in self._agents.values():
            # Filter by role
            if role is not None and agent.role != role:
                continue

            # Filter by capability (substring match)
            if capability is not None:
                cap_lower = capability.lower()
                if not any(cap_lower in c.lower() for c in agent.capabilities):
                    continue

            # Filter by region (substring match)
            if region is not None:
                region_lower = region.lower()
                if region_lower not in agent.region.lower() and region_lower not in agent.country.lower():
                    continue

            # Filter by minimum trust
            if agent.trust.reputation_score < min_trust:
                continue

            results.append(agent)

        # Rank by trust score (descending)
        results.sort(key=lambda a: a.trust.reputation_score, reverse=True)

        return results

    def verify(self, agent_id: str) -> dict:
        """
        Return trust verification info for an agent.
        Three layers: identity, capability attestation, reputation.
        """
        agent = self.get(agent_id)
        if agent is None:
            return {"verified": False, "error": "Agent not found"}

        return {
            "verified": agent.trust.verified,
            "agent_id": agent.agent_id,
            "name": agent.name,
            "identity": {
                "domain_verified": agent.trust.verified,
                "endpoint": agent.endpoint,
            },
            "capability_attestation": {
                "self_declared": agent.capabilities,
                "certifications": [c.model_dump() for c in agent.certifications],
            },
            "reputation": {
                "score": agent.trust.reputation_score,
                "total_transactions": agent.trust.total_transactions,
                "dispute_rate": agent.trust.dispute_rate,
            },
        }

    def rank_for_rfq(
        self,
        agents: list[AgentFacts],
        deadline_days: int = 7,
        budget_weight: float = 0.3,
    ) -> list[tuple[AgentFacts, float]]:
        """
        Rank agents for an RFQ considering deadline constraints.

        Returns list of (agent, score) tuples.
        Agents that can't meet deadline get score penalty.

        Formula:
        score = trust(35%) + speed_fit(25%) + reliability(20%) + price_tier(20%)
        """
        scored = []

        for agent in agents:
            # Trust component (35%)
            trust_score = agent.trust.reputation_score * 0.35

            # Speed fit (25%) - penalize if lead time exceeds deadline
            if agent.avg_lead_time_days <= deadline_days:
                speed_score = 0.25
            else:
                # Penalty proportional to how much over deadline
                overage = agent.avg_lead_time_days - deadline_days
                speed_score = max(0, 0.25 - (overage * 0.05))

            # Reliability (20%) - inverse of dispute rate
            reliability_score = (1 - agent.trust.dispute_rate) * 0.20

            # Transaction history bonus (20%) - more transactions = more trusted
            tx_score = min(agent.trust.total_transactions / 100, 1.0) * 0.20

            total = trust_score + speed_score + reliability_score + tx_score
            scored.append((agent, round(total, 3)))

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    def __len__(self) -> int:
        return len(self._agents)

    def __contains__(self, agent_id: str) -> bool:
        return agent_id in self._agents


# Singleton instance for the application
registry = AgentRegistry()
