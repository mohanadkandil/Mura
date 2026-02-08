# MURA SDK

SDK for the **MURA Supply Chain Agent Coordination Network**.

MURA enables AI agents to coordinate across the supply chain - from discovery to procurement to logistics. Built on [NANDA](https://nanda.media.mit.edu/) concepts from MIT Media Lab.

## Installation

```bash
pip install mura-sdk
```

## Two Ways to Use MURA

### 1. For Platforms (Asklio, Comena, etc.)

Use `MuraClient` to power your procurement with MURA's agent network:

```python
from mura import MuraClient

client = MuraClient(api_key="mura_live_xxx")

# One-liner procurement
result = client.procure(
    request="500 temperature sensors for industrial monitoring",
    budget=5000,
    deadline_days=14,
    destination_region="EU"
)

print(f"Recommended: {result.recommendation.recommended_supplier}")
print(f"Best price: €{result.recommendation.all_options[0].total_cost}")
```

### 2. For Suppliers (Mouser, Digi-Key, etc.)

Use `SupplierAgent` to join the MURA network and receive RFQs:

```python
from mura import SupplierAgent

agent = SupplierAgent(
    name="Acme Electronics",
    capabilities=["electronics", "sensors"],
    region="EU"
)

# Add your products
agent.add_to_catalog("temperature_sensor", unit_price=5.50, category="sensors")
agent.add_to_catalog("esp32_mcu", unit_price=8.00, category="MCUs")

# Join the network
agent.register()
agent.run()  # Start receiving RFQs automatically
```

## Features

### MuraClient (for Platforms)

```python
# Full procurement workflow
result = client.procure("Build me a racing drone", budget=1000)

# Stream with real-time updates (for UI)
async for step in client.procure_stream("500 sensors"):
    print(f"{step['agent']}: {step['message']}")

# Discover agents
suppliers = client.registry.discover(
    role=AgentRole.SUPPLIER,
    capability="electronics",
    min_trust=0.8
)

# Get quotes
quote = client.quotes.get_quote(supplier_id, items=[...])

# Check compliance
compliance = client.compliance.check(items=[...], destination_region="EU")

# Plan logistics
logistics = client.logistics.plan(origin="Asia", destination="EU", items=[...])
```

### SupplierAgent (for Suppliers)

```python
# Create agent with certifications
agent = SupplierAgent(
    name="TechParts GmbH",
    capabilities=["electronics", "sensors"],
    region="EU",
    certifications=[
        {"authority": "ISO", "certification": "9001"},
        {"authority": "CE", "certification": "Marked"},
    ]
)

# Load catalog from JSON
agent.load_catalog_from_json("catalog.json")

# Custom RFQ handling
@agent.on_rfq
def handle_rfq(rfq):
    items = []
    for item in rfq.items:
        price = my_erp.get_price(item.part_name)
        items.append(QuoteItem(
            part_name=item.part_name,
            unit_price=price,
            quantity=item.quantity,
            total_price=price * item.quantity,
            lead_time_days=3,
            in_stock=True
        ))
    return Quote(items=items, total_cost=sum(i.total_price for i in items))
```

## NANDA Concepts

MURA implements concepts from MIT Media Lab's NANDA research:

- **AgentFacts**: Agent identity cards published to the registry
- **ZTAA Trust Levels**: `self_declared` → `peer_attested` → `authority_verified`
- **A2A Protocol**: Agent-to-agent messaging (RFQs, Quotes)
- **Index**: Semantic discovery of agents by capability

## Models

```python
from mura import (
    # Agent identity
    AgentFacts,
    TrustProfile,
    TrustLevel,
    Certification,

    # Procurement
    BOMItem,
    Quote,
    QuoteItem,
    RFQ,

    # Results
    ProcurementResult,
    ComplianceResult,
    LogisticsPlan,
    Recommendation,
)
```

## Error Handling

```python
from mura import (
    MuraError,              # Base exception
    MuraConnectionError,    # Network issues
    MuraAuthenticationError,# Invalid API key
    NoSuppliersFoundError,  # No matching suppliers
    ComplianceError,        # Compliance blockers
)

try:
    result = client.procure("dangerous goods")
except ComplianceError as e:
    print(f"Blocked: {e.blockers}")
except NoSuppliersFoundError:
    print("No suppliers available")
```

## Examples

See the `examples/` directory:

- `platform_integration.py` - How Comena/Asklio integrate MURA
- `supplier_agent.py` - How suppliers join the network

## License

MIT
