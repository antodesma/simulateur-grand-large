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
from paniers import CLASSES_ACTIFS, PANIERS, normaliser_ponderations, rendement_volatilite_panier
from trajectoire import comparer
from demembrement import (
    calcul_droits_donation,
    calcul_droits_donation_famille,
    comparer_transmission,
    pourcentage_usufruit,
    valeur_usufruit_nue_propriete,
)
from fiscalite_tns import (
    cotisations_tns,
    net_apres_dividende_tns,
    net_apres_dividende_tns_pur,
    net_apres_remuneration_tns,
    seuil_dividendes_sans_cotisations,
)
from optimisation import analyse_sensibilite, net_total_mix, repartition_optimale
from pacte_dutreil import calcul_transmission_dutreil, TAUX_EXONERATION_DUTREIL

echecs = []


def verifier(nom, condition):
    statut = "OK" if condition else "ECHEC"
    if not condition:
        echecs.append(nom)
    print(f"[{statut}] {nom}")


def _leve_exception(fonction):
    """True si l'appel de fonction() lève bien une exception - utile pour
    vérifier qu'un cas invalide est rejeté plutôt que silencieusement mal
    calculé (ex. une division par zéro masquée)."""
    try:
        fonction()
        return False
    except Exception:
        return True


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

# --- abattement par enfant ET par parent (art. 779 CGI) : pas un abattement unique global ---
verifier(
    "2 enfants à parts égales = 2x l'abattement d'un seul enfant (sous le seuil, droits nuls des deux côtés)",
    comparer_transmission(180_000, 65, nombre_enfants=2)["droits_pleine_propriete"] == 0
)
verifier(
    "2 enfants : les droits totaux sont strictement inférieurs à ceux d'un enfant unique sur le même bien",
    comparer_transmission(500_000, 65, nombre_enfants=2)["droits_pleine_propriete"]
    < comparer_transmission(500_000, 65, nombre_enfants=1)["droits_pleine_propriete"]
)
verifier(
    "2 parents donateurs conjointement = 2x l'abattement d'un seul parent (sous 200k€, droits nuls)",
    comparer_transmission(180_000, 65, nombre_donateurs=2)["droits_pleine_propriete"] == 0
)
verifier(
    "1 enfant, 1 bien de 400k, réparti en 2 parts égales (2 enfants) : chaque part de 200k reste sous abattement -> 0€ de droits",
    comparer_transmission(200_000, 65, nombre_enfants=2)["droits_pleine_propriete"] == 0
)
verifier(
    "nombre_enfants=1 et nombre_donateurs=1 : comportement identique à l'ancienne API (non-régression)",
    comparer_transmission(400_000, 65, 1, 1)["economie_droits"] == comparer_transmission(400_000, 65)["economie_droits"]
)

# --- régime TNS (gérant majoritaire de SARL) ---
verifier(
    "cotisation minimale TNS due même à rémunération nulle (plancher forfaitaire, affiliation maintenue)",
    cotisations_tns(0) > 0
)
verifier("cotisations TNS strictement positives et inférieures à la rémunération (80k€)", 0 < cotisations_tns(80_000) < 80_000)
verifier("cotisations TNS croissantes avec la rémunération", cotisations_tns(100_000) > cotisations_tns(50_000))
verifier(
    "le régime TNS laisse plus de net que le régime assimilé salarié à montant égal (charges TNS globalement plus légères)",
    net_apres_remuneration_tns(80_000) > net_apres_salaire(80_000)
)
verifier(
    "seuil de dividende non cotisé = 10% de (capital + compte courant)",
    abs(seuil_dividendes_sans_cotisations(100_000, 20_000) - 12_000) < 0.01
)
verifier(
    "dividende entièrement sous le seuil des 10% : pas de cotisations TNS dessus",
    net_apres_dividende_tns(50_000, capital_social=1_000_000)["cotisations_exces"] == 0
)
verifier(
    "dividende très au-delà du seuil des 10% (capital quasi nul) : des cotisations TNS s'appliquent",
    net_apres_dividende_tns(80_000, capital_social=1)["cotisations_exces"] > 0
)
verifier(
    "net dividende avec capital social élevé (peu cotisé) > net dividende avec capital social quasi nul (tout cotisé)",
    net_apres_dividende_tns(80_000, capital_social=1_000_000)["net_total"]
    > net_apres_dividende_tns(80_000, capital_social=1)["net_total"]
)

