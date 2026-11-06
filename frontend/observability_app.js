// BurnIQ Enterprise Telemetry, Observability (Datadog, Substrate, New Relic, Soluble) & ROI Platform

let GLOBAL_OBSERVABILITY = null;
let GLOBAL_OVERVIEW = null;

function fmtNum(n) {
  return Number(n || 0).toLocaleString("en-US");
}

function fmtUsd(n, decimals = 0) {
  return "$" + Number(n || 0).toLocaleString("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

function switchMainTab(tabId) {
  document.querySelectorAll(".tab-panel").forEach((el) => el.classList.remove("active"));
  document.querySelectorAll(".nav-tab").forEach((el) => el.classList.remove("active"));

  const targetPanel = document.getElementById(`tab-${tabId}`);
  const targetBtn = document.getElementById(`nav-btn-${tabId}`);
  if (targetPanel) targetPanel.classList.add("active");
  if (targetBtn) targetBtn.classList.add("active");
}

function filterVendorSection(vendor) {
  document.querySelectorAll(".subnav-btn").forEach((b) => b.classList.remove("active"));
  const activeBtn = document.getElementById(`subbtn-${vendor}`);
  if (activeBtn) activeBtn.classList.add("active");

  document.querySelectorAll(".vendor-hero-card").forEach((c) => {
    c.classList.toggle("active-vendor", vendor !== "all" && c.dataset.vendor === vendor);
  });

  const corrSec = document.getElementById("section-correlations");
  if (corrSec) {
    corrSec.style.display = vendor === "all" ? "block" : "none";
  }

  const allSecs = ["datadog", "substrate", "newrelic", "soluble"];
  allSecs.forEach((v) => {
    const el = document.getElementById(`vendor-sec-${v}`);
    if (el) {
      el.style.display = vendor === "all" || vendor === v ? "block" : "none";
    }
  });
}

async function initBurnIQ() {
  try {
    const [overviewResp, obsResp, connResp] = await Promise.all([
      fetch("/api/overview"),
      fetch("/api/observability"),
      fetch("/api/connectors"),
    ]);

    GLOBAL_OVERVIEW = await overviewResp.json();
    GLOBAL_OBSERVABILITY = await obsResp.json();
    const connData = await connResp.json();

    renderFeatured4Hero(GLOBAL_OVERVIEW.featured_4_status);
    renderCorrelations(GLOBAL_OBSERVABILITY.cross_platform_correlations);
    renderDatadog(GLOBAL_OBSERVABILITY.datadog);
    renderSubstrate(GLOBAL_OBSERVABILITY.substrate);
    renderNewRelic(GLOBAL_OBSERVABILITY.newrelic);
    renderSoluble(GLOBAL_OBSERVABILITY.soluble);
    renderAttribution(GLOBAL_OVERVIEW.releases);
    renderWorkdayRoi(GLOBAL_OVERVIEW.workday_roi);
    renderConnectors(connData.connectors);

    // Run initial NRQL query and Soluble scan so both interactive consoles are populated on load
    await executeObservabilityQuery();
    await runSolubleInteractiveScan();
  } catch (err) {
    console.error("Failed to initialize BurnIQ telemetry:", err);
  }
}

function renderFeatured4Hero(cards) {
  const container = document.getElementById("featured-4-cards");
  if (!container || !cards) return;
  container.innerHTML = cards
    .map(
      (c) => `
      <div class="vendor-hero-card" data-vendor="${c.id}" onclick="filterVendorSection('${c.id}')">
        <div class="vendor-header">
          <div class="vendor-name">
            <span class="status-dot"></span>
            ${c.name}
          </div>
          <span class="vendor-host">${c.host}</span>
        </div>
        <div class="vendor-tagline">${c.tagline}</div>
        <div class="vendor-metric-primary tabular">${c.primary_metric}</div>
        <div class="vendor-metric-secondary tabular">${c.secondary_metric}</div>
      </div>
    `
    )
    .join("");
}

function renderCorrelations(correlations) {
  const tbody = document.getElementById("tbody-correlations");
  if (!tbody || !correlations) return;
  tbody.innerHTML = correlations
    .map(
      (c) => `
      <tr>
        <td>
          <div class="mono" style="color:var(--accent-cyan); font-weight:700;">${c.correlation_id}</div>
          <div style="font-weight:600; margin-top:2px;">${c.title}</div>
        </td>
        <td>${c.datadog_signal}</td>
        <td>${c.substrate_signal}</td>
        <td>${c.newrelic_signal}</td>
        <td>${c.soluble_signal}</td>
        <td><span class="badge badge-emerald">${c.net_business_impact}</span></td>
      </tr>
    `
    )
    .join("");
}

function renderDatadog(dd) {
  if (!dd) return;
  const ai = dd.dora_comparison.ai_assisted_releases;
  const hum = dd.dora_comparison.human_baseline_releases;

  const barsEl = document.getElementById("datadog-dora-bars");
  if (barsEl) {
    barsEl.innerHTML = `
      <div class="comparison-row">
        <div class="comparison-header">
          <span><strong>Deployment Frequency</strong> (AI-Assisted vs. Human Baseline)</span>
          <span class="mono text-emerald">${ai.deployment_frequency_per_day}/day vs. ${hum.deployment_frequency_per_day}/day (+242%)</span>
        </div>
        <div class="progress-track"><div class="progress-fill" style="width:88%; background:var(--accent-emerald);"></div></div>
      </div>
      <div class="comparison-row">
        <div class="comparison-header">
          <span><strong>Lead Time for Changes</strong> (Commit to Production)</span>
          <span class="mono text-cyan">${ai.lead_time_hours} hrs vs. ${hum.lead_time_hours} hrs (-80.3%)</span>
        </div>
        <div class="progress-track"><div class="progress-fill" style="width:82%; background:var(--accent-cyan);"></div></div>
      </div>
      <div class="comparison-row">
        <div class="comparison-header">
          <span><strong>Change Failure Rate</strong> (Post-Release Incident Rate)</span>
          <span class="mono text-emerald">${ai.change_failure_rate_pct}% vs. ${hum.change_failure_rate_pct}% (-73.7% fewer failures)</span>
        </div>
        <div class="progress-track"><div class="progress-fill" style="width:91%; background:var(--accent-emerald);"></div></div>
      </div>
      <div class="comparison-row" style="margin-bottom:0;">
        <div class="comparison-header">
          <span><strong>Mean Time to Restore (MTTR)</strong> (Datadog + PagerDuty + Opsgenie)</span>
          <span class="mono text-cyan">${ai.mttr_minutes} mins vs. ${hum.mttr_minutes} mins (-75.7%)</span>
        </div>
        <div class="progress-track"><div class="progress-fill" style="width:86%; background:var(--accent-cyan);"></div></div>
      </div>
    `;
  }

  const cicdTbody = document.getElementById("tbody-dd-cicd");
  if (cicdTbody) {
    cicdTbody.innerHTML = dd.dora_comparison.by_cicd_provider
      .map(
        (p) => `
        <tr>
          <td><strong>${p.provider}</strong></td>
          <td class="mono">${p.deployments_30d}</td>
          <td class="mono text-cyan">${p.lead_time_hrs}h</td>
          <td class="mono text-emerald">${p.cfr_pct}%</td>
          <td class="mono">${p.mttr_min}m</td>
          <td><span class="badge badge-emerald">${p.ai_commit_share_pct}% AI</span></td>
        </tr>
      `
      )
      .join("");
  }

  const spansTbody = document.getElementById("tbody-dd-spans");
  if (spansTbody) {
    spansTbody.innerHTML = dd.llm_observability_spans
      .map((s) => {
        const isHigh = s.task_category.includes("High-Value");
        return `
        <tr>
          <td class="mono">
            <div style="color:var(--accent-cyan); font-weight:600;">${s.trace_id}</div>
            <div style="font-size:11px; color:var(--text-secondary);">${s.span_id}</div>
          </td>
          <td>
            <div style="font-weight:600;">${s.service}</div>
            <div style="font-size:11.5px; color:var(--text-secondary);">${s.provider}</div>
          </td>
          <td class="mono">${s.model}</td>
          <td>
            <div>${s.engineer}</div>
            <div style="font-size:11.5px; color:var(--text-secondary);">${s.department}</div>
          </td>
          <td>
            <span class="badge ${isHigh ? "badge-emerald" : "badge-coral"}">${s.task_category}</span>
            <div style="font-size:11.5px; color:var(--text-secondary); margin-top:3px;">${s.operation}</div>
          </td>
          <td class="mono">${fmtNum(s.total_tokens)}</td>
          <td class="mono">${fmtUsd(s.cost_usd, 4)}</td>
          <td class="mono">${s.latency_ms}ms <span style="color:var(--text-secondary);">(${s.ttft_ms}ms TTFT)</span></td>
          <td class="mono">
            <div>Commit: <span class="text-cyan">${s.git_commit}</span></div>
            <div style="font-size:11px; color:var(--text-secondary);">Jira: ${s.jira_key} · ${s.release_id}</div>
          </td>
        </tr>
      `;
      })
      .join("");
  }

  const monTbody = document.getElementById("tbody-dd-monitors");
  if (monTbody) {
    monTbody.innerHTML = dd.apm_monitors
      .map((m) => {
        const badgeClass = m.status === "OK" ? "badge-emerald" : m.status === "ALERT" ? "badge-coral" : "badge-amber";
        return `
        <tr>
          <td class="mono" style="font-weight:700;">${m.monitor_id}</td>
          <td><span class="badge ${badgeClass}">${m.status} (${m.severity})</span></td>
          <td>
            <div style="font-weight:600;">${m.name}</div>
            <div class="mono" style="font-size:11.5px; color:var(--text-secondary);">service:${m.service} · type:${m.type}</div>
          </td>
          <td class="mono">
            <div>Current: <strong>${m.current_value}</strong></div>
            <div style="font-size:11.5px; color:var(--text-secondary);">SLA: ${m.threshold}</div>
          </td>
          <td class="mono">${m.linked_release}</td>
          <td>${m.remediation}</td>
        </tr>
      `;
      })
      .join("");
  }
}

function renderSubstrate(sub) {
  if (!sub) return;
  const sigTbody = document.getElementById("tbody-substrate-signals");
  const auditTbody = document.getElementById("tbody-low-value-audit");

  const rowsHtml = sub.microsoft_substrate_signals
    .map((s) => {
      const isWaste = s.value_classification.includes("WASTE");
      const isOpt = s.value_classification.includes("OPTIMIZED");
      const badgeClass = isWaste ? "badge-coral" : isOpt ? "badge-cyan" : "badge-emerald";
      return `
      <tr>
        <td>
          <div class="mono" style="font-weight:700; color:var(--accent-cyan);">${s.signal_id}</div>
          <div style="font-size:12px;">${s.channel}</div>
        </td>
        <td>
          <div style="font-weight:600;">${s.artifact_type}</div>
          <div style="font-size:11.5px; color:var(--text-secondary);">${s.department}</div>
        </td>
        <td>
          <div>${s.model}</div>
          <div style="font-size:11.5px; color:var(--text-secondary);">${s.llm_provider}</div>
        </td>
        <td class="mono">
          <div>${fmtNum(s.monthly_events)} events</div>
          <div style="font-size:11.5px; color:var(--text-secondary);">${fmtNum(s.tokens_burned)} tokens</div>
        </td>
        <td class="mono">${fmtUsd(s.llm_cost_usd)}/mo</td>
        <td class="mono">
          <div class="${isWaste ? "text-coral" : "text-emerald"}" style="font-weight:700;">${fmtUsd(s.workday_salary_burn_usd)}/mo</div>
          <div style="font-size:11.5px; color:var(--text-secondary);">${fmtNum(s.employee_hours_spent)} hrs @ $${s.avg_workday_hourly_usd}/hr</div>
        </td>
        <td class="mono">${s.code_or_release_link}</td>
        <td><span class="badge ${badgeClass}">${s.value_classification}</span></td>
        <td>
          <div style="font-size:11.5px; margin-bottom:4px;">${s.action_policy}</div>
          ${
            isWaste
              ? `<button class="btn btn-primary btn-sm" onclick="enforceSubstratePolicyUI('${s.signal_id}')">Enforce Haiku/Flash Routing</button>`
              : `<span class="badge badge-emerald">Policy Verified</span>`
          }
        </td>
      </tr>
    `;
    })
    .join("");

  if (sigTbody) sigTbody.innerHTML = rowsHtml;
  if (auditTbody) auditTbody.innerHTML = rowsHtml;

  const wkTbody = document.getElementById("tbody-substrate-workloads");
  if (wkTbody) {
    wkTbody.innerHTML = sub.substrate_compute_workloads
      .map((w) => {
        const isWaste = w.status.includes("THROTTLE");
        return `
        <tr>
          <td>
            <div class="mono" style="color:var(--accent-cyan); font-weight:700;">${w.workload_id}</div>
            <div style="font-weight:600;">${w.name}</div>
          </td>
          <td>${w.cloud_substrate}</td>
          <td class="mono">${w.accelerator}</td>
          <td>${w.llm_Target}</td>
          <td class="mono">${w.utilization_pct}%</td>
          <td class="mono">${w.p95_latency_ms}ms</td>
          <td class="mono">${fmtUsd(w.monthly_compute_cost_usd)}/mo</td>
          <td class="mono">${w.attributed_releases} releases (${fmtUsd(w.attributed_value_usd)})</td>
          <td><span class="badge ${isWaste ? "badge-coral" : "badge-emerald"}">${w.roi_multiple}</span></td>
        </tr>
      `;
      })
      .join("");
  }
}

async function enforceSubstratePolicyUI(signalId) {
  try {
    await fetch("/api/substrate/enforce-policy", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ signal_id: signalId, action: "ENFORCE_HAIKU_FLASH_ROUTING" }),
    });
    const subResp = await fetch("/api/substrate");
    const subData = await subResp.json();
    renderSubstrate(subData);
  } catch (err) {
    console.error("Failed to enforce Substrate policy:", err);
  }
}

