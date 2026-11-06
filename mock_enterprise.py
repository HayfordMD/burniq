"""Mock Enterprise Gateway for BurnIQ (serves both standalone port 8090 and /mock-enterprise on port 8000)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from burniq.data_store import store

mock_router = APIRouter()


def _timestamp() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


@mock_router.get("/api.intacct.com/ia/api/v1/connection")
@mock_router.get("/company.sage.com/api/v1/connection")
async def sage_intacct_connection() -> Dict[str, Any]:
    sage = store.state["sage_erp"]
    return {
        "ok": True,
        "provider": "Sage Intacct & Sage X3 Enterprise",
        "protocol": "Sage Intacct REST API v1 & XML Gateway",
        "company_id": sage["company_id"],
        "status": "CONNECTED",
        "entities_active": [e["entity_id"] for e in sage["entities"]],
        "gl_accounts_count": len(sage["gl_accounts"]),
        "gl_batches_count": len(sage["gl_batches"]),
        "vendor_bills_count": len(sage["vendor_bills"]),
        "asc_350_40_capex_enabled": True,
        "timestamp": _timestamp(),
    }


@mock_router.get("/company.suitetalk.api.netsuite.com/services/rest/record/v1/connection")
@mock_router.get("/company.netsuite.com/api/v1/connection")
async def oracle_netsuite_connection() -> Dict[str, Any]:
    ns = store.state["oracle_netsuite"]
    return {
        "ok": True,
        "provider": "Oracle NetSuite OneWorld Enterprise",
        "protocol": "SuiteTalk REST Web Services v1 + SuiteQL Analytics",
        "account_id": ns["account_id"],
        "status": "CONNECTED",
        "subsidiaries_active": [s["internal_id"] for s in ns["subsidiaries"]],
        "journal_entries_count": len(ns["journal_entries"]),
        "purchase_orders_count": len(ns["purchase_orders"]),
        "amortization_schedules_count": len(ns["amortization_schedules"]),
        "oauth2_m2m_token_valid": True,
        "timestamp": _timestamp(),
    }


@mock_router.get("/company.workday.com/api/connection")
@mock_router.get("/company.workday.com/api/commection")
async def workday_connection() -> Dict[str, Any]:
    return {
        "ok": True,
        "provider": "Workday HCM & Payroll",
        "protocol": "Workday REST v41",
        "status": "CONNECTED",
        "employees_synced": len(store.state["employees"]),
        "compensation_attribution": "ACTIVE",
        "timestamp": _timestamp(),
    }


@mock_router.get("/api.powerbi.com/v1.0/myorg/connection")
async def powerbi_connection() -> Dict[str, Any]:
    return {
        "ok": True,
        "provider": "Microsoft Power BI & Fabric",
        "workspace": "BurnIQ Executive CFO/CTO Telemetry",
        "status": "CONNECTED",
        "datasets_pushed": ["AI_ROI_Semantic_Model", "Sage_NetSuite_GL_Consolidated"],
        "timestamp": _timestamp(),
    }


@mock_router.get("/company.zendesk.com/api/v2/connection")
async def zendesk_connection() -> Dict[str, Any]:
    return {
        "ok": True,
        "provider": "Zendesk Enterprise Support",
        "status": "CONNECTED",
        "tickets_analyzed": 15300,
        "ai_deflection_rate_pct": 64.2,
        "timestamp": _timestamp(),
    }


@mock_router.get("/company.service-now.com/api/now/connection")
async def servicenow_connection() -> Dict[str, Any]:
    return {
        "ok": True,
        "provider": "ServiceNow ITSM & Change Management",
        "status": "CONNECTED",
        "change_requests_linked": 4,
        "cmdb_sync": "ACTIVE",
        "timestamp": _timestamp(),
    }


@mock_router.get("/company.sap.com/sap/opu/odata/sap/connection")
async def sap_connection() -> Dict[str, Any]:
    return {
        "ok": True,
        "provider": "SAP S/4HANA Cloud",
        "protocol": "OData v4",
        "status": "CONNECTED",
        "controlling_area": "BIQ0",
        "wbs_elements_synced": 18,
        "timestamp": _timestamp(),
    }


@mock_router.get("/company.my.salesforce.com/services/data/v60.0/connection")
async def salesforce_connection() -> Dict[str, Any]:
    return {
        "ok": True,
        "provider": "Salesforce Revenue Cloud",
        "status": "CONNECTED",
        "arr_attributed_usd": 4280000.0,
        "timestamp": _timestamp(),
    }


@mock_router.api_route("/{host}/{rest_of_path:path}", methods=["GET", "POST", "PUT"])
async def universal_enterprise_mock(
    host: str, rest_of_path: str, request: Request
) -> Dict[str, Any]:
    is_on = True
    try:
        from backend.database import get_connection
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT enabled FROM service_connections WHERE endpoint_url LIKE ?", (f"%{host}%",))
        row = cur.fetchone()
        conn.close()
        if row is not None:
            is_on = bool(row["enabled"])
    except Exception:
        pass

    for c in store.state.get("connectors", []):
        if host in c.get("endpoint", "") or host in c.get("mock_path", ""):
            if "enabled" in c:
                is_on = bool(c["enabled"])

    return {
        "ok": True,
        "host": host,
        "path": f"/{rest_of_path}",
        "method": request.method,
        "circuit_state": "ON" if is_on else "OFF",
        "status": "CONNECTED" if is_on else "PAUSED",
        "gateway": "BurnIQ Enterprise Mock Gateway",
        "timestamp": _timestamp(),
    }


app = FastAPI(
    title="BurnIQ Enterprise Mock Gateway",
    version="2.4.0",
    description="Simulates Sage Intacct, Sage X3, Oracle NetSuite OneWorld, Workday, SAP, Salesforce, Power BI, ServiceNow, Zendesk, Jira, and CI/CD endpoints.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
@app.get("/api/health")
async def gateway_health() -> Dict[str, Any]:
    return {"status": "ok", "service": "burniq-mock-enterprise-gateway", "port": 8090}


app.include_router(mock_router)