res_sasu = repartition_optimale(80_000, est_sarl=False)
verifier(
    "optimiseur SASU : p=0% recoupe exactement le net dividende pur",
    abs(res_sasu["net_100_dividende"] - net_apres_dividende(80_000)) < 0.01
)
verifier(
    "optimiseur SASU : p=100% recoupe exactement le net salaire pur",
    abs(res_sasu["net_100_salaire"] - net_apres_salaire(80_000)) < 0.01
)
verifier(
    "optimiseur SASU : le point optimal n'est jamais pire que les deux extrêmes",
    res_sasu["meilleur_net"] >= res_sasu["net_100_salaire"] - 0.01
    and res_sasu["meilleur_net"] >= res_sasu["net_100_dividende"] - 0.01
)
verifier(
    "optimiseur SASU : le gain par rapport aux extrêmes n'est jamais négatif",
    res_sasu["gain_vs_extremes"] >= -0.01
)
verifier(
    "optimiseur SASU à 80k€ : l'optimum est bien un point intermédiaire (effet de seuil), pas un extrême",
    0 < res_sasu["meilleur_p_pct"] < 100
)

verifier(
    "net_apres_dividende_tns_pur = net_total - cotisation TNS minimale (rémunération nulle)",
    abs(
        net_apres_dividende_tns_pur(80_000, capital_social=10_000)
        - (net_apres_dividende_tns(80_000, capital_social=10_000)["net_total"] - cotisations_tns(0))
    ) < 0.01
)

res_sarl = repartition_optimale(80_000, est_sarl=True, capital_social=10_000)
verifier(
    "optimiseur SARL : p=0% recoupe exactement le net dividende TNS pur (cotisation minimale incluse)",
    abs(res_sarl["net_100_dividende"] - net_apres_dividende_tns_pur(80_000, capital_social=10_000)) < 0.01
)
verifier(
    "optimiseur SARL : p=100% recoupe exactement le net rémunération TNS pur",
    abs(res_sarl["net_100_salaire"] - net_apres_remuneration_tns(80_000)) < 0.01
)
verifier(
    "net_total_mix(p=0) et net_total_mix(p=1) cohérents avec repartition_optimale",
    abs(net_total_mix(80_000, 0.0, est_sarl=False) - res_sasu["net_100_dividende"]) < 0.01
    and abs(net_total_mix(80_000, 1.0, est_sarl=False) - res_sasu["net_100_salaire"]) < 0.01
)

res_dutreil = calcul_transmission_dutreil(2_000_000, nombre_enfants=2, nombre_donateurs=2)
verifier(
    "Dutreil : valeur exonérée = 75% exactement de la valeur transmise",
    abs(res_dutreil["valeur_exoneree"] - 2_000_000 * TAUX_EXONERATION_DUTREIL) < 0.01
)
verifier(
    "Dutreil : valeur exonérée + valeur taxable = valeur totale (pas de valeur perdue)",
    abs(res_dutreil["valeur_exoneree"] + res_dutreil["valeur_taxable_apres_dutreil"] - 2_000_000) < 0.01
)
verifier(
    "Dutreil : les droits avec Dutreil sont strictement inférieurs aux droits sans Dutreil",
    res_dutreil["droits_avec_dutreil"] < res_dutreil["droits_sans_dutreil"]
)
verifier(
    "Dutreil : l'économie annoncée est cohérente avec la différence des deux droits",
    abs(res_dutreil["economie"] - (res_dutreil["droits_sans_dutreil"] - res_dutreil["droits_avec_dutreil"])) < 0.01
)
verifier(
    "Dutreil : sans exonération (taux à 0), les droits avec/sans Dutreil sont strictement identiques",
    calcul_transmission_dutreil(2_000_000, 2, 2)["droits_sans_dutreil"]
    == calcul_droits_donation_famille(2_000_000, 2, 2)
)
verifier(
    "Dutreil : valeur transmise nulle -> aucun droit, aucune économie",
    calcul_transmission_dutreil(0, 2, 2)["economie"] == 0
)

for nom_panier, ponderations in PANIERS.items():
    verifier(
        f"panier {nom_panier} : la répartition somme à 100 % (±0,1 point)",
        abs(sum(ponderations.values()) - 1.0) < 0.001,
    )