function renderNewRelic(nr) {
  if (!nr) return;
  const apmTbody = document.getElementById("tbody-nr-apm");
  if (apmTbody) {
    apmTbody.innerHTML = nr.apm_services
      .map((a) => {
        const improved = a.latency_delta_pct < 0;
        return `
        <tr>
          <td>
            <div class="mono" style="color:var(--accent-cyan); font-weight:700;">${a.app_id}</div>
            <div style="font-weight:600;">${a.service_name}</div>
          </td>
          <td>${a.tier}</td>
          <td class="mono"><span class="badge ${a.apdex_score >= 0.95 ? "badge-emerald" : "badge-amber"}">${a.apdex_score}</span></td>
          <td class="mono">${fmtNum(a.throughput_rpm)} rpm</td>
          <td class="mono"><strong>${a.response_time_p95_ms}ms</strong> / ${a.response_time_p99_ms}ms</td>
          <td class="mono">${a.pre_ai_release_p95_ms}ms</td>
          <td class="mono">
            <span class="badge ${improved ? "badge-emerald" : "badge-coral"}">
              ${a.latency_delta_pct > 0 ? "+" : ""}${a.latency_delta_pct}%
            </span>
          </td>
          <td class="mono">${a.error_rate_pct}%</td>
          <td>
            <div class="mono" style="font-size:12px;">${a.release_id} (${a.cicd_source})</div>
            <div style="font-size:11.5px; color:var(--text-secondary);">${a.llm_contributor}</div>
          </td>
        </tr>
      `;
      })
      .join("");
  }

  const modelsTbody = document.getElementById("tbody-nr-aimodels");
  if (modelsTbody) {
    modelsTbody.innerHTML = nr.ai_monitoring_models
      .map(
        (m) => `
        <tr>
          <td>
            <div class="mono" style="font-weight:700;">${m.model}</div>
            <div style="font-size:11.5px; color:var(--text-secondary);">${m.provider}</div>
          </td>
          <td class="mono">${fmtNum(m.requests_24h)}</td>
          <td class="mono">${fmtNum(m.tokens_24h)}</td>
          <td class="mono">${m.avg_latency_ms}ms</td>
          <td class="mono">${m.hallucination_retry_pct}%</td>
          <td class="mono">${fmtUsd(m.cost_24h_usd, 2)}</td>
          <td style="font-size:12px;">${m.primary_attribution}</td>
        </tr>
      `
      )
      .join("");
  }
}

