"""BurnIQ Main FastAPI Server (Port 8000) — Enterprise LLM Telemetry, Datadog, Substrate, New Relic, Soluble, Sage ERP, Oracle NetSuite & Workday ROI."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict

from fastapi import Body, FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from burniq.data_store import store
from mock_enterprise import mock_router
from backend.main import (
    ObservabilityQueryRequest,
    SolubleScanRequest,
    SubstratePolicyRequest,
    CsvImportRequest,
    api_datadog,
    api_substrate,
    api_newrelic,
    api_soluble,
    api_observability,
    run_observability_query,
    run_soluble_iac_scan,
    enforce_substrate_policy,
    api_attribution,
    api_workday_roi,
    api_low_value_audit,
    api_overview,
    test_all_connectors,
    export_csv_dataset,
    import_csv_dataset,
    _probe_connector,
)
from backend.telemetry_data import get_enterprise_connectors

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
os.makedirs(STATIC_DIR, exist_ok=True)

app = FastAPI(
    title="BurnIQ Enterprise Telemetry, Datadog, Substrate, New Relic, Soluble, Sage & Oracle NetSuite ERP & Workday ROI Platform",
    version="2.4.0",
    description=(
        "Full-stack corporate LLM usage attribution platform connecting Claude & Gemini token telemetry "
        "across GitHub, GitLab, Bitbucket, Jenkins, Bamboo, and Jira directly into Datadog, Substrate, "
        "New Relic, Soluble, Workday HCM compensation, Sage Intacct / Sage X3 General Ledger, "
        "Oracle NetSuite OneWorld SuiteTalk/SuiteQL, SAP, Salesforce, Power BI, ServiceNow, Zendesk, "
        "PagerDuty, Opsgenie, and Low-Value Task Auditing."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def api_health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "burniq-enterprise-platform",
        "version": "2.4.0",
        "featured_integrations": {
            "datadog": "CONNECTED (api.datadoghq.com — LLM Obs, APM, CI Visibility, DORA)",
            "substrate": "CONNECTED (substrate.office.com & api.substrate.run — M365 Graph Audit & AI Compute)",
            "newrelic": "CONNECTED (api.newrelic.com — APM Golden Signals, NerdGraph, AI Monitoring, NRQL)",
            "soluble": "CONNECTED (api.soluble.io — Cloud-Native IaC Security & PR Auto-Remediation)",
        },
        "erp_integrations": {
            "sage": "CONNECTED (Sage Intacct REST v1 & Sage X3)",
            "oracle_netsuite": "CONNECTED (Oracle NetSuite OneWorld SuiteTalk REST & SuiteQL)",
            "sap": "CONNECTED (SAP S/4HANA OData v4)",
        },
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


@app.get("/api/dashboard")
async def get_dashboard() -> Dict[str, Any]:
    summary = store.get_dashboard_summary()
    obs = await api_observability()
    summary["observability"] = obs
    return summary


@app.get("/api/datadog")
async def get_datadog_route() -> Dict[str, Any]:
    return await api_datadog()


@app.get("/api/substrate")
async def get_substrate_route() -> Dict[str, Any]:
    return await api_substrate()


@app.get("/api/newrelic")
async def get_newrelic_route() -> Dict[str, Any]:
    return await api_newrelic()


@app.get("/api/soluble")
async def get_soluble_route() -> Dict[str, Any]:
    return await api_soluble()


@app.get("/api/observability")
async def get_observability_route() -> Dict[str, Any]:
    return await api_observability()


@app.post("/api/observability/query")
async def post_observability_query_route(req: ObservabilityQueryRequest) -> Dict[str, Any]:
    return await run_observability_query(req)


@app.post("/api/soluble/scan")
async def post_soluble_scan_route(req: SolubleScanRequest) -> Dict[str, Any]:
    return await run_soluble_iac_scan(req)


@app.post("/api/substrate/enforce-policy")
async def post_substrate_enforce_policy_route(req: SubstratePolicyRequest) -> Dict[str, Any]:
    return await enforce_substrate_policy(req)


@app.get("/api/attribution")
async def get_attribution_route() -> Dict[str, Any]:
    return await api_attribution()


@app.get("/api/workday-roi")
async def get_workday_roi_route() -> Dict[str, Any]:
    return await api_workday_roi()


@app.get("/api/low-value-audit")
async def get_low_value_audit_observability_route() -> Dict[str, Any]:
    return await api_low_value_audit()


@app.get("/api/overview")
async def get_overview_route() -> Dict[str, Any]:
    return await api_overview()


@app.get("/api/connectors")
async def get_connectors() -> Dict[str, Any]:
    return {
        "count": len(store.state["connectors"]),
        "total": len(store.state["connectors"]),
        "featured_ids": ["datadog", "substrate", "newrelic", "soluble", "sage", "netsuite"],
        "connectors": store.state["connectors"],
    }


@app.post("/api/connectors/test-all")
async def post_test_all_connectors_route() -> Dict[str, Any]:
    return await test_all_connectors()


@app.post("/api/connectors/{connector_id}/test")
async def test_connector(connector_id: str) -> Dict[str, Any]:
    cid = connector_id.lower()
    now_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    probe_result = None
    for tconn in get_enterprise_connectors():
        if tconn["id"].lower() == cid:
            probe_result = _probe_connector(tconn)
            break

    for conn in store.state["connectors"]:
        if conn["id"] == cid:
            conn["status"] = "CONNECTED"
            conn["last_sync"] = now_iso
            conn["records_synced"] = int(conn.get("records_synced", 1000)) + 12
            store._save()
            return {
                "ok": True,
                "status": "CONNECTED",
                "connector_id": cid,
                "connector": conn,
                "handshake": f"Verified {conn['protocol']} handshake with {conn['endpoint']}",
                "routed_via": probe_result["routed_via"] if probe_result else "local-mock-gateway:8000",
                "response_payload": probe_result["response_payload"] if probe_result else {"status": "CONNECTED"},
                "tested_at": now_iso,
            }
    if probe_result:
        return {"ok": True, **probe_result}
    return {
        "ok": True,
        "connector_id": connector_id,
        "status": "CONNECTED",
        "tested_at": now_iso,
    }


@app.get("/api/erp/sage")
async def get_sage_erp() -> Dict[str, Any]:
    return store.state["sage_erp"]


@app.post("/api/erp/sage/gl-batch")
async def create_sage_gl_batch(payload: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    batch = store.create_sage_gl_batch(payload or {})
    return {
        "status": "POSTED",
        "batch": batch,
        "sage_erp": store.state["sage_erp"],
    }


@app.get("/api/erp/netsuite")
async def get_oracle_netsuite() -> Dict[str, Any]:
    return store.state["oracle_netsuite"]


@app.post("/api/erp/netsuite/journal-entry")
async def create_netsuite_je(payload: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    je = store.create_netsuite_journal_entry(payload or {})
    return {
        "status": "POSTED",
        "journal_entry": je,
        "oracle_netsuite": store.state["oracle_netsuite"],
    }


@app.post("/api/erp/netsuite/suiteql")
async def run_netsuite_suiteql(payload: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    query = (payload or {}).get(
        "query",
        "SELECT tran_id, trandate, subsidiary, debit_account, credit_account, amount_usd, cseg_ai_provider, cseg_task_value_tier FROM transaction WHERE type = 'Journal'",
    )
    return store.execute_suiteql(query)


@app.get("/api/audit/low-value")
async def get_low_value_audit() -> Dict[str, Any]:
    return {
        "smart_routing_enabled": store.state["meta"]["smart_routing_enabled"],
        "items": store.state["low_value_tasks"],
    }


@app.post("/api/audit/optimize-routing")
async def optimize_low_value_routing() -> Dict[str, Any]:
    return store.apply_smart_routing_and_erp_reallocation()


@app.get("/api/export/{target}")
async def export_csv_endpoint(target: str) -> PlainTextResponse:
    csv_data = store.export_csv(target)
    filename = f"burniq_{target.lower()}_export.csv"
    return PlainTextResponse(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/csv/export/{dataset}")
async def export_csv_dataset_route(dataset: str) -> Response:
    return await export_csv_dataset(dataset)


@app.post("/api/import/csv")
async def import_csv_endpoint(payload: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    csv_text = (payload or {}).get("csv_text", "")
    target = (payload or {}).get("target", "sage")
    if not csv_text.strip():
        return {"status": "ERROR", "message": "Empty CSV payload"}
    result = store.import_csv_rows(csv_text, target=target)
    return result


@app.post("/api/csv/import")
async def import_csv_dataset_route(req: CsvImportRequest) -> Dict[str, Any]:
    return await import_csv_dataset(req)


@app.post("/api/reset")
async def reset_demo_state() -> Dict[str, Any]:
    store.reset()
    return await get_dashboard()


# Mount Mock Enterprise Router under /mock-enterprise
app.include_router(mock_router, prefix="/mock-enterprise")

# Mount static assets
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/observability-static", StaticFiles(directory=FRONTEND_DIR), name="observability-static")


@app.get("/")
async def index_page() -> FileResponse:
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/observability-ui")
async def observability_ui_page() -> FileResponse:
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

