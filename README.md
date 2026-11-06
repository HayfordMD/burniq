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

3. **22 Enterprise Connectors & Mock Enterprise Gateway**:
   - **Incident Management**: PagerDuty, Opsgenie (Genie)
   - **LLM Providers**: Anthropic Claude Enterprise, Google Gemini Enterprise
   - **SCM & CI/CD**: GitHub Enterprise, GitLab Enterprise, Bitbucket Cloud, Jenkins CI, Atlassian Bamboo
   - **ITSM & Support**: Jira Software, ServiceNow ITSM, Zendesk Enterprise
   - **Observability & DevSecOps**: Datadog, Substrate AI FinOps, New Relic One, Soluble Cloud Security
   - **HRM, ERP, CRM & BI**: Workday HRM, Salesforce CRM, SAP S/4HANA ERP, Sage Intacct / X3, Oracle NetSuite ERP, Microsoft Power BI, and CSV Import/Export

## Running Locally

```bash
# Main BurnIQ Platform (Port 8000)
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Standalone Mock Enterprise Gateway (Port 8090)
uvicorn app.mock_enterprise:mock_app --host 0.0.0.0 --port 8090
```

## Running Tests

```bash
python3 -m unittest discover -s tests -v
```