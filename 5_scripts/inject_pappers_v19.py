#!/usr/bin/env python3
"""Injecte Pappers + bilans détaillés dans les popups. v18."""
import json, re, html as htmlmod, os

HTML_IN = '/home/claude/workspace/inputs/carte_prospection_etape3a_v9.html'
HTML_OUT = '/home/claude/workspace/outputs/carte_prospection_etape3a_v19_bilans.html'

# Charger laveries + matchs
with open('/home/claude/workspace/inputs/laveries_matched.json') as f:
    laveries = json.load(f)
match_by_marker = {l['marker_id']: l for l in laveries}

# Charger tous les bilans collectés
bilans = {}
for fn in os.listdir('/home/claude/workspace/bilans'):
    if fn.endswith('.json') and not fn.startswith('_') and fn != 'to_fetch.json':
        siren = fn.replace('.json','')
        bilans[siren] = json.load(open(f'/home/claude/workspace/bilans/{fn}'))

print(f"Loaded {len(match_by_marker)} laveries, {len(bilans)} bilans en base")

with open(HTML_IN) as f:
    html_content = f.read()

chunks = html_content.split('var circle_marker_')
print(f"Chunks: {len(chunks)}")

new_chunks = [chunks[0]]
enriched = 0
with_bilan = 0
etabs_cesses = 0
with_enseigne = 0

def fmt_eur(v):
    if v is None or v == 0: return '—'
    return f"{int(v):,} €".replace(',', ' ')

def get_last_fin(bilan):
    """Renvoie la dernière finance avec CA non null."""
    for f in bilan.get('finances', []):
        if f.get('ca') and f['ca'] != 0:
            return f
    return None

def color_marge(v, good=15, bad=5):
    if v is None: return '#95a5a6'
    if v >= good: return '#27ae60'
    if v >= bad: return '#f39c12'
    return '#e74c3c'

def color_score(score_str):
    if not score_str: return '#95a5a6'
    try:
        n = float(str(score_str).replace('/20','').replace(',','.').strip())
        if n >= 14: return '#27ae60'
        if n >= 9: return '#f39c12'
        return '#e74c3c'
    except: return '#95a5a6'