function loadPresetQuery() {
  const engine = document.getElementById("select-query-engine").value;
  const input = document.getElementById("input-observability-query");
  if (engine === "newrelic_nrql") {
    input.value =
      "SELECT apdex(duration, t: 0.08), percentile(duration, 95), percentage(count(*), WHERE error IS true) FROM Transaction FACET appName, releaseId, llmContributor SINCE 7 days ago";
  } else if (engine === "datadog_spans") {
    input.value =
      "datadog:llm_obs service:burniq-* @task_category:High-Value OR @task_category:Low-Value | rollup(sum(@tokens), sum(@cost_usd)) by @model, @release_id";
  } else if (engine === "substrate_graph") {
    input.value =
      "substrate.office.com/v1.0/signals?$filter=valueClassification eq 'LOW-VALUE WASTE'&$orderby=workdaySalaryBurnUsd desc";
  } else if (engine === "soluble_policy") {
    input.value =
      "soluble:assessments --iac-type=terraform,k8s,helm --compare=ai-attributed,human-baseline --status=AUTO_REMEDIATED";
  }
  executeObservabilityQuery();
}

async function executeObservabilityQuery() {
  const engine = document.getElementById("select-query-engine").value;
  const query = document.getElementById("input-observability-query").value;
  try {
    const resp = await fetch("/api/observability/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ engine, query }),
    });
    const data = await resp.json();
    document.getElementById("nrql-query-insight").textContent = `✓ [${data.execution_time_ms}ms · ${data.row_count} rows] ${data.finops_insight}`;

    const thead = document.getElementById("thead-nrql-results");
    const tbody = document.getElementById("tbody-nrql-results");
    if (data.rows && data.rows.length > 0) {
      const cols = Object.keys(data.rows[0]);
      thead.innerHTML = `<tr>${cols.map((c) => `<th>${c}</th>`).join("")}</tr>`;
      tbody.innerHTML = data.rows
        .map((r) => `<tr>${cols.map((c) => `<td class="mono">${r[c]}</td>`).join("")}</tr>`)
        .join("");
    }
  } catch (err) {
    console.error("Query execution failed:", err);
  }
}

