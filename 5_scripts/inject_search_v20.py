#!/usr/bin/env python3
"""Ajoute un moteur de recherche rue/ville en haut à gauche de la carte v19 → v20."""
import json, re

HTML_IN  = '/home/claude/workspace/outputs/carte_prospection_etape3a_v19_bilans.html'
HTML_OUT = '/home/claude/workspace/outputs/carte_prospection_etape3a_v20_search.html'

with open(HTML_IN) as f:
    html = f.read()

# Trouver le nom de la variable map Folium
m = re.search(r'(map_[a-f0-9]{20,})\s*=\s*L\.map', html)
MAP_VAR = m.group(1)
print(f"Variable map détectée : {MAP_VAR}")

# Charger les données
laveries = json.load(open('/home/claude/workspace/inputs/laveries_matched.json'))

# Construire la table compacte pour JS
# On garde : id, name, addr_full, rue, cp, ville, lat, lng, color, has_match
data = []
for l in laveries:
    pm = l.get('pappers_match') or {}
    data.append({
        'id': l['marker_id'],
        'n': l.get('name') or '',
        'a': l.get('addr_full') or '',
        'r': l.get('rue') or '',
        'p': l.get('cp') or '',
        'v': l.get('ville') or '',
        'lat': l.get('lat'),
        'lng': l.get('lng'),
        'c': l.get('color') or '#3388ff',
        'm': 1 if pm.get('siren') else 0,  # matché Pappers
        'd': pm.get('nom_legal') or '',  # dénomination Pappers
    })
print(f"Données préparées : {len(data)} laveries")

DATA_JSON = json.dumps(data, ensure_ascii=False, separators=(',', ':'))

# ============== COMPOSANT À INJECTER ==============
COMPONENT = """
<style>
#lav-search-wrap {
  position: absolute;
  top: 12px;
  left: 12px;
  z-index: 1000;
  width: 340px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
  font-size: 13px;
}
#lav-search-card {
  background: rgba(255,255,255,0.98);
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.18);
  border: 1px solid rgba(0,0,0,0.08);
  overflow: hidden;
}
#lav-search-header {
  background: linear-gradient(135deg, #2c3e50, #34495e);
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
#lav-search-header .chevron { transition: transform 0.2s; }
#lav-search-body.collapsed { display: none; }
#lav-search-wrap.collapsed #lav-search-header .chevron { transform: rotate(-90deg); }
#lav-search-body { padding: 10px; }
#lav-search-input {
  width: 100%;
  border: 1px solid #ccc;
  border-radius: 6px;
  padding: 8px 30px 8px 10px;
  font-size: 13px;
  box-sizing: border-box;
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}
#lav-search-input:focus {
  border-color: #2980b9;
  box-shadow: 0 0 0 3px rgba(41,128,185,0.15);
}
.lav-clear {
  position: absolute;
  right: 18px;
  top: 50%;
  transform: translateY(-50%);
  color: #999;
  cursor: pointer;
  font-size: 16px;
  user-select: none;
  display: none;
}
.lav-clear:hover { color: #555; }
#lav-input-wrap {
  position: relative;
}
#lav-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 6px;
  font-size: 11px;
  color: #555;
}
#lav-meta .count { font-weight: 600; }
#lav-filter-toggle {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  user-select: none;
}
#lav-filter-toggle input { margin: 0; }
#lav-results {
  max-height: 320px;
  overflow-y: auto;
  margin-top: 8px;
  border-top: 1px solid #eee;
  display: none;
}
#lav-results.show { display: block; }
.lav-item {
  padding: 8px 10px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  display: flex;
  gap: 8px;
  align-items: flex-start;
  transition: background 0.1s;
}
.lav-item:hover { background: #f4f8fb; }
.lav-item:last-child { border-bottom: none; }
.lav-item .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 5px;
}
.lav-item .text { flex: 1; min-width: 0; }
.lav-item .name {
  font-weight: 600;
  color: #2c3e50;
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.lav-item .addr {
  font-size: 11px;
  color: #777;
  margin-top: 1px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.lav-item .badge {
  font-size: 9px;
  background: #ecf0f1;
  color: #555;
  padding: 1px 5px;
  border-radius: 3px;
  margin-left: 4px;
}
.lav-item .badge.matched { background: #d5f5e3; color: #1e8449; }
.lav-item mark { background: #ffeaa7; color: #2c3e50; padding: 0; }
#lav-geocoder-btn {
  margin-top: 8px;
  width: 100%;
  padding: 6px 10px;
  background: #f8f9fa;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 11px;
  color: #555;
  cursor: pointer;
  transition: background 0.1s;
}
#lav-geocoder-btn:hover { background: #ecf0f1; }
.lav-empty {
  padding: 14px;
  text-align: center;
  color: #999;
  font-size: 12px;
  font-style: italic;
}
.lav-empty button {
  display: block;
  margin: 8px auto 0;
  padding: 6px 12px;
  background: #2980b9;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 11px;
}
.lav-empty button:hover { background: #21618c; }
@media (max-width: 600px) {
  #lav-search-wrap { width: calc(100vw - 24px); }
}
</style>

<div id="lav-search-wrap">
  <div id="lav-search-card">
    <div id="lav-search-header" onclick="LavSearch.toggleCollapse()">
      <span>🔍 Rechercher une laverie</span>
      <span class="chevron">▼</span>
    </div>
    <div id="lav-search-body">
      <div id="lav-input-wrap">
        <input id="lav-search-input" type="text" placeholder="Rue, ville, code postal, enseigne…" autocomplete="off" />
        <span class="lav-clear" onclick="LavSearch.clear()">✕</span>
      </div>
      <div id="lav-meta">
        <span class="count" id="lav-count">__TOTAL__ laveries</span>
        <label id="lav-filter-toggle" title="Masquer les autres laveries sur la carte">
          <input type="checkbox" id="lav-filter-cb" />
          <span>Filtrer la carte</span>
        </label>
      </div>
      <div id="lav-results"></div>
      <button id="lav-geocoder-btn" onclick="LavSearch.geocode()">
        🌍 Centrer sur une adresse (OpenStreetMap)
      </button>
    </div>
  </div>
</div>

<script>
window.LAVERIES_DATA = __DATA__;

(function() {
  const map = window.__MAP_VAR__;
  const data = window.LAVERIES_DATA;
  const input = document.getElementById('lav-search-input');
  const results = document.getElementById('lav-results');
  const count = document.getElementById('lav-count');
  const clearBtn = document.querySelector('.lav-clear');
  const filterCb = document.getElementById('lav-filter-cb');
  const TOTAL = data.length;

  // Normalisation : minuscules + accents enlevés
  function norm(s) {
    if (!s) return '';
    return s.toString().toLowerCase()
      .normalize('NFD').replace(/[\\u0300-\\u036f]/g, '');
  }

  // Pré-calcul du champ recherchable pour chaque laverie
  data.forEach(d => {
    d._s = norm([d.n, d.d, d.a, d.r, d.p, d.v].filter(Boolean).join(' '));
  });

  let currentResults = [];
  let highlightedMarkers = [];

  function highlightText(text, query) {
    if (!query || !text) return text;
    const n = norm(text);
    const nq = norm(query);
    const idx = n.indexOf(nq);
    if (idx === -1) return text;
    return text.substring(0, idx) + '<mark>' +
           text.substring(idx, idx + query.length) + '</mark>' +
           text.substring(idx + query.length);
  }

  function search(q) {
    const nq = norm(q.trim());
    if (!nq) {
      currentResults = [];
      renderResults();
      count.textContent = TOTAL + ' laveries';
      results.classList.remove('show');
      clearBtn.style.display = 'none';
      applyFilter();
      return;
    }
    clearBtn.style.display = 'block';
    // Recherche par tokens (toutes les portions doivent matcher)
    const tokens = nq.split(/\\s+/).filter(Boolean);
    currentResults = data.filter(d => tokens.every(t => d._s.indexOf(t) !== -1));
    count.textContent = currentResults.length + ' / ' + TOTAL + ' laveries';
    renderResults(q);
    results.classList.add('show');
    applyFilter();
  }

  function renderResults(q) {
    if (currentResults.length === 0) {
      results.innerHTML = `
        <div class="lav-empty">
          Aucune laverie trouvée pour « ${escapeHtml(q || '')} »
          <button onclick="LavSearch.geocode()">🌍 Chercher cette adresse sur la carte</button>
        </div>`;
      return;
    }
    const top = currentResults.slice(0, 50);
    const html = top.map(d => {
      const name = d.d || d.n || '(sans nom)';
      const addr = [d.a, d.p, d.v].filter(Boolean).join(' · ');
      return `
        <div class="lav-item" onclick="LavSearch.goto('${d.id}')">
          <div class="dot" style="background:${d.c}"></div>
          <div class="text">
            <div class="name">${highlightText(escapeHtml(name), q)}${d.m ? '<span class="badge matched">SIREN</span>' : ''}</div>
            <div class="addr">${highlightText(escapeHtml(addr), q)}</div>
          </div>
        </div>`;
    }).join('');
    const more = currentResults.length > 50
      ? `<div class="lav-empty" style="padding:6px;">+ ${currentResults.length - 50} autres résultats — affinez votre recherche</div>`
      : '';
    results.innerHTML = html + more;
  }

  function escapeHtml(s) {
    return (s || '').toString()
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function goto(markerId) {
    const d = data.find(x => x.id === markerId);
    if (!d) return;
    const marker = window['circle_marker_' + markerId];
    if (!marker) {
      console.warn('Marker introuvable', markerId);
      // Fallback : centrer sur les coords
      map.setView([d.lat, d.lng], 17);
      return;
    }
    // Toujours assurer que le marker est ajouté à la carte
    if (!map.hasLayer(marker)) {
      marker.addTo(map);
    }
    map.setView([d.lat, d.lng], 17);
    setTimeout(() => marker.openPopup(), 350);
  }

  function applyFilter() {
    const filterOn = filterCb.checked;
    const q = input.value.trim();
    if (!filterOn || !q) {
      // Tout réafficher
      data.forEach(d => {
        const m = window['circle_marker_' + d.id];
        if (m && !map.hasLayer(m)) m.addTo(map);
      });
      return;
    }
    const visibleIds = new Set(currentResults.map(d => d.id));
    data.forEach(d => {
      const m = window['circle_marker_' + d.id];
      if (!m) return;
      if (visibleIds.has(d.id)) {
        if (!map.hasLayer(m)) m.addTo(map);
      } else {
        if (map.hasLayer(m)) map.removeLayer(m);
      }
    });
  }

  function clearSearch() {
    input.value = '';
    search('');
    input.focus();
  }

  function toggleCollapse() {
    document.getElementById('lav-search-wrap').classList.toggle('collapsed');
    document.getElementById('lav-search-body').classList.toggle('collapsed');
  }

  async function geocode() {
    const q = input.value.trim();
    if (!q) {
      input.focus();
      return;
    }
    // Nominatim — pas de clé requise mais limiter à 1 req/s
    const url = 'https://nominatim.openstreetmap.org/search?format=json&limit=5&countrycodes=fr&q=' + encodeURIComponent(q);
    try {
      const r = await fetch(url, { headers: { 'Accept-Language': 'fr' } });
      const arr = await r.json();
      if (!arr.length) {
        alert('Adresse introuvable : ' + q);
        return;
      }
      const hit = arr[0];
      const lat = parseFloat(hit.lat), lng = parseFloat(hit.lon);
      map.setView([lat, lng], 16);
      // Marker temporaire
      if (window._lavGeocodeMarker) map.removeLayer(window._lavGeocodeMarker);
      window._lavGeocodeMarker = L.marker([lat, lng], {
        icon: L.divIcon({
          html: '<div style="background:#e74c3c;color:white;border-radius:50%;width:30px;height:30px;display:flex;align-items:center;justify-content:center;font-size:16px;box-shadow:0 2px 8px rgba(0,0,0,0.3);border:2px solid white;">📍</div>',
          iconSize: [30, 30],
          iconAnchor: [15, 15],
          className: ''
        })
      }).addTo(map).bindPopup('<b>Adresse cherchée</b><br>' + escapeHtml(hit.display_name)).openPopup();
    } catch (e) {
      alert('Erreur géocodage : ' + e.message);
    }
  }

  // Listeners
  let timer;
  input.addEventListener('input', e => {
    clearTimeout(timer);
    timer = setTimeout(() => search(e.target.value), 100);
  });
  input.addEventListener('keydown', e => {
    if (e.key === 'Escape') clearSearch();
    if (e.key === 'Enter' && currentResults.length === 1) {
      goto(currentResults[0].id);
    } else if (e.key === 'Enter' && currentResults.length === 0 && input.value.trim()) {
      geocode();
    }
  });
  filterCb.addEventListener('change', applyFilter);

  // API publique
  window.LavSearch = {
    goto, clear: clearSearch, toggleCollapse, geocode, search
  };

  // Empêcher les clics carte sur le wrap
  const wrap = document.getElementById('lav-search-wrap');
  L.DomEvent.disableClickPropagation(wrap);
  L.DomEvent.disableScrollPropagation(wrap);

  console.log('[LavSearch] Moteur de recherche initialisé sur ' + TOTAL + ' laveries');
})();
</script>
"""

# Substitution des placeholders
COMPONENT = COMPONENT.replace('__DATA__', DATA_JSON)
COMPONENT = COMPONENT.replace('__MAP_VAR__', MAP_VAR)
COMPONENT = COMPONENT.replace('__TOTAL__', str(len(data)))

# Injection : juste avant </html>
new_html = html.replace('</html>', COMPONENT + '\n</html>')

with open(HTML_OUT, 'w') as f:
    f.write(new_html)

print(f"Carte v20 écrite : {HTML_OUT}")
print(f"Taille : {len(new_html):,} bytes (+ {len(new_html) - len(html):,} bytes pour le moteur)")
