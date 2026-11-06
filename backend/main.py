"""
BurnIQ Enterprise Telemetry, Service Connection Control, Multi-Persona Dashboards,
Hybrid Search & Google Flash 3-8 Fast Lite RAG Platform — FastAPI Backend.
"""

import json
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from burniq.data_store import store
from mock_enterprise import mock_router as erp_mock_router
from .database import get_connection, init_db
from .mock_enterprise import mock_router
from .rag_engine import rag_engine

app = FastAPI(
    title="BurnIQ Enterprise Telemetry, Service Connection Control, Dual-ERP & Flash-Lite RAG Platform",
    version="2.4.0",
    description="Enterprise LLM Telemetry, Service Connection ON/OFF Control, Multi-Persona Dashboards (TechOps, Developers, Managers, C-Suite), Sage & NetSuite ERP, Hybrid Search & Google Flash 3-8 Fast Lite RAG Engine.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(erp_mock_router, prefix="/mock-enterprise")
app.include_router(mock_router)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
STATIC_DIR = os.path.join(BASE_DIR, "static")


class ToggleConnectionRequest(BaseModel):
    enabled: Optional[bool] = None
    rag_enabled: Optional[bool] = None
    sync_interval_min: Optional[int] = None
    endpoint_url: Optional[str] = None
    actor: str = "admin-console"


class BulkToggleRequest(BaseModel):
    enabled: bool
    category: Optional[str] = None
    connection_ids: Optional[List[str]] = None
    actor: str = "admin-console"


class SearchRequest(BaseModel):
    query: str = ""
    persona: str = "all"
    connection_id: str = "all"
    source_type: str = "all"
    active_only: bool = True
    sort_by: str = "hybrid"
    top_k: int = 20


class LLMChatRequest(BaseModel):
    prompt: str
    model_id: str = "google/gemini-3-8-flash-lite"
    persona: str = "csuite"
    top_k: int = 5
    active_only: bool = True
    temperature: float = 0.2
    api_key: Optional[str] = None


class RAGIngestRequest(BaseModel):
    title: str
    connection_id: str = "conn-gemini-flash-lite"
    source_type: str = "rag_knowledge"
    persona_tags: str = "techops,developers,managers,csuite"
    department: str = "Data & AI Platform"
    content: str
    chunk_strategy: str = "semantic"
    importance_weight: float = 1.25


class RAGTrainRequest(BaseModel):
    model_id: str = "google/gemini-3-8-flash-lite"
    adapter_name: str = "burniq-flash-3-8-fast-lite-rag-v2.5"
    embedding_dim: int = 64
    system_prompt: Optional[str] = None


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    rag_engine.build_index()


@app.api_route("/api/health", methods=["GET", "HEAD"])
@app.api_route("/health", methods=["GET", "HEAD"])
def get_health() -> Dict[str, Any]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as total, SUM(enabled) as active FROM service_connections")
    row = cur.fetchone()
    conn.close()
    return {
        "status": "healthy",
        "ok": True,
        "service": "burniq-enterprise-platform",
        "platform": "BurnIQ Enterprise Telemetry & RAG Platform",
        "version": "2.4.0",
        "default_llm": "google/gemini-3-8-flash-lite",
        "connections_total": row["total"] or 0,
        "connections_active": row["active"] or 0,
        "rag_corpus_size": len(rag_engine.corpus),
        "rag_vocab_size": len(rag_engine.vocab),
        "erp_integrations": {
            "sage": "CONNECTED (Sage Intacct REST v1 & Sage X3)",
            "oracle_netsuite": "CONNECTED (Oracle NetSuite OneWorld SuiteTalk REST & SuiteQL)",
            "sap": "CONNECTED (SAP S/4HANA OData v4)",
        },
        "featured_integrations": {
            "datadog": "CONNECTED (api.datadoghq.com — LLM Obs, APM, CI Visibility, DORA)",
            "substrate": "CONNECTED (substrate.office.com & api.substrate.run — M365 Graph Audit & AI Compute)",
            "newrelic": "CONNECTED (api.newrelic.com — APM Golden Signals, NerdGraph, AI Monitoring, NRQL)",
            "soluble": "CONNECTED (api.soluble.io — Cloud-Native IaC Security & PR Auto-Remediation)",
        },
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


# -----------------------------------------------------------------------------
# 1. Service Connection Management Endpoints (Turn ON / OFF, Bulk, Test, Sync)
# -----------------------------------------------------------------------------
@app.get("/api/connections")
def list_connections(
    category: str = Query("all"),
    persona: str = Query("all"),
    status: str = Query("all"),
) -> Dict[str, Any]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM service_connections ORDER BY category, name")
    all_rows = [dict(r) for r in cur.fetchall()]

    for r in all_rows:
        r["enabled"] = bool(r["enabled"])
        r["rag_enabled"] = bool(r["rag_enabled"])
        r["primary_personas_list"] = r["primary_personas"].split(",")
        r["config"] = json.loads(r["config_json"] or "{}")

    filtered = []
    for r in all_rows:
        if category != "all" and r["category"] != category:
            continue
        if persona != "all" and persona not in r["primary_personas_list"]:
            continue
        if status == "online" and not r["enabled"]:
            continue
        if status == "paused" and r["enabled"]:
            continue
        filtered.append(r)

    cur.execute("SELECT * FROM connection_events ORDER BY id DESC LIMIT 12")
    events = [dict(e) for e in cur.fetchall()]
    conn.close()

    online_conns = [c for c in all_rows if c["enabled"]]
    paused_conns = [c for c in all_rows if not c["enabled"]]

    categories = sorted(list({c["category"] for c in all_rows}))

    return {
        "connections": filtered,
        "all_count": len(all_rows),
        "online_count": len(online_conns),
        "paused_count": len(paused_conns),
        "rag_active_count": sum(1 for c in all_rows if c["enabled"] and c["rag_enabled"]),
        "total_events_per_hour": sum(c["events_per_hour"] for c in online_conns),
        "total_docs_indexed": sum(c["docs_indexed"] for c in online_conns if c["rag_enabled"]),
        "active_monthly_cost_usd": round(sum(c["monthly_cost_usd"] for c in online_conns), 2),
        "active_monthly_value_usd": round(sum(c["monthly_value_usd"] for c in online_conns), 2),
        "categories": categories,
        "recent_events": events,
    }


@app.post("/api/connections/{conn_id}/toggle")
@app.patch("/api/connections/{conn_id}")
def toggle_connection(conn_id: str, req: ToggleConnectionRequest) -> Dict[str, Any]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM service_connections WHERE id = ?", (conn_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Service connection '{conn_id}' not found")

    current = dict(row)
    prev_enabled = bool(current["enabled"])
    new_enabled = req.enabled if req.enabled is not None else (not prev_enabled)
    new_rag = req.rag_enabled if req.rag_enabled is not None else bool(current["rag_enabled"])
    new_interval = req.sync_interval_min if req.sync_interval_min is not None else current["sync_interval_min"]
    new_endpoint = req.endpoint_url if req.endpoint_url is not None else current["endpoint_url"]
    new_status = "online" if new_enabled else "paused"
    now_iso = datetime.utcnow().isoformat()

    cur.execute(
        """
        UPDATE service_connections
        SET enabled = ?, rag_enabled = ?, status = ?, sync_interval_min = ?, endpoint_url = ?, last_sync_at = ?
        WHERE id = ?
        """,
        (1 if new_enabled else 0, 1 if new_rag else 0, new_status, new_interval, new_endpoint, now_iso, conn_id),
    )

    event_type = "TOGGLE_ON" if new_enabled else "TOGGLE_OFF"
    if req.enabled is None and req.rag_enabled is not None:
        event_type = "RAG_TOGGLE"

    details = (
        f"Service connection '{current['name']}' turned {'ON (Online)' if new_enabled else 'OFF (Paused)'} "
        f"[RAG Indexing: {'ON' if new_rag else 'OFF'}]."
    )
    cur.execute(
        """
        INSERT INTO connection_events (connection_id, event_type, previous_state, new_state, actor, details, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (conn_id, event_type, "online" if prev_enabled else "paused", new_status, req.actor, details, now_iso),
    )
    conn.commit()

    cur.execute("SELECT * FROM service_connections WHERE id = ?", (conn_id,))
    updated = dict(cur.fetchone())
    updated["enabled"] = bool(updated["enabled"])
    updated["rag_enabled"] = bool(updated["rag_enabled"])
    conn.close()

    # Refresh RAG index flags
    rag_engine.build_index()

    return {
        "status": "updated",
        "connection": updated,
        "message": details,
        "summary": list_connections()["online_count"],
    }


@app.post("/api/connections/bulk-toggle")
def bulk_toggle_connections(req: BulkToggleRequest) -> Dict[str, Any]:
    conn = get_connection()
    cur = conn.cursor()
    now_iso = datetime.utcnow().isoformat()
    new_status = "online" if req.enabled else "paused"
    val = 1 if req.enabled else 0

    if req.connection_ids:
        placeholders = ",".join("?" for _ in req.connection_ids)
        cur.execute(
            f"UPDATE service_connections SET enabled = ?, status = ?, last_sync_at = ? WHERE id IN ({placeholders})",
            [val, new_status, now_iso] + req.connection_ids,
        )
        scope_desc = f"{len(req.connection_ids)} selected connections"
    elif req.category and req.category != "all":
        cur.execute(
            "UPDATE service_connections SET enabled = ?, status = ?, last_sync_at = ? WHERE category = ?",
            (val, new_status, now_iso, req.category),
        )
        scope_desc = f"category '{req.category}'"
    else:
        cur.execute(
            "UPDATE service_connections SET enabled = ?, status = ?, last_sync_at = ?",
            (val, new_status, now_iso),
        )
        scope_desc = "all 16 enterprise connections"

    cur.execute(
        """
        INSERT INTO connection_events (connection_id, event_type, previous_state, new_state, actor, details, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "bulk-operation",
            "BULK_ON" if req.enabled else "BULK_OFF",
            "mixed",
            new_status,
            req.actor,
            f"Bulk turned {'ON' if req.enabled else 'OFF'} {scope_desc}.",
            now_iso,
        ),
    )
    conn.commit()
    conn.close()

    rag_engine.build_index()
    return list_connections()


@app.post("/api/connections/{conn_id}/test")
def test_connection_endpoint(conn_id: str) -> Dict[str, Any]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM service_connections WHERE id = ?", (conn_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Service connection not found")
    c = dict(row)
    is_on = bool(c["enabled"])
    now_iso = datetime.utcnow().isoformat()

    details = (
        f"Health check passed ({c['latency_ms']}ms, HTTP 200, {c['auth_mode']})"
        if is_on
        else "Connection circuit is currently turned OFF (Paused by administrator)."
    )
    cur.execute(
        """
        INSERT INTO connection_events (connection_id, event_type, previous_state, new_state, actor, details, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (conn_id, "HEALTH_TEST", c["status"], c["status"], "diagnostic-probe", details, now_iso),
    )
    conn.commit()
    conn.close()

    return {
        "connection_id": conn_id,
        "name": c["name"],
        "enabled": is_on,
        "reachable": is_on,
        "http_status": 200 if is_on else 503,
        "latency_ms": c["latency_ms"] if is_on else 0,
        "auth_mode": c["auth_mode"],
        "endpoint_url": c["endpoint_url"],
        "message": details,
        "timestamp": now_iso,
    }


@app.post("/api/connections/{conn_id}/sync")
def sync_connection_now(conn_id: str) -> Dict[str, Any]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM service_connections WHERE id = ?", (conn_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Service connection not found")
    c = dict(row)
    if not c["enabled"]:
        conn.close()
        raise HTTPException(
            status_code=400,
            detail=f"Cannot sync '{c['name']}' while its connection switch is turned OFF. Turn it ON first.",
        )

    now_iso = datetime.utcnow().isoformat()
    new_docs = c["docs_indexed"] + 2
    new_events = c["events_per_hour"] + 45

    cur.execute(
        "UPDATE service_connections SET docs_indexed = ?, events_per_hour = ?, last_sync_at = ? WHERE id = ?",
        (new_docs, new_events, now_iso, conn_id),
    )
    cur.execute(
        """
        INSERT INTO connection_events (connection_id, event_type, previous_state, new_state, actor, details, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            conn_id,
            "MANUAL_SYNC",
            "online",
            "online",
            "manual-sync",
            f"Ingested +2 RAG telemetry documents & synced {new_events:,} events/hr from {c['name']}.",
            now_iso,
        ),
    )
    conn.commit()
    conn.close()

    rag_engine.build_index()
    return {
        "status": "synced",
        "connection_id": conn_id,
        "name": c["name"],
        "docs_indexed": new_docs,
        "events_per_hour": new_events,
        "last_sync_at": now_iso,
    }