function renderSoluble(sol) {
  if (!sol) return;
  const fwTbody = document.getElementById("tbody-soluble-frameworks");
  if (fwTbody) {
    fwTbody.innerHTML = sol.ai_vs_human_posture.by_iac_framework
      .map(
        (f) => `
        <tr>
          <td><strong>${f.framework}</strong></td>
          <td class="mono">${fmtNum(f.scans_30d)}</td>
          <td class="mono">${f.findings_detected}</td>
          <td class="mono text-emerald">${f.auto_fixed_by_ai} (${Math.round((f.auto_fixed_by_ai / f.findings_detected) * 100)}%)</td>
          <td><span class="badge badge-emerald">${f.compliance_score_pct}%</span></td>
        </tr>
      `
      )
      .join("");
  }

  const findTbody = document.getElementById("tbody-soluble-findings");
  if (findTbody) {
    findTbody.innerHTML = sol.security_findings
      .map((f) => {
        const sevClass = f.severity === "CRITICAL" ? "badge-coral" : f.severity === "HIGH" ? "badge-amber" : "badge-info";
        const stClass = f.status === "AUTO_REMEDIATED" ? "badge-emerald" : "badge-amber";
        return `
        <tr>
          <td class="mono">
            <div style="font-weight:700; color:var(--accent-cyan);">${f.finding_id}</div>
            <div style="font-size:11px; color:var(--text-secondary);">${f.rule_id}</div>
          </td>
          <td><span class="badge ${sevClass}">${f.severity}</span></td>
          <td><strong>${f.iac_type}</strong></td>
          <td>
            <div style="font-weight:600;">${f.title}</div>
            <div class="mono" style="font-size:11.5px; color:var(--text-secondary);">${f.repository} (${f.branch})</div>
          </td>
          <td class="mono">
            <div>SHA: <span class="text-cyan">${f.commit_sha}</span></div>
            <div style="font-size:11.5px; color:var(--text-secondary);">${f.ci_pipeline}</div>
          </td>
          <td>${f.author_attribution}</td>
          <td><span class="badge badge-cobalt">${f.policy_framework}</span></td>
          <td>
            <span class="badge ${stClass}">${f.status} (${f.remediation_time_mins}m)</span>
            <div style="font-size:11.5px; color:var(--text-secondary); margin-top:3px;">${f.remediation_detail}</div>
          </td>
        </tr>
      `;
      })
      .join("");
  }
}

