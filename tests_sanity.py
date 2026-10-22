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
    TAUX_PFU,
)
from simulation import PROFILS, simulation_comparaison, simuler_directe, simuler_holding
from paniers import CLASSES_ACTIFS, PANIERS, normaliser_ponderations, rendement_volatilite_panier
from trajectoire import comparer, sortie_holding, trajectoire_directe, trajectoire_holding
from demembrement import (
    calcul_droits_donation,
    calcul_droits_donation_famille,
    comparer_transmission,
    pourcentage_usufruit,
    valeur_usufruit_nue_propriete,
)
from assurance_vie import (
    ABATTEMENT_757_B_GLOBAL,
    ABATTEMENT_990_I_PAR_BENEFICIAIRE,
    net_apres_rachat,
    prelevement_757_b,
    prelevement_990_i,
    taxation_transmission,
)
from per import (
    comparer_per,
    economie_impot_per,
    fiscalite_sortie_capital,
    montant_deductible,
    plafond_deduction_salarie,
    plafond_deduction_tns,
)
from sci import (
    TAUX_IR_PLUS_VALUE_IMMO,
    comparer_sci,
    plus_value_brute,
    plus_value_nette_sci_ir,
    plus_value_nette_sci_is,
    revenu_net_sci_ir,
    revenu_net_sci_is,
    taux_abattement_ir_duree,
    taux_abattement_ps_duree,
)
from ifi import (
    ABATTEMENT_RESIDENCE_PRINCIPALE,
    SEUIL_ASSUJETTISSEMENT_IFI,
    assiette_ifi,
    calcul_ifi,
    calcul_ifi_brut,
    decote_ifi,
    synthese_ifi,
)
from succession import (
    ABATTEMENT_FRERE_SOEUR,
    ABATTEMENT_NEVEU_NIECE,
    ABATTEMENT_TIERS,
    CONJOINT,
    ENFANT,
    FRERE_SOEUR,
    NEVEU_NIECE,
    TIERS,
    calcul_droits_succession,
    comparer_liens_parente,
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

# --- Trajectoire pluriannuelle : forme juridique SASU/SARL (task #27) ---
verifier(
    "trajectoire_directe SASU : comportement inchangé par défaut (est_sarl=False)",
    abs(trajectoire_directe(80_000, 0.05, 10)[-1] - trajectoire_directe(80_000, 0.05, 10, est_sarl=False)[-1]) < 1e-6
)
verifier(
    "trajectoire_directe SARL (capital social faible) : net strictement inférieur à la SASU, même profit/rendement",
    trajectoire_directe(80_000, 0.05, 10, est_sarl=True, capital_social=10_000)[-1]
    < trajectoire_directe(80_000, 0.05, 10, est_sarl=False)[-1]
)
verifier(
    "sortie_holding SARL : un capital social plus élevé laisse un net au moins aussi élevé (moins de dividende réintégré en TNS)",
    sortie_holding(500_000, est_sarl=True, capital_social=200_000) >= sortie_holding(500_000, est_sarl=True, capital_social=10_000)
)
verifier(
    "comparer SARL (capital social faible) : l'année de croisement n'est jamais plus précoce que pour la SASU (le régime TNS pénalise surtout le direct, pas la holding qui ne distribue qu'à la sortie)",
    (lambda a, b: a is None or (b is not None and a >= b))(
        comparer(80_000, 0.05, 15, est_sarl=True, capital_social=10_000)["annee_croisement"],
        comparer(80_000, 0.05, 15, est_sarl=False)["annee_croisement"],
    )
)

_rendements_constants_test = np.full((2, 8), 0.05)
verifier(
    "simuler_directe (vectorisé) SARL recoupe exactement trajectoire_directe (scalaire), à rendement constant",
    np.allclose(
        simuler_directe(80_000, _rendements_constants_test, est_sarl=True, capital_social=10_000)[0],
        trajectoire_directe(80_000, 0.05, 8, est_sarl=True, capital_social=10_000),
    )
)
verifier(
    "simuler_holding (vectorisé) SARL recoupe exactement trajectoire_holding + sortie_holding (scalaires), à rendement constant",
    np.allclose(
        simuler_holding(80_000, _rendements_constants_test, est_sarl=True, capital_social=10_000)[0],
        [sortie_holding(c, est_sarl=True, capital_social=10_000) for c in trajectoire_holding(80_000, 0.05, 8)],
    )
)
verifier(
    "simulation_comparaison : accepte est_sarl/capital_social sans erreur et modifie bien le résultat",
    simulation_comparaison(80_000, 0.05, 0.08, 10, nb_simulations=200, graine=1, est_sarl=True, capital_social=10_000)["directe"][50][-1]
    != simulation_comparaison(80_000, 0.05, 0.08, 10, nb_simulations=200, graine=1, est_sarl=False)["directe"][50][-1]
)

# --- Assurance-vie : rachat (task #28) ---
verifier(
    "net_apres_rachat, contrat < 8 ans : taux de 12,8% appliqué sans abattement",
    abs(net_apres_rachat(10_000, anciennete_annees=5)["ir"] - 10_000 * 0.128) < 1e-6
)
verifier(
    "net_apres_rachat, contrat >= 8 ans, sous le seuil de 150 000€ : taux réduit de 7,5% après abattement de 4 600€",
    abs(net_apres_rachat(10_000, anciennete_annees=10, versements_cumules=100_000)["ir"] - (10_000 - 4_600) * 0.075) < 1e-6
)
verifier(
    "net_apres_rachat, contrat >= 8 ans, au-delà du seuil de 150 000€ de versements : taux majoré de 12,8%",
    abs(net_apres_rachat(10_000, anciennete_annees=10, versements_cumules=200_000)["ir"] - (10_000 - 4_600) * 0.128) < 1e-6
)
verifier(
    "net_apres_rachat : prélèvements sociaux de 17,2% toujours dus sur la totalité des gains, sans abattement",
    abs(net_apres_rachat(10_000, anciennete_annees=10)["prelevements_sociaux"] - 10_000 * 0.172) < 1e-6
)
verifier(
    "net_apres_rachat : un contrat de plus de 8 ans laisse un net au moins aussi élevé qu'un contrat de moins de 8 ans, à gains identiques",
    net_apres_rachat(10_000, anciennete_annees=10)["net"] >= net_apres_rachat(10_000, anciennete_annees=5)["net"]
)
verifier(
    "net_apres_rachat : l'abattement de 9 200€ (couple) laisse un net au moins aussi élevé que celui de 4 600€ (personne seule), à gains identiques",
    net_apres_rachat(10_000, anciennete_annees=10, abattement_annuel=9_200)["net"]
    >= net_apres_rachat(10_000, anciennete_annees=10, abattement_annuel=4_600)["net"]
)

# --- Assurance-vie : transmission, articles 990 I et 757 B (task #28) ---
verifier(
    "prelevement_990_i : capital sous l'abattement de 152 500€ -> aucun prélèvement",
    prelevement_990_i(100_000) == 0
)
verifier(
    "prelevement_990_i : taux de 20% appliqué juste au-dessus de l'abattement",
    abs(prelevement_990_i(ABATTEMENT_990_I_PAR_BENEFICIAIRE + 10_000) - 10_000 * 0.20) < 1e-6
)
verifier(
    "prelevement_990_i : taux majoré de 31,25% au-delà de 700 000€ de base taxable",
    abs(
        prelevement_990_i(ABATTEMENT_990_I_PAR_BENEFICIAIRE + 700_000 + 10_000)
        - (700_000 * 0.20 + 10_000 * 0.3125)
    ) < 1e-6
)
verifier(
    "prelevement_757_b : primes sous l'abattement global de 30 500€ -> aucun droit de succession",
    prelevement_757_b(20_000)["droits_succession"] == 0
)
verifier(
    "prelevement_757_b : l'abattement global se répartit entre les bénéficiaires (2 bénéficiaires -> moitié moins d'abattement chacun, donc des droits plus élevés sur une même part de primes)",
    prelevement_757_b(150_000, nombre_beneficiaires=2)["droits_succession"]
    > prelevement_757_b(150_000, nombre_beneficiaires=1)["droits_succession"]
)
verifier(
    "taxation_transmission : versements avant 70 ans -> régime 990 I appliqué",
    taxation_transmission(400_000, age_versement=65)["article"] == "990 I"
)
verifier(
    "taxation_transmission : versements après 70 ans -> régime 757 B appliqué",
    taxation_transmission(400_000, age_versement=75, part_primes_versees=350_000)["article"] == "757 B"
)
verifier(
    "taxation_transmission 757 B : les gains (hors primes) sont intégralement exonérés, jamais taxés",
    taxation_transmission(400_000, age_versement=75, part_primes_versees=350_000)["gains_exoneres"] == 50_000
)
verifier(
    "taxation_transmission : à montant identique, le régime 990 I (abattement 152 500€) est toujours au moins aussi favorable que le 757 B (abattement 30 500€) sur la part primes",
    taxation_transmission(400_000, age_versement=65)["net_beneficiaire"]
    >= taxation_transmission(400_000, age_versement=75, part_primes_versees=400_000)["net_beneficiaire"]
)

# --- Succession hors donation (task #29) ---
verifier(
    "calcul_droits_succession : conjoint survivant/partenaire pacsé -> exonération totale, quel que soit le montant",
    calcul_droits_succession(5_000_000, CONJOINT) == 0
)
verifier(
    "calcul_droits_succession : montant sous l'abattement correspondant -> aucun droit, pour chaque lien de parenté",
    calcul_droits_succession(10_000, ENFANT) == 0
    and calcul_droits_succession(10_000, FRERE_SOEUR) == 0
    and calcul_droits_succession(5_000, NEVEU_NIECE) == 0
    and calcul_droits_succession(1_000, TIERS) == 0
)
verifier(
    "calcul_droits_succession : abattement de 15 932€ pour frère/soeur bien appliqué avant le taux de 35%",
    abs(calcul_droits_succession(ABATTEMENT_FRERE_SOEUR + 10_000, FRERE_SOEUR) - 10_000 * 0.35) < 1e-6
)
verifier(
    "calcul_droits_succession : taux majoré de 45% pour frère/soeur au-delà de 24 430€ de base taxable",
    abs(
        calcul_droits_succession(ABATTEMENT_FRERE_SOEUR + 24_430 + 10_000, FRERE_SOEUR)
        - (24_430 * 0.35 + 10_000 * 0.45)
    ) < 1e-6
)
verifier(
    "calcul_droits_succession : taux fixe de 55% pour neveu/nièce après abattement de 7 967€",
    abs(calcul_droits_succession(ABATTEMENT_NEVEU_NIECE + 10_000, NEVEU_NIECE) - 10_000 * 0.55) < 1e-6
)
verifier(
    "calcul_droits_succession : taux fixe de 60% pour un tiers sans lien de parenté après abattement de 1 594€",
    abs(calcul_droits_succession(ABATTEMENT_TIERS + 10_000, TIERS) - 10_000 * 0.60) < 1e-6
)
verifier(
    "calcul_droits_succession : à montant identique, le conjoint est toujours au moins aussi favorisé que l'enfant, lui-même toujours au moins aussi favorisé qu'un tiers sans lien de parenté",
    calcul_droits_succession(500_000, CONJOINT) <= calcul_droits_succession(500_000, ENFANT, nombre_enfants=1)
    <= calcul_droits_succession(500_000, TIERS)
)
verifier(
    "calcul_droits_succession : répartir entre 2 enfants laisse strictement moins de droits totaux qu'un enfant unique, à masse successorale identique (deux abattements de 100 000€ au lieu d'un seul)",
    calcul_droits_succession(500_000, ENFANT, nombre_enfants=2) < calcul_droits_succession(500_000, ENFANT, nombre_enfants=1)
)
verifier(
    "comparer_liens_parente : renvoie bien les 5 liens de parenté, triés dans l'ordre de LIENS_PARENTE",
    [r["lien"] for r in comparer_liens_parente(500_000)] == [CONJOINT, ENFANT, FRERE_SOEUR, NEVEU_NIECE, TIERS]
)
verifier(
    "comparer_liens_parente : le net perçu décroît (au sens large) du conjoint vers le tiers sans lien de parenté",
    [r["net"] for r in comparer_liens_parente(500_000)] == sorted([r["net"] for r in comparer_liens_parente(500_000)], reverse=True)
)

# --- IFI (task #30) ---
verifier(
    "assiette_ifi : abattement de 30% bien appliqué sur la résidence principale seule",
    assiette_ifi(valeur_residence_principale=1_000_000) == 1_000_000 * (1 - ABATTEMENT_RESIDENCE_PRINCIPALE)
)
verifier(
    "assiette_ifi : les dettes déductibles diminuent bien l'assiette, sans jamais la rendre négative",
    assiette_ifi(valeur_autres_biens_immobiliers=100_000, dettes_deductibles=500_000) == 0
)
verifier(
    "calcul_ifi : patrimoine sous le seuil d'assujettissement de 1 300 000€ -> aucun IFI, même si > 800 000€",
    calcul_ifi(1_000_000) == 0 and calcul_ifi(SEUIL_ASSUJETTISSEMENT_IFI - 1) == 0
)
verifier(
    "calcul_ifi_brut : tranche à 0% bien appliquée jusqu'à 800 000€",
    calcul_ifi_brut(800_000) == 0
)
verifier(
    "calcul_ifi_brut : taux de 0,5% appliqué juste au-dessus de 800 000€",
    abs(calcul_ifi_brut(810_000) - 10_000 * 0.005) < 1e-6
)
verifier(
    "decote_ifi : nulle en-dessous de 1 300 000€ et au-dessus de 1 400 000€, non nulle entre les deux",
    decote_ifi(1_200_000) == 0 and decote_ifi(1_450_000) == 0 and decote_ifi(1_350_000) > 0
)
verifier(
    "synthese_ifi : au seuil de 1 300 001€, IFI brut de 2 500€ et décote de 1 250€ (valeurs de référence)",
    abs(synthese_ifi(0, 1_300_001, 0)["ifi_brut"] - 2_500) < 1
    and abs(synthese_ifi(0, 1_300_001, 0)["decote"] - 1_250) < 1
)
verifier(
    "synthese_ifi : l'IFI net croît (au sens large) avec le patrimoine net taxable",
    synthese_ifi(0, 2_000_000)["ifi_net"] < synthese_ifi(0, 3_000_000)["ifi_net"] < synthese_ifi(0, 6_000_000)["ifi_net"]
)
verifier(
    "synthese_ifi : à patrimoine identique, détenir sa résidence principale (abattement 30%) laisse un IFI net au plus égal à celui d'un même montant détenu en résidence secondaire (sans abattement)",
    synthese_ifi(valeur_residence_principale=2_000_000)["ifi_net"] <= synthese_ifi(valeur_autres_biens_immobiliers=2_000_000)["ifi_net"]
)

# --- SCI à l'IS vs à l'IR (task #31) ---
verifier(
    "taux_abattement_ir_duree : aucun abattement avant 6 ans, exonération totale à partir de 22 ans",
    taux_abattement_ir_duree(5) == 0.0 and taux_abattement_ir_duree(22) == 1.0 and taux_abattement_ir_duree(30) == 1.0
)
verifier(
    "taux_abattement_ps_duree : rythme plus lent que l'IR, exonération totale seulement à partir de 30 ans",
    taux_abattement_ps_duree(22) == 0.28 and taux_abattement_ps_duree(21) < taux_abattement_ir_duree(21)
    and taux_abattement_ps_duree(29) < 1.0 and taux_abattement_ps_duree(30) == 1.0
)
verifier(
    "plus_value_brute : les frais d'acquisition et les travaux réduisent bien la plus-value imposable",
    plus_value_brute(600_000, 400_000, frais_acquisition=20_000, travaux=30_000) == 150_000
)
verifier(
    "plus_value_nette_sci_ir : exonération totale (IR et prélèvements sociaux) après 30 ans de détention",
    plus_value_nette_sci_ir(600_000, 400_000, annees_detention=30)["net"] == 200_000
)
verifier(
    "plus_value_nette_sci_ir : net croissant avec la durée de détention, à plus-value brute identique",
    plus_value_nette_sci_ir(600_000, 400_000, annees_detention=10)["net"]
    < plus_value_nette_sci_ir(600_000, 400_000, annees_detention=25)["net"]
    < plus_value_nette_sci_ir(600_000, 400_000, annees_detention=30)["net"]
)
verifier(
    "revenu_net_sci_ir : prélèvements sociaux de 17,2% et IR au TMI bien appliqués sur le revenu foncier net",
    abs(revenu_net_sci_ir(30_000, 10_000, tmi=0.30)["net"] - 20_000 * (1 - 0.30 - 0.172)) < 1e-6
)
verifier(
    "revenu_net_sci_is : non distribué -> rien ne sort pour l'associé cette année-là (capitalisation, comme une holding)",
    revenu_net_sci_is(30_000, 10_000, amortissement_annuel=5_000, distribue=False)["net"] == 0.0
)
verifier(
    "revenu_net_sci_is : distribué -> double imposition (IS puis PFU), donc net strictement positif mais inférieur au résultat après IS seul",
    0 < revenu_net_sci_is(30_000, 10_000, amortissement_annuel=5_000, distribue=True)["net"]
    < revenu_net_sci_is(30_000, 10_000, amortissement_annuel=5_000, distribue=True)["resultat_apres_is"]
)
verifier(
    "plus_value_nette_sci_is : à prix de cession identique, un bien plus amorti (valeur nette comptable plus faible) génère une plus-value brute - donc un IS - plus élevé",
    plus_value_nette_sci_is(600_000, 400_000, amortissements_cumules=300_000)["is_du"]
    > plus_value_nette_sci_is(600_000, 400_000, amortissements_cumules=50_000)["is_du"]
)
verifier(
    "comparer_sci : renvoie bien un total IR et un total IS cohérents (somme des revenus cumulés et de la plus-value nette)",
    abs(
        comparer_sci(36_000, 8_000, 10_000, 0.30, 400_000, 600_000, 15)["total_ir"]
        - (comparer_sci(36_000, 8_000, 10_000, 0.30, 400_000, 600_000, 15)["cumul_revenus_ir"]
           + comparer_sci(36_000, 8_000, 10_000, 0.30, 400_000, 600_000, 15)["plus_value_nette_ir"])
    ) < 1e-6
)

# --- PER : plafond de déduction, économie d'impôt, fiscalité de sortie (task #32) ---
verifier(
    "plafond_deduction_salarie : plancher garanti de 10% d'un PASS même avec un faible revenu",
    plafond_deduction_salarie(10_000) == 0.10 * PASS_2026
)
verifier(
    "plafond_deduction_salarie : plafonné à 10% de 8 PASS au-delà de 8 PASS de revenu",
    plafond_deduction_salarie(400_000) == 0.10 * 8 * PASS_2026
)
verifier(
    "plafond_deduction_tns : exemple de référence (bénéfice 120 000 €) conforme à la source (10% + 15% au-delà d'1 PASS)",
    abs(plafond_deduction_tns(120_000) - 22_791) < 1
)
verifier(
    "plafond_deduction_tns : plafonné à 88 911 € au-delà de 8 PASS de bénéfice (10% de 8 PASS + 15% de 7 PASS)",
    abs(plafond_deduction_tns(400_000) - 88_911) < 1
)
verifier(
    "plafond_deduction_tns : structurellement plus généreux que le plafond salarié pour un même revenu élevé",
    plafond_deduction_tns(120_000) > plafond_deduction_salarie(120_000)
)
verifier(
    "montant_deductible : jamais plus que le plafond disponible, jamais négatif",
    montant_deductible(50_000, 10_000) == 10_000 and montant_deductible(-5_000, 10_000) == 0.0
)
verifier(
    "economie_impot_per : économie d'impôt proportionnelle à la TMI",
    economie_impot_per(10_000, 0.30) == 3_000
)
verifier(
    "fiscalite_sortie_capital : versements non déduits à l'entrée -> totalement exonérés à la sortie, seuls les gains sont taxés (au PFU)",
    fiscalite_sortie_capital(10_000, 2_000, deduit=False, tmi_sortie=0.30)["impot_versements"] == 0.0
)
verifier(
    "fiscalite_sortie_capital : versements déduits à l'entrée -> taxés au barème IR (TMI de sortie) à la sortie, sans prélèvements sociaux",
    fiscalite_sortie_capital(10_000, 2_000, deduit=True, tmi_sortie=0.30)["impot_versements"] == 3_000
)
verifier(
    "fiscalite_sortie_capital : les gains sont toujours taxés au PFU de 31,4%, déduit ou non",
    abs(fiscalite_sortie_capital(10_000, 2_000, deduit=True, tmi_sortie=0.30)["impot_gains"] - 2_000 * TAUX_PFU) < 1e-6
    and abs(fiscalite_sortie_capital(10_000, 2_000, deduit=False)["impot_gains"] - 2_000 * TAUX_PFU) < 1e-6
)
verifier(
    "comparer_per : à TMI identique à l'entrée et à la sortie, le PER laisse toujours plus que l'absence de PER (le capital taxé à l'entrée ne fructifie jamais dans l'autre scénario)",
    comparer_per(10_000, tmi_entree=0.30, tmi_sortie=0.30, rendement_annuel=0.04, duree_annees=20, deduit=True)["ecart"] > 0
)
verifier(
    "comparer_per : l'écart en faveur du PER est encore plus favorable quand la TMI de sortie est inférieure à celle de l'entrée (cas classique du départ à la retraite)",
    comparer_per(10_000, tmi_entree=0.41, tmi_sortie=0.11, rendement_annuel=0.04, duree_annees=20, deduit=True)["ecart"]
    > comparer_per(10_000, tmi_entree=0.41, tmi_sortie=0.41, rendement_annuel=0.04, duree_annees=20, deduit=True)["ecart"]
)

print()
if echecs:
    print(f"{len(echecs)} échec(s) : {echecs}")
else:
    print("Tous les tests passent.")
