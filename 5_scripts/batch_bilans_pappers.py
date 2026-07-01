#!/usr/bin/env python3
"""
batch_bilans_pappers.py — Sprint A3 : récupération des bilans pluriannuels des 104 LS.

Input  : ls_cross_section_ready.csv (siren,nom,...)
Output : panel_bilans_LS.csv (siren,nom,annee,ca,res,mb,ebe,rexp,mn,df,tr,caf,...)
         + panel_bilans_LS_full.json (réponse Pappers brute par SIREN, pour audit)
         + bilans_pdf_tokens.csv (siren,annee,token_pdf,token_xlsx) si tu veux DL les PDF après

Usage  : 
    export PAPPERS_API_KEY=ton_token_pappers
    python batch_bilans_pappers.py ls_cross_section_ready.csv

Endpoint Pappers v2 utilisé : GET /entreprise (avec format=json)
Doc : https://www.pappers.fr/api/documentation
Rate limit : 1 req/sec par défaut (configurable via SLEEP_SEC). Pappers tolère bien.
"""

import os, sys, csv, json, time, argparse
from pathlib import Path
import requests

API_KEY = os.environ.get("PAPPERS_API_KEY")
if not API_KEY:
    sys.exit("ERREUR : export PAPPERS_API_KEY=... avant de lancer.")

BASE_URL = "https://api.pappers.fr/v2/entreprise"
SLEEP_SEC = 0.6           # 1.6 req/s, marge confortable
MAX_RETRIES = 3
TIMEOUT = 30

# Champs ratios à conserver (par année)
RATIOS = [
    "chiffre_affaires", "resultat", "marge_brute",
    "excedent_brut_exploitation", "resultat_exploitation",
    "marge_nette", "taux_marge_EBITDA", "taux_marge_operationnelle",
    "dettes_financieres", "tresorerie", "capacite_autofinancement",
    "valeur_ajoutee", "salaires_charges_sociales",
    "BFR", "ratio_endettement", "autonomie_financiere",
    "rentabilite_economique", "rentabilite_fonds_propres",
    "effectif"
]

def fetch_comptes(siren: str) -> dict:
    """Tape /entreprise sur Pappers — retourne le JSON complet (incluant comptes annuels)."""
    params = {"api_token": API_KEY, "siren": siren, "format_publications_officielles": "json"}
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.get(BASE_URL, params=params, timeout=TIMEOUT)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 429:
                print(f"  [{siren}] 429 rate-limited, sleep 10s…")
                time.sleep(10)
                continue
            if r.status_code == 404:
                print(f"  [{siren}] 404 not found")
                return {}
            print(f"  [{siren}] HTTP {r.status_code} (try {attempt+1})")
            time.sleep(2 ** attempt)
        except Exception as e:
            print(f"  [{siren}] err {e} (try {attempt+1})")
            time.sleep(2 ** attempt)
    return {}

def extract_panel_rows(siren: str, nom: str, payload: dict) -> list[dict]:
    """Extrait les ratios par année à partir du JSON Pappers."""
    rows = []
    # Pappers v2 : ratios financiers dans `finances` (liste de dicts {annee: ..., ...})
    for fin in payload.get("finances", []) or []:
        annee = fin.get("annee") or fin.get("date_cloture", "")[:4]
        if not annee:
            continue
        row = {"siren": siren, "nom": nom, "annee": annee}
        for f in RATIOS:
            row[f] = fin.get(f)
        rows.append(row)
    return rows

def extract_pdf_tokens(siren: str, payload: dict) -> list[dict]:
    """Extrait les tokens PDF des bilans pour DL ultérieur."""
    rows = []
    for c in payload.get("comptes", []) or []:
        if c.get("disponible") and c.get("token"):
            rows.append({
                "siren": siren,
                "annee": c.get("annee_cloture"),
                "date_depot": c.get("date_depot"),
                "type_comptes": c.get("type_comptes"),
                "filename_pdf": c.get("nom_fichier_pdf"),
                "token_pdf": c.get("token"),
                "filename_xlsx": c.get("nom_fichier_xlsx"),
                "token_xlsx": c.get("token_xlsx"),
            })
    return rows

def main(input_csv: str):
    out_dir = Path(".")
    panel_path = out_dir / "panel_bilans_LS.csv"
    tokens_path = out_dir / "bilans_pdf_tokens.csv"
    raw_path = out_dir / "panel_bilans_LS_full.json"

    # Load SIRENs
    with open(input_csv) as f:
        sirens = [(r["siren"], r["nom"]) for r in csv.DictReader(f)]
    print(f"À traiter : {len(sirens)} SIRENs")

    raw_dump = {}
    all_panel = []
    all_tokens = []

    for i, (siren, nom) in enumerate(sirens, 1):
        print(f"[{i}/{len(sirens)}] {siren} {nom}")
        payload = fetch_comptes(siren)
        if not payload:
            continue
        raw_dump[siren] = payload
        all_panel.extend(extract_panel_rows(siren, nom, payload))
        all_tokens.extend(extract_pdf_tokens(siren, payload))
        time.sleep(SLEEP_SEC)

    # Write panel
    if all_panel:
        with open(panel_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["siren","nom","annee"] + RATIOS)
            w.writeheader()
            w.writerows(all_panel)
        print(f"\n✓ Panel : {len(all_panel)} obs → {panel_path}")

    # Write tokens
    if all_tokens:
        with open(tokens_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(all_tokens[0].keys()))
            w.writeheader()
            w.writerows(all_tokens)
        print(f"✓ Tokens PDF : {len(all_tokens)} bilans → {tokens_path}")

    # Raw dump
    with open(raw_path, "w") as f:
        json.dump(raw_dump, f)
    print(f"✓ Raw : {raw_path}")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "ls_cross_section_ready.csv")
