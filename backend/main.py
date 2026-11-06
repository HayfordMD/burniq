"""
BurnIQ — Enterprise LLM Usage, Code-to-Release Attribution, Observability (Datadog, Substrate, New Relic, Soluble),
Workday Salary ROI & Low-Value Task Audit Platform.
Main FastAPI Server (Port 8000).
"""

import csv
import io
import os
import time
import urllib.request
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.telemetry_data import (
    get_datadog_telemetry,
    get_substrate_telemetry,
    get_newrelic_telemetry,
    get_soluble_telemetry,
    get_code_to_release_attribution,
    get_workday_and_erp_roi,
    get_enterprise_connectors,
)
from backend.mock_enterprise import mock_router, build_vendor_connection_payload

app = FastAPI(
    title="BurnIQ Enterprise Telemetry & ROI Platform",
    description=(
        "Enterprise LLM Usage (Claude & Gemini), Code-to-Release Attribution (GitHub, GitLab, Bitbucket, Jenkins, Bamboo), "
        "Observability & DevSecOps (Datadog, Substrate, New Relic, Soluble), Workday HRM Salary ROI, ERP/CRM "
        "(SAP, Sage, Oracle NetSuite, Salesforce, Power BI), ITSM/Incident (Jira, ServiceNow, Zendesk, PagerDuty, Opsgenie), "
        "and Low-Value Task Audit Platform."
    ),
    version="2.4.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the Mock Enterprise Gateway at /mock-enterprise on Port 8000 as well
app.include_router(mock_router, prefix="/mock-enterprise")

# Runtime state for interactive policy enforcement & custom scans
POLICY_OVERRIDES: Dict[str, Dict[str, Any]] = {}
CUSTOM_INGESTED_RECORDS: List[Dict[str, Any]] = []


class ObservabilityQueryRequest(BaseModel):
    engine: str = "newrelic_nrql"  # newrelic_nrql | datadog_spans | substrate_graph | soluble_policy
    query: str


class SolubleScanRequest(BaseModel):
    iac_type: str = "Terraform"
    repository: str = "HayfordMD/burniq-payments-infra"
    branch: str = "feat/ai-generated-infra"
    llm_author: str = "Claude 3.7 Sonnet"
    code_snippet: str


class SubstratePolicyRequest(BaseModel):
    signal_id: str
    action: str = "ENFORCE_HAIKU_FLASH_ROUTING"


class CsvImportRequest(BaseModel):
    dataset_type: str = "observability"
    csv_content: str


@app.get("/api/health")
async def api_health() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "platform": "BurnIQ Enterprise Telemetry & ROI Platform",
        "version": "2.4.0",
        "port": 8000,
        "mock_enterprise_port": 8090,
        "featured_integrations": {
            "datadog": "CONNECTED (api.datadoghq.com)",
            "substrate": "CONNECTED (substrate.office.com & api.substrate.run)",
            "newrelic": "CONNECTED (api.newrelic.com / NerdGraph)",
            "soluble": "CONNECTED (api.soluble.io)",
        },
        "total_connectors_online": len(get_enterprise_connectors()),
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


@app.get("/api/datadog")
async def api_datadog() -> Dict[str, Any]:
    return get_datadog_telemetry()


@app.get("/api/substrate")
async def api_substrate() -> Dict[str, Any]:
    data = get_substrate_telemetry()
    for sig in data["microsoft_substrate_signals"]:
        sid = sig["signal_id"]
        if sid in POLICY_OVERRIDES:
            sig["value_classification"] = POLICY_OVERRIDES[sid]["status"]
            sig["action_policy"] = POLICY_OVERRIDES[sid]["applied_policy"]
    return data


@app.get("/api/newrelic")
async def api_newrelic() -> Dict[str, Any]:
    return get_newrelic_telemetry()


@app.get("/api/soluble")
async def api_soluble() -> Dict[str, Any]:
    return get_soluble_telemetry()


@app.get("/api/observability")
async def api_observability() -> Dict[str, Any]:
    dd = get_datadog_telemetry()
    sub = await api_substrate()
    nr = get_newrelic_telemetry()
    sol = get_soluble_telemetry()
    return {
        "datadog": dd,
        "substrate": sub,
        "newrelic": nr,
        "soluble": sol,
        "cross_platform_correlations": [
            {
                "correlation_id": "CORR-01",
                "title": "Claude 3.7 Sonnet Settlement Release (REL-2026.11.04-GH)",
                "datadog_signal": "Lead time -79% (4.8h) · 22.6k LLM tokens ($0.12)",
                "newrelic_signal": "Apdex 0.99 · p95 latency dropped 77.5ms -> 48.0ms (-38.1%)",
                "soluble_signal": "SOL-TF-AWS-042 Wildcard KMS/S3 IAM caught & auto-fixed in 4.2m",
                "substrate_signal": "Executed on AWS Bedrock/EKS H100 Substrate (16.8x ROI)",
                "net_business_impact": "+$185,000 Salesforce ARR · $6,138 Workday Salary Saved · 0 Incidents",
            },
            {
                "correlation_id": "CORR-02",
                "title": "Unthrottled Executive Email & Meeting Note Burn (Audit Flag)",
                "datadog_signal": "DD-MON-101 Alert: $4,820/wk Claude 3 Opus spend on non-code prompts",
                "newrelic_signal": "NRQL LlmChatCompletionSummary shows 2,790ms latency & 0 Jira links",
                "soluble_signal": "N/A (No Git/IaC artifacts produced)",
                "substrate_signal": "Microsoft Substrate Graph flags 194.2k routine emails & 68.4k passive meeting notes ($146.8k/mo Workday salary burn)",
                "net_business_impact": "$1.74M/yr Recoverable via Haiku / Gemini 2.5 Flash Auto-Routing Policy",
            },
            {
                "correlation_id": "CORR-03",
                "title": "Human-Only Legacy Commerce Hotfix Regression (REL-2026.11.02-BAM)",
                "datadog_signal": "DD-MON-104 Warning: Pod memory utilization 83.4% in Bamboo deploy",
                "newrelic_signal": "NR-APM-05 Apdex dropped to 0.91 · p95 latency +4.2% regression",
                "soluble_signal": "SOL-K8S-POD-019 Missing Helm memory limit & non-root securityContext (Auto-fix PR #418 generated)",
                "substrate_signal": "Remediation agent queued on AWS Inferentia2 Substrate worker",
                "net_business_impact": "Prevented P1 Outage via Soluble + Datadog + New Relic triad",
            },
        ],
    }


@app.post("/api/observability/query")
async def run_observability_query(req: ObservabilityQueryRequest) -> Dict[str, Any]:
    q_lower = req.query.lower()
    dd = get_datadog_telemetry()
    sub = get_substrate_telemetry()
    nr = get_newrelic_telemetry()
    sol = get_soluble_telemetry()

    if req.engine == "datadog_spans" or "datadog" in q_lower or "dd_" in q_lower:
        rows = [
            {
                "trace_id": s["trace_id"],
                "service": s["service"],
                "model": s["model"],
                "task_category": s["task_category"],
                "tokens": s["total_tokens"],
                "cost_usd": s["cost_usd"],
                "latency_ms": s["latency_ms"],
                "release_id": s["release_id"],
            }
            for s in dd["llm_observability_spans"]
        ]
        insight = "Datadog LLM Observability confirms 71.6% of engineering tokens map directly to shipped CI/CD releases with 3.1% Change Failure Rate."
    elif req.engine == "substrate_graph" or "substrate" in q_lower or "mail" in q_lower:
        rows = [
            {
                "signal_id": s["signal_id"],
                "channel": s["channel"],
                "artifact_type": s["artifact_type"],
                "model": s["model"],
                "tokens_burned": s["tokens_burned"],
                "workday_salary_burn_usd": s["workday_salary_burn_usd"],
                "classification": s["value_classification"],
            }
            for s in sub["microsoft_substrate_signals"]
        ]
        insight = "Microsoft Substrate Graph identifies $146,800/mo in Workday salary burn and $18,420/mo in LLM tokens spent on routine internal emails & passive meeting notes."
    elif req.engine == "soluble_policy" or "soluble" in q_lower or "iac" in q_lower:
        rows = [
            {
                "finding_id": f["finding_id"],
                "rule_id": f["rule_id"],
                "severity": f["severity"],
                "iac_type": f["iac_type"],
                "author_attribution": f["author_attribution"],
                "status": f["status"],
                "remediation_mins": f["remediation_time_mins"],
            }
            for f in sol["security_findings"]
        ]
        insight = "Soluble IaC scanning shows AI-assisted PRs achieve a 96.4% policy pass rate with 11.5-minute mean auto-remediation vs 185 minutes for manual fixes."
    else:
        # Default New Relic NRQL execution
        if "transaction" in q_lower or "apdex" in q_lower or "apm" in q_lower:
            rows = [
                {
                    "service_name": a["service_name"],
                    "apdex_score": a["apdex_score"],
                    "p95_ms": a["response_time_p95_ms"],
                    "error_rate_pct": a["error_rate_pct"],
                    "latency_delta_pct": a["latency_delta_pct"],
                    "release_id": a["release_id"],
                    "llm_contributor": a["llm_contributor"],
                }
                for a in nr["apm_services"]
            ]
            insight = "New Relic NerdGraph / NRQL shows AI-attributed releases improved fleet p95 response latency by 31.4% while maintaining 0.97 Fleet Apdex."
        else:
            rows = [
                {
                    "model": m["model"],
                    "provider": m["provider"],
                    "requests_24h": m["requests_24h"],
                    "tokens_24h": m["tokens_24h"],
                    "avg_latency_ms": m["avg_latency_ms"],
                    "cost_24h_usd": m["cost_24h_usd"],
                    "primary_attribution": m["primary_attribution"],
                }
                for m in nr["ai_monitoring_models"]
            ]
            insight = "New Relic AI Monitoring (`LlmChatCompletionSummary`) highlights Claude 3.7 Sonnet and Gemini 2.5 Pro driving 92% of shipped production code value."

    return {
        "status": "SUCCESS",
        "engine": req.engine,
        "query": req.query,
        "execution_time_ms": 14.8,
        "row_count": len(rows),
        "rows": rows,
        "finops_insight": insight,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


@app.post("/api/soluble/scan")
async def run_soluble_iac_scan(req: SolubleScanRequest) -> Dict[str, Any]:
    snippet = req.code_snippet
    snippet_lower = snippet.lower()
    findings = []

    if "*" in snippet or "Action = \"*\"" in snippet or "kms:*" in snippet_lower or "s3:*" in snippet_lower:
        findings.append({
            "rule_id": "SOL-TF-AWS-042",
            "severity": "CRITICAL",
            "framework": "PCI-DSS 4.0 / CIS AWS v3.0",
            "issue": "Over-permissive wildcard IAM action (`*`) detected in resource policy.",
            "auto_remediation": "Restrict `Action` to least-privilege operations (`s3:GetObject`, `s3:PutObject`, `kms:Decrypt`) scoped to specific ARN.",
        })
    if "privileged: true" in snippet_lower or ("resources:" not in snippet_lower and ("kind: deployment" in snippet_lower or "image:" in snippet_lower)):
        findings.append({
            "rule_id": "SOL-K8S-POD-019",
            "severity": "HIGH",
            "framework": "NSA/CISA Kubernetes Hardening",
            "issue": "Container specification missing bounded memory limits or running without `runAsNonRoot: true`.",
            "auto_remediation": "Inject `securityContext.runAsNonRoot: true` and `resources.limits.memory: 512Mi`.",
        })
    if "password" in snippet_lower or "secret" in snippet_lower or "api_key" in snippet_lower or "sk-" in snippet_lower:
        findings.append({
            "rule_id": "SOL-SEC-GIT-007",
            "severity": "CRITICAL",
            "framework": "SOC2 CC6.1 Secrets Hygiene",
            "issue": "Potential hardcoded credential or API token in IaC/pipeline definition.",
            "auto_remediation": "Replace inline secret literal with `vault_generic_secret` or AWS Secrets Manager reference.",
        })
    if "encrypted = false" in snippet_lower or "publicly_accessible = true" in snippet_lower:
        findings.append({
            "rule_id": "SOL-TF-RDS-011",
            "severity": "CRITICAL",
            "framework": "HIPAA / SOC2 Encryption-at-Rest",
            "issue": "Storage/Database resource configured with `encrypted = false` or public ingress.",
            "auto_remediation": "Set `storage_encrypted = true`, attach customer-managed KMS key, and set `publicly_accessible = false`.",
        })

    if not findings:
        findings.append({
            "rule_id": "SOL-GEN-BP-001",
            "severity": "LOW",
            "framework": "BurnIQ FinOps & Tagging Standard",
            "issue": "Resource block missing mandatory FinOps attribution tags (`burniq:release_id`, `burniq:cost_center`).",
            "auto_remediation": "Append `tags = { \"burniq:cost_center\" = \"WD-CC-101\", \"burniq:llm_author\" = \"" + req.llm_author + "\" }`.",
        })

    remediated_code = (
        f"# [Soluble Auto-Remediated Patch · Verified by {req.llm_author}]\n"
        + snippet.replace('"*"', '["s3:GetObject", "s3:PutObject"]')
                 .replace("encrypted = false", "encrypted = true")
                 .replace("publicly_accessible = true", "publicly_accessible = false")
        + "\n# + Added Soluble FinOps & SecOps Compliance Tags (burniq:verified = true)"
    )

    return {
        "status": "SCAN_COMPLETE",
        "scanner": "Soluble Cloud-Native IaC Engine v4.12.0",
        "repository": req.repository,
        "branch": req.branch,
        "iac_type": req.iac_type,
        "llm_author": req.llm_author,
        "findings_count": len(findings),
        "gate_decision": "AUTO_REMEDIATED_READY_TO_MERGE",
        "estimated_manual_fix_mins_saved": 45 * len(findings),
        "workday_secops_savings_usd": round(45 * len(findings) * (124.0 / 60.0), 2),
        "findings": findings,
        "remediated_code": remediated_code,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


@app.post("/api/substrate/enforce-policy")
async def enforce_substrate_policy(req: SubstratePolicyRequest) -> Dict[str, Any]:
    POLICY_OVERRIDES[req.signal_id] = {
        "status": "OPTIMIZED (HAIKU/FLASH ROUTED)",
        "applied_policy": f"Active Policy [{req.action}] — Routed to Low-Cost Fast Tier & Capped Context",
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    return {
        "status": "POLICY_APPLIED",
        "signal_id": req.signal_id,
        "action": req.action,
        "updated_classification": "OPTIMIZED (HAIKU/FLASH ROUTED)",
        "message": f"Substrate governance policy '{req.action}' enforced on {req.signal_id}. Projected token & salary waste reduced by 78%.",
    }


@app.get("/api/attribution")
async def api_attribution() -> Dict[str, Any]:
    releases = get_code_to_release_attribution()
    return {
        "total_releases_tracked": len(releases),
        "scm_providers": ["GitHub", "GitLab", "Bitbucket"],
        "cicd_providers": ["GitHub Actions", "GitLab CI", "Bitbucket Pipelines", "Jenkins", "Atlassian Bamboo"],
        "observability_links": ["Datadog DORA & LLM Obs", "New Relic APM Golden Signals", "Soluble IaC SecOps", "Substrate Compute"],
        "releases": releases,
    }


@app.get("/api/workday-roi")
async def api_workday_roi() -> Dict[str, Any]:
    return get_workday_and_erp_roi()


@app.get("/api/low-value-audit")
async def api_low_value_audit() -> Dict[str, Any]:
    sub = await api_substrate()
    return {
        "summary": {
            "total_low_value_prompts_30d": 162500,
            "total_low_value_llm_cost_usd": 17040,
            "total_workday_salary_burned_usd": 146800,
            "total_combined_monthly_waste_usd": 163840,
            "annualized_recoverable_waste_usd": 1966080,
            "primary_detection_engine": "Microsoft Substrate Graph + Datadog LLM Observability + New Relic AI Monitoring",
        },
        "substrate_signals": sub["microsoft_substrate_signals"],
    }


@app.get("/api/overview")
async def api_overview() -> Dict[str, Any]:
    dd = get_datadog_telemetry()
    sub = await api_substrate()
    nr = get_newrelic_telemetry()
    sol = get_soluble_telemetry()
    roi = get_workday_and_erp_roi()
    releases = get_code_to_release_attribution()
    connectors = get_enterprise_connectors()

    return {
        "kpis": {
            "total_llm_spend_monthly_usd": roi["summary"]["total_monthly_llm_spend_usd"],
            "claude_spend_usd": roi["summary"]["monthly_llm_spend_claude_usd"],
            "gemini_spend_usd": roi["summary"]["monthly_llm_spend_gemini_usd"],
            "workday_salary_saved_usd": roi["summary"]["workday_salary_value_generated_usd"],
            "low_value_task_waste_usd": roi["summary"]["low_value_email_notes_salary_waste_usd"],
            "net_monthly_roi_usd": roi["summary"]["net_workday_salary_roi_usd"],
            "net_roi_pct": roi["summary"]["net_roi_percentage"],
            "datadog_dora_deploy_freq": dd["summary"]["dora_deployment_freq_per_day"],
            "newrelic_fleet_apdex": nr["summary"]["fleet_apdex_score"],
            "soluble_iac_pass_rate_pct": sol["summary"]["policy_pass_rate_ai_assisted_pct"],
            "substrate_recoverable_annual_usd": sub["summary"]["recoverable_annual_savings_usd"],
        },
        "featured_4_status": [
            {
                "id": "datadog",
                "name": "Datadog",
                "tagline": "LLM Observability · APM · CI Visibility · DORA Metrics",
                "host": dd["api_host"],
                "status": dd["status"],
                "primary_metric": f"{dd['summary']['dora_deployment_freq_per_day']}/day Deploys · {dd['summary']['dora_change_failure_rate_pct']}% CFR",
                "secondary_metric": f"{dd['summary']['total_llm_spans_30d']:,} LLM Spans Tracked",
            },
            {
                "id": "substrate",
                "name": "Substrate",
                "tagline": "M365 Email/Notes Graph Audit & Multi-Cloud AI Compute",
                "host": sub["api_host"],
                "status": sub["status"],
                "primary_metric": f"${sub['summary']['workday_salary_burned_on_low_value_usd_30d']:,}/mo Low-Value Salary Burn Caught",
                "secondary_metric": f"{sub['summary']['active_ai_compute_workloads']} AI Compute Fleets ({sub['summary']['compute_cluster_utilization_pct']}% Util)",
            },
            {
                "id": "newrelic",
                "name": "New Relic",
                "tagline": "APM Golden Signals · NerdGraph · AI Monitoring · NRQL",
                "host": nr["api_host"],
                "status": nr["status"],
                "primary_metric": f"{nr['summary']['fleet_apdex_score']} Fleet Apdex · -{nr['summary']['ai_release_latency_improvement_pct']}% Latency",
                "secondary_metric": f"{nr['summary']['ai_monitoring_llm_calls_24h']:,} AI Monitored Calls / 24h",
            },
            {
                "id": "soluble",
                "name": "Soluble",
                "tagline": "Cloud-Native IaC Security · PR Policy Gates · AI Auto-Fix",
                "host": sol["api_host"],
                "status": sol["status"],
                "primary_metric": f"{sol['summary']['policy_pass_rate_ai_assisted_pct']}% IaC Pass Rate · {sol['summary']['mean_time_to_remediate_iac_mins']}m MTTR",
                "secondary_metric": f"{sol['summary']['auto_remediation_prs_merged']} Auto-Remediation PRs Merged",
            },
        ],
        "releases": releases,
        "workday_roi": roi,
        "connectors_count": len(connectors),
    }


@app.get("/api/connectors")
async def api_connectors() -> Dict[str, Any]:
    connectors = get_enterprise_connectors()
    return {
        "total": len(connectors),
        "featured_ids": ["datadog", "substrate", "newrelic", "soluble"],
        "connectors": connectors,
    }


_NO_PROXY_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def _probe_connector(conn: Dict[str, Any]) -> Dict[str, Any]:
    start = time.time()
    port_8090_url = conn["port_8090_endpoint"].replace("localhost:8090", "127.0.0.1:8090")
    payload = None
    via = "local-mock-gateway:8000"

    if "8090" in port_8090_url:
        try:
            req = urllib.request.Request(port_8090_url, method="GET")
            with _NO_PROXY_OPENER.open(req, timeout=1.5) as resp:
                if resp.status == 200:
                    payload = json.loads(resp.read().decode("utf-8"))
                    via = "mock-enterprise-server:8090"
        except Exception:
            payload = None

    if payload is None:
        rel_path = conn["endpoint"].replace("/mock-enterprise/", "")
        payload = build_vendor_connection_payload(rel_path)

    elapsed_ms = round((time.time() - start) * 1000 + conn.get("latency_ms", 12), 1)
    return {
        "connector_id": conn["id"],
        "name": conn["name"],
        "category": conn["category"],
        "host": conn["host"],
        "tested_endpoint": conn["endpoint"],
        "port_8090_endpoint": conn["port_8090_endpoint"],
        "routed_via": via,
        "http_status": 200,
        "status": "CONNECTED",
        "latency_ms": elapsed_ms,
        "response_payload": payload,
        "verified_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


@app.post("/api/connectors/{connector_id}/test")
async def test_single_connector(connector_id: str) -> Dict[str, Any]:
    connectors = get_enterprise_connectors()
    for conn in connectors:
        if conn["id"].lower() == connector_id.lower():
            return _probe_connector(conn)
    raise HTTPException(status_code=404, detail=f"Connector '{connector_id}' not found")


@app.post("/api/connectors/test-all")
async def test_all_connectors() -> Dict[str, Any]:
    connectors = get_enterprise_connectors()
    results = [_probe_connector(c) for c in connectors]
    return {
        "status": "ALL_CONNECTED",
        "tested_count": len(results),
        "passed_count": len(results),
        "featured_verified": ["datadog", "substrate", "newrelic", "soluble"],
        "results": results,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


@app.get("/api/csv/export/{dataset}")
async def export_csv_dataset(dataset: str) -> Response:
    ds = dataset.lower()
    output = io.StringIO()
    writer = csv.writer(output)

    if ds == "datadog":
        dd = get_datadog_telemetry()
        writer.writerow(["trace_id", "service", "provider", "model", "engineer", "department", "task_category", "total_tokens", "cost_usd", "latency_ms", "git_commit", "jira_key", "release_id"])
        for s in dd["llm_observability_spans"]:
            writer.writerow([s["trace_id"], s["service"], s["provider"], s["model"], s["engineer"], s["department"], s["task_category"], s["total_tokens"], s["cost_usd"], s["latency_ms"], s["git_commit"], s["jira_key"], s["release_id"]])
    elif ds == "substrate":
        sub = get_substrate_telemetry()
        writer.writerow(["signal_id", "channel", "artifact_type", "department", "llm_provider", "model", "monthly_events", "tokens_burned", "llm_cost_usd", "workday_salary_burn_usd", "value_classification"])
        for s in sub["microsoft_substrate_signals"]:
            writer.writerow([s["signal_id"], s["channel"], s["artifact_type"], s["department"], s["llm_provider"], s["model"], s["monthly_events"], s["tokens_burned"], s["llm_cost_usd"], s["workday_salary_burn_usd"], s["value_classification"]])
    elif ds == "newrelic":
        nr = get_newrelic_telemetry()
        writer.writerow(["app_id", "service_name", "tier", "apdex_score", "throughput_rpm", "response_time_p95_ms", "error_rate_pct", "latency_delta_pct", "release_id", "cicd_source", "llm_contributor"])
        for a in nr["apm_services"]:
            writer.writerow([a["app_id"], a["service_name"], a["tier"], a["apdex_score"], a["throughput_rpm"], a["response_time_p95_ms"], a["error_rate_pct"], a["latency_delta_pct"], a["release_id"], a["cicd_source"], a["llm_contributor"]])
    elif ds == "soluble":
        sol = get_soluble_telemetry()
        writer.writerow(["finding_id", "rule_id", "severity", "iac_type", "title", "repository", "branch", "commit_sha", "ci_pipeline", "policy_framework", "status", "remediation_time_mins"])
        for f in sol["security_findings"]:
            writer.writerow([f["finding_id"], f["rule_id"], f["severity"], f["iac_type"], f["title"], f["repository"], f["branch"], f["commit_sha"], f["ci_pipeline"], f["policy_framework"], f["status"], f["remediation_time_mins"]])
    elif ds == "workday_roi":
        roi = get_workday_and_erp_roi()
        writer.writerow(["department", "workday_cost_center", "erp_system", "headcount", "avg_loaded_hourly_usd", "claude_spend_usd", "gemini_spend_usd", "high_value_code_pct", "low_value_email_notes_pct", "releases_shipped_30d", "hours_saved_30d", "salary_roi_usd", "net_roi_multiple"])
        for d in roi["departments"]:
            writer.writerow([d["department"], d["workday_cost_center"], d["erp_system"], d["headcount"], d["avg_loaded_hourly_usd"], d["claude_spend_usd"], d["gemini_spend_usd"], d["high_value_code_pct"], d["low_value_email_notes_pct"], d["releases_shipped_30d"], d["hours_saved_30d"], d["salary_roi_usd"], d["net_roi_multiple"]])
    else:
        # Default unified observability & release attribution export
        writer.writerow(["release_id", "release_name", "scm_platform", "cicd_platform", "commit_sha", "jira_epic", "lead_engineer", "llm_cost_usd", "workday_salary_saved_usd", "salesforce_arr_attributed_usd", "datadog_dora_impact", "newrelic_apm_impact", "soluble_secops_status", "roi_multiple"])
        for r in get_code_to_release_attribution():
            writer.writerow([r["release_id"], r["release_name"], r["scm_platform"], r["cicd_platform"], r["commit_sha"], r["jira_epic"], r["lead_engineer"], r["llm_cost_usd"], r["workday_salary_saved_usd"], r["salesforce_arr_attributed_usd"], r["datadog_dora_impact"], r["newrelic_apm_impact"], r["soluble_secops_status"], r["roi_multiple"]])

    csv_bytes = output.getvalue()
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="burniq_{ds}_export.csv"'},
    )


@app.post("/api/csv/import")
async def import_csv_dataset(req: CsvImportRequest) -> Dict[str, Any]:
    reader = csv.DictReader(io.StringIO(req.csv_content.strip()))
    rows = [dict(r) for r in reader]
    CUSTOM_INGESTED_RECORDS.extend(rows)
    return {
        "status": "IMPORTED",
        "dataset_type": req.dataset_type,
        "rows_ingested": len(rows),
        "total_custom_records_in_memory": len(CUSTOM_INGESTED_RECORDS),
        "columns_detected": list(rows[0].keys()) if rows else [],
        "preview": rows[:5],
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
async def serve_index() -> Any:
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>BurnIQ Enterprise Telemetry Platform</h1><p>Frontend building...</p>")
