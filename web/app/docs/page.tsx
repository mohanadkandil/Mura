"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Highlight, themes } from "prism-react-renderer";
import {
  Copy,
  Check,
  ChevronRight,
  Book,
  Code2,
  Boxes,
  Users,
  ArrowRight,
  Github,
  Sparkles,
} from "lucide-react";

type NavItem = {
  title: string;
  href: string;
  icon?: React.ReactNode;
  items?: { title: string; href: string }[];
};

const navigation: NavItem[] = [
  {
    title: "Getting Started",
    href: "#getting-started",
    icon: <Book className="w-4 h-4" />,
    items: [
      { title: "Introduction", href: "#introduction" },
      { title: "Installation", href: "#installation" },
      { title: "Quick Start", href: "#quickstart" },
    ],
  },
  {
    title: "MuraClient",
    href: "#mura-client",
    icon: <Boxes className="w-4 h-4" />,
    items: [
      { title: "Overview", href: "#client-overview" },
      { title: "procure()", href: "#procure" },
      { title: "procure_stream()", href: "#procure-stream" },
      { title: "registry", href: "#registry" },
      { title: "quotes", href: "#quotes" },
      { title: "compliance", href: "#compliance" },
      { title: "logistics", href: "#logistics" },
    ],
  },
  {
    title: "SupplierAgent",
    href: "#supplier-agent",
    icon: <Users className="w-4 h-4" />,
    items: [
      { title: "Overview", href: "#supplier-overview" },
      { title: "Catalog Management", href: "#catalog" },
      { title: "RFQ Handler", href: "#rfq-handler" },
    ],
  },
  {
    title: "Reference",
    href: "#reference",
    icon: <Code2 className="w-4 h-4" />,
    items: [
      { title: "Models", href: "#models" },
      { title: "Enums", href: "#enums" },
      { title: "Errors", href: "#errors" },
    ],
  },
];

