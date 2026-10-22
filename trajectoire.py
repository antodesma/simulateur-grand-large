"""
Module trajectoire - Comparaison pluriannuelle : extraction directe vs
holding qui réinvestit.
Grand Large Patrimoine - projet de stage

HYPOTHESES EXPLICITES (affichées dans l'outil, jamais cachées) :
- Le profit annuel avant impôt (P) est constant sur l'horizon, pour isoler
  l'effet de la structure plutôt que celui de la variabilité des revenus.
- Scénario direct : chaque année, P est distribué en dividende (IS puis
  PFU), le net rejoint un capital personnel réinvesti ; les gains de ce
  placement personnel sont eux aussi taxés chaque année au PFU (hypothèse :
  produits de placement courants, hors niches type PEA/assurance-vie).
- Scénario holding : P reste dans la société, ne paie que l'IS, et se
  réinvestit sans frottement fiscal annuel supplémentaire (hypothèse de
  capitalisation interne, cohérente avec un contrat de capitalisation ou des
  titres non cédés). Tout ne sort qu'à la fin de l'horizon, sous forme de
  dividende (IS déjà payé au fil de l'eau + PFU à la sortie).
- Ces hypothèses isolent un effet structurel ; elles ne remplacent pas une
  étude par un professionnel et doivent rester visibles dans le rendu final.
"""

from fiscalite import calcul_is, TAUX_PFU
from fiscalite_tns import cotisations_tns, net_apres_dividende_tns


def _net_distribue_annuel(profit_annuel, est_sarl, capital_social=10_000, compte_courant_moyen=0.0):
    """
    Net personnel d'une distribution annuelle de profit_annuel, qu'il
    s'agisse d'un dividende "normal" (SASU) ou du dividende d'un gérant
    majoritaire de SARL (TNS, avec réintégration au-delà de 10% du capital
    social dans l'assiette des cotisations - voir fiscalite_tns.py).

    Pour la SARL, la cotisation TNS minimale forfaitaire (due pour
    maintenir l'affiliation du gérant, même à rémunération nulle) est
    retranchée CHAQUE année : tant que le gérant reste affilié sans se
    verser de rémunération, c'est un coût réellement récurrent, pas
    ponctuel - même logique que dans l'onglet "Rémunération annuelle"
    (voir net_dividende dans app.py, tab1).
    """
    if est_sarl:
        return (
            net_apres_dividende_tns(profit_annuel, capital_social, compte_courant_moyen)["net_total"]
            - cotisations_tns(0)
        )
    is_du = calcul_is(profit_annuel)
    return (profit_annuel - is_du) * (1 - TAUX_PFU)


def trajectoire_directe(profit_annuel, rendement, horizon_annees, est_sarl=False, capital_social=10_000, compte_courant_moyen=0.0):
    """
    Chaque année : le capital déjà en place produit un rendement taxé au
    PFU (gain de placement personnel, imposé pareil quelle que soit la
    forme juridique de la société), puis le profit de l'année est
    distribué et rejoint ce capital - au régime dividende classique
    (SASU) ou au régime TNS du gérant majoritaire (SARL, voir
    _net_distribue_annuel). Renvoie le capital net en fin de chaque année.
    """
    capital = 0.0
    historique = []
    net_distribue = _net_distribue_annuel(profit_annuel, est_sarl, capital_social, compte_courant_moyen)
    for _ in range(horizon_annees):
        gain = capital * rendement
        capital += gain * (1 - TAUX_PFU)
        capital += net_distribue
        historique.append(capital)
    return historique


def trajectoire_holding(profit_annuel, rendement, horizon_annees):
    """
    Chaque année : le capital de la holding se réinvestit brut (hypothèse
    de capitalisation interne), puis le profit de l'année, après IS,
    rejoint ce capital. Renvoie le capital BRUT détenu par la holding en
    fin de chaque année (avant sortie personnelle).

    Identique quelle que soit la forme juridique du dirigeant : tant que
    rien ne sort de la société, il n'y a ni dividende ni rémunération
    personnelle, donc pas de régime social à distinguer - seule la SORTIE
    (sortie_holding) diffère entre SASU et SARL.
    """
    capital = 0.0
    historique = []
    for _ in range(horizon_annees):
        capital *= (1 + rendement)
        is_du = calcul_is(profit_annuel)
        capital += profit_annuel - is_du
        historique.append(capital)
    return historique


def sortie_holding(capital_brut, est_sarl=False, capital_social=10_000, compte_courant_moyen=0.0):
    """
    Sortie finale de la holding : l'IS a déjà été payé au fil des ans sur
    les profits, il ne reste qu'à sortir le capital accumulé en dividende
    personnel - PFU seul (SASU), ou régime TNS du gérant majoritaire
    (SARL) si ce capital dépasse 10% du capital social + compte courant,
    EXACTEMENT comme une distribution annuelle classique (voir
    _net_distribue_annuel) : fiscalement, peu importe que la somme
    distribuée vienne d'un profit de l'année ou de plusieurs années de
    capitalisation interne, seul le montant distribué compte pour ce calcul.
    """
    if est_sarl:
        return (
            net_apres_dividende_tns(capital_brut, capital_social, compte_courant_moyen)["net_total"]
            - cotisations_tns(0)
        )
    return capital_brut * (1 - TAUX_PFU)


def comparer(profit_annuel, rendement, horizon_annees, est_sarl=False, capital_social=10_000, compte_courant_moyen=0.0):
    """
    Renvoie les deux trajectoires en net réel (ce que la personne aurait en
    poche si elle sortait tout à l'année en question), plus l'année où la
    holding dépasse le direct.
    """
    traj_directe = trajectoire_directe(profit_annuel, rendement, horizon_annees, est_sarl, capital_social, compte_courant_moyen)
    traj_holding_brut = trajectoire_holding(profit_annuel, rendement, horizon_annees)
    traj_holding_net = [sortie_holding(c, est_sarl, capital_social, compte_courant_moyen) for c in traj_holding_brut]

    annee_croisement = None
    for i in range(len(traj_directe)):
        if traj_holding_net[i] > traj_directe[i]:
            annee_croisement = i + 1
            break

    return {
        "directe": traj_directe,
        "holding_net": traj_holding_net,
        "annee_croisement": annee_croisement,
    }


if __name__ == "__main__":
    resultat = comparer(profit_annuel=50000, rendement=0.05, horizon_annees=10)
    print("Année | Direct (net si sortie)  | Holding (net si sortie)")
    for i in range(10):
        d = resultat["directe"][i]
        h = resultat["holding_net"][i]
        print(f"{i + 1:>5} | {d:>20,.0f} € | {h:>20,.0f} €")
    print(f"\nAnnée où la holding dépasse le direct : {resultat['annee_croisement']}")