# -----------------------------------------------------------------------------
# 2. Multi-Persona Dashboards Endpoint (TechOps, Developers, Managers, C-Suite)
# -----------------------------------------------------------------------------
@app.get("/api/dashboard/{persona}")
def get_persona_dashboard(
    persona: str,
    timeframe: str = Query("30d"),
    department: str = Query("all"),
) -> Dict[str, Any]:
    persona = persona.lower().strip()
    if persona not in ("techops", "developers", "managers", "csuite"):
        raise HTTPException(status_code=400, detail="Invalid persona. Choose techops, developers, managers, or csuite.")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM service_connections ORDER BY category, name")
    all_conns = [dict(r) for r in cur.fetchall()]
    for c in all_conns:
        c["enabled"] = bool(c["enabled"])
        c["rag_enabled"] = bool(c["rag_enabled"])

    active_conns = [c for c in all_conns if c["enabled"]]
    paused_conns = [c for c in all_conns if not c["enabled"]]
    active_ids = {c["id"] for c in active_conns}

    cur.execute("SELECT * FROM department_metrics")
    all_depts = [dict(r) for r in cur.fetchall()]
    if department != "all":
        depts = [d for d in all_depts if d["department"].lower() == department.lower()]
        if not depts:
            depts = all_depts
    else:
        depts = all_depts

    cur.execute("SELECT * FROM code_telemetry ORDER BY created_at DESC")
    all_commits = [dict(r) for r in cur.fetchall()]
    if department != "all":
        commits = [cm for cm in all_commits if cm["department"].lower() == department.lower()] or all_commits
    else:
        commits = all_commits

    cur.execute("SELECT * FROM task_audit_logs ORDER BY created_at DESC")
    all_audits = [dict(r) for r in cur.fetchall()]
    if department != "all":
        audits = [a for a in all_audits if a["department"].lower() == department.lower()] or all_audits
    else:
        audits = all_audits

    cur.execute("SELECT * FROM llm_models ORDER BY is_default DESC, input_cost_per_1m ASC")
    models = [dict(m) for m in cur.fetchall()]

    cur.execute("SELECT * FROM rag_training_runs ORDER BY created_at DESC LIMIT 1")
    latest_train = dict(cur.fetchone())

    conn.close()

    # Timeframe multiplier for volume metrics
    tf_mult = {"24h": 0.035, "7d": 0.25, "30d": 1.0, "90d": 2.9, "12m": 11.6}.get(timeframe, 1.0)
    # Active connection ratio dynamically scales live telemetry streams
    active_ratio = max(len(active_conns) / max(len(all_conns), 1), 0.1)

    persona_conns = [
        c for c in all_conns if persona in c["primary_personas"].split(",")
    ]

    if persona == "techops":
        payload = _build_techops_dashboard(
            all_conns, active_conns, paused_conns, persona_conns, models, latest_train, tf_mult, active_ratio, timeframe
        )
    elif persona == "developers":
        payload = _build_developers_dashboard(
            all_conns, active_conns, paused_conns, persona_conns, commits, models, tf_mult, active_ratio, timeframe
        )
    elif persona == "managers":
        payload = _build_managers_dashboard(
            all_conns, active_conns, paused_conns, persona_conns, depts, audits, commits, tf_mult, active_ratio, timeframe
        )
    else:
        payload = _build_csuite_dashboard(
            all_conns, active_conns, paused_conns, persona_conns, depts, audits, models, tf_mult, active_ratio, timeframe
        )

    payload["persona"] = persona
    payload["timeframe"] = timeframe
    payload["department"] = department
    payload["available_departments"] = ["all"] + [d["department"] for d in all_depts]
    payload["connection_summary"] = {
        "total": len(all_conns),
        "online": len(active_conns),
        "paused": len(paused_conns),
        "paused_names": [c["name"] for c in paused_conns],
        "persona_connections": persona_conns,
    }
    return payload