def build_bilan_block(siren, bilan):
    """Construit le bloc HTML détaillé pour les bilans."""
    last = get_last_fin(bilan)
    if not last:
        return f"""<div style='margin-top:6px;padding:5px 7px;background:#f8f9fa;border-radius:4px;font-size:10px;color:#888;'>
📊 <b>Bilans Pappers</b> : comptes confidentiels ou trop anciens</div>"""
    
    annee = last.get('annee', '?')
    ca = last.get('ca')
    ebe = last.get('ebe')
    marge_eb = last.get('marge_ebitda')
    marge_n = last.get('marge_nette')
    croissance = last.get('croissance_ca')
    salaires_ca = last.get('salaires_ca')
    
    sf = bilan.get('scoring_financier') or {}
    snf = bilan.get('scoring_non_financier') or {}
    
    parts = []
    parts.append(f"""<div style='margin-top:6px;padding:6px 8px;background:linear-gradient(135deg,#fef9e7 0%,#fff 100%);border-left:3px solid #f39c12;border-radius:4px;font-size:10px;'>
<div style='font-weight:700;color:#7d6608;margin-bottom:4px;'>📊 Bilan {annee}</div>""")
    
    # Tableau compact
    lines = []
    if ca:
        cstr = f"<span style='color:#27ae60;font-weight:600;'>+{croissance:.1f}%</span>" if croissance and croissance > 0 else (f"<span style='color:#e74c3c;font-weight:600;'>{croissance:.1f}%</span>" if croissance else "")
        lines.append(f"<div><b>CA</b> : {fmt_eur(ca)} {cstr}</div>")
    if ebe is not None:
        lines.append(f"<div><b>EBE</b> : {fmt_eur(ebe)}</div>")
    if marge_eb is not None:
        c = color_marge(marge_eb, 20, 10)
        lines.append(f"<div><b>Marge EBITDA</b> : <span style='color:{c};font-weight:700;'>{marge_eb:.1f}%</span></div>")
    if marge_n is not None:
        c = color_marge(marge_n, 10, 3)
        lines.append(f"<div><b>Marge nette</b> : <span style='color:{c};font-weight:700;'>{marge_n:.1f}%</span></div>")
    if salaires_ca is not None and salaires_ca > 0:
        c = '#e74c3c' if salaires_ca > 35 else ('#f39c12' if salaires_ca > 20 else '#27ae60')
        lines.append(f"<div><b>Salaires/CA</b> : <span style='color:{c};font-weight:600;'>{salaires_ca:.1f}%</span></div>")
    
    parts.append(''.join(lines))
    
    # Scoring
    sf_score = sf.get('score')
    snf_score = snf.get('score')
    if sf_score or snf_score:
        parts.append("<div style='margin-top:4px;padding-top:4px;border-top:1px dashed #ddd;'>")
        if sf_score:
            c = color_score(sf_score)
            parts.append(f"<span style='background:{c};color:white;padding:1px 5px;border-radius:3px;font-size:9px;font-weight:600;margin-right:3px;'>Fin. {sf_score}</span>")
        if snf_score:
            c = color_score(snf_score)
            parts.append(f"<span style='background:{c};color:white;padding:1px 5px;border-radius:3px;font-size:9px;font-weight:600;'>NonFin. {snf_score}</span>")
        parts.append("</div>")
    
    # Dirigeant principal
    reps = bilan.get('representants', [])
    main_rep = None
    for r in reps:
        if r.get('qualite') in ['Président','Gérant','Président du directoire','Directeur général']:
            main_rep = r
            break
    if not main_rep and reps:
        main_rep = reps[0]
    if main_rep:
        nom = main_rep.get('nom','')
        age = main_rep.get('age')
        qual = main_rep.get('qualite','')
        if main_rep.get('pm'):
            parts.append(f"<div style='margin-top:3px;font-size:9px;color:#555;'>👤 <b>{qual}</b> : {htmlmod.escape(str(nom))} (PM)</div>")
        else:
            age_str = f", {age} ans" if age else ""
            parts.append(f"<div style='margin-top:3px;font-size:9px;color:#555;'>👤 <b>{qual}</b> : {htmlmod.escape(str(nom))}{age_str}</div>")
    
    # Alerte
    alerte = bilan.get('alerte')
    if alerte:
        parts.append(f"<div style='margin-top:3px;padding:2px 4px;background:#fadbd8;color:#922b21;border-radius:2px;font-size:9px;font-weight:600;'>{htmlmod.escape(str(alerte))}</div>")
    
    # Observations
    obs = bilan.get('observations')
    if obs:
        parts.append(f"<div style='margin-top:3px;font-size:9px;color:#555;font-style:italic;'>{htmlmod.escape(str(obs)[:150])}</div>")
    
    parts.append("</div>")
    return ''.join(parts)

