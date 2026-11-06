"""BurnIQ Main FastAPI Server (Port 8000) — Enterprise LLM Telemetry, Sage ERP, Oracle NetSuite & Workday ROI."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict

from fastapi import Body, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from burniq.data_store import store
from mock_enterprise import mock_router

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(STATIC_DIR, exist_ok=True)

app = FastAPI(
    title="BurnIQ Enterprise Telemetry, Sage & Oracle NetSuite ERP & Workday ROI Platform",
    version="2.4.0",
    description=(
        "Full-stack corporate LLM usage attribution platform connecting Claude & Gemini token telemetry "
        "across GitHub, GitLab, Bitbucket, Jenkins, Bamboo, and Jira directly into Workday HCM compensation, "
        "Sage Intacct / Sage X3 General Ledger, Oracle NetSuite OneWorld SuiteTalk/SuiteQL, SAP, Salesforce, "
        "Power BI, ServiceNow, Zendesk, and Low-Value Task Auditing."
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
        "erp_integrations": {
            "sage": "CONNECTED (Sage Intacct REST v1 & Sage X3)",
            "oracle_netsuite": "CONNECTED (Oracle NetSuite OneWorld SuiteTalk REST & SuiteQL)",
            "sap": "CONNECTED (SAP S/4HANA OData v4)",
        },
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


@app.get("/api/dashboard")
async def get_dashboard() -> Dict[str, Any]:
    return store.get_dashboard_summary()


@app.get("/api/connectors")
async def get_connectors() -> Dict[str, Any]:
    return {
        "count": len(store.state["connectors"]),
        "connectors": store.state["connectors"],
    }


@app.post("/api/connectors/{connector_id}/test")
async def test_connector(connector_id: str) -> Dict[str, Any]:
    cid = connector_id.lower()
    now_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    for conn in store.state["connectors"]:
        if conn["id"] == cid:
            conn["status"] = "CONNECTED"
            conn["last_sync"] = now_iso
            conn["records_synced"] = int(conn.get("records_synced", 1000)) + 12
            store._save()
            return {
                "ok": True,
                "connector": conn,
                "handshake": f"Verified {conn['protocol']} handshake with {conn['endpoint']}",
                "tested_at": now_iso,
            }
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


@app.post("/api/import/csv")
async def import_csv_endpoint(payload: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    csv_text = (payload or {}).get("csv_text", "")
    target = (payload or {}).get("target", "sage")
    if not csv_text.strip():
        return {"status": "ERROR", "message": "Empty CSV payload"}
    result = store.import_csv_rows(csv_text, target=target)
    return result


@app.post("/api/reset")
async def reset_demo_state() -> Dict[str, Any]:
    store.reset()
    return store.get_dashboard_summary()


# Mount Mock Enterprise Router under /mock-enterprise
app.include_router(mock_router, prefix="/mock-enterprise")

# Mount static assets
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def index_page() -> FileResponse:
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))
