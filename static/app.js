/* BurnIQ Frontend Application Controller — Sage Intacct/X3, Oracle NetSuite OneWorld/SuiteQL & Telemetry */

(function () {
  "use strict";

  let dashboardState = null;

  function fmtUSD(val) {
    const num = Number(val || 0);
    return "$" + num.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function fmtInt(val) {
    return Number(val || 0).toLocaleString("en-US");
  }

  function showToast(msg) {
    const el = document.getElementById("toast-banner");
    if (!el) return;
    el.textContent = msg;
    el.classList.add("visible");
    clearTimeout(el._timer);
    el._timer = setTimeout(() => {
      el.classList.remove("visible");
    }, 4200);
  }

  function activateTab(targetId) {
    document.querySelectorAll(".nav-tab").forEach((btn) => {
      btn.classList.toggle("active", btn.getAttribute("data-target") === targetId);
    });
    document.querySelectorAll(".tab-panel").forEach((panel) => {
      panel.classList.toggle("active", panel.id === targetId);
    });
  }

  async function fetchDashboard() {
    const res = await fetch("/api/dashboard");
    dashboardState = await res.json();
    renderAll(dashboardState);
  }

  function renderAll(data) {
    if (!data) return;
    const kpis = data.kpis || {};
    document.getElementById("kpi-total-spend").textContent = fmtUSD(kpis.total_llm_spend_mtd_usd);
    document.getElementById("kpi-capex-rd").textContent = fmtUSD(kpis.capitalized_rd_asc350_usd);
    document.getElementById("kpi-workday-roi").textContent = fmtUSD(kpis.workday_net_salary_roi_usd);
    document.getElementById("kpi-hours-saved").textContent = kpis.workday_engineering_hours_saved;
    document.getElementById("kpi-low-value-waste").textContent = fmtUSD(kpis.low_value_email_notes_waste_usd);
    document.getElementById("kpi-recoverable-savings").textContent = fmtUSD(kpis.recoverable_monthly_savings_usd);
    document.getElementById("kpi-salesforce-arr").textContent = "$" + fmtInt(kpis.salesforce_arr_attributed_usd);
    document.getElementById("kpi-connected-systems").textContent =
      kpis.connected_enterprise_systems + " / " + kpis.connected_enterprise_systems;
    const badgeConn = document.getElementById("badge-connectors-count");
    if (badgeConn) badgeConn.textContent = kpis.connected_enterprise_systems;

    renderOverview(data);
    renderSageErp(data.sage_erp);
    renderNetSuite(data.oracle_netsuite);
    renderWorkdayEmployees(data.employees);
    renderLowValueAudit(data.low_value_tasks);
    renderConnectors(data.connectors);
  }

  function renderOverview(data) {
    const sageEntities = (data.sage_erp && data.sage_erp.entities) || [];
    const sageTbody = document.getElementById("overview-sage-entities-tbody");
    sageTbody.innerHTML = sageEntities
      .map(
        (e) => `
      <tr>
        <td><strong>${e.entity_id}</strong> &mdash; ${e.name}</td>
        <td><span class="badge badge-success">${e.erp_module}</span></td>
        <td class="mono">${fmtUSD(e.ai_actual_spend)}</td>
        <td class="mono">${fmtUSD(e.capitalized_rd_usd)}</td>
        <td class="mono">${fmtUSD(e.low_value_waste_usd)}</td>
        <td class="mono"><strong>${fmtUSD(e.net_salary_roi_usd)}</strong></td>
      </tr>`
      )
      .join("");

    const nsSubs = (data.oracle_netsuite && data.oracle_netsuite.subsidiaries) || [];
    const nsTbody = document.getElementById("overview-netsuite-subs-tbody");
    nsTbody.innerHTML = nsSubs
      .map(
        (s) => `
      <tr>
        <td><strong>${s.internal_id}</strong> &mdash; ${s.name}</td>
        <td class="mono">${s.currency}</td>
        <td class="mono">${fmtUSD(s.llm_po_commit_usd)}</td>
        <td class="mono">${fmtUSD(s.mtd_token_burn_usd)}</td>
        <td class="mono">${fmtUSD(s.capex_amortized_mtd_usd)}</td>
        <td><span class="badge badge-amber">+${s.ebitda_margin_lift_bps} bps</span></td>
      </tr>`
      )
      .join("");

    const releases = data.releases || [];
    const relTbody = document.getElementById("overview-releases-tbody");
    relTbody.innerHTML = releases
      .map(
        (r) => `
      <tr>
        <td><strong>${r.release_id}</strong><br/><span style="font-size:11.5px;color:var(--text-secondary)">${r.name}</span></td>
        <td><strong>${r.scm_provider}</strong> &bull; <code class="mono">${r.branch}</code><br/><span style="font-size:11.5px;color:var(--text-muted)">${r.commit_count} commits (${r.head_sha})</span></td>
        <td><span class="badge badge-sky">${r.ci_cd_provider}: ${r.build_number}</span></td>
        <td class="mono">${r.jira_epic}<br/><span style="font-size:11.5px;color:var(--text-muted)">${r.servicenow_chg}</span></td>
        <td class="mono">${fmtInt(r.claude_tokens + r.gemini_tokens)} tok</td>
        <td class="mono">${fmtUSD(r.token_cost_usd)}</td>
        <td class="mono"><strong>${fmtUSD(r.workday_salary_value_usd)}</strong> (${r.workday_hours_saved}h)</td>
        <td><span class="badge badge-success">${r.sage_gl_account}</span></td>
        <td><span class="badge badge-amber">${r.netsuite_je}</span></td>
        <td><strong>${r.roi_multiple}x</strong></td>
      </tr>`
      )
      .join("");
  }

  function renderSageErp(sage) {
    if (!sage) return;
    const acctTbody = document.getElementById("sage-gl-accounts-tbody");
    acctTbody.innerHTML = (sage.gl_accounts || [])
      .map(
        (a) => `
      <tr>
        <td class="mono"><strong>${a.account_no}</strong></td>
        <td><strong>${a.title}</strong></td>
        <td><span class="badge ${a.account_no === "6120-02" ? "badge-danger" : "badge-success"}">${a.account_type}</span></td>
        <td class="mono">${a.normal_balance}</td>
        <td class="mono">${a.department_dim}</td>
        <td class="mono"><strong>${fmtUSD(a.mtd_balance_usd)}</strong></td>
        <td class="mono">${fmtUSD(a.ytd_balance_usd)}</td>
        <td style="font-size:12px;color:var(--text-secondary)">${a.compliance_rule}</td>
      </tr>`
      )
      .join("");

    const batchesTbody = document.getElementById("sage-batches-tbody");
    batchesTbody.innerHTML = (sage.gl_batches || [])
      .map(
        (b) => `
      <tr>
        <td class="mono"><strong>${b.batch_id}</strong></td>
        <td class="mono">${b.journal_symbol}</td>
        <td class="mono">${b.posting_date}</td>
        <td class="mono">${b.entity_id}</td>
        <td class="mono">DR ${b.debit_account} / CR ${b.credit_account}</td>
        <td class="mono"><strong>${fmtUSD(b.amount_usd)}</strong></td>
        <td>${b.department}<br/><code class="mono" style="font-size:11.5px;color:var(--text-muted)">${b.project_dim}</code></td>
        <td><span class="badge ${b.status.includes("FLAGGED") ? "badge-danger" : "badge-success"}">${b.status}</span></td>
        <td style="font-size:12px;color:var(--text-secondary)">${b.audit_trail}</td>
      </tr>`
      )
      .join("");

    const billsTbody = document.getElementById("sage-bills-tbody");
    billsTbody.innerHTML = (sage.vendor_bills || [])
      .map(
        (v) => `
      <tr>
        <td class="mono"><strong>${v.bill_id}</strong></td>
        <td><strong>${v.vendor_name}</strong></td>
        <td class="mono">${v.entity_id}</td>
        <td class="mono">${v.invoice_date}</td>
        <td class="mono">${fmtUSD(v.billed_amount_usd)}</td>
        <td class="mono">${fmtUSD(v.telemetry_verified_usd)}</td>
        <td class="mono">${fmtUSD(v.capex_eligible_usd)}</td>
        <td class="mono">${fmtUSD(v.low_value_waste_usd)}</td>
        <td><span class="badge badge-success">${v.match_status}</span></td>
      </tr>`
      )
      .join("");
  }

  function renderNetSuite(ns) {
    if (!ns) return;
    const subsTbody = document.getElementById("netsuite-subs-tbody");
    subsTbody.innerHTML = (ns.subsidiaries || [])
      .map(
        (s) => `
      <tr>
        <td class="mono"><strong>${s.internal_id}</strong></td>
        <td><strong>${s.name}</strong></td>
        <td class="mono">${s.currency}</td>
        <td>${s.country}</td>
        <td class="mono">${fmtUSD(s.llm_po_commit_usd)}</td>
        <td class="mono">${fmtUSD(s.mtd_token_burn_usd)}</td>
        <td class="mono">${fmtUSD(s.capex_amortized_mtd_usd)}</td>
        <td class="mono"><strong>${fmtUSD(s.arr_attributed_usd)}</strong></td>
        <td><span class="badge badge-amber">+${s.ebitda_margin_lift_bps} bps</span></td>
      </tr>`
      )
      .join("");

    const jeTbody = document.getElementById("netsuite-je-tbody");
    jeTbody.innerHTML = (ns.journal_entries || [])
      .map(
        (j) => `
      <tr>
        <td class="mono"><strong>${j.tran_id}</strong></td>
        <td class="mono">${j.trandate}</td>
        <td>${j.subsidiary}</td>
        <td>${j.debit_account}</td>
        <td>${j.credit_account}</td>
        <td class="mono"><strong>${fmtUSD(j.amount_usd)}</strong></td>
        <td><span class="badge badge-sky">${j.cseg_ai_provider}</span></td>
        <td><span class="badge ${j.cseg_task_value_tier.includes("Tier 3") ? "badge-danger" : "badge-success"}">${j.cseg_task_value_tier}</span></td>
        <td class="mono">${j.linked_git_release}<br/><span style="font-size:11px;color:var(--text-muted)">${j.linked_jira_epic}</span></td>
        <td><span class="badge ${j.approval_status.includes("Flagged") ? "badge-danger" : "badge-amber"}">${j.approval_status}</span></td>
      </tr>`
      )
      .join("");

    const poTbody = document.getElementById("netsuite-po-tbody");
    poTbody.innerHTML = (ns.purchase_orders || [])
      .map(
        (p) => `
      <tr>
        <td class="mono"><strong>${p.po_number}</strong></td>
        <td><strong>${p.vendor}</strong></td>
        <td class="mono">${fmtUSD(p.total_commit_usd)}</td>
        <td class="mono">${fmtUSD(p.consumed_ytd_usd)} (${p.burn_utilization_pct}%)</td>
        <td class="mono">${fmtUSD(p.remaining_balance_usd)}</td>
        <td><span class="badge badge-success">${p.productive_code_pct}% Productive</span></td>
      </tr>`
      )
      .join("");

    const amortTbody = document.getElementById("netsuite-amort-tbody");
    amortTbody.innerHTML = (ns.amortization_schedules || [])
      .map(
        (a) => `
      <tr>
        <td class="mono"><strong>${a.schedule_id}</strong></td>
        <td class="mono">${a.release_tag}</td>
        <td class="mono">${fmtUSD(a.capitalized_token_usd)}</td>
        <td class="mono">${fmtUSD(a.capitalized_workday_labor_usd)}</td>
        <td class="mono"><strong>${fmtUSD(a.total_capitalized_asset_usd)}</strong></td>
        <td class="mono">${fmtUSD(a.monthly_amortization_usd)}/mo</td>
      </tr>`
      )
      .join("");
  }

  async function executeSuiteQL(queryText) {
    const res = await fetch("/api/erp/netsuite/suiteql", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: queryText }),
    });
    const payload = await res.json();
    const metaBar = document.getElementById("suiteql-meta-bar");
    metaBar.textContent = `SuiteQL v${payload.suiteql_version} • Account ${payload.account_id} • Returned ${payload.row_count} rows in ${payload.execution_time_ms} ms`;

    const cols = payload.columns || [];
    const items = payload.items || [];
    document.getElementById("suiteql-results-thead").innerHTML =
      "<tr>" + cols.map((c) => `<th>${c}</th>`).join("") + "</tr>";
    document.getElementById("suiteql-results-tbody").innerHTML = items
      .map(
        (row) =>
          "<tr>" +
          cols
            .map((c) => {
              const v = row[c];
              if (typeof v === "number" && c.includes("usd")) {
                return `<td class="mono">${fmtUSD(v)}</td>`;
              }
              return `<td class="mono">${v !== undefined ? v : ""}</td>`;
            })
            .join("") +
          "</tr>"
      )
      .join("");
  }

  function renderWorkdayEmployees(employees) {
    const tbody = document.getElementById("workday-employees-tbody");
    tbody.innerHTML = (employees || [])
      .map(
        (e) => `
      <tr>
        <td class="mono"><strong>${e.workday_id}</strong></td>
        <td><strong>${e.name}</strong><br/><span style="font-size:11.5px;color:var(--text-secondary)">${e.role}</span></td>
        <td>${e.department}</td>
        <td class="mono">Sage: ${e.sage_entity}<br/><span style="font-size:11.5px;color:var(--text-muted)">${e.netsuite_subsidiary}</span></td>
        <td class="mono">${fmtUSD(e.annual_loaded_salary_usd)}/yr ($${e.hourly_rate_usd}/hr)</td>
        <td class="mono">${e.commits_shipped} commits / ${e.releases_contributed} rels (${e.jira_story_points} pts)</td>
        <td class="mono">${fmtUSD(e.token_spend_mtd_usd)}</td>
        <td class="mono">${fmtUSD(e.low_value_spend_usd)}</td>
        <td class="mono">${e.hours_saved_mtd}h</td>
        <td class="mono"><strong>${fmtUSD(e.salary_value_created_usd)}</strong></td>
        <td class="mono"><strong>${e.net_roi_pct}%</strong></td>
        <td><span class="badge ${e.audit_status.includes("ALERT") ? "badge-danger" : "badge-success"}">${e.audit_status}</span></td>
      </tr>`
      )
      .join("");
  }

  function renderLowValueAudit(tasks) {
    const tbody = document.getElementById("low-value-audit-tbody");
    tbody.innerHTML = (tasks || [])
      .map(
        (t) => `
      <tr>
        <td class="mono"><strong>${t.audit_id}</strong></td>
        <td><strong>${t.employee}</strong><br/><code class="mono" style="font-size:11px;color:var(--text-muted)">${t.workday_id}</code></td>
        <td>${t.department}</td>
        <td><strong>${t.task_category}</strong></td>
        <td class="mono">${t.model_used}</td>
        <td class="mono">${t.recommended_model}</td>
        <td class="mono">${fmtInt(t.prompt_count)}</td>
        <td class="mono">${fmtUSD(t.current_cost_usd)}</td>
        <td class="mono">${fmtUSD(t.projected_routed_cost_usd)}</td>
        <td class="mono"><strong>${fmtUSD(t.monthly_savings_usd)}</strong></td>
        <td class="mono">Sage: ${t.sage_gl_impact}<br/>NetSuite: ${t.netsuite_je_impact}</td>
        <td><span class="badge ${t.status === "OPTIMIZED_ROUTED" ? "badge-success" : "badge-danger"}">${t.status}</span></td>
      </tr>`
      )
      .join("");
  }

  function renderConnectors(connectors) {
    const grid = document.getElementById("connectors-grid");
    grid.innerHTML = (connectors || [])
      .map(
        (c) => `
      <div class="connector-card" id="connector-card-${c.id}">
        <div class="connector-top">
          <div>
            <div class="connector-name">${c.name}</div>
            <div class="connector-cat">${c.category} &bull; ${c.protocol}</div>
          </div>
          <span class="badge badge-success">${c.status} (${c.health_ms}ms)</span>
        </div>
        <div class="connector-desc">${c.description}</div>
        <div class="connector-meta">
          <span class="mono">${fmtInt(c.records_synced)} records</span>
          <button class="btn btn-test-conn" data-conn-id="${c.id}" type="button">Test Handshake</button>
        </div>
      </div>`
      )
      .join("");

    grid.querySelectorAll(".btn-test-conn").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const cid = btn.getAttribute("data-conn-id");
        const res = await fetch(`/api/connectors/${cid}/test`, { method: "POST" });
        const out = await res.json();
        showToast(out.handshake || `Verified ${cid} connection`);
        fetchDashboard();
      });
    });
  }

  function bindEvents() {
    document.querySelectorAll(".nav-tab").forEach((btn) => {
      btn.addEventListener("click", () => {
        activateTab(btn.getAttribute("data-target"));
      });
    });

    document.getElementById("btn-goto-sage").addEventListener("click", () => activateTab("panel-sage"));
    document.getElementById("btn-goto-netsuite").addEventListener("click", () => activateTab("panel-netsuite"));

    document.getElementById("btn-test-sage-conn").addEventListener("click", async () => {
      const res = await fetch("/mock-enterprise/api.intacct.com/ia/api/v1/connection");
      const data = await res.json();
      showToast(`Sage Intacct & X3 Connected: Company ${data.company_id} (${data.entities_active.join(", ")})`);
    });

    document.getElementById("btn-test-netsuite-conn").addEventListener("click", async () => {
      const res = await fetch("/mock-enterprise/company.suitetalk.api.netsuite.com/services/rest/record/v1/connection");
      const data = await res.json();
      showToast(`Oracle NetSuite OneWorld Connected: Account ${data.account_id} (${data.subsidiaries_active.length} Subsidiaries)`);
    });

    document.getElementById("form-sage-gl-batch").addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      const payload = Object.fromEntries(fd.entries());
      const res = await fetch("/api/erp/sage/gl-batch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const out = await res.json();
      showToast(`Posted Sage Intacct GL Batch ${out.batch.batch_id} ($${out.batch.amount_usd})`);
      fetchDashboard();
    });

    document.getElementById("form-netsuite-je").addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      const payload = Object.fromEntries(fd.entries());
      const res = await fetch("/api/erp/netsuite/journal-entry", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const out = await res.json();
      showToast(`Posted Oracle NetSuite Journal Entry ${out.journal_entry.tran_id}`);
      fetchDashboard();
      executeSuiteQL(document.getElementById("suiteql-query-input").value);
    });

    document.getElementById("btn-run-suiteql").addEventListener("click", () => {
      const q = document.getElementById("suiteql-query-input").value;
      executeSuiteQL(q);
    });

    document.querySelectorAll(".suiteql-preset").forEach((btn) => {
      btn.addEventListener("click", () => {
        const q = btn.getAttribute("data-query");
        document.getElementById("suiteql-query-input").value = q;
        executeSuiteQL(q);
      });
    });

    async function handleOptimizeWaste() {
      const res = await fetch("/api/audit/optimize-routing", { method: "POST" });
      const out = await res.json();
      showToast(
        `Smart Routing Active! Saved ${fmtUSD(out.monthly_savings_realized_usd)}/mo & Reconciled Sage GL 6120-02 + NetSuite JE-NS-9043`
      );
      fetchDashboard();
    }

    document.getElementById("btn-apply-smart-routing").addEventListener("click", handleOptimizeWaste);
    document.getElementById("btn-overview-optimize-waste").addEventListener("click", handleOptimizeWaste);

    document.getElementById("form-csv-import").addEventListener("submit", async (e) => {
      e.preventDefault();
      const target = document.getElementById("csv-target-select").value;
      const csvText = document.getElementById("csv-payload-input").value;
      const res = await fetch("/api/import/csv", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target, csv_text: csvText }),
      });
      const out = await res.json();
      showToast(`Imported ${out.rows_imported} CSV rows into ${target.toUpperCase()} ledger`);
      fetchDashboard();
    });

    document.getElementById("btn-reset-demo").addEventListener("click", async () => {
      await fetch("/api/reset", { method: "POST" });
      showToast("Reset BurnIQ telemetry, Sage Intacct & Oracle NetSuite ledgers to baseline");
      fetchDashboard();
      executeSuiteQL(document.getElementById("suiteql-query-input").value);
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    bindEvents();
    fetchDashboard();
    executeSuiteQL(document.getElementById("suiteql-query-input").value);
  });
})();
