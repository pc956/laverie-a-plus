#!/usr/bin/env python3
"""v24 : Paris + 92 + sidebar de synthèse persistante avec point-in-polygon."""
import json, re, math

HTML_IN  = '/home/claude/workspace/outputs/carte_prospection_etape3a_v21_clean.html'
HTML_OUT = '/home/claude/workspace/outputs/carte_prospection_etape3a_v24_paris_92.html'
GEOJSON  = '/home/claude/workspace/iris/iris_75_92_enriched.geojson'

with open(HTML_IN) as f:
    html = f.read()

m = re.search(r'(map_[a-f0-9]{20,})\s*=\s*L\.map', html)
MAP_VAR = m.group(1)

with open(GEOJSON) as f:
    gj = json.load(f)
for feat in gj['features']:
    p = feat['properties']
    for k, v in list(p.items()):
        if isinstance(v, float) and math.isnan(v):
            p[k] = None
print(f"Features : {len(gj['features'])}")

GJSON = json.dumps(gj, ensure_ascii=False, separators=(',', ':'))

COMPONENT = """
<style>
/* === Panneau IRIS (config + légende) en bas à gauche === */
#iris-panel-wrap {
  position: absolute; bottom: 20px; left: 12px; z-index: 1000;
  width: 280px;
  font-family: -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
  font-size: 12px;
}
#iris-panel-card {
  background: rgba(255,255,255,0.98); border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.18);
  border: 1px solid rgba(0,0,0,0.08); overflow: hidden;
}
#iris-panel-header {
  background: linear-gradient(135deg,#1e3a5f,#2c5282); color: white;
  padding: 8px 12px; font-weight: 600; font-size: 12px;
  display: flex; justify-content: space-between; align-items: center;
  cursor: pointer; user-select: none;
}
#iris-panel-wrap.collapsed #iris-panel-header .chevron { transform: rotate(-90deg); }
#iris-panel-header .chevron { transition: transform 0.2s; }
#iris-panel-body { padding: 10px; }
#iris-panel-body.collapsed { display: none; }
#iris-toggle-on { display: flex; align-items: center; gap: 6px; margin-bottom: 8px; font-size: 11px; color: #444; cursor: pointer; }
.iris-var-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 4px; margin-bottom: 8px; }
.iris-var-btn { padding: 5px 6px; font-size: 10px; background: #ecf0f1; border: 1px solid #ddd; border-radius: 4px; cursor: pointer; text-align: center; user-select: none; color: #333; }
.iris-var-btn:hover { background: #d6dbdf; }
.iris-var-btn.active { background: linear-gradient(135deg,#2c5282,#1e3a5f); color: white; border-color: #1e3a5f; font-weight: 600; }
.iris-mode-row { display: flex; gap: 4px; margin-bottom: 8px; font-size: 10px; }
.iris-mode-btn { flex: 1; padding: 4px; background: #f4f4f5; border: 1px solid #ddd; border-radius: 4px; cursor: pointer; text-align: center; }
.iris-mode-btn.active { background: #34495e; color: white; border-color: #34495e; }
#iris-legend { border-top: 1px solid #eee; padding-top: 6px; margin-top: 4px; font-size: 10px; }
.iris-leg-row { display: flex; align-items: center; gap: 6px; padding: 1px 0; }
.iris-leg-swatch { width: 18px; height: 12px; border: 1px solid rgba(0,0,0,0.15); border-radius: 2px; flex-shrink: 0; }
.iris-leg-label { color: #555; }
#iris-opacity-row { display: flex; align-items: center; gap: 6px; margin-top: 8px; font-size: 10px; color: #666; }
#iris-opacity-slider { flex: 1; margin: 0; height: 4px; }
#iris-source { font-size: 9px; color: #999; margin-top: 6px; font-style: italic; }

/* === Sidebar synthèse à droite === */
#iris-detail-wrap {
  position: absolute; top: 12px; right: 12px; z-index: 1000;
  width: 290px;
  font-family: -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
  font-size: 12px;
  display: none;
}
#iris-detail-wrap.show { display: block; }
#iris-detail-card {
  background: rgba(255,255,255,0.98); border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.18);
  border: 1px solid rgba(0,0,0,0.08); overflow: hidden;
}
#iris-detail-header {
  background: linear-gradient(135deg,#7c3aed,#5b21b6); color: white;
  padding: 8px 12px; font-weight: 600; font-size: 12px;
  display: flex; justify-content: space-between; align-items: center;
}
#iris-detail-close {
  background: rgba(255,255,255,0.2); border: none; color: white;
  width: 22px; height: 22px; border-radius: 50%; cursor: pointer;
  font-size: 14px; line-height: 1; padding: 0;
}
#iris-detail-close:hover { background: rgba(255,255,255,0.35); }
#iris-detail-body { padding: 12px; max-height: 70vh; overflow-y: auto; }
.iris-d-title { font-size: 14px; font-weight: 700; color: #1e3a5f; margin-bottom: 2px; }
.iris-d-meta { font-size: 10px; color: #777; margin-bottom: 10px; padding-bottom: 6px; border-bottom: 1px solid #eee; }
.iris-d-section { margin-bottom: 10px; }
.iris-d-section-title { font-size: 10px; font-weight: 700; color: #5b21b6; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }
.iris-d-row { display: flex; justify-content: space-between; padding: 3px 0; font-size: 12px; border-bottom: 1px dashed #f0f0f0; }
.iris-d-row:last-child { border-bottom: none; }
.iris-d-label { color: #555; }
.iris-d-value { font-weight: 600; color: #1a1a1a; }
.iris-d-value.bold { color: #5b21b6; font-size: 13px; }
.iris-d-value.bad { color: #dc2626; }
.iris-d-value.good { color: #16a34a; }
.iris-d-rank {
  display: inline-block; font-size: 10px; padding: 2px 6px;
  border-radius: 10px; color: white; font-weight: 600;
  margin-left: 4px;
}
.iris-d-cta {
  margin-top: 10px; padding: 8px;
  background: linear-gradient(135deg,#fef3c7,#fde68a);
  border-radius: 6px; font-size: 11px; color: #78350f;
  border-left: 3px solid #d97706;
}
.iris-d-help {
  margin-top: 8px; padding: 8px; font-size: 10px;
  color: #777; background: #f9fafb; border-radius: 4px;
  font-style: italic;
}
@media (max-width: 600px) {
  #iris-panel-wrap, #iris-detail-wrap { width: calc(100vw - 24px); }
  #iris-detail-wrap { top: auto; bottom: 380px; right: 12px; left: 12px; }
}
</style>

<!-- Panneau config + légende -->
<div id="iris-panel-wrap">
  <div id="iris-panel-card">
    <div id="iris-panel-header" onclick="IrisLayer.toggleCollapse()">
      <span>📊 IRIS INSEE — Paris + 92</span>
      <span class="chevron">▼</span>
    </div>
    <div id="iris-panel-body">
      <label id="iris-toggle-on">
        <input type="checkbox" id="iris-on-cb" checked />
        <span>Afficher la couche IRIS</span>
      </label>
      <div class="iris-var-grid">
        <div class="iris-var-btn active" data-var="DISP_MED21" onclick="IrisLayer.setVar(this)">💶 Revenu</div>
        <div class="iris-var-btn" data-var="P22_NPER_RP" onclick="IrisLayer.setVar(this)">👥 Habitants</div>
        <div class="iris-var-btn" data-var="PCT_PROP" onclick="IrisLayer.setVar(this)">🏠 % Prop.</div>
        <div class="iris-var-btn" data-var="PCT_T1_T2" onclick="IrisLayer.setVar(this)">🛏️ % T1+T2</div>
        <div class="iris-var-btn" data-var="P22_RP" onclick="IrisLayer.setVar(this)" style="grid-column:span 2;">🏘️ Ménages (résid. princ.)</div>
      </div>
      <div id="iris-legend"></div>
      <div id="iris-opacity-row">
        <span>Opacité</span>
        <input type="range" id="iris-opacity-slider" min="0" max="100" value="55" />
        <span id="iris-opacity-val">55%</span>
      </div>
      <div id="iris-source">Sources : INSEE recens. 2022 + Filosofi 2021 — 1 608 IRIS (Paris 992 + 92 616)</div>
    </div>
  </div>
</div>

<!-- Sidebar synthèse IRIS -->
<div id="iris-detail-wrap">
  <div id="iris-detail-card">
    <div id="iris-detail-header">
      <span>📍 Synthèse IRIS</span>
      <button id="iris-detail-close" onclick="IrisLayer.closeDetail()">×</button>
    </div>
    <div id="iris-detail-body"></div>
  </div>
</div>

<script>
window.IRIS_DATA = __GEOJSON__;

(function() {
  const map = window.__MAP_VAR__;
  const data = window.IRIS_DATA;

  // Précalculer ranking 92 et 75 séparément (et global) pour chaque variable
  function buildRanks() {
    const ranks = {};
    const vars = ['DISP_MED21','P22_NPER_RP','PCT_PROP','PCT_T1_T2','P22_RP'];
    for (const dept of ['75','92','all']) {
      ranks[dept] = {};
      const feats = data.features.filter(f => {
        if (dept === 'all') return true;
        return (f.properties.INSEE_COM || '').startsWith(dept);
      });
      for (const v of vars) {
        const sorted = feats
          .map(f => ({id: f.properties.CODE_IRIS, val: f.properties[v]}))
          .filter(x => x.val !== null && x.val !== undefined && !isNaN(x.val))
          .sort((a,b) => b.val - a.val);
        ranks[dept][v] = {};
        sorted.forEach((x, i) => ranks[dept][v][x.id] = i + 1);
        ranks[dept][v]._total = sorted.length;
      }
    }
    return ranks;
  }
  const RANKS = buildRanks();

  const VAR_CONFIG = {
    'DISP_MED21': {
      label: 'Revenu médian dispo. / UC',
      palette: ['#fef3c7','#fcd34d','#fb923c','#dc2626','#7f1d1d'],
      hasPct: false, format: v => Math.round(v).toLocaleString('fr-FR') + ' €', unit: '€'
    },
    'P22_NPER_RP': {
      label: 'Habitants',
      palette: ['#eff6ff','#bfdbfe','#7eb1ee','#3b82e0','#1e4b9c'],
      hasPct: false, format: v => Math.round(v).toLocaleString('fr-FR'), unit: ''
    },
    'PCT_PROP': {
      label: '% Propriétaires',
      varAbs: 'P22_RP_PROP',
      palette: ['#dcfce7','#a3eab8','#65d186','#2ea556','#196b32'],
      hasPct: true, format: v => v.toFixed(1) + '%',
      formatAbs: v => Math.round(v).toLocaleString('fr-FR'), unit: '%'
    },
    'PCT_T1_T2': {
      label: '% T1+T2',
      varAbs: 'T1_T2',
      palette: ['#fff7ed','#fed7aa','#fb923c','#ea580c','#9a3412'],
      hasPct: true, format: v => v.toFixed(1) + '%',
      formatAbs: v => Math.round(v).toLocaleString('fr-FR'), unit: '%'
    },
    'P22_RP': {
      label: 'Résid. principales',
      palette: ['#f5f3ff','#ddd6fe','#a78bfa','#7c3aed','#4c1d95'],
      hasPct: false, format: v => Math.round(v).toLocaleString('fr-FR'), unit: ''
    }
  };

  let currentVar = 'DISP_MED21';
  let currentMode = 'pct';
  let opacity = 0.55;
  let layer = null;
  let selectedLayer = null;

  function getBreaks(varKey) {
    const cfg = VAR_CONFIG[varKey];
    let actualVar = varKey;
    if (cfg.hasPct && currentMode === 'abs') actualVar = cfg.varAbs;
    if (!cfg.hasPct) actualVar = varKey;
    const values = data.features
      .map(f => f.properties[actualVar])
      .filter(v => v !== null && v !== undefined && !isNaN(v))
      .sort((a,b) => a-b);
    if (!values.length) return { breaks: [0,1,2,3,4,5], varUsed: actualVar };
    const q = p => values[Math.floor(values.length * p)];
    return { breaks: [values[0], q(0.2), q(0.4), q(0.6), q(0.8), values[values.length-1]], varUsed: actualVar };
  }

  function getColor(value, breaks, palette) {
    if (value === null || value === undefined || isNaN(value)) return '#cccccc';
    for (let i = palette.length - 1; i >= 0; i--) {
      if (value >= breaks[i]) return palette[i];
    }
    return palette[0];
  }

  function styleFeature(feature) {
    const cfg = VAR_CONFIG[currentVar];
    const { breaks, varUsed } = getBreaks(currentVar);
    const v = feature.properties[varUsed];
    return {
      fillColor: getColor(v, breaks, cfg.palette),
      weight: 0.5,
      opacity: 0.6,
      color: '#1e3a5f',
      fillOpacity: v === null ? 0.1 : opacity
    };
  }

  function highlightFeature(e) {
    const lyr = e.target;
    lyr.setStyle({ weight: 2.5, color: '#1a1a1a', fillOpacity: Math.min(opacity + 0.2, 1) });
    lyr.bringToFront();
  }

  function resetHighlight(e) {
    if (selectedLayer === e.target) return; // garder sélection
    layer.resetStyle(e.target);
  }

  function selectIris(featureLayer) {
    if (selectedLayer && selectedLayer !== featureLayer) {
      layer.resetStyle(selectedLayer);
    }
    selectedLayer = featureLayer;
    featureLayer.setStyle({ weight: 3, color: '#7c3aed', fillOpacity: Math.min(opacity + 0.2, 1) });
    featureLayer.bringToFront();
    showDetail(featureLayer.feature.properties);
  }

  // Point-in-polygon pour gérer les clics traversant les markers
  function pointInRing(point, ring) {
    const [x, y] = point;
    let inside = false;
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
      const [xi, yi] = ring[i], [xj, yj] = ring[j];
      const intersect = ((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi);
      if (intersect) inside = !inside;
    }
    return inside;
  }
  function pointInPolygon(point, geom) {
    if (geom.type === 'Polygon') {
      if (!pointInRing(point, geom.coordinates[0])) return false;
      // Vérifier les trous
      for (let h = 1; h < geom.coordinates.length; h++) {
        if (pointInRing(point, geom.coordinates[h])) return false;
      }
      return true;
    } else if (geom.type === 'MultiPolygon') {
      for (const poly of geom.coordinates) {
        if (pointInRing(point, poly[0])) {
          let inHole = false;
          for (let h = 1; h < poly.length; h++) if (pointInRing(point, poly[h])) inHole = true;
          if (!inHole) return true;
        }
      }
      return false;
    }
    return false;
  }
  function findIrisAtLatLng(latlng) {
    const pt = [latlng.lng, latlng.lat];
    for (const feat of data.features) {
      if (pointInPolygon(pt, feat.geometry)) return feat;
    }
    return null;
  }

  function fmt(v, decimals = 0) {
    return v != null ? Math.round(v).toLocaleString('fr-FR') : '—';
  }
  function fmtPct(n, d) {
    return (n != null && d) ? (n / d * 100).toFixed(1) + '%' : '—';
  }

  function showDetail(props) {
    const wrap = document.getElementById('iris-detail-wrap');
    const body = document.getElementById('iris-detail-body');
    const rp = props.P22_RP || 0;
    const dept = (props.INSEE_COM || '').startsWith('75') ? '75' : '92';
    const deptLabel = dept === '75' ? 'Paris' : '92';

    function rankBadge(varKey, val, lowerBetter = false) {
      if (val == null) return '';
      const rank = RANKS[dept][varKey][props.CODE_IRIS];
      const total = RANKS[dept][varKey]._total;
      if (!rank) return '';
      const pct = rank / total;
      const isBest = lowerBetter ? pct >= 0.8 : pct <= 0.2; // top 20%
      const isWorst = lowerBetter ? pct <= 0.2 : pct >= 0.8;
      const color = isBest ? '#16a34a' : (isWorst ? '#dc2626' : '#6b7280');
      const lbl = lowerBetter ? (total - rank + 1) : rank;
      return `<span class="iris-d-rank" style="background:${color};">#${lbl}/${total} ${deptLabel}</span>`;
    }

    // Indicateur composite "attractivité laverie" : faible revenu + petits logements + locataires
    function laverieScore() {
      const med = props.DISP_MED21;
      const pctT12 = props.PCT_T1_T2;
      const pctProp = props.PCT_PROP;
      if (med == null || pctT12 == null || pctProp == null) return null;
      // Normaliser : revenu bas = bon (inversé), T1+T2 haut = bon, propriétaires bas = bon (inversé)
      const medRank = RANKS.all['DISP_MED21'][props.CODE_IRIS] / RANKS.all['DISP_MED21']._total;
      const t12Rank = 1 - (RANKS.all['PCT_T1_T2'][props.CODE_IRIS] / RANKS.all['PCT_T1_T2']._total);
      const propRank = RANKS.all['PCT_PROP'][props.CODE_IRIS] / RANKS.all['PCT_PROP']._total;
      const score = (medRank + t12Rank + propRank) / 3 * 100;
      return Math.round(score);
    }
    const ls = laverieScore();

    body.innerHTML = `
      <div class="iris-d-title">${props.NOM_IRIS || 'IRIS ' + props.CODE_IRIS}</div>
      <div class="iris-d-meta">${props.NOM_COM} · IRIS ${props.CODE_IRIS} · ${props.TYP_IRIS === 'H' ? 'Habitat' : (props.TYP_IRIS === 'A' ? 'Activité' : (props.TYP_IRIS === 'D' ? 'Divers' : props.TYP_IRIS || '?'))}</div>

      <div class="iris-d-section">
        <div class="iris-d-section-title">💶 Revenus 2021</div>
        <div class="iris-d-row"><span class="iris-d-label">Médiane disponible / UC</span><span class="iris-d-value bold">${fmt(props.DISP_MED21)} €${rankBadge('DISP_MED21', props.DISP_MED21)}</span></div>
        <div class="iris-d-row"><span class="iris-d-label">Q1 — bas (25%)</span><span class="iris-d-value">${fmt(props.DISP_Q121)} €</span></div>
        <div class="iris-d-row"><span class="iris-d-label">Q3 — haut (75%)</span><span class="iris-d-value">${fmt(props.DISP_Q321)} €</span></div>
        <div class="iris-d-row"><span class="iris-d-label">Taux pauvreté 60%</span><span class="iris-d-value ${props.DISP_TP6021 > 20 ? 'bad' : ''}">${props.DISP_TP6021 != null ? props.DISP_TP6021.toFixed(1) + '%' : '—'}</span></div>
      </div>

      <div class="iris-d-section">
        <div class="iris-d-section-title">👥 Population 2022</div>
        <div class="iris-d-row"><span class="iris-d-label">Habitants (rés. principales)</span><span class="iris-d-value bold">${fmt(props.P22_NPER_RP)}${rankBadge('P22_NPER_RP', props.P22_NPER_RP)}</span></div>
        <div class="iris-d-row"><span class="iris-d-label">Résidences principales</span><span class="iris-d-value">${fmt(props.P22_RP)}</span></div>
      </div>

      <div class="iris-d-section">
        <div class="iris-d-section-title">🏠 Statut occupation</div>
        <div class="iris-d-row"><span class="iris-d-label">Propriétaires</span><span class="iris-d-value">${fmt(props.P22_RP_PROP)} (${fmtPct(props.P22_RP_PROP, rp)})</span></div>
        <div class="iris-d-row"><span class="iris-d-label">Locataires</span><span class="iris-d-value good">${fmtPct(rp - (props.P22_RP_PROP || 0), rp)}</span></div>
      </div>

      <div class="iris-d-section">
        <div class="iris-d-section-title">🛏️ Composition logements</div>
        <div class="iris-d-row"><span class="iris-d-label">T1 (1 pièce)</span><span class="iris-d-value">${fmt(props.P22_RP_1P)} (${fmtPct(props.P22_RP_1P, rp)})</span></div>
        <div class="iris-d-row"><span class="iris-d-label">T2 (2 pièces)</span><span class="iris-d-value">${fmt(props.P22_RP_2P)} (${fmtPct(props.P22_RP_2P, rp)})</span></div>
        <div class="iris-d-row"><span class="iris-d-label"><b>T1+T2 cumulés</b></span><span class="iris-d-value bold">${fmt(props.T1_T2)} (${fmtPct(props.T1_T2, rp)})${rankBadge('PCT_T1_T2', props.PCT_T1_T2)}</span></div>
      </div>

      ${ls != null ? `<div class="iris-d-cta">
        <b>Score « attractivité laverie » : ${ls}/100</b><br>
        <span style="font-size:10px;">Combine bas revenu (40%) + densité T1+T2 (30%) + % locataires (30%). Sur 1 608 IRIS Paris+92.</span>
      </div>` : ''}

      <div class="iris-d-help">💡 Clique sur la carte ou un autre IRIS pour changer la sélection. Le score est une heuristique indicative, à valider avec la performance observée des laveries voisines (popups bilan).</div>
    `;
    wrap.classList.add('show');
  }

  function closeDetail() {
    document.getElementById('iris-detail-wrap').classList.remove('show');
    if (selectedLayer) {
      layer.resetStyle(selectedLayer);
      selectedLayer = null;
    }
  }

  function onEachFeature(feature, lyr) {
    lyr.on({
      mouseover: highlightFeature,
      mouseout: resetHighlight,
      click: e => {
        L.DomEvent.stopPropagation(e);
        selectIris(e.target);
      }
    });
  }

  function renderLegend() {
    const cfg = VAR_CONFIG[currentVar];
    const { breaks, varUsed } = getBreaks(currentVar);
    const isPct = cfg.hasPct && currentMode === 'pct';
    const fmtFn = isPct ? cfg.format : (cfg.hasPct ? cfg.formatAbs : cfg.format);
    const html = ['<div style="font-weight:600;margin-bottom:3px;color:#1e3a5f;">' + cfg.label + (cfg.hasPct ? (isPct ? ' (%)' : ' (Total)') : '') + '</div>'];
    for (let i = 0; i < cfg.palette.length; i++) {
      html.push(`<div class="iris-leg-row"><div class="iris-leg-swatch" style="background:${cfg.palette[i]};opacity:${opacity};"></div><span class="iris-leg-label">${fmtFn(breaks[i])} – ${fmtFn(breaks[i+1])}</span></div>`);
    }
    document.getElementById('iris-legend').innerHTML = html.join('');
  }

  function buildLayer() {
    if (layer) { map.removeLayer(layer); layer = null; selectedLayer = null; }
    if (!document.getElementById('iris-on-cb').checked) { renderLegend(); return; }
    layer = L.geoJSON(data, { style: styleFeature, onEachFeature }).addTo(map);
    layer.bringToBack();
    renderLegend();
  }

  function setVar(btn) {
    document.querySelectorAll('.iris-var-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentVar = btn.dataset.var;
    const cfg = VAR_CONFIG[currentVar];
    buildLayer();
  }
  function toggleCollapse() {
    document.getElementById('iris-panel-wrap').classList.toggle('collapsed');
    document.getElementById('iris-panel-body').classList.toggle('collapsed');
  }

  // === Listeners ===
  document.getElementById('iris-on-cb').addEventListener('change', buildLayer);
  document.getElementById('iris-opacity-slider').addEventListener('input', e => {
    opacity = parseInt(e.target.value) / 100;
    document.getElementById('iris-opacity-val').textContent = e.target.value + '%';
    if (layer) layer.eachLayer(l => l.setStyle(styleFeature(l.feature)));
    renderLegend();
  });

  // Clic sur la map (fallback quand le clic tombe sur une zone sans IRIS interactif ou via un marker)
  map.on('click', e => {
    // Vérifier si le clic n'a pas déjà été géré par un marker (e.originalEvent.target n'est pas la map)
    // En Leaflet, si on clique sur un marker, map.click ne se déclenche pas par défaut
    // Donc ce handler fonctionne pour les zones vides
    const feat = findIrisAtLatLng(e.latlng);
    if (feat) {
      // Trouver le layer correspondant et le sélectionner
      layer.eachLayer(l => {
        if (l.feature.properties.CODE_IRIS === feat.properties.CODE_IRIS) {
          selectIris(l);
        }
      });
    }
  });

  // Hook supplémentaire : intercepter le clic sur les markers laveries pour aussi
  // mettre à jour la sidebar IRIS (en complément de l'ouverture du popup laverie)
  setTimeout(() => {
    Object.keys(window).forEach(key => {
      if (key.startsWith('circle_marker_') && window[key] && window[key].on) {
        window[key].on('click', function(e) {
          const latlng = this.getLatLng();
          const feat = findIrisAtLatLng(latlng);
          if (feat && layer) {
            layer.eachLayer(l => {
              if (l.feature.properties.CODE_IRIS === feat.properties.CODE_IRIS) {
                if (selectedLayer && selectedLayer !== l) layer.resetStyle(selectedLayer);
                selectedLayer = l;
                l.setStyle({ weight: 3, color: '#7c3aed', fillOpacity: Math.min(opacity + 0.2, 1) });
                l.bringToBack(); // garder sous le marker
                showDetail(feat.properties);
              }
            });
          }
        });
      }
    });
    console.log('[IrisLayer] Markers hook installé');
  }, 500);

  window.IrisLayer = { setVar, toggleCollapse, closeDetail, showDetail };

  buildLayer();

  // Empêcher conflits map
  ['iris-panel-wrap', 'iris-detail-wrap'].forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      L.DomEvent.disableClickPropagation(el);
      L.DomEvent.disableScrollPropagation(el);
    }
  });

  console.log('[IrisLayer] v24 chargée : ' + data.features.length + ' IRIS (Paris + 92)');
})();
</script>
"""

COMPONENT = COMPONENT.replace('__GEOJSON__', GJSON)
COMPONENT = COMPONENT.replace('__MAP_VAR__', MAP_VAR)

new_html = html.replace('</html>', COMPONENT + '\n</html>')

with open(HTML_OUT, 'w') as f:
    f.write(new_html)

import os
print(f"✅ v24 écrite : {HTML_OUT}")
print(f"   Taille : {os.path.getsize(HTML_OUT):,} octets")
