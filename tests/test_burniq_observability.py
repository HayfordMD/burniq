"""End-to-end verification tests for BurnIQ Datadog, Substrate, New Relic & Soluble integrations."""

from __future__ import annotations

import json
import urllib.request


BASE_URL = "http://127.0.0.1:8000"
GATEWAY_URL = "http://127.0.0.1:8090"

_NO_PROXY_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def _req(url: str, method: str = "GET", payload: dict | None = None) -> tuple[int, str, dict | None]:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with _NO_PROXY_OPENER.open(req, timeout=5) as resp:
        body = resp.read().decode("utf-8")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = None
        return resp.status, body, parsed


def run_all_observability_tests() -> None:
    # 1. Health check includes Datadog, Substrate, New Relic, Soluble
    st, _, health = _req(f"{BASE_URL}/api/health")
    assert st == 200 and health is not None
    feat = health["featured_integrations"]
    assert "datadog" in feat and "substrate" in feat and "newrelic" in feat and "soluble" in feat

    # 2. Verify Mock Enterprise Gateway on both Port 8000 (/mock-enterprise) and Port 8090
    for vendor_path, expected_vendor in [
        ("api.datadoghq.com/api/v2/connection", "Datadog"),
        ("api.datadoghq.com/api/v2/llm-obs/v1/spans", "Datadog LLM Observability"),
        ("api.datadoghq.com/api/v2/dora/metrics", "Datadog DORA Metrics"),
        ("substrate.office.com/v1.0/graph/connection", "Substrate"),
        ("substrate.office.com/v1.0/graph/signals", "Microsoft Substrate Graph"),
        ("api.substrate.run/v1/workloads", "Substrate AI Compute"),
        ("api.newrelic.com/graphql/connection", "New Relic"),
        ("api.newrelic.com/v2/apm/applications", "New Relic APM"),
        ("api.newrelic.com/v2/ai-monitoring/models", "New Relic AI Monitoring"),
        ("api.soluble.io/api/v1/connection", "Soluble"),
        ("app.soluble.cloud/api/v1/connection", "Soluble"),
        ("api.soluble.io/api/v1/findings", "Soluble IaC Findings"),
    ]:
        for base in [f"{BASE_URL}/mock-enterprise", GATEWAY_URL]:
            st, _, js = _req(f"{base}/{vendor_path}")
            assert st == 200 and js is not None, f"Failed on {base}/{vendor_path}"
            assert js["status"] == "CONNECTED"
            assert js["ok"] is True
            assert expected_vendor in js["vendor"]

    # 3. Verify dedicated REST APIs (/api/datadog, /api/substrate, /api/newrelic, /api/soluble, /api/observability)
    st, _, dd = _req(f"{BASE_URL}/api/datadog")
    assert st == 200 and dd is not None
    assert dd["vendor"] == "Datadog"
    assert len(dd["llm_observability_spans"]) >= 5
    assert len(dd["dora_comparison"]["by_cicd_provider"]) == 5
    assert len(dd["apm_monitors"]) >= 4

    st, _, sub = _req(f"{BASE_URL}/api/substrate")
    assert st == 200 and sub is not None
    assert "Substrate" in sub["vendor"]
    assert len(sub["microsoft_substrate_signals"]) >= 4
    assert len(sub["substrate_compute_workloads"]) >= 4

    st, _, nr = _req(f"{BASE_URL}/api/newrelic")
    assert st == 200 and nr is not None
    assert nr["vendor"] == "New Relic"
    assert len(nr["apm_services"]) >= 4
    assert len(nr["ai_monitoring_models"]) >= 4

    st, _, sol = _req(f"{BASE_URL}/api/soluble")
    assert st == 200 and sol is not None
    assert "Soluble" in sol["vendor"]
    assert len(sol["security_findings"]) >= 4

    st, _, obs = _req(f"{BASE_URL}/api/observability")
    assert st == 200 and obs is not None
    assert len(obs["cross_platform_correlations"]) == 3

    # 4. Verify Interactive Observability / NRQL Query Engine
    for engine, query in [
        ("newrelic_nrql", "SELECT average(duration), apdex(duration) FROM Transaction FACET appName"),
        ("newrelic_nrql", "SELECT sum(tokenCount) FROM LlmChatCompletionSummary FACET model"),
        ("datadog_spans", "datadog llm_obs spans service:*"),
        ("substrate_graph", "substrate.office.com/v1.0/graph/signals"),
        ("soluble_policy", "soluble iac findings"),
    ]:
        st, _, qres = _req(
            f"{BASE_URL}/api/observability/query",
            method="POST",
            payload={"engine": engine, "query": query},
        )
        assert st == 200 and qres and qres["status"] == "SUCCESS"
        assert qres["row_count"] >= 4

    # 5. Verify Soluble Live IaC Auto-Remediation Scanner
    st, _, scan_res = _req(
        f"{BASE_URL}/api/soluble/scan",
        method="POST",
        payload={
            "iac_type": "Terraform",
            "llm_author": "Claude 3.7 Sonnet",
            "code_snippet": 'resource "aws_iam_policy" "p" { Action = "*" encrypted = false }',
        },
    )
    assert st == 200 and scan_res and scan_res["status"] == "SCAN_COMPLETE"
    assert scan_res["findings_count"] >= 2
    assert "Soluble Auto-Remediated Patch" in scan_res["remediated_code"]

    # 6. Verify Substrate Governance Policy Enforcement
    st, _, pol_res = _req(
        f"{BASE_URL}/api/substrate/enforce-policy",
        method="POST",
        payload={"signal_id": "SUB-M365-801", "action": "ENFORCE_HAIKU_FLASH_ROUTING"},
    )
    assert st == 200 and pol_res and pol_res["status"] == "POLICY_APPLIED"

    # 7. Verify Connector Handshake Tests & CSV Exports for all 4 vendors
    for cid in ["datadog", "substrate", "newrelic", "soluble"]:
        st, _, tconn = _req(f"{BASE_URL}/api/connectors/{cid}/test", method="POST")
        assert st == 200 and tconn and tconn["status"] == "CONNECTED"
        assert tconn["routed_via"] == "mock-enterprise-server:8090"

        st, csv_body, _ = _req(f"{BASE_URL}/api/export/{cid}")
        assert st == 200 and len(csv_body.splitlines()) >= 5

    st, _, all_conn = _req(f"{BASE_URL}/api/connectors/test-all", method="POST")
    assert st == 200 and all_conn and all_conn["status"] == "ALL_CONNECTED"
    assert all_conn["passed_count"] >= 22

    # 8. Verify UI HTML includes Datadog, Substrate, New Relic, Soluble
    st, html_text, _ = _req(f"{BASE_URL}/")
    assert st == 200
    for keyword in ["Datadog", "Substrate", "New Relic", "Soluble", "panel-observability"]:
        assert keyword in html_text, f"Missing {keyword} in index.html"

    # Reset state cleanly
    _req(f"{BASE_URL}/api/reset", method="POST")
    print("ALL BURNIQ DATADOG, SUBSTRATE, NEW RELIC & SOLUBLE TESTS PASSED!")


if __name__ == "__main__":
    run_all_observability_tests()
