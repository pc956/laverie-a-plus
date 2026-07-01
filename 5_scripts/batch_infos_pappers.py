#!/usr/bin/env python3
"""
batch_infos_pappers.py — Sprint A2 (adresses LS) & A4 (qualif ambigus).

Tape informations-entreprise pour chaque SIREN et sort un CSV enrichi :
- adresse complète (ligne_1, CP, ville)
- lat/lng (pour join IRIS INSEE)
- objet_social, code_naf (validation classification)
- nb_etablissements, état cessation, procédure collective

Input  : CSV avec au moins une colonne `siren` (autres colonnes ignorées)
Output : <prefix>_enriched.csv  +  <prefix>_full.json (audit)

Usage :
    export PAPPERS_API_KEY=ton_token  (ou $env:PAPPERS_API_KEY = "ton_token" en PowerShell)
    python batch_infos_pappers.py ls_cross_section_ready.csv addresses_LS
    python batch_infos_pappers.py ambigu_sirens.csv addresses_ambigu
"""

import os, sys, csv, json, time
from pathlib import Path
import requests

API_KEY = os.environ.get("PAPPERS_API_KEY")
if not API_KEY:
    sys.exit("ERREUR : export/set PAPPERS_API_KEY avant de lancer.")

BASE_URL = "https://api.pappers.fr/v2/entreprise"
SLEEP_SEC = 0.6
MAX_RETRIES = 3
TIMEOUT = 30

def fetch_entreprise(siren: str) -> dict:
    params = {"api_token": API_KEY, "siren": siren}
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.get(BASE_URL, params=params, timeout=TIMEOUT)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 429:
                print(f"  [{siren}] 429 sleep 10s")
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

def extract_row(siren: str, nom_orig: str, p: dict) -> dict:
    siege = p.get("siege") or {}
    etabs = p.get("etablissements") or []
    pc = p.get("procedures_collectives") or []
    pc_en_cours = any(x.get("date_fin") is None for x in pc)
    last_pc_type = pc[-1].get("type") if pc else None

    return {
        "siren": siren,
        "nom_orig": nom_orig,
        "nom_pappers": p.get("nom_entreprise") or p.get("denomination") or "",
        "objet_social": (p.get("objet_social") or "").replace("\n", " ").strip(),
        "code_naf": p.get("code_naf") or siege.get("code_naf") or "",
        "libelle_naf": p.get("libelle_code_naf") or siege.get("libelle_code_naf") or "",
        "forme_juridique": p.get("forme_juridique") or "",
        "date_creation": p.get("date_creation") or "",
        "entreprise_cessee": p.get("entreprise_cessee"),
        "date_cessation": p.get("date_cessation"),
        "adresse_ligne_1": siege.get("adresse_ligne_1") or "",
        "complement_adresse": siege.get("complement_adresse") or "",
        "code_postal": siege.get("code_postal") or "",
        "ville": siege.get("ville") or "",
        "latitude": siege.get("latitude"),
        "longitude": siege.get("longitude"),
        "enseigne": siege.get("enseigne") or "",
        "nom_commercial": siege.get("nom_commercial") or "",
        "siret_siege": siege.get("siret") or "",
        "nb_etablissements_actifs": sum(1 for e in etabs if not e.get("etablissement_cesse")),
        "nb_etablissements_total": len(etabs),
        "procedure_collective_en_cours": pc_en_cours,
        "derniere_procedure_type": last_pc_type or "",
    }

def main(input_csv: str, out_prefix: str):
    out_csv = Path(f"{out_prefix}_enriched.csv")
    out_json = Path(f"{out_prefix}_full.json")

    with open(input_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows_in = [{"siren": r["siren"], "nom": r.get("nom") or r.get("nom_entreprise") or ""} for r in reader]
    print(f"À traiter : {len(rows_in)} SIRENs")

    rows_out = []
    raw_dump = {}
    for i, r in enumerate(rows_in, 1):
        siren, nom = r["siren"], r["nom"]
        print(f"[{i}/{len(rows_in)}] {siren} {nom}")
        p = fetch_entreprise(siren)
        if not p:
            continue
        raw_dump[siren] = p
        rows_out.append(extract_row(siren, nom, p))
        time.sleep(SLEEP_SEC)

    if rows_out:
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
            w.writeheader()
            w.writerows(rows_out)
        print(f"\n✓ Enriched : {len(rows_out)} rows → {out_csv}")

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(raw_dump, f, ensure_ascii=False)
    print(f"✓ Raw : {out_json}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python batch_infos_pappers.py <input.csv> <output_prefix>")
        print("Ex   : python batch_infos_pappers.py ls_cross_section_ready.csv addresses_LS")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
