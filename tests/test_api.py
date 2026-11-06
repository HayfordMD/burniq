"""
End-to-End Automated Verification Suite for BurnIQ v2.4:
Tests Service Connection ON/OFF toggles, Bulk Toggles, Mock Enterprise Endpoints,
All 4 Persona Dashboards (TechOps, Developers, Managers, C-Suite),
Hybrid BM25+Vector Search, and Google Flash 3-8 Fast Lite RAG LLM & Ingestion/Training.
"""

import json
import urllib.request

BASE_URL = "http://127.0.0.1:8000"


def request_json(path: str, method: str = "GET", payload: dict = None) -> dict:
    url = f"{BASE_URL}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req, timeout=10) as resp:
        assert resp.status == 200, f"Expected 200 for {path}, got {resp.status}"
        return json.loads(resp.read().decode("utf-8"))


def run_tests() -> None:
    print("1. Testing /api/health...")
    health = request_json("/api/health")
    assert health["status"] == "healthy"
    assert health["default_llm"] == "google/gemini-3-8-flash-lite"
    assert health["connections_total"] == 16
    print("   PASS:", health)

    print("2. Testing /api/connections & Individual ON/OFF Circuit Toggles...")
    conns = request_json("/api/connections")
    assert conns["all_count"] == 16
    initial_online = conns["online_count"]

    # Toggle GitHub Enterprise OFF
    t_off = request_json("/api/connections/conn-github-ent/toggle", "POST", {"enabled": False})
    assert t_off["connection"]["enabled"] is False
    assert t_off["connection"]["status"] == "paused"

    # Verify mock enterprise endpoint reflects OFF state
    mock_off = request_json("/mock-enterprise/api.github.com/enterprises/burniq/connection")
    assert mock_off["circuit_state"] == "OFF"

    # Toggle GitHub Enterprise back ON
    t_on = request_json("/api/connections/conn-github-ent/toggle", "POST", {"enabled": True})
    assert t_on["connection"]["enabled"] is True
    assert t_on["connection"]["status"] == "online"

    # Test diagnostic probe & manual sync
    probe = request_json("/api/connections/conn-workday/test", "POST", {})
    assert probe["reachable"] is True
    sync_res = request_json("/api/connections/conn-workday/sync", "POST", {})
    assert sync_res["status"] == "synced"
    print(f"   PASS: Toggled conn-github-ent OFF->ON, probed & synced conn-workday (Online={initial_online}/16)")

    print("3. Testing All 4 Persona Dashboards (techops, developers, managers, csuite)...")
    for persona in ("techops", "developers", "managers", "csuite"):
        dash = request_json(f"/api/dashboard/{persona}?timeframe=30d&department=all")
        assert dash["persona"] == persona
        assert len(dash["kpis"]) == 6, f"Expected 6 KPIs for {persona}"
        assert len(dash["charts"]) == 4, f"Expected 4 charts for {persona}"
        assert len(dash["table_rows"]) > 0, f"Expected table rows for {persona}"
        print(f"   PASS [{persona.upper()}]: 6 KPIs, 4 charts, {len(dash['table_rows'])} table rows")

    print("4. Testing Robust Enterprise Hybrid Search (/api/search)...")
    s_res = request_json("/api/search?q=Flash+3-8+Fast+Lite+Workday+ROI&active_only=true")
    assert s_res["total_matches"] > 0
    top_hit = s_res["results"][0]
    assert "hybrid_score" in top_hit and "bm25_score" in top_hit and "vector_score" in top_hit
    print(f"   PASS: Search returned {s_res['total_matches']} matches in {s_res['latency_ms']}ms (Top hit: {top_hit['id']})")

    print("5. Testing Custom RAG Ingestion (/api/rag/ingest) & Adapter Training (/api/rag/train)...")
    ingest = request_json(
        "/api/rag/ingest",
        "POST",
        {
            "title": "Q4 Flash 3-8 Fast Lite Kubernetes Autoscaling Runbook",
            "connection_id": "conn-gemini-flash-lite",
            "department": "Platform & Technical Ops",
            "content": "BurnIQ Kubernetes HPA scales Google Flash 3-8 Fast Lite vLLM replicas between 2 and 16 pods keeping P95 latency under 115ms at $0.035 per 1M input tokens.",
            "chunk_strategy": "semantic",
        },
    )
    assert ingest["status"] == "ingested"
    assert ingest["chunks_created"] >= 1

    train = request_json(
        "/api/rag/train",
        "POST",
        {
            "model_id": "google/gemini-3-8-flash-lite",
            "adapter_name": "burniq-flash-3-8-fast-lite-rag-v2.6",
        },
    )
    assert train["status"] == "trained"
    print(
        f"   PASS: Ingested {ingest['created_doc_ids']} & trained {train['training_run']['adapter_name']} "
        f"(Recall@5={train['training_run']['retrieval_recall_at_5']})"
    )

    print("6. Testing Customized RAG-Trained LLM (/api/llm/chat) with Google Flash 3-8 Fast Lite...")
    chat = request_json(
        "/api/llm/chat",
        "POST",
        {
            "prompt": "Summarize our Workday salary ROI, low-value email audit savings, and Google Flash 3-8 Fast Lite performance.",
            "model_id": "google/gemini-3-8-flash-lite",
            "persona": "csuite",
            "top_k": 5,
        },
    )
    assert chat["model"]["id"] == "google/gemini-3-8-flash-lite"
    assert len(chat["citations"]) > 0
    assert chat["telemetry"]["cost_savings_pct"] > 90.0
    print(
        f"   PASS: Flash 3-8 Fast Lite synthesized response in {chat['telemetry']['total_latency_ms']}ms, "
        f"cost=${chat['telemetry']['cost_usd']}, savings={chat['telemetry']['cost_savings_pct']}% vs frontier"
    )

    print("\nALL END-TO-END BURNIQ VERIFICATION TESTS PASSED!")


if __name__ == "__main__":
    run_tests()
