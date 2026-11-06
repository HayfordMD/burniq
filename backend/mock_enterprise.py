"""
BurnIQ Mock Enterprise Gateway Router.
Simulates live enterprise REST endpoints for all 16 connectors (Google Flash 3-8 Fast Lite,
Vertex Gemini Pro, Anthropic Claude, Azure AI Foundry, GitHub, GitLab, Bitbucket, Jenkins,
Bamboo, Jira, ServiceNow, Zendesk, Workday HRM, Salesforce, SAP S/4HANA, Power BI & Workspace Audit).
Respects each connector's ON/OFF circuit state in real time.
"""

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter

from .database import get_connection

mock_router = APIRouter()


@mock_router.get("/mock-enterprise/{full_path:path}")
@mock_router.post("/mock-enterprise/{full_path:path}")
def handle_mock_enterprise_endpoint(full_path: str) -> Dict[str, Any]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM service_connections WHERE endpoint_url LIKE ?",
        (f"%{full_path.split('/')[0]}%",),
    )
    row = cur.fetchone()
    conn.close()

    now_iso = datetime.utcnow().isoformat() + "Z"

    if row:
        c = dict(row)
        is_on = bool(c["enabled"])
        return {
            "gateway": "BurnIQ Enterprise mTLS Proxy v2.4",
            "connection_id": c["id"],
            "service_name": c["name"],
            "vendor": c["vendor"],
            "endpoint_path": f"/mock-enterprise/{full_path}",
            "circuit_state": "ON" if is_on else "OFF",
            "status": "OK" if is_on else "CIRCUIT_PAUSED_BY_USER",
            "http_code": 200 if is_on else 503,
            "auth_verified": True,
            "auth_mode": c["auth_mode"],
            "rag_indexing_enabled": bool(c["rag_enabled"]),
            "latency_ms": c["latency_ms"] if is_on else 0,
            "events_per_hour": c["events_per_hour"] if is_on else 0,
            "timestamp": now_iso,
            "sample_payload": {
                "schema_version": "2026.11",
                "active_stream": is_on,
                "docs_indexed": c["docs_indexed"],
                "monthly_value_usd": c["monthly_value_usd"],
            },
        }

    return {
        "gateway": "BurnIQ Enterprise mTLS Proxy v2.4",
        "endpoint_path": f"/mock-enterprise/{full_path}",
        "circuit_state": "ON",
        "status": "OK",
        "http_code": 200,
        "auth_verified": True,
        "timestamp": now_iso,
    }
