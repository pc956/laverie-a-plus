# Matching GPS des 105 laveries non-matchées — Rapport

**Méthode** : Pappers `recherche-parcelles`, rayon 40 m, filtre `code_naf_occupant=96.01B`
(le point dans le code NAF est indispensable ; `9601B` renvoie 0 résultat).
Un appel par adresse Google Maps non-matchée ; les laveries 96.01B occupant une
parcelle dans le rayon sont retenues comme candidats.

## Résultats (103 adresses réelles, hors 2 marqueurs Laverie A+)

| Statut | Nombre |
|---|---|
| Match exact (numéro + rue) | 17 |
| Match par proximité (< 40 m) | 71 |
| Non-matché | 15 |
| **Taux de résolution** | **88/103 = 85 %** |

- **112 SIREN 96.01B distincts** captés, dont **77 nouveaux** (jamais rattachés dans les 558 précédents).
- **65 matchs haute-confiance** (exact ou candidat unique) → prêts à réinjecter automatiquement (`patch_laveries_matched_gps.json`).
- **23 adresses multi-candidats** non-exactes → arbitrage manuel requis (choisir par distance exacte / vérif terrain).

## Pourquoi cette méthode bat le plan initial
`recherche-parcelles` capte des laveries **absentes de `recherche-entreprises`** car
sans comptes publiés (donc hors filtre CA 1–500 k€) : JESSI-BLANC, CHAGZEL, PGH CONSEIL,
AXYDIA, VISION WASH, POWERWASH, HAIDER ET PETIT FILS (le fameux « Mini Clean »)…

## Points de vigilance pour la consolidation
1. **Multi-établissements** (rattacher par établissement, pas par SIREN) :
   PHISER ×4, JESSI-BLANC ×3, BOBILLOT SELF SERVICE ×3, CHAGZEL ×2, LAVERIE FJL ×2,
   SOC SELF SERVICE JUMIN ×2, POWERWASH ×2, WHITE BEAR FINANCE ×2, SLAV ×2.
2. **Doublons Google Maps** (2 marqueurs → 1 laverie) : idx 96/97 (Sèvres), idx 3/100 (Sèvres),
   idx 23/47 (11 rue d'Enghien).
3. **Faux positifs Google Maps** parmi les 15 non-matchés : « Bar La Laverie » (idx 87), etc.
4. **Réseaux concurrents confirmés** : Redon (PHISER, SBS SERGE BLANC SERVICE, RBS REDON BLANC SERVICE).

## Les 15 non-matchés (aucune laverie 96.01B dans 40 m)
idx 7, 16, 51, 54, 58, 67, 76, 87, 88, 92, 94, 95, 98, 99, 101 — cf. CSV colonne `flags`.
À investiguer : élargir à 60 m, vérifier fermeture, ou faux positif GMaps.

## Fichiers livrés
- `matching_gps_103_non_matchees.csv` — table complète (candidat retenu + autres candidats + flags)
- `patch_laveries_matched_gps.json` — 65 matchs haute-confiance à réinjecter dans `laveries_matched.json`
