"""
Module de calculs fiscaux - Simulateur rémunération dirigeant / holding
Grand Large Patrimoine - projet de stage

IMPORTANT : outil informatif uniquement, ne constitue pas un conseil
fiscal personnalisé. Barèmes vérifiés en octobre 2026 (revenus 2025 /
exercice 2026). Sources citées ligne par ligne ci-dessous.
"""

# --- Barèmes officiels (sources citées dans la conversation) ---

BAREME_IR = [
    (11600, 0.00),
    (29579, 0.11),
    (84577, 0.30),
    (181917, 0.41),
    (float("inf"), 0.45),
]

SEUIL_IS_REDUIT = 42500
TAUX_IS_REDUIT = 0.15
TAUX_IS_NORMAL = 0.25

TAUX_PFU = 0.314  # 12.8% IR + 18.6% prélèvements sociaux

# Abattement forfaitaire de 10% pour frais professionnels, applicable aux
# traitements et salaires avant le calcul de l'IR (pas aux dividendes).
# Source : legifiscal.fr, revenus 2025 / déclaration 2026.
ABATTEMENT_10_MIN = 509
ABATTEMENT_10_MAX = 14555

# --- Cotisations sociales : président de SASU, statut "assimilé salarié" ---
# Source : legisocial.fr (taux URSSAF 2026) + wisestart.fr (détail spécifique
# président SASU). Point clé vérifié : un président de SASU ne cotise PAS à
# l'assurance chômage (il n'y a pas droit), contrairement à un salarié classique.
#
# Les cotisations retraite complémentaire (Agirc-Arrco/CEG) changent de taux
# au-dessus d'un seuil : le PASS (plafond annuel de sécurité sociale).
PASS_2026 = 48060  # € par an (= 4 005 €/mois, le "PMSS")

# Taux appliqués sur la totalité du brut (pas de distinction de tranche)
TAUX_EMPLOYEUR_FLAT = (
    0.1300  # maladie
    + 0.0525  # allocations familiales
    + 0.0211  # vieillesse déplafonnée
    + 0.0085  # accident du travail (variable selon activité, ~0,85% retenu)
    + 0.0010  # FNAL
    + 0.0030  # contribution solidarité autonomie (CSA)
    + 0.0055  # formation professionnelle
    + 0.0068  # taxe d'apprentissage
)
TAUX_SALARIE_FLAT = (
    0.0953  # CSG/CRDS (9,70% appliqué sur 98,25% du brut)
    + 0.0040  # vieillesse déplafonnée
)

# Taux appliqués seulement sur la part du brut en dessous du PASS (tranche 1)
TAUX_EMPLOYEUR_T1 = (
    0.0855  # vieillesse plafonnée
    + 0.0472  # Agirc-Arrco tranche 1
    + 0.0129  # CEG tranche 1
    + 0.0150  # prévoyance cadre (si applicable)
    + 0.0004  # APEC
)
TAUX_SALARIE_T1 = (
    0.0690  # vieillesse plafonnée
    + 0.0315  # Agirc-Arrco tranche 1
    + 0.0086  # CEG tranche 1
    + 0.0002  # APEC
)

# Taux appliqués seulement sur la part du brut au-dessus du PASS (tranche 2)
TAUX_EMPLOYEUR_T2 = (
    0.1295  # Agirc-Arrco tranche 2
    + 0.0162  # CEG tranche 2
    + 0.0021  # CET
)
TAUX_SALARIE_T2 = (
    0.0864  # Agirc-Arrco tranche 2
    + 0.0108  # CEG tranche 2
    + 0.0014  # CET
)


def charges_sur_brut(brut, pass_value=PASS_2026):
    """
    Calcule les charges patronales et salariales pour un brut annuel donné,
    en tenant compte du seuil PASS (tranche 1 / tranche 2).
    pass_value : surcharge du PASS, uniquement pour tester la sensibilité du
    résultat à ce seuil (graphique tornado) - la valeur réelle PASS_2026
    reste le défaut partout ailleurs dans l'outil.
    Renvoie (charges_employeur, charges_salarie).
    """
    tranche1 = min(brut, pass_value)
    tranche2 = max(0, brut - pass_value)

    charges_employeur = (
        brut * TAUX_EMPLOYEUR_FLAT
        + tranche1 * TAUX_EMPLOYEUR_T1
        + tranche2 * TAUX_EMPLOYEUR_T2
    )
    charges_salarie = (
        brut * TAUX_SALARIE_FLAT
        + tranche1 * TAUX_SALARIE_T1
        + tranche2 * TAUX_SALARIE_T2
    )
    return charges_employeur, charges_salarie


