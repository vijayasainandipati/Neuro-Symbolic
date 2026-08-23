/* ═══════════════════════════════════════════════════════════════════════════
   Neuro-Symbolic Multi-Hazard & Defense AI — Dashboard JavaScript
   ═══════════════════════════════════════════════════════════════════════════ */

// ── Icon Maps ───────────────────────────────────────────────────────────────
const HAZARD_ICONS = { flood:'🌊', landslide:'🏔️', cyclone:'🌀', fire:'🔥', defense:'🛡️', compound:'⚠️' };
const ALERT_ICONS  = { RED:'🔴', ORANGE:'🟠', YELLOW:'🟡', BLUE:'🔵', GREEN:'🟢' };
const THREAT_ICONS = { CRITICAL:'🔴', HIGH:'🟠', ELEVATED:'🟡', GUARDED:'🔵', SAFE:'🟢' };

// ── State ───────────────────────────────────────────────────────────────────
let lastAnalysis = null;
let lastSimulation = null;

// ── DOM Helpers ─────────────────────────────────────────────────────────────
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);
const loading = (show) => $('#loading').classList.toggle('show', show);

function getLevel(decision) {
    return decision.alert_level || decision.threat_level || 'GREEN';
}

function getLevelIcon(decision) {
    const lvl = getLevel(decision);
    return ALERT_ICONS[lvl] || THREAT_ICONS[lvl] || '⚪';
}

function badgeClass(level) {
    const map = { RED:'badge-red', ORANGE:'badge-orange', YELLOW:'badge-yellow', BLUE:'badge-blue', GREEN:'badge-green',
                  CRITICAL:'badge-red', HIGH:'badge-orange', ELEVATED:'badge-yellow', GUARDED:'badge-blue', SAFE:'badge-green' };
    return map[level] || 'badge-green';
}

// ── Sidebar Range Sliders ───────────────────────────────────────────────────
function initSliders() {
    const sliders = [
        ['cfg-population', 'val-population', v => v],
        ['cfg-elevation',  'val-elevation',  v => v],
        ['cfg-rainfall',   'val-rainfall',   v => v],
        ['cfg-soil',       'val-soil',       v => (v/100).toFixed(2)],
        ['cfg-wind',       'val-wind',       v => v],
        ['cfg-temp',       'val-temp',       v => v],
        ['cfg-slope',      'val-slope',      v => v],
        ['cfg-vehicles',   'val-vehicles',   v => v],
        ['cfg-proximity',  'val-proximity',  v => parseFloat(v).toFixed(1)],
    ];
    sliders.forEach(([sliderId, valId, fmt]) => {
        const slider = document.getElementById(sliderId);
        const valEl  = document.getElementById(valId);
        if (slider && valEl) {
            slider.addEventListener('input', () => { valEl.textContent = fmt(slider.value); });
        }
    });
}

// ── Mode Toggle ─────────────────────────────────────────────────────────────
function initModeToggle() {
    const modeSelect = $('#cfg-mode');
    const defenseParams = $('#defense-params');
    modeSelect.addEventListener('change', () => {
        defenseParams.style.display = (modeSelect.value === 'disaster') ? 'none' : 'block';
    });
}

// ── Tab Navigation ──────────────────────────────────────────────────────────
function initTabs() {
    $$('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            $$('.tab-btn').forEach(b => b.classList.remove('active'));
            $$('.tab-panel').forEach(p => p.classList.remove('active'));
            btn.classList.add('active');
            $(`#tab-${btn.dataset.tab}`).classList.add('active');
        });
    });
}

// ── Sidebar Toggle (mobile) ─────────────────────────────────────────────────
function initMenuToggle() {
    $('#menu-btn').addEventListener('click', () => {
        $('#sidebar').classList.toggle('open');
    });
}

// ── File Upload Previews ────────────────────────────────────────────────────
function initUploads() {
    setupUpload('analyze-file', 'preview-img', 'upload-area');
    setupUpload('defense-file', 'defense-preview', 'defense-upload-area');
}

function setupUpload(inputId, previewId, areaId) {
    const input   = document.getElementById(inputId);
    const preview = document.getElementById(previewId);
    const area    = document.getElementById(areaId);

    if (!input || !preview || !area) return;

    input.addEventListener('change', () => {
        if (input.files && input.files[0]) {
            const reader = new FileReader();
            reader.onload = (e) => { preview.src = e.target.result; preview.style.display = 'block'; };
            reader.readAsDataURL(input.files[0]);
        }
    });

    area.addEventListener('dragover', (e) => { e.preventDefault(); area.classList.add('dragover'); });
    area.addEventListener('dragleave', () => area.classList.remove('dragover'));
    area.addEventListener('drop', (e) => {
        e.preventDefault();
        area.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
            input.files = e.dataTransfer.files;
            input.dispatchEvent(new Event('change'));
        }
    });
}