for chunk in chunks[1:]:
    m_id = re.match(r'^([a-f0-9]+)\s*=', chunk)
    if not m_id:
        new_chunks.append('var circle_marker_' + chunk)
        continue
    marker_id = m_id.group(1)
    laverie = match_by_marker.get(marker_id)
    if not laverie:
        new_chunks.append('var circle_marker_' + chunk)
        continue
    
    match = laverie.get('pappers_match')
    match_type = laverie.get('match_type', '')
    
    pappers_parts = []
    
    if match:
        enriched += 1
        siren = match['siren']
        siren_f = f"{siren[:3]} {siren[3:6]} {siren[6:]}"
        nom_legal = match.get('nom_legal','') or match.get('nom','')
        enseigne = match.get('enseigne_etab')
        nc_etab = match.get('nom_commercial_etab')
        cap = match.get('cap')
        forme = match.get('forme','')
        rcs = match.get('rcs','')
        rcs_color = '#27ae60' if rcs=='Inscrit' else ('#e74c3c' if rcs=='Radié' else '#95a5a6')
        is_siege = match.get('is_siege', False)
        etab_cesse = match.get('etab_cesse', False)
        ca = match.get('chiffre_affaires')
        res = match.get('resultat')
        
        if enseigne or nc_etab: with_enseigne += 1
        if etab_cesse: etabs_cesses += 1
        
        conf_label = {'exact':'✓','fuzzy-num-close':'~','same-street':'?'}.get(match_type,'?')
        conf_color = {'exact':'#27ae60','fuzzy-num-close':'#f39c12','same-street':'#95a5a6'}.get(match_type,'#95a5a6')
        
        if enseigne or nc_etab:
            ens_disp = htmlmod.escape(enseigne or nc_etab)
            pappers_parts.append(f"<div style='background:#9b59b6;color:white;padding:2px 6px;border-radius:3px;display:inline-block;font-size:10px;font-weight:600;margin-bottom:4px;'>🏷️ {ens_disp}</div>")
        if etab_cesse:
            pappers_parts.append(f"<div style='background:#e74c3c;color:white;padding:2px 6px;border-radius:3px;display:inline-block;font-size:10px;font-weight:600;margin-bottom:4px;margin-left:4px;'>⚠️ Étab. cessé</div>")
        
        type_etab = "Siège" if is_siege else "Étab. secondaire"
        ca_str = fmt_eur(ca)
        res_str = fmt_eur(res)
        
        pappers_parts.append(f"""<div style='margin-top:8px;padding-top:6px;border-top:1px solid #eee;font-size:11px;'>
<div style='display:flex;align-items:center;gap:6px;margin-bottom:3px;'>
<b style='color:#2c3e50;'>📋 Pappers</b>
<span style='background:{conf_color};color:white;padding:1px 5px;border-radius:3px;font-size:9px;font-weight:600;'>{conf_label}</span>
<span style='color:#888;font-size:9px;'>{type_etab}</span>
</div>
<div><b>{htmlmod.escape(nom_legal)}</b> ({forme})</div>
<div style='color:#555;'>SIREN <a href='https://www.pappers.fr/entreprise/{siren}' target='_blank' style='color:#2980b9;text-decoration:none;'>{siren_f}</a></div>
<div style='color:#555;'>Capital : {fmt_eur(cap)} · CA : {ca_str} · Résultat : {res_str}</div>
<div><span style='color:{rcs_color};font-weight:600;'>● {rcs}</span> · NAF {match.get('naf_etab','')}</div>
</div>""")
        
        # AJOUT : bloc bilan si disponible
        if siren in bilans:
            with_bilan += 1
            pappers_parts.append(build_bilan_block(siren, bilans[siren]))
        
        pappers_html = ''.join(pappers_parts)
    else:
        pappers_html = "<div style='margin-top:8px;padding-top:6px;border-top:1px solid #eee;font-size:10px;color:#aaa;'>📋 Pappers : non identifié</div>"
    
    pappers_html_escaped = pappers_html.replace('`','\\`').replace('$','\\$')
    
    new_chunk = re.sub(
        r"(<div style='font-size:9px;color:#aaa;margin-top:8px;'>Source[^<]*</div>)(</div>`\)\[0\];)",
        pappers_html_escaped + r"\1\2",
        chunk, count=1
    )
    new_chunks.append('var circle_marker_' + new_chunk)

new_html = ''.join(new_chunks)

with open(HTML_OUT, 'w', encoding='utf-8') as f:
    f.write(new_html)

print(f"Enriched: {enriched}")
print(f"Avec bilan détaillé : {with_bilan}")
print(f"Avec enseigne/NC : {with_enseigne}")
print(f"Étabs cessés : {etabs_cesses}")
print(f"Size: {len(new_html):,} bytes")
print(f"Written to {HTML_OUT}")