def brut_depuis_cout_total(cout_total, precision=0.01, pass_value=PASS_2026):
    """
    Problème : on connaît le COÛT TOTAL que l'entreprise est prête à payer
    (brut + charges patronales), on veut retrouver le BRUT correspondant.
    Impossible à inverser directement à cause du seuil PASS (la formule
    change de forme selon qu'on est au-dessus ou en dessous).

    Solution : la dichotomie (recherche par encadrement). On teste un brut,
    on regarde si le coût total qu'il génère est trop petit ou trop grand,
    et on resserre l'intervalle jusqu'à tomber dans la précision voulue.
    C'est une technique générale (root-finding) : utile dès qu'une formule
    n'a pas d'inverse simple à écrire.

    pass_value : surcharge du PASS, uniquement pour tester la sensibilité
    du résultat à ce seuil (graphique tornade) - PASS_2026 reste le défaut
    partout ailleurs dans l'outil.
    """
    borne_basse, borne_haute = 0, cout_total  # le brut est forcément entre 0 et le coût total
    while borne_haute - borne_basse > precision:
        brut_test = (borne_basse + borne_haute) / 2
        charges_employeur, _ = charges_sur_brut(brut_test, pass_value)
        cout_genere = brut_test + charges_employeur
        if cout_genere > cout_total:
            borne_haute = brut_test
        else:
            borne_basse = brut_test
    return (borne_basse + borne_haute) / 2


def calcul_is(profit, taux_normal=TAUX_IS_NORMAL):
    """
    Impôt sur les sociétés : 15% jusqu'à 42 500€, taux normal au-delà
    (25% actuellement). On ne paie le taux normal QUE sur la part qui
    dépasse le seuil.
    taux_normal : surcharge du taux normal, uniquement pour tester la
    sensibilité du résultat à ce taux (graphique tornade) - 25% reste le
    défaut partout ailleurs dans l'outil.
    """
    if profit <= SEUIL_IS_REDUIT:
        return profit * TAUX_IS_REDUIT
    return SEUIL_IS_REDUIT * TAUX_IS_REDUIT + (profit - SEUIL_IS_REDUIT) * taux_normal


def calcul_ir(revenu_imposable):
    """
    Impôt sur le revenu par tranches (barème progressif).
    Logique : on calcule l'impôt tranche par tranche, jamais un taux unique sur tout.
    """
    impot = 0.0
    borne_precedente = 0
    for borne, taux in BAREME_IR:
        tranche = max(0, min(revenu_imposable, borne) - borne_precedente)
        impot += tranche * taux
        if revenu_imposable <= borne:
            break
        borne_precedente = borne
    return impot


def applique_abattement_salaire(net_imposable_brut, taux_abattement=0.10):
    """
    Déduction forfaitaire de 10% pour frais professionnels, plafonnée.
    S'applique aux salaires avant le calcul de l'IR, pas aux dividendes.
    taux_abattement : surcharge du taux (10% actuellement), uniquement
    pour tester la sensibilité du résultat à ce taux (graphique tornade) -
    10% reste le défaut partout ailleurs dans l'outil. Les bornes planchers
    et plafond (en euros) restent celles réellement en vigueur : seul le
    taux appliqué à l'intérieur de cette fourchette est testé.
    """
    abattement = net_imposable_brut * taux_abattement
    abattement = max(ABATTEMENT_10_MIN, min(abattement, ABATTEMENT_10_MAX))
    return net_imposable_brut - abattement


def net_apres_salaire(montant_disponible, pass_value=PASS_2026, abattement_taux=0.10):
    """
    Scénario salaire : on part du coût total que l'entreprise est prête à
    payer, on en déduit le brut (par dichotomie), on retire les charges
    salariales pour avoir le net avant abattement, on applique l'abattement
    de 10% (plafonné) propre aux salaires, puis l'IR sur ce qui reste.
    pass_value : surcharge du PASS, abattement_taux : surcharge du taux
    d'abattement forfaitaire (10%) - toutes deux uniquement pour le
    graphique tornade de sensibilité (voir brut_depuis_cout_total et
    applique_abattement_salaire).
    """
    brut = brut_depuis_cout_total(montant_disponible, pass_value=pass_value)
    _, charges_salarie = charges_sur_brut(brut, pass_value)
    net_avant_abattement = brut - charges_salarie
    net_imposable = applique_abattement_salaire(net_avant_abattement, abattement_taux)
    impot = calcul_ir(net_imposable)
    return net_avant_abattement - impot


def net_apres_dividende(montant_disponible, taux_is_normal=TAUX_IS_NORMAL):
    """
    Scénario dividende : IS d'abord (sur le profit avant distribution), puis PFU.
    taux_is_normal : surcharge du taux normal d'IS, uniquement pour le
    graphique tornade de sensibilité (voir calcul_is).
    """
    is_du = calcul_is(montant_disponible, taux_is_normal)
    distribuable = montant_disponible - is_du
    return distribuable * (1 - TAUX_PFU)


if __name__ == "__main__":
    # Test rapide avec un cas simple, pour vérifier que ça tourne
    montant = 80000
    print(f"Montant disponible : {montant} €")
    print(f"Net si salaire   : {net_apres_salaire(montant):,.0f} €")
    print(f"Net si dividende : {net_apres_dividende(montant):,.0f} €")