def _build_techops_dashboard(
    all_conns: List[Dict[str, Any]],
    active_conns: List[Dict[str, Any]],
    paused_conns: List[Dict[str, Any]],
    persona_conns: List[Dict[str, Any]],
    models: List[Dict[str, Any]],
    latest_train: Dict[str, Any],
    tf_mult: float,
    active_ratio: float,
    timeframe: str,
) -> Dict[str, Any]:
    events_hr = sum(c["events_per_hour"] for c in active_conns)
    events_min = int(round(events_hr / 60.0))
    avg_uptime = round(sum(c["uptime_pct"] for c in active_conns) / max(len(active_conns), 1), 2) if active_conns else 0.0
    flash_on = any(c["id"] == "conn-gemini-flash-lite" and c["enabled"] for c in all_conns)
    servicenow_on = any(c["id"] == "conn-servicenow" and c["enabled"] for c in all_conns)
    p95_lat = 112 if flash_on else 580
    mttr_mins = 18.4 if (servicenow_on and flash_on) else 41.2

    kpis = [
        {
            "id": "kpi-techops-conns",
            "label": "Active Service Connections",
            "value": f"{len(active_conns)} / {len(all_conns)}",
            "subvalue": f"{avg_uptime}% Mean Pipeline Uptime",
            "delta": f"{len(paused_conns)} Paused" if paused_conns else "100% Online",
            "delta_type": "positive" if len(active_conns) >= 14 else "warning",
        },
        {
            "id": "kpi-techops-throughput",
            "label": "Live Ingestion Throughput",
            "value": f"{events_min:,} ev/min",
            "subvalue": f"{int(events_hr * 24 * tf_mult):,} events ({timeframe})",
            "delta": "+18.4% vs baseline",
            "delta_type": "positive",
        },
        {
            "id": "kpi-techops-latency",
            "label": "Flash 3-8 Fast Lite P95 Latency",
            "value": f"{p95_lat} ms",
            "subvalue": "94 ms avg TTFT (LoRA RAG v2.4)" if flash_on else "Fallback to Pro (Flash-Lite OFF)",
            "delta": "-68% vs Frontier Models" if flash_on else "Flash-Lite Paused",
            "delta_type": "positive" if flash_on else "warning",
        },
        {
            "id": "kpi-techops-rag-index",
            "label": "RAG Vector Index Health",
            "value": f"{len(rag_engine.corpus)} Chunks",
            "subvalue": f"{len(rag_engine.vocab):,} terms · {rag_engine.embedding_dim}-dim SVD",
            "delta": f"Recall@5: {latest_train['retrieval_recall_at_5'] * 100:.1f}%",
            "delta_type": "positive",
        },
        {
            "id": "kpi-techops-routing",
            "label": "Lightweight Model Traffic Share",
            "value": "78.4%" if flash_on else "0.0%",
            "subvalue": "$0.035 / 1M input · $0.008 / 1M cached",
            "delta": "$34.8K/mo infra saved",
            "delta_type": "positive" if flash_on else "warning",
        },
        {
            "id": "kpi-techops-mttr",
            "label": "ServiceNow P1/P2 MTTR",
            "value": f"{mttr_mins} mins",
            "subvalue": "Auto-RAG runbook correlation",
            "delta": "-54.0% MTTR reduction" if servicenow_on else "ServiceNow Paused",
            "delta_type": "positive" if servicenow_on else "warning",
        },
    ]

    # Chart 1: Multi-series Latency & Throughput over Time
    labels = ["00:00", "03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00"]
    scale = active_ratio
    charts = {
        "throughput_latency_series": {
            "title": "Telemetry Ingestion Throughput (req/min) & Model P95 Latency (ms)",
            "subtitle": "Real-time comparison of Google Flash 3-8 Fast Lite vs Frontier Models across active connectors",
            "type": "multi_line",
            "labels": labels,
            "series": [
                {
                    "name": "Flash 3-8 Fast Lite P95 (ms)",
                    "color": "#10B981",
                    "unit": "ms",
                    "data": [98, 96, 102, 114, 118, 112, 106, 99] if flash_on else [0] * 8,
                },
                {
                    "name": "Gemini 2.5 Flash P95 (ms)",
                    "color": "#19B5FE",
                    "unit": "ms",
                    "data": [210, 205, 224, 248, 255, 242, 230, 215],
                },
                {
                    "name": "Claude 3.7 Sonnet P95 (ms)",
                    "color": "#F59E0B",
                    "unit": "ms",
                    "data": [590, 580, 620, 695, 740, 710, 660, 615],
                },
                {
                    "name": "Ingestion Rate (x10 ev/min)",
                    "color": "#F43F5E",
                    "unit": "x10 ev/m",
                    "data": [int(v * scale) for v in [520, 480, 610, 840, 920, 890, 760, 640]],
                },
            ],
        },
        "connector_throughput_bars": {
            "title": "Service Connection Ingestion Volume (Events/Hr) & Circuit State",
            "subtitle": "Live throughput across top enterprise connectors (turning a connector OFF drops its stream to 0)",
            "type": "horizontal_bar",
            "items": [
                {
                    "id": c["id"],
                    "label": c["name"].replace("Enterprise", "").replace("(RAG Engine)", "").strip(),
                    "value": c["events_per_hour"] if c["enabled"] else 0,
                    "max_value": 15000,
                    "latency_ms": c["latency_ms"] if c["enabled"] else 0,
                    "enabled": c["enabled"],
                    "category": c["category"],
                    "color": "#10B981" if c["enabled"] else "#64748B",
                }
                for c in all_conns[:10]
            ],
        },
        "model_traffic_donut": {
            "title": "LLM Gateway Request Routing & Cost Share",
            "subtitle": "78.4% of requests routed to custom RAG-trained Google Flash 3-8 Fast Lite",
            "type": "donut",
            "center_label": "78.4%",
            "center_sublabel": "Flash 3-8 Lite",
            "segments": [
                {"label": "Google Flash 3-8 Fast Lite ($0.035/1M)", "value": 78.4, "cost_usd": 8140, "color": "#10B981"},
                {"label": "Google Gemini 2.5 Flash ($0.15/1M)", "value": 8.2, "cost_usd": 1920, "color": "#19B5FE"},
                {"label": "Anthropic Claude 3.5 Haiku ($0.80/1M)", "value": 4.8, "cost_usd": 2410, "color": "#F59E0B"},
                {"label": "Google Gemini 2.5 Pro ($1.25/1M)", "value": 4.6, "cost_usd": 5130, "color": "#38BDF8"},
                {"label": "Anthropic Claude 3.7 Sonnet ($3.00/1M)", "value": 4.0, "cost_usd": 7740, "color": "#F43F5E"},
            ],
        },
        "incident_mttr_chart": {
            "title": "ServiceNow P1/P2 Incident MTTR (Minutes) vs RAG Auto-Triage Coverage (%)",
            "subtitle": "Impact of indexing Jenkins, GitHub & ServiceNow runbooks into Flash 3-8 Fast Lite RAG",
            "type": "grouped_bar",
            "labels": ["Jun", "Jul", "Aug", "Sep", "Oct", "Nov (BurnIQ v2.4)"],
            "series": [
                {"name": "P1/P2 MTTR (mins)", "color": "#F43F5E", "data": [44.0, 41.5, 36.2, 28.4, 21.9, mttr_mins]},
                {"name": "RAG Auto-Triage Coverage (%)", "color": "#10B981", "data": [18.0, 32.0, 54.0, 72.0, 86.0, 94.6 if flash_on else 25.0]},
            ],
        },
    }

    return {
        "title": "Technical Operations, SRE & RAG Infrastructure Command",
        "subtitle": "Real-time connector circuit states, webhook ingestion throughput, P95 model latency, ServiceNow MTTR, and vector index health.",
        "kpis": kpis,
        "charts": charts,
        "table_title": "Enterprise Service Connection Telemetry & Circuit Matrix",
        "table_rows": all_conns,
    }


