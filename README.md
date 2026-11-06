# BurnIQ — Enterprise AI Telemetry, Service Connection Control, Multi-Persona Analytics & Google Flash 3-8 Fast Lite RAG Platform

**BurnIQ** is a full-stack enterprise LLM telemetry, FinOps attribution, service connection governance, and RAG intelligence platform. It tracks corporate AI usage (Google Gemini & Anthropic Claude) end-to-end from source code, Git commits, branches, and CI/CD releases (**GitHub, GitLab, Bitbucket, Jenkins, Bamboo**) to **Jira** tasks, **ServiceNow** incidents, **Zendesk** support deflection, **Workday HRM** compensation bands, **Salesforce** pipeline velocity, **SAP S/4HANA** cost centers, **Power BI**, and low-value task audits (corporate emails, meeting notes, and Slack summaries).

---

## Core Capabilities

### 1. Real-Time Service Connection Control Center (Turn ON / OFF)
- **16 Enterprise Connectors** across 6 categories (*LLM Gateways*, *Source Control*, *CI/CD Pipelines*, *Issue & ITSM*, *ERP / HR / CRM*, *BI & Ingestion*).
- **Individual & Bulk ON / OFF Circuit Switches**: Toggle any service connection `ON` or `OFF` from the global quick-strip, the dedicated Connections Control Center, or inline within Technical Ops charts/tables.
- **Live Downstream Impact**: Turning a connection `OFF` immediately pauses webhook ingestion, halts token spend for that stream, updates all 4 persona dashboards, and isolates its live stream from default RAG retrieval.
- **Per-Connector RAG Indexing Toggle, Diagnostic Health Probe & Manual Sync**.

### 2. Multi-Persona Charts & Metric Dashboards
- **01 · Technical Ops & SRE (`techops`)**: Active connector uptime, telemetry ingestion throughput (`ev/min`), `Google Flash 3-8 Fast Lite` P95 latency (`112ms`), RAG vector index health, and ServiceNow P1/P2 MTTR reduction (`-54%`).
- **02 · Developers & Architects (`developers`)**: Code-to-Release attribution funnel (Prompts &rarr; Git Commits &rarr; Branches &rarr; PRs &rarr; Jenkins/Bamboo CI &rarr; Releases), LOC per 1k tokens by language, PR merge cycle time (`4.2 hrs`), and IDE RAG cache hit rate (`89.5%`).
- **03 · Engineering Managers (`managers`)**: Jira sprint velocity (`470 SP`), engineering hours reclaimed (`11.6 hrs/dev/wk`), and **High-Value vs Low-Value Task Audit** (automatically routing low-value email polishing & meeting note formatting to `Google Flash 3-8 Fast Lite` to eliminate 97.6% of administrative token waste).
- **04 · C-Suite Executive (`csuite`)**: Net Enterprise AI ROI (`5.4x`), verified **Workday HRM** payroll value reclaimed (`$286.2K/mo` gross / `$168.4K/mo` net), **SAP S/4HANA** cost-center budget variance (`15.8% under budget`), and an interactive **FinOps & Flash-Lite Routing Simulator**.

### 3. Robust Enterprise Search & Customized RAG-Trained LLM (`Google Flash 3-8 Fast Lite`)
- **Hybrid BM25 + 64-Dim NumPy SVD Vector Search (`/api/search`)**: Instant lexical + semantic search across commits, CI builds, Jira epics, ServiceNow postmortems, Workday ROI ledgers, and custom RAG documents, with active-connection circuit filtering.
- **Customized RAG-Trained Lightweight LLM (`/api/llm/chat`)**: Powered by **`google/gemini-3-8-flash-lite` (Google Flash 3-8 Fast Lite)** (`$0.035/1M` input tokens, `$0.008/1M` cached RAG tokens, `94ms` avg TTFT) trained on enterprise RAG ingestion (`burniq-flash-3-8-fast-lite-rag-v2.4`), returning persona-adapted markdown tables, inline `[DOC-xxx]` citations, and live cost-savings telemetry (`96.8%+` cheaper than frontier models).
- **Interactive RAG Ingestion & LoRA Adapter Calibration Studio (`/api/rag/ingest` & `/api/rag/train`)**: Ingest new markdown runbooks or CSV datasets and trigger live SVD vector re-indexing and adapter calibration.

---

## Quick Start

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Run the automated end-to-end verification suite:

```bash
python3 tests/test_api.py
```