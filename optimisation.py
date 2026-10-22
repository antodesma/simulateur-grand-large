"""
Optimiseur de la répartition rémunération / dividende.

Le dirigeant n'est pas obligé de choisir entre 100% salaire (ou rémunération
TNS) et 100% dividende : on peut répartir le montant disponible entre les
deux. À cause des effets de seuil (plafond de la sécurité sociale, tranches
de l'IR, seuil des 10% de dividende non cotisé en SARL, plancher/plafond de
l'abattement forfaitaire), le total net en poche n'est pas une fonction
monotone de cette répartition : il existe parfois un optimum intermédiaire,
meilleur que les deux options pures.

Pas de méthode d'optimisation analytique ici (les seuils cassent la
dérivabilité) : un balayage exhaustif, pas à pas, suffit largement pour une
fonction à une seule variable sur un intervalle borné, et reste exact.
"""

from fiscalite import PASS_2026, TAUX_IS_NORMAL, net_apres_salaire, net_apres_dividende
from fiscalite_tns import net_apres_remuneration_tns, net_apres_dividende_tns, cotisations_tns


def net_total_mix(montant, p, est_sarl, capital_social=10_000, compte_courant_moyen=0.0,
                   pass_value=PASS_2026, taux_is_normal=TAUX_IS_NORMAL, abattement_taux=0.10):
    """Net en poche total si une fraction p (0 à 1) du montant disponible est
    versée en salaire/rémunération, le reste en dividende.

    Cas SARL à p=0 (rémunération nulle) : le gérant majoritaire reste
    affilié au régime TNS et doit la cotisation minimale forfaitaire même
    à rémunération nulle - net_apres_remuneration_tns(0) la facture déjà
    correctement (valeur négative), donc l'addition directe suffit ici ;
    c'est le même principe que net_apres_dividende_tns_pur.

    pass_value, taux_is_normal, abattement_taux : surcharges utilisées
    uniquement par l'analyse de sensibilité (graphique tornade, voir
    analyse_sensibilite) - les valeurs par défaut sont celles réellement
    en vigueur, utilisées partout ailleurs dans l'outil. pass_value et
    abattement_taux n'affectent que le scénario SASU (le régime TNS
    n'utilise pas directement le PASS dans ce modèle, cf. fiscalite_tns.py,
    et sa propre variante de l'abattement n'est pas testée ici)."""
    cout_salaire = p * montant
    cout_dividende = montant - cout_salaire
    if est_sarl:
        net_sal = net_apres_remuneration_tns(cout_salaire)
        net_div = net_apres_dividende_tns(cout_dividende, capital_social, compte_courant_moyen, taux_is_normal=taux_is_normal)["net_total"]
    else:
        net_sal = net_apres_salaire(cout_salaire, pass_value=pass_value, abattement_taux=abattement_taux)
        net_div = net_apres_dividende(cout_dividende, taux_is_normal=taux_is_normal)
    return net_sal + net_div


def repartition_optimale(montant, est_sarl, capital_social=10_000, compte_courant_moyen=0.0, pas_pourcent=1,
                          pass_value=PASS_2026, taux_is_normal=TAUX_IS_NORMAL, abattement_taux=0.10):
    """Balaie toutes les répartitions de 0% à 100% (par pas de `pas_pourcent`
    points), et retourne la courbe complète plus le point optimal."""
    points = [
        (p_pct, net_total_mix(montant, p_pct / 100, est_sarl, capital_social, compte_courant_moyen, pass_value, taux_is_normal, abattement_taux))
        for p_pct in range(0, 101, pas_pourcent)
    ]
    meilleur_p_pct, meilleur_net = max(points, key=lambda t: t[1])
    net_100_salaire = points[-1][1]
    net_100_dividende = points[0][1]
    meilleur_extreme = max(net_100_salaire, net_100_dividende)

    return {
        "points": points,
        "meilleur_p_pct": meilleur_p_pct,
        "meilleur_net": meilleur_net,
        "net_100_salaire": net_100_salaire,
        "net_100_dividende": net_100_dividende,
        "gain_vs_extremes": meilleur_net - meilleur_extreme,
    }


