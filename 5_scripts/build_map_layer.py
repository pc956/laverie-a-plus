#!/usr/bin/env python3
"""
build_map_layer.py — Construit la couche cartographique des LS mono-établissement avec bilans.

Filtre : has_panel_data=1 AND flag_multi_etabs=0
Pour chaque SIREN, agrège les ratios sur les années dispos :
- CA dernier exercice + moyenne 5Y + min/max
- Résultat / EBE / marge nette
- Dette financière, trésorerie (dernier)

Inputs (dossier courant) :
- LS_universe_final.csv      (sortie de finalize_sprint_a.py)
- panel_LS_final.csv         (sortie de finalize_sprint_a.py)

Outputs :
- map_layer_LS_mono.csv      → tableur classique (1 ligne = 1 SIREN)
- map_layer_LS_mono.geojson  → directement chargeable Mapbox / Leaflet / Folium / QGIS

Usage : python build_map_layer.py
"""

import csv, json, statistics
from pathlib import Path

def read_csv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))

def to_float(x):
    if x is None or x == "" or x == "None":
        return None
    try:
        return float(x)
    except (ValueError, TypeError):
        return None

def main():
    print("=" * 60)
    print("Lecture des inputs")
    print("=" * 60)
    universe = read_csv("LS_universe_final.csv")
    panel = read_csv("panel_LS_final.csv")
    print(f"  Univers total : {len(universe)} SIRENs")
    print(f"  Panel total   : {len(panel)} obs")

    # Filtre univers : has_panel_data=1 AND flag_multi_etabs=0
    mono_ls = [u for u in universe
               if u.get("has_panel_data") == "1" and u.get("flag_multi_etabs") == "0"]
    print(f"\n  Mono-LS avec bilans : {len(mono_ls)} / {len(universe)}")

    mono_sirens = {u["siren"] for u in mono_ls}

    # Group panel rows par SIREN
    panel_by_siren = {}
    for r in panel:
        s = r["siren"]
        if s not in mono_sirens:
            continue
        panel_by_siren.setdefault(s, []).append(r)

    print(f"  SIRENs mono avec obs panel effectives : {len(panel_by_siren)}")

    # Agrégation par SIREN
    print("\n" + "=" * 60)
    print("Agrégation panel → ratios par SIREN")
    print("=" * 60)
    rows_out = []
    for u in mono_ls:
        siren = u["siren"]
        years = panel_by_siren.get(siren, [])
        if not years:
            continue
        # Tri par année desc
        years_sorted = sorted(years, key=lambda x: int(x["annee"]) if x["annee"].isdigit() else 0, reverse=True)

        ca_list = [to_float(y["chiffre_affaires"]) for y in years_sorted]
        ca_list = [c for c in ca_list if c is not None and c > 0]  # exclure 0 et None
        res_list = [to_float(y["resultat"]) for y in years_sorted if to_float(y["resultat"]) is not None]
        ebe_list = [to_float(y["excedent_brut_exploitation"]) for y in years_sorted if to_float(y["excedent_brut_exploitation"]) is not None]
        mn_list = [to_float(y["marge_nette"]) for y in years_sorted if to_float(y["marge_nette"]) is not None]

        last_year_row = years_sorted[0] if years_sorted else {}
        last_year_int = int(last_year_row.get("annee", 0) or 0)

        # Stats CA (excl. zéros et nulls)
        ca_dernier = ca_list[0] if ca_list else None
        ca_avg = round(statistics.mean(ca_list)) if ca_list else None
        ca_avg_5y = round(statistics.mean(ca_list[:5])) if ca_list else None
        ca_min = round(min(ca_list)) if ca_list else None
        ca_max = round(max(ca_list)) if ca_list else None

        # Tendance CA (delta dernier vs avant-dernier)
        ca_delta_yoy_pct = None
        if len(ca_list) >= 2 and ca_list[1] > 0:
            ca_delta_yoy_pct = round((ca_list[0] - ca_list[1]) / ca_list[1] * 100, 1)

        rows_out.append({
            "siren": siren,
            "nom": u.get("nom_pappers", ""),
            "enseigne": u.get("enseigne", ""),
            "nom_commercial": u.get("nom_commercial", ""),
            "classification": u.get("classification_finale", ""),
            "adresse": u.get("adresse_ligne_1", ""),
            "code_postal": u.get("code_postal", ""),
            "ville": u.get("ville", ""),
            "latitude": to_float(u.get("latitude")),
            "longitude": to_float(u.get("longitude")),
            "date_creation": u.get("date_creation", ""),
            "nb_annees_bilans": len(ca_list),
            "annee_derniere": last_year_int if last_year_int else None,
            "ca_dernier": ca_dernier,
            "ca_avg_5y": ca_avg_5y,
            "ca_avg_total": ca_avg,
            "ca_min": ca_min,
            "ca_max": ca_max,
            "ca_delta_yoy_pct": ca_delta_yoy_pct,
            "res_dernier": round(res_list[0]) if res_list else None,
            "res_avg": round(statistics.mean(res_list)) if res_list else None,
            "ebe_dernier": round(ebe_list[0]) if ebe_list else None,
            "ebe_avg": round(statistics.mean(ebe_list)) if ebe_list else None,
            "marge_nette_avg": round(statistics.mean(mn_list), 1) if mn_list else None,
            "dette_financiere_dernier": to_float(last_year_row.get("dettes_financieres")),
            "tresorerie_dernier": to_float(last_year_row.get("tresorerie")),
            "procedure_collective": u.get("procedure_collective_en_cours", "False"),
        })

    # Filtre final : drop les SIRENs sans lat/lng (pas plottables)
    rows_geocoded = [r for r in rows_out if r["latitude"] and r["longitude"]]
    rows_no_geo = len(rows_out) - len(rows_geocoded)
    if rows_no_geo:
        print(f"  ⚠ {rows_no_geo} SIRENs sans lat/lng, exclus de la carte")
    print(f"  ✓ {len(rows_geocoded)} SIRENs geocodés prêts pour carto")

    # --- Output 1 : CSV ---
    fieldnames = list(rows_geocoded[0].keys())
    with open("map_layer_LS_mono.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows_geocoded)
    print(f"\n✓ map_layer_LS_mono.csv ({len(rows_geocoded)} lignes)")

    # --- Output 2 : GeoJSON ---
    features = []
    for r in rows_geocoded:
        props = {k: v for k, v in r.items() if k not in ("latitude", "longitude")}
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [r["longitude"], r["latitude"]]
            },
            "properties": props
        })
    geojson = {"type": "FeatureCollection", "features": features}
    with open("map_layer_LS_mono.geojson", "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False)
    print(f"✓ map_layer_LS_mono.geojson ({len(features)} features)")

    # --- Récap stats CA ---
    print("\n" + "=" * 60)
    print("Distribution CA dernier exercice (sur les LS geocodées)")
    print("=" * 60)
    ca_d = sorted([r["ca_dernier"] for r in rows_geocoded if r["ca_dernier"]])
    if ca_d:
        n = len(ca_d)
        print(f"  n          : {n}")
        print(f"  min        : {round(ca_d[0]):>10} €")
        print(f"  p25        : {round(ca_d[n//4]):>10} €")
        print(f"  médiane    : {round(ca_d[n//2]):>10} €")
        print(f"  p75        : {round(ca_d[3*n//4]):>10} €")
        print(f"  max        : {round(ca_d[-1]):>10} €")
        print(f"  moyenne    : {round(sum(ca_d)/n):>10} €")

    print("\n✓ Layer carto prêt. Charge `map_layer_LS_mono.geojson` dans Mapbox/Leaflet/Folium/QGIS.")

if __name__ == "__main__":
    main()
