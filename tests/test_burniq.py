from __future__ import annotations

import asyncio
import unittest
from unittest.mock import MagicMock

from app.data_store import BurnIQDataStore
from app.main import (
    api_csv_export,
    api_csv_import,
    api_dashboard,
    api_employees,
    api_erp_crm,
    api_health,
    api_incidents_attribution,
    api_list_connectors,
    api_low_value_tasks,
    api_observability,
    api_opsgenie_alert_action,
    api_opsgenie_alerts,
    api_opsgenie_create_alert,
    api_opsgenie_heartbeats,
    api_opsgenie_ping_heartbeat,
    api_opsgenie_schedules,
    api_opsgenie_status,
    api_opsgenie_sync,
    api_opsgenie_teams,
    api_pagerduty_incident_action,
    api_pagerduty_incidents,
    api_pagerduty_rules,
    api_pagerduty_schedules,
    api_pagerduty_services,
    api_pagerduty_status,
    api_pagerduty_sync,
    api_pagerduty_trigger_incident,
    api_releases,
    api_summary,
    api_test_connector,
    serve_index,
)
from app.mock_enterprise import (
    mock_gateway_health,
    mock_opsgenie_alert_action,
    mock_opsgenie_alerts,
    mock_opsgenie_connection,
    mock_opsgenie_create_alert,
    mock_opsgenie_heartbeat_ping,
    mock_opsgenie_heartbeats,
    mock_opsgenie_schedules,
    mock_opsgenie_teams,
    mock_pagerduty_connection,
    mock_pagerduty_enqueue,
    mock_pagerduty_incidents,
    mock_pagerduty_schedules,
    mock_pagerduty_services,
    mock_universal_enterprise_endpoint,
)