verifier(
    "panier 100 % épargne sécurisée : rendement/volatilité du panier = ceux de la classe seule",
    abs(
        rendement_volatilite_panier({"epargne_securisee": 1.0})["rendement_moyen"]
        - CLASSES_ACTIFS["epargne_securisee"].rendement_moyen
    ) < 1e-9
)
verifier(
    "panier 50/50 de deux classes : rendement = moyenne simple des deux rendements",
    abs(
        rendement_volatilite_panier({"epargne_securisee": 0.5, "marches_financiers": 0.5})["rendement_moyen"]
        - (CLASSES_ACTIFS["epargne_securisee"].rendement_moyen + CLASSES_ACTIFS["marches_financiers"].rendement_moyen) / 2
    ) < 1e-9
)
verifier(
    "panier Dynamique : rendement moyen supérieur au panier Prudent (plus de non coté/actions, moins d'épargne)",
    rendement_volatilite_panier(PANIERS["Dynamique"])["rendement_moyen"]
    > rendement_volatilite_panier(PANIERS["Prudent"])["rendement_moyen"]
)
verifier(
    "panier Dynamique : volatilité supérieure au panier Prudent",
    rendement_volatilite_panier(PANIERS["Dynamique"])["volatilite"]
    > rendement_volatilite_panier(PANIERS["Prudent"])["volatilite"]
)
verifier(
    "normaliser_ponderations : une répartition saisie à 90 (pas 100) est bien remise à somme 1.0",
    abs(sum(normaliser_ponderations({"epargne_securisee": 60, "marches_financiers": 30}).values()) - 1.0) < 1e-9
)
verifier(
    "normaliser_ponderations : poids tous nuls -> erreur plutôt qu'une division silencieuse par zéro",
    _leve_exception(lambda: normaliser_ponderations({"epargne_securisee": 0, "marches_financiers": 0}))
)
verifier(
    "rendement_volatilite_panier avec rendements_override : la classe remplacée utilise la valeur manuelle",
    abs(
        rendement_volatilite_panier({"epargne_securisee": 1.0}, rendements_override={"epargne_securisee": 0.05})["rendement_moyen"]
        - 0.05
    ) < 1e-9
)
verifier(
    "rendement_volatilite_panier avec rendements_override : une classe absente du dict garde son rendement sourcé",
    abs(
        rendement_volatilite_panier({"epargne_securisee": 0.5, "marches_financiers": 0.5}, rendements_override={"epargne_securisee": 0.05})["rendement_moyen"]
        - (0.5 * 0.05 + 0.5 * CLASSES_ACTIFS["marches_financiers"].rendement_moyen)
    ) < 1e-9
)

# --- Analyse de sensibilité (tornade) ---
_sensibilite_sasu = analyse_sensibilite(80_000, False)
_sensibilite_sarl = analyse_sensibilite(80_000, True, capital_social=10_000)

verifier(
    "analyse_sensibilite SASU : 3 paramètres (forme juridique, taux IS, abattement forfaitaire)",
    {r["parametre"].split(" (")[0] for r in _sensibilite_sasu} == {"Forme juridique", "Taux normal d'IS", "Abattement forfaitaire frais professionnels"}
)
verifier(
    "analyse_sensibilite SASU : la sensibilité à l'abattement forfaitaire est non nulle (contrairement au PASS, volontairement écarté - voir le code)",
    abs(
        next(r for r in _sensibilite_sasu if r["parametre"].startswith("Abattement"))["valeur_haut"]
        - next(r for r in _sensibilite_sasu if r["parametre"].startswith("Abattement"))["valeur_bas"]
    ) > 1
)
verifier(
    "analyse_sensibilite SARL : 3 paramètres (forme juridique, taux IS, capital social)",
    {r["parametre"].split(" (")[0] for r in _sensibilite_sarl} == {"Forme juridique", "Taux normal d'IS", "Capital social de la SARL"}
)
verifier(
    "analyse_sensibilite : triée par amplitude d'impact décroissante",
    all(
        abs(_sensibilite_sasu[i]["valeur_haut"] - _sensibilite_sasu[i]["valeur_bas"])
        >= abs(_sensibilite_sasu[i + 1]["valeur_haut"] - _sensibilite_sasu[i + 1]["valeur_bas"])
        for i in range(len(_sensibilite_sasu) - 1)
    )
)
verifier(
    "analyse_sensibilite : la ligne « Forme juridique » recoupe repartition_optimale pour chaque forme",
    abs(
        next(r for r in _sensibilite_sasu if r["parametre"].startswith("Forme juridique"))["valeur_bas"]
        - repartition_optimale(80_000, False)["meilleur_net"]
    ) < 1e-6
)
verifier(
    "net_total_mix SASU à p=100% : pass_value est bien pris en compte (change le résultat)",
    net_total_mix(80_000, 1.0, False, pass_value=PASS_2026 * 2) != net_total_mix(80_000, 1.0, False, pass_value=PASS_2026)
)
verifier(
    "net_total_mix SASU à p=100% : avec pass_value = PASS_2026, résultat identique à l'appel sans surcharge",
    abs(net_total_mix(80_000, 1.0, False) - net_total_mix(80_000, 1.0, False, pass_value=PASS_2026)) < 1e-9
)

print()
if echecs:
    print(f"{len(echecs)} échec(s) : {echecs}")
else:
    print("Tous les tests passent.")
