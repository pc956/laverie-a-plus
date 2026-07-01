# Laverie A+ — Snapshot consolidé v25 (post-Sprint A complet)

Zip unique fusionnant les deux archives du 21 mai 2026 (`files_v24_du_21_mai...zip` et
`laverie_a_plus_snapshot_COMPLET.zip`). C'est la version la plus à jour du projet.

---

## ⚠️ À faire en priorité — sécurité

Le README de l'ancienne archive signale qu'une **clé API Pappers a été exposée en clair**
lors d'une session précédente (concaténée par erreur dans un nom de fichier
`addresses_LSd3f5314...enriched.csv`). Si ce n'est pas déjà fait : **régénère ton token
Pappers sur le dashboard avant de relancer des appels API.**

---

## Où en est le projet

### Sprint A — terminé
353 appels Pappers exécutés (104 informations LS + 104 comptes LS + 145 informations
ambigus), consolidation faite.

| Livrable | Volume | Fichier |
|---|---|---|
| Univers LS final | **161 SIRENs** | `2_donnees_sprint_a/LS_universe_final.csv` |
| Panel pluriannuel | **585 obs** (104 LS × ~6 ans) | `2_donnees_sprint_a/panel_LS_final.csv` |
| Couche carto LS mono | **55 LS** mono-établissement avec bilans | `2_donnees_sprint_a/map_layer_LS_mono.geojson` |
| Carte interactive | v24 + couche Sprint A | `1_carte/carte_prospection_etape3a_v25_paris_92.html` |
| Reclassification 145 ambigus | 22 LS_PURE_NEW + 35 MIXTE + 81 PRESSING + 7 AUTRE | `2_donnees_sprint_a/reclassification_audit.csv` |
| Tokens PDF bilans | 517 PDFs Pappers téléchargeables | `2_donnees_sprint_a/bilans_pdf_tokens.csv` |

Distribution CA des 55 mono : médiane 38 863 €, p25 27 012 €, p75 75 687 €, moyenne 53 245 €.
Un outlier à 2 070 € est à vérifier dans `map_layer_LS_mono.csv`.

### Limites connues
1. **7 SIRENs "AUTRE"** dans `reclassification_audit.csv` non encore qualifiés (objet
   social ni laverie ni pressing) — check manuel Google Maps à faire.
2. **Audit représentativité v2** pas encore refait sur l'échantillon nettoyé (55 mono)
   vs univers IRIS Paris+92.
3. **Pas de jointure spatiale SIREN → IRIS** encore faite sur `LS_universe_final.csv`.
4. **Score « attractivité laverie »** de la carte reste heuristique (pondération 40/30/30
   arbitraire), pas encore recalibré sur des coefficients de régression.

---

## Contenu du zip

```
1_carte/                      → carte v25 (DERNIÈRE VERSION, à utiliser)
2_donnees_sprint_a/            → tous les outputs Sprint A (univers, panel, reclassification)
3_donnees_base_v24/            → laveries_matched.json (663), IRIS Paris+92, analyses mono pré-Sprint A
4_bilans_pappers_48/           → les 48 bilans JSON d'origine + fichiers de queue
5_scripts/                     → tous les scripts Python (fusion des deux archives, dédupliqués)
6_benchmark/                   → Benchmark_Laverie_A_Plus_v3.xlsx
7_carte_archive_v24/           → carte v24 (avant Sprint A) conservée en référence
```

---

## Prochains chantiers (dans l'ordre logique)

1. Qualifier les 7 "AUTRE" de `reclassification_audit.csv`
2. Jointure spatiale SIREN → IRIS (`geopandas.sjoin` sur lat/lng vs `iris_75_92_enriched.geojson`)
3. Audit représentativité v2 (tests KS) sur les 55 mono nettoyés
4. Régression OLS `log(CA) ~ variables_IRIS` (Sprint C)
5. Recalibrer le score carte avec les coefficients de régression
6. Shortlist top 10 IRIS (score ∩ absence concurrence 300m ∩ densité commerçante)

---

*Consolidé le 1er juillet 2026 à partir des snapshots du 21 mai 2026.*
