#!/usr/bin/env python3
"""
inject_v25.py — Carte Laverie A+ : ajoute la couche "55 LS mono confirmées Sprint A"
                avec bilans pluriannuels en popup, par-dessus la v24.

Input (dossier courant ou paths CLI) :
  --carte    carte_prospection_etape3a_v24_paris_92.html
  --geojson  map_layer_LS_mono.geojson      (sortie de build_map_layer.py)
  --panel    panel_LS_final.csv             (sortie de finalize_sprint_a.py)

Output :
  carte_prospection_etape3a_v25_paris_92.html

Différenciation visuelle vs v24 :
- Markers carrés vert→rouge selon marge_nette dernier exercice
- Taille proportionnelle au log(CA)
- Toggle layer dédié dans un mini-panneau bottom-right

Usage :
  python inject_v25.py
  (ou)  python inject_v25.py --carte ... --geojson ... --panel ...
"""

import json, re, csv, math, argparse, sys
from pathlib import Path
from collections import defaultdict

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--carte",   default="carte_prospection_etape3a_v24_paris_92.html")
    ap.add_argument("--geojson", default="map_layer_LS_mono.geojson")
    ap.add_argument("--panel",   default="panel_LS_final.csv")
    ap.add_argument("--out",     default="carte_prospection_etape3a_v25_paris_92.html")
    return ap.parse_args()

def to_float(x):
    if x is None or x == "" or x == "None":
        return None
    try: return float(x)
    except: return None

def main():
    args = parse_args()
    for p in (args.carte, args.geojson, args.panel):
        if not Path(p).exists():
            sys.exit(f"ERREUR : fichier manquant : {p}")

    # 1) Carte HTML
    with open(args.carte, encoding="utf-8") as f:
        html = f.read()
    m = re.search(r'(map_[a-f0-9]{20,})\s*=\s*L\.map', html)
    if not m: sys.exit("ERREUR : impossible de trouver la variable map_xxx dans la carte v24.")
    MAP_VAR = m.group(1)
    print(f"  Carte v24 : {len(html):,} caractères, MAP_VAR={MAP_VAR[:25]}…")

    # 2) GeoJSON 55 LS mono
    with open(args.geojson, encoding="utf-8") as f:
        gj = json.load(f)
    print(f"  GeoJSON   : {len(gj['features'])} features (LS mono Sprint A)")

    # 3) Panel pluriannuel par SIREN → enrichit le geojson avec l'historique
    panel_by_siren = defaultdict(list)
    with open(args.panel, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            panel_by_siren[r["siren"]].append(r)

    for feat in gj["features"]:
        siren = feat["properties"].get("siren")
        rows = sorted(
            panel_by_siren.get(siren, []),
            key=lambda x: int(x["annee"]) if x["annee"].isdigit() else 0,
            reverse=True,
        )
        history = []
        for r in rows[:7]:  # 7 dernières années max pour le popup
            history.append({
                "annee": r["annee"],
                "ca": to_float(r["chiffre_affaires"]),
                "res": to_float(r["resultat"]),
                "ebe": to_float(r["excedent_brut_exploitation"]),
                "mn": to_float(r["marge_nette"]),
                "tr": to_float(r["tresorerie"]),
                "df": to_float(r["dettes_financieres"]),
            })
        feat["properties"]["history"] = history

    GJSON = json.dumps(gj, ensure_ascii=False, separators=(",", ":"))

    # 4) Composant JS injecté
    COMPONENT = """
<style>
/* Panneau toggle Sprint A en bas à droite */
#sa-panel { position:absolute; bottom:20px; right:12px; z-index:1000;
  background:rgba(255,255,255,0.98); border-radius:8px;
  box-shadow:0 4px 16px rgba(0,0,0,0.18); border:1px solid rgba(0,0,0,0.08);
  font-family:-apple-system,BlinkMacSystemFont,system-ui,sans-serif; font-size:12px;
  padding:8px 12px; max-width:240px; }
#sa-panel-header { font-weight:600; color:#0a6e3d; display:flex; align-items:center; gap:6px; margin-bottom:4px;}
#sa-panel-header .badge { background:#0a6e3d; color:white; font-size:10px; padding:1px 6px; border-radius:10px; }
#sa-toggle-row { display:flex; align-items:center; gap:6px; margin-top:4px; color:#444;}
#sa-legend { margin-top:8px; padding-top:6px; border-top:1px solid #eee; font-size:10px; color:#666;}
.sa-leg-row { display:flex; align-items:center; gap:6px; padding:2px 0; }
.sa-leg-dot { width:12px; height:12px; border-radius:2px; border:1px solid rgba(0,0,0,0.2); flex-shrink:0; }
.sa-popup { font-family:-apple-system,system-ui,sans-serif; font-size:12px; min-width:280px; }
.sa-popup h3 { margin:0 0 4px 0; font-size:13px; color:#0a6e3d; }
.sa-popup .sa-tag { display:inline-block; padding:1px 6px; background:#e7f5ee; color:#0a6e3d;
  border-radius:10px; font-size:10px; font-weight:600; margin-left:4px; }
.sa-popup .sa-addr { color:#666; font-size:11px; margin-bottom:6px; }
.sa-popup table { width:100%; border-collapse:collapse; margin-top:4px; font-size:11px; }
.sa-popup th { text-align:left; background:#f4f4f5; padding:3px 6px; font-weight:600; color:#333; border-bottom:1px solid #ddd; }
.sa-popup td { padding:2px 6px; border-bottom:1px solid #f0f0f0; }
.sa-popup td.num { text-align:right; font-variant-numeric:tabular-nums; }
.sa-popup .sa-meta { margin-top:6px; font-size:10px; color:#888; font-style:italic; }
.sa-popup .pos { color:#0a6e3d; }
.sa-popup .neg { color:#c0392b; }
</style>

<div id="sa-panel">
  <div id="sa-panel-header">🧺 Sprint A — LS mono <span class="badge">__N__</span></div>
  <div id="sa-toggle-row">
    <input type="checkbox" id="sa-on-cb" checked>
    <label for="sa-on-cb">Afficher la couche</label>
  </div>
  <div id="sa-legend">
    <div style="font-weight:600;color:#333;margin-bottom:3px;">Marge nette dernière année</div>
    <div class="sa-leg-row"><div class="sa-leg-dot" style="background:#2ecc71;"></div><span>≥ 10 % (rentable)</span></div>
    <div class="sa-leg-row"><div class="sa-leg-dot" style="background:#f39c12;"></div><span>0 – 10 %</span></div>
    <div class="sa-leg-row"><div class="sa-leg-dot" style="background:#e74c3c;"></div><span>&lt; 0 % (déficitaire)</span></div>
    <div class="sa-leg-row"><div class="sa-leg-dot" style="background:#95a5a6;"></div><span>n/c</span></div>
    <div style="margin-top:6px;color:#999;font-size:9px;">Taille ∝ log(CA dernier)</div>
  </div>
</div>

<script>
(function(){
  var data = __GEOJSON__;
  var map = __MAP_VAR__;
  var layer = null;

  function fmt(n){ if(n==null||isNaN(n)) return '–'; return Math.round(n).toLocaleString('fr-FR'); }
  function fmtPct(n){ if(n==null||isNaN(n)) return '–'; return (n>=0?'+':'') + n.toFixed(1) + '%'; }

  function colorFromMargin(mn){
    if(mn==null||isNaN(mn)) return '#95a5a6';
    if(mn >= 10) return '#2ecc71';
    if(mn >= 0)  return '#f39c12';
    return '#e74c3c';
  }
  function radiusFromCA(ca){
    if(!ca||ca<=0) return 6;
    var r = Math.log10(ca) * 2.5;
    return Math.max(5, Math.min(16, r));
  }

  function buildPopup(p){
    var hist = p.history || [];
    var last = hist[0] || {};
    var prev = hist[1] || {};
    var deltaCA = (last.ca && prev.ca && prev.ca > 0) ? ((last.ca-prev.ca)/prev.ca*100) : null;
    var arrow = deltaCA==null ? '' : (deltaCA>=0 ? '<span class="pos">▲</span>' : '<span class="neg">▼</span>');

    var rows = hist.map(h => {
      var mnCls = (h.mn!=null) ? (h.mn>=0?'pos':'neg') : '';
      return `<tr>
        <td>${h.annee}</td>
        <td class="num">${fmt(h.ca)}</td>
        <td class="num">${fmt(h.res)}</td>
        <td class="num">${fmt(h.ebe)}</td>
        <td class="num ${mnCls}">${h.mn!=null ? h.mn.toFixed(1)+'%' : '–'}</td>
      </tr>`;
    }).join('');

    var meta = [];
    if(p.classification) meta.push(p.classification);
    if(p.date_creation) meta.push('créé ' + p.date_creation);
    if(p.procedure_collective && p.procedure_collective !== 'False') meta.push('⚠ procédure collective');

    return `<div class="sa-popup">
      <h3>${p.nom || '(sans nom)'} <span class="sa-tag">${p.classification || 'LS'}</span></h3>
      <div class="sa-addr">${p.adresse || ''}, ${p.code_postal || ''} ${p.ville || ''}</div>
      <div style="font-size:11px;">
        Dernier exercice <b>${last.annee || '–'}</b> :
        <b>${fmt(last.ca)} €</b> CA ${arrow}${deltaCA!=null ? ' '+fmtPct(deltaCA) : ''}
        &nbsp;•&nbsp; marge ${last.mn!=null ? last.mn.toFixed(1)+'%' : '–'}
        &nbsp;•&nbsp; ${p.nb_annees_bilans} bilan${p.nb_annees_bilans>1?'s':''}
      </div>
      <table>
        <thead><tr><th>Année</th><th>CA</th><th>Résultat</th><th>EBE</th><th>Marge n.</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
      <div class="sa-meta">SIREN ${p.siren}${p.enseigne ? ' • '+p.enseigne : ''} • ${meta.join(' • ')}</div>
    </div>`;
  }

  function buildLayer(){
    if(layer){ map.removeLayer(layer); layer=null; }
    if(!document.getElementById('sa-on-cb').checked) return;

    layer = L.geoJSON(data, {
      pointToLayer: function(feat, latlng){
        var p = feat.properties;
        var mn = (p.history && p.history[0]) ? p.history[0].mn : null;
        return L.circleMarker(latlng, {
          radius: radiusFromCA(p.ca_dernier),
          fillColor: colorFromMargin(mn),
          color: '#0a6e3d',
          weight: 2,
          opacity: 0.9,
          fillOpacity: 0.85
        });
      },
      onEachFeature: function(feat, lay){
        lay.bindPopup(buildPopup(feat.properties), {maxWidth: 360, minWidth: 290});
      }
    }).addTo(map);
    layer.bringToFront();
  }

  document.getElementById('sa-on-cb').addEventListener('change', buildLayer);
  buildLayer();
})();
</script>
"""

    n_features = len(gj["features"])
    COMPONENT = COMPONENT.replace("__GEOJSON__", GJSON)
    COMPONENT = COMPONENT.replace("__MAP_VAR__", MAP_VAR)
    COMPONENT = COMPONENT.replace("__N__", str(n_features))

    new_html = html.replace("</html>", COMPONENT + "\n</html>")

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(new_html)

    print(f"\n✅ v25 écrite : {args.out}")
    print(f"   Taille : {Path(args.out).stat().st_size:,} octets")
    print(f"   {n_features} LS mono Sprint A injectées par-dessus la v24")
    print(f"\nOuvre {args.out} dans ton navigateur (double-clic).")

if __name__ == "__main__":
    main()