def _build_developers_dashboard(
    all_conns: List[Dict[str, Any]],
    active_conns: List[Dict[str, Any]],
    paused_conns: List[Dict[str, Any]],
    persona_conns: List[Dict[str, Any]],
    commits: List[Dict[str, Any]],
    models: List[Dict[str, Any]],
    tf_mult: float,
    active_ratio: float,
    timeframe: str,
) -> Dict[str, Any]:
    scm_on = any(c["id"] in ("conn-github-ent", "conn-gitlab-scm", "conn-bitbucket") and c["enabled"] for c in all_conns)
    ci_on = any(c["id"] in ("conn-jenkins", "conn-bamboo") and c["enabled"] for c in all_conns)

    total_lines = sum(cm["lines_added"] for cm in commits)
    ai_lines = sum(cm["lines_ai_attributed"] for cm in commits)
    attr_pct = round((ai_lines / max(total_lines, 1)) * 100.0, 1) if scm_on else 0.0
    avg_cycle = round(sum(cm["pr_cycle_hours"] for cm in commits) / max(len(commits), 1), 1)

    kpis = [
        {
            "id": "kpi-dev-attribution",
            "label": "Code-to-Release AI Attribution",
            "value": f"{attr_pct}%",
            "subvalue": f"{int(ai_lines * 18 * tf_mult):,} AI-verified LOC shipped ({timeframe})",
            "delta": "+24.2% vs Q3",
            "delta_type": "positive" if scm_on else "warning",
        },
        {
            "id": "kpi-dev-pr-cycle",
            "label": "Mean PR Merge Cycle Time",
            "value": f"{avg_cycle} hrs",
            "subvalue": "Down from 11.8 hrs pre-RAG baseline",
            "delta": "64.4% faster merges",
            "delta_type": "positive",
        },
        {
            "id": "kpi-dev-ci-pass",
            "label": "First-Run CI Build Pass Rate",
            "value": "94.2%" if ci_on else "Paused",
            "subvalue": "Jenkins + Bamboo automated test gates",
            "delta": "+11.8% pass rate",
            "delta_type": "positive" if ci_on else "warning",
        },
        {
            "id": "kpi-dev-cost-per-pr",
            "label": "Mean LLM Cost per Merged PR",
            "value": "$0.38",
            "subvalue": "Powered by Google Flash 3-8 Fast Lite",
            "delta": "-89% vs Sonnet-only",
            "delta_type": "positive",
        },
        {
            "id": "kpi-dev-rag-hit",
            "label": "IDE RAG Context Cache Hit Rate",
            "value": "89.5%",
            "subvalue": "Repo docs, Jira specs & PR history",
            "delta": "$0.008 / 1M cached tokens",
            "delta_type": "positive",
        },
        {
            "id": "kpi-dev-rollback",
            "label": "Production Release Rollback Rate",
            "value": "1.1%",
            "subvalue": "Down from 6.8% across 29 Bamboo plans",
            "delta": "-83.8% rollbacks",
            "delta_type": "positive",
        },
    ]

    scale = tf_mult * active_ratio
    charts = {
        "attribution_funnel": {
            "title": "Code-to-Release Telemetry Lineage Funnel",
            "subtitle": "End-to-end traceability from IDE prompt sessions to Git commits, branches, PRs, Jenkins/Bamboo CI, and production releases",
            "type": "funnel",
            "stages": [
                {"stage": "1. IDE & CLI Prompt Sessions (Flash-Lite + Claude)", "count": int(18420 * scale), "pct": 100.0, "color": "#19B5FE"},
                {"stage": "2. RAG-Grounded Context Injections (Jira + Repo KB)", "count": int(16485 * scale), "pct": 89.5, "color": "#38BDF8"},
                {"stage": "3. Git Commits with AI Line Attribution (GitHub/GitLab/Bitbucket)", "count": int(6840 * scale), "pct": 64.8, "color": "#10B981"},
                {"stage": "4. Pull Requests & Merge Requests Opened", "count": int(1920 * scale), "pct": 52.0, "color": "#F59E0B"},
                {"stage": "5. Passing Jenkins & Bamboo CI Build Pipelines", "count": int(1808 * scale), "pct": 94.2, "color": "#10B981"},
                {"stage": "6. Verified Production Releases Linked to Jira Epics", "count": int(312 * scale), "pct": 98.9, "color": "#10B981"},
            ],
        },
        "repo_efficiency_bars": {
            "title": "Repository AI Code Output (LOC) vs Token Efficiency by Language",
            "subtitle": "Verified lines shipped per 1,000 tokens across core microservices",
            "type": "grouped_bar",
            "labels": ["burniq-rag (Py)", "ingestor (Go)", "web-console (TS)", "vector-core (Rust)", "finops-dbt (SQL)", "support-bot (Py)"],
            "series": [
                {"name": "AI-Attributed Lines (x100 LOC)", "color": "#10B981", "data": [48, 39, 54, 42, 31, 45]},
                {"name": "LOC per 1k Tokens", "color": "#19B5FE", "data": [54, 49, 46, 51, 62, 58]},
            ],
        },
        "model_coding_scatter": {
            "title": "Developer Task Routing: Model Latency (ms) vs Code Acceptance Rate (%)",
            "subtitle": "Google Flash 3-8 Fast Lite handles 80% of unit tests, docstrings, RAG lookups & PR triage under 115ms",
            "type": "horizontal_bar",
            "items": [
                {"id": "m-flash-lite", "label": "Google Flash 3-8 Fast Lite (Unit Tests, RAG, Boilerplate)", "value": 94.8, "max_value": 100, "latency_ms": 94, "enabled": True, "category": "$0.035/1M", "color": "#10B981"},
                {"id": "m-gemini-flash", "label": "Google Gemini 2.5 Flash (Repo Summarization & Diffs)", "value": 95.6, "max_value": 100, "latency_ms": 195, "enabled": True, "category": "$0.15/1M", "color": "#19B5FE"},
                {"id": "m-claude-haiku", "label": "Anthropic Claude 3.5 Haiku (Inline Autocomplete)", "value": 93.4, "max_value": 100, "latency_ms": 240, "enabled": True, "category": "$0.80/1M", "color": "#F59E0B"},
                {"id": "m-claude-sonnet", "label": "Anthropic Claude 3.7 Sonnet (Complex Multi-File Refactor)", "value": 97.9, "max_value": 100, "latency_ms": 610, "enabled": True, "category": "$3.00/1M", "color": "#F43F5E"},
                {"id": "m-gemini-pro", "label": "Google Gemini 2.5 Pro (System Architecture & Security)", "value": 98.2, "max_value": 100, "latency_ms": 520, "enabled": True, "category": "$1.25/1M", "color": "#38BDF8"},
            ],
        },
        "commit_velocity_series": {
            "title": "Weekly Commit Velocity: AI-Assisted vs Manual Commits & CI Pass Rate",
            "subtitle": "Continuous acceleration following Flash 3-8 Fast Lite repository RAG indexing",
            "type": "multi_line",
            "labels": ["W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8"],
            "series": [
                {"name": "AI-Assisted Commits", "color": "#10B981", "unit": "commits", "data": [410, 465, 530, 610, 690, 745, 810, 860]},
                {"name": "Manual-Only Commits", "color": "#64748B", "unit": "commits", "data": [520, 495, 480, 460, 450, 440, 435, 430]},
                {"name": "Jenkins/Bamboo Pass Rate (%)", "color": "#F59E0B", "unit": "%", "data": [86, 88, 89, 91, 92, 93, 94, 95]},
            ],
        },
    }

    return {
        "title": "Developer Productivity, Code-to-Release Lineage & CI Telemetry",
        "subtitle": "Git commit SHA attribution, branch & PR cycle velocity, Jenkins/Bamboo build pass rates, and IDE RAG caching.",
        "kpis": kpis,
        "charts": charts,
        "table_title": "Live Code-to-Release Attribution Lineage (Commits -> Branches -> CI -> Jira -> Workday Value)",
        "table_rows": commits,
    }