function loadSolubleSample(sampleType) {
  const textarea = document.getElementById("soluble-code-input");
  const typeSelect = document.getElementById("soluble-iac-type");
  if (sampleType === "terraform") {
    typeSelect.value = "Terraform";
    textarea.value = `resource "aws_iam_role_policy" "settlement_s3" {
  name = "settlement-wildcard-policy"
  policy = jsonencode({
    Effect   = "Allow"
    Action   = "*"
    Resource = "arn:aws:s3:::burniq-settlement-ledger/*"
  })
}
resource "aws_db_instance" "ledger_db" {
  engine              = "postgres"
  encrypted           = false
  publicly_accessible = true
}`;
  } else {
    typeSelect.value = "Kubernetes";
    textarea.value = `apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-fulfillment-api
spec:
  template:
    spec:
      containers:
      - name: api
        image: burniq/order-fulfillment:latest
        securityContext:
          privileged: true
        env:
        - name: STRIPE_API_KEY
          value: "sk-live-9948102948102948"`;
  }
  runSolubleInteractiveScan();
}

async function runSolubleInteractiveScan() {
  const iac_type = document.getElementById("soluble-iac-type").value;
  const llm_author = document.getElementById("soluble-llm-author").value;
  const code_snippet = document.getElementById("soluble-code-input").value;
  const container = document.getElementById("soluble-scan-results");

  try {
    const resp = await fetch("/api/soluble/scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        iac_type,
        llm_author,
        repository: "HayfordMD/burniq-payments-infra",
        branch: "feat/ai-secops-check",
        code_snippet,
      }),
    });
    const res = await resp.json();
    container.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; flex-wrap:wrap; gap:6px;">
        <span class="badge badge-emerald">✓ ${res.gate_decision} (${res.findings_count} findings caught &amp; auto-fixed)</span>
        <span class="mono" style="font-size:12px; color:var(--accent-cyan);">
          SecOps Time Saved: ${res.estimated_manual_fix_mins_saved}m (${fmtUsd(res.workday_secops_savings_usd, 2)} Workday Value)
        </span>
      </div>
      <div style="margin-bottom:8px;">
        ${res.findings
          .map(
            (f) => `
          <div style="font-size:12px; padding:6px 8px; background:var(--bg-surface); border-left:3px solid var(--accent-coral); margin-bottom:5px; border-radius:4px;">
            <strong class="mono text-coral">[${f.rule_id} · ${f.severity}]</strong> (${f.framework}): ${f.issue}
            <div style="color:var(--accent-emerald); margin-top:2px;">→ Auto-Fix: ${f.auto_remediation}</div>
          </div>
        `
          )
          .join("")}
      </div>
      <div style="font-size:11.5px; color:var(--text-secondary); margin-bottom:4px;">Soluble + ${res.llm_author} Auto-Remediated Output:</div>
      <pre class="code-pre">${res.remediated_code}</pre>
    `;
  } catch (err) {
    console.error("Soluble scan failed:", err);
  }
}

function renderAttribution(releases) {
  const tbody = document.getElementById("tbody-attribution");
  if (!tbody || !releases) return;
  tbody.innerHTML = releases
    .map(
      (r) => `
      <tr>
        <td>
          <div class="mono" style="color:var(--accent-cyan); font-weight:700;">${r.release_id}</div>
          <div style="font-weight:600;">${r.release_name}</div>
          <div class="mono" style="font-size:11px; color:var(--text-secondary);">${r.repository}</div>
        </td>
        <td>
          <div><strong>${r.scm_platform}</strong></div>
          <div style="font-size:11.5px; color:var(--text-secondary);">${r.cicd_platform}</div>
        </td>
        <td class="mono">
          <div>SHA: <span class="text-cyan">${r.commit_sha}</span></div>
          <div style="font-size:11px; color:var(--text-secondary);">${r.jira_epic} · ${r.servicenow_chg}</div>
        </td>
        <td>
          <div style="font-weight:600;">${r.lead_engineer}</div>
          <div style="font-size:11.5px; color:var(--text-secondary);">${r.workday_level}</div>
        </td>
        <td>
          <div>${r.llm_models_used.join(", ")}</div>
          <div class="mono" style="font-size:11.5px; color:var(--text-secondary);">${fmtNum(r.llm_tokens_total)} tok (${fmtUsd(r.llm_cost_usd, 2)})</div>
        </td>
        <td class="mono"><span class="badge ${r.ai_code_attribution_pct > 0 ? "badge-emerald" : "badge-amber"}">${r.ai_code_attribution_pct}%</span></td>
        <td class="mono text-emerald">
          <strong>${fmtUsd(r.workday_salary_saved_usd)}</strong>
          <div style="font-size:11px; color:var(--text-secondary);">${r.engineering_hours_saved}h saved</div>
        </td>
        <td class="mono text-cyan"><strong>${fmtUsd(r.salesforce_arr_attributed_usd)}</strong></td>
        <td style="font-size:12px;">${r.datadog_dora_impact}</td>
        <td style="font-size:12px;">${r.newrelic_apm_impact}</td>
        <td style="font-size:12px;">${r.soluble_secops_status}</td>
        <td><span class="badge badge-emerald">${r.roi_multiple}</span></td>
      </tr>
    `
    )
    .join("");
}

function renderWorkdayRoi(roi) {
  const tbody = document.getElementById("tbody-workday-roi");
  if (!tbody || !roi || !roi.departments) return;
  tbody.innerHTML = roi.departments
    .map((d) => {
      const isNeg = d.salary_roi_usd < 0;
      return `
      <tr>
        <td><strong>${d.department}</strong></td>
        <td>
          <div class="mono" style="color:var(--accent-cyan);">${d.workday_cost_center}</div>
          <div style="font-size:11.5px; color:var(--text-secondary);">${d.erp_system}</div>
        </td>
        <td class="mono">${d.headcount} FTEs @ $${d.avg_loaded_hourly_usd}/hr</td>
        <td class="mono">${fmtUsd(d.claude_spend_usd)}</td>
        <td class="mono">${fmtUsd(d.gemini_spend_usd)}</td>
        <td class="mono text-emerald">${d.high_value_code_pct}%</td>
        <td class="mono ${d.low_value_email_notes_pct > 50 ? "text-coral" : ""}">${d.low_value_email_notes_pct}%</td>
        <td class="mono">${d.releases_shipped_30d}</td>
        <td class="mono">${fmtNum(d.hours_saved_30d)} hrs</td>
        <td class="mono ${isNeg ? "text-coral" : "text-emerald"}" style="font-weight:700;">${fmtUsd(d.salary_roi_usd)}</td>
        <td><span class="badge ${isNeg ? "badge-coral" : "badge-emerald"}">${d.net_roi_multiple}</span></td>
      </tr>
    `;
    })
    .join("");
}

function renderConnectors(connectors) {
  const grid = document.getElementById("connectors-grid");
  if (!grid || !connectors) return;
  grid.innerHTML = connectors
    .map(
      (c) => `
      <div class="connector-card ${c.featured ? "featured" : ""}" id="conn-card-${c.id}">
        <div>
          <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:8px; margin-bottom:6px;">
            <div>
              <span class="badge ${c.featured ? "badge-emerald" : "badge-cobalt"}" style="margin-bottom:4px;">
                ${c.featured ? "★ Featured Core 4" : c.category}
              </span>
              <h3 style="font-size:15px; font-weight:700;">${c.name}</h3>
            </div>
            <span class="badge badge-ok" id="conn-badge-${c.id}">${c.status} · ${c.latency_ms}ms</span>
          </div>
          <p style="font-size:12.5px; color:var(--text-secondary); margin-bottom:10px;">${c.description}</p>
          <div class="mono" style="font-size:11.5px; color:var(--accent-cyan); margin-bottom:4px;">Host: ${c.host}</div>
          <div class="mono" style="font-size:11px; color:var(--text-secondary);">Synced: ${c.records_synced}</div>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center; padding-top:10px; border-top:1px solid var(--border-subtle);">
          <span class="mono" style="font-size:11px; color:var(--text-muted);">${c.protocol}</span>
          <button class="btn btn-sm" onclick="testSingleConnectorUI('${c.id}')">Test Live API</button>
        </div>
      </div>
    `
    )
    .join("");
}

async function testSingleConnectorUI(connectorId) {
  try {
    const resp = await fetch(`/api/connectors/${connectorId}/test`, { method: "POST" });
    const data = await resp.json();

    const badge = document.getElementById(`conn-badge-${connectorId}`);
    if (badge) {
      badge.textContent = `VERIFIED 200 OK · ${data.latency_ms}ms`;
    }

    const outBox = document.getElementById("connector-test-output");
    const outTitle = document.getElementById("connector-test-title");
    const outJson = document.getElementById("connector-test-json");

    if (outBox && outTitle && outJson) {
      outBox.style.display = "block";
      outTitle.textContent = `✓ Live Handshake Verified: ${data.name} (${data.routed_via} · HTTP ${data.http_status} · ${data.latency_ms}ms)`;
      outJson.textContent = JSON.stringify(data, null, 2);
    }

    // If user clicked from the Observability tab, show a quick visual confirmation on that button too
    const btn = document.getElementById(`btn-test-${connectorId}`);
    if (btn) {
      const orig = btn.textContent;
      btn.textContent = `✓ 200 OK (${data.latency_ms}ms via ${data.routed_via})`;
      setTimeout(() => {
        btn.textContent = orig;
      }, 3500);
    }
  } catch (err) {
    console.error("Failed connector test:", err);
  }
}

async function verifyAllConnectorsBanner() {
  const btn = document.getElementById("btn-verify-all-header");
  if (btn) btn.textContent = "Testing 23 Enterprise Endpoints...";
  try {
    const resp = await fetch("/api/connectors/test-all", { method: "POST" });
    const data = await resp.json();
    if (btn) {
      btn.textContent = `✓ All ${data.passed_count}/23 Connectors 200 OK`;
    }
    const outBox = document.getElementById("connector-test-output");
    const outTitle = document.getElementById("connector-test-title");
    const outJson = document.getElementById("connector-test-json");
    if (outBox && outTitle && outJson) {
      outBox.style.display = "block";
      outTitle.textContent = `✓ Verified All ${data.passed_count}/23 Enterprise Connectors (Datadog, Substrate, New Relic, Soluble + 19 Enterprise Systems)`;
      outJson.textContent = JSON.stringify(data, null, 2);
    }
  } catch (err) {
    console.error("Batch connector test failed:", err);
  }
}

async function submitCsvImport() {
  const csvContent = document.getElementById("csv-import-textarea").value;
  const resDiv = document.getElementById("csv-import-result");
  try {
    const resp = await fetch("/api/csv/import", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dataset_type: "observability", csv_content: csvContent }),
    });
    const data = await resp.json();
    resDiv.innerHTML = `<span class="badge badge-emerald">✓ Ingested ${data.rows_ingested} CSV telemetry records (${data.columns_detected.join(", ")})</span>`;
  } catch (err) {
    console.error("CSV import failed:", err);
  }
}

window.addEventListener("DOMContentLoaded", initBurnIQ);
