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

from fiscalite import net_apres_salaire, net_apres_dividende
from fiscalite_tns import net_apres_remuneration_tns, net_apres_dividende_tns, cotisations_tns


def net_total_mix(montant, p, est_sarl, capital_social=10_000, compte_courant_moyen=0.0):
    """Net en poche total si une fraction p (0 à 1) du montant disponible est
    versée en salaire/rémunération, le reste en dividende.

    Cas SARL à p=0 (rémunération nulle) : le gérant majoritaire reste
    affilié au régime TNS et doit la cotisation minimale forfaitaire même
    à rémunération nulle - net_apres_remuneration_tns(0) la facture déjà
    correctement (valeur négative), donc l'addition directe suffit ici ;
    c'est le même principe que net_apres_dividende_tns_pur."""
    cout_salaire = p * montant
    cout_dividende = montant - cout_salaire
    if est_sarl:
        net_sal = net_apres_remuneration_tns(cout_salaire)
        net_div = net_apres_dividende_tns(cout_dividende, capital_social, compte_courant_moyen)["net_total"]
    else:
        net_sal = net_apres_salaire(cout_salaire)
        net_div = net_apres_dividende(cout_dividende)
    return net_sal + net_div


def repartition_optimale(montant, est_sarl, capital_social=10_000, compte_courant_moyen=0.0, pas_pourcent=1):
    """Balaie toutes les répartitions de 0% à 100% (par pas de `pas_pourcent`
    points), et retourne la courbe complète plus le point optimal."""
    points = [
        (p_pct, net_total_mix(montant, p_pct / 100, est_sarl, capital_social, compte_courant_moyen))
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