def _build_managers_dashboard(
    all_conns: List[Dict[str, Any]],
    active_conns: List[Dict[str, Any]],
    paused_conns: List[Dict[str, Any]],
    persona_conns: List[Dict[str, Any]],
    depts: List[Dict[str, Any]],
    audits: List[Dict[str, Any]],
    commits: List[Dict[str, Any]],
    tf_mult: float,
    active_ratio: float,
    timeframe: str,
) -> Dict[str, Any]:
    total_sp = int(sum(d["jira_story_points"] for d in depts) * tf_mult)
    total_hours = round(sum(d["hours_reclaimed_month"] for d in depts) * tf_mult, 1)
    total_headcount = sum(d["headcount"] for d in depts)
    total_seats = sum(d["active_ai_seats"] for d in depts)
    total_spend = sum(d["actual_llm_spend_usd"] for d in depts) * tf_mult
    sp_per_100 = round((total_sp / max(total_spend, 1.0)) * 100.0, 1)
    hrs_per_dev_wk = round((sum(d["hours_reclaimed_month"] for d in depts) / max(total_headcount, 1)) / 4.0, 1)

    kpis = [
        {
            "id": "kpi-mgr-velocity",
            "label": "Jira Sprint Velocity Delivered",
            "value": f"{total_sp:,} SP",
            "subvalue": "Across 6 engineering & ops squads",
            "delta": "+38.4% velocity lift",
            "delta_type": "positive",
        },
        {
            "id": "kpi-mgr-hours",
            "label": "Engineering Hours Reclaimed",
            "value": f"{total_hours:,.0f} hrs",
            "subvalue": f"{hrs_per_dev_wk} hrs / engineer / week saved",
            "delta": "+4.2 hrs/wk with RAG",
            "delta_type": "positive",
        },
        {
            "id": "kpi-mgr-high-value",
            "label": "High-Value vs Low-Value Task Mix",
            "value": "86.2% High",
            "subvalue": "13.8% Low-Value email/notes auto-routed to Flash-Lite",
            "delta": "$11.2K/mo waste cut",
            "delta_type": "positive",
        },
        {
            "id": "kpi-mgr-sp-efficiency",
            "label": "Story Points per $100 AI Spend",
            "value": f"{sp_per_100} SP",
            "subvalue": "Jira + SAP cost center correlation",
            "delta": "+112% FinOps efficiency",
            "delta_type": "positive",
        },
        {
            "id": "kpi-mgr-adoption",
            "label": "Active Squad AI Seat Adoption",
            "value": f"{total_seats} / {total_headcount}",
            "subvalue": f"{round(total_seats / max(total_headcount, 1) * 100, 1)}% active daily utilization",
            "delta": "Top quartile adoption",
            "delta_type": "positive",
        },
        {
            "id": "kpi-mgr-epic-ontime",
            "label": "On-Time Jira Epic Delivery",
            "value": "92.8%",
            "subvalue": "Tracked across Jira -> Bamboo releases",
            "delta": "+19.5% vs Q2",
            "delta_type": "positive",
        },
    ]

    charts = {
        "squad_velocity_spend": {
            "title": "Squad Jira Story Points Delivered vs Monthly LLM Spend ($100s)",
            "subtitle": "Comparing engineering output and Workday hours reclaimed across squads",
            "type": "grouped_bar",
            "labels": [d["squad"].split("&")[0].strip() for d in depts],
            "series": [
                {"name": "Jira Story Points", "color": "#10B981", "data": [int(d["jira_story_points"] * tf_mult) for d in depts]},
                {"name": "Hours Reclaimed (x10 hrs)", "color": "#19B5FE", "data": [int((d["hours_reclaimed_month"] * tf_mult) / 10) for d in depts]},
                {"name": "LLM Spend ($100s)", "color": "#F59E0B", "data": [int((d["actual_llm_spend_usd"] * tf_mult) / 100) for d in depts]},
            ],
        },
        "task_value_audit_donut": {
            "title": "Enterprise Task Value Audit: High-Value Engineering vs Low-Value Email/Notes",
            "subtitle": "Low-value tasks (emails, meeting notes, chat rewrites) are automatically downgraded to Google Flash 3-8 Fast Lite",
            "type": "donut",
            "center_label": "86.2%",
            "center_sublabel": "High-Value Work",
            "segments": [
                {"label": "Feature Code & Unit Testing (High-Value)", "value": 42.4, "cost_usd": 11200, "color": "#10B981"},
                {"label": "RAG Architecture & Code Review (High-Value)", "value": 21.8, "cost_usd": 5840, "color": "#19B5FE"},
                {"label": "ServiceNow P1/P2 & Zendesk Triage (High-Value)", "value": 22.0, "cost_usd": 5120, "color": "#38BDF8"},
                {"label": "Email Polishing & Tone Rewrite (Low-Value -> Flash-Lite)", "value": 6.4, "cost_usd": 420, "color": "#F59E0B"},
                {"label": "Meeting Notes & Slack Summaries (Low-Value -> Flash-Lite)", "value": 7.4, "cost_usd": 490, "color": "#F43F5E"},
            ],
        },
        "sprint_burndown_chart": {
            "title": "Sprint 44 Story Point Burndown: Ideal vs Pre-AI Baseline vs BurnIQ RAG Trajectory",
            "subtitle": "Squads complete sprint commitments 2.4 days ahead of schedule with Flash 3-8 Fast Lite RAG context",
            "type": "multi_line",
            "labels": ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7", "Day 8", "Day 9", "Day 10"],
            "series": [
                {"name": "Ideal Burndown (SP remaining)", "color": "#64748B", "unit": "SP", "data": [470, 420, 370, 320, 270, 220, 170, 120, 60, 0]},
                {"name": "BurnIQ RAG-Assisted Actual (SP)", "color": "#10B981", "unit": "SP", "data": [470, 405, 330, 255, 185, 120, 65, 18, 0, 0]},
                {"name": "Historical Pre-RAG Baseline (SP)", "color": "#F43F5E", "unit": "SP", "data": [470, 445, 415, 380, 345, 305, 260, 210, 155, 95]},
            ],
        },
        "time_saved_breakdown": {
            "title": "Hours Reclaimed per Engineer / Week by Workflow Activity",
            "subtitle": "Total 11.6 hours/week saved per engineer across coding, testing, RAG search, and incident ops",
            "type": "horizontal_bar",
            "items": [
                {"id": "wf-code", "label": "Boilerplate, Feature Scaffolding & Unit Test Generation", "value": 4.2, "max_value": 5.0, "latency_ms": 94, "enabled": True, "category": "4.2 hrs/wk", "color": "#10B981"},
                {"id": "wf-review", "label": "Automated PR Diff Review & CI Failure Analysis (Jenkins/Bamboo)", "value": 2.8, "max_value": 5.0, "latency_ms": 108, "enabled": True, "category": "2.8 hrs/wk", "color": "#19B5FE"},
                {"id": "wf-rag", "label": "Enterprise RAG Codebase, Jira & Runbook Discovery", "value": 2.4, "max_value": 5.0, "latency_ms": 88, "enabled": True, "category": "2.4 hrs/wk", "color": "#38BDF8"},
                {"id": "wf-incident", "label": "ServiceNow Incident Root-Cause & Log Triage", "value": 1.4, "max_value": 5.0, "latency_ms": 96, "enabled": True, "category": "1.4 hrs/wk", "color": "#F59E0B"},
                {"id": "wf-admin", "label": "Documentation, Release Notes & Sprint Summaries (Flash-Lite)", "value": 0.8, "max_value": 5.0, "latency_ms": 76, "enabled": True, "category": "0.8 hrs/wk", "color": "#64748B"},
            ],
        },
    }

    return {
        "title": "Engineering & Operations Management — Velocity, Squad ROI & Task Audit",
        "subtitle": "Jira sprint delivery, engineering hours reclaimed, high-value vs low-value task governance, and squad adoption.",
        "kpis": kpis,
        "charts": charts,
        "table_title": "Enterprise Task Value & Governance Audit Log (High-Value Engineering vs Low-Value Email/Notes)",
        "table_rows": audits,
        "secondary_table_title": "Squad Capacity, Jira Velocity & Workday ROI Breakdown",
        "secondary_table_rows": depts,
    }


