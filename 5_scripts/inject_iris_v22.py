#!/usr/bin/env python3
"""Injecte une couche choroplèthe IRIS du 92 sur la carte v21 → v22."""
import json, re

HTML_IN  = '/home/claude/workspace/outputs/carte_prospection_etape3a_v21_clean.html'
HTML_OUT = '/home/claude/workspace/outputs/carte_prospection_etape3a_v22_iris.html'
GEOJSON  = '/home/claude/workspace/iris/iris_92_enriched.geojson'

with open(HTML_IN) as f:
    html = f.read()

m = re.search(r'(map_[a-f0-9]{20,})\s*=\s*L\.map', html)
MAP_VAR = m.group(1)

with open(GEOJSON) as f:
    iris_gj = json.load(f)

# Nettoyer les NaN/null dans les properties
import math
for feat in iris_gj['features']:
    p = feat['properties']
    for k, v in list(p.items()):
        if isinstance(v, float) and math.isnan(v):
            p[k] = None
print(f"Features chargées : {len(iris_gj['features'])}")

GEOJSON_JSON = json.dumps(iris_gj, ensure_ascii=False, separators=(',', ':'))
SIZE_KB = len(GEOJSON_JSON) // 1024

COMPONENT = """
<style>
#iris-panel-wrap {
  position: absolute;
  bottom: 20px;
  left: 12px;
  z-index: 1000;
  width: 280px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
  font-size: 12px;
}
#iris-panel-card {
  background: rgba(255,255,255,0.98);
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.18);
  border: 1px solid rgba(0,0,0,0.08);
  overflow: hidden;
}
#iris-panel-header {
  background: linear-gradient(135deg, #1e3a5f, #2c5282);
  color: white;
  padding: 8px 12px;
  font-weight: 600;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  user-select: none;
}
#iris-panel-header .chevron { transition: transform 0.2s; }
#iris-panel-wrap.collapsed #iris-panel-header .chevron { transform: rotate(-90deg); }
#iris-panel-body { padding: 10px; }
#iris-panel-body.collapsed { display: none; }
#iris-toggle-on {
  display: flex; align-items: center; gap: 6px;
  margin-bottom: 8px; font-size: 11px; color: #444;
  cursor: pointer; user-select: none;
}
.iris-var-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px;
  margin-bottom: 8px;
}
.iris-var-btn {
  padding: 5px 6px;
  font-size: 10px;
  background: #ecf0f1;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  text-align: center;
  transition: all 0.1s;
  user-select: none;
  color: #333;
}
.iris-var-btn:hover { background: #d6dbdf; }
.iris-var-btn.active {
  background: linear-gradient(135deg, #2c5282, #1e3a5f);
  color: white;
  border-color: #1e3a5f;
  font-weight: 600;
}
.iris-mode-row {
  display: flex; gap: 4px;
  margin-bottom: 8px;
  font-size: 10px;
}
.iris-mode-btn {
  flex: 1;
  padding: 4px;
  background: #f4f4f5;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  text-align: center;
}
.iris-mode-btn.active {
  background: #34495e;
  color: white;
  border-color: #34495e;
}
#iris-legend {
  border-top: 1px solid #eee;
  padding-top: 6px;
  margin-top: 4px;
  font-size: 10px;
}
.iris-leg-row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 1px 0;
}
.iris-leg-swatch {
  width: 18px;
  height: 12px;
  border: 1px solid rgba(0,0,0,0.15);
  border-radius: 2px;
  flex-shrink: 0;
}
.iris-leg-label { color: #555; }
#iris-opacity-row {
  display: flex; align-items: center; gap: 6px;
  margin-top: 8px; font-size: 10px; color: #666;
}
#iris-opacity-slider {
  flex: 1;
  margin: 0;
  height: 4px;
}
#iris-source {
  font-size: 9px; color: #999;
  margin-top: 6px;
  font-style: italic;
}
.iris-popup-table {
  font-size: 11px;
  border-collapse: collapse;
}
.iris-popup-table td {
  padding: 2px 6px 2px 0;
}
.iris-popup-table td:first-child {
  color: #666;
  text-align: right;
}
.iris-popup-table td:last-child {
  font-weight: 600;
  color: #1a1a1a;
}
.iris-popup-title {
  font-weight: 700;
  font-size: 13px;
  color: #1e3a5f;
  margin-bottom: 4px;
}
.iris-popup-meta {
  font-size: 10px;
  color: #777;
  margin-bottom: 6px;
  padding-bottom: 4px;
  border-bottom: 1px solid #eee;
}
@media (max-width: 600px) {
  #iris-panel-wrap { width: calc(100vw - 24px); }
}
</style>

<div id="iris-panel-wrap">
  <div id="iris-panel-card">
    <div id="iris-panel-header" onclick="IrisLayer.toggleCollapse()">
      <span>📊 IRIS INSEE 92</span>
      <span class="chevron">▼</span>
    </div>
    <div id="iris-panel-body">
      <label id="iris-toggle-on">
        <input type="checkbox" id="iris-on-cb" checked />
        <span>Afficher la couche IRIS</span>
      </label>
      <div class="iris-var-grid">
        <div class="iris-var-btn active" data-var="P22_NPER_RP" onclick="IrisLayer.setVar(this)">👥 Habitants</div>
        <div class="iris-var-btn" data-var="PCT_PROP" onclick="IrisLayer.setVar(this)">🏠 Propriétaires</div>
        <div class="iris-var-btn" data-var="PCT_T1_T2" onclick="IrisLayer.setVar(this)">🛏️ T1+T2</div>
        <div class="iris-var-btn" data-var="P22_RP" onclick="IrisLayer.setVar(this)">🏘️ Ménages</div>
      </div>
      <div class="iris-mode-row" id="iris-mode-row">
        <div class="iris-mode-btn" data-mode="abs" onclick="IrisLayer.setMode(this)">Total</div>
        <div class="iris-mode-btn" data-mode="pct" onclick="IrisLayer.setMode(this)">%</div>
      </div>
      <div id="iris-legend"></div>
      <div id="iris-opacity-row">
        <span>Opacité</span>
        <input type="range" id="iris-opacity-slider" min="0" max="100" value="55" />
        <span id="iris-opacity-val">55%</span>
      </div>
      <div id="iris-source">Source : INSEE recensement 2022 — base IC Logement (616 IRIS)</div>
    </div>
  </div>
</div>

<script>
window.IRIS_DATA = __GEOJSON__;

(function() {
  const map = window.__MAP_VAR__;
  const data = window.IRIS_DATA;

  // Configuration des variables
  const VAR_CONFIG = {
    'P22_NPER_RP': {
      label: 'Habitants',
      palette: ['#eff6ff','#bfdbfe','#7eb1ee','#3b82e0','#1e4b9c'],
      hasPct: false,
      format: v => Math.round(v).toLocaleString('fr-FR'),
      unit: ''
    },
    'PCT_PROP': {
      label: '% Propriétaires',
      varAbs: 'P22_RP_PROP',
      palette: ['#dcfce7','#a3eab8','#65d186','#2ea556','#196b32'],
      hasPct: true,
      format: v => v.toFixed(1) + '%',
      formatAbs: v => Math.round(v).toLocaleString('fr-FR'),
      unit: '%'
    },
    'PCT_T1_T2': {
      label: '% T1+T2',
      varAbs: 'T1_T2',
      palette: ['#fff7ed','#fed7aa','#fb923c','#ea580c','#9a3412'],
      hasPct: true,
      format: v => v.toFixed(1) + '%',
      formatAbs: v => Math.round(v).toLocaleString('fr-FR'),
      unit: '%'
    },
    'P22_RP': {
      label: 'Résid. principales',
      palette: ['#f5f3ff','#ddd6fe','#a78bfa','#7c3aed','#4c1d95'],
      hasPct: false,
      format: v => Math.round(v).toLocaleString('fr-FR'),
      unit: ''
    }
  };

  let currentVar = 'P22_NPER_RP';
  let currentMode = 'abs'; // 'abs' ou 'pct'
  let opacity = 0.55;
  let layer = null;

  // Calcul des breaks (quintiles) pour une variable donnée
  function getBreaks(varKey) {
    const cfg = VAR_CONFIG[varKey];
    let actualVar = varKey;
    if (cfg.hasPct && currentMode === 'abs') actualVar = cfg.varAbs;
    if (!cfg.hasPct) actualVar = varKey;

    const values = data.features
      .map(f => f.properties[actualVar])
      .filter(v => v !== null && v !== undefined && !isNaN(v))
      .sort((a, b) => a - b);
    if (values.length === 0) return { breaks: [0,1,2,3,4,5], varUsed: actualVar };
    // Quintiles
    const q = (p) => values[Math.floor(values.length * p)];
    const breaks = [values[0], q(0.2), q(0.4), q(0.6), q(0.8), values[values.length-1]];
    return { breaks, varUsed: actualVar };
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
      opacity: 0.7,
      color: '#1e3a5f',
      fillOpacity: v === null ? 0.1 : opacity
    };
  }

  function highlightFeature(e) {
    const layer = e.target;
    layer.setStyle({
      weight: 2.5,
      color: '#1a1a1a',
      fillOpacity: Math.min(opacity + 0.15, 1)
    });
    layer.bringToFront();
  }

  function resetHighlight(e) {
    layer.resetStyle(e.target);
  }

  function buildPopup(props) {
    const fmt = v => v != null ? Math.round(v).toLocaleString('fr-FR') : '—';
    const pct = (n, d) => (n != null && d) ? (n / d * 100).toFixed(1) + '%' : '—';
    const rp = props.P22_RP || 0;
    return `
      <div class="iris-popup-title">${props.NOM_IRIS || 'IRIS ' + props.CODE_IRIS}</div>
      <div class="iris-popup-meta">${props.NOM_COM || ''} · IRIS ${props.CODE_IRIS} · type ${props.TYP_IRIS || '?'}</div>
      <table class="iris-popup-table">
        <tr><td>Habitants (rés. princ.)</td><td>${fmt(props.P22_NPER_RP)}</td></tr>
        <tr><td>Résid. principales</td><td>${fmt(props.P22_RP)}</td></tr>
        <tr><td>Propriétaires</td><td>${fmt(props.P22_RP_PROP)} (${pct(props.P22_RP_PROP, rp)})</td></tr>
        <tr><td>Locataires</td><td>${pct(rp - (props.P22_RP_PROP||0), rp)}</td></tr>
        <tr><td>T1 (1 pièce)</td><td>${fmt(props.P22_RP_1P)} (${pct(props.P22_RP_1P, rp)})</td></tr>
        <tr><td>T2 (2 pièces)</td><td>${fmt(props.P22_RP_2P)} (${pct(props.P22_RP_2P, rp)})</td></tr>
        <tr><td><b>T1+T2 cumulés</b></td><td><b>${fmt(props.T1_T2)} (${pct(props.T1_T2, rp)})</b></td></tr>
      </table>
    `;
  }

  function onEachFeature(feature, lyr) {
    lyr.on({
      mouseover: highlightFeature,
      mouseout: resetHighlight,
      click: e => {
        const popup = L.popup({maxWidth: 320, className: 'iris-popup'})
          .setLatLng(e.latlng)
          .setContent(buildPopup(feature.properties))
          .openOn(map);
      }
    });
  }

  function renderLegend() {
    const cfg = VAR_CONFIG[currentVar];
    let { breaks, varUsed } = getBreaks(currentVar);
    const isPct = cfg.hasPct && currentMode === 'pct';
    const fmt = isPct ? cfg.format : (cfg.hasPct ? cfg.formatAbs : cfg.format);

    const html = ['<div style="font-weight:600;margin-bottom:3px;color:#1e3a5f;">' + cfg.label + (isPct ? ' (%)' : '') + '</div>'];
    for (let i = 0; i < cfg.palette.length; i++) {
      const from = breaks[i], to = breaks[i+1];
      html.push(`<div class="iris-leg-row">
        <div class="iris-leg-swatch" style="background:${cfg.palette[i]};opacity:${opacity};"></div>
        <span class="iris-leg-label">${fmt(from)} – ${fmt(to)}</span>
      </div>`);
    }
    document.getElementById('iris-legend').innerHTML = html.join('');
  }

  function buildLayer() {
    if (layer) {
      map.removeLayer(layer);
      layer = null;
    }
    if (!document.getElementById('iris-on-cb').checked) {
      renderLegend();
      return;
    }
    layer = L.geoJSON(data, {
      style: styleFeature,
      onEachFeature: onEachFeature
    }).addTo(map);
    layer.bringToBack();
    renderLegend();
  }

  function setVar(btn) {
    document.querySelectorAll('.iris-var-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentVar = btn.dataset.var;
    // Activer/désactiver le toggle mode selon variable
    const cfg = VAR_CONFIG[currentVar];
    document.getElementById('iris-mode-row').style.display = cfg.hasPct ? 'flex' : 'none';
    if (cfg.hasPct) {
      document.querySelectorAll('.iris-mode-btn').forEach(b => {
        b.classList.toggle('active', b.dataset.mode === currentMode);
      });
    }
    buildLayer();
  }

  function setMode(btn) {
    document.querySelectorAll('.iris-mode-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentMode = btn.dataset.mode;
    buildLayer();
  }

  function toggleCollapse() {
    document.getElementById('iris-panel-wrap').classList.toggle('collapsed');
    document.getElementById('iris-panel-body').classList.toggle('collapsed');
  }

  // Listeners
  document.getElementById('iris-on-cb').addEventListener('change', buildLayer);
  document.getElementById('iris-opacity-slider').addEventListener('input', e => {
    opacity = parseInt(e.target.value) / 100;
    document.getElementById('iris-opacity-val').textContent = e.target.value + '%';
    if (layer) layer.setStyle(styleFeature);
    renderLegend();
  });

  // Init mode display (par défaut sur Habitants qui n'a pas de mode)
  document.getElementById('iris-mode-row').style.display = 'none';
  // Préselectionner 'pct' comme mode par défaut sur les variables qui le supportent
  document.querySelector('[data-mode="pct"]').classList.add('active');
  currentMode = 'pct';

  window.IrisLayer = { setVar, setMode, toggleCollapse };

  // Init carte
  buildLayer();

  // Empêcher conflits avec carte
  const wrap = document.getElementById('iris-panel-wrap');
  L.DomEvent.disableClickPropagation(wrap);
  L.DomEvent.disableScrollPropagation(wrap);

  console.log('[IrisLayer] Couche IRIS chargée : ' + data.features.length + ' IRIS du 92');
})();
</script>
"""

COMPONENT = COMPONENT.replace('__GEOJSON__', GEOJSON_JSON)
COMPONENT = COMPONENT.replace('__MAP_VAR__', MAP_VAR)

new_html = html.replace('</html>', COMPONENT + '\n</html>')

with open(HTML_OUT, 'w') as f:
    f.write(new_html)

import os
print(f"Carte v22 écrite : {HTML_OUT}")
print(f"Taille : {os.path.getsize(HTML_OUT):,} octets (+ {os.path.getsize(HTML_OUT) - os.path.getsize(HTML_IN):,} pour IRIS)")
