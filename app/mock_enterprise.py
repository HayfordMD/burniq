"""
Mock Enterprise Gateway for BurnIQ Telemetry & ROI Platform.

Serves realistic enterprise REST/GraphQL/Events responses on:
- Port 8090 directly (`http://localhost:8090/<host>/<path>`)
- Port 8000 under `/mock-enterprise` (`http://localhost:8000/mock-enterprise/<host>/<path>`)

Includes full PagerDuty REST/Events API v2 (`api.pagerduty.com`) and
Atlassian Opsgenie Alert/Heartbeat/Schedule API v2 (`api.opsgenie.com`),
plus Sage Intacct/X3, Oracle NetSuite OneWorld, Workday, Jira, ServiceNow,
Zendesk, Power BI, GitHub, GitLab, Bitbucket, Jenkins, Bamboo, Salesforce,
SAP, Datadog, Substrate, New Relic, Soluble, Claude, and Gemini.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict

from fastapi import APIRouter, Body, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.data_store import STORE, _now_iso
from burniq.data_store import store as erp_store

mock_router = APIRouter()


HOST_TO_CONNECTOR_ID: Dict[str, str] = {
    "api.pagerduty.com": "pagerduty",
    "events.pagerduty.com": "pagerduty",
    "company.pagerduty.com": "pagerduty",
    "api.opsgenie.com": "opsgenie",
    "api.eu.opsgenie.com": "opsgenie",
    "api.genie.com": "opsgenie",
    "company.opsgenie.com": "opsgenie",
    "api.anthropic.com": "claude",
    "generativelanguage.googleapis.com": "gemini",
    "us-central1-aiplatform.googleapis.com": "gemini",
    "api.github.com": "github",
    "gitlab.com": "gitlab",
    "gitlab.company.com": "gitlab",
    "api.bitbucket.org": "bitbucket",
    "jenkins.company.com": "jenkins",
    "bamboo.company.com": "bamboo",
    "company.atlassian.net": "jira",
    "company.service-now.com": "servicenow",
    "company.zendesk.com": "zendesk",
    "api.datadoghq.com": "datadog",
    "api.newrelic.com": "newrelic",
    "api.substrate.com": "substrate",
    "api.substrate.run": "substrate",
    "api.soluble.io": "soluble",
    "app.soluble.cloud": "soluble",
    "company.workday.com": "workday",
    "company.my.salesforce.com": "salesforce",
    "api.sap.com": "sap",
    "company.sap.com": "sap",
    "api.intacct.com": "sage",
    "company.sage.com": "sage",
    "company.suitetalk.api.netsuite.com": "netsuite",
    "company.netsuite.com": "netsuite",
    "api.netsuite.com": "netsuite",
    "api.powerbi.com": "powerbi",
}


# ----------------------------------------------------------------------
# PAGERDUTY MOCK ENDPOINTS (api.pagerduty.com & events.pagerduty.com)
# ----------------------------------------------------------------------
@mock_router.get("/api.pagerduty.com/v2/connection")
@mock_router.get("/api.pagerduty.com/connection")
@mock_router.get("/events.pagerduty.com/v2/connection")
def mock_pagerduty_connection() -> Dict[str, Any]:
    conn = STORE.connectors["pagerduty"]
    return {
        "ok": True,
        "status": "connected",
        "provider": "PagerDuty Enterprise",
        "host": "api.pagerduty.com",
        "api_version": "v2",
        "events_api": "https://events.pagerduty.com/v2/enqueue",
        "Abilities": [
            "incidents",
            "services",
            "schedules",
            "escalation_policies",
            "events_v2",
            "change_events",
            "llm_mttr_attribution",
        ],
        "latency_ms": conn["latency_ms"],
        "active_incidents": sum(
            1 for i in STORE.pagerduty_incidents if i["status"] != "resolved"
        ),
        "total_incidents": len(STORE.pagerduty_incidents),
        "services_count": len(STORE.pagerduty_services),
        "schedules_count": len(STORE.pagerduty_schedules),
        "checked_at": _now_iso(),
    }


@mock_router.get("/api.pagerduty.com/incidents")
@mock_router.get("/api.pagerduty.com/v2/incidents")
def mock_pagerduty_incidents() -> Dict[str, Any]:
    return {
        "incidents": STORE.pagerduty_incidents,
        "limit": 25,
        "offset": 0,
        "total": len(STORE.pagerduty_incidents),
        "more": False,
    }


@mock_router.post("/api.pagerduty.com/v2/enqueue")
@mock_router.post("/events.pagerduty.com/v2/enqueue")
@mock_router.post("/api.pagerduty.com/incidents")
def mock_pagerduty_enqueue(
    payload: Dict[str, Any] = Body(default_factory=dict),
) -> Dict[str, Any]:
    inc = STORE.trigger_pagerduty_incident(payload)
    return {
        "status": "success",
        "message": "Event processed",
        "dedup_key": inc["dedup_key"],
        "incident": inc,
    }


@mock_router.get("/api.pagerduty.com/services")
@mock_router.get("/api.pagerduty.com/v2/services")
def mock_pagerduty_services() -> Dict[str, Any]:
    return {
        "services": STORE.pagerduty_services,
        "total": len(STORE.pagerduty_services),
    }


@mock_router.get("/api.pagerduty.com/schedules")
@mock_router.get("/api.pagerduty.com/v2/schedules")
@mock_router.get("/api.pagerduty.com/oncalls")
def mock_pagerduty_schedules() -> Dict[str, Any]:
    return {
        "schedules": STORE.pagerduty_schedules,
        "total": len(STORE.pagerduty_schedules),
    }


# ----------------------------------------------------------------------
# OPSGENIE ("GENIE") MOCK ENDPOINTS (api.opsgenie.com & api.genie.com)
# ----------------------------------------------------------------------
@mock_router.get("/api.opsgenie.com/v2/connection")
@mock_router.get("/api.opsgenie.com/connection")
@mock_router.get("/api.genie.com/v2/connection")
def mock_opsgenie_connection() -> Dict[str, Any]:
    conn = STORE.connectors["opsgenie"]
    return {
        "ok": True,
        "result": "Connected",
        "status": "connected",
        "provider": "Atlassian Opsgenie (Genie)",
        "host": "api.opsgenie.com",
        "api_version": "v2",
        "capabilities": [
            "alerts_v2",
            "incidents_v1",
            "heartbeats_v2",
            "schedules_v2",
            "teams_v2",
            "genie_llm_runbooks",
        ],
        "latency_ms": conn["latency_ms"],
        "open_alerts": sum(
            1 for a in STORE.opsgenie_alerts if a["status"] != "closed"
        ),
        "total_alerts": len(STORE.opsgenie_alerts),
        "healthy_heartbeats": sum(
            1 for h in STORE.opsgenie_heartbeats if not h.get("expired", False)
        ),
        "teams_count": len(STORE.opsgenie_teams),
        "checked_at": _now_iso(),
    }


@mock_router.get("/api.opsgenie.com/v2/alerts")
@mock_router.get("/api.opsgenie.com/v2/incidents")
@mock_router.get("/api.genie.com/v2/alerts")
def mock_opsgenie_alerts() -> Dict[str, Any]:
    return {
        "data": STORE.opsgenie_alerts,
        "paging": {"first": "/v2/alerts?offset=0", "last": "/v2/alerts?offset=0"},
        "took": 0.018,
        "requestId": str(uuid.uuid4()),
    }


@mock_router.post("/api.opsgenie.com/v2/alerts")
@mock_router.post("/api.genie.com/v2/alerts")
def mock_opsgenie_create_alert(
    payload: Dict[str, Any] = Body(default_factory=dict),
) -> Dict[str, Any]:
    alert = STORE.create_opsgenie_alert(payload)
    return {
        "result": "Request will be processed",
        "took": 0.014,
        "requestId": str(uuid.uuid4()),
        "alert": alert,
    }


@mock_router.post("/api.opsgenie.com/v2/alerts/{alert_id}/{action}")
@mock_router.post("/api.genie.com/v2/alerts/{alert_id}/{action}")
def mock_opsgenie_alert_action(alert_id: str, action: str) -> Dict[str, Any]:
    updated = STORE.update_opsgenie_alert_status(alert_id, action)
    return {
        "result": f"Alert {alert_id} action '{action}' processed",
        "took": 0.012,
        "requestId": str(uuid.uuid4()),
        "alert": updated,
    }


@mock_router.get("/api.opsgenie.com/v2/schedules")
@mock_router.get("/api.genie.com/v2/schedules")
def mock_opsgenie_schedules() -> Dict[str, Any]:
    return {
        "data": STORE.opsgenie_schedules,
        "took": 0.011,
        "requestId": str(uuid.uuid4()),
    }


@mock_router.get("/api.opsgenie.com/v2/teams")
@mock_router.get("/api.genie.com/v2/teams")
def mock_opsgenie_teams() -> Dict[str, Any]:
    return {
        "data": STORE.opsgenie_teams,
        "took": 0.010,
        "requestId": str(uuid.uuid4()),
    }


@mock_router.get("/api.opsgenie.com/v2/heartbeats")
@mock_router.get("/api.genie.com/v2/heartbeats")
def mock_opsgenie_heartbeats() -> Dict[str, Any]:
    return {
        "data": {"heartbeats": STORE.opsgenie_heartbeats},
        "took": 0.009,
        "requestId": str(uuid.uuid4()),
    }


@mock_router.get("/api.opsgenie.com/v2/heartbeats/{name}/ping")
@mock_router.post("/api.opsgenie.com/v2/heartbeats/{name}/ping")
@mock_router.post("/api.genie.com/v2/heartbeats/{name}/ping")
def mock_opsgenie_heartbeat_ping(name: str) -> Dict[str, Any]:
    hb = STORE.ping_opsgenie_heartbeat(name)
    return {
        "result": "Pinging heartbeat is successful",
        "took": 0.006,
        "requestId": str(uuid.uuid4()),
        "heartbeat": hb,
    }


# ----------------------------------------------------------------------
# SAGE INTACCT / X3 & ORACLE NETSUITE ONEWORLD MOCK ENDPOINTS
# ----------------------------------------------------------------------
@mock_router.get("/api.intacct.com/ia/api/v1/connection")
@mock_router.get("/company.sage.com/api/v1/connection")
async def sage_intacct_connection() -> Dict[str, Any]:
    sage = erp_store.state["sage_erp"]
    return {
        "ok": True,
        "provider": "Sage Intacct & Sage X3 Enterprise",
        "protocol": "Sage Intacct REST API v1 & XML Gateway",
        "company_id": sage["company_id"],
        "status": "connected",
        "entities_active": [e["entity_id"] for e in sage["entities"]],
        "gl_accounts_count": len(sage["gl_accounts"]),
        "gl_batches_count": len(sage["gl_batches"]),
        "vendor_bills_count": len(sage["vendor_bills"]),
        "asc_350_40_capex_enabled": True,
        "timestamp": _now_iso(),
    }


@mock_router.get("/company.suitetalk.api.netsuite.com/services/rest/record/v1/connection")
@mock_router.get("/company.netsuite.com/api/v1/connection")
async def oracle_netsuite_connection() -> Dict[str, Any]:
    ns = erp_store.state["oracle_netsuite"]
    return {
        "ok": True,
        "provider": "Oracle NetSuite OneWorld Enterprise",
        "protocol": "SuiteTalk REST Web Services v1 + SuiteQL Analytics",
        "account_id": ns["account_id"],
        "status": "connected",
        "subsidiaries_active": [s["internal_id"] for s in ns["subsidiaries"]],
        "journal_entries_count": len(ns["journal_entries"]),
        "purchase_orders_count": len(ns["purchase_orders"]),
        "amortization_schedules_count": len(ns["amortization_schedules"]),
        "oauth2_m2m_token_valid": True,
        "timestamp": _now_iso(),
    }


# ----------------------------------------------------------------------
# UNIVERSAL ENTERPRISE MOCK ROUTER (Workday, Power BI, Zendesk, ServiceNow,
# Sage, NetSuite, Datadog, Substrate, New Relic, Soluble, SAP, Salesforce, etc.)
# ----------------------------------------------------------------------
@mock_router.get("/health")
@mock_router.get("/api/health")
def mock_gateway_health() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "service": "BurnIQ Mock Enterprise Gateway",
        "port": 8090,
        "supported_hosts": list(HOST_TO_CONNECTOR_ID.keys()),
        "timestamp": _now_iso(),
    }


from backend.observability_mock import build_vendor_connection_payload


@mock_router.api_route(
    "/{host}/{rest_of_path:path}", methods=["GET", "POST", "PUT", "PATCH"]
)
async def mock_universal_enterprise_endpoint(
    host: str, rest_of_path: str, request: Request
) -> Dict[str, Any]:
    connector_id = HOST_TO_CONNECTOR_ID.get(host.lower())
    connector = (
        STORE.connectors.get(connector_id)
        if connector_id
        else {
            "id": host.split(".")[0],
            "name": host,
            "category": "Enterprise Integration",
            "host": host,
            "protocol": "REST API",
            "status": "connected",
            "latency_ms": 20,
            "records_synced": 1000,
            "highlights": "Connected via BurnIQ Enterprise Gateway",
        }
    )
    circuit_state = "ON"
    try:
        from backend.database import get_connection
        db_conn = get_connection()
        cur = db_conn.cursor()
        cur.execute(
            "SELECT enabled FROM service_connections WHERE endpoint_url LIKE ?",
            (f"%{host}%",),
        )
        row = cur.fetchone()
        db_conn.close()
        if row is not None and not bool(row["enabled"]):
            circuit_state = "OFF"
    except Exception:
        pass

    vendor_payload = build_vendor_connection_payload(f"{host}/{rest_of_path}")
    return {
        **vendor_payload,
        "circuit_state": circuit_state,
        "status": "connected",
        "ok": True,
        "host": host,
        "path": f"/{rest_of_path}",
        "method": request.method,
        "connector": connector,
        "timestamp": _now_iso(),
    }


# Standalone FastAPI app for port 8090
mock_app = FastAPI(
    title="BurnIQ Mock Enterprise Gateway (Port 8090)",
    version="2.6.0",
)
mock_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
mock_app.include_router(mock_router)

# Alias `app` so `uvicorn mock_enterprise:app` and `uvicorn app.mock_enterprise:mock_app` both work
app = mock_app