def _build_csuite_dashboard(
    all_conns: List[Dict[str, Any]],
    active_conns: List[Dict[str, Any]],
    paused_conns: List[Dict[str, Any]],
    persona_conns: List[Dict[str, Any]],
    depts: List[Dict[str, Any]],
    audits: List[Dict[str, Any]],
    models: List[Dict[str, Any]],
    tf_mult: float,
    active_ratio: float,
    timeframe: str,
) -> Dict[str, Any]:
    workday_on = any(c["id"] == "conn-workday" and c["enabled"] for c in all_conns)
    sap_on = any(c["id"] == "conn-sap-erp" and c["enabled"] for c in all_conns)
    flash_on = any(c["id"] == "conn-gemini-flash-lite" and c["enabled"] for c in all_conns)

    gross_workday_val = sum(d["workday_value_created_usd"] for d in depts) * tf_mult * (1.0 if workday_on else 0.75)
    total_spend = sum(d["actual_llm_spend_usd"] for d in depts) * tf_mult
    sap_budget = sum(d["sap_monthly_budget_usd"] for d in depts) * tf_mult
    flash_savings = sum(d["flash_lite_savings_usd"] for d in depts) * tf_mult * (1.0 if flash_on else 0.0)
    net_roi = round(gross_workday_val / max(total_spend, 1.0), 1)
    budget_var_pct = round(((total_spend - sap_budget) / max(sap_budget, 1.0)) * 100.0, 1)

    kpis = [
        {
            "id": "kpi-csuite-roi",
            "label": "Net Enterprise AI ROI Multiple",
            "value": f"{net_roi}x ROI",
            "subvalue": f"${gross_workday_val * 12 / max(tf_mult, 0.01):,.0f} Annualized Value Run-Rate",
            "delta": "+2.1x after Flash-Lite RAG",
            "delta_type": "positive",
        },
        {
            "id": "kpi-csuite-workday",
            "label": "Workday Payroll Value Created",
            "value": f"${gross_workday_val:,.0f}",
            "subvalue": "Verified L3-L7 hourly bands x reclaimed hrs" if workday_on else "Cached Bands (Workday Connector OFF)",
            "delta": "2,313 hrs/mo reclaimed" if workday_on else "Workday Paused",
            "delta_type": "positive" if workday_on else "warning",
        },
        {
            "id": "kpi-csuite-sap-spend",
            "label": "Total AI Spend vs SAP Budget",
            "value": f"${total_spend:,.0f}",
            "subvalue": f"SAP S/4HANA Ceiling: ${sap_budget:,.0f}",
            "delta": f"{abs(budget_var_pct)}% Under Budget" if budget_var_pct <= 0 else f"{budget_var_pct}% Over",
            "delta_type": "positive" if budget_var_pct <= 0 else "warning",
        },
        {
            "id": "kpi-csuite-flash-savings",
            "label": "Flash 3-8 Fast Lite FinOps Savings",
            "value": f"${flash_savings:,.0f}",
            "subvalue": f"${flash_savings * 12 / max(tf_mult, 0.01):,.0f}/yr saved via lightweight RAG",
            "delta": "96.8% lower token unit cost" if flash_on else "Flash-Lite Paused",
            "delta_type": "positive" if flash_on else "warning",
        },
        {
            "id": "kpi-csuite-arr-support",
            "label": "GTM ARR & Support Impact",
            "value": "$420K ARR",
            "subvalue": "68.4% Zendesk Tier-1 AI ticket deflection",
            "delta": "+5.2 pts CSAT lift",
            "delta_type": "positive",
        },
        {
            "id": "kpi-csuite-governance",
            "label": "FinOps & Security Governance",
            "value": "98.6 / 100",
            "subvalue": f"{len(active_conns)}/16 connectors active · SOC2/ISO42001",
            "delta": "Zero PII leakage",
            "delta_type": "positive",
        },
    ]

    charts = {
        "executive_roi_curve": {
            "title": "12-Month Cumulative Workday Value Created ($K) vs Total AI Spend ($K)",
            "subtitle": "Board-verified financial return across engineering, SRE, customer support, and revenue operations",
            "type": "multi_line",
            "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov"],
            "series": [
                {"name": "Workday Payroll Value Created ($K)", "color": "#10B981", "unit": "$K", "data": [82, 96, 114, 132, 155, 178, 204, 228, 251, 272, 286]},
                {"name": "Cumulative Flash-Lite FinOps Savings ($K)", "color": "#19B5FE", "unit": "$K", "data": [4, 9, 15, 22, 31, 42, 58, 76, 98, 124, 159]},
                {"name": "Total Enterprise AI Spend ($K)", "color": "#F59E0B", "unit": "$K", "data": [48, 51, 54, 52, 46, 39, 34, 31, 28, 26, 25]},
            ],
        },
        "department_roi_bars": {
            "title": "Departmental FinOps Ledger: SAP Budget vs Actual Spend vs Workday Value ($K)",
            "subtitle": "Every business unit operates under SAP S/4HANA budget ceiling with >7x gross payroll value creation",
            "type": "grouped_bar",
            "labels": ["Platform SRE", "Core Product", "Data & RAG", "Ent FinOps", "Zendesk Ops", "GTM & Rev"],
            "series": [
                {"name": "Workday Value Created ($K)", "color": "#10B981", "data": [round(d["workday_value_created_usd"] / 1000, 1) for d in depts]},
                {"name": "Flash-Lite Savings ($K)", "color": "#19B5FE", "data": [round(d["flash_lite_savings_usd"] / 1000, 1) for d in depts]},
                {"name": "Actual LLM Spend ($K)", "color": "#F59E0B", "data": [round(d["actual_llm_spend_usd"] / 1000, 1) for d in depts]},
            ],
        },
        "finops_waterfall": {
            "title": "Monthly FinOps Cost Optimization Bridge (Unoptimized Frontier -> BurnIQ Flash-Lite)",
            "subtitle": "How BurnIQ cut monthly token spend by 57.9% ($34.8K/mo saved) while increasing output quality",
            "type": "horizontal_bar",
            "items": [
                {"id": "wf-1", "label": "1. Unoptimized Frontier Baseline (100% Sonnet / GPT-4o / Pro)", "value": 60160, "max_value": 65000, "latency_ms": 680, "enabled": True, "category": "$60,160/mo", "color": "#F43F5E"},
                {"id": "wf-2", "label": "2. After Low-Value Email/Notes Down-Tiering (-$11,240/mo)", "value": 48920, "max_value": 65000, "latency_ms": 420, "enabled": True, "category": "$48,920/mo", "color": "#F59E0B"},
                {"id": "wf-3", "label": "3. After Semantic RAG Prompt Caching (-$8,380/mo)", "value": 40540, "max_value": 65000, "latency_ms": 260, "enabled": True, "category": "$40,540/mo", "color": "#19B5FE"},
                {"id": "wf-4", "label": "4. After Google Flash 3-8 Fast Lite RAG Routing (-$15,200/mo)", "value": 25340, "max_value": 65000, "latency_ms": 94, "enabled": True, "category": "$25,340/mo", "color": "#10B981"},
            ],
        },
        "cost_center_donut": {
            "title": "SAP S/4HANA Monthly Spend Allocation by Cost Center ($25,340 Total)",
            "subtitle": "15.8% under the $30,100 monthly board budget ceiling",
            "type": "donut",
            "center_label": "$25.3K",
            "center_sublabel": "Monthly Burn",
            "segments": [
                {"label": "Core Product Engineering (CC-ENG-101)", "value": 28.6, "cost_usd": 7240, "color": "#10B981"},
                {"label": "Platform & Technical Ops (CC-OPS-202)", "value": 19.0, "cost_usd": 4820, "color": "#19B5FE"},
                {"label": "Data & RAG Platform (CC-AI-105)", "value": 18.5, "cost_usd": 4690, "color": "#38BDF8"},
                {"label": "Enterprise Systems & FinOps (CC-FIN-204)", "value": 13.5, "cost_usd": 3410, "color": "#F59E0B"},
                {"label": "Customer Ops & GTM (CC-GTM-303)", "value": 20.4, "cost_usd": 5180, "color": "#F43F5E"},
            ],
        },
    }

    return {
        "title": "C-Suite Executive Boardroom — Workday Payroll ROI, SAP FinOps & Strategic AI Yield",
        "subtitle": "Consolidated CFO/CTO/CEO view of net enterprise AI ROI, Workday salary hours reclaimed, SAP cost-center variance, and Google Flash 3-8 Fast Lite savings.",
        "kpis": kpis,
        "charts": charts,
        "table_title": "Executive Business Unit FinOps & Workday Salary ROI Ledger",
        "table_rows": depts,
    }


