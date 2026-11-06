"""
BurnIQ Mock Enterprise Sandbox Server (Port 8090 & mounted at /mock-enterprise on Port 8000).
Simulates realistic enterprise REST & GraphQL APIs for:
- Datadog (api.datadoghq.com)
- Substrate (substrate.office.com & api.substrate.run)
- New Relic (api.newrelic.com & one.newrelic.com)
- Soluble (api.soluble.io)
- Workday HRM, SAP, Sage Intacct, Oracle NetSuite, Salesforce, Power BI
- GitHub, GitLab, Bitbucket, Jenkins, Bamboo
- Jira, ServiceNow, Zendesk, PagerDuty, Opsgenie
- Anthropic Claude, Google Gemini
"""

from datetime import datetime
from typing import Dict, Any
from fastapi import FastAPI, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware

from backend.telemetry_data import (
    get_datadog_telemetry,
    get_substrate_telemetry,
    get_newrelic_telemetry,
    get_soluble_telemetry,
    get_enterprise_connectors,
)

mock_router = APIRouter()


def build_vendor_connection_payload(full_path: str) -> Dict[str, Any]:
    path_lower = full_path.lower().strip("/")
    now_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    if "datadoghq.com" in path_lower:
        dd = get_datadog_telemetry()
        if "spans" in path_lower or "llm-obs" in path_lower:
            return {"status": "CONNECTED", "http_status": 200, "vendor": "Datadog LLM Observability", "data": dd["llm_observability_spans"]}
        if "dora" in path_lower:
            return {"status": "CONNECTED", "http_status": 200, "vendor": "Datadog DORA Metrics", "data": dd["dora_comparison"]}
        if "monitor" in path_lower:
            return {"status": "CONNECTED", "http_status": 200, "vendor": "Datadog APM Monitors", "data": dd["apm_monitors"]}
        return {
            "status": "CONNECTED",
            "http_status": 200,
            "authenticated": True,
            "vendor": "Datadog",
            "host": "api.datadoghq.com",
            "endpoint": f"/{full_path}",
            "site": dd["site"],
            "agent_version": dd["agent_version"],
            "scopes": ["llm_observability_read", "apm_read", "ci_visibility_read", "dora_metrics_read", "monitors_read"],
            "telemetry_summary": dd["summary"],
            "timestamp": now_iso,
        }

    if "substrate.office.com" in path_lower or "substrate.run" in path_lower or "substrate" in path_lower:
        sub = get_substrate_telemetry()
        if "signals" in path_lower or "low-value" in path_lower:
            return {"status": "CONNECTED", "http_status": 200, "vendor": "Microsoft Substrate Graph", "data": sub["microsoft_substrate_signals"]}
        if "workloads" in path_lower:
            return {"status": "CONNECTED", "http_status": 200, "vendor": "Substrate AI Compute", "data": sub["substrate_compute_workloads"]}
        return {
            "status": "CONNECTED",
            "http_status": 200,
            "authenticated": True,
            "vendor": "Substrate (M365 Knowledge Graph & AI Compute)",
            "host": "substrate.office.com / api.substrate.run",
            "endpoint": f"/{full_path}",
            "tenant_id": sub["tenant_id"],
            "scopes": ["Substrate.Mail.Read", "Substrate.TeamsNotes.Audit", "Substrate.Compute.Telemetry"],
            "telemetry_summary": sub["summary"],
            "timestamp": now_iso,
        }

    if "newrelic.com" in path_lower or "newrelick" in path_lower:
        nr = get_newrelic_telemetry()
        if "apm" in path_lower or "applications" in path_lower:
            return {"status": "CONNECTED", "http_status": 200, "vendor": "New Relic APM", "data": nr["apm_services"]}
        if "ai-monitoring" in path_lower or "models" in path_lower:
            return {"status": "CONNECTED", "http_status": 200, "vendor": "New Relic AI Monitoring", "data": nr["ai_monitoring_models"]}
        return {
            "status": "CONNECTED",
            "http_status": 200,
            "authenticated": True,
            "vendor": "New Relic",
            "host": "api.newrelic.com",
            "endpoint": f"/{full_path}",
            "account_id": nr["account_id"],
            "protocol": "NerdGraph GraphQL + REST v2 + NRQL",
            "scopes": ["APM.GoldenSignals", "AIMonitoring.LlmSummary", "ChangeTracking.Deployments", "NRQL.Query"],
            "telemetry_summary": nr["summary"],
            "timestamp": now_iso,
        }

    if "soluble.io" in path_lower or "soluble.cloud" in path_lower or "soluble" in path_lower:
        sol = get_soluble_telemetry()
        if "findings" in path_lower:
            return {"status": "CONNECTED", "http_status": 200, "vendor": "Soluble IaC Findings", "data": sol["security_findings"]}
        if "assessments" in path_lower:
            return {"status": "CONNECTED", "http_status": 200, "vendor": "Soluble IaC Assessments", "data": sol["ai_vs_human_posture"]}
        return {
            "status": "CONNECTED",
            "http_status": 200,
            "authenticated": True,
            "vendor": "Soluble Cloud-Native IaC Security",
            "host": "api.soluble.io",
            "endpoint": f"/{full_path}",
            "org_id": sol["org_id"],
            "scanner_version": sol["scanner_version"],
            "scopes": ["iac.terraform.scan", "iac.k8s.scan", "iac.helm.scan", "secrets.detect", "pr.autofix"],
            "telemetry_summary": sol["summary"],
            "timestamp": now_iso,
        }

    # Match against all other known connectors
    for conn in get_enterprise_connectors():
        if conn["host"].lower() in path_lower or conn["id"].lower() in path_lower:
            return {
                "status": "CONNECTED",
                "authenticated": True,
                "vendor": conn["name"],
                "connector_id": conn["id"],
                "host": conn["host"],
                "endpoint": f"/{full_path}",
                "protocol": conn["protocol"],
                "records_synced": conn["records_synced"],
                "latency_ms": conn["latency_ms"],
                "timestamp": now_iso,
            }

    return {
        "status": "CONNECTED",
        "authenticated": True,
        "vendor": full_path.split("/")[0] if "/" in full_path else full_path,
        "endpoint": f"/{full_path}",
        "message": "Mock Enterprise Gateway connection verified",
        "timestamp": now_iso,
    }


@mock_router.get("/health")
async def mock_health() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "service": "burniq-mock-enterprise-gateway",
        "port": 8090,
        "vendors_online": 23,
        "featured_integrations": ["datadog", "substrate", "newrelic", "soluble"],
    }


@mock_router.api_route("/{full_path:path}", methods=["GET", "POST", "PUT"])
async def mock_enterprise_catchall(full_path: str, request: Request) -> Dict[str, Any]:
    return build_vendor_connection_payload(full_path)


mock_app = FastAPI(
    title="BurnIQ Mock Enterprise Telemetry Gateway",
    description="Simulates Datadog, Substrate, New Relic, Soluble, Workday, SAP, Sage, NetSuite, Salesforce, Power BI, GitHub, GitLab, Bitbucket, Jenkins, Bamboo, Jira, ServiceNow, Zendesk, PagerDuty, and Opsgenie.",
    version="2.4.0",
)

mock_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

mock_app.include_router(mock_router)
