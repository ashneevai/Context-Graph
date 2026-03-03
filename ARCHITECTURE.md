# Architecture — Billing Support Knowledge Context Graph

> An AI-powered billing support agent that grounds LLM responses in a structured
> knowledge graph, using **Groq** (llama-3.3-70b-versatile) for language
> understanding and **NetworkX** for graph traversal.

---

## Table of Contents

1. [Overview](#1-overview)
2. [System Architecture](#2-system-architecture)
3. [Component Breakdown](#3-component-breakdown)
4. [Knowledge Graph Design](#4-knowledge-graph-design)
5. [Data Flow](#5-data-flow)
6. [Entity Reference](#6-entity-reference)
7. [Relationship Reference](#7-relationship-reference)
8. [Key Design Decisions](#8-key-design-decisions)
9. [Extension Points](#9-extension-points)
10. [File Reference](#10-file-reference)

---

## 1. Overview

Traditional LLM-based support agents are prone to hallucination because they rely
entirely on parametric knowledge baked into model weights. This system solves that
by maintaining an **explicit, auditable knowledge graph** of billing domain concepts
and injecting the relevant subgraph into the LLM prompt at query time.

```
Customer Query
      │
      ▼
Entity Extraction (Groq)
      │
      ▼
Graph Traversal (NetworkX)  ◄──  Billing Knowledge Graph
      │                               (16 nodes, 30 edges)
      ▼
Context-Grounded Prompt
      │
      ▼
Response Generation (Groq)
      │
      ▼
Agent Reply
```

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        main.py  (CLI)                           │
│  ┌─────────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │ User Input  │  │  graph   │  │ entities │  │ path A B   │  │
│  │  (query)    │  │ command  │  │ command  │  │ command    │  │
│  └──────┬──────┘  └──────────┘  └──────────┘  └────────────┘  │
└─────────┼───────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    groq_agent.py  (Agent)                       │
│                                                                 │
│   ┌─────────────────────┐      ┌──────────────────────────┐    │
│   │  extract_entities() │      │       answer()           │    │
│   │                     │      │                          │    │
│   │  Groq API call      │      │  1. extract_entities()   │    │
│   │  (temp=0, max=150)  │      │  2. get_context()        │    │
│   │                     │      │  3. build system prompt  │    │
│   │  Returns: [str]     │      │  4. Groq API call        │    │
│   └──────────┬──────────┘      │  5. append to history    │    │
│              │                 └──────────────────────────┘    │
└──────────────┼──────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│               knowledge_graph.py  (Graph Store)                 │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │  nx.DiGraph                                             │  │
│   │                                                         │  │
│   │  Nodes (16)  ──  type, description,                     │  │
│   │                  common_issues[], solutions[]           │  │
│   │                                                         │  │
│   │  Edges (30)  ──  rel (label), desc (description)        │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│   get_context_for_entities()  ──  BFS-style subgraph builder   │
│   find_path()                 ──  nx.shortest_path wrapper      │
│   get_neighbors()             ──  successors + predecessors     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Breakdown

### `knowledge_graph.py` — Graph Store

**Class:** `BillingKnowledgeGraph`

Builds and exposes a `networkx.DiGraph` containing all billing domain knowledge.
Constructed once at startup; read-only at runtime.

| Method | Description |
|--------|-------------|
| `_build_billing_knowledge()` | Populates nodes and edges on init |
| `get_node_info(node)` | Returns all attributes for a node |
| `get_all_node_names()` | Returns list of all 16 entity names |
| `get_neighbors(node)` | Returns bidirectional neighbors |
| `find_path(source, target)` | Shortest directed path between two nodes |
| `get_context_for_entities(names)` | Builds structured context string from subgraph |
| `get_graph_summary()` | One-line summary of graph size |

**`get_context_for_entities()`** is the core retrieval function:
1. Iterates over requested entity names
2. For each node: emits description, common issues, solutions, outgoing relationships
3. Expands one level of unvisited neighbors (capped at 3) for additional context
4. Returns a plain-text string injected into the LLM system prompt

---

### `groq_agent.py` — LLM Agent

**Class:** `BillingSupportAgent`

Wraps the Groq client and `BillingKnowledgeGraph` into a two-stage pipeline.

**Model:** `llama-3.3-70b-versatile`

#### Stage 1 — Entity Extraction (`extract_entities`)

```
Query → Groq (temp=0) → JSON array of entity names → validated against graph nodes
```

- Temperature set to `0` for deterministic, structured output
- Parses JSON array from response; falls back to keyword matching if JSON fails
- Filters candidates to only valid graph node names

#### Stage 2 — Answer Generation (`answer`)

```
Entities → Graph Context → System Prompt + History → Groq (temp=0.7) → Response
```

- Injects the graph context as the system message
- Maintains `conversation_history` as a list of `{role, content}` dicts
- Appends each turn so the model has full conversational context
- Falls back to `[Customer, Invoice, Payment]` context if no entities extracted

---

### `main.py` — CLI Interface

Interactive REPL loop with built-in graph exploration commands.

| Command | Action |
|---------|--------|
| `<query>` | Ask a billing support question |
| `graph` | Print graph summary (nodes + edge count) |
| `entities` | List all 16 entities with descriptions |
| `path A B` | Show shortest relationship path between two entities |
| `reset` | Clear conversation history |
| `help` | Show command reference |
| `quit` / `exit` | Exit |

---

### `visualize.py` — Graph Renderer

Generates a static PNG of the knowledge graph using `matplotlib` + `networkx`.

- **Layout:** Spring layout (`seed=42`, `k=2.8`) for reproducible positioning
- **Node color coding:**
  - Blue (`#4A90D9`) — Entity nodes
  - Amber (`#E8A838`) — Process nodes
  - Red (`#E05C5C`) — Event nodes
- **Edge labels:** relationship type (`rel` attribute)
- **Output:** `billing_knowledge_graph.png` at 150 DPI
- Uses `Agg` (non-interactive) backend — safe in headless/server environments

---

## 4. Knowledge Graph Design

### Node Schema

Each node carries four attributes:

```python
{
    "type":          str,        # "entity" | "process" | "event"
    "description":   str,        # plain-language definition
    "common_issues": List[str],  # 4 typical support scenarios
    "solutions":     List[str],  # 4 corresponding resolution steps
}
```

### Edge Schema

Each directed edge carries two attributes:

```python
{
    "rel":  str,  # short relationship label  (e.g. "generates", "can_become")
    "desc": str,  # full description of the relationship
}
```

### Node Type Classification

| Type | Meaning | Examples |
|------|---------|---------|
| `entity` | A persistent billing domain object | Customer, Invoice, Plan, Credit |
| `process` | A workflow or lifecycle action | Payment, Refund, Cancellation, BillingCycle |
| `event` | A system-triggered occurrence | FailedPayment, Chargeback, UsageOverage |

---

## 5. Data Flow

### Normal Query Flow

```
1.  User types:   "My payment failed and subscription was cancelled"

2.  extract_entities()
    ├── Prompt: "Available entities: [...] — identify relevant ones"
    ├── Groq returns: ["Payment", "FailedPayment", "Subscription", "Cancellation"]
    └── Validated against graph node names

3.  get_context_for_entities(["Payment", "FailedPayment", "Subscription", "Cancellation"])
    ├── Payment node → description, issues, solutions, outgoing edges
    ├── FailedPayment node → description, issues, solutions, outgoing edges
    ├── Subscription node → description, issues, solutions, outgoing edges
    ├── Cancellation node → description, issues, solutions, outgoing edges
    └── 1-hop neighbors expanded (e.g. PaymentMethod, Plan, Refund)

4.  System prompt assembled:
    ├── Role instruction: "You are an expert billing support agent"
    ├── Graph context block (plain text, ~800-1200 tokens)
    └── Behavioural guidelines

5.  Groq call (temp=0.7, max_tokens=800)
    ├── Messages: [system] + conversation_history
    └── Returns grounded, actionable response

6.  Response appended to conversation_history
    └── Next query has full context of prior turns
```

### Graph Path Query Flow

```
User:  "path Customer Refund"
       │
       ▼
find_path("Customer", "Refund")
       │
       ▼
nx.shortest_path(G, "Customer", "Refund")
       │
       ▼
["Customer", "Invoice", "Payment", "Refund"]
       │
       ▼
Displayed as:  Customer → Invoice → Payment → Refund
```

---

## 6. Entity Reference

| Entity | Type | Key Relationships (outgoing) |
|--------|------|------------------------------|
| Customer | entity | has→Subscription, owns→PaymentMethod, receives→Invoice, creates→SupportTicket, holds→Credit, applies→Discount |
| Subscription | entity | belongs_to→Plan, generates→Invoice, follows→BillingCycle, can_trigger→Cancellation, can_incur→UsageOverage |
| Invoice | entity | requires→Payment, includes→Tax, may_include→Discount, may_apply→Credit, may_include→UsageOverage |
| Payment | process | uses→PaymentMethod, can_generate→Refund, can_become→FailedPayment, can_trigger→Chargeback |
| Refund | process | relates_to→Invoice, can_become→Credit |
| Plan | entity | defines→BillingCycle, eligible_for→Discount |
| PaymentMethod | entity | _(target only)_ |
| FailedPayment | event | risks→Subscription, generates→SupportTicket |
| Discount | entity | _(target only)_ |
| Cancellation | process | may_trigger→Refund, terminates→Subscription |
| Chargeback | event | can_suspend→Subscription, creates→SupportTicket |
| Tax | entity | _(target only)_ |
| BillingCycle | process | _(target only)_ |
| Credit | entity | _(target only)_ |
| UsageOverage | event | _(target only)_ |
| SupportTicket | process | _(target only)_ |

---

## 7. Relationship Reference

| Source | Relationship | Target |
|--------|-------------|--------|
| Customer | has | Subscription |
| Customer | owns | PaymentMethod |
| Customer | receives | Invoice |
| Customer | creates | SupportTicket |
| Customer | holds | Credit |
| Customer | applies | Discount |
| Subscription | belongs_to | Plan |
| Subscription | generates | Invoice |
| Subscription | follows | BillingCycle |
| Subscription | can_trigger | Cancellation |
| Subscription | can_incur | UsageOverage |
| Invoice | requires | Payment |
| Invoice | includes | Tax |
| Invoice | may_include | Discount |
| Invoice | may_apply | Credit |
| Invoice | may_include | UsageOverage |
| Payment | uses | PaymentMethod |
| Payment | can_generate | Refund |
| Payment | can_become | FailedPayment |
| Payment | can_trigger | Chargeback |
| FailedPayment | risks | Subscription |
| FailedPayment | generates | SupportTicket |
| Refund | relates_to | Invoice |
| Refund | can_become | Credit |
| Cancellation | may_trigger | Refund |
| Cancellation | terminates | Subscription |
| Chargeback | can_suspend | Subscription |
| Chargeback | creates | SupportTicket |
| Plan | defines | BillingCycle |
| Plan | eligible_for | Discount |

---

## 8. Key Design Decisions

### Why a Knowledge Graph instead of a vector store?

| Concern | Vector Store | Knowledge Graph |
|---------|-------------|-----------------|
| Relationship traversal | Implicit (similarity) | Explicit (typed edges) |
| Auditability | Opaque embedding space | Inspectable nodes/edges |
| Hallucination risk | Higher (retrieval miss) | Lower (structured facts) |
| Update cost | Re-embed on change | Edit node/edge dict |
| Path queries | Not supported | Native (`find_path`) |

### Two-stage LLM pipeline

Separating entity extraction (temp=0) from response generation (temp=0.7) gives:
- Deterministic, structured graph lookups
- Fluent, empathetic final responses
- Smaller, cheaper first call (max_tokens=150)

### Stateful conversation history

The agent appends every turn to `conversation_history`, which is passed as the
message list on every call. This allows multi-turn resolution flows (e.g. the
user first asks about a failed payment, then follows up asking about refund timing)
without losing context.

### Context depth capping

`get_context_for_entities()` expands only **1 hop** of unvisited neighbors
(capped at 3 per seed entity). This balances completeness against prompt token
budget — a full BFS traversal of the graph would exceed practical context limits.

---

## 9. Extension Points

| What to add | Where to change |
|-------------|-----------------|
| New billing entity | Add node dict in `_build_billing_knowledge()` |
| New relationship | Add tuple to `edges` list in `_build_billing_knowledge()` |
| Live account data | Pass DB lookup results into `system_prompt` in `answer()` |
| Different LLM | Change `MODEL` constant in `BillingSupportAgent` |
| REST API | Wrap `BillingSupportAgent.answer()` in a FastAPI route |
| Deeper graph traversal | Increase neighbor cap in `get_context_for_entities()` |
| Persistent memory | Serialize `conversation_history` to a database |

---

## 10. File Reference

```
Context graph/
├── knowledge_graph.py       # BillingKnowledgeGraph — graph store + retrieval
├── groq_agent.py            # BillingSupportAgent  — two-stage LLM pipeline
├── main.py                  # Interactive CLI REPL
├── visualize.py             # PNG graph renderer (matplotlib + networkx)
├── requirements.txt         # groq, networkx, python-dotenv, matplotlib
├── .env                     # GROQ_API_KEY (git-ignored)
├── .gitignore               # excludes venv/, .env, __pycache__, *.png
├── ARCHITECTURE.md          # this document
└── venv/                    # Python virtual environment (git-ignored)
```

### Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `groq` | 1.0.0 | Groq API client (LLM inference) |
| `networkx` | 3.6.1 | Graph data structure and algorithms |
| `python-dotenv` | 1.2.2 | Load GROQ_API_KEY from .env |
| `matplotlib` | 3.10.8 | Graph visualization rendering |

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes | API key from [console.groq.com](https://console.groq.com) |