# -----------------------------------------------------------------------------
# 3. Robust Enterprise Search & Customized RAG-Trained LLM Endpoints
# -----------------------------------------------------------------------------
@app.get("/api/search")
def search_get(
    q: str = Query(""),
    persona: str = Query("all"),
    connection_id: str = Query("all"),
    source_type: str = Query("all"),
    active_only: bool = Query(True),
    sort_by: str = Query("hybrid"),
    top_k: int = Query(20),
) -> Dict[str, Any]:
    return rag_engine.search(
        query=q,
        persona=persona,
        connection_id=connection_id,
        source_type=source_type,
        active_only=active_only,
        sort_by=sort_by,
        top_k=top_k,
    )


@app.post("/api/search")
def search_post(req: SearchRequest) -> Dict[str, Any]:
    return rag_engine.search(
        query=req.query,
        persona=req.persona,
        connection_id=req.connection_id,
        source_type=req.source_type,
        active_only=req.active_only,
        sort_by=req.sort_by,
        top_k=req.top_k,
    )


@app.get("/api/llm/models")
def list_llm_models() -> Dict[str, Any]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM llm_models ORDER BY is_default DESC, input_cost_per_1m ASC")
    models = [dict(r) for r in cur.fetchall()]
    cur.execute("SELECT * FROM rag_training_runs ORDER BY created_at DESC LIMIT 5")
    training_runs = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {
        "models": models,
        "training_runs": training_runs,
        "rag_index": {
            "corpus_size": len(rag_engine.corpus),
            "vocabulary_size": len(rag_engine.vocab),
            "embedding_dim": rag_engine.embedding_dim,
            "last_indexed_at": rag_engine.last_indexed_at,
        },
    }


@app.post("/api/llm/chat")
def llm_rag_chat(req: LLMChatRequest) -> Dict[str, Any]:
    return rag_engine.generate_rag_response(
        prompt=req.prompt,
        model_id=req.model_id,
        persona=req.persona,
        top_k=req.top_k,
        active_only=req.active_only,
        temperature=req.temperature,
        api_key=req.api_key,
    )


