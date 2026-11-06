# BurnIQ — Enterprise AI Telemetry, Incident Response & ROI Platform

**BurnIQ** correlates corporate **Anthropic Claude** & **Google Gemini** token consumption against engineering velocity, incident MTTR savings (**PagerDuty** & **Opsgenie / Genie**), CI/CD release impact, Workday HRM compensation, ERP/CRM financial ledgers, and low-value task overhead.

## Key Capabilities

1. **PagerDuty (`api.pagerduty.com` & `events.pagerduty.com/v2/enqueue`)**:
   - Real-time incident lifecycle management (`triggered` -> `acknowledged` -> `resolved`).
   - Events v2 API support for automated alert triggers, acknowledgments, and resolutions.
   - Escalation policies, on-call schedules (`PD-SCH-01`..`04`), service directory (`PD-SVC-01`..`04`), and automated event orchestration rules (`PD-RULE-01`..`04`).
   - AI remediation correlation showing Claude & Gemini root-cause analysis and MTTR hours/salary saved.

2. **Opsgenie / Genie (`api.opsgenie.com` & `/api/genie/*`)**:
   - Full Alert API v2 lifecycle (`open`, `acknowledged`, `snoozed`, `closed`, `escalate`) with bi-directional PagerDuty incident mirroring.
   - Responder routing teams (`team-sre-core`, `team-llm-platform`, `team-finops-erp`, `team-secops`) and on-call rotations (`OG-SCH-01`..`04`).
   - Active heartbeat monitoring (`claude-anthropic-enterprise-hb`, `gemini-vertex-telemetry-hb`, `cicd-release-correlator-hb`, `workday-netsuite-sage-roi-hb`, `datadog-newrelic-soluble-bridge-hb`) with live ping support.

### 2. Oracle NetSuite OneWorld & SuiteQL Integration (`/api/erp/netsuite`)
- **OneWorld Multi-Subsidiary Hierarchy**:
  - `SUB-1` (*BurnIQ Global Holdings Consolidated USD*), `SUB-2` (*BurnIQ Technologies US Inc.*), `SUB-3` (*BurnIQ Europe Ltd. GBP*), and `SUB-4` (*BurnIQ DACH GmbH EUR*).
- **SuiteTalk REST v1 Journal Entries & Custom Segments**:
  - Posts multi-subsidiary `journalEntry` records tagged with Custom Segments `cseg_ai_provider` (*Anthropic Claude*, *Google Gemini*) and `cseg_task_value_tier` (*Tier 1: Production Release Code*, *Tier 2: Architecture & PR Review*, *Tier 3: Low-Value Email/Notes Waste*).
- **Interactive SuiteQL Analytics Query Engine (`POST /api/erp/netsuite/suiteql`)**:
  - Query NetSuite transactions, OneWorld subsidiaries, annual LLM commit Purchase Orders (`PO-NS-8841`, `PO-NS-8842`), and 36-month R&D CapEx Amortization Schedules (`AMORT-NS-301`..`303`).

### 3. Datadog, Substrate, New Relic & Soluble Observability & DevSecOps (`/api/observability`)
- **Datadog (`api.datadoghq.com`, `/api/datadog`)**:
  - Tracks LLM Observability trace spans (`dd-tr-*`), token latency percentiles, APM production service monitors (`DD-MON-101`..`104`), and CI Visibility / DORA metrics (Deployment Frequency, Lead Time for Changes, Change Failure Rate, and MTTR) across GitHub Actions, GitLab CI, Jenkins, Bitbucket Pipelines, and Atlassian Bamboo.
- **Substrate (`substrate.office.com` & `api.substrate.run`, `/api/substrate`)**:
  - **Microsoft Substrate M365 Knowledge Graph**: Audits Outlook MailItems, Teams Meeting Transcripts, and Copilot Chat Threads burning frontier LLMs with zero git/release output, with 1-click Haiku/Flash routing policy enforcement (`POST /api/substrate/enforce-policy`).
  - **Substrate Multi-Cloud AI Compute**: Tracks distributed inference & agentic orchestration across AWS Bedrock, GCP Vertex AI, and Azure OpenAI.
- **New Relic (`api.newrelic.com`, `/api/newrelic`)**:
  - APM Golden Signals (Apdex, RPM throughput, p95 response latency delta, error rates) per shipped release, AI Monitoring (`LlmChatCompletionSummary`), and an interactive **NerdGraph / NRQL Query Console (`POST /api/observability/query`)**.
- **Soluble (`api.soluble.io` / `app.soluble.cloud`, `/api/soluble`)**:
  - Cloud-Native Infrastructure-as-Code (IaC) & DevSecOps security auditing across Terraform, Kubernetes, Helm, Dockerfiles, and Secrets, plus a **Live IaC Auto-Remediation Scanner (`POST /api/soluble/scan`)** that detects wildcard IAM policies, unencrypted storage, and missing pod limits and generates compliant patches.

### 4. Low-Value Task Auditor (Emails, Meeting Notes & Ad-Hoc Prompts)
- Identifies non-engineering prompts burning frontier models (`claude-3-opus`, `claude-3-7-sonnet`, `gemini-2.5-pro`) on routine internal emails and meeting notes with zero git commits.
- Provides 1-click **Smart Model Routing (`POST /api/audit/optimize-routing`)** to downgrade routine email/notes traffic to `claude-3-5-haiku` / `gemini-2.5-flash` and automatically update **Sage GL `6120-02`** and **Oracle NetSuite `JE-NS-9043`**.

---

## Running Locally & Running End-to-End Tests

```bash
# Start Main BurnIQ Platform on Port 8000
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000

# Start Mock Enterprise Gateway on Port 8090
python3 -m uvicorn mock_enterprise:app --host 0.0.0.0 --port 8090

# Run End-to-End Verification Suites
python3 tests/test_burniq_erp.py
python3 tests/test_burniq_observability.py
```