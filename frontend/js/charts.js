/**
 * BurnIQ Interactive SVG & Telemetry Chart Engine (Zero External Dependencies).
 * Renders Multi-Line/Area Charts, Grouped Bar Charts, Donut Charts,
 * Code-to-Release Attribution Funnels, and Interactive Horizontal Bars
 * with inline Service Connection ON/OFF toggles.
 */

window.BurnIQCharts = (function () {
  function escapeHtml(str) {
    return String(str ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function renderChartPanel(chartKey, chartConfig) {
    const type = chartConfig.type || "multi_line";
    let bodyHtml = "";
    let legendHtml = "";

    if (type === "multi_line") {
      legendHtml = renderSeriesLegend(chartConfig.series || []);
      bodyHtml = renderMultiLineSVG(chartConfig);
    } else if (type === "grouped_bar") {
      legendHtml = renderSeriesLegend(chartConfig.series || []);
      bodyHtml = renderGroupedBarSVG(chartConfig);
    } else if (type === "donut") {
      bodyHtml = renderDonutSVG(chartConfig);
    } else if (type === "funnel") {
      bodyHtml = renderFunnelHTML(chartConfig);
    } else if (type === "horizontal_bar") {
      bodyHtml = renderHorizontalBarsHTML(chartConfig);
    }

    return `
      <article class="chart-panel" id="chart-panel-${escapeHtml(chartKey)}">
        <div class="chart-header">
          <div>
            <h2 class="chart-title">${escapeHtml(chartConfig.title)}</h2>
            <p class="chart-subtitle">${escapeHtml(chartConfig.subtitle || "")}</p>
          </div>
          ${legendHtml}
        </div>
        <div class="chart-canvas-wrap">
          ${bodyHtml}
        </div>
      </article>
    `;
  }

  function renderSeriesLegend(series) {
    if (!series || !series.length) return "";
    const items = series
      .map(
        (s) => `
        <span class="legend-item">
          <span class="legend-swatch" style="background:${escapeHtml(s.color)}"></span>
          <span>${escapeHtml(s.name)}</span>
        </span>
      `
      )
      .join("");
    return `<div class="chart-legend">${items}</div>`;
  }

  function renderMultiLineSVG(cfg) {
    const labels = cfg.labels || [];
    const series = cfg.series || [];
    if (!labels.length || !series.length) return "<p>No time-series data</p>";

    const width = 680;
    const height = 235;
    const padLeft = 48;
    const padRight = 22;
    const padTop = 18;
    const padBottom = 32;
    const plotW = width - padLeft - padRight;
    const plotH = height - padTop - padBottom;

    let maxVal = 10;
    series.forEach((s) => {
      (s.data || []).forEach((v) => {
        if (v > maxVal) maxVal = v;
      });
    });
    maxVal = Math.ceil(maxVal * 1.12);

    // Grid lines
    let gridSvg = "";
    const steps = 4;
    for (let i = 0; i <= steps; i++) {
      const y = padTop + (plotH / steps) * i;
      const val = Math.round(maxVal - (maxVal / steps) * i);
      gridSvg += `
        <line x1="${padLeft}" y1="${y}" x2="${width - padRight}" y2="${y}" stroke="var(--border-default)" stroke-dasharray="3,3" />
        <text x="${padLeft - 8}" y="${y + 4}" text-anchor="end" fill="var(--text-muted)" font-size="10.5" font-family="monospace">${val}</text>
      `;
    }

    // X-axis labels
    let xSvg = "";
    const n = labels.length;
    labels.forEach((lbl, idx) => {
      const x = padLeft + (n > 1 ? (plotW / (n - 1)) * idx : plotW / 2);
      xSvg += `<text x="${x}" y="${height - 8}" text-anchor="middle" fill="var(--text-muted)" font-size="10.5" font-family="monospace">${escapeHtml(lbl)}</text>`;
    });

    // Series paths
    let pathsSvg = "";
    series.forEach((s, sIdx) => {
      const pts = (s.data || []).map((v, idx) => {
        const x = padLeft + (n > 1 ? (plotW / (n - 1)) * idx : plotW / 2);
        const y = padTop + plotH - (Math.max(v, 0) / maxVal) * plotH;
        return { x, y, v };
      });
      if (!pts.length) return;

      const dLine = pts.map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ");
      const dArea = `${dLine} L${pts[pts.length - 1].x.toFixed(1)},${(padTop + plotH).toFixed(1)} L${pts[0].x.toFixed(1)},${(padTop + plotH).toFixed(1)} Z`;

      if (sIdx === 0) {
        pathsSvg += `<path d="${dArea}" fill="${escapeHtml(s.color)}" fill-opacity="0.12" />`;
      }
      pathsSvg += `<path d="${dLine}" fill="none" stroke="${escapeHtml(s.color)}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" />`;

      pts.forEach((p) => {
        pathsSvg += `
          <circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="3.6" fill="${escapeHtml(s.color)}" stroke="var(--bg-surface)" stroke-width="1.5">
            <title>${escapeHtml(s.name)}: ${p.v} ${escapeHtml(s.unit || "")}</title>
          </circle>
        `;
      });
    });

    return `
      <svg viewBox="0 0 ${width} ${height}" width="100%" height="235" role="img" aria-label="${escapeHtml(cfg.title)}">
        ${gridSvg}
        ${pathsSvg}
        ${xSvg}
      </svg>
    `;
  }

  function renderGroupedBarSVG(cfg) {
    const labels = cfg.labels || [];
    const series = cfg.series || [];
    if (!labels.length || !series.length) return "<p>No bar chart data</p>";

    const width = 680;
    const height = 235;
    const padLeft = 46;
    const padRight = 18;
    const padTop = 18;
    const padBottom = 34;
    const plotW = width - padLeft - padRight;
    const plotH = height - padTop - padBottom;

    let maxVal = 10;
    series.forEach((s) => {
      (s.data || []).forEach((v) => {
        if (v > maxVal) maxVal = v;
      });
    });
    maxVal = Math.ceil(maxVal * 1.15);

    let gridSvg = "";
    const steps = 4;
    for (let i = 0; i <= steps; i++) {
      const y = padTop + (plotH / steps) * i;
      const val = Math.round(maxVal - (maxVal / steps) * i);
      gridSvg += `
        <line x1="${padLeft}" y1="${y}" x2="${width - padRight}" y2="${y}" stroke="var(--border-default)" stroke-dasharray="3,3" />
        <text x="${padLeft - 8}" y="${y + 4}" text-anchor="end" fill="var(--text-muted)" font-size="10.5" font-family="monospace">${val}</text>
      `;
    }

    const groupCount = labels.length;
    const groupW = plotW / groupCount;
    const barCount = series.length;
    const barW = Math.min((groupW * 0.68) / barCount, 26);

    let barsSvg = "";
    labels.forEach((lbl, gIdx) => {
      const groupCenter = padLeft + groupW * gIdx + groupW / 2;
      const startX = groupCenter - (barCount * barW + (barCount - 1) * 3) / 2;

      series.forEach((s, bIdx) => {
        const v = (s.data || [])[gIdx] || 0;
        const barH = Math.max((v / maxVal) * plotH, 2);
        const x = startX + bIdx * (barW + 3);
        const y = padTop + plotH - barH;
        barsSvg += `
          <rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${barW.toFixed(1)}" height="${barH.toFixed(1)}" rx="3" fill="${escapeHtml(s.color)}">
            <title>${escapeHtml(lbl)} — ${escapeHtml(s.name)}: ${v}</title>
          </rect>
        `;
      });

      barsSvg += `<text x="${groupCenter.toFixed(1)}" y="${height - 10}" text-anchor="middle" fill="var(--text-muted)" font-size="10.5" font-family="monospace">${escapeHtml(lbl)}</text>`;
    });

    return `
      <svg viewBox="0 0 ${width} ${height}" width="100%" height="235" role="img" aria-label="${escapeHtml(cfg.title)}">
        ${gridSvg}
        ${barsSvg}
      </svg>
    `;
  }

  function renderDonutSVG(cfg) {
    const segments = cfg.segments || [];
    const total = segments.reduce((acc, s) => acc + (Number(s.value) || 0), 0) || 100;
    const r = 68;
    const cx = 92;
    const cy = 92;
    const circum = 2 * Math.PI * r;

    let offset = 0;
    let circlesSvg = "";
    segments.forEach((seg) => {
      const pct = (Number(seg.value) || 0) / total;
      const dash = pct * circum;
      circlesSvg += `
        <circle
          cx="${cx}" cy="${cy}" r="${r}"
          fill="transparent"
          stroke="${escapeHtml(seg.color)}"
          stroke-width="22"
          stroke-dasharray="${dash.toFixed(2)} ${circum.toFixed(2)}"
          stroke-dashoffset="${(-offset).toFixed(2)}"
          transform="rotate(-90 ${cx} ${cy})"
        >
          <title>${escapeHtml(seg.label)}: ${seg.value}% ($${Number(seg.cost_usd || 0).toLocaleString()}/mo)</title>
        </circle>
      `;
      offset += dash;
    });

    const legendRows = segments
      .map(
        (seg) => `
        <div style="display:flex;align-items:center;justify-content:space-between;gap:0.75rem;font-size:0.79rem;padding:0.25rem 0;border-bottom:1px solid var(--border-subtle);">
          <span style="display:inline-flex;align-items:center;gap:0.45rem;color:var(--text-primary);">
            <span class="legend-swatch" style="background:${escapeHtml(seg.color)}"></span>
            <span>${escapeHtml(seg.label)}</span>
          </span>
          <span class="tabular-nums" style="font-family:var(--font-mono);color:var(--text-secondary);white-space:nowrap;">
            <strong>${seg.value}%</strong> · $${Number(seg.cost_usd || 0).toLocaleString()}
          </span>
        </div>
      `
      )
      .join("");

    return `
      <div style="display:grid;grid-template-columns:185px 1fr;gap:1.15rem;align-items:center;width:100%;">
        <svg viewBox="0 0 184 184" width="180" height="180" role="img" aria-label="${escapeHtml(cfg.title)}">
          ${circlesSvg}
          <text x="${cx}" y="${cy - 4}" text-anchor="middle" fill="var(--text-primary)" font-size="19" font-weight="700" font-family="monospace">${escapeHtml(cfg.center_label || "")}</text>
          <text x="${cx}" y="${cy + 15}" text-anchor="middle" fill="#94a3b8" font-size="10.5" font-family="sans-serif">${escapeHtml(cfg.center_sublabel || "")}</text>
        </svg>
        <div style="display:flex;flex-direction:column;gap:0.15rem;">
          ${legendRows}
        </div>
      </div>
    `;
  }

  function renderFunnelHTML(cfg) {
    const stages = cfg.stages || [];
    const maxCount = Math.max(...stages.map((s) => s.count || 1), 1);

    const rows = stages
      .map((s) => {
        const widthPct = Math.max(Math.round((s.count / maxCount) * 100), 14);
        return `
          <div class="hbar-row">
            <div class="hbar-meta">
              <span class="hbar-label">${escapeHtml(s.stage)}</span>
              <span class="hbar-stats">
                <strong>${Number(s.count).toLocaleString()}</strong>
                <span class="code-badge">${s.pct}% rate</span>
              </span>
            </div>
            <div class="hbar-track">
              <div class="hbar-fill" style="width:${widthPct}%;background:${escapeHtml(s.color)};"></div>
            </div>
          </div>
        `;
      })
      .join("");

    return `<div class="hbar-list">${rows}</div>`;
  }

  function renderHorizontalBarsHTML(cfg) {
    const items = cfg.items || [];
    const rows = items
      .map((item) => {
        const maxVal = item.max_value || 100;
        const pct = Math.min(Math.round((item.value / maxVal) * 100), 100);
        const isConn = String(item.id || "").startsWith("conn-");
        const toggleBtn = isConn
          ? `<button type="button" class="btn btn-sm ${item.enabled ? "btn-emerald" : "btn-coral-subtle"}" data-action="toggle-conn" data-conn-id="${escapeHtml(item.id)}" id="chart-toggle-${escapeHtml(item.id)}">
               ${item.enabled ? "ON" : "OFF"}
             </button>`
          : "";

        return `
          <div class="hbar-row">
            <div class="hbar-meta">
              <span class="hbar-label">
                ${toggleBtn}
                <span>${escapeHtml(item.label)}</span>
              </span>
              <span class="hbar-stats">
                <span>${escapeHtml(item.category || "")}</span>
                <strong>${Number(item.value).toLocaleString()}</strong>
                ${item.latency_ms ? `<span>(${item.latency_ms}ms)</span>` : ""}
              </span>
            </div>
            <div class="hbar-track">
              <div class="hbar-fill" style="width:${pct}%;background:${escapeHtml(item.color)};"></div>
            </div>
          </div>
        `;
      })
      .join("");

    return `<div class="hbar-list">${rows}</div>`;
  }

  return {
    renderChartPanel,
  };
})();