// ── Get Config Values ───────────────────────────────────────────────────────
function getConfig() {
    return {
        region:       $('#cfg-region').value,
        population:   $('#cfg-population').value,
        elevation:    $('#cfg-elevation').value,
        rainfall_mm:  $('#cfg-rainfall').value,
        soil_moisture:(parseInt($('#cfg-soil').value) / 100).toFixed(2),
        wind_speed:   $('#cfg-wind').value,
        temperature:  $('#cfg-temp').value,
        terrain_slope:$('#cfg-slope').value,
        num_vehicles: $('#cfg-vehicles').value,
        movement_direction: $('#cfg-movement').value,
        region_type:  $('#cfg-regiontype').value,
        proximity_km: $('#cfg-proximity').value,
    };
}

// ── Render a Decision Result Card ───────────────────────────────────────────
function renderResultCard(hazard, detection, decision) {
    const level = getLevel(decision);
    const icon  = HAZARD_ICONS[hazard] || '❓';
    const lvlIcon = getLevelIcon(decision);

    const prob = decision[`${hazard}_probability`]
        || detection.probability
        || detection.confidence
        || decision.threat_score
        || 0;

    let actionsHtml = '';
    if (decision.actions && decision.actions.length) {
        actionsHtml = '<ul class="action-list">' +
            decision.actions.map(a => `<li>${a}</li>`).join('') +
            '</ul>';
    }

    let reasonsHtml = '';
    if (decision.reasons && decision.reasons.length) {
        reasonsHtml = decision.reasons.map(r => `<div class="reason-box">${r}</div>`).join('');
    }

    return `
        <div class="result-card level-${level}">
            <h4>${icon} ${hazard.charAt(0).toUpperCase() + hazard.slice(1)} — ${lvlIcon} ${level}</h4>
            <div class="metric-row">
                <div class="metric">
                    <div class="metric-value">${(prob * 100).toFixed(1)}%</div>
                    <div class="metric-label">Probability</div>
                </div>
                <div class="metric">
                    <div class="metric-value">${decision.priority || 0}</div>
                    <div class="metric-label">Priority</div>
                </div>
            </div>
            <strong>Recommended Actions:</strong>
            ${actionsHtml}
            ${reasonsHtml}
        </div>`;
}

// ═══════════════════════════════════════════════════════════════════════════
// TAB 1: ANALYSIS
// ═══════════════════════════════════════════════════════════════════════════
function initAnalysis() {
    $('#analyze-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const fileInput = $('#analyze-file');
        if (!fileInput.files || !fileInput.files[0]) {
            alert('Please select an image to analyze.');
            return;
        }

        const cfg = getConfig();
        const formData = new FormData();
        formData.append('image', fileInput.files[0]);
        formData.append('region', cfg.region);
        formData.append('population', cfg.population);
        formData.append('elevation', cfg.elevation);
        formData.append('rainfall_mm', cfg.rainfall_mm);
        formData.append('soil_moisture', cfg.soil_moisture);
        formData.append('wind_speed', cfg.wind_speed);
        formData.append('temperature', cfg.temperature);
        formData.append('terrain_slope', cfg.terrain_slope);

        const hazardBoxes = $$('#analyze-form input[name="hazards"]:checked');
        hazardBoxes.forEach(cb => formData.append('hazards', cb.value));

        loading(true);
        try {
            const resp = await fetch('/api/analyze', { method: 'POST', body: formData });
            const data = await resp.json();
            lastAnalysis = data.results;
            renderAnalysisResults(data.results);
            renderXAI();
        } catch (err) {
            $('#analysis-output').innerHTML = `<p class="placeholder" style="color:var(--red);">Error: ${err.message}</p>`;
        } finally {
            loading(false);
        }
    });
}

function renderAnalysisResults(results) {
    if (!results || !results.length) {
        $('#analysis-output').innerHTML = '<p class="placeholder">No results.</p>';
        return;
    }
    $('#analysis-output').innerHTML = results.map(r =>
        renderResultCard(r.hazard, r.detection, r.decision)
    ).join('');
}

