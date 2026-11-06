# BurnIQ — Enterprise LLM Telemetry, Sage & Oracle NetSuite ERP & Workday Salary ROI Platform

**BurnIQ** attributes corporate LLM usage (**Anthropic Claude** & **Google Cloud Vertex AI Gemini**) across engineering source control (**GitHub**, **GitLab**, **Bitbucket**), CI/CD release pipelines (**Jenkins**, **Bamboo**), agile & ITSM workflows (**Jira**, **ServiceNow**, **Zendesk**), observability & security (**Datadog**, **Substrate**, **New Relic**, **Soluble**, **PagerDuty**, **Opsgenie**), employee compensation (**Workday HCM**), and enterprise financial ledgers (**Sage Intacct / Sage X3**, **Oracle NetSuite OneWorld & SuiteQL**, **SAP S/4HANA**, **Salesforce Revenue Cloud**, and **Microsoft Power BI**).

---

## Core Enterprise Capabilities

### 1. Sage Intacct, Sage X3 & Sage 300 ERP Integration (`/api/erp/sage`)
- **Multi-Entity General Ledger Consolidation**:
  - `E100` — *BurnIQ North America Inc.* (Sage Intacct Multi-Entity, USD)
  - `E200` — *BurnIQ EMEA Operations Ltd.* (Sage X3 Enterprise, EUR)
  - `E300` — *BurnIQ APAC Pte. Ltd.* (Sage 300 Cloud, SGD)
- **ASC 350-40 / IAS 38 Software Development Capitalization**:
  - Automatically maps verified engineering token spend + Workday loaded engineering hours from shipped Git/CI-CD releases into **Sage GL Account `1650-01` (Capitalized AI R&D)** vs **`6120-01` (Production AI OpEx)** and **`6120-02` (Low-Value Email/Notes SG&A Waste)**.
- **3-Way Matched AP Vendor Bills**:
  - Reconciles monthly Anthropic PBC and Google Cloud Vertex AI invoices against granular developer token telemetry.
- **Live GL Batch Creation & CSV Export**:
  - Create and post balanced Sage Intacct GL Batches (`POST /api/erp/sage/gl-batch`) and export Sage Intacct-compatible CSV batches (`GET /api/export/sage`).

### 2. Oracle NetSuite OneWorld & SuiteQL Integration (`/api/erp/netsuite`)
- **OneWorld Multi-Subsidiary Hierarchy**:
  - `SUB-1` (*BurnIQ Global Holdings Consolidated USD*), `SUB-2` (*BurnIQ Technologies US Inc.*), `SUB-3` (*BurnIQ Europe Ltd. GBP*), and `SUB-4` (*BurnIQ DACH GmbH EUR*).
- **SuiteTalk REST v1 Journal Entries & Custom Segments**:
  - Posts multi-subsidiary `journalEntry` records tagged with Custom Segments `cseg_ai_provider` (*Anthropic Claude*, *Google Gemini*) and `cseg_task_value_tier` (*Tier 1: Production Release Code*, *Tier 2: Architecture & PR Review*, *Tier 3: Low-Value Email/Notes Waste*).
- **Interactive SuiteQL Analytics Query Engine (`POST /api/erp/netsuite/suiteql`)**:
  - Query NetSuite transactions, OneWorld subsidiaries, annual LLM commit Purchase Orders (`PO-NS-8841`, `PO-NS-8842`), and 36-month R&D CapEx Amortization Schedules (`AMORT-NS-301`..`303`).

### 3. Low-Value Task Auditor (Emails, Meeting Notes & Ad-Hoc Prompts)
- Identifies non-engineering prompts burning frontier models (`claude-3-opus`, `claude-3-7-sonnet`, `gemini-2.5-pro`) on routine internal emails and meeting notes with zero git commits.
- Provides 1-click **Smart Model Routing (`POST /api/audit/optimize-routing`)** to downgrade routine email/notes traffic to `claude-3-5-haiku` / `gemini-2.5-flash` and automatically update **Sage GL `6120-02`** and **Oracle NetSuite `JE-NS-9043`**.

---

## Running Locally

```bash
# Start Main BurnIQ Platform on Port 8000
uvicorn main:app --host 0.0.0.0 --port 8000

# Start Mock Enterprise Gateway on Port 8090
uvicorn mock_enterprise:app --host 0.0.0.0 --port 8090
```