"""
Module simulation - Introduit le risque dans la comparaison direct vs
holding, via une simulation Monte-Carlo plutôt qu'un rendement fixe.
Grand Large Patrimoine - projet de stage

POURQUOI UNE SIMULATION ET PAS UN CHIFFRE UNIQUE :
Afficher "5% de rendement" comme une certitude ressemble à une prévision
de marché, ce qui s'approche d'un conseil en investissement personnalisé
(interdit pour cet outil). On simule à la place plusieurs centaines de
trajectoires de rendement tirées au hasard autour d'une moyenne et d'une
volatilité choisies par l'utilisateur, puis on affiche une fourchette de
résultats (ex. "dans 90% des cas, entre X et Y €"). Ça montre le risque au
lieu de le cacher, et ça reste une hypothèse explicite, jamais une
prévision.

Important : les MÊMES tirages aléatoires de rendement sont appliqués aux
deux scénarios (direct et holding) chaque année, dans chaque simulation.
On compare donc les deux structures dans les MÊMES conditions de marché,
pas deux hasards indépendants — sinon la comparaison ne voudrait rien dire.

PROFILS ILLUSTRATIFS (hypothèses pédagogiques, pas des recommandations,
non rattachées à un produit ou une classe d'actifs précise) :
- prudent    : rendement moyen 2%, volatilité 3%
- équilibré  : rendement moyen 5%, volatilité 8%
- dynamique  : rendement moyen 8%, volatilité 15%
"""

import numpy as np

from fiscalite import calcul_is, TAUX_PFU

PROFILS = {
    "prudent": {"rendement_moyen": 0.02, "volatilite": 0.03},
    "equilibre": {"rendement_moyen": 0.05, "volatilite": 0.08},
    "dynamique": {"rendement_moyen": 0.08, "volatilite": 0.15},
}


def tirer_rendements(rendement_moyen, volatilite, horizon_annees, nb_simulations, graine=None):
    """
    Tire nb_simulations trajectoires de rendements annuels, chacune sur
    horizon_annees, suivant une loi normale (rendement_moyen, volatilite).
    Renvoie un tableau de forme (nb_simulations, horizon_annees).
    """
    rng = np.random.default_rng(graine)
    return rng.normal(rendement_moyen, volatilite, size=(nb_simulations, horizon_annees))


def simuler_directe(profit_annuel, rendements, is_fn=calcul_is, taux_pfu=TAUX_PFU):
    """
    Version vectorisée de trajectoire_directe : applique la même logique
    mais sur toutes les simulations à la fois (une ligne par simulation).
    rendements : tableau (nb_simulations, horizon_annees).
    """
    nb_simulations, horizon = rendements.shape
    capital = np.zeros(nb_simulations)
    historique = np.zeros((nb_simulations, horizon))
    is_du = is_fn(profit_annuel)
    net_distribue = (profit_annuel - is_du) * (1 - taux_pfu)
    for annee in range(horizon):
        gain = capital * rendements[:, annee]
        capital = capital + gain * (1 - taux_pfu) + net_distribue
        historique[:, annee] = capital
    return historique


def simuler_holding(profit_annuel, rendements, is_fn=calcul_is, taux_pfu=TAUX_PFU):
    """
    Version vectorisée de trajectoire_holding + sortie_holding : la holding
    capitalise brut chaque année, la sortie en net est calculée après coup.
    """
    nb_simulations, horizon = rendements.shape
    capital = np.zeros(nb_simulations)
    historique_brut = np.zeros((nb_simulations, horizon))
    is_du = is_fn(profit_annuel)
    apport_net_is = profit_annuel - is_du
    for annee in range(horizon):
        capital = capital * (1 + rendements[:, annee]) + apport_net_is
        historique_brut[:, annee] = capital
    return historique_brut * (1 - taux_pfu)


def simulation_comparaison(profit_annuel, rendement_moyen, volatilite, horizon_annees,
                            nb_simulations=1000, graine=None):
    """
    Lance la simulation Monte-Carlo et renvoie, pour chaque année, les
    percentiles 10/50/90 des deux trajectoires (direct et holding net).
    """
    rendements = tirer_rendements(rendement_moyen, volatilite, horizon_annees, nb_simulations, graine)

    directe = simuler_directe(profit_annuel, rendements)
    holding = simuler_holding(profit_annuel, rendements)

    percentiles = [10, 50, 90]
    resultat = {"directe": {}, "holding": {}}
    for p in percentiles:
        resultat["directe"][p] = np.percentile(directe, p, axis=0)
        resultat["holding"][p] = np.percentile(holding, p, axis=0)
    return resultat


if __name__ == "__main__":
    # Test avec le profil "équilibré", seed fixée pour reproductibilité
    resultat = simulation_comparaison(
        profit_annuel=50000,
        rendement_moyen=PROFILS["equilibre"]["rendement_moyen"],
        volatilite=PROFILS["equilibre"]["volatilite"],
        horizon_annees=10,
        nb_simulations=2000,
        graine=42,
    )

    print("Profil équilibré (moyenne 5%, volatilité 8%) - 2000 simulations\n")
    print(f"{'Année':>5} | {'Direct médiane':>16} | {'Direct P10-P90':>22} | {'Holding médiane':>17} | {'Holding P10-P90':>22}")
    for i in range(10):
        d10, d50, d90 = resultat["directe"][10][i], resultat["directe"][50][i], resultat["directe"][90][i]
        h10, h50, h90 = resultat["holding"][10][i], resultat["holding"][50][i], resultat["holding"][90][i]
        print(f"{i + 1:>5} | {d50:>13,.0f} €  | {d10:>9,.0f} - {d90:>9,.0f} | {h50:>14,.0f} €  | {h10:>9,.0f} - {h90:>9,.0f}")
