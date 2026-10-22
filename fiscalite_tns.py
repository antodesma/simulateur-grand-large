"""
Module fiscalite_tns - Cotisations sociales du gérant majoritaire de SARL
(statut de travailleur non salarié, TNS), par opposition au président de
SASU (assimilé salarié) couvert par fiscalite.py.
Grand Large Patrimoine - projet de stage

IMPORTANT : outil informatif uniquement, ne constitue pas un conseil
fiscal ou social personnalisé. Barèmes TNS vérifiés en octobre 2026
(source principale : hayot-expertise.fr, barème commerçants/artisans
2026 - aucun tableau officiel URSSAF dédié spécifiquement au gérant
majoritaire de SARL n'a été trouvé ; le gérant majoritaire relève en
pratique du même barème que les commerçants). Ce module simplifie
volontairement deux points, faute de seconde source permettant de les
vérifier avec certitude :
  1. La progressivité des cotisations maladie-maternité et allocations
     familiales entre leurs seuils bas et haut est ici interpolée
     linéairement (l'URSSAF ne publie pas la formule exacte de la
     courbe, seulement les paliers 0% / taux plein).
  2. L'assiette de la CSG-CRDS est prise égale à la rémunération
     professionnelle elle-même (hors un abattement forfaitaire
     spécifique parfois mentionné, dont le taux exact n'a pas pu être
     confirmé par une seconde source).
Ces deux points sont à vérifier auprès d'un expert-comptable avant tout
usage au-delà d'une démonstration pédagogique.

PRINCIPE SARL/TNS (par opposition à la SASU) :
- Pas de distinction charges patronales / salariales : le gérant
  majoritaire paie lui-même l'intégralité de ses cotisations sur la
  rémunération que lui verse la société (déductible de l'IS).
- Pas de cotisation chômage (identique à la SASU sur ce point).
- Cotisations globalement moins élevées que le régime assimilé salarié,
  en contrepartie de droits sociaux moindres (retraite, prévoyance).
- Dividendes : pour un gérant majoritaire, la fraction des dividendes
  qui dépasse 10% du capital social (parts du gérant et de sa famille
  proche) + primes d'émission + solde moyen du compte courant d'associé
  est réintégrée dans l'assiette des cotisations sociales TNS (article
  L131-6 du code de la sécurité sociale). Seule la part sous ce seuil
  reste au régime du PFU classique (12,8% IR + 18,6% prélèvements
  sociaux). Source : lecoindesentrepreneurs.fr.
"""

from fiscalite import PASS_2026, TAUX_IS_NORMAL, TAUX_PFU, calcul_ir, calcul_is

TAUX_IR_SEUL_PFU = 0.128  # la part "impôt sur le revenu" du PFU (12,8%), sans les 18,6% de prélèvements sociaux

# --- Cotisations à taux fixe, par tranche de revenu professionnel ---
TAUX_RETRAITE_BASE_T1 = 0.1787      # jusqu'à 1 PASS
TAUX_RETRAITE_BASE_T2 = 0.0072      # au-delà de 1 PASS, sans plafond
TAUX_RCI_T1 = 0.0810                # jusqu'à 1 PASS
TAUX_RCI_T2 = 0.0910                # de 1 à 4 PASS
PLAFOND_RCI = 4 * PASS_2026
TAUX_INVALIDITE_DECES = 0.0130      # jusqu'à 1 PASS seulement
TAUX_INDEMNITES_JOURNALIERES = 0.0050  # jusqu'à 5 PASS
PLAFOND_IJ = 5 * PASS_2026
TAUX_CSG_CRDS = 0.0970              # sur la rémunération professionnelle, sans plafond

# --- Cotisations à taux progressif (interpolation linéaire, cf. docstring) ---
SEUIL_BAS_MALADIE = 0.20 * PASS_2026
SEUIL_HAUT_MALADIE = 3.00 * PASS_2026
TAUX_MAX_MALADIE = 0.0850
TAUX_AU_DELA_MALADIE = 0.0650  # taux qui redescend au-delà de 300% du PASS

SEUIL_BAS_FAMILLE = 1.10 * PASS_2026
SEUIL_HAUT_FAMILLE = 1.40 * PASS_2026
TAUX_MAX_FAMILLE = 0.0310

