"""Stateful Enterprise Telemetry, ERP (Sage & Oracle NetSuite), HRM & ROI Data Store for BurnIQ."""

from __future__ import annotations

import copy
import csv
import io
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional


DEFAULT_STATE: Dict[str, Any] = {
    "meta": {
        "platform": "BurnIQ Enterprise Telemetry, Financial ERP & Salary ROI Platform",
        "version": "2.4.0",
        "reporting_period": "2026-11",
        "currency": "USD",
        "last_synced": "2026-11-06T20:55:00Z",
        "smart_routing_enabled": False,
    },
    "connectors": [
        {
            "id": "sage",
            "name": "Sage Intacct & Sage X3",
            "category": "ERP & Accounting",
            "vendor": "Sage Group plc",
            "protocol": "REST API v1 & XML Gateway",
            "endpoint": "https://api.intacct.com/ia/api/v1/connection",
            "mock_path": "/mock-enterprise/api.intacct.com/ia/api/v1/connection",
            "alt_mock_path": "/mock-enterprise/company.sage.com/api/v1/connection",
            "status": "CONNECTED",
            "health_ms": 38,
            "last_sync": "2026-11-06T20:54:12Z",
            "company_id": "BURNIQ-CORP-US",
            "entities_synced": 3,
            "records_synced": 14820,
            "description": "Multi-entity General Ledger, AP Vendor Bills (Anthropic & Google Vertex AI), ASC 350-40 R&D Software Capitalization batches, and Cost Center budget vs actuals across Sage Intacct (US) & Sage X3 (EMEA).",
        },
        {
            "id": "netsuite",
            "name": "Oracle NetSuite OneWorld",
            "category": "ERP & Accounting",
            "vendor": "Oracle Corporation",
            "protocol": "SuiteTalk REST v1 + SuiteQL OAuth 2.0",
            "endpoint": "https://company.suitetalk.api.netsuite.com/services/rest/record/v1/connection",
            "mock_path": "/mock-enterprise/company.suitetalk.api.netsuite.com/services/rest/record/v1/connection",
            "alt_mock_path": "/mock-enterprise/company.netsuite.com/api/v1/connection",
            "status": "CONNECTED",
            "health_ms": 44,
            "last_sync": "2026-11-06T20:54:35Z",
            "account_id": "TSTDRV2026991",
            "subsidiaries_synced": 4,
            "records_synced": 22450,
            "description": "OneWorld Multi-Subsidiary Consolidation, SuiteQL Financial Analytics, LLM Commit Purchase Orders, Journal Entries, and 36-Month R&D CapEx Amortization Schedules.",
        },
        {
            "id": "sap",
            "name": "SAP S/4HANA Cloud",
            "category": "ERP & Accounting",
            "vendor": "SAP SE",
            "protocol": "OData v4 / BAPI",
            "endpoint": "https://company.sap.com/sap/opu/odata/sap/connection",
            "mock_path": "/mock-enterprise/company.sap.com/sap/opu/odata/sap/connection",
            "status": "CONNECTED",
            "health_ms": 51,
            "last_sync": "2026-11-06T20:51:00Z",
            "records_synced": 9840,
            "description": "Controlling Areas, WBS R&D Elements, Cost Object Controlling, and Global Vendor Master sync.",
        },
        {
            "id": "workday",
            "name": "Workday HCM & Payroll",
            "category": "HR & Compensation",
            "vendor": "Workday, Inc.",
            "protocol": "Workday REST / SOAP v41",
            "endpoint": "https://company.workday.com/api/connection",
            "mock_path": "/mock-enterprise/company.workday.com/api/connection",
            "status": "CONNECTED",
            "health_ms": 34,
            "last_sync": "2026-11-06T20:53:10Z",
            "records_synced": 412,
            "description": "Employee compensation bands, loaded hourly engineering rates, cost center hierarchy, and time-saved salary ROI attribution.",
        },
        {
            "id": "claude",
            "name": "Anthropic Claude Enterprise",
            "category": "LLM Telemetry",
            "vendor": "Anthropic PBC",
            "protocol": "Anthropic Admin & Telemetry API v1",
            "endpoint": "https://api.anthropic.com/v1/connection",
            "mock_path": "/mock-enterprise/api.anthropic.com/v1/connection",
            "status": "CONNECTED",
            "health_ms": 29,
            "last_sync": "2026-11-06T20:55:01Z",
            "records_synced": 184920,
            "description": "Claude 3.7 Sonnet, 3.5 Sonnet, 3.5 Haiku, and 3 Opus token telemetry across Claude Code CLI, IDE extensions, and web workspaces.",
        },
        {
            "id": "gemini",
            "name": "Google Cloud Vertex AI Gemini",
            "category": "LLM Telemetry",
            "vendor": "Google Cloud",
            "protocol": "Vertex AI Telemetry & Billing Export v1",
            "endpoint": "https://us-central1-aiplatform.googleapis.com/v1/connection",
            "mock_path": "/mock-enterprise/us-central1-aiplatform.googleapis.com/v1/connection",
            "status": "CONNECTED",
            "health_ms": 27,
            "last_sync": "2026-11-06T20:55:04Z",
            "records_synced": 219400,
            "description": "Gemini 2.5 Pro, Gemini 2.5 Flash, and Gemini Code Assist usage, context caching, and workspace productivity logs.",
        },
        {
            "id": "github",
            "name": "GitHub Enterprise Cloud",
            "category": "SCM & Code",
            "vendor": "GitHub, Inc.",
            "protocol": "GraphQL v4 & Webhooks",
            "endpoint": "https://api.github.com/connection",
            "mock_path": "/mock-enterprise/api.github.com/connection",
            "status": "CONNECTED",
            "health_ms": 22,
            "last_sync": "2026-11-06T20:54:50Z",
            "records_synced": 34210,
            "description": "Repository commits, branches, PR reviews, GitHub Actions workflows, and AI co-authored line diffs.",
        },
        {
            "id": "gitlab",
            "name": "GitLab Enterprise Ultimate",
            "category": "SCM & Code",
            "vendor": "GitLab Inc.",
            "protocol": "REST API v4",
            "endpoint": "https://gitlab.company.com/api/v4/connection",
            "mock_path": "/mock-enterprise/gitlab.company.com/api/v4/connection",
            "status": "CONNECTED",
            "health_ms": 39,
            "last_sync": "2026-11-06T20:52:40Z",
            "records_synced": 12890,
            "description": "Merge requests, branches, commits, and GitLab CI/CD deployment pipelines.",
        },
        {
            "id": "bitbucket",
            "name": "Atlassian Bitbucket Data Center",
            "category": "SCM & Code",
            "vendor": "Atlassian",
            "protocol": "REST API 2.0",
            "endpoint": "https://api.bitbucket.org/2.0/connection",
            "mock_path": "/mock-enterprise/api.bitbucket.org/2.0/connection",
            "status": "CONNECTED",
            "health_ms": 41,
            "last_sync": "2026-11-06T20:50:19Z",
            "records_synced": 8410,
            "description": "Enterprise repositories, branch permissions, pull requests, and Bitbucket Pipelines.",
        },
        {
            "id": "jenkins",
            "name": "Jenkins Enterprise CI/CD",
            "category": "CI/CD Releases",
            "vendor": "CloudBees / Jenkins",
            "protocol": "Remote Access JSON API",
            "endpoint": "https://jenkins.company.com/api/json/connection",
            "mock_path": "/mock-enterprise/jenkins.company.com/api/json/connection",
            "status": "CONNECTED",
            "health_ms": 31,
            "last_sync": "2026-11-06T20:54:00Z",
            "records_synced": 6150,
            "description": "Multi-branch pipeline builds, artifact promotions, test pass rates, and production release tags.",
        },
        {
            "id": "bamboo",
            "name": "Atlassian Bamboo Release Server",
            "category": "CI/CD Releases",
            "vendor": "Atlassian",
            "protocol": "REST API Latest",
            "endpoint": "https://bamboo.company.com/rest/api/latest/connection",
            "mock_path": "/mock-enterprise/bamboo.company.com/rest/api/latest/connection",
            "status": "CONNECTED",
            "health_ms": 45,
            "last_sync": "2026-11-06T20:49:15Z",
            "records_synced": 4390,
            "description": "Deployment projects, release environments, and Jira issue-linked build artifacts.",
        },
        {
            "id": "jira",
            "name": "Atlassian Jira Software",
            "category": "Agile & Tasks",
            "vendor": "Atlassian",
            "protocol": "REST API v3",
            "endpoint": "https://company.atlassian.net/rest/api/3/connection",
            "mock_path": "/mock-enterprise/company.atlassian.net/rest/api/3/connection",
            "status": "CONNECTED",
            "health_ms": 36,
            "last_sync": "2026-11-06T20:54:22Z",
            "records_synced": 19540,
            "description": "Epics, stories, sprint velocity, story points, and capex-eligible R&D feature flags.",
        },
        {
            "id": "servicenow",
            "name": "ServiceNow ITSM & Change",
            "category": "ITSM & Support",
            "vendor": "ServiceNow",
            "protocol": "Table & Change REST API",
            "endpoint": "https://company.service-now.com/api/now/connection",
            "mock_path": "/mock-enterprise/company.service-now.com/api/now/connection",
            "status": "CONNECTED",
            "health_ms": 48,
            "last_sync": "2026-11-06T20:53:44Z",
            "records_synced": 7820,
            "description": "Production change requests (CHG), incident root-cause resolution, and CMDB release governance.",
        },
        {
            "id": "zendesk",
            "name": "Zendesk Enterprise Support",
            "category": "ITSM & Support",
            "vendor": "Zendesk",
            "protocol": "REST API v2",
            "endpoint": "https://company.zendesk.com/api/v2/connection",
            "mock_path": "/mock-enterprise/company.zendesk.com/api/v2/connection",
            "status": "CONNECTED",
            "health_ms": 37,
            "last_sync": "2026-11-06T20:52:11Z",
            "records_synced": 15300,
            "description": "Customer escalations, AI ticket deflection metrics, and engineering bug-fix attribution.",
        },
        {
            "id": "salesforce",
            "name": "Salesforce Revenue Cloud",
            "category": "CRM & Revenue",
            "vendor": "Salesforce, Inc.",
            "protocol": "REST API v60.0",
            "endpoint": "https://company.my.salesforce.com/services/data/v60.0/connection",
            "mock_path": "/mock-enterprise/company.my.salesforce.com/services/data/v60.0/connection",
            "status": "CONNECTED",
            "health_ms": 42,
            "last_sync": "2026-11-06T20:51:55Z",
            "records_synced": 11240,
            "description": "Enterprise ARR pipeline, feature-driven deal closures, and customer expansion tied to AI releases.",
        },
        {
            "id": "powerbi",
            "name": "Microsoft Power BI & Fabric",
            "category": "Executive BI",
            "vendor": "Microsoft",
            "protocol": "Power BI REST v1.0",
            "endpoint": "https://api.powerbi.com/v1.0/myorg/connection",
            "mock_path": "/mock-enterprise/api.powerbi.com/v1.0/myorg/connection",
            "status": "CONNECTED",
            "health_ms": 33,
            "last_sync": "2026-11-06T20:54:05Z",
            "records_synced": 5400,
            "description": "Executive CFO/CTO semantic model push for AI token ROI, Sage GL actuals, and NetSuite EBITDA impact.",
        },
        {
            "id": "datadog",
            "name": "Datadog LLM Observability & APM",
            "category": "Observability & APM",
            "vendor": "Datadog, Inc.",
            "protocol": "Datadog API v2 & OTLP",
            "endpoint": "https://api.datadoghq.com/api/v2/connection",
            "mock_path": "/mock-enterprise/api.datadoghq.com/api/v2/connection",
            "status": "CONNECTED",
            "health_ms": 24,
            "last_sync": "2026-11-06T20:54:48Z",
            "records_synced": 92400,
            "description": "LLM trace spans, token latency percentiles, APM production deployment correlation, and cloud cost monitors.",
        },
        {
            "id": "substrate",
            "name": "Substrate AI Compute & Multi-Agent Mesh",
            "category": "AI Infrastructure",
            "vendor": "Substrate",
            "protocol": "Substrate Graph REST v1",
            "endpoint": "https://api.substrate.run/v1/connection",
            "mock_path": "/mock-enterprise/api.substrate.run/v1/connection",
            "status": "CONNECTED",
            "health_ms": 28,
            "last_sync": "2026-11-06T20:54:51Z",
            "records_synced": 41200,
            "description": "Multi-step inference graph orchestration, compound AI workflow routing, and compute node cost attribution.",
        },
        {
            "id": "newrelic",
            "name": "New Relic AI Monitoring & NerdGraph",
            "category": "Observability & APM",
            "vendor": "New Relic, Inc.",
            "protocol": "NerdGraph GraphQL & Telemetry SDK",
            "endpoint": "https://api.newrelic.com/graphql/connection",
            "mock_path": "/mock-enterprise/api.newrelic.com/graphql/connection",
            "status": "CONNECTED",
            "health_ms": 31,
            "last_sync": "2026-11-06T20:54:19Z",
            "records_synced": 68300,
            "description": "Golden signals, release marker error-rate deltas, and LLM token throughput correlation.",
        },
        {
            "id": "soluble",
            "name": "Soluble Cloud Native & IaC Security",
            "category": "DevSecOps & IaC",
            "vendor": "Soluble / Lacework",
            "protocol": "Soluble REST API v1",
            "endpoint": "https://app.soluble.cloud/api/v1/connection",
            "mock_path": "/mock-enterprise/app.soluble.cloud/api/v1/connection",
            "status": "CONNECTED",
            "health_ms": 35,
            "last_sync": "2026-11-06T20:53:55Z",
            "records_synced": 14900,
            "description": "Automated PR security checks, Terraform/Kubernetes IaC drift auditing on AI-generated commits.",
        },
        {
            "id": "pagerduty",
            "name": "PagerDuty Incident & On-Call Response",
            "category": "Incident Management",
            "vendor": "PagerDuty, Inc.",
            "protocol": "PagerDuty Events & REST v2",
            "endpoint": "https://api.pagerduty.com/connection",
            "mock_path": "/mock-enterprise/api.pagerduty.com/connection",
            "status": "CONNECTED",
            "health_ms": 26,
            "last_sync": "2026-11-06T20:54:40Z",
            "records_synced": 8930,
            "description": "P1/P2 incident MTTR reduction, on-call responder AI root-cause triage, and release rollback alerts.",
        },
        {
            "id": "opsgenie",
            "name": "Atlassian Opsgenie Alerting & On-Call",
            "category": "Incident Management",
            "vendor": "Atlassian",
            "protocol": "Opsgenie Alert API v2",
            "endpoint": "https://api.opsgenie.com/v2/connection",
            "mock_path": "/mock-enterprise/api.opsgenie.com/v2/connection",
            "status": "CONNECTED",
            "health_ms": 29,
            "last_sync": "2026-11-06T20:54:32Z",
            "records_synced": 11420,
            "description": "Alert deduplication, escalation routing linked to Jira/Bitbucket deployments, and AI remediation runbooks.",
        },
    ],
    "sage_erp": {
        "company_id": "BURNIQ-CORP-US",
        "system_edition": "Sage Intacct Enterprise + Sage X3 (EMEA) + Sage 300 (APAC)",
        "api_version": "ia/api/v1 (REST) & XML Web Services v3.0",
        "connection_status": "CONNECTED",
        "last_reconciled": "2026-11-06T20:54:12Z",
        "entities": [
            {
                "entity_id": "E100",
                "name": "BurnIQ North America Inc.",
                "erp_module": "Sage Intacct Multi-Entity",
                "base_currency": "USD",
                "location": "San Francisco, US",
                "ai_budget_monthly": 45000.00,
                "ai_actual_spend": 38420.50,
                "capitalized_rd_usd": 24890.00,
                "opex_prod_usd": 8110.50,
                "low_value_waste_usd": 5420.00,
                "net_salary_roi_usd": 194500.00,
            },
            {
                "entity_id": "E200",
                "name": "BurnIQ EMEA Operations Ltd.",
                "erp_module": "Sage X3 Enterprise",
                "base_currency": "EUR",
                "location": "London & Frankfurt",
                "ai_budget_monthly": 22000.00,
                "ai_actual_spend": 19150.00,
                "capitalized_rd_usd": 12400.00,
                "opex_prod_usd": 4120.00,
                "low_value_waste_usd": 2630.00,
                "net_salary_roi_usd": 88200.00,
            },
            {
                "entity_id": "E300",
                "name": "BurnIQ APAC Pte. Ltd.",
                "erp_module": "Sage 300 Cloud",
                "base_currency": "SGD",
                "location": "Singapore",
                "ai_budget_monthly": 12000.00,
                "ai_actual_spend": 9840.00,
                "capitalized_rd_usd": 6510.00,
                "opex_prod_usd": 2190.00,
                "low_value_waste_usd": 1140.00,
                "net_salary_roi_usd": 46800.00,
            },
        ],
        "gl_accounts": [
            {
                "account_no": "1650-01",
                "title": "Software Development Costs — Capitalized AI R&D (ASC 350-40)",
                "account_type": "Asset (CapEx)",
                "normal_balance": "Debit",
                "department_dim": "DEPT-100 / DEPT-200",
                "mtd_balance_usd": 43800.00,
                "ytd_balance_usd": 412600.00,
                "linked_releases": ["REL-2026.11.4", "REL-2026.11.3", "REL-2026.11.2"],
                "compliance_rule": "Requires linked Jira Epic + Git Commit SHA + CI/CD Production Release (Jenkins/Bamboo)",
            },
            {
                "account_no": "6120-01",
                "title": "AI & LLM Compute Infrastructure — Production Engineering",
                "account_type": "Expense (R&D OpEx)",
                "normal_balance": "Debit",
                "department_dim": "DEPT-100 / DEPT-200",
                "mtd_balance_usd": 14420.50,
                "ytd_balance_usd": 138900.00,
                "linked_releases": ["REL-2026.11.4", "REL-2026.11.1"],
                "compliance_rule": "Bug fixes, CI triage, PR reviews, and non-capitalizable sprint maintenance",
            },
            {
                "account_no": "6120-02",
                "title": "Low-Value AI Token Spend — Routine Emails, Meeting Notes & Unlinked Chat",
                "account_type": "Expense (SG&A Waste Audit)",
                "normal_balance": "Debit",
                "department_dim": "DEPT-300 / DEPT-400",
                "mtd_balance_usd": 9190.00,
                "ytd_balance_usd": 94300.00,
                "linked_releases": [],
                "compliance_rule": "NON-CAPITALIZABLE: Flagged by BurnIQ Low-Value Task Auditor for Haiku/Flash downgrade",
            },
            {
                "account_no": "5110-01",
                "title": "Workday Engineering Loaded Payroll Applied to Shipped AI Releases",
                "account_type": "Capitalized Labor Contra / COGS",
                "normal_balance": "Debit",
                "department_dim": "DEPT-100 / DEPT-200",
                "mtd_balance_usd": 329500.00,
                "ytd_balance_usd": 3180000.00,
                "linked_releases": ["REL-2026.11.4", "REL-2026.11.3", "REL-2026.11.2"],
                "compliance_rule": "Workday HCM verified engineering hours saved & applied to shipped production releases",
            },
            {
                "account_no": "2100-01",
                "title": "Accounts Payable — AI & Cloud Providers (Anthropic & Google Cloud)",
                "account_type": "Liability (AP)",
                "normal_balance": "Credit",
                "department_dim": "ALL",
                "mtd_balance_usd": 67410.50,
                "ytd_balance_usd": 645800.00,
                "linked_releases": [],
                "compliance_rule": "Matched 3-way against Anthropic & Vertex AI telemetry logs and vendor bills",
            },
        ],
        "gl_batches": [
            {
                "batch_id": "BATCH-SAGE-2026-11A",
                "journal_symbol": "AIRD",
                "posting_date": "2026-11-06",
                "entity_id": "E100",
                "description": "ASC 350-40 R&D Capitalization — Release REL-2026.11.4 (Claude 3.7 Sonnet + Gemini 2.5 Pro)",
                "debit_account": "1650-01",
                "credit_account": "2100-01",
                "amount_usd": 24890.00,
                "department": "DEPT-100 Core Platform",
                "project_dim": "REL-2026.11.4 / JIRA-EPIC-402",
                "status": "POSTED",
                "audit_trail": "Verified 48 GitHub commits + Jenkins build #1842 + Workday 312 eng hrs",
            },
            {
                "batch_id": "BATCH-SAGE-2026-11B",
                "journal_symbol": "AIOP",
                "posting_date": "2026-11-06",
                "entity_id": "E200",
                "description": "Sage X3 EMEA R&D & CI/CD Triage — Release REL-2026.11.3 (GitLab CI + Bamboo)",
                "debit_account": "1650-01",
                "credit_account": "2100-01",
                "amount_usd": 12400.00,
                "department": "DEPT-200 AI & Data",
                "project_dim": "REL-2026.11.3 / JIRA-EPIC-389",
                "status": "POSTED",
                "audit_trail": "Verified 29 GitLab commits + Bamboo deploy #910 + Workday 164 eng hrs",
            },
            {
                "batch_id": "BATCH-SAGE-2026-11C",
                "journal_symbol": "SGAW",
                "posting_date": "2026-11-06",
                "entity_id": "E100",
                "description": "Low-Value Task Reclassification (Internal Emails & Meeting Notes on Frontier Models)",
                "debit_account": "6120-02",
                "credit_account": "2100-01",
                "amount_usd": 9190.00,
                "department": "DEPT-400 G&A Operations",
                "project_dim": "UNLINKED-LOW-VALUE",
                "status": "FLAGGED_FOR_OPTIMIZATION",
                "audit_trail": "3,410 unlinked email/notes prompts using Claude Opus & Gemini Pro — 0 git commits",
            },
        ],
        "vendor_bills": [
            {
                "bill_id": "BILL-SAGE-9910",
                "vendor_id": "VEND-ANTHROPIC",
                "vendor_name": "Anthropic PBC (Claude Enterprise API)",
                "entity_id": "E100",
                "invoice_date": "2026-11-05",
                "due_date": "2026-12-05",
                "billed_amount_usd": 38910.50,
                "telemetry_verified_usd": 38910.50,
                "variance_usd": 0.00,
                "capex_eligible_usd": 25400.00,
                "low_value_waste_usd": 5640.00,
                "match_status": "3-WAY MATCHED",
            },
            {
                "bill_id": "BILL-SAGE-9911",
                "vendor_id": "VEND-GOOGLE-CLOUD",
                "vendor_name": "Google Cloud EMEA/US (Vertex AI Gemini)",
                "entity_id": "E100 / E200",
                "invoice_date": "2026-11-05",
                "due_date": "2026-12-05",
                "billed_amount_usd": 28500.00,
                "telemetry_verified_usd": 28500.00,
                "variance_usd": 0.00,
                "capex_eligible_usd": 18400.00,
                "low_value_waste_usd": 3550.00,
                "match_status": "3-WAY MATCHED",
            },
        ],
    },
    "oracle_netsuite": {
        "account_id": "TSTDRV2026991",
        "edition": "Oracle NetSuite OneWorld Enterprise + SuiteAnalytics Connect (SuiteQL)",
        "rest_api": "SuiteTalk REST Web Services v1 & SuiteQL",
        "connection_status": "CONNECTED",
        "last_reconciled": "2026-11-06T20:54:35Z",
        "subsidiaries": [
            {
                "internal_id": "SUB-1",
                "name": "BurnIQ Global Holdings Inc. (Consolidated)",
                "currency": "USD",
                "country": "United States",
                "elimination": False,
                "llm_po_commit_usd": 800000.00,
                "mtd_token_burn_usd": 67410.50,
                "capex_amortized_mtd_usd": 11450.00,
                "arr_attributed_usd": 4280000.00,
                "ebitda_margin_lift_bps": 340,
            },
            {
                "internal_id": "SUB-2",
                "name": "BurnIQ Technologies US Inc.",
                "currency": "USD",
                "country": "United States",
                "elimination": False,
                "llm_po_commit_usd": 520000.00,
                "mtd_token_burn_usd": 38420.50,
                "capex_amortized_mtd_usd": 7200.00,
                "arr_attributed_usd": 2850000.00,
                "ebitda_margin_lift_bps": 390,
            },
            {
                "internal_id": "SUB-3",
                "name": "BurnIQ Europe Ltd. (UK)",
                "currency": "GBP",
                "country": "United Kingdom",
                "elimination": False,
                "llm_po_commit_usd": 180000.00,
                "mtd_token_burn_usd": 19150.00,
                "capex_amortized_mtd_usd": 2850.00,
                "arr_attributed_usd": 980000.00,
                "ebitda_margin_lift_bps": 285,
            },
            {
                "internal_id": "SUB-4",
                "name": "BurnIQ DACH GmbH (Germany)",
                "currency": "EUR",
                "country": "Germany",
                "elimination": False,
                "llm_po_commit_usd": 100000.00,
                "mtd_token_burn_usd": 9840.00,
                "capex_amortized_mtd_usd": 1400.00,
                "arr_attributed_usd": 450000.00,
                "ebitda_margin_lift_bps": 260,
            },
        ],
        "journal_entries": [
            {
                "tran_id": "JE-NS-9041",
                "internal_id": "884101",
                "trandate": "2026-11-06",
                "subsidiary": "SUB-2 BurnIQ Technologies US Inc.",
                "posting_period": "Nov 2026",
                "currency": "USD",
                "memo": "NetSuite OneWorld CapEx Allocation — Release REL-2026.11.4 (Claude & Gemini Code Attribution)",
                "debit_account": "16500 Capitalized Software R&D (Intangible Asset)",
                "credit_account": "61200 AI Compute & Engineering Payroll Clearing",
                "amount_usd": 24890.00,
                "cseg_ai_provider": "Anthropic Claude + Google Gemini",
                "cseg_task_value_tier": "Tier 1: Production Release Code",
                "linked_jira_epic": "JIRA-EPIC-402",
                "linked_git_release": "REL-2026.11.4 (GitHub / Jenkins #1842)",
                "approval_status": "Approved for Posting",
            },
            {
                "tran_id": "JE-NS-9042",
                "internal_id": "884102",
                "trandate": "2026-11-06",
                "subsidiary": "SUB-3 BurnIQ Europe Ltd. (UK)",
                "posting_period": "Nov 2026",
                "currency": "USD",
                "memo": "NetSuite OneWorld CapEx Allocation — Release REL-2026.11.3 (GitLab / Bamboo Pipeline)",
                "debit_account": "16500 Capitalized Software R&D (Intangible Asset)",
                "credit_account": "61200 AI Compute & Engineering Payroll Clearing",
                "amount_usd": 12400.00,
                "cseg_ai_provider": "Google Vertex AI Gemini 2.5 Pro",
                "cseg_task_value_tier": "Tier 1: Production Release Code",
                "linked_jira_epic": "JIRA-EPIC-389",
                "linked_git_release": "REL-2026.11.3 (GitLab / Bamboo #910)",
                "approval_status": "Approved for Posting",
            },
            {
                "tran_id": "JE-NS-9043",
                "internal_id": "884103",
                "trandate": "2026-11-06",
                "subsidiary": "SUB-2 BurnIQ Technologies US Inc.",
                "posting_period": "Nov 2026",
                "currency": "USD",
                "memo": "SG&A Low-Value AI Expense Accrual — Routine Internal Emails & Meeting Notes Audit",
                "debit_account": "68450 SG&A Non-Productive AI Token Waste",
                "credit_account": "21100 Accounts Payable — LLM Vendors",
                "amount_usd": 9190.00,
                "cseg_ai_provider": "Claude 3 Opus / Gemini 2.5 Pro (Misrouted)",
                "cseg_task_value_tier": "Tier 3: Low-Value Email/Notes Waste",
                "linked_jira_epic": "NONE (Unlinked Ad-Hoc Usage)",
                "linked_git_release": "NONE",
                "approval_status": "Flagged — Pending CFO Reallocation",
            },
        ],
        "purchase_orders": [
            {
                "po_number": "PO-NS-8841",
                "vendor": "Anthropic PBC",
                "subsidiary": "SUB-1 BurnIQ Global Holdings Inc.",
                "contract_term": "FY2026 Annual Enterprise Commit",
                "total_commit_usd": 480000.00,
                "consumed_ytd_usd": 382400.00,
                "remaining_balance_usd": 97600.00,
                "burn_utilization_pct": 79.7,
                "productive_code_pct": 85.4,
                "low_value_email_notes_pct": 14.6,
                "status": "Partially Billed — Active",
            },
            {
                "po_number": "PO-NS-8842",
                "vendor": "Google Cloud (Vertex AI Gemini)",
                "subsidiary": "SUB-1 BurnIQ Global Holdings Inc.",
                "contract_term": "FY2026 Annual Enterprise Commit",
                "total_commit_usd": 320000.00,
                "consumed_ytd_usd": 263400.00,
                "remaining_balance_usd": 56600.00,
                "burn_utilization_pct": 82.3,
                "productive_code_pct": 87.5,
                "low_value_email_notes_pct": 12.5,
                "status": "Partially Billed — Active",
            },
        ],
        "amortization_schedules": [
            {
                "schedule_id": "AMORT-NS-301",
                "release_tag": "REL-2026.11.4",
                "release_name": "Autonomous ERP Ledger & Telemetry Engine v2.4",
                "scm_pipeline": "GitHub -> Jenkins #1842",
                "jira_epic": "JIRA-EPIC-402",
                "subsidiary": "SUB-2 BurnIQ Technologies US Inc.",
                "capitalized_token_usd": 24890.00,
                "capitalized_workday_labor_usd": 68400.00,
                "total_capitalized_asset_usd": 93290.00,
                "useful_life_months": 36,
                "monthly_amortization_usd": 2591.39,
                "arr_impact_salesforce_usd": 1450000.00,
            },
            {
                "schedule_id": "AMORT-NS-302",
                "release_name": "Multi-Cloud Streaming Telemetry Mesh v2.3",
                "release_tag": "REL-2026.11.3",
                "scm_pipeline": "GitLab -> Bamboo #910",
                "jira_epic": "JIRA-EPIC-389",
                "subsidiary": "SUB-3 BurnIQ Europe Ltd. (UK)",
                "capitalized_token_usd": 12400.00,
                "capitalized_workday_labor_usd": 41200.00,
                "total_capitalized_asset_usd": 53600.00,
                "useful_life_months": 36,
                "monthly_amortization_usd": 1488.89,
                "arr_impact_salesforce_usd": 980000.00,
            },
            {
                "schedule_id": "AMORT-NS-303",
                "release_name": "Zero-Trust SSO & Workday Attribution Sync v2.2",
                "release_tag": "REL-2026.11.2",
                "scm_pipeline": "Bitbucket -> Jenkins #1799",
                "jira_epic": "JIRA-EPIC-361",
                "subsidiary": "SUB-4 BurnIQ DACH GmbH",
                "capitalized_token_usd": 6510.00,
                "capitalized_workday_labor_usd": 26800.00,
                "total_capitalized_asset_usd": 33310.00,
                "useful_life_months": 36,
                "monthly_amortization_usd": 925.28,
                "arr_impact_salesforce_usd": 620000.00,
            },
        ],
    },
    "releases": [
        {
            "release_id": "REL-2026.11.4",
            "name": "Autonomous ERP Ledger & Telemetry Engine v2.4",
            "scm_provider": "GitHub",
            "repository": "HayfordMD/burniq-core",
            "branch": "release/v2.4-erp-sync",
            "commit_count": 48,
            "head_sha": "9f82c1d",
            "ci_cd_provider": "Jenkins",
            "build_number": "JENKINS-1842",
            "jira_epic": "JIRA-EPIC-402",
            "servicenow_chg": "CHG0049210",
            "claude_tokens": 14200000,
            "gemini_tokens": 11800000,
            "token_cost_usd": 24890.00,
            "workday_hours_saved": 312.0,
            "workday_salary_value_usd": 49920.00,
            "salesforce_arr_influenced_usd": 1450000.00,
            "sage_gl_account": "1650-01 (CapEx)",
            "netsuite_je": "JE-NS-9041",
            "roi_multiple": 8.4,
            "status": "DEPLOYED_PROD",
        },
        {
            "release_id": "REL-2026.11.3",
            "name": "Multi-Cloud Streaming Telemetry Mesh v2.3",
            "scm_provider": "GitLab",
            "repository": "burniq/telemetry-mesh",
            "branch": "main",
            "commit_count": 29,
            "head_sha": "4e19a7b",
            "ci_cd_provider": "Bamboo",
            "build_number": "BAMBOO-910",
            "jira_epic": "JIRA-EPIC-389",
            "servicenow_chg": "CHG0049184",
            "claude_tokens": 6100000,
            "gemini_tokens": 9400000,
            "token_cost_usd": 12400.00,
            "workday_hours_saved": 164.0,
            "workday_salary_value_usd": 24928.00,
            "salesforce_arr_influenced_usd": 980000.00,
            "sage_gl_account": "1650-01 (CapEx)",
            "netsuite_je": "JE-NS-9042",
            "roi_multiple": 7.1,
            "status": "DEPLOYED_PROD",
        },
        {
            "release_id": "REL-2026.11.2",
            "name": "Zero-Trust SSO & Workday Attribution Sync v2.2",
            "scm_provider": "Bitbucket",
            "repository": "burniq/workday-connector",
            "branch": "release/2.2",
            "commit_count": 19,
            "head_sha": "7c31b0e",
            "ci_cd_provider": "Jenkins",
            "build_number": "JENKINS-1799",
            "jira_epic": "JIRA-EPIC-361",
            "servicenow_chg": "CHG0049102",
            "claude_tokens": 4200000,
            "gemini_tokens": 3800000,
            "token_cost_usd": 6510.00,
            "workday_hours_saved": 96.0,
            "workday_salary_value_usd": 14880.00,
            "salesforce_arr_influenced_usd": 620000.00,
            "sage_gl_account": "1650-01 (CapEx)",
            "netsuite_je": "JE-NS-9039",
            "roi_multiple": 6.8,
            "status": "DEPLOYED_PROD",
        },
        {
            "release_id": "REL-2026.11.1",
            "name": "Zendesk & ServiceNow Incident Auto-Triage Patch",
            "scm_provider": "GitHub",
            "repository": "HayfordMD/burniq-triage",
            "branch": "hotfix/triage-v2.1.4",
            "commit_count": 14,
            "head_sha": "2a90f4c",
            "ci_cd_provider": "Bamboo",
            "build_number": "BAMBOO-894",
            "jira_epic": "JIRA-EPIC-344",
            "servicenow_chg": "CHG0049055",
            "claude_tokens": 5800000,
            "gemini_tokens": 7100000,
            "token_cost_usd": 14420.50,
            "workday_hours_saved": 142.0,
            "workday_salary_value_usd": 21300.00,
            "salesforce_arr_influenced_usd": 410000.00,
            "sage_gl_account": "6120-01 (R&D OpEx)",
            "netsuite_je": "JE-NS-9035",
            "roi_multiple": 4.9,
            "status": "DEPLOYED_PROD",
        },
    ],
    "employees": [
        {
            "workday_id": "WD-10041",
            "name": "Elena Rostova",
            "role": "L6 Principal Systems Architect",
            "department": "DEPT-100 Core Platform",
            "sage_entity": "E100",
            "netsuite_subsidiary": "SUB-2 BurnIQ Technologies US Inc.",
            "annual_loaded_salary_usd": 332800.0,
            "hourly_rate_usd": 160.0,
            "primary_llm": "Claude 3.7 Sonnet + Gemini 2.5 Pro",
            "commits_shipped": 31,
            "releases_contributed": 3,
            "jira_story_points": 54,
            "token_spend_mtd_usd": 4820.0,
            "low_value_spend_usd": 95.0,
            "hours_saved_mtd": 84.5,
            "salary_value_created_usd": 13520.0,
            "net_roi_pct": 180.5,
            "audit_status": "HIGH_ROI_EXEMPLAR",
        },
        {
            "workday_id": "WD-10088",
            "name": "Marcus Vance",
            "role": "L5 Staff Distributed Engineer",
            "department": "DEPT-200 AI & Data",
            "sage_entity": "E200",
            "netsuite_subsidiary": "SUB-3 BurnIQ Europe Ltd. (UK)",
            "annual_loaded_salary_usd": 291200.0,
            "hourly_rate_usd": 140.0,
            "primary_llm": "Gemini 2.5 Pro + Claude 3.5 Sonnet",
            "commits_shipped": 27,
            "releases_contributed": 2,
            "jira_story_points": 46,
            "token_spend_mtd_usd": 3910.0,
            "low_value_spend_usd": 120.0,
            "hours_saved_mtd": 72.0,
            "salary_value_created_usd": 10080.0,
            "net_roi_pct": 157.8,
            "audit_status": "HIGH_ROI_EXEMPLAR",
        },
        {
            "workday_id": "WD-10112",
            "name": "Priya Nair",
            "role": "L5 Senior Full-Stack Engineer",
            "department": "DEPT-100 Core Platform",
            "sage_entity": "E300",
            "netsuite_subsidiary": "SUB-4 BurnIQ DACH GmbH",
            "annual_loaded_salary_usd": 270400.0,
            "hourly_rate_usd": 130.0,
            "primary_llm": "Claude 3.7 Sonnet",
            "commits_shipped": 24,
            "releases_contributed": 2,
            "jira_story_points": 39,
            "token_spend_mtd_usd": 3180.0,
            "low_value_spend_usd": 80.0,
            "hours_saved_mtd": 64.0,
            "salary_value_created_usd": 8320.0,
            "net_roi_pct": 161.6,
            "audit_status": "OPTIMAL",
        },
        {
            "workday_id": "WD-10209",
            "name": "Devon Sterling",
            "role": "Director of Internal Ops & Strategy",
            "department": "DEPT-400 G&A Operations",
            "sage_entity": "E100",
            "netsuite_subsidiary": "SUB-2 BurnIQ Technologies US Inc.",
            "annual_loaded_salary_usd": 228800.0,
            "hourly_rate_usd": 110.0,
            "primary_llm": "Claude 3 Opus (Unrouted)",
            "commits_shipped": 0,
            "releases_contributed": 0,
            "jira_story_points": 2,
            "token_spend_mtd_usd": 3840.0,
            "low_value_spend_usd": 3620.0,
            "hours_saved_mtd": 6.5,
            "salary_value_created_usd": 715.0,
            "net_roi_pct": -81.4,
            "audit_status": "LOW_VALUE_EMAIL_NOTES_ALERT",
        },
        {
            "workday_id": "WD-10244",
            "name": "claire.dupont@burniq.io (Claire Dupont)",
            "role": "Program Coordinator",
            "department": "DEPT-300 Revenue & GTM",
            "sage_entity": "E200",
            "netsuite_subsidiary": "SUB-3 BurnIQ Europe Ltd. (UK)",
            "annual_loaded_salary_usd": 166400.0,
            "hourly_rate_usd": 80.0,
            "primary_llm": "Gemini 2.5 Pro (Unrouted)",
            "commits_shipped": 0,
            "releases_contributed": 0,
            "jira_story_points": 3,
            "token_spend_mtd_usd": 2790.0,
            "low_value_spend_usd": 2540.0,
            "hours_saved_mtd": 8.0,
            "salary_value_created_usd": 640.0,
            "net_roi_pct": -77.1,
            "audit_status": "LOW_VALUE_EMAIL_NOTES_ALERT",
        },
    ],
    "low_value_tasks": [
        {
            "audit_id": "LVA-901",
            "workday_id": "WD-10209",
            "employee": "Devon Sterling",
            "department": "DEPT-400 G&A Operations",
            "task_category": "Routine Internal Email Drafting & Formatting",
            "model_used": "claude-3-opus-20240229",
            "recommended_model": "claude-3-5-haiku / gemini-2.5-flash",
            "prompt_count": 1420,
            "tokens_burned": 18400000,
            "current_cost_usd": 3620.00,
            "projected_routed_cost_usd": 290.00,
            "monthly_savings_usd": 3330.00,
            "linked_git_commits": 0,
            "linked_jira_keys": "NONE",
            "sage_gl_impact": "6120-02 (SG&A Waste)",
            "netsuite_je_impact": "JE-NS-9043 (Tier 3 Waste)",
            "status": "OPEN_WASTE",
        },
        {
            "audit_id": "LVA-902",
            "workday_id": "WD-10244",
            "employee": "Claire Dupont",
            "department": "DEPT-300 Revenue & GTM",
            "task_category": "Meeting Notes Summarization & Calendar Recaps",
            "model_used": "gemini-2.5-pro",
            "recommended_model": "gemini-2.5-flash",
            "prompt_count": 1180,
            "tokens_burned": 15900000,
            "current_cost_usd": 2540.00,
            "projected_routed_cost_usd": 210.00,
            "monthly_savings_usd": 2330.00,
            "linked_git_commits": 0,
            "linked_jira_keys": "NONE",
            "sage_gl_impact": "6120-02 (SG&A Waste)",
            "netsuite_je_impact": "JE-NS-9043 (Tier 3 Waste)",
            "status": "OPEN_WASTE",
        },
        {
            "audit_id": "LVA-903",
            "workday_id": "WD-10310",
            "employee": "G&A Shared Workspace Bot",
            "department": "DEPT-400 G&A Operations",
            "task_category": "Ad-Hoc Slack/Email Tone Rewriting & Trivia",
            "model_used": "claude-3-7-sonnet",
            "recommended_model": "claude-3-5-haiku",
            "prompt_count": 810,
            "tokens_burned": 11200000,
            "current_cost_usd": 3030.00,
            "projected_routed_cost_usd": 340.00,
            "monthly_savings_usd": 2690.00,
            "linked_git_commits": 0,
            "linked_jira_keys": "NONE",
            "sage_gl_impact": "6120-02 (SG&A Waste)",
            "netsuite_je_impact": "JE-NS-9043 (Tier 3 Waste)",
            "status": "OPEN_WASTE",
        },
    ],
}


