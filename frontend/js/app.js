/**
 * BurnIQ v2.4 — Enterprise Application Controller.
 * Manages Service Connection ON/OFF circuit toggles, 4 Role-Based Persona Dashboards
 * (Technical Ops, Developers, Managers, C-Suite), Hybrid BM25+Vector Search,
 * and Customized RAG-Trained Google Flash 3-8 Fast Lite LLM Studio.
 */

(function () {
  const state = {
    activeView: "dashboards",
    activePersona: "csuite",
    timeframe: "30d",
    department: "all",
    connCategory: "all",
    connStatus: "all",
    connectionsData: null,
    dashboardData: null,
    lastSearchResults: null,
  };

  function escapeHtml(str) {
    return String(str ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function showToast(message, tone = "emerald") {
    const container = document.getElementById("toast-container");
    if (!container) return;
    const item = document.createElement("div");
    item.className = "toast-item";
    const dotColor =
      tone === "coral"
        ? "var(--accent-coral)"
        : tone === "amber"
        ? "var(--accent-amber)"
        : "var(--accent-emerald)";
    item.innerHTML = `
      <span class="status-dot" style="background:${dotColor};box-shadow:0 0 8px ${dotColor};"></span>
      <span>${escapeHtml(message)}</span>
    `;
    container.appendChild(item);
    setTimeout(() => {
      item.remove();
    }, 3600);
  }

  async function apiFetch(url, options = {}) {
    const resp = await fetch(url, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    if (!resp.ok) {
      let errMsg = `HTTP ${resp.status}`;
      try {
        const errData = await resp.json();
        errMsg = errData.detail || errMsg;
      } catch (_) {}
      throw new Error(errMsg);
    }
    return resp.json();
  }

  // ---------------------------------------------------------------------------
  // Navigation & View Switching
  // ---------------------------------------------------------------------------
  function switchView(viewName) {
    state.activeView = viewName;
    document.querySelectorAll(".nav-tab").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.view === viewName);
    });
    document.querySelectorAll(".workspace-view").forEach((sec) => {
      sec.style.display = sec.id === `view-${viewName}` ? "block" : "none";
    });

    if (viewName === "connections") {
      loadConnections();
    } else if (viewName === "search-rag") {
      runEnterpriseSearch();
    } else {
      loadPersonaDashboard();
    }
  }

  function switchPersona(persona) {
    state.activePersona = persona;
    document.querySelectorAll(".persona-card-btn").forEach((btn) => {
      const isAct = btn.dataset.persona === persona;
      btn.classList.toggle("active", isAct);
      btn.setAttribute("aria-selected", isAct ? "true" : "false");
    });

    const labels = {
      techops: "TechOps",
      developers: "Developers",
      managers: "Managers",
      csuite: "C-Suite",
    };
    const badge = document.getElementById("badge-active-persona");
    if (badge) badge.textContent = labels[persona] || persona;

    loadPersonaDashboard();
  }

  // ---------------------------------------------------------------------------
  // Global Service Connections State & Quick Strip
  // ---------------------------------------------------------------------------
  async function loadConnections() {
    try {
      const params = new URLSearchParams({
        category: state.connCategory,
        status: state.connStatus,
      });
      const data = await apiFetch(`/api/connections?${params.toString()}`);
      state.connectionsData = data;
      renderQuickStrip(data);
      renderConnectionsView(data);
    } catch (err) {
      showToast(`Failed to load connections: ${err.message}`, "coral");
    }
  }

  function renderQuickStrip(data) {
    const badge = document.getElementById("badge-connections-count");
    if (badge) {
      badge.textContent = `${data.online_count}/${data.all_count} ON`;
      badge.className = `nav-badge ${data.online_count < data.all_count ? "amber" : ""}`;
    }

    const dot = document.getElementById("strip-global-dot");
    if (dot) {
      dot.className = `status-dot ${data.online_count > 0 ? "online" : "paused"}`;
    }

    const summary = document.getElementById("strip-online-summary");
    if (summary) {
      summary.textContent = `${data.online_count} / ${data.all_count} Service Connections ON`;
    }

    const tp = document.getElementById("strip-throughput-summary");
    if (tp) {
      tp.textContent = `(${Number(data.total_events_per_hour).toLocaleString()} ev/hr · $${Number(data.active_monthly_value_usd).toLocaleString()}/mo ROI)`;
    }

    const pillsWrap = document.getElementById("quick-strip-pills");
    if (!pillsWrap) return;

    // Fetch full list if filtered
    const list = data.connections || [];
    pillsWrap.innerHTML = list
      .map((c) => {
        const shortName = c.name
          .replace("Google ", "")
          .replace("Anthropic ", "")
          .replace("Atlassian ", "")
          .replace("Microsoft ", "")
          .replace("Enterprise", "")
          .replace("(RAG Engine)", "")
          .trim();
        return `
          <button
            type="button"
            class="conn-mini-pill ${c.enabled ? "on" : "off"}"
            data-action="toggle-conn"
            data-conn-id="${escapeHtml(c.id)}"
            id="strip-pill-${escapeHtml(c.id)}"
            title="Click to turn ${escapeHtml(c.name)} ${c.enabled ? "OFF" : "ON"}"
          >
            <span class="conn-mini-state ${c.enabled ? "on" : "off"}">${c.enabled ? "ON" : "OFF"}</span>
            <span>${escapeHtml(shortName)}</span>
          </button>
        `;
      })
      .join("");
  }

  function renderConnectionsView(data) {
    const kpiWrap = document.getElementById("connections-summary-kpis");
    if (kpiWrap) {
      const netRoi = (data.active_monthly_value_usd / Math.max(data.active_monthly_cost_usd, 1)).toFixed(1);
      kpiWrap.innerHTML = `
        <div class="kpi-card">
          <span class="kpi-label">Active Connections (ON)</span>
          <span class="kpi-value">${data.online_count} / ${data.all_count}</span>
          <div class="kpi-footer">
            <span class="kpi-subvalue">${data.paused_count} paused circuits</span>
            <span class="kpi-delta positive">Real-Time Control</span>
          </div>
        </div>
        <div class="kpi-card">
          <span class="kpi-label">RAG-Enabled Connectors</span>
          <span class="kpi-value">${data.rag_active_count}</span>
          <div class="kpi-footer">
            <span class="kpi-subvalue">${data.total_docs_indexed} source docs indexed</span>
            <span class="kpi-delta positive">Flash-Lite Synced</span>
          </div>
        </div>
        <div class="kpi-card">
          <span class="kpi-label">Active Telemetry Stream</span>
          <span class="kpi-value">${Number(data.total_events_per_hour).toLocaleString()}</span>
          <div class="kpi-footer">
            <span class="kpi-subvalue">Events / Hour ingested</span>
            <span class="kpi-delta positive">mTLS Verified</span>
          </div>
        </div>
        <div class="kpi-card">
          <span class="kpi-label">Active Monthly Spend</span>
          <span class="kpi-value">$${Number(data.active_monthly_cost_usd).toLocaleString()}</span>
          <div class="kpi-footer">
            <span class="kpi-subvalue">SAP S/4HANA tracked</span>
            <span class="kpi-delta positive">Under Ceiling</span>
          </div>
        </div>
        <div class="kpi-card">
          <span class="kpi-label">Active Workday &amp; Ops Value</span>
          <span class="kpi-value">$${Number(data.active_monthly_value_usd).toLocaleString()}</span>
          <div class="kpi-footer">
            <span class="kpi-subvalue">Verified monthly value</span>
            <span class="kpi-delta positive">${netRoi}x Active Yield</span>
          </div>
        </div>
        <div class="kpi-card">
          <span class="kpi-label">Primary RAG Engine</span>
          <span class="kpi-value">Flash 3-8 Lite</span>
          <div class="kpi-footer">
            <span class="kpi-subvalue">$0.035 / 1M input tokens</span>
            <span class="kpi-delta positive">94ms TTFT</span>
          </div>
        </div>
      `;
    }

    const grid = document.getElementById("connections-cards-grid");
    if (grid) {
      grid.innerHTML = (data.connections || [])
        .map((c) => {
          const isOn = Boolean(c.enabled);
          const isRag = Boolean(c.rag_enabled);
          return `
            <article class="connection-card ${isOn ? "is-on" : "is-off"}" id="card-${escapeHtml(c.id)}">
              <div class="conn-card-header">
                <div>
                  <span class="conn-category-tag">${escapeHtml(c.category)} · ${escapeHtml(c.subcategory)}</span>
                  <h2 class="conn-title">${escapeHtml(c.name)}</h2>
                  <span class="conn-vendor">${escapeHtml(c.vendor)} · <code>${escapeHtml(c.auth_mode)}</code></span>
                </div>
                <div class="circuit-switch-group">
                  <button
                    type="button"
                    role="switch"
                    aria-checked="${isOn ? "true" : "false"}"
                    aria-label="Turn ${escapeHtml(c.name)} ${isOn ? "OFF" : "ON"}"
                    class="circuit-switch"
                    id="switch-${escapeHtml(c.id)}"
                    data-action="toggle-conn"
                    data-conn-id="${escapeHtml(c.id)}"
                  >
                    <span class="circuit-switch-thumb"></span>
                  </button>
                  <span class="circuit-state-label ${isOn ? "on" : "off"}">${isOn ? "CIRCUIT ON" : "CIRCUIT OFF"}</span>
                </div>
              </div>

              <p class="conn-desc">${escapeHtml(c.description)}</p>

              <div class="conn-metrics-strip">
                <div class="conn-metric-item">
                  <span class="conn-metric-label">Stream Rate</span>
                  <span class="conn-metric-val">${isOn ? Number(c.events_per_hour).toLocaleString() + "/hr" : "0/hr (OFF)"}</span>
                </div>
                <div class="conn-metric-item">
                  <span class="conn-metric-label">Latency</span>
                  <span class="conn-metric-val">${isOn ? c.latency_ms + " ms" : "Paused"}</span>
                </div>
                <div class="conn-metric-item">
                  <span class="conn-metric-label">RAG Docs</span>
                  <span class="conn-metric-val">${c.docs_indexed} chunks</span>
                </div>
                <div class="conn-metric-item">
                  <span class="conn-metric-label">Monthly ROI</span>
                  <span class="conn-metric-val" style="color:var(--accent-emerald);">$${Number(c.monthly_value_usd).toLocaleString()}</span>
                </div>
              </div>

              <div class="conn-card-footer">
                <label class="rag-checkbox-label" for="rag-chk-${escapeHtml(c.id)}">
                  <input
                    type="checkbox"
                    id="rag-chk-${escapeHtml(c.id)}"
                    data-action="toggle-rag"
                    data-conn-id="${escapeHtml(c.id)}"
                    ${isRag ? "checked" : ""}
                  />
                  <span>Feed into Flash 3-8 Lite RAG</span>
                </label>
                <div style="display:flex;gap:0.4rem;">
                  <button type="button" class="btn btn-sm" data-action="test-conn" data-conn-id="${escapeHtml(c.id)}" id="btn-test-${escapeHtml(c.id)}">
                    Test Endpoint
                  </button>
                  <button type="button" class="btn btn-sm ${isOn ? "btn-amber" : ""}" data-action="sync-conn" data-conn-id="${escapeHtml(c.id)}" id="btn-sync-${escapeHtml(c.id)}" ${!isOn ? "disabled" : ""}>
                    Sync Now
                  </button>
                </div>
              </div>
            </article>
          `;
        })
        .join("");
    }

    const eventsWrap = document.getElementById("connection-events-table-wrap");
    if (eventsWrap) {
      const rows = (data.recent_events || [])
        .map(
          (ev) => `
          <tr>
            <td><span class="code-badge">${escapeHtml(ev.connection_id)}</span></td>
            <td><strong>${escapeHtml(ev.event_type)}</strong></td>
            <td><span class="code-badge">${escapeHtml(ev.previous_state)} &rarr; ${escapeHtml(ev.new_state)}</span></td>
            <td>${escapeHtml(ev.details)}</td>
            <td>${escapeHtml(ev.actor)}</td>
            <td class="tabular-nums">${escapeHtml(String(ev.created_at).slice(0, 19).replace("T", " "))}</td>
          </tr>
        `
        )
        .join("");

      eventsWrap.innerHTML = `
        <table class="telemetry-table">
          <thead>
            <tr>
              <th>Connection ID</th>
              <th>Event Type</th>
              <th>State Transition</th>
              <th>Audit Details</th>
              <th>Actor</th>
              <th>Timestamp (UTC)</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      `;
    }
  }

  async function toggleConnectionState(connId, explicitEnabled = null, explicitRag = null) {
    try {
      const payload = {};
      if (explicitEnabled !== null) payload.enabled = explicitEnabled;
      if (explicitRag !== null) payload.rag_enabled = explicitRag;

      const res = await apiFetch(`/api/connections/${encodeURIComponent(connId)}/toggle`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      const isNowOn = res.connection.enabled;
      showToast(res.message, isNowOn ? "emerald" : "amber");

      await loadConnections();
      if (state.activeView === "dashboards") {
        await loadPersonaDashboard();
      } else if (state.activeView === "search-rag") {
        await runEnterpriseSearch();
      }
    } catch (err) {
      showToast(`Toggle error: ${err.message}`, "coral");
    }
  }

  async function bulkToggleConnections(enabled, useCategoryFilter = false) {
    try {
      const category = useCategoryFilter ? state.connCategory : "all";
      await apiFetch("/api/connections/bulk-toggle", {
        method: "POST",
        body: JSON.stringify({ enabled, category }),
      });
      showToast(
        `Turned ${enabled ? "ON" : "OFF"} ${category === "all" ? "all 16 service connections" : category}`,
        enabled ? "emerald" : "amber"
      );
      await loadConnections();
      if (state.activeView === "dashboards") {
        await loadPersonaDashboard();
      } else if (state.activeView === "search-rag") {
        await runEnterpriseSearch();
      }
    } catch (err) {
      showToast(`Bulk toggle failed: ${err.message}`, "coral");
    }
  }

  async function testConnection(connId) {
    try {
      const res = await apiFetch(`/api/connections/${encodeURIComponent(connId)}/test`, {
        method: "POST",
      });
      showToast(`${res.name}: ${res.message}`, res.reachable ? "emerald" : "amber");
      await loadConnections();
    } catch (err) {
      showToast(`Test failed: ${err.message}`, "coral");
    }
  }

  async function syncConnection(connId) {
    try {
      const res = await apiFetch(`/api/connections/${encodeURIComponent(connId)}/sync`, {
        method: "POST",
      });
      showToast(
        `Synced ${res.name}: ${res.docs_indexed} RAG docs, ${Number(res.events_per_hour).toLocaleString()} ev/hr`,
        "emerald"
      );
      await loadConnections();
      if (state.activeView === "dashboards") await loadPersonaDashboard();
    } catch (err) {
      showToast(`Sync failed: ${err.message}`, "coral");
    }
  }

  // ---------------------------------------------------------------------------
  // Multi-Persona Dashboards (Technical Ops, Developers, Managers, C-Suite)
  // ---------------------------------------------------------------------------
  async function loadPersonaDashboard() {
    try {
      const params = new URLSearchParams({
        timeframe: state.timeframe,
        department: state.department,
      });
      const data = await apiFetch(
        `/api/dashboard/${encodeURIComponent(state.activePersona)}?${params.toString()}`
      );
      state.dashboardData = data;
      renderPersonaDashboard(data);
    } catch (err) {
      showToast(`Dashboard error: ${err.message}`, "coral");
    }
  }

  function renderPersonaDashboard(data) {
    const titleEl = document.getElementById("dashboard-main-title");
    const subEl = document.getElementById("dashboard-main-subtitle");
    if (titleEl) titleEl.textContent = data.title;
    if (subEl) subEl.textContent = data.subtitle;

    // Populate department selector once
    const deptSelect = document.getElementById("select-dashboard-department");
    if (deptSelect && deptSelect.options.length <= 1 && data.available_departments) {
      deptSelect.innerHTML = data.available_departments
        .map(
          (d) =>
            `<option value="${escapeHtml(d)}" ${d === state.department ? "selected" : ""}>${
              d === "all" ? "All Enterprise Departments" : escapeHtml(d)
            }</option>`
        )
        .join("");
    }

    // Render 6 KPI cards
    const kpiGrid = document.getElementById("dashboard-kpi-grid");
    if (kpiGrid) {
      kpiGrid.innerHTML = (data.kpis || [])
        .map(
          (k) => `
          <div class="kpi-card" id="${escapeHtml(k.id)}">
            <span class="kpi-label">${escapeHtml(k.label)}</span>
            <span class="kpi-value">${escapeHtml(k.value)}</span>
            <div class="kpi-footer">
              <span class="kpi-subvalue">${escapeHtml(k.subvalue)}</span>
              <span class="kpi-delta ${escapeHtml(k.delta_type)}">${escapeHtml(k.delta)}</span>
            </div>
          </div>
        `
        )
        .join("");
    }

    // Render 4 Charts
    const chartsGrid = document.getElementById("dashboard-charts-grid");
    if (chartsGrid && window.BurnIQCharts) {
      const entries = Object.entries(data.charts || {});
      chartsGrid.innerHTML = entries
        .map(([key, cfg]) => window.BurnIQCharts.renderChartPanel(key, cfg))
        .join("");
    }

    // Render Persona Table
    const tableTitle = document.getElementById("dashboard-table-title");
    if (tableTitle) tableTitle.textContent = data.table_title || "Telemetry Records";

    const tableWrap = document.getElementById("dashboard-table-container");
    if (tableWrap) {
      tableWrap.innerHTML = renderPersonaTableHTML(data.persona, data.table_rows || []);
    }
  }

  function renderPersonaTableHTML(persona, rows) {
    if (!rows.length) return "<p>No records matching filter.</p>";

    if (persona === "techops") {
      const body = rows
        .map(
          (c) => `
          <tr>
            <td>
              <button
                type="button"
                class="btn btn-sm ${c.enabled ? "btn-emerald" : "btn-coral-subtle"}"
                data-action="toggle-conn"
                data-conn-id="${escapeHtml(c.id)}"
                id="tbl-toggle-${escapeHtml(c.id)}"
              >
                ${c.enabled ? "ON (Online)" : "OFF (Paused)"}
              </button>
            </td>
            <td><strong>${escapeHtml(c.name)}</strong><br/><span style="font-size:0.74rem;color:var(--text-muted);">${escapeHtml(c.endpoint_url)}</span></td>
            <td><span class="code-badge">${escapeHtml(c.category)}</span></td>
            <td>${escapeHtml(c.auth_mode)}</td>
            <td class="tabular-nums">${c.enabled ? Number(c.events_per_hour).toLocaleString() + " / hr" : "0 (Paused)"}</td>
            <td class="tabular-nums">${c.enabled ? c.latency_ms + " ms" : "—"}</td>
            <td class="tabular-nums">${c.uptime_pct}%</td>
            <td class="tabular-nums">${c.docs_indexed} chunks</td>
          </tr>
        `
        )
        .join("");
      return `
        <table class="telemetry-table">
          <thead>
            <tr>
              <th>Circuit Switch</th>
              <th>Service Connection &amp; Endpoint</th>
              <th>Category</th>
              <th>Security &amp; Auth</th>
              <th>Ingestion Rate</th>
              <th>P95 Latency</th>
              <th>SLA Uptime</th>
              <th>RAG Index</th>
            </tr>
          </thead>
          <tbody>${body}</tbody>
        </table>
      `;
    }

    if (persona === "developers") {
      const body = rows
        .map((r) => {
          const wdVal = (r.hours_saved * r.workday_hourly_rate).toFixed(2);
          return `
            <tr>
              <td><span class="code-badge">${escapeHtml(r.commit_sha)}</span><br/><span style="font-size:0.74rem;color:var(--text-muted);">${escapeHtml(r.branch)}</span></td>
              <td><strong>${escapeHtml(r.repository)}</strong><br/><span style="font-size:0.75rem;color:var(--accent-cyan);">Jira: ${escapeHtml(r.jira_key)} · ${escapeHtml(r.story_points)} SP</span></td>
              <td>${escapeHtml(r.author_name)}<br/><span style="font-size:0.74rem;color:var(--text-muted);">${escapeHtml(r.squad)}</span></td>
              <td><span class="code-badge">${escapeHtml(r.ci_build_id)}</span> &rarr; <strong>${escapeHtml(r.release_tag)}</strong></td>
              <td><code>${escapeHtml(r.llm_model)}</code></td>
              <td class="tabular-nums">${r.lines_ai_attributed} / ${r.lines_added} LOC (${escapeHtml(r.language)})</td>
              <td class="tabular-nums">$${Number(r.cost_usd).toFixed(4)}</td>
              <td class="tabular-nums" style="color:var(--accent-emerald);"><strong>$${wdVal}</strong> (${r.hours_saved}h)</td>
            </tr>
          `;
        })
        .join("");
      return `
        <table class="telemetry-table">
          <thead>
            <tr>
              <th>Commit &amp; Branch</th>
              <th>Repository &amp; Jira Key</th>
              <th>Developer &amp; Squad</th>
              <th>CI Build &amp; Release</th>
              <th>LLM Model</th>
              <th>AI Code Attribution</th>
              <th>Token Cost</th>
              <th>Workday Value Saved</th>
            </tr>
          </thead>
          <tbody>${body}</tbody>
        </table>
      `;
    }

    if (persona === "managers") {
      const body = rows
        .map((a) => {
          const isLow = a.value_tier === "low_value";
          return `
            <tr>
              <td><span class="kpi-delta ${isLow ? "warning" : "positive"}">${isLow ? "LOW-VALUE AUDIT" : "HIGH-VALUE ENG"}</span></td>
              <td><strong>${escapeHtml(a.task_category)}</strong><br/><span style="font-size:0.75rem;color:var(--text-muted);">${escapeHtml(a.task_summary)}</span></td>
              <td>${escapeHtml(a.department)}<br/><span style="font-size:0.74rem;color:var(--text-muted);">${escapeHtml(a.employee_level)}</span></td>
              <td><code>${escapeHtml(a.llm_model)}</code> &rarr; <strong style="color:var(--accent-emerald);">${escapeHtml(a.recommended_model)}</strong></td>
              <td class="tabular-nums">$${Number(a.actual_cost_usd).toFixed(3)} &rarr; <strong>$${Number(a.optimized_cost_usd).toFixed(3)}</strong></td>
              <td class="tabular-nums" style="color:var(--accent-emerald);"><strong>$${Number(a.workday_value_usd).toFixed(2)}</strong> (${a.hours_saved}h)</td>
              <td>${escapeHtml(a.governance_action)}</td>
            </tr>
          `;
        })
        .join("");
      return `
        <table class="telemetry-table">
          <thead>
            <tr>
              <th>Value Tier</th>
              <th>Task Category &amp; Audit Summary</th>
              <th>Department &amp; Band</th>
              <th>Model Tier Routing</th>
              <th>Cost Optimization</th>
              <th>Workday Value</th>
              <th>FinOps Governance Action</th>
            </tr>
          </thead>
          <tbody>${body}</tbody>
        </table>
      `;
    }

    // C-Suite Executive Department ROI Table
    const body = rows
      .map((d) => {
        const roi = (d.workday_value_created_usd / Math.max(d.actual_llm_spend_usd, 1)).toFixed(1);
        return `
          <tr>
            <td><strong>${escapeHtml(d.department)}</strong><br/><span style="font-size:0.74rem;color:var(--text-muted);">${escapeHtml(d.squad)}</span></td>
            <td class="tabular-nums">${d.active_ai_seats} / ${d.headcount}</td>
            <td class="tabular-nums">$${Number(d.avg_workday_salary_usd).toLocaleString()}/yr ($${Number(d.fully_loaded_hourly_usd).toFixed(2)}/hr)</td>
            <td class="tabular-nums">$${Number(d.sap_monthly_budget_usd).toLocaleString()}</td>
            <td class="tabular-nums">$${Number(d.actual_llm_spend_usd).toLocaleString()}</td>
            <td class="tabular-nums" style="color:var(--accent-cyan);"><strong>$${Number(d.flash_lite_savings_usd).toLocaleString()}/mo</strong></td>
            <td class="tabular-nums">${d.hours_reclaimed_month} hrs (${d.jira_story_points} SP)</td>
            <td class="tabular-nums" style="color:var(--accent-emerald);"><strong>$${Number(d.workday_value_created_usd).toLocaleString()} (${roi}x)</strong></td>
          </tr>
        `;
      })
      .join("");
    return `
      <table class="telemetry-table">
        <thead>
          <tr>
            <th>Business Unit &amp; Squad</th>
            <th>Active Seats</th>
            <th>Workday Comp Band</th>
            <th>SAP Budget</th>
            <th>Actual AI Spend</th>
            <th>Flash 3-8 Lite Savings</th>
            <th>Hours &amp; Jira SP</th>
            <th>Verified Workday ROI</th>
          </tr>
        </thead>
        <tbody>${body}</tbody>
      </table>
    `;
  }

  // ---------------------------------------------------------------------------
  // Interactive FinOps & Flash-Lite Scenario Simulator
  // ---------------------------------------------------------------------------
  function updateScenarioSimulator() {
    const shareSlider = document.getElementById("slider-flash-share");
    const hcSlider = document.getElementById("slider-eng-headcount");
    if (!shareSlider || !hcSlider) return;

    const flashSharePct = Number(shareSlider.value);
    const headcount = Number(hcSlider.value);

    document.getElementById("val-flash-share").textContent = `${flashSharePct}%`;
    document.getElementById("val-eng-headcount").textContent = `${headcount} seats`;

    const hcScale = headcount / 69.0;
    const unoptimizedMonthly = 60160 * hcScale;
    const flashCostFactor = 1.0 - (flashSharePct / 100.0) * 0.74;
    const projectedMonthlyBurn = Math.round(unoptimizedMonthly * flashCostFactor);
    const annualSavings = Math.round((unoptimizedMonthly - projectedMonthlyBurn) * 12);
    const workdayMonthlyValue = Math.round(286235 * hcScale * (0.85 + (flashSharePct / 100.0) * 0.2));
    const roiMultiple = (workdayMonthlyValue / Math.max(projectedMonthlyBurn, 1)).toFixed(1);

    document.getElementById("sim-monthly-burn").textContent = `$${projectedMonthlyBurn.toLocaleString()}`;
    document.getElementById("sim-annual-savings").textContent = `$${annualSavings.toLocaleString()}`;
    document.getElementById("sim-workday-value").textContent = `$${workdayMonthlyValue.toLocaleString()}/mo`;
    document.getElementById("sim-roi-multiple").textContent = `${roiMultiple}x`;
  }

  // ---------------------------------------------------------------------------
  // Enterprise Hybrid Search & Google Flash 3-8 Fast Lite RAG Studio
  // ---------------------------------------------------------------------------
  async function runEnterpriseSearch() {
    try {
      const q = (document.getElementById("search-query-input")?.value || "").trim();
      const persona = document.getElementById("search-filter-persona")?.value || "all";
      const sourceType = document.getElementById("search-filter-type")?.value || "all";
      const sortBy = document.getElementById("search-filter-sort")?.value || "hybrid";
      const activeOnly = Boolean(document.getElementById("chk-search-active-only")?.checked);

      const params = new URLSearchParams({
        q,
        persona,
        source_type: sourceType,
        sort_by: sortBy,
        active_only: String(activeOnly),
        top_k: "20",
      });

      const data = await apiFetch(`/api/search?${params.toString()}`);
      state.lastSearchResults = data;
      renderSearchResults(data);
    } catch (err) {
      showToast(`Search error: ${err.message}`, "coral");
    }
  }

  function renderSearchResults(data) {
    const latBadge = document.getElementById("search-latency-badge");
    if (latBadge) latBadge.textContent = `${data.latency_ms} ms · ${data.total_matches} hits`;

    const ragBadge = document.getElementById("badge-rag-docs");
    if (ragBadge && data.index_stats) {
      ragBadge.textContent = `${data.index_stats.corpus_size} Chunks`;
    }

    const statusLine = document.getElementById("search-index-status-line");
    if (statusLine && data.index_stats) {
      statusLine.textContent = `Indexed ${data.index_stats.corpus_size} RAG chunks (${data.index_stats.vocabulary_size} vocab terms, ${data.index_stats.embedding_dim}-dim SVD vectors)`;
    }

    const exclBanner = document.getElementById("search-excluded-banner");
    if (exclBanner) {
      if (data.excluded_offline_docs > 0) {
        exclBanner.style.display = "block";
        exclBanner.innerHTML = `<strong>Circuit Isolation Active:</strong> ${data.excluded_offline_docs} document(s) from paused/OFF connection(s) (${escapeHtml(
          (data.excluded_connections || []).join(", ")
        )}) were excluded from live search. Turn them ON or uncheck "Only Active Connections" to include.`;
      } else {
        exclBanner.style.display = "none";
      }
    }

    const container = document.getElementById("search-results-container");
    if (!container) return;

    if (!data.results || !data.results.length) {
      container.innerHTML = `<div class="search-hit-card"><p>No matching enterprise artifacts found. Try broadening filters or enabling paused service connections.</p></div>`;
      return;
    }

    container.innerHTML = data.results
      .map(
        (hit) => `
        <article class="search-hit-card" id="search-hit-${escapeHtml(hit.id)}">
          <div class="search-hit-top">
            <div>
              <span class="code-badge">${escapeHtml(hit.id)}</span>
              <span class="code-badge" style="color:var(--accent-cyan);">${escapeHtml(hit.connection_name)}</span>
              <span class="code-badge">${escapeHtml(hit.source_type)}</span>
            </div>
            <div class="search-score-pills">
              <span class="kpi-delta positive">Hybrid: ${hit.hybrid_score}</span>
              <span class="code-badge">BM25: ${hit.bm25_score}</span>
              <span class="code-badge">Vec: ${hit.vector_score}</span>
            </div>
          </div>
          <h3 class="search-hit-title">${escapeHtml(hit.title)}</h3>
          <p class="search-snippet">${hit.snippet}</p>
          <div style="display:flex;justify-content:space-between;align-items:center;margin-top:0.25rem;">
            <span style="font-size:0.74rem;color:var(--text-muted);">Dept: ${escapeHtml(hit.department)} · Personas: ${escapeHtml((hit.persona_tags || []).join(", "))}</span>
            <button
              type="button"
              class="btn btn-sm btn-emerald"
              data-action="ask-about-doc"
              data-doc-title="${escapeHtml(hit.title)}"
              data-doc-id="${escapeHtml(hit.id)}"
            >
              Ask Flash-Lite About [${escapeHtml(hit.id)}]
            </button>
          </div>
        </article>
      `
      )
      .join("");
  }

  // ---------------------------------------------------------------------------
  // Google Flash 3-8 Fast Lite RAG Chat & Synthesis
  // ---------------------------------------------------------------------------
  async function runFlashLiteChat(customPrompt = null) {
    const inputEl = document.getElementById("llm-prompt-input");
    const prompt = customPrompt !== null ? customPrompt : (inputEl?.value || "").trim();
    if (!prompt) return;
    if (customPrompt !== null && inputEl) {
      inputEl.value = customPrompt;
    }

    const modelId = document.getElementById("llm-model-select")?.value || "google/gemini-3-8-flash-lite";
    const persona = document.getElementById("llm-persona-select")?.value || state.activePersona || "csuite";
    const topK = Number(document.getElementById("llm-topk-select")?.value || 5);
    const activeOnly = Boolean(document.getElementById("chk-search-active-only")?.checked ?? true);

    const respBox = document.getElementById("llm-response-container");
    if (respBox) {
      respBox.innerHTML = `<p style="color:var(--accent-cyan);">Retrieving Top-${topK} RAG chunks from active service connections and synthesizing via <code>${escapeHtml(
        modelId
      )}</code>...</p>`;
    }

    try {
      const data = await apiFetch("/api/llm/chat", {
        method: "POST",
        body: JSON.stringify({
          prompt,
          model_id: modelId,
          persona,
          top_k: topK,
          active_only: activeOnly,
        }),
      });

      if (respBox) {
        respBox.innerHTML = renderMarkdownToHtml(data.answer || "");
      }

      const tel = data.telemetry || {};
      document.getElementById("tel-model-name").textContent =
        data.model?.id === "google/gemini-3-8-flash-lite" ? "Flash 3-8 Fast Lite" : data.model?.display_name || modelId;
      document.getElementById("tel-latency").textContent = `${tel.total_latency_ms} ms`;
      document.getElementById("tel-tokens").textContent = `${tel.prompt_tokens} / ${tel.rag_context_tokens} / ${tel.output_tokens}`;
      document.getElementById("tel-cost").textContent = `$${Number(tel.cost_usd || 0).toFixed(6)}`;
      document.getElementById("tel-savings").textContent = `${tel.cost_savings_pct}% Saved`;

      const citWrap = document.getElementById("llm-citations-container");
      if (citWrap) {
        citWrap.innerHTML = (data.citations || [])
          .map(
            (c) => `
            <div style="display:flex;align-items:center;justify-content:space-between;gap:0.5rem;padding:0.45rem 0.65rem;background:var(--bg-elevated);border:1px solid var(--border-subtle);border-radius:6px;font-size:0.78rem;">
              <span>
                <strong style="color:var(--accent-emerald);">[${escapeHtml(c.id)}]</strong>
                <strong>${escapeHtml(c.title)}</strong>
                <span style="color:var(--text-muted);">(${escapeHtml(c.connection_name)})</span>
              </span>
              <span class="code-badge">Score: ${c.hybrid_score}</span>
            </div>
          `
          )
          .join("");
      }
    } catch (err) {
      if (respBox) {
        respBox.innerHTML = `<p style="color:var(--accent-coral);">Inference error: ${escapeHtml(err.message)}</p>`;
      }
    }
  }

  function renderMarkdownToHtml(md) {
    const lines = String(md || "").split("\n");
    let html = "";
    let inTable = false;
    let inList = false;

    const formatInline = (text) => {
      let s = escapeHtml(text);
      s = s.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
      s = s.replace(/\*(.+?)\*/g, "<em>$1</em>");
      s = s.replace(/`([^`]+)`/g, '<code class="code-badge">$1</code>');
      s = s.replace(
        /\[([A-Z]+-\d+[A-Z0-9_-]*)\]/g,
        '<span class="nav-badge" style="margin:0 2px;">[$1]</span>'
      );
      return s;
    };

    for (let i = 0; i < lines.length; i++) {
      const raw = lines[i].trim();
      if (!raw) {
        if (inTable) {
          html += "</tbody></table>";
          inTable = false;
        }
        if (inList) {
          html += "</ul>";
          inList = false;
        }
        continue;
      }

      if (raw.startsWith("|") && raw.endsWith("|")) {
        if (inList) {
          html += "</ul>";
          inList = false;
        }
        const cells = raw
          .slice(1, -1)
          .split("|")
          .map((c) => c.trim());
        if (cells.every((c) => /^[:\-]+$/.test(c))) {
          continue;
        }
        if (!inTable) {
          html += "<table><thead><tr>" + cells.map((c) => `<th>${formatInline(c)}</th>`).join("") + "</tr></thead><tbody>";
          inTable = true;
        } else {
          html += "<tr>" + cells.map((c) => `<td>${formatInline(c)}</td>`).join("") + "</tr>";
        }
        continue;
      } else if (inTable) {
        html += "</tbody></table>";
        inTable = false;
      }

      if (raw.startsWith("### ")) {
        if (inList) {
          html += "</ul>";
          inList = false;
        }
        html += `<h3>${formatInline(raw.slice(4))}</h3>`;
      } else if (raw.startsWith("#### ")) {
        if (inList) {
          html += "</ul>";
          inList = false;
        }
        html += `<h4>${formatInline(raw.slice(5))}</h4>`;
      } else if (raw.startsWith("> ")) {
        if (inList) {
          html += "</ul>";
          inList = false;
        }
        html += `<blockquote>${formatInline(raw.slice(2))}</blockquote>`;
      } else if (raw.startsWith("- ")) {
        if (!inList) {
          html += '<ul style="padding-left:1.25rem;margin:0.4rem 0;">';
          inList = true;
        }
        html += `<li style="margin-bottom:0.3rem;">${formatInline(raw.slice(2))}</li>`;
      } else {
        if (inList) {
          html += "</ul>";
          inList = false;
        }
        html += `<p style="margin:0.45rem 0;">${formatInline(raw)}</p>`;
      }
    }

    if (inTable) html += "</tbody></table>";
    if (inList) html += "</ul>";
    return html;
  }

  async function ingestCustomRagDoc() {
    const title = (document.getElementById("ingest-doc-title")?.value || "").trim();
    const content = (document.getElementById("ingest-doc-content")?.value || "").trim();
    const connectionId = document.getElementById("ingest-doc-connection")?.value || "conn-gemini-flash-lite";
    const department = document.getElementById("ingest-doc-department")?.value || "Data & AI Platform";
    const chunkStrategy = document.getElementById("ingest-chunk-strategy")?.value || "semantic";

    if (!title || !content) {
      showToast("Please provide both a document title and content to ingest.", "amber");
      return;
    }

    try {
      const res = await apiFetch("/api/rag/ingest", {
        method: "POST",
        body: JSON.stringify({
          title,
          content,
          connection_id: connectionId,
          department,
          chunk_strategy: chunkStrategy,
        }),
      });
      showToast(
        `Ingested ${res.chunks_created} chunk(s) (${res.created_doc_ids.join(", ")}) into Flash 3-8 Lite RAG Index!`,
        "emerald"
      );
      document.getElementById("ingest-doc-title").value = "";
      document.getElementById("ingest-doc-content").value = "";
      await loadConnections();
      await runEnterpriseSearch();
    } catch (err) {
      showToast(`Ingest failed: ${err.message}`, "coral");
    }
  }

  async function trainFlashLiteAdapter() {
    try {
      const res = await apiFetch("/api/rag/train", {
        method: "POST",
        body: JSON.stringify({
          model_id: "google/gemini-3-8-flash-lite",
          adapter_name: `burniq-flash-3-8-fast-lite-rag-v2.${Math.floor(Math.random() * 5) + 5}`,
        }),
      });
      const run = res.training_run;
      const statusText = document.getElementById("rag-training-status-text");
      if (statusText) {
        statusText.innerHTML = `Adapter: <code>${escapeHtml(run.adapter_name)}</code> · Recall@5: <strong>${(
          run.retrieval_recall_at_5 * 100
        ).toFixed(1)}%</strong> · MRR: <strong>${(run.mrr_score * 100).toFixed(1)}%</strong> (${run.training_duration_ms}ms)`;
      }
      showToast(
        `Trained ${run.adapter_name} across ${run.active_connections_count} active connections (${run.documents_indexed} chunks, Recall@5 ${(
          run.retrieval_recall_at_5 * 100
        ).toFixed(1)}%)!`,
        "emerald"
      );
      await runEnterpriseSearch();
    } catch (err) {
      showToast(`Training error: ${err.message}`, "coral");
    }
  }

  // ---------------------------------------------------------------------------
  // Event Listeners & Initialization
  // ---------------------------------------------------------------------------
  function bindEvents() {
    // Primary Nav Tabs
    document.querySelectorAll(".nav-tab").forEach((btn) => {
      btn.addEventListener("click", () => switchView(btn.dataset.view));
    });

    // Persona Cards
    document.querySelectorAll(".persona-card-btn").forEach((btn) => {
      btn.addEventListener("click", () => switchPersona(btn.dataset.persona));
    });

    // Quick Search Trigger & Ctrl+K
    document.getElementById("btn-header-quick-search")?.addEventListener("click", () => {
      switchView("search-rag");
      document.getElementById("search-query-input")?.focus();
    });

    window.addEventListener("keydown", (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        switchView("search-rag");
        document.getElementById("search-query-input")?.focus();
      }
    });

    // Theme Toggle
    document.getElementById("btn-theme-toggle")?.addEventListener("click", () => {
      const html = document.documentElement;
      const next = html.getAttribute("data-theme") === "light" ? "dark" : "light";
      html.setAttribute("data-theme", next);
      document.getElementById("theme-toggle-label").textContent = next === "light" ? "Dark Mode" : "Light Mode";
    });

    // Dashboard Filters
    document.getElementById("select-dashboard-timeframe")?.addEventListener("change", (e) => {
      state.timeframe = e.target.value;
      loadPersonaDashboard();
    });
    document.getElementById("select-dashboard-department")?.addEventListener("change", (e) => {
      state.department = e.target.value;
      loadPersonaDashboard();
    });

    // Analyze Persona View with Flash-Lite button
    document.getElementById("btn-ask-persona-ai")?.addEventListener("click", () => {
      const personaPrompts = {
        techops: "Show Technical Ops health across active service connections, P95 latency for Flash 3-8 Fast Lite, and ServiceNow P1 MTTR.",
        developers: "Trace our code-to-release attribution across GitHub, GitLab, Bitbucket commits, Jenkins/Bamboo CI builds, and Jira story points.",
        managers: "Analyze low-value email and meeting note LLM waste across departments and how routing to Google Flash 3-8 Fast Lite cuts spend.",
        csuite: "Summarize our Net Enterprise ROI comparing Workday payroll value against SAP AI spend and Google Flash 3-8 Fast Lite savings.",
      };
      const llmPersonaEl = document.getElementById("llm-persona-select");
      if (llmPersonaEl) llmPersonaEl.value = state.activePersona;
      switchView("search-rag");
      runFlashLiteChat(personaPrompts[state.activePersona]);
    });

    // Scenario Simulator Sliders
    document.getElementById("slider-flash-share")?.addEventListener("input", updateScenarioSimulator);
    document.getElementById("slider-eng-headcount")?.addEventListener("input", updateScenarioSimulator);

    // Connections View Filters & Bulk Actions
    document.getElementById("select-conn-category")?.addEventListener("change", (e) => {
      state.connCategory = e.target.value;
      loadConnections();
    });
    document.getElementById("select-conn-status")?.addEventListener("change", (e) => {
      state.connStatus = e.target.value;
      loadConnections();
    });
    document.getElementById("btn-bulk-turn-on")?.addEventListener("click", () => bulkToggleConnections(true, true));
    document.getElementById("btn-bulk-turn-off")?.addEventListener("click", () => bulkToggleConnections(false, true));
    document.getElementById("btn-strip-all-on")?.addEventListener("click", () => bulkToggleConnections(true, false));
    document.getElementById("btn-strip-all-off")?.addEventListener("click", () => bulkToggleConnections(false, false));

    // Delegated Clicks for Service Connection Toggles, Test, Sync, and Ask Doc
    document.body.addEventListener("click", (e) => {
      const actionBtn = e.target.closest("[data-action]");
      if (!actionBtn) return;

      const action = actionBtn.dataset.action;
      const connId = actionBtn.dataset.connId;

      if (action === "toggle-conn" && connId) {
        toggleConnectionState(connId);
      } else if (action === "test-conn" && connId) {
        testConnection(connId);
      } else if (action === "sync-conn" && connId) {
        syncConnection(connId);
      } else if (action === "ask-about-doc") {
        const docId = actionBtn.dataset.docId;
        const docTitle = actionBtn.dataset.docTitle;
        runFlashLiteChat(`Provide a detailed breakdown of [${docId}] (${docTitle}) and its impact on ROI and operations.`);
      }
    });

    document.body.addEventListener("change", (e) => {
      const ragChk = e.target.closest('[data-action="toggle-rag"]');
      if (ragChk && ragChk.dataset.connId) {
        toggleConnectionState(ragChk.dataset.connId, null, ragChk.checked);
      }
    });

    // Search & RAG Controls
    document.getElementById("btn-run-search")?.addEventListener("click", runEnterpriseSearch);
    document.getElementById("search-query-input")?.addEventListener("input", () => {
      clearTimeout(window._searchTimer);
      window._searchTimer = setTimeout(runEnterpriseSearch, 220);
    });
    ["search-filter-persona", "search-filter-type", "search-filter-sort", "chk-search-active-only"].forEach((id) => {
      document.getElementById(id)?.addEventListener("change", runEnterpriseSearch);
    });

    // LLM Chat Controls
    document.getElementById("btn-ask-flash-lite")?.addEventListener("click", () => runFlashLiteChat());
    document.getElementById("llm-prompt-input")?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        runFlashLiteChat();
      }
    });
    document.querySelectorAll(".prompt-chip").forEach((chip) => {
      chip.addEventListener("click", () => {
        runFlashLiteChat(chip.dataset.prompt);
      });
    });

    // RAG Ingest & Train
    document.getElementById("btn-ingest-rag-doc")?.addEventListener("click", ingestCustomRagDoc);
    document.getElementById("btn-train-rag-adapter")?.addEventListener("click", trainFlashLiteAdapter);

    // Export CSV
    document.getElementById("btn-export-table-csv")?.addEventListener("click", () => {
      const rows = state.dashboardData?.table_rows || [];
      if (!rows.length) return;
      const headers = Object.keys(rows[0]);
      const csv = [
        headers.join(","),
        ...rows.map((r) => headers.map((h) => JSON.stringify(r[h] ?? "")).join(",")),
      ].join("\n");
      const blob = new Blob([csv], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `burniq-${state.activePersona}-${state.timeframe}.csv`;
      a.click();
      URL.revokeObjectURL(url);
      showToast(`Exported ${rows.length} rows to CSV`, "emerald");
    });
  }

  async function init() {
    bindEvents();
    updateScenarioSimulator();
    await Promise.all([loadConnections(), loadPersonaDashboard()]);
    // Pre-populate the Flash-Lite RAG Studio response so it is immediately ready when inspected
    runEnterpriseSearch();
    runFlashLiteChat();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