// ═══════════════════════════════════════════════════════════════════════════
// TAB 2: SIMULATION
// ═══════════════════════════════════════════════════════════════════════════
function initSimulation() {
    $('#btn-simulate').addEventListener('click', async () => {
        const hazards = [];
        $$('.sim-hazard:checked').forEach(cb => hazards.push(cb.value));
        const region = $('#sim-region').value;

        loading(true);
        try {
            const resp = await fetch('/api/simulate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ hazards, region }),
            });
            const data = await resp.json();
            lastSimulation = data;
            renderSimulation(data);
            renderXAI();
        } catch (err) {
            $('#simulation-output').innerHTML = `<p class="placeholder" style="color:var(--red);">Error: ${err.message}</p>`;
        } finally {
            loading(false);
        }
    });
}

function renderSimulation(data) {
    let html = `<div class="card"><h3>Cycle ${data.cycle} — Region: ${data.region}</h3>`;

    // Environmental data
    const env = data.environmental_data || {};
    html += `<div class="metric-row">
        <div class="metric"><div class="metric-value">${env.population_density || '-'}</div><div class="metric-label">Population</div></div>
        <div class="metric"><div class="metric-value">${env.elevation || '-'}m</div><div class="metric-label">Elevation</div></div>
        <div class="metric"><div class="metric-value">${env.rainfall_mm || '-'}mm</div><div class="metric-label">Rainfall</div></div>
        <div class="metric"><div class="metric-value">${env.wind_speed_kmh || '-'}km/h</div><div class="metric-label">Wind</div></div>
    </div></div>`;

    // Detections
    for (const [hazard, detection] of Object.entries(data.detections || {})) {
        const decision = (data.decisions || {})[hazard] || {};
        html += renderResultCard(hazard, detection, decision);
    }

    // Compound event
    const compound = data.compound_assessment;
    if (compound && compound.compound_event) {
        const ce = compound.compound_event;
        html += `<div class="compound-alert">
            <h4>⚠️ COMPOUND EVENT DETECTED — Alert: ${ce.alert_level || 'RED'}</h4>`;
        if (ce.reasons) ce.reasons.forEach(r => { html += `<div class="reason-box" style="border-left-color:var(--red);">${r}</div>`; });
        if (ce.actions) {
            html += '<ul class="action-list">';
            ce.actions.forEach(a => { html += `<li><strong>${a}</strong></li>`; });
            html += '</ul>';
        }
        html += '</div>';
    }

    $('#simulation-output').innerHTML = html;
}

// ═══════════════════════════════════════════════════════════════════════════
// TAB 3: AI EXPLANATIONS
// ═══════════════════════════════════════════════════════════════════════════
function renderXAI() {
    const container = $('#xai-output');

    const items = lastAnalysis || (lastSimulation ? buildSimItems(lastSimulation) : null);
    if (!items || !items.length) {
        container.innerHTML = '<p class="placeholder">Run an analysis or simulation to see AI explanations.</p>';
        return;
    }

    container.innerHTML = items.map((r, i) => {
        const hazard = r.hazard;
        const icon = HAZARD_ICONS[hazard] || '❓';
        return `
        <div class="card">
            <h3>${icon} ${hazard.charAt(0).toUpperCase() + hazard.slice(1)} Decision Trace</h3>
            <p><strong>Step 1: Neural Network Detection</strong></p>
            <div class="json-block">${JSON.stringify(r.detection, null, 2)}</div>
            <p><strong>Step 2: Symbolic Rules Applied</strong></p>
            <div class="json-block">${JSON.stringify(r.decision, null, 2)}</div>
            <p><strong>Step 3: Reasoning Narrative</strong></p>
            ${(r.decision.reasons || []).map(rr => `<div class="reason-box">${rr}</div>`).join('')}
        </div>`;
    }).join('');
}

function buildSimItems(simData) {
    if (!simData || !simData.detections) return [];
    return Object.entries(simData.detections).map(([hazard, detection]) => ({
        hazard,
        detection,
        decision: (simData.decisions || {})[hazard] || {},
    }));
}

// ═══════════════════════════════════════════════════════════════════════════
// TAB 5: DEFENSE MONITOR
// ═══════════════════════════════════════════════════════════════════════════
function initDefense() {
    $('#defense-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const fileInput = $('#defense-file');
        if (!fileInput.files || !fileInput.files[0]) {
            alert('Please select a surveillance image.');
            return;
        }

        const cfg = getConfig();
        const formData = new FormData();
        formData.append('image', fileInput.files[0]);
        formData.append('region', cfg.region);
        formData.append('num_vehicles', cfg.num_vehicles);
        formData.append('movement_direction', cfg.movement_direction);
        formData.append('region_type', cfg.region_type);
        formData.append('proximity_km', cfg.proximity_km);

        loading(true);
        try {
            const resp = await fetch('/api/defense', { method: 'POST', body: formData });
            const data = await resp.json();
            renderDefenseResult(data.decision);
        } catch (err) {
            $('#defense-output').innerHTML = `<p class="placeholder" style="color:var(--red);">Error: ${err.message}</p>`;
        } finally {
            loading(false);
        }
    });
}