# --- Forfait formation professionnelle (catégorie commerçant, par défaut pour un gérant de SARL) ---
FORFAIT_FORMATION_PRO = 0.0025 * PASS_2026

# --- Cotisation minimale (base forfaitaire même à revenu nul ou très faible) ---
BASE_MIN_IJ = 0.40 * PASS_2026
BASE_MIN_RETRAITE = 0.1125 * PASS_2026
BASE_MIN_INVALIDITE = 0.1150 * PASS_2026


def _taux_progressif(revenu, seuil_bas, seuil_haut, taux_max, taux_au_dela=None):
    """Taux interpolé linéairement entre 0 (sous seuil_bas) et taux_max
    (à seuil_haut), appliqué à la totalité du revenu (pas par tranche) -
    c'est ainsi que l'URSSAF présente ces deux cotisations (un taux
    "plein" déterminé par le niveau de revenu, pas un barème marginal)."""
    if revenu <= seuil_bas:
        return 0.0
    if revenu >= seuil_haut:
        return taux_au_dela if taux_au_dela is not None else taux_max
    return taux_max * (revenu - seuil_bas) / (seuil_haut - seuil_bas)


def cotisations_tns(remuneration):
    """
    Calcule le total des cotisations sociales TNS dues sur une
    rémunération professionnelle annuelle (gérant majoritaire de SARL).
    Renvoie le montant total des cotisations (détail non renvoyé, somme
    uniquement - cohérent avec le niveau de détail déjà utilisé pour la
    SASU dans fiscalite.py).
    """
    tranche1 = min(remuneration, PASS_2026)
    tranche2_rci = max(0, min(remuneration, PLAFOND_RCI) - PASS_2026)
    tranche_au_dela_pass = max(0, remuneration - PASS_2026)
    tranche_ij = min(remuneration, PLAFOND_IJ)

    retraite_base = tranche1 * TAUX_RETRAITE_BASE_T1 + tranche_au_dela_pass * TAUX_RETRAITE_BASE_T2
    retraite_base = max(retraite_base, BASE_MIN_RETRAITE * TAUX_RETRAITE_BASE_T1)

    rci = tranche1 * TAUX_RCI_T1 + tranche2_rci * TAUX_RCI_T2

    invalidite_deces = max(tranche1 * TAUX_INVALIDITE_DECES, BASE_MIN_INVALIDITE * TAUX_INVALIDITE_DECES)

    indemnites_journalieres = max(tranche_ij * TAUX_INDEMNITES_JOURNALIERES, BASE_MIN_IJ * TAUX_INDEMNITES_JOURNALIERES)

    taux_maladie = _taux_progressif(remuneration, SEUIL_BAS_MALADIE, SEUIL_HAUT_MALADIE, TAUX_MAX_MALADIE, TAUX_AU_DELA_MALADIE)
    maladie = remuneration * taux_maladie

    taux_famille = _taux_progressif(remuneration, SEUIL_BAS_FAMILLE, SEUIL_HAUT_FAMILLE, TAUX_MAX_FAMILLE)
    allocations_familiales = remuneration * taux_famille

    csg_crds = remuneration * TAUX_CSG_CRDS

    formation_pro = FORFAIT_FORMATION_PRO

    return (
        retraite_base + rci + invalidite_deces + indemnites_journalieres
        + maladie + allocations_familiales + csg_crds + formation_pro
    )


def net_apres_remuneration_tns(montant_disponible):
    """
    Scénario rémunération pour un gérant majoritaire de SARL : la société
    verse une rémunération égale au montant disponible (déductible en
    totalité de l'IS, pas de charges patronales séparées contrairement à
    la SASU), le gérant paie lui-même ses cotisations TNS dessus, puis
    l'abattement forfaitaire de 10% et l'IR s'appliquent comme pour un
    salaire (article 62 du CGI).
    """
    from fiscalite import applique_abattement_salaire

    remuneration = montant_disponible
    cotisations = cotisations_tns(remuneration)
    net_avant_abattement = remuneration - cotisations
    net_imposable = applique_abattement_salaire(net_avant_abattement)
    impot = calcul_ir(net_imposable)
    return net_avant_abattement - impot