export default function DocsPage() {
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [activeSection, setActiveSection] = useState("introduction");
  const [expandedNav, setExpandedNav] = useState<string[]>(["Getting Started", "MuraClient", "SupplierAgent", "Reference"]);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveSection(entry.target.id);
          }
        });
      },
      { rootMargin: "-100px 0px -66%" }
    );

    document.querySelectorAll("section[id]").forEach((section) => {
      observer.observe(section);
    });

    return () => observer.disconnect();
  }, []);

  const copyCode = (code: string, id: string) => {
    navigator.clipboard.writeText(code);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const toggleNav = (title: string) => {
    setExpandedNav((prev) =>
      prev.includes(title)
        ? prev.filter((t) => t !== title)
        : [...prev, title]
    );
  };

  return (
    <div className="min-h-screen bg-[#fef6e4]">
      {/* Top Navigation */}
      <header className="sticky top-0 z-50 bg-[#fef6e4]/95 backdrop-blur-sm border-b-2 border-[#001858]">
        <div className="max-w-[1400px] mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link href="/" className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-[#f582ae] border-2 border-[#001858] flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-[#001858]" />
              </div>
              <span className="font-bold text-[#001858] text-lg">MURA</span>
            </Link>
            <nav className="hidden md:flex items-center gap-1">
              <Link
                href="/"
                className="px-3 py-2 text-sm font-medium text-[#172c66] hover:text-[#001858] hover:bg-[#f3d2c1] rounded-lg transition-colors"
              >
                Demo
              </Link>
              <Link
                href="/registry"
                className="px-3 py-2 text-sm font-medium text-[#172c66] hover:text-[#001858] hover:bg-[#f3d2c1] rounded-lg transition-colors"
              >
                Registry
              </Link>
              <Link
                href="/docs"
                className="px-3 py-2 text-sm font-medium text-[#001858] bg-[#f3d2c1] rounded-lg"
              >
                SDK Docs
              </Link>
            </nav>
          </div>
          <div className="flex items-center gap-4">
            <a
              href="https://github.com/mura-network"
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 text-[#172c66] hover:text-[#001858] hover:bg-[#f3d2c1] rounded-lg transition-colors"
            >
              <Github className="w-5 h-5" />
            </a>
          </div>
        </div>
      </header>

      <div className="max-w-[1400px] mx-auto flex">
        {/* Sidebar */}
        <aside className="hidden lg:block w-64 shrink-0 sticky top-16 h-[calc(100vh-64px)] overflow-y-auto border-r-2 border-[#001858] py-8 px-4">
          <nav className="space-y-2">
            {navigation.map((item) => (
              <div key={item.title}>
                <button
                  onClick={() => toggleNav(item.title)}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm font-semibold text-[#001858] hover:bg-[#f3d2c1] rounded-lg transition-colors"
                >
                  {item.icon}
                  {item.title}
                  <ChevronRight
                    className={`w-4 h-4 ml-auto transition-transform ${
                      expandedNav.includes(item.title) ? "rotate-90" : ""
                    }`}
                  />
                </button>
                {expandedNav.includes(item.title) && item.items && (
                  <div className="ml-6 mt-1 space-y-1 border-l-2 border-[#f3d2c1]">
                    {item.items.map((subItem) => (
                      <a
                        key={subItem.href}
                        href={subItem.href}
                        className={`block pl-4 py-1.5 text-sm transition-colors ${
                          activeSection === subItem.href.slice(1)
                            ? "text-[#f582ae] font-medium border-l-2 border-[#f582ae] -ml-[2px]"
                            : "text-[#172c66] hover:text-[#001858]"
                        }`}
                      >
                        {subItem.title}
                      </a>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 min-w-0 px-8 py-12 lg:px-16">
          {/* Hero */}
          <section id="introduction" className="mb-16">
            <div className="flex items-center gap-2 text-sm text-[#172c66] mb-4">
              <span>Docs</span>
              <ChevronRight className="w-4 h-4" />
              <span>Getting Started</span>
            </div>
            <h1 className="text-4xl font-bold text-[#001858] mb-4">
              MURA SDK
            </h1>
            <p className="text-xl text-[#172c66] mb-8 max-w-2xl">
              Python SDK for the MURA Supply Chain Agent Network. Enable AI agents to coordinate procurement, logistics, and compliance.
            </p>

            <div className="grid sm:grid-cols-2 gap-4 mb-8">
              <Card
                href="#client-overview"
                title="For Platforms"
                description="Use MuraClient to power your procurement with MURA's agent network"
                icon={<Boxes className="w-5 h-5" />}
              />
              <Card
                href="#supplier-overview"
                title="For Suppliers"
                description="Use SupplierAgent to join the network and receive RFQs automatically"
                icon={<Users className="w-5 h-5" />}
              />
            </div>

            <div className="p-4 rounded-xl bg-[#8bd3dd]/30 border-2 border-[#001858]">
              <p className="text-sm text-[#001858]">
                <strong>Built on NANDA</strong> — MURA implements concepts from MIT Media Lab's{" "}
                <a href="https://nanda.media.mit.edu/" target="_blank" rel="noopener noreferrer" className="text-[#f582ae] font-semibold hover:underline">
                  NANDA research
                </a>{" "}
                for agent coordination.
              </p>
            </div>
          </section>

          {/* Installation */}
          <section id="installation" className="mb-16">
            <h2 className="text-2xl font-bold text-[#001858] mb-4">Installation</h2>
            <CodeBlock
              code="pip install mura-sdk"
              language="bash"
              id="install"
              onCopy={copyCode}
              copied={copiedId === "install"}
            />
            <p className="mt-4 text-sm text-[#172c66]">
              Requires Python 3.10+
            </p>
          </section>

          {/* Quick Start */}
          <section id="quickstart" className="mb-16">
            <h2 className="text-2xl font-bold text-[#001858] mb-4">Quick Start</h2>

            <h3 className="text-lg font-semibold text-[#001858] mt-8 mb-3">For Platforms</h3>
            <CodeBlock
              code={`from mura import MuraClient

client = MuraClient(api_key="mura_live_xxx")

result = client.procure(
    request="500 temperature sensors",
    budget=5000,
    destination_region="EU"
)

print(result.recommendation.recommended_supplier)`}
              language="python"
              id="quickstart-platform"
              onCopy={copyCode}
              copied={copiedId === "quickstart-platform"}
            />

            <h3 className="text-lg font-semibold text-[#001858] mt-8 mb-3">For Suppliers</h3>
            <CodeBlock
              code={`from mura import SupplierAgent

agent = SupplierAgent(
    name="Acme Electronics",
    capabilities=["electronics", "sensors"],
    region="EU"
)

agent.add_to_catalog("temperature_sensor", 5.50, "sensors")
agent.register()
agent.run()`}
              language="python"
              id="quickstart-supplier"
              onCopy={copyCode}
              copied={copiedId === "quickstart-supplier"}
            />
          </section>

          <Divider />

          {/* MuraClient */}
          <section id="client-overview" className="mb-16">
            <div className="flex items-center gap-2 text-sm text-[#172c66] mb-4">
              <span>SDK</span>
              <ChevronRight className="w-4 h-4" />
              <span>MuraClient</span>
            </div>
            <h2 className="text-2xl font-bold text-[#001858] mb-4">MuraClient</h2>
            <p className="text-[#172c66] mb-6">
              The main client for platforms to use MURA as supply chain infrastructure.
            </p>

            <CodeBlock
              code={`from mura import MuraClient

client = MuraClient(
    api_key="mura_live_xxx",      # Your API key
    base_url="https://mura-production.up.railway.app",  # Optional
    timeout=120.0                  # Request timeout
)`}
              language="python"
              id="client-init"
              onCopy={copyCode}
              copied={copiedId === "client-init"}
            />

            <ParamTable
              title="Parameters"
              params={[
                { name: "api_key", type: "str", description: "Your MURA API key" },
                { name: "base_url", type: "str", description: "API base URL (optional)" },
                { name: "timeout", type: "float", description: "Request timeout in seconds (default: 120)" },
              ]}
            />
          </section>

          {/* procure() */}
          <section id="procure" className="mb-16">
            <MethodSignature
              name="client.procure"
              params={["request", "budget=None", "deadline_days=7", "destination_region='EU'"]}
              returns="ProcurementResult"
            />
            <p className="text-[#172c66] mb-4">
              Run the full procurement workflow: BOM → discovery → quoting → compliance → logistics → recommendation.
            </p>

            <CodeBlock
              code={`result = client.procure(
    request="Build me a racing drone",
    budget=1000,
    deadline_days=14,
    destination_region="EU"
)

# Access results
result.bom                    # Bill of Materials
result.quotes                 # All quotes
result.compliance             # Compliance result
result.logistics              # Shipping plan
result.recommendation         # Final recommendation`}
              language="python"
              id="procure-example"
              onCopy={copyCode}
              copied={copiedId === "procure-example"}
            />

            <ParamTable
              params={[
                { name: "request", type: "str", description: "Natural language procurement request", required: true },
                { name: "budget", type: "float", description: "Budget constraint in EUR" },
                { name: "deadline_days", type: "int", description: "Delivery deadline (default: 7)" },
                { name: "destination_region", type: "str", description: "Destination: EU, US, Asia" },
              ]}
            />
          </section>

          {/* procure_stream() */}
          <section id="procure-stream" className="mb-16">
            <MethodSignature
              name="client.procure_stream"
              params={["request", "..."]}
              returns="AsyncGenerator[dict]"
              isAsync
            />
            <p className="text-[#172c66] mb-4">
              Stream procurement with real-time updates. Perfect for live UI progress.
            </p>

            <CodeBlock
              code={`async for step in client.procure_stream("500 sensors"):
    print(f"[{step['agent']}] {step['message']}")

    if step.get('phase') == 'complete':
        result = step.get('data')`}
              language="python"
              id="stream-example"
              onCopy={copyCode}
              copied={copiedId === "stream-example"}
            />

            <ResponseBlock
              title="Step Object"
              code={`{
  "agent": "compliance",
  "message": "Checking EU regulations...",
  "phase": "compliance",
  "progress": 0.7
}`}
            />
          </section>

          {/* registry */}
          <section id="registry" className="mb-16">
            <MethodSignature
              name="client.registry.discover"
              params={["role=None", "capability=None", "region=None", "min_trust=0.0"]}
              returns="List[AgentFacts]"
            />
            <p className="text-[#172c66] mb-4">
              Discover agents in the MURA network.
            </p>

            <CodeBlock
              code={`from mura import AgentRole

suppliers = client.registry.discover(
    role=AgentRole.SUPPLIER,
    capability="electronics",
    region="EU",
    min_trust=0.8
)

for s in suppliers:
    print(f"{s.name}: {s.trust.reputation_score}")`}
              language="python"
              id="registry-example"
              onCopy={copyCode}
              copied={copiedId === "registry-example"}
            />
          </section>

          {/* quotes */}
          <section id="quotes" className="mb-16">
            <MethodSignature
              name="client.quotes.get_quote"
              params={["supplier_id", "items", "deadline_days=None"]}
              returns="dict"
            />

            <CodeBlock
              code={`quote = client.quotes.get_quote(
    supplier_id="supplier-abc123",
    items=[
        {"part_name": "temperature_sensor", "quantity": 100},
        {"part_name": "humidity_sensor", "quantity": 50}
    ]
)

print(f"Total: €{quote['total_cost']}")`}
              language="python"
              id="quotes-example"
              onCopy={copyCode}
              copied={copiedId === "quotes-example"}
            />
          </section>

          {/* compliance */}
          <section id="compliance" className="mb-16">
            <MethodSignature
              name="client.compliance.check"
              params={["items", "destination_region", "transport_type='air'"]}
              returns="dict"
            />

            <CodeBlock
              code={`result = client.compliance.check(
    items=[{"part_name": "battery_li_ion", "category": "electronics"}],
    destination_region="EU",
    transport_type="air"
)

print(f"Status: {result['status']}")  # passed, warning, failed`}
              language="python"
              id="compliance-example"
              onCopy={copyCode}
              copied={copiedId === "compliance-example"}
            />
          </section>

          {/* logistics */}
          <section id="logistics" className="mb-16">
            <MethodSignature
              name="client.logistics.plan"
              params={["origin_region", "destination_region", "items", "deadline_days=None"]}
              returns="dict"
            />

            <CodeBlock
              code={`plan = client.logistics.plan(
    origin_region="Asia",
    destination_region="EU",
    items=[{"weight_kg": 5}],
    deadline_days=7
)

print(f"Provider: {plan['provider']}, Cost: €{plan['shipping_cost']}")`}
              language="python"
              id="logistics-example"
              onCopy={copyCode}
              copied={copiedId === "logistics-example"}
            />
          </section>

          <Divider />

          {/* SupplierAgent */}
          <section id="supplier-overview" className="mb-16">
            <div className="flex items-center gap-2 text-sm text-[#172c66] mb-4">
              <span>SDK</span>
              <ChevronRight className="w-4 h-4" />
              <span>SupplierAgent</span>
            </div>
            <h2 className="text-2xl font-bold text-[#001858] mb-4">SupplierAgent</h2>
            <p className="text-[#172c66] mb-6">
              Join the MURA network as a supplier to receive RFQs and respond with quotes.
            </p>

            <CodeBlock
              code={`from mura import SupplierAgent

agent = SupplierAgent(
    name="Acme Electronics",
    capabilities=["electronics", "sensors", "MCUs"],
    region="EU",
    country="Germany",
    certifications=[
        {"authority": "ISO", "certification": "9001"},
    ],
    max_discount_pct=15.0,
    lead_time_days=5
)`}
              language="python"
              id="supplier-init"
              onCopy={copyCode}
              copied={copiedId === "supplier-init"}
            />

            <ParamTable
              params={[
                { name: "name", type: "str", description: "Your company name", required: true },
                { name: "capabilities", type: "List[str]", description: "What you supply", required: true },
                { name: "region", type: "str", description: "Your region: EU, US, Asia", required: true },
                { name: "country", type: "str", description: "Your country" },
                { name: "certifications", type: "List[dict]", description: "Your certifications" },
              ]}
            />
          </section>

          {/* Catalog */}
          <section id="catalog" className="mb-16">
            <h3 className="text-xl font-bold text-[#001858] mb-4">Catalog Management</h3>

            <CodeBlock
              code={`# Add items to catalog
agent.add_to_catalog(
    part_name="temperature_sensor",
    unit_price=5.50,
    category="sensors",
    stock=1000,
    lead_time_days=3
)

# Load from JSON file
agent.load_catalog_from_json("catalog.json")

# Load from dictionary
agent.load_catalog_from_dict({
    "esp32": {"unit_price": 8.0, "category": "MCUs", "stock": 500}
})`}
              language="python"
              id="catalog-example"
              onCopy={copyCode}
              copied={copiedId === "catalog-example"}
            />
          </section>

          {/* RFQ Handler */}
          <section id="rfq-handler" className="mb-16">
            <h3 className="text-xl font-bold text-[#001858] mb-4">Custom RFQ Handler</h3>
            <p className="text-[#172c66] mb-4">
              Connect to your ERP/inventory system with a custom handler.
            </p>

            <CodeBlock
              code={`from mura import Quote, QuoteItem

@agent.on_rfq
def handle_rfq(rfq):
    items = []

    for item in rfq.items:
        price = my_erp.get_price(item.part_name)
        if price is None:
            continue

        items.append(QuoteItem(
            part_name=item.part_name,
            unit_price=price,
            quantity=item.quantity,
            total_price=price * item.quantity,
            lead_time_days=3,
            in_stock=True
        ))

    return Quote(
        supplier_id=agent.agent_id,
        supplier_name=agent.name,
        region=agent.region,
        items=items,
        total_cost=sum(i.total_price for i in items),
        currency="EUR",
        lead_time_days=max(i.lead_time_days for i in items)
    )

agent.register()
agent.run()`}
              language="python"
              id="handler-example"
              onCopy={copyCode}
              copied={copiedId === "handler-example"}
            />
          </section>

          <Divider />

          {/* Models */}
          <section id="models" className="mb-16">
            <div className="flex items-center gap-2 text-sm text-[#172c66] mb-4">
              <span>Reference</span>
              <ChevronRight className="w-4 h-4" />
              <span>Models</span>
            </div>
            <h2 className="text-2xl font-bold text-[#001858] mb-4">Models</h2>

            <CodeBlock
              code={`from mura import (
    # Agent Identity (NANDA)
    AgentFacts,
    TrustProfile,
    Certification,

    # Procurement
    BOMItem,
    BillOfMaterials,
    Quote,
    QuoteItem,
    RFQ,

    # Results
    ProcurementResult,
    ComplianceResult,
    LogisticsPlan,
    Recommendation,
)`}
              language="python"
              id="models-import"
              onCopy={copyCode}
              copied={copiedId === "models-import"}
            />
          </section>

          {/* Enums */}
          <section id="enums" className="mb-16">
            <h3 className="text-xl font-bold text-[#001858] mb-4">Enums</h3>

            <CodeBlock
              code={`from mura import TrustLevel, AgentRole, ComplianceStatus

# Trust Levels (ZTAA)
TrustLevel.SELF_DECLARED       # Agent claims capabilities
TrustLevel.PEER_ATTESTED       # Other agents vouch
TrustLevel.AUTHORITY_VERIFIED  # Official verification

# Agent Roles
AgentRole.SUPPLIER
AgentRole.LOGISTICS
AgentRole.COMPLIANCE
AgentRole.BUYER

# Compliance Status
ComplianceStatus.PASSED
ComplianceStatus.WARNING
ComplianceStatus.FAILED`}
              language="python"
              id="enums-example"
              onCopy={copyCode}
              copied={copiedId === "enums-example"}
            />
          </section>

          {/* Errors */}
          <section id="errors" className="mb-16">
            <h3 className="text-xl font-bold text-[#001858] mb-4">Error Handling</h3>

            <CodeBlock
              code={`from mura import (
    MuraError,               # Base exception
    MuraConnectionError,     # Network issues
    MuraAuthenticationError, # Invalid API key
    NoSuppliersFoundError,   # No matching suppliers
    ComplianceError,         # Compliance blockers
)

try:
    result = client.procure("dangerous goods")
except ComplianceError as e:
    print(f"Blocked: {e.blockers}")
except NoSuppliersFoundError:
    print("No suppliers available")`}
              language="python"
              id="errors-example"
              onCopy={copyCode}
              copied={copiedId === "errors-example"}
            />
          </section>

                  </main>
      </div>
    </div>
  );
}

// Components

function Card({
  href,
  title,
  description,
  icon,
}: {
  href: string;
  title: string;
  description: string;
  icon: React.ReactNode;
}) {
  return (
    <a
      href={href}
      className="group p-5 rounded-xl border-2 border-[#001858] bg-white hover:bg-[#f3d2c1] transition-all hover:shadow-[4px_4px_0_#001858] hover:-translate-x-0.5 hover:-translate-y-0.5"
    >
      <div className="flex items-center gap-3 mb-2">
        <div className="text-[#f582ae]">{icon}</div>
        <h3 className="font-bold text-[#001858]">{title}</h3>
        <ArrowRight className="w-4 h-4 ml-auto text-[#172c66] opacity-0 group-hover:opacity-100 transition-opacity" />
      </div>
      <p className="text-sm text-[#172c66]">{description}</p>
    </a>
  );
}

function MethodSignature({
  name,
  params,
  returns,
  isAsync = false,
}: {
  name: string;
  params: string[];
  returns: string;
  isAsync?: boolean;
}) {
  return (
    <div className="mb-4 p-4 rounded-xl bg-[#001858] border-2 border-[#001858]">
      <code className="text-sm text-[#fef6e4]">
        {isAsync && <span className="text-[#f582ae]">async </span>}
        <span className="text-[#8bd3dd]">{name}</span>
        <span className="text-[#f3d2c1]">(</span>
        {params.map((p, i) => (
          <span key={p}>
            <span className="text-[#fef6e4]">{p}</span>
            {i < params.length - 1 && <span className="text-[#f3d2c1]">, </span>}
          </span>
        ))}
        <span className="text-[#f3d2c1]">)</span>
        <span className="text-[#f3d2c1]"> → </span>
        <span className="text-[#8bd3dd]">{returns}</span>
      </code>
    </div>
  );
}

function CodeBlock({
  code,
  language,
  id,
  onCopy,
  copied,
}: {
  code: string;
  language: string;
  id: string;
  onCopy: (code: string, id: string) => void;
  copied: boolean;
}) {
  return (
    <div className="rounded-xl overflow-hidden border-2 border-[#001858]">
      <div className="flex items-center justify-between px-4 py-2 bg-[#001858]">
        <span className="text-xs font-medium text-[#f3d2c1]">{language}</span>
        <button
          onClick={() => onCopy(code, id)}
          className="flex items-center gap-1.5 text-xs font-medium text-[#fef6e4] hover:text-white transition-colors"
        >
          {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <Highlight theme={themes.nightOwl} code={code.trim()} language={language as any}>
        {({ style, tokens, getLineProps, getTokenProps }) => (
          <pre className="p-4 overflow-x-auto text-sm" style={{ ...style, margin: 0 }}>
            {tokens.map((line, i) => (
              <div key={i} {...getLineProps({ line })}>
                <span className="inline-block w-8 text-right mr-4 select-none text-[#8bd3dd]/40 text-xs">
                  {i + 1}
                </span>
                {line.map((token, key) => (
                  <span key={key} {...getTokenProps({ token })} />
                ))}
              </div>
            ))}
          </pre>
        )}
      </Highlight>
    </div>
  );
}

function ParamTable({
  title = "Parameters",
  params,
}: {
  title?: string;
  params: { name: string; type: string; description: string; required?: boolean }[];
}) {
  return (
    <div className="mt-6">
      <h4 className="text-sm font-bold text-[#001858] mb-3">{title}</h4>
      <div className="rounded-xl border-2 border-[#001858] overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-[#f3d2c1]">
              <th className="text-left px-4 py-2 font-semibold text-[#001858] border-b-2 border-[#001858]">Name</th>
              <th className="text-left px-4 py-2 font-semibold text-[#001858] border-b-2 border-[#001858]">Type</th>
              <th className="text-left px-4 py-2 font-semibold text-[#001858] border-b-2 border-[#001858]">Description</th>
            </tr>
          </thead>
          <tbody>
            {params.map((param, i) => (
              <tr key={param.name} className={i % 2 === 0 ? "bg-white" : "bg-[#fef6e4]"}>
                <td className="px-4 py-2.5 font-mono text-[#001858]">
                  {param.name}
                  {param.required && <span className="text-[#f582ae] ml-1">*</span>}
                </td>
                <td className="px-4 py-2.5">
                  <code className="text-xs px-1.5 py-0.5 rounded bg-[#8bd3dd]/30 text-[#001858]">
                    {param.type}
                  </code>
                </td>
                <td className="px-4 py-2.5 text-[#172c66]">{param.description}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ResponseBlock({ title, code }: { title: string; code: string }) {
  return (
    <div className="mt-4 p-4 rounded-xl bg-[#f3d2c1]/50 border-2 border-[#001858]">
      <p className="text-xs font-bold text-[#001858] mb-2">{title}</p>
      <pre className="text-xs text-[#001858] font-mono overflow-x-auto">{code}</pre>
    </div>
  );
}

function Divider() {
  return <hr className="my-16 border-t-2 border-[#f3d2c1]" />;
}