def analyse_sensibilite(montant, est_sarl, capital_social=10_000, compte_courant_moyen=0.0):
    """
    Analyse de sensibilité (graphique tornade) : de combien bouge le net en
    poche optimal (meilleur_net de repartition_optimale) si on fait varier,
    un paramètre à la fois, toutes choses égales par ailleurs ?

    Chaque variation est un TEST DE SENSIBILITÉ, pas une prévision - certains
    paramètres (taux d'IS, PASS) ne changent pas du jour au lendemain dans la
    réalité. L'objectif est de montrer la robustesse du résultat face à ces
    paramètres, pas d'anticiper un changement réglementaire précis.

    Renvoie une liste de dicts {"parametre", "type", "param_bas", "valeur_bas",
    "libelle_bas" (si type == "categoriel"), "param_haut", "valeur_haut",
    "libelle_haut" (si type == "categoriel")}, triée par amplitude d'impact
    décroissante (le paramètre qui fait le plus bouger le résultat en premier).
    """
    resultats = []

    # 1. Forme juridique : SASU vs SARL, à répartition optimale pour chacune,
    # même montant (et même capital social si on bascule en SARL).
    net_sasu = repartition_optimale(montant, False)["meilleur_net"]
    net_sarl = repartition_optimale(montant, True, capital_social, compte_courant_moyen)["meilleur_net"]
    resultats.append({
        "parametre": "Forme juridique (SASU / SARL)",
        "type": "categoriel",
        "libelle_bas": "SASU", "valeur_bas": net_sasu,
        "libelle_haut": "SARL", "valeur_haut": net_sarl,
    })

    # 2. Taux normal d'IS (25% actuellement, part du profit > 42 500€) :
    # test hypothétique à ±5 points.
    taux_is_bas = TAUX_IS_NORMAL - 0.05
    taux_is_haut = TAUX_IS_NORMAL + 0.05
    net_is_bas = repartition_optimale(montant, est_sarl, capital_social, compte_courant_moyen, taux_is_normal=taux_is_bas)["meilleur_net"]
    net_is_haut = repartition_optimale(montant, est_sarl, capital_social, compte_courant_moyen, taux_is_normal=taux_is_haut)["meilleur_net"]
    resultats.append({
        "parametre": "Taux normal d'IS (test ± 5 points)",
        "type": "pourcentage",
        "param_bas": taux_is_bas, "valeur_bas": net_is_bas,
        "param_haut": taux_is_haut, "valeur_haut": net_is_haut,
    })

    if est_sarl:
        # 3. Capital social de la SARL : un vrai paramètre modifiable par le
        # client (pas une hypothèse réglementaire) - il fait directement
        # varier le seuil de dividende non réintégré dans l'assiette TNS.
        capital_bas = capital_social * 0.5
        capital_haut = capital_social * 2
        net_cap_bas = repartition_optimale(montant, True, capital_bas, compte_courant_moyen)["meilleur_net"]
        net_cap_haut = repartition_optimale(montant, True, capital_haut, compte_courant_moyen)["meilleur_net"]
        resultats.append({
            "parametre": "Capital social de la SARL (× 0,5 / × 2)",
            "type": "montant",
            "param_bas": capital_bas, "valeur_bas": net_cap_bas,
            "param_haut": capital_haut, "valeur_haut": net_cap_haut,
        })
    else:
        # 3. Abattement forfaitaire pour frais professionnels (10%
        # actuellement, sur le salaire) : test hypothétique à 5% / 15%.
        # Note méthodologique : le PASS (plafond de la sécurité sociale)
        # n'est volontairement PAS testé ici - dans ce modèle, la
        # répartition optimale maintient systématiquement la part salariale
        # bien en dessous du PASS (les effets de seuil de l'IR rendent un
        # gros salaire rarement optimal), donc le faire varier n'aurait
        # aucun effet observable sur ce résultat précis, quel que soit le
        # montant testé dans la plage de l'outil.
        abattement_bas, abattement_haut = 0.05, 0.15
        net_abat_bas = repartition_optimale(montant, False, abattement_taux=abattement_bas)["meilleur_net"]
        net_abat_haut = repartition_optimale(montant, False, abattement_taux=abattement_haut)["meilleur_net"]
        resultats.append({
            "parametre": "Abattement forfaitaire frais professionnels (test 5% / 15%)",
            "type": "pourcentage",
            "param_bas": abattement_bas, "valeur_bas": net_abat_bas,
            "param_haut": abattement_haut, "valeur_haut": net_abat_haut,
        })

    resultats.sort(key=lambda r: abs(r["valeur_haut"] - r["valeur_bas"]), reverse=True)
    return resultats
