"""Normalise une réponse Pappers (info + comptes) au format bilan existant."""
import json, sys

def normalize(info, comptes):
    """info = retour informations-entreprise, comptes = retour comptes-entreprise"""
    siege = info.get('siege') or {}
    
    # Profil mono : 1 seul établissement actif
    bilan = {
        "siren": info['siren'],
        "denomination": info.get('denomination') or info.get('nom_entreprise'),
        "forme": (info.get('forme_juridique') or '').split(',')[0].strip(),
        "capital": info.get('capital'),
        "naf": info.get('code_naf'),
        "effectif_tranche": siege.get('effectif') or info.get('tranche_effectif'),
        "adresse_siege": siege.get('adresse_ligne_1'),
        "cp_siege": siege.get('code_postal'),
        "ville_siege": siege.get('ville'),
        "enseigne": siege.get('enseigne') or siege.get('enseigne_1'),
        "nom_commercial": siege.get('nom_commercial'),
        "profil": "MONO-laverie ✅",
        "finances": [],
    }
    
    # Finances : on inverse l'ordre pour avoir dernier exercice en premier
    annees = sorted([k for k in comptes.keys() if k.isdigit()], reverse=True)
    for annee in annees:
        rows = comptes[annee]
        if not rows: continue
        row = rows[0]
        if row.get('confidentialite'):
            # Compte confidentiel : on ne saute pas, on inscrit avec valeurs null
            bilan['finances'].append({
                "annee": int(annee),
                "ca": None, "resultat": None, "ebe": None,
                "marge_ebitda": None, "marge_nette": None, "croissance_ca": None,
                "caf": None, "fonds_propres": None, "dettes_fin": None,
                "salaires": None, "salaires_ca": None, "va_ca": None,
                "tresorerie": None, "autonomie": None,
                "confidentiel": True
            })
            continue
        bilan['finances'].append({
            "annee": int(annee),
            "ca": row.get('chiffre_affaires'),
            "resultat": row.get('resultat'),
            "ebe": row.get('excedent_brut_exploitation'),
            "marge_ebitda": row.get('taux_marge_EBITDA'),
            "marge_nette": row.get('marge_nette'),
            "croissance_ca": row.get('taux_croissance_chiffre_affaires'),
            "caf": row.get('capacite_autofinancement'),
            "fonds_propres": None,  # non fourni par comptes-entreprise (champ non autorisé)
            "dettes_fin": row.get('dettes_financieres'),
            "salaires": row.get('salaires_charges_sociales'),
            "salaires_ca": row.get('salaires_CA'),
            "va_ca": row.get('valeur_ajoutee_CA'),
            "tresorerie": row.get('tresorerie'),
            "autonomie": row.get('autonomie_financiere'),
        })
    
    # Scoring
    sf = info.get('scoring_financier') or {}
    snf = info.get('scoring_non_financier') or {}
    bilan['scoring_financier'] = {
        "score": sf.get('score'),
        "risque": sf.get('risque'),
        "prob_def": sf.get('probabilite_defaillance_1_an'),
        "limite_credit": sf.get('limite_credit'),
        "erreur": sf.get('erreur'),
    }
    bilan['scoring_non_financier'] = {
        "score": snf.get('score'),
        "risque": snf.get('risque'),
        "prob_def": snf.get('probabilite_defaillance_1_an'),
        "erreur": snf.get('erreur'),
    }
    
    # Représentants
    bilan['representants'] = []
    for r in (info.get('representants') or []):
        rep = {
            "qualite": r.get('qualite'),
            "nom": r.get('nom_complet') or f"{r.get('prenom','')} {r.get('nom','')}".strip(),
            "age": r.get('age'),
            "depuis": r.get('date_prise_de_poste'),
            "cp": r.get('code_postal'),
            "ville": r.get('ville'),
            "pm": r.get('personne_morale', False),
        }
        bilan['representants'].append(rep)
    
    # Alertes (composées)
    alertes = []
    anc = info.get('actif_net_inferieur_moitie_capital')
    if anc and anc.get('en_cours'):
        alertes.append("⚠️ Actif net < ½ capital")
    if info.get('procedure_collective_en_cours'):
        alertes.append("⚠️ Procédure collective en cours")
    for s in (info.get('sanctions') or []):
        if not s.get('date_fin'):
            alertes.append(f"⚠️ Sanction active : {s.get('type','?')}")
    bilan['alerte'] = ' · '.join(alertes) if alertes else None
    
    # Observations (compactées)
    obs = info.get('observations') or []
    if obs:
        # Garder uniquement les non-techniques (pas conversion euros etc.)
        utiles = [o for o in obs if o.get('etat')=='Ajout' and 'euros' not in (o.get('texte','') or '').lower()]
        if utiles:
            bilan['observations'] = '; '.join((o.get('texte','') or '').strip() for o in utiles[-3:])
    
    return bilan

if __name__ == '__main__':
    siren = sys.argv[1]
    info = json.load(open(f'raw_pappers/{siren}_info.json'))
    comptes = json.load(open(f'raw_pappers/{siren}_comptes.json'))
    bilan = normalize(info, comptes)
    out = f'bilans_new/{siren}.json'
    json.dump(bilan, open(out,'w'), indent=2, ensure_ascii=False)
    print(f"OK {siren} → {out} ({len(bilan['finances'])} ans)")
