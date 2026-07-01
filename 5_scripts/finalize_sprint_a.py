#!/usr/bin/env python3
"""
finalize_sprint_a.py — Consolidation finale du Sprint A SANS aucun appel Pappers.

Pure merge / reclassif des données déjà récupérées :
1. Reclassifie les 145 ambigus (regex sur objet_social → LS_PURE_NEW / MIXTE / PRESSING / AUTRE)
2. Construit l'univers final : 104 LS originaux + nouveaux LS confirmés (LS_PURE_NEW + MIXTE)
3. Conserve le panel A3 tel quel (585 obs sur 104 LS, dispos pour régression)

Inputs (dans le dossier courant) :
- addresses_ambigu_enriched.csv
- addresses_LS_enriched.csv
- panel_bilans_LS.csv

Outputs :
- LS_universe_final.csv             (~161 SIRENs avec adresse + classif → join IRIS)
- panel_LS_final.csv                (copie de panel_bilans_LS.csv, 585 obs, 104 LS)
- reclassification_audit.csv        (145 ambigus reclassifiés)

Usage : python finalize_sprint_a.py
"""

import csv, re, shutil
from pathlib import Path

RX_LAVERIE = re.compile(r"laverie|self.?service|libre.?service|laundromat|laundry", re.I)
RX_PRESSING = re.compile(r"pressing|blanchiss|nettoyage", re.I)

def classify(objet_social: str) -> str:
    o = objet_social or ""
    l = bool(RX_LAVERIE.search(o))
    p = bool(RX_PRESSING.search(o))
    if l and p: return "MIXTE"
    if l:       return "LS_PURE_NEW"
    if p:       return "PRESSING"
    return "AUTRE"

def read_csv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

def main():
    print("=" * 60)
    print("ETAPE 1 : Reclassification des 145 ambigus")
    print("=" * 60)
    amb = read_csv("addresses_ambigu_enriched.csv")
    for r in amb:
        r["classification_finale"] = classify(r.get("objet_social", ""))
        r["source_classification"] = "A4_reclass"

    counts = {}
    for r in amb:
        c = r["classification_finale"]
        counts[c] = counts.get(c, 0) + 1
    for c, n in sorted(counts.items()):
        print(f"  {c:<15} {n}")

    write_csv("reclassification_audit.csv", amb, list(amb[0].keys()))
    print(f"  -> reclassification_audit.csv ({len(amb)} rows)")

    new_ls = [r for r in amb if r["classification_finale"] in ("LS_PURE_NEW", "MIXTE")]
    print(f"\n  Nouveaux LS confirmes : {len(new_ls)}")

    print("\n" + "=" * 60)
    print("ETAPE 2 : Univers final (1 SIREN = 1 ligne)")
    print("=" * 60)
    ls_orig = read_csv("addresses_LS_enriched.csv")
    print(f"  LS originales (Sprint A1+A2) : {len(ls_orig)}")

    common_fields = [
        "siren","nom_pappers","classification_finale","source_classification",
        "objet_social","code_naf","libelle_naf","forme_juridique",
        "adresse_ligne_1","code_postal","ville","latitude","longitude",
        "enseigne","nom_commercial","date_creation",
        "entreprise_cessee","date_cessation",
        "nb_etablissements_actifs","nb_etablissements_total",
        "procedure_collective_en_cours","derniere_procedure_type",
        "siret_siege","has_panel_data"
    ]

    universe = []
    for r in ls_orig:
        out = {f: r.get(f, "") for f in common_fields}
        out["classification_finale"] = "LS_INITIAL"
        out["source_classification"] = "A1_pure_or_probable"
        out["has_panel_data"] = "1"
        universe.append(out)
    for r in new_ls:
        out = {f: r.get(f, "") for f in common_fields}
        out["has_panel_data"] = "0"
        universe.append(out)

    for u in universe:
        try:
            n = int(u.get("nb_etablissements_actifs") or 0)
        except Exception:
            n = 0
        u["flag_multi_etabs"] = "1" if n > 1 else "0"

    write_csv("LS_universe_final.csv", universe, common_fields + ["flag_multi_etabs"])
    print(f"  Univers final : {len(universe)} SIRENs -> LS_universe_final.csv")

    print("\n" + "=" * 60)
    print("ETAPE 3 : Panel pluriannuel (copie de A3)")
    print("=" * 60)
    if Path("panel_bilans_LS.csv").exists():
        shutil.copy("panel_bilans_LS.csv", "panel_LS_final.csv")
        n_panel = sum(1 for _ in open("panel_LS_final.csv", encoding="utf-8")) - 1
        print(f"  -> panel_LS_final.csv ({n_panel} obs sur 104 LS)")

    print("\n" + "=" * 60)
    print("RECAP SPRINT A")
    print("=" * 60)
    by_classif = {}
    for u in universe:
        c = u["classification_finale"]
        by_classif[c] = by_classif.get(c, 0) + 1
    for c, n in sorted(by_classif.items()):
        print(f"  {c:<20} {n}")
    multi = sum(1 for u in universe if u["flag_multi_etabs"] == "1")
    with_panel = sum(1 for u in universe if u["has_panel_data"] == "1")
    print(f"\n  Multi-etablissements (flag)  : {multi}")
    print(f"  Avec donnees panel A3        : {with_panel} / {len(universe)}")
    print(f"\nOK Sprint A cloture.")
    print(f"  Pour join IRIS  : utilise LS_universe_final.csv (latitude/longitude)")
    print(f"  Pour regression : utilise panel_LS_final.csv (filtre has_panel_data=1)")

if __name__ == "__main__":
    main()
