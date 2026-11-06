"""End-to-end verification tests for BurnIQ Sage Intacct/X3 & Oracle NetSuite OneWorld ERP integrations."""

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


def run_all_tests() -> None:
    # 1. Reset baseline
    status, _, data = _req(f"{BASE_URL}/api/reset", method="POST")
    assert status == 200 and data is not None
    assert data["kpis"]["sage_entities_active"] == 3
    assert data["kpis"]["netsuite_subsidiaries_active"] == 4
    assert data["kpis"]["connected_enterprise_systems"] >= 22

    # 2. Test Sage Intacct & Sage X3 Mock Gateway & API
    for url in [
        f"{BASE_URL}/mock-enterprise/api.intacct.com/ia/api/v1/connection",
        f"{BASE_URL}/mock-enterprise/company.sage.com/api/v1/connection",
        f"{GATEWAY_URL}/api.intacct.com/ia/api/v1/connection",
    ]:
        st, _, js = _req(url)
        assert st == 200 and js and js["ok"] is True
        assert js["company_id"] == "BURNIQ-CORP-US"

    st, _, sage_data = _req(f"{BASE_URL}/api/erp/sage")
    assert st == 200 and sage_data is not None
    assert len(sage_data["gl_accounts"]) == 5
    assert any(a["account_no"] == "1650-01" for a in sage_data["gl_accounts"])

    # Post new Sage GL Batch
    st, _, batch_resp = _req(
        f"{BASE_URL}/api/erp/sage/gl-batch",
        method="POST",
        payload={
            "entity_id": "E100",
            "journal_symbol": "AIRD",
            "debit_account": "1650-01",
            "amount_usd": 17500.00,
            "project_dim": "REL-2026.11.4 / JIRA-EPIC-402",
            "description": "Automated Test ASC 350-40 Sage Intacct Batch",
        },
    )
    assert st == 200 and batch_resp and batch_resp["status"] == "POSTED"
    assert batch_resp["batch"]["amount_usd"] == 17500.00

    # 3. Test Oracle NetSuite OneWorld & SuiteQL Mock Gateway & API
    for url in [
        f"{BASE_URL}/mock-enterprise/company.suitetalk.api.netsuite.com/services/rest/record/v1/connection",
        f"{BASE_URL}/mock-enterprise/company.netsuite.com/api/v1/connection",
        f"{GATEWAY_URL}/company.suitetalk.api.netsuite.com/services/rest/record/v1/connection",
    ]:
        st, _, js = _req(url)
        assert st == 200 and js and js["ok"] is True
        assert js["account_id"] == "TSTDRV2026991"

    st, _, ns_data = _req(f"{BASE_URL}/api/erp/netsuite")
    assert st == 200 and ns_data is not None
    assert len(ns_data["subsidiaries"]) == 4

    # Post new NetSuite Journal Entry
    st, _, je_resp = _req(
        f"{BASE_URL}/api/erp/netsuite/journal-entry",
        method="POST",
        payload={
            "subsidiary": "SUB-2 BurnIQ Technologies US Inc.",
            "debit_account": "16500 Capitalized Software R&D (Intangible Asset)",
            "cseg_ai_provider": "Anthropic Claude + Google Gemini",
            "cseg_task_value_tier": "Tier 1: Production Release Code",
            "amount_usd": 21200.00,
            "memo": "Automated Test NetSuite OneWorld CapEx JE",
        },
    )
    assert st == 200 and je_resp and je_resp["status"] == "POSTED"
    assert je_resp["journal_entry"]["amount_usd"] == 21200.00

    # Execute SuiteQL Queries
    for q in [
        "SELECT * FROM transaction WHERE type = 'Journal'",
        "SELECT * FROM subsidiary",
        "SELECT * FROM purchaseOrder",
        "SELECT * FROM amortizationSchedule",
    ]:
        st, _, sq = _req(
            f"{BASE_URL}/api/erp/netsuite/suiteql",
            method="POST",
            payload={"query": q},
        )
        assert st == 200 and sq and sq["row_count"] >= 2

    # 4. Test Low-Value Task Audit & Smart Model Routing
    st, _, opt_resp = _req(f"{BASE_URL}/api/audit/optimize-routing", method="POST")
    assert st == 200 and opt_resp and opt_resp["smart_routing_enabled"] is True
    assert opt_resp["monthly_savings_realized_usd"] > 8000.0

    # 5. Test CSV Export for Sage & NetSuite
    st, sage_csv, _ = _req(f"{BASE_URL}/api/export/sage")
    assert st == 200 and "BATCH-SAGE-" in sage_csv
    st, ns_csv, _ = _req(f"{BASE_URL}/api/export/netsuite")
    assert st == 200 and "JE-NS-" in ns_csv

    # 6. Reset back to clean baseline for live UI preview
    _req(f"{BASE_URL}/api/reset", method="POST")
    print("ALL BURNIQ SAGE & ORACLE NETSUITE ERP TESTS PASSED!")


if __name__ == "__main__":
    run_all_tests()
