"""
Tests de bon sens (sanity checks) - pas une suite de tests exhaustive,
mais une vérification rapide que rien n'est cassé ou absurde avant de
montrer l'outil. A relancer après chaque modification des modules.
Grand Large Patrimoine - projet de stage
"""

import numpy as np

from fiscalite import (
    applique_abattement_salaire,
    brut_depuis_cout_total,
    calcul_ir,
    calcul_is,
    charges_sur_brut,
    net_apres_dividende,
    net_apres_salaire,
    PASS_2026,
)
from simulation import PROFILS, simulation_comparaison
from trajectoire import comparer
from demembrement import (
    calcul_droits_donation,
    comparer_transmission,
    pourcentage_usufruit,
    valeur_usufruit_nue_propriete,
)

echecs = []


def verifier(nom, condition):
    statut = "OK" if condition else "ECHEC"
    if not condition:
        echecs.append(nom)
    print(f"[{statut}] {nom}")


# --- Cas limites évidents ---
verifier("montant=0 -> net salaire = 0", net_apres_salaire(0) == 0)
verifier("montant=0 -> net dividende = 0", net_apres_dividende(0) == 0)
verifier("net salaire(0) < net salaire(80000)", net_apres_salaire(0) < net_apres_salaire(80_000))

# --- Monotonie : plus de montant disponible => plus de net, jamais moins ---
montants = [10_000, 30_000, 60_000, 100_000, 200_000]
nets_salaire = [net_apres_salaire(m) for m in montants]
nets_dividende = [net_apres_dividende(m) for m in montants]
verifier("net salaire strictement croissant avec le montant", all(b > a for a, b in zip(nets_salaire, nets_salaire[1:])))
verifier("net dividende strictement croissant avec le montant", all(b > a for a, b in zip(nets_dividende, nets_dividende[1:])))

# --- IR : jamais négatif, jamais > au revenu imposable ---
for revenu in [0, 5_000, 50_000, 500_000]:
    ir = calcul_ir(revenu)
    verifier(f"IR({revenu}) >= 0", ir >= 0)
    verifier(f"IR({revenu}) <= revenu", ir <= revenu)

# --- IS : jamais négatif, cohérent avec le seuil à 42 500 € ---
verifier("IS(42500) == 42500*0.15", abs(calcul_is(42_500) - 42_500 * 0.15) < 0.01)
verifier("IS(100000) > IS(42500)", calcul_is(100_000) > calcul_is(42_500))

# --- Charges sociales : le passage du seuil PASS ne doit pas créer de saut absurde ---
brut_avant_pass = PASS_2026 - 1
brut_apres_pass = PASS_2026 + 1
charges_avant, _ = charges_sur_brut(brut_avant_pass)
charges_apres, _ = charges_sur_brut(brut_apres_pass)
ecart_relatif = abs(charges_apres - charges_avant) / charges_avant
verifier("pas de saut brutal de charges employeur autour du PASS (<1% d'écart pour 2€ de brut)", ecart_relatif < 0.01)

# --- Abattement 10% : respecte le plancher et le plafond ---
verifier("abattement minimum appliqué sur petit salaire", applique_abattement_salaire(1_000) == 1_000 - 509)
verifier("abattement plafonné sur gros salaire", applique_abattement_salaire(500_000) == 500_000 - 14_555)

# --- Dichotomie brut<->coût : doit retomber sur ses pieds (aller-retour cohérent) ---
for cout in [20_000, 80_000, 150_000, 300_000]:
    brut = brut_depuis_cout_total(cout)
    charges_employeur, _ = charges_sur_brut(brut)
    cout_recalcule = brut + charges_employeur
    verifier(f"dichotomie cohérente pour un coût de {cout}€ (écart < 1€)", abs(cout_recalcule - cout) < 1)

# --- Trajectoire déterministe : la holding ne doit jamais partir derrière en année 1 ---
resultat_det = comparer(profit_annuel=50_000, rendement=0.05, horizon_annees=10)
verifier("année 1 identique entre direct et holding (rien n'a encore composé)", abs(resultat_det["directe"][0] - resultat_det["holding_net"][0]) < 1)
verifier("la trajectoire est strictement croissante (direct)", all(b > a for a, b in zip(resultat_det["directe"], resultat_det["directe"][1:])))
verifier("la trajectoire est strictement croissante (holding)", all(b > a for a, b in zip(resultat_det["holding_net"], resultat_det["holding_net"][1:])))

# --- Simulation Monte-Carlo : reproductibilité avec une graine fixée ---
r1 = simulation_comparaison(50_000, 0.05, 0.08, 10, nb_simulations=500, graine=42)
r2 = simulation_comparaison(50_000, 0.05, 0.08, 10, nb_simulations=500, graine=42)
verifier("même graine => mêmes résultats (reproductible)", np.allclose(r1["directe"][50], r2["directe"][50]))

# --- Simulation : la médiane doit rester dans un ordre de grandeur raisonnable du cas déterministe ---
for profil, parametres in PROFILS.items():
    resultat_simu = simulation_comparaison(50_000, parametres["rendement_moyen"], parametres["volatilite"], 10, nb_simulations=3000, graine=1)
    resultat_det_profil = comparer(50_000, parametres["rendement_moyen"], 10)
    ecart_pct = abs(resultat_simu["directe"][50][-1] - resultat_det_profil["directe"][-1]) / resultat_det_profil["directe"][-1]
    verifier(f"profil {profil} : médiane simulée proche du déterministe (< 5% d'écart)", ecart_pct < 0.05)

# --- Simulation : P10 <= médiane <= P90, à chaque année ---
r = simulation_comparaison(50_000, 0.05, 0.08, 10, nb_simulations=1000, graine=7)
ordre_ok = all(
    r["directe"][10][i] <= r["directe"][50][i] <= r["directe"][90][i]
    for i in range(10)
)
verifier("P10 <= médiane <= P90 à chaque année (direct)", ordre_ok)

# --- Démembrement : barème 669, cas limites et cohérence économique ---
verifier("usufruit 90% avant 21 ans", pourcentage_usufruit(20) == 0.90)
verifier("usufruit 80% à 21 ans (bascule)", pourcentage_usufruit(21) == 0.80)
verifier("usufruit 10% après 91 ans", pourcentage_usufruit(95) == 0.10)
verifier("usufruit + nue-propriété = 100% de la valeur", all(
    abs(sum(valeur_usufruit_nue_propriete(age, 100_000)) - 100_000) < 0.01
    for age in [10, 25, 45, 65, 85, 95]
))
verifier("démembrement ne coûte jamais plus cher que la pleine propriété", all(
    comparer_transmission(400_000, age)["economie_droits"] >= 0 for age in [25, 45, 65, 85]
))
verifier("cas 400k€ / 65 ans : économie exacte de 32 000€ (vérifié à la main)", abs(comparer_transmission(400_000, 65)["economie_droits"] - 32_000) < 1)
verifier("sous l'abattement (100k€), aucun droit des deux côtés", comparer_transmission(90_000, 65)["droits_pleine_propriete"] == 0 and comparer_transmission(90_000, 65)["droits_demembrement"] == 0)

print()
if echecs:
    print(f"{len(echecs)} échec(s) : {echecs}")
else:
    print("Tous les tests passent.")