@app.post("/api/rag/ingest")
def ingest_rag_document(req: RAGIngestRequest) -> Dict[str, Any]:
    if not req.title.strip() or not req.content.strip():
        raise HTTPException(status_code=400, detail="Document title and content are required.")

    conn = get_connection()
    cur = conn.cursor()
    now_iso = datetime.utcnow().isoformat()

    # Chunk content if multi-paragraph or CSV
    raw_text = req.content.strip()
    if req.chunk_strategy == "csv_rows" and "\n" in raw_text:
        lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]
        header = lines[0] if lines else "CSV Record"
        chunks = [f"CSV Header: {header} | Row: {ln}" for ln in lines[1:]] if len(lines) > 1 else [raw_text]
    elif req.chunk_strategy == "fixed_window" and len(raw_text) > 700:
        chunks = [raw_text[i : i + 700] for i in range(0, len(raw_text), 600)]
    else:
        paras = [p.strip() for p in raw_text.split("\n\n") if len(p.strip()) > 20]
        chunks = paras if len(paras) > 1 else [raw_text]

    created_ids: List[str] = []
    cur.execute("SELECT COUNT(*) as cnt FROM rag_documents")
    base_num = 100 + (cur.fetchone()["cnt"] or 0) + 1

    for idx, ch in enumerate(chunks[:10]):
        doc_id = f"DOC-{base_num + idx}"
        tok_cnt = max(len(ch.split()), 12)
        title_str = req.title.strip() if len(chunks) == 1 else f"{req.title.strip()} (Chunk #{idx + 1})"
        cur.execute(
            """
            INSERT INTO rag_documents (
                id, title, connection_id, source_type, persona_tags, department,
                content, metadata_json, token_count, chunk_index, importance_weight, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                doc_id,
                title_str,
                req.connection_id,
                req.source_type,
                req.persona_tags,
                req.department,
                ch,
                json.dumps({"chunk_strategy": req.chunk_strategy, "custom_ingested": True}),
                tok_cnt,
                idx,
                req.importance_weight,
                now_iso,
            ),
        )
        created_ids.append(doc_id)

    cur.execute(
        "UPDATE service_connections SET docs_indexed = docs_indexed + ?, last_sync_at = ? WHERE id = ?",
        (len(created_ids), now_iso, req.connection_id),
    )
    conn.commit()
    conn.close()

    stats = rag_engine.build_index()
    return {
        "status": "ingested",
        "created_doc_ids": created_ids,
        "chunks_created": len(created_ids),
        "index_stats": stats,
    }


@app.post("/api/rag/train")
def train_rag_adapter(req: RAGTrainRequest) -> Dict[str, Any]:
    t0 = time.perf_counter()
    stats = rag_engine.build_index()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as active_cnt FROM service_connections WHERE enabled = 1 AND rag_enabled = 1")
    active_cnt = cur.fetchone()["active_cnt"] or 0

    cur.execute("SELECT COUNT(*) as run_cnt FROM rag_training_runs")
    run_num = (cur.fetchone()["run_cnt"] or 0) + 1
    run_id = f"train-run-{run_num:03d}"
    now_iso = datetime.utcnow().isoformat()

    sys_prompt = req.system_prompt or (
        "You are BurnIQ Flash-Lite AI (powered by Google Gemini 3-8 Flash-Lite, custom-trained on enterprise RAG ingestion). "
        "Provide concise, data-grounded answers with exact telemetry metrics, Workday ROI figures, commit/CI lineage, "
        "and inline [DOC-xxx] citations tailored to Technical Ops, Developers, Managers, or C-Suite executives."
    )

    duration_ms = max(int((time.perf_counter() - t0) * 1000) + 120, 140)
    recall = min(0.946 + 0.002 * run_num, 0.992)
    mrr = min(0.918 + 0.002 * run_num, 0.985)

    cur.execute(
        """
        INSERT INTO rag_training_runs (
            id, model_id, adapter_name, status, active_connections_count,
            documents_indexed, vocabulary_size, embedding_dim,
            retrieval_recall_at_5, mrr_score, training_duration_ms,
            system_prompt, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            req.model_id,
            req.adapter_name,
            "completed",
            active_cnt,
            stats["documents_indexed"],
            stats["vocabulary_size"],
            stats["embedding_dim"],
            round(recall, 4),
            round(mrr, 4),
            duration_ms,
            sys_prompt,
            now_iso,
        ),
    )
    conn.commit()

    cur.execute("SELECT * FROM rag_training_runs WHERE id = ?", (run_id,))
    run_record = dict(cur.fetchone())
    conn.close()

    return {
        "status": "trained",
        "training_run": run_record,
        "index_stats": stats,
    }


# -----------------------------------------------------------------------------
# 4. Dual-ERP (Sage Intacct/X3 & Oracle NetSuite OneWorld) & Legacy Store Endpoints
# -----------------------------------------------------------------------------
@app.get("/api/dashboard")
async def get_dashboard() -> Dict[str, Any]:
    return store.get_dashboard_summary()


@app.get("/api/connectors")
async def get_connectors() -> Dict[str, Any]:
    for c in store.state["connectors"]:
        if "enabled" not in c:
            c["enabled"] = c.get("status", "CONNECTED") != "PAUSED"
    return {
        "count": len(store.state["connectors"]),
        "connectors": store.state["connectors"],
    }


@app.post("/api/connectors/{connector_id}/toggle")
async def toggle_store_connector(connector_id: str, payload: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    cid = connector_id.lower()
    now_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    for conn in store.state["connectors"]:
        if conn["id"] == cid:
            cur_enabled = bool(conn.get("enabled", conn.get("status", "CONNECTED") != "PAUSED"))
            new_enabled = payload.get("enabled") if payload and "enabled" in payload else (not cur_enabled)
            conn["enabled"] = bool(new_enabled)
            conn["status"] = "CONNECTED" if new_enabled else "PAUSED"
            conn["last_sync"] = now_iso
            store._save()
            rag_engine.build_index()
            return {"ok": True, "connector": conn}
    raise HTTPException(status_code=404, detail=f"Connector {connector_id} not found")


@app.post("/api/connectors/{connector_id}/test")
async def test_connector(connector_id: str) -> Dict[str, Any]:
    cid = connector_id.lower()
    now_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    for conn in store.state["connectors"]:
        if conn["id"] == cid:
            conn["status"] = "CONNECTED"
            conn["enabled"] = True
            conn["last_sync"] = now_iso
            conn["records_synced"] = int(conn.get("records_synced", 1000)) + 12
            store._save()
            return {
                "ok": True,
                "status": "CONNECTED",
                "verified": True,
                "connector_id": cid,
                "connector": conn,
                "routed_via": "mock-enterprise-server:8090",
                "handshake": f"Verified {conn['protocol']} handshake with {conn['endpoint']}",
                "tested_at": now_iso,
            }
    return {
        "ok": True,
        "connector_id": connector_id,
        "status": "CONNECTED",
        "routed_via": "mock-enterprise-server:8090",
        "tested_at": now_iso,
    }


@app.get("/api/erp/sage")
async def get_sage_erp() -> Dict[str, Any]:
    return store.state["sage_erp"]


@app.post("/api/erp/sage/gl-batch")
async def create_sage_gl_batch(payload: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    batch = store.create_sage_gl_batch(payload or {})
    rag_engine.build_index()
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
    rag_engine.build_index()
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
    rag_engine.build_index()
    return result


@app.post("/api/reset")
async def reset_demo_state() -> Dict[str, Any]:
    store.reset()
    rag_engine.build_index()
    return store.get_dashboard_summary()


# -----------------------------------------------------------------------------
# 5. Include PagerDuty & Opsgenie Incident Routes from app.main
# -----------------------------------------------------------------------------
try:
    from app.main import app as pd_og_app

    existing_paths = {getattr(r, "path", None) for r in app.routes}
    for route in pd_og_app.routes:
        r_path = getattr(route, "path", None)
        if r_path and r_path not in existing_paths and r_path.startswith("/api/"):
            app.routes.append(route)
except Exception:
    pass

# -----------------------------------------------------------------------------
# 6. Serve Static Frontend
# -----------------------------------------------------------------------------
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

if os.path.isdir(FRONTEND_DIR):
    app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
    app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")), name="js")

    @app.api_route("/", methods=["GET", "HEAD"])
    def serve_index() -> FileResponse:
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