def seuil_dividendes_sans_cotisations(capital_social, compte_courant_moyen=0.0, primes_emission=0.0):
    """Plafond annuel de dividendes non réintégrés dans l'assiette des
    cotisations TNS : 10% de (capital social détenu par le gérant et sa
    famille proche + solde moyen du compte courant d'associé + primes
    d'émission). Au-delà, l'excédent est soumis aux cotisations TNS."""
    return 0.10 * (capital_social + compte_courant_moyen + primes_emission)


def net_apres_dividende_tns(montant_disponible, capital_social, compte_courant_moyen=0.0, primes_emission=0.0, taux_is_normal=TAUX_IS_NORMAL):
    """
    Scénario dividende pour un gérant majoritaire de SARL : IS d'abord
    (identique à la SASU), puis séparation du dividende distribuable en
    deux parts selon le seuil des 10% - la part sous le seuil reste au
    PFU classique (31,4%), la part au-dessus est réintégrée dans
    l'assiette des cotisations TNS (calculées sur cette seule part,
    traitée comme un revenu professionnel isolé - simplification
    explicite, cf. docstring du module) et ne supporte que les 12,8%
    d'impôt sur le revenu du PFU (la CSG-CRDS est déjà comprise dans les
    cotisations).
    taux_is_normal : surcharge du taux normal d'IS, uniquement pour le
    graphique tornade de sensibilité (voir fiscalite.calcul_is).
    """
    is_du = calcul_is(montant_disponible, taux_is_normal)
    distribuable = montant_disponible - is_du
    seuil = seuil_dividendes_sans_cotisations(capital_social, compte_courant_moyen, primes_emission)

    part_sous_seuil = min(distribuable, seuil)
    part_au_dela = max(0.0, distribuable - seuil)

    net_sous_seuil = part_sous_seuil * (1 - TAUX_PFU)

    # Si aucune part ne dépasse le seuil, aucune réintégration dans l'assiette
    # TNS n'a lieu : la cotisation minimale (due même à revenu professionnel
    # nul, cf. cotisations_tns) ne doit pas s'appliquer ici, elle n'a de sens
    # que pour une rémunération réellement versée.
    cotisations_exces = cotisations_tns(part_au_dela) if part_au_dela > 0 else 0.0
    net_au_dela = part_au_dela - cotisations_exces - part_au_dela * TAUX_IR_SEUL_PFU

    return {
        "net_total": net_sous_seuil + net_au_dela,
        "part_sous_seuil": part_sous_seuil,
        "part_au_dela": part_au_dela,
        "cotisations_exces": cotisations_exces,
        "seuil": seuil,
    }


def net_apres_dividende_tns_pur(montant_disponible, capital_social, compte_courant_moyen=0.0, primes_emission=0.0):
    """
    Net réel si le gérant majoritaire choisit de ne se verser AUCUNE
    rémunération et de tout prendre en dividende (p=0% dans l'optimiseur de
    répartition). Tant qu'il reste gérant majoritaire, il reste affilié au
    régime TNS et doit la cotisation minimale forfaitaire même à
    rémunération nulle (cf. cotisations_tns) : net_apres_dividende_tns()
    seul l'omet, parce qu'il ne modélise que la fiscalité du dividende, pas
    le coût de l'affiliation elle-même.
    """
    net_dividende = net_apres_dividende_tns(
        montant_disponible, capital_social, compte_courant_moyen, primes_emission
    )["net_total"]
    return net_dividende - cotisations_tns(0)


if __name__ == "__main__":
    montant = 80_000
    print(f"Montant disponible : {montant} €")
    print(f"Cotisations TNS sur {montant} € de rémunération : {cotisations_tns(montant):,.0f} €")
    print(f"Net si rémunération (gérant SARL) : {net_apres_remuneration_tns(montant):,.0f} €")
    resultat_div = net_apres_dividende_tns(montant, capital_social=10_000)
    print(f"Net si dividende (gérant SARL, capital 10 000€) : {resultat_div['net_total']:,.0f} €")
    print(f"  dont part sous le seuil des 10% : {resultat_div['part_sous_seuil']:,.0f} €, part au-delà : {resultat_div['part_au_dela']:,.0f} €")
