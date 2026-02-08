# MURA

**Agent Coordination Network for Supply Chain Automation**

MURA is infrastructure for agent-to-agent coordination in supply chains. Instead of humans manually orchestrating procurement, software agents handle discovery, quoting, compliance, and logistics autonomously.

Built for HackNation Feb 2026.

## What It Does

You send a natural language request like:

```
Build me a 5-inch FPV racing drone, budget €500, deliver to Germany
```

MURA orchestrates everything:

1. Generates a Bill of Materials from your request
2. Discovers capable suppliers from the registry
3. Requests quotes from multiple suppliers in parallel
4. Runs compliance checks (EU regulations, export controls, certifications)
5. Plans logistics and shipping routes
6. Returns ranked recommendations with pricing

A procurement workflow that used to take weeks now completes in seconds.

## Architecture

```
                         MURA NETWORK
                              |
     -------------------------+-------------------------
     |                        |                        |
 PLATFORMS              AGENT REGISTRY             SUPPLIERS
 (Your App)              (AgentFacts)            (25+ Agents)
     |                        |                        |
     +------------------------+------------------------+
                              |
                      MURA ORCHESTRATOR
                              |
          +-------------------+-------------------+
          |                   |                   |
     COMPLIANCE           LOGISTICS            QUOTES
       AGENT               AGENT             (parallel)
```

The system is built on concepts from NANDA (MIT Media Lab):

- **AgentFacts**: Structured identity cards for agents (capabilities, certifications, trust scores)
- **A2A Protocol**: Standardized agent communication (RFQ, Quote, Negotiate, Trust Update)
- **ZTAA**: Zero Trust Agent Architecture where trust is earned through successful transactions

## Project Structure

```
mura/
├── backend/                 # FastAPI backend
│   ├── agents/              # LangGraph agents
│   │   ├── orchestrator.py  # Main coordination logic
│   │   ├── supplier_agent.py
│   │   ├── compliance_agent.py
│   │   └── logistics_agent.py
│   ├── core/                # Registry, memory, RL
│   ├── data/                # Supplier catalogs
│   └── main.py              # API endpoints
├── web/                     # Next.js frontend
│   ├── app/
│   │   ├── page.tsx         # Main interface
│   │   ├── docs/            # SDK documentation
│   │   └── api/             # API routes
│   └── components/          # Agent network visualization
├── sdk/                     # Python SDK (pip install mura-sdk)
│   ├── mura/
│   │   ├── client.py        # MuraClient for platforms
│   │   └── supplier.py      # SupplierAgent for suppliers
│   └── examples/
└── TECHNICAL_REPORT.pdf     # One-page technical overview
```

## Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
# or with uv: uv sync

# Set your OpenAI API key
export OPENAI_API_KEY=sk-...

uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd web
bun install  # or npm install
bun dev      # or npm run dev
```

Open http://localhost:3000

### SDK

```bash
pip install mura-sdk
```

```python
from mura import MuraClient

client = MuraClient(base_url="https://mura-production.up.railway.app")

result = client.procure(
    request="Build me a racing drone",
    budget=500,
    destination_region="EU"
)

print(result["recommendation"])
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/procure` | POST | Full procurement workflow |
| `/procure/stream` | POST | SSE streaming procurement |
| `/quote` | POST | Get quote from specific supplier |
| `/compliance` | POST | Run compliance check |
| `/logistics` | POST | Calculate shipping options |
| `/registry/agents` | GET | List all registered agents |
| `/registry/discover` | POST | Find agents by criteria |

## Suppliers

The registry includes 25+ suppliers across:

- Drone components (motors, ESCs, frames, FPV gear)
- Electronics (sensors, microcontrollers, displays)
- Mechanical (motors, bearings, CNC parts)
- Keyboards (switches, keycaps, PCBs)
- 3D Printing (filament, hotends, beds)
- Solar and EV components
- Medical grade parts

Each supplier has:
- Catalog with real pricing
- Trust score and transaction history
- Certifications (ISO, CE, FDA, etc.)
- Lead times and regional availability

## Tech Stack

- **Backend**: FastAPI, LangGraph, Claude/GPT
- **Frontend**: Next.js 15, React 19, TailwindCSS
- **SDK**: Python, Pydantic, httpx
- **Streaming**: Server-Sent Events (SSE)

## Links

- **GitHub**: https://github.com/mohanadkandil/Mura
- **PyPI**: https://pypi.org/project/mura-sdk
- **API**: https://mura-production.up.railway.app

## Author

Mohanad Kandil
mohanadmkandil@gmail.com