function renderDefenseResult(decision) {
    const level = decision.threat_level || 'SAFE';
    const icon  = THREAT_ICONS[level] || '⚪';

    let html = `<div class="result-card level-${level}">
        <h4>${icon} Threat Level: ${level}</h4>
        <div class="metric-row">
            <div class="metric"><div class="metric-value">${((decision.threat_score || 0) * 100).toFixed(1)}%</div><div class="metric-label">Threat Score</div></div>
            <div class="metric"><div class="metric-value">${decision.num_vehicles || 0}</div><div class="metric-label">Vehicles</div></div>
            <div class="metric"><div class="metric-value">${decision.priority || 0}</div><div class="metric-label">Priority</div></div>
        </div>
        <strong>Recommended Actions:</strong>
        <ul class="action-list">${(decision.actions || []).map(a => `<li>${a}</li>`).join('')}</ul>
        ${(decision.reasons || []).map(r => `<div class="reason-box">${r}</div>`).join('')}
    </div>`;

    $('#defense-output').innerHTML = html;
}

// ═══════════════════════════════════════════════════════════════════════════
// TAB 6: DECISION HISTORY
// ═══════════════════════════════════════════════════════════════════════════
function initHistory() {
    $('#btn-refresh-history').addEventListener('click', loadHistory);
    $('#btn-clear-history').addEventListener('click', async () => {
        if (!confirm('Clear all decision history?')) return;
        await fetch('/api/history', { method: 'DELETE' });
        loadHistory();
    });
}

async function loadHistory() {
    try {
        const resp = await fetch('/api/history');
        const data = await resp.json();
        renderHistory(data.log || []);
    } catch (err) {
        $('#history-summary').innerHTML = `<p style="color:var(--red);">Error loading history.</p>`;
    }
}

function renderHistory(log) {
    // Summary
    const summaryEl = $('#history-summary');
    if (!log.length) {
        summaryEl.innerHTML = '<p class="placeholder">No decisions recorded yet.</p>';
        $('#history-table').querySelector('tbody').innerHTML = '';
        $('#timeline-chart').innerHTML = '';
        return;
    }

    const typeCounts = {};
    log.forEach(entry => {
        const t = entry.event_type || 'unknown';
        typeCounts[t] = (typeCounts[t] || 0) + 1;
    });

    summaryEl.innerHTML = `<h3>Total Decisions: ${log.length}</h3>
        <div class="summary-metrics">
            ${Object.entries(typeCounts).map(([t, c]) =>
                `<div class="metric"><div class="metric-value">${c}</div><div class="metric-label">${HAZARD_ICONS[t] || '❓'} ${t}</div></div>`
            ).join('')}
        </div>`;

    // Timeline chart (CSS bars)
    const recent = log.slice(-30);
    const maxPri = 5;
    const colors = { 5:'var(--red)', 4:'var(--orange)', 3:'var(--yellow)', 2:'var(--blue)', 1:'var(--green)', 0:'var(--green)' };

    $('#timeline-chart').innerHTML = `<div class="timeline-bar-group">
        ${recent.map(entry => {
            const p = entry.priority || 0;
            const h = Math.max(8, (p / maxPri) * 100);
            const c = colors[p] || 'var(--green)';
            const lbl = `${(entry.event_type || '').toUpperCase()} P${p}`;
            return `<div class="timeline-bar" style="height:${h}%;background:${c};" data-label="${lbl}"></div>`;
        }).join('')}
    </div>`;

    // Table
    const tbody = $('#history-table').querySelector('tbody');
    tbody.innerHTML = log.slice().reverse().slice(0, 50).map(entry => {
        const level = entry.alert_level || entry.threat_level || 'N/A';
        return `<tr>
            <td>${(entry.timestamp || '').slice(0, 19)}</td>
            <td>${entry.region || ''}</td>
            <td>${(entry.event_type || '').charAt(0).toUpperCase() + (entry.event_type || '').slice(1)}</td>
            <td><span class="badge ${badgeClass(level)}">${level}</span></td>
            <td>${entry.priority || 0}</td>
            <td>${(entry.actions || []).join('; ')}</td>
        </tr>`;
    }).join('');
}

// ═══════════════════════════════════════════════════════════════════════════
// INIT
// ═══════════════════════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
    initSliders();
    initModeToggle();
    initTabs();
    initMenuToggle();
    initUploads();
    initAnalysis();
    initSimulation();
    initDefense();
    initHistory();
});
