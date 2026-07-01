"""
Référence pour boucler les 16 mono-laveries restantes.

USAGE : Ce fichier sert de référence à Claude dans une nouvelle conversation.
Les outils Pappers MCP ne sont exposés qu'à Claude (pas à un script Python).

Workflow à suivre par Claude :

1. Charger /home/claude/bilans/_queue_mono.json (16 SIRENs)
2. Pour chaque SIREN, appeler en parallèle (par batches de 8) :
   - Pappers:informations-entreprise(siren, return_fields=[...])
   - Pappers:comptes-entreprise(siren, return_fields=[...])
3. Persister les réponses brutes dans raw_pappers/{siren}_info.json et {siren}_comptes.json
4. Exécuter normalize_bilan.py sur chaque SIREN
5. Mettre à jour _queue_mono.json (retirer les traités)
6. Lancer inject_v19.py → carte v20
7. Régénérer Benchmark_Laverie_A_Plus_v4.xlsx

Champs requis informations-entreprise :
  ["siren", "denomination", "forme_juridique", "capital", "code_naf", "siege",
   "representants", "scoring_financier", "scoring_non_financier", "procedure_collective_en_cours"]

Champs requis comptes-entreprise :
  ["chiffre_affaires", "resultat", "excedent_brut_exploitation",
   "taux_croissance_chiffre_affaires", "taux_marge_EBITDA", "marge_nette",
   "capacite_autofinancement", "tresorerie", "dettes_financieres",
   "salaires_charges_sociales", "salaires_CA", "valeur_ajoutee_CA",
   "autonomie_financiere"]

Liste ordonnée des 16 SIRENs restants :
"""

QUEUE_16 = [
    "821614450",  # LAVERIE SAINT PETERSBOURG, 75008
    "834318628",  # LAVERIE DU POTEAU, 75018
    "850855065",  # LAVERIE N12, 75012
    "531057867",  # YS LAVERIE, 75014
    "809487739",  # AU FIL DE L'EAU, 92240
    "749905097",  # LAV'NADHIF, 92800
    "845236868",  # LAVERIES SPEED WASH, 92400
    "483359030",  # LE FER A LA MAIN, 92150
    "903047975",  # SARL FASO, 92230
    "841717416",  # SWHAT SERVICE, 92600
    "504408477",  # 3.A, 83300
    "378107775",  # BRITOPHE, 92200
    "542023163",  # SOC AUTOMATIC LAVERY, 75016
    "642057681",  # ROYAL PRESSING BERRI, 75008
    "790557920",  # JINANE, 75019
    "790979900",  # JM LAVERIE, 92110
]

if __name__ == '__main__':
    print(f"Queue mono restante : {len(QUEUE_16)} SIRENs")
    print("Ce script ne fait rien tout seul — Claude doit l'utiliser comme référence.")
    print("Voir README.md pour le workflow complet.")