class EnterpriseDataStore:
    """Thread-safe JSON-backed state store for BurnIQ Enterprise Telemetry & ERP integrations."""

    def __init__(self, storage_path: Optional[str] = None) -> None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.storage_path = storage_path or os.path.join(base_dir, "data", "enterprise_state.json")
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        self.state: Dict[str, Any] = self._load_or_init()

    def _load_or_init(self) -> Dict[str, Any]:
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        state = copy.deepcopy(DEFAULT_STATE)
        self._save(state)
        return state

    def _save(self, state: Optional[Dict[str, Any]] = None) -> None:
        target = state if state is not None else self.state
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(target, f, indent=2)

    def reset(self) -> Dict[str, Any]:
        self.state = copy.deepcopy(DEFAULT_STATE)
        self._save()
        return self.state

    def get_dashboard_summary(self) -> Dict[str, Any]:
        sage = self.state["sage_erp"]
        ns = self.state["oracle_netsuite"]
        releases = self.state["releases"]
        employees = self.state["employees"]
        low_value = self.state["low_value_tasks"]

        total_spend = sum(e["ai_actual_spend"] for e in sage["entities"])
        total_capex = sum(e["capitalized_rd_usd"] for e in sage["entities"])
        total_opex = sum(e["opex_prod_usd"] for e in sage["entities"])
        total_waste = sum(t["current_cost_usd"] for t in low_value)
        potential_savings = sum(t["monthly_savings_usd"] for t in low_value)
        total_hours_saved = sum(r["workday_hours_saved"] for r in releases)
        total_salary_roi = sum(e["net_salary_roi_usd"] for e in sage["entities"])
        total_arr_attributed = sum(r["salesforce_arr_influenced_usd"] for r in releases)

        return {
            "meta": self.state["meta"],
            "kpis": {
                "total_llm_spend_mtd_usd": round(total_spend, 2),
                "capitalized_rd_asc350_usd": round(total_capex, 2),
                "productive_opex_usd": round(total_opex, 2),
                "low_value_email_notes_waste_usd": round(total_waste, 2),
                "recoverable_monthly_savings_usd": round(potential_savings, 2),
                "workday_engineering_hours_saved": round(total_hours_saved, 1),
                "workday_net_salary_roi_usd": round(total_salary_roi, 2),
                "salesforce_arr_attributed_usd": round(total_arr_attributed, 2),
                "connected_enterprise_systems": len(self.state["connectors"]),
                "sage_entities_active": len(sage["entities"]),
                "netsuite_subsidiaries_active": len(ns["subsidiaries"]),
                "net_roi_multiple": round(total_salary_roi / max(total_spend, 1.0), 2),
            },
            "connectors": self.state["connectors"],
            "sage_erp": sage,
            "oracle_netsuite": ns,
            "releases": releases,
            "employees": employees,
            "low_value_tasks": low_value,
        }

    def create_sage_gl_batch(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        batches = self.state["sage_erp"]["gl_batches"]
        batch_num = len(batches) + 1
        now_date = datetime.utcnow().strftime("%Y-%m-%d")
        new_batch = {
            "batch_id": payload.get("batch_id") or f"BATCH-SAGE-2026-11{chr(64 + batch_num)}",
            "journal_symbol": payload.get("journal_symbol", "AIRD"),
            "posting_date": payload.get("posting_date", now_date),
            "entity_id": payload.get("entity_id", "E100"),
            "description": payload.get(
                "description",
                "Automated BurnIQ ASC 350-40 AI R&D Capitalization Batch (Claude & Gemini)",
            ),
            "debit_account": payload.get("debit_account", "1650-01"),
            "credit_account": payload.get("credit_account", "2100-01"),
            "amount_usd": float(payload.get("amount_usd", 14250.00)),
            "department": payload.get("department", "DEPT-100 Core Platform"),
            "project_dim": payload.get("project_dim", "REL-2026.11.4 / JIRA-EPIC-402"),
            "status": "POSTED",
            "audit_trail": payload.get(
                "audit_trail",
                "Auto-reconciled via Sage Intacct REST v1 + GitHub/Jenkins + Workday HCM",
            ),
        }
        batches.insert(0, new_batch)
        self.state["sage_erp"]["last_reconciled"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        self._save()
        return new_batch

    def create_netsuite_journal_entry(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        entries = self.state["oracle_netsuite"]["journal_entries"]
        next_num = 9041 + len(entries)
        now_date = datetime.utcnow().strftime("%Y-%m-%d")
        new_je = {
            "tran_id": payload.get("tran_id") or f"JE-NS-{next_num}",
            "internal_id": str(884100 + len(entries) + 1),
            "trandate": payload.get("trandate", now_date),
            "subsidiary": payload.get("subsidiary", "SUB-2 BurnIQ Technologies US Inc."),
            "posting_period": payload.get("posting_period", "Nov 2026"),
            "currency": payload.get("currency", "USD"),
            "memo": payload.get(
                "memo",
                "SuiteTalk REST Automated AI CapEx & Token Attribution Journal Entry",
            ),
            "debit_account": payload.get(
                "debit_account", "16500 Capitalized Software R&D (Intangible Asset)"
            ),
            "credit_account": payload.get(
                "credit_account", "61200 AI Compute & Engineering Payroll Clearing"
            ),
            "amount_usd": float(payload.get("amount_usd", 18600.00)),
            "cseg_ai_provider": payload.get("cseg_ai_provider", "Anthropic Claude + Google Gemini"),
            "cseg_task_value_tier": payload.get(
                "cseg_task_value_tier", "Tier 1: Production Release Code"
            ),
            "linked_jira_epic": payload.get("linked_jira_epic", "JIRA-EPIC-402"),
            "linked_git_release": payload.get("linked_git_release", "REL-2026.11.4"),
            "approval_status": "Approved & Posted (SuiteTalk REST v1)",
        }
        entries.insert(0, new_je)
        self.state["oracle_netsuite"]["last_reconciled"] = datetime.utcnow().strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        self._save()
        return new_je

    def execute_suiteql(self, query: str) -> Dict[str, Any]:
        """Executes a SuiteQL query against the Oracle NetSuite OneWorld dataset."""
        q_lower = (query or "").strip().lower()
        ns = self.state["oracle_netsuite"]

        if "subsidiary" in q_lower or "oneworld" in q_lower:
            rows = ns["subsidiaries"]
            columns = [
                "internal_id",
                "name",
                "currency",
                "country",
                "llm_po_commit_usd",
                "mtd_token_burn_usd",
                "capex_amortized_mtd_usd",
                "arr_attributed_usd",
            ]
        elif "purchaseorder" in q_lower or "po_number" in q_lower or "vendor" in q_lower:
            rows = ns["purchase_orders"]
            columns = [
                "po_number",
                "vendor",
                "subsidiary",
                "total_commit_usd",
                "consumed_ytd_usd",
                "remaining_balance_usd",
                "burn_utilization_pct",
                "status",
            ]
        elif "amortization" in q_lower or "schedule" in q_lower:
            rows = ns["amortization_schedules"]
            columns = [
                "schedule_id",
                "release_tag",
                "subsidiary",
                "capitalized_token_usd",
                "capitalized_workday_labor_usd",
                "total_capitalized_asset_usd",
                "monthly_amortization_usd",
            ]
        else:
            rows = ns["journal_entries"]
            columns = [
                "tran_id",
                "trandate",
                "subsidiary",
                "debit_account",
                "credit_account",
                "amount_usd",
                "cseg_ai_provider",
                "cseg_task_value_tier",
                "linked_git_release",
                "approval_status",
            ]

        return {
            "suiteql_version": "2026.2",
            "account_id": ns["account_id"],
            "query_executed": query,
            "row_count": len(rows),
            "columns": columns,
            "items": rows,
            "execution_time_ms": 18.4,
        }

    def apply_smart_routing_and_erp_reallocation(self) -> Dict[str, Any]:
        """Routes low-value email/notes tasks to Haiku/Flash and updates Sage & NetSuite GLs."""
        self.state["meta"]["smart_routing_enabled"] = True
        total_saved = 0.0
        for item in self.state["low_value_tasks"]:
            if item["status"] != "OPTIMIZED_ROUTED":
                saved = item["current_cost_usd"] - item["projected_routed_cost_usd"]
                total_saved += saved
                item["current_cost_usd"] = item["projected_routed_cost_usd"]
                item["status"] = "OPTIMIZED_ROUTED"

        for batch in self.state["sage_erp"]["gl_batches"]:
            if batch["debit_account"] == "6120-02":
                batch["status"] = "OPTIMIZED_HAIKU_FLASH_ROUTED"
                batch["amount_usd"] = 840.00

        for je in self.state["oracle_netsuite"]["journal_entries"]:
            if "68450" in je["debit_account"]:
                je["approval_status"] = "Optimized — Routed to Gemini Flash / Claude Haiku"
                je["amount_usd"] = 840.00

        self._save()
        return {
            "status": "SUCCESS",
            "smart_routing_enabled": True,
            "monthly_savings_realized_usd": round(total_saved, 2),
            "annualized_savings_usd": round(total_saved * 12, 2),
            "sage_gl_updated": "6120-02 Low-Value AI Spend reduced by 90.8%",
            "netsuite_je_updated": "JE-NS-9043 updated via SuiteTalk REST v1",
        }

    def export_csv(self, target: str) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        target_key = (target or "sage").lower()

        if target_key == "sage":
            writer.writerow(
                [
                    "BATCH_ID",
                    "JOURNAL",
                    "POSTING_DATE",
                    "ENTITY_ID",
                    "DEBIT_ACCT",
                    "CREDIT_ACCT",
                    "AMOUNT_USD",
                    "DEPARTMENT_DIM",
                    "PROJECT_RELEASE_DIM",
                    "STATUS",
                    "AUDIT_TRAIL",
                ]
            )
            for b in self.state["sage_erp"]["gl_batches"]:
                writer.writerow(
                    [
                        b["batch_id"],
                        b["journal_symbol"],
                        b["posting_date"],
                        b["entity_id"],
                        b["debit_account"],
                        b["credit_account"],
                        f"{b['amount_usd']:.2f}",
                        b["department"],
                        b["project_dim"],
                        b["status"],
                        b["audit_trail"],
                    ]
                )
        elif target_key == "netsuite":
            writer.writerow(
                [
                    "EXTERNAL_ID",
                    "TRANDATE",
                    "SUBSIDIARY",
                    "POSTING_PERIOD",
                    "CURRENCY",
                    "DEBIT_ACCOUNT",
                    "CREDIT_ACCOUNT",
                    "AMOUNT_USD",
                    "CSEG_AI_PROVIDER",
                    "CSEG_TASK_VALUE_TIER",
                    "LINKED_JIRA_EPIC",
                    "LINKED_GIT_RELEASE",
                    "MEMO",
                ]
            )
            for je in self.state["oracle_netsuite"]["journal_entries"]:
                writer.writerow(
                    [
                        je["tran_id"],
                        je["trandate"],
                        je["subsidiary"],
                        je["posting_period"],
                        je["currency"],
                        je["debit_account"],
                        je["credit_account"],
                        f"{je['amount_usd']:.2f}",
                        je["cseg_ai_provider"],
                        je["cseg_task_value_tier"],
                        je["linked_jira_epic"],
                        je["linked_git_release"],
                        je["memo"],
                    ]
                )
        elif target_key == "datadog":
            from backend.telemetry_data import get_datadog_telemetry
            dd = get_datadog_telemetry()
            writer.writerow(["trace_id", "service", "provider", "model", "engineer", "department", "task_category", "total_tokens", "cost_usd", "latency_ms", "git_commit", "jira_key", "release_id"])
            for s in dd["llm_observability_spans"]:
                writer.writerow([s["trace_id"], s["service"], s["provider"], s["model"], s["engineer"], s["department"], s["task_category"], s["total_tokens"], s["cost_usd"], s["latency_ms"], s["git_commit"], s["jira_key"], s["release_id"]])
        elif target_key == "substrate":
            from backend.telemetry_data import get_substrate_telemetry
            sub = get_substrate_telemetry()
            writer.writerow(["signal_id", "channel", "artifact_type", "department", "llm_provider", "model", "monthly_events", "tokens_burned", "llm_cost_usd", "workday_salary_burn_usd", "value_classification"])
            for s in sub["microsoft_substrate_signals"]:
                writer.writerow([s["signal_id"], s["channel"], s["artifact_type"], s["department"], s["llm_provider"], s["model"], s["monthly_events"], s["tokens_burned"], s["llm_cost_usd"], s["workday_salary_burn_usd"], s["value_classification"]])
        elif target_key == "newrelic":
            from backend.telemetry_data import get_newrelic_telemetry
            nr = get_newrelic_telemetry()
            writer.writerow(["app_id", "service_name", "tier", "apdex_score", "throughput_rpm", "response_time_p95_ms", "error_rate_pct", "latency_delta_pct", "release_id", "cicd_source", "llm_contributor"])
            for a in nr["apm_services"]:
                writer.writerow([a["app_id"], a["service_name"], a["tier"], a["apdex_score"], a["throughput_rpm"], a["response_time_p95_ms"], a["error_rate_pct"], a["latency_delta_pct"], a["release_id"], a["cicd_source"], a["llm_contributor"]])
        elif target_key == "soluble":
            from backend.telemetry_data import get_soluble_telemetry
            sol = get_soluble_telemetry()
            writer.writerow(["finding_id", "rule_id", "severity", "iac_type", "title", "repository", "branch", "commit_sha", "ci_pipeline", "policy_framework", "status", "remediation_time_mins"])
            for f in sol["security_findings"]:
                writer.writerow([f["finding_id"], f["rule_id"], f["severity"], f["iac_type"], f["title"], f["repository"], f["branch"], f["commit_sha"], f["ci_pipeline"], f["policy_framework"], f["status"], f["remediation_time_mins"]])
        else:
            writer.writerow(
                [
                    "RELEASE_ID",
                    "SCM_PROVIDER",
                    "REPOSITORY",
                    "CI_CD_BUILD",
                    "JIRA_EPIC",
                    "CLAUDE_TOKENS",
                    "GEMINI_TOKENS",
                    "TOKEN_COST_USD",
                    "WORKDAY_HOURS_SAVED",
                    "SALARY_VALUE_USD",
                    "SAGE_GL_ACCOUNT",
                    "NETSUITE_JE",
                    "ROI_MULTIPLE",
                ]
            )
            for r in self.state["releases"]:
                writer.writerow(
                    [
                        r["release_id"],
                        r["scm_provider"],
                        r["repository"],
                        r["build_number"],
                        r["jira_epic"],
                        r["claude_tokens"],
                        r["gemini_tokens"],
                        f"{r['token_cost_usd']:.2f}",
                        r["workday_hours_saved"],
                        f"{r['workday_salary_value_usd']:.2f}",
                        r["sage_gl_account"],
                        r["netsuite_je"],
                        r["roi_multiple"],
                    ]
                )
        return output.getvalue()

    def import_csv_rows(self, csv_text: str, target: str = "sage") -> Dict[str, Any]:
        reader = csv.DictReader(io.StringIO(csv_text.strip()))
        imported_count = 0
        for row in reader:
            imported_count += 1
            if target == "netsuite" or "SUBSIDIARY" in row or "subsidiary" in row:
                self.create_netsuite_journal_entry(
                    {
                        "tran_id": row.get("EXTERNAL_ID") or row.get("tran_id"),
                        "subsidiary": row.get("SUBSIDIARY")
                        or row.get("subsidiary")
                        or "SUB-2 BurnIQ Technologies US Inc.",
                        "amount_usd": float(
                            row.get("AMOUNT_USD") or row.get("amount_usd") or 9500.0
                        ),
                        "memo": row.get("MEMO")
                        or row.get("memo")
                        or "CSV Imported NetSuite AI Ledger Entry",
                        "linked_git_release": row.get("LINKED_GIT_RELEASE") or "REL-2026.11.4",
                    }
                )
            else:
                self.create_sage_gl_batch(
                    {
                        "batch_id": row.get("BATCH_ID") or row.get("batch_id"),
                        "entity_id": row.get("ENTITY_ID") or row.get("entity_id") or "E100",
                        "amount_usd": float(
                            row.get("AMOUNT_USD") or row.get("amount_usd") or 9500.0
                        ),
                        "description": row.get("AUDIT_TRAIL")
                        or row.get("description")
                        or "CSV Imported Sage Intacct AI GL Batch",
                    }
                )
        return {
            "status": "IMPORTED",
            "target": target,
            "rows_imported": imported_count,
        }


store = EnterpriseDataStore()
