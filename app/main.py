"""
BurnIQ Enterprise Telemetry & ROI Platform — Main FastAPI Application (Port 8000).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import Body, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from app.data_store import STORE, _now_iso
from app.mock_enterprise import mock_router
from burniq.data_store import store as erp_store

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="BurnIQ Enterprise Telemetry & ROI Platform",
    description=(
        "Tracks corporate LLM usage (Claude & Gemini) across PagerDuty & Opsgenie "
        "incidents/alerts, code/commits/branches/CI-CD releases (GitHub, GitLab, "
        "Bitbucket, Jenkins, Bamboo), Jira, ServiceNow, Zendesk, Datadog, Substrate, "
        "New Relic, Soluble, Workday HRM salaries, Salesforce, SAP, Sage Intacct/X3, "
        "Oracle NetSuite, Power BI, CSVs, and low-value tasks (emails & notes)."
    ),
    version="2.6.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Mock Enterprise Gateway under /mock-enterprise on port 8000
app.include_router(mock_router, prefix="/mock-enterprise")


@app.get("/api/health")
def api_health() -> Dict[str, Any]:
    summary = STORE.get_executive_summary()
    return {
        "status": "ok",
        "healthy": True,
        "service": "burniq-enterprise-platform",
        "platform": summary["platform"],
        "version": summary["version"],
        "timestamp": _now_iso(),
        "pagerduty": {
            "status": "connected",
            "host": "api.pagerduty.com",
            "active_incidents": summary["pagerduty_summary"]["active_incidents"],
            "total_incidents": summary["pagerduty_summary"]["total_incidents"],
        },
        "opsgenie": {
            "status": "connected",
            "host": "api.opsgenie.com",
            "open_alerts": summary["opsgenie_summary"]["open_or_acked_alerts"],
            "total_alerts": summary["opsgenie_summary"]["total_alerts"],
            "healthy_heartbeats": summary["opsgenie_summary"]["heartbeats_healthy"],
        },
        "erp_integrations": {
            "sage": "CONNECTED (Sage Intacct REST v1 & Sage X3)",
            "oracle_netsuite": "CONNECTED (Oracle NetSuite OneWorld SuiteTalk REST & SuiteQL)",
            "sap": "CONNECTED (SAP S/4HANA OData v4)",
        },
        "connectors_connected": summary["connectors_connected"],
        "connectors_total": summary["connectors_total"],
    }


@app.get("/api/summary")
def api_summary() -> Dict[str, Any]:
    return STORE.get_executive_summary()


@app.get("/api/dashboard")
@app.get("/api/telemetry")
def api_dashboard() -> Dict[str, Any]:
    erp_summary = erp_store.get_dashboard_summary()
    return {
        **erp_summary,
        "summary": STORE.get_executive_summary(),
        "connectors": list(STORE.connectors.values()),
        "pagerduty": {
            "connector": STORE.connectors["pagerduty"],
            "incidents": STORE.pagerduty_incidents,
            "services": STORE.pagerduty_services,
            "schedules": STORE.pagerduty_schedules,
            "alert_rules": STORE.pagerduty_alert_rules,
        },
        "opsgenie": {
            "connector": STORE.connectors["opsgenie"],
            "alerts": STORE.opsgenie_alerts,
            "teams": STORE.opsgenie_teams,
            "schedules": STORE.opsgenie_schedules,
            "heartbeats": STORE.opsgenie_heartbeats,
        },
        "employees": STORE.employees,
        "commits_and_releases": STORE.commits_and_releases,
        "low_value_tasks": STORE.low_value_tasks,
        "erp_crm_records": STORE.erp_crm_records,
        "observability_events": STORE.observability_events,
        "csv_imports": STORE.csv_imports,
    }


# ----------------------------------------------------------------------
# ENTERPRISE CONNECTORS API
# ----------------------------------------------------------------------
@app.get("/api/connectors")
def api_list_connectors() -> Dict[str, Any]:
    conns = list(STORE.connectors.values())
    return {
        "total": len(conns),
        "count": len(conns),
        "connectors": conns,
    }


@app.post("/api/connectors/{connector_id}/test")
@app.get("/api/connectors/{connector_id}/test")
def api_test_connector(connector_id: str) -> Dict[str, Any]:
    cid = connector_id.lower()
    if cid in ("genie", "opsgenie-genie"):
        cid = "opsgenie"
    elif cid in ("pager-duty", "pd"):
        cid = "pagerduty"
    elif cid in ("oracle-netsuite", "oracle_netsuite"):
        cid = "netsuite"
    elif cid in ("sage-intacct", "sage_intacct"):
        cid = "sage"
    elif cid in ("new-relic", "new_relic"):
        cid = "newrelic"
    elif cid in ("service-now", "service_now"):
        cid = "servicenow"
    elif cid in ("power-bi", "power_bi"):
        cid = "powerbi"

    conn = STORE.connectors.get(cid)
    if not conn:
        raise HTTPException(status_code=404, detail=f"Connector '{connector_id}' not found")
    conn["last_sync"] = _now_iso()
    conn["status"] = "connected"
    return {
        "ok": True,
        "status": "connected",
        "verified": True,
        "connector": conn,
        "tested_at": _now_iso(),
    }


# ----------------------------------------------------------------------
# PAGERDUTY DEDICATED ENDPOINTS
# ----------------------------------------------------------------------
@app.get("/api/pagerduty/status")
def api_pagerduty_status() -> Dict[str, Any]:
    summary = STORE.get_executive_summary()["pagerduty_summary"]
    return {
        "connector": STORE.connectors["pagerduty"],
        "summary": summary,
        "services": STORE.pagerduty_services,
        "schedules": STORE.pagerduty_schedules,
        "alert_rules": STORE.pagerduty_alert_rules,
        "incidents": STORE.pagerduty_incidents,
    }


@app.get("/api/pagerduty/incidents")
def api_pagerduty_incidents(
    status: Optional[str] = None, priority: Optional[str] = None
) -> Dict[str, Any]:
    items = STORE.pagerduty_incidents
    if status:
        items = [i for i in items if i["status"].lower() == status.lower()]
    if priority:
        items = [i for i in items if i["priority"].upper() == priority.upper()]
    return {
        "total": len(items),
        "incidents": items,
    }


@app.post("/api/pagerduty/incidents")
def api_pagerduty_trigger_incident(
    payload: Dict[str, Any] = Body(default_factory=dict),
) -> Dict[str, Any]:
    inc = STORE.trigger_pagerduty_incident(payload)
    return {
        "status": "triggered",
        "incident": inc,
        "summary": STORE.get_executive_summary()["pagerduty_summary"],
    }


@app.post("/api/pagerduty/incidents/{incident_id}/{action}")
def api_pagerduty_incident_action(incident_id: str, action: str) -> Dict[str, Any]:
    inc = STORE.update_pagerduty_incident_status(incident_id, action)
    if not inc:
        raise HTTPException(
            status_code=404, detail=f"PagerDuty incident '{incident_id}' not found"
        )
    return {
        "status": "updated",
        "action": action,
        "incident": inc,
        "summary": STORE.get_executive_summary()["pagerduty_summary"],
    }


@app.get("/api/pagerduty/services")
def api_pagerduty_services() -> Dict[str, Any]:
    return {
        "total": len(STORE.pagerduty_services),
        "services": STORE.pagerduty_services,
    }


@app.get("/api/pagerduty/schedules")
@app.get("/api/pagerduty/oncalls")
def api_pagerduty_schedules() -> Dict[str, Any]:
    return {
        "total": len(STORE.pagerduty_schedules),
        "schedules": STORE.pagerduty_schedules,
    }


@app.get("/api/pagerduty/rules")
def api_pagerduty_rules() -> Dict[str, Any]:
    return {
        "total": len(STORE.pagerduty_alert_rules),
        "rules": STORE.pagerduty_alert_rules,
    }


@app.post("/api/pagerduty/sync")
def api_pagerduty_sync() -> Dict[str, Any]:
    STORE.connectors["pagerduty"]["last_sync"] = _now_iso()
    STORE.connectors["pagerduty"]["records_synced"] += 12
    return {
        "status": "synced",
        "connector": STORE.connectors["pagerduty"],
        "summary": STORE.get_executive_summary()["pagerduty_summary"],
    }


# ----------------------------------------------------------------------
# OPSGENIE ("GENIE") DEDICATED ENDPOINTS (/api/opsgenie/... & /api/genie/...)
# ----------------------------------------------------------------------
@app.get("/api/opsgenie/status")
@app.get("/api/genie/status")
def api_opsgenie_status() -> Dict[str, Any]:
    summary = STORE.get_executive_summary()["opsgenie_summary"]
    return {
        "connector": STORE.connectors["opsgenie"],
        "summary": summary,
        "alerts": STORE.opsgenie_alerts,
        "teams": STORE.opsgenie_teams,
        "schedules": STORE.opsgenie_schedules,
        "heartbeats": STORE.opsgenie_heartbeats,
    }


@app.get("/api/opsgenie/alerts")
@app.get("/api/genie/alerts")
def api_opsgenie_alerts(
    status: Optional[str] = None, priority: Optional[str] = None
) -> Dict[str, Any]:
    items = STORE.opsgenie_alerts
    if status:
        items = [a for a in items if a["status"].lower() == status.lower()]
    if priority:
        items = [a for a in items if a["priority"].upper() == priority.upper()]
    return {
        "total": len(items),
        "alerts": items,
    }


@app.post("/api/opsgenie/alerts")
@app.post("/api/genie/alerts")
def api_opsgenie_create_alert(
    payload: Dict[str, Any] = Body(default_factory=dict),
) -> Dict[str, Any]:
    alert = STORE.create_opsgenie_alert(payload)
    return {
        "status": "created",
        "alert": alert,
        "summary": STORE.get_executive_summary()["opsgenie_summary"],
    }


@app.post("/api/opsgenie/alerts/{alert_id}/{action}")
@app.post("/api/genie/alerts/{alert_id}/{action}")
def api_opsgenie_alert_action(alert_id: str, action: str) -> Dict[str, Any]:
    alert = STORE.update_opsgenie_alert_status(alert_id, action)
    if not alert:
        raise HTTPException(
            status_code=404, detail=f"Opsgenie alert '{alert_id}' not found"
        )
    return {
        "status": "updated",
        "action": action,
        "alert": alert,
        "summary": STORE.get_executive_summary()["opsgenie_summary"],
    }


@app.get("/api/opsgenie/schedules")
@app.get("/api/genie/schedules")
def api_opsgenie_schedules() -> Dict[str, Any]:
    return {
        "total": len(STORE.opsgenie_schedules),
        "schedules": STORE.opsgenie_schedules,
    }


@app.get("/api/opsgenie/teams")
@app.get("/api/genie/teams")
def api_opsgenie_teams() -> Dict[str, Any]:
    return {
        "total": len(STORE.opsgenie_teams),
        "teams": STORE.opsgenie_teams,
    }


@app.get("/api/opsgenie/heartbeats")
@app.get("/api/genie/heartbeats")
def api_opsgenie_heartbeats() -> Dict[str, Any]:
    return {
        "total": len(STORE.opsgenie_heartbeats),
        "heartbeats": STORE.opsgenie_heartbeats,
    }


@app.post("/api/opsgenie/heartbeats/{name}/ping")
@app.post("/api/genie/heartbeats/{name}/ping")
def api_opsgenie_ping_heartbeat(name: str) -> Dict[str, Any]:
    hb = STORE.ping_opsgenie_heartbeat(name)
    return {
        "status": "pinged",
        "heartbeat": hb,
    }


@app.post("/api/opsgenie/sync")
@app.post("/api/genie/sync")
def api_opsgenie_sync() -> Dict[str, Any]:
    STORE.connectors["opsgenie"]["last_sync"] = _now_iso()
    STORE.connectors["opsgenie"]["records_synced"] += 15
    return {
        "status": "synced",
        "connector": STORE.connectors["opsgenie"],
        "summary": STORE.get_executive_summary()["opsgenie_summary"],
    }


# ----------------------------------------------------------------------
# UNIFIED INCIDENT-TO-LLM-TO-WORKDAY ATTRIBUTION ENDPOINT
# ----------------------------------------------------------------------
@app.get("/api/incidents/attribution")
def api_incidents_attribution() -> Dict[str, Any]:
    summary = STORE.get_executive_summary()
    return {
        "pagerduty_summary": summary["pagerduty_summary"],
        "opsgenie_summary": summary["opsgenie_summary"],
        "pagerduty_incidents": STORE.pagerduty_incidents,
        "opsgenie_alerts": STORE.opsgenie_alerts,
        "pagerduty_services": STORE.pagerduty_services,
        "pagerduty_schedules": STORE.pagerduty_schedules,
        "pagerduty_alert_rules": STORE.pagerduty_alert_rules,
        "opsgenie_teams": STORE.opsgenie_teams,
        "opsgenie_schedules": STORE.opsgenie_schedules,
        "opsgenie_heartbeats": STORE.opsgenie_heartbeats,
    }


# ----------------------------------------------------------------------
# SAGE INTACCT / X3 & ORACLE NETSUITE ONEWORLD ERP ENDPOINTS
# ----------------------------------------------------------------------
@app.get("/api/erp/sage")
def get_sage_erp() -> Dict[str, Any]:
    return erp_store.state["sage_erp"]


@app.post("/api/erp/sage/gl-batch")
def create_sage_gl_batch(payload: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    batch = erp_store.create_sage_gl_batch(payload or {})
    return {
        "status": "POSTED",
        "batch": batch,
        "sage_erp": erp_store.state["sage_erp"],
    }


@app.get("/api/erp/netsuite")
def get_oracle_netsuite() -> Dict[str, Any]:
    return erp_store.state["oracle_netsuite"]


@app.post("/api/erp/netsuite/journal-entry")
def create_netsuite_je(payload: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    je = erp_store.create_netsuite_journal_entry(payload or {})
    return {
        "status": "POSTED",
        "journal_entry": je,
        "oracle_netsuite": erp_store.state["oracle_netsuite"],
    }


@app.post("/api/erp/netsuite/suiteql")
def run_netsuite_suiteql(payload: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    query = (payload or {}).get(
        "query",
        "SELECT tran_id, trandate, subsidiary, debit_account, credit_account, amount_usd, cseg_ai_provider, cseg_task_value_tier FROM transaction WHERE type = 'Journal'",
    )
    return erp_store.execute_suiteql(query)


@app.get("/api/audit/low-value")
def get_low_value_audit() -> Dict[str, Any]:
    return {
        "smart_routing_enabled": erp_store.state["meta"]["smart_routing_enabled"],
        "items": erp_store.state["low_value_tasks"],
    }


@app.post("/api/audit/optimize-routing")
def optimize_low_value_routing() -> Dict[str, Any]:
    return erp_store.apply_smart_routing_and_erp_reallocation()


@app.get("/api/export/{target}")
def export_csv_endpoint(target: str) -> PlainTextResponse:
    csv_data = erp_store.export_csv(target)
    filename = f"burniq_{target.lower()}_export.csv"
    return PlainTextResponse(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/api/import/csv")
def import_csv_endpoint(payload: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    csv_text = (payload or {}).get("csv_text", "")
    target = (payload or {}).get("target", "sage")
    if not csv_text.strip():
        return {"status": "ERROR", "message": "Empty CSV payload"}
    return erp_store.import_csv_rows(csv_text, target=target)


@app.post("/api/reset")
def reset_demo_state() -> Dict[str, Any]:
    erp_store.reset()
    STORE.__init__()
    return erp_store.get_dashboard_summary()


# ----------------------------------------------------------------------
# WORKDAY, CI/CD, LOW-VALUE TASKS, ERP/CRM, OBSERVABILITY & CSV ENDPOINTS
# ----------------------------------------------------------------------
@app.get("/api/employees")
def api_employees() -> Dict[str, Any]:
    return {"total": len(STORE.employees), "employees": STORE.employees}


@app.get("/api/releases")
def api_releases() -> Dict[str, Any]:
    return {
        "total": len(STORE.commits_and_releases),
        "releases": STORE.commits_and_releases,
    }


@app.get("/api/low-value-tasks")
def api_low_value_tasks() -> Dict[str, Any]:
    return {
        "total": len(STORE.low_value_tasks),
        "tasks": STORE.low_value_tasks,
    }


@app.get("/api/erp-crm")
def api_erp_crm() -> Dict[str, Any]:
    return {
        "total": len(STORE.erp_crm_records),
        "records": STORE.erp_crm_records,
    }


@app.get("/api/observability")
def api_observability() -> Dict[str, Any]:
    return {
        "total": len(STORE.observability_events),
        "events": STORE.observability_events,
    }


@app.post("/api/csv/import")
def api_csv_import(payload: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    filename = payload.get("filename", "uploaded_telemetry.csv")
    csv_text = payload.get(
        "csv_text",
        "incident_id,alert_id,llm_provider,tokens,roi_usd\nPD-INC-9050,OG-ALT-7710,Claude,84000,1420.00",
    )
    return STORE.import_csv_content(filename, csv_text)


@app.get("/api/csv/export")
def api_csv_export() -> Response:
    csv_content = STORE.export_incidents_and_roi_csv()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="burniq_pagerduty_opsgenie_roi.csv"'
        },
    )


# ----------------------------------------------------------------------
# FRONTEND UI SERVING
# ----------------------------------------------------------------------
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
def serve_index() -> Response:
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return HTMLResponse("<h1>BurnIQ Enterprise Telemetry & ROI Platform</h1>")