def run_async(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class BurnIQPlatformTestSuite(unittest.TestCase):
    def test_01_data_store_initialization_and_summary(self):
        store = BurnIQDataStore()
        summary = store.get_executive_summary()
        self.assertEqual(summary["connectors_total"], 22)
        self.assertEqual(summary["connectors_connected"], 22)
        self.assertEqual(summary["pagerduty_summary"]["status"], "connected")
        self.assertEqual(summary["opsgenie_summary"]["status"], "connected")
        self.assertGreater(summary["llm_telemetry"]["total_llm_spend_usd"], 0)
        self.assertGreater(summary["workday_roi"]["total_incident_mttr_hours_saved"], 0)
        self.assertGreater(summary["workday_roi"]["net_salary_roi_usd"], 0)
        self.assertGreater(summary["pagerduty_summary"]["net_incident_roi_usd"], 0)

    def test_02_pagerduty_lifecycle_and_bidirectional_mirroring(self):
        store = BurnIQDataStore()
        initial_pd_count = len(store.pagerduty_incidents)
        initial_og_count = len(store.opsgenie_alerts)

        # Trigger PagerDuty incident with Opsgenie mirror
        created = store.trigger_pagerduty_incident(
            {
                "title": "High Latency in Claude Sonnet Code Review Pipeline",
                "service_id": "PD-SVC-01",
                "urgency": "high",
                "severity": "critical",
                "priority": "P1",
                "llm_provider": "Claude",
                "llm_model": "claude-3-7-sonnet",
                "observability_source": "Datadog",
                "mirror_to_opsgenie": True,
            }
        )
        self.assertEqual(len(store.pagerduty_incidents), initial_pd_count + 1)
        self.assertEqual(len(store.opsgenie_alerts), initial_og_count + 1)
        inc_id = created["id"]
        self.assertEqual(created["status"], "triggered")
        self.assertTrue(created["opsgenie_linked_alert_id"].startswith("OG-ALT-"))

        # Acknowledge PagerDuty incident -> also acknowledges Opsgenie mirror
        acked = store.update_pagerduty_incident_status(inc_id, "acknowledge")
        self.assertEqual(acked["status"], "acknowledged")
        mirrored_og = next(
            a for a in store.opsgenie_alerts if a["id"] == created["opsgenie_linked_alert_id"]
        )
        self.assertEqual(mirrored_og["status"], "acked")

        # Resolve PagerDuty incident -> also closes Opsgenie mirror
        resolved = store.update_pagerduty_incident_status(inc_id, "resolve")
        self.assertEqual(resolved["status"], "resolved")
        self.assertEqual(mirrored_og["status"], "closed")

    def test_03_opsgenie_lifecycle_and_heartbeats(self):
        store = BurnIQDataStore()
        created_og = store.create_opsgenie_alert(
            {
                "message": "Genie Alert: Oracle NetSuite & Sage Intacct Sync Drift",
                "priority": "P2",
                "team": "team-finops-erp",
                "source": "Oracle NetSuite",
                "llm_provider": "Gemini",
                "llm_model": "gemini-2.5-pro",
            }
        )
        alert_id = created_og["id"]
        self.assertEqual(created_og["status"], "open")

        snoozed = store.update_opsgenie_alert_status(alert_id, "snooze")
        self.assertEqual(snoozed["status"], "snoozed")

        escalated = store.update_opsgenie_alert_status(alert_id, "escalate")
        self.assertEqual(escalated["status"], "acked")
        self.assertTrue(escalated["linked_pd_incident_id"].startswith("PD-INC-"))

        acked = store.update_opsgenie_alert_status(alert_id, "acknowledge")
        self.assertEqual(acked["status"], "acked")

        closed = store.update_opsgenie_alert_status(alert_id, "close")
        self.assertEqual(closed["status"], "closed")

        # Heartbeat ping
        hb = store.ping_opsgenie_heartbeat("claude-anthropic-enterprise-hb")
        self.assertEqual(hb["status"], "healthy")
        self.assertFalse(hb["expired"])

    def test_04_fastapi_main_endpoints(self):
        h = api_health()
        self.assertEqual(h["status"], "ok")
        self.assertTrue(h["healthy"])
        self.assertEqual(h["pagerduty"]["status"], "connected")
        self.assertEqual(h["opsgenie"]["status"], "connected")
        self.assertEqual(h["connectors_total"], 22)

        s = api_summary()
        self.assertIn("pagerduty_summary", s)
        self.assertIn("opsgenie_summary", s)

        d = api_dashboard()
        self.assertIn("pagerduty", d)
        self.assertIn("opsgenie", d)
        self.assertIn("employees", d)
        self.assertIn("commits_and_releases", d)

        conns = api_list_connectors()
        self.assertEqual(conns["total"], 22)

        for alias in ["pagerduty", "opsgenie", "genie", "netsuite", "sage", "datadog", "substrate", "newrelic", "soluble"]:
            res = api_test_connector(alias)
            self.assertEqual(res["status"], "connected")
            self.assertTrue(res["verified"])

        pd_st = api_pagerduty_status()
        self.assertEqual(pd_st["connector"]["id"], "pagerduty")
        self.assertGreaterEqual(len(pd_st["incidents"]), 5)

        og_st = api_opsgenie_status()
        self.assertEqual(og_st["connector"]["id"], "opsgenie")
        self.assertGreaterEqual(len(og_st["alerts"]), 5)

    def test_05_fastapi_pagerduty_and_opsgenie_mutation_routes(self):
        # PagerDuty trigger, ack, resolve, sync
        trig = api_pagerduty_trigger_incident(
            {
                "title": "Unit Test PagerDuty Incident",
                "service_id": "PD-SVC-02",
                "urgency": "high",
                "severity": "error",
                "priority": "P2",
                "mirror_to_opsgenie": True,
            }
        )
        inc_id = trig["incident"]["id"]
        ack = api_pagerduty_incident_action(inc_id, "acknowledge")
        self.assertEqual(ack["incident"]["status"], "acknowledged")
        res = api_pagerduty_incident_action(inc_id, "resolve")
        self.assertEqual(res["incident"]["status"], "resolved")

        self.assertGreaterEqual(api_pagerduty_incidents()["total"], 5)
        self.assertGreaterEqual(api_pagerduty_services()["total"], 4)
        self.assertGreaterEqual(api_pagerduty_schedules()["total"], 4)
        self.assertGreaterEqual(api_pagerduty_rules()["total"], 4)
        self.assertEqual(api_pagerduty_sync()["status"], "synced")

        # Opsgenie / Genie routes
        og_create = api_opsgenie_create_alert(
            {
                "message": "Unit Test Genie Alert",
                "priority": "P2",
                "team": "team-sre-core",
            }
        )
        alt_id = og_create["alert"]["id"]
        og_ack = api_opsgenie_alert_action(alt_id, "acknowledge")
        self.assertEqual(og_ack["alert"]["status"], "acked")
        og_snz = api_opsgenie_alert_action(alt_id, "snooze")
        self.assertEqual(og_snz["alert"]["status"], "snoozed")
        og_esc = api_opsgenie_alert_action(alt_id, "escalate")
        self.assertEqual(og_esc["alert"]["status"], "acked")
        og_cls = api_opsgenie_alert_action(alt_id, "close")
        self.assertEqual(og_cls["alert"]["status"], "closed")

        self.assertGreaterEqual(api_opsgenie_alerts()["total"], 5)
        self.assertGreaterEqual(api_opsgenie_schedules()["total"], 4)
        self.assertGreaterEqual(api_opsgenie_teams()["total"], 4)
        self.assertGreaterEqual(api_opsgenie_heartbeats()["total"], 5)
        self.assertEqual(
            api_opsgenie_ping_heartbeat("gemini-vertex-telemetry-hb")["status"],
            "pinged",
        )
        self.assertEqual(api_opsgenie_sync()["status"], "synced")

    def test_06_enterprise_and_csv_endpoints(self):
        attr = api_incidents_attribution()
        self.assertIn("pagerduty_summary", attr)
        self.assertIn("opsgenie_summary", attr)
        self.assertGreaterEqual(api_employees()["total"], 6)
        self.assertGreaterEqual(api_releases()["total"], 5)
        self.assertGreaterEqual(api_low_value_tasks()["total"], 3)
        self.assertGreaterEqual(api_erp_crm()["total"], 5)
        self.assertGreaterEqual(api_observability()["total"], 4)

        csv_imp = api_csv_import(
            {
                "filename": "unit_test.csv",
                "csv_text": "incident_id,alert_id,llm_provider,tokens,roi_usd\nPD-INC-9099,OG-ALT-7799,Claude,55000,980.00\n",
            }
        )
        self.assertEqual(csv_imp["batch"]["rows_imported"], 1)

        csv_exp = api_csv_export()
        self.assertEqual(csv_exp.media_type, "text/csv")

        idx = serve_index()
        self.assertEqual(idx.status_code, 200)

    def test_07_mock_enterprise_gateway_routes(self):
        root = mock_gateway_health()
        self.assertEqual(root["status"], "healthy")

        pd_conn = mock_pagerduty_connection()
        self.assertEqual(pd_conn["host"], "api.pagerduty.com")
        self.assertIn("incidents", mock_pagerduty_incidents())
        self.assertIn("services", mock_pagerduty_services())
        self.assertIn("schedules", mock_pagerduty_schedules())

        ev = mock_pagerduty_enqueue(
            {
                "event_action": "trigger",
                "payload": {
                    "summary": "Events v2 Trigger Test",
                    "severity": "critical",
                    "source": "New Relic",
                },
            }
        )
        self.assertEqual(ev["status"], "success")

        og_conn = mock_opsgenie_connection()
        self.assertEqual(og_conn["host"], "api.opsgenie.com")
        self.assertIn("data", mock_opsgenie_alerts())
        self.assertIn("data", mock_opsgenie_schedules())
        self.assertIn("data", mock_opsgenie_teams())
        self.assertIn("data", mock_opsgenie_heartbeats())
        self.assertIn(
            "heartbeat",
            mock_opsgenie_heartbeat_ping("workday-netsuite-sage-roi-hb"),
        )

        created_mock_og = mock_opsgenie_create_alert({"message": "Mock Gateway Genie Alert"})
        self.assertIn("alert", created_mock_og)
        alt_id = created_mock_og["alert"]["id"]
        acted_mock_og = mock_opsgenie_alert_action(alt_id, "acknowledge")
        self.assertEqual(acted_mock_og["alert"]["status"], "acked")

        # Verify universal host connection check for other enterprise integrations
        dummy_req = MagicMock()
        dummy_req.method = "GET"
        for host, path in [
            ("company.workday.com", "ccx/service/customreport2/payroll"),
            ("api.powerbi.com", "v1.0/myorg/datasets"),
            ("company.zendesk.com", "api/v2/tickets.json"),
            ("company.service-now.com", "api/now/table/incident"),
            ("api.datadoghq.com", "api/v2/Monitor/events"),
            ("api.substrate.com", "v1/cost-attribution"),
            ("api.newrelic.com", "graphql"),
            ("api.soluble.io", "api/v1/org/assessments"),
            ("api.intacct.com", "ia/xml/xmlgw.phtml"),
            ("company.suitetalk.api.netsuite.com", "services/rest/record/v1/journalEntry"),
        ]:
            res = run_async(mock_universal_enterprise_endpoint(host, path, dummy_req))
            self.assertEqual(res["status"], "connected")
            self.assertTrue(res["ok"])


if __name__ == "__main__":
    unittest.main()
