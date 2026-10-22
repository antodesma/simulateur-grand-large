"""
Module sci - SCI (société civile immobilière) à l'impôt sur le revenu (IR,
régime de la transparence fiscale, "translucide") vs à l'impôt sur les
sociétés (IS) : revenus locatifs annuels et plus-value de cession.
Grand Large Patrimoine - projet de stage

IMPORTANT : outil informatif uniquement, ne constitue pas un conseil
fiscal ou juridique personnalisé. Barèmes vérifiés en octobre 2026.
Sources : CGI (régime des revenus fonciers et des plus-values
immobilières des particuliers, articles 150 U et suivants), et le même
calcul_is que fiscalite.py pour la partie IS.

PRINCIPE :
Une SCI à l'IR est "transparente" : les loyers et la plus-value de
cession sont imposés directement entre les mains des associés, au régime
des revenus fonciers et des plus-values immobilières des PARTICULIERS -
pas d'amortissement déductible du bien, mais un abattement pour durée de
détention qui exonère totalement la plus-value après 22 ans (impôt sur
le revenu) et 30 ans (prélèvements sociaux).

Une SCI à l'IS, au contraire, peut amortir le bien comme n'importe quelle
société (ce qui réduit le résultat imposable chaque année, sans sortie de
trésorerie), mais perd l'abattement durée de détention à la revente (la
plus-value se calcule sur la valeur nette COMPTABLE, après amortissements
déjà déduits - donc souvent plus élevée) et subit une DOUBLE imposition
dès que l'argent sort de la société vers l'associé (IS dans la société,
puis PFU sur le dividende) - exactement le même arbitrage que SASU/SARL
vs holding déjà traité ailleurs dans cet outil (voir trajectoire.py).

CE QUE CE MODULE NE FAIT PAS : il ne modélise ni le report des déficits
fonciers (IR) ou des déficits fiscaux (IS) d'une année sur l'autre - il
suppose un résultat positif chaque année - ni la CFE (cotisation foncière
des entreprises, due par une SCI à l'IS qui a une activité de location
nue, généralement minime), ni les droits d'enregistrement de 5 % dus sur
la cession de parts de SCI (hors du champ "revenus + plus-value" traité
ici).
"""

from fiscalite import calcul_is, TAUX_PFU
from assurance_vie import TAUX_PRELEVEMENTS_SOCIAUX

# --- Plus-value immobilière des particuliers (SCI à l'IR) ---
TAUX_IR_PLUS_VALUE_IMMO = 0.19  # taux forfaitaire, avant abattement pour durée de détention


def taux_abattement_ir_duree(annees_detention):
    """
    Abattement pour durée de détention sur la part IMPÔT SUR LE REVENU de
    la plus-value : aucun jusqu'à 5 ans, 6 % par an de la 6e à la 21e
    année (96 % cumulé), puis 4 % la 22e année - exonération totale à
    partir de 22 ans de détention.
    """
    if annees_detention <= 5:
        return 0.0
    if annees_detention >= 22:
        return 1.0
    return (annees_detention - 5) * 0.06


def taux_abattement_ps_duree(annees_detention):
    """
    Abattement pour durée de détention sur la part PRÉLÈVEMENTS SOCIAUX de
    la plus-value : rythme différent et plus lent que l'IR - aucun jusqu'à
    5 ans, 1,65 % par an de la 6e à la 21e année, 1,60 % la 22e année
    (28 % cumulé), puis 9 % par an de la 23e à la 30e année - exonération
    totale à partir de 30 ans de détention seulement.
    """
    if annees_detention <= 5:
        return 0.0
    if annees_detention <= 21:
        return (annees_detention - 5) * 0.0165
    if annees_detention == 22:
        return 0.28
    if annees_detention >= 30:
        return 1.0
    return min(1.0, 0.28 + (annees_detention - 22) * 0.09)


def plus_value_brute(prix_cession, prix_acquisition, frais_acquisition=0, travaux=0):
    """Plus-value brute, avant tout abattement : prix de cession moins le prix
    d'acquisition majoré des frais d'acquisition et des travaux (qui augmentent
    le prix de revient fiscal et réduisent d'autant la plus-value imposable)."""
    return max(0.0, prix_cession - prix_acquisition - frais_acquisition - travaux)


def plus_value_nette_sci_ir(prix_cession, prix_acquisition, annees_detention, frais_acquisition=0, travaux=0):
    """
    Plus-value nette perçue par l'associé d'une SCI à l'IR lors de la
    cession du bien : la plus-value BRUTE subit deux abattements distincts
    (IR et prélèvements sociaux, à des rythmes différents), puis chaque
    base réduite est taxée à son propre taux.
    """
    brute = plus_value_brute(prix_cession, prix_acquisition, frais_acquisition, travaux)
    base_ir = brute * (1 - taux_abattement_ir_duree(annees_detention))
    base_ps = brute * (1 - taux_abattement_ps_duree(annees_detention))
    impot_ir = base_ir * TAUX_IR_PLUS_VALUE_IMMO
    prelevements_sociaux = base_ps * TAUX_PRELEVEMENTS_SOCIAUX
    return {
        "plus_value_brute": brute,
        "impot_ir": impot_ir,
        "prelevements_sociaux": prelevements_sociaux,
        "net": brute - impot_ir - prelevements_sociaux,
    }


def revenu_net_sci_ir(loyers_annuels, charges_deductibles, tmi):
    """
    Revenu net annuel perçu par l'associé d'une SCI à l'IR (régime réel des
    revenus fonciers) : loyers moins charges réellement déductibles
    (intérêts d'emprunt, travaux d'entretien, taxe foncière, assurance,
    frais de gestion - PAS d'amortissement du bien, non déductible dans ce
    régime), le solde étant taxé directement entre les mains de l'associé
    à son taux marginal d'imposition (tmi) plus 17,2 % de prélèvements
    sociaux - rien ne transite par une société, donc pas de double
    imposition possible.
    """
    revenu_foncier_net = max(0.0, loyers_annuels - charges_deductibles)
    impot = revenu_foncier_net * tmi
    prelevements_sociaux = revenu_foncier_net * TAUX_PRELEVEMENTS_SOCIAUX
    return {
        "revenu_foncier_net": revenu_foncier_net,
        "impot": impot,
        "prelevements_sociaux": prelevements_sociaux,
        "net": revenu_foncier_net - impot - prelevements_sociaux,
    }


def revenu_net_sci_is(loyers_annuels, charges_deductibles, amortissement_annuel, distribue=True):
    """
    Revenu net annuel perçu par l'associé d'une SCI à l'IS : le résultat
    comptable (loyers moins charges ET moins l'amortissement du bien, lui
    déductible à l'IS) est d'abord taxé à l'IS dans la société (mêmes
    taux que fiscalite.calcul_is), puis, SI le solde est distribué en
    dividende (distribue=True), re-taxé au PFU chez l'associé - double
    imposition. Si distribue=False, le solde net d'IS reste capitalisé
    dans la société (logique de holding) et rien ne sort pour l'associé
    cette année-là.
    """
    resultat_comptable = max(0.0, loyers_annuels - charges_deductibles - amortissement_annuel)
    is_du = calcul_is(resultat_comptable)
    resultat_apres_is = resultat_comptable - is_du
    net_distribue = resultat_apres_is * (1 - TAUX_PFU) if distribue else 0.0
    return {
        "resultat_comptable": resultat_comptable,
        "is_du": is_du,
        "resultat_apres_is": resultat_apres_is,
        "net": net_distribue,
    }


def plus_value_nette_sci_is(prix_cession, prix_acquisition, amortissements_cumules, distribue=True):
    """
    Plus-value nette perçue par l'associé d'une SCI à l'IS lors de la
    cession : contrairement à l'IR, pas d'abattement pour durée de
    détention, mais la plus-value se calcule sur la valeur nette
    COMPTABLE du bien (prix d'acquisition moins les amortissements déjà
    déduits au fil des ans) - une plus-value souvent bien plus élevée
    qu'à l'IR pour un bien ancien très amorti. Taxée à l'IS, puis
    re-taxée au PFU si le produit de cession est distribué à l'associé.
    """
    valeur_nette_comptable = max(0.0, prix_acquisition - amortissements_cumules)
    brute = max(0.0, prix_cession - valeur_nette_comptable)
    is_du = calcul_is(brute)
    net_societe = brute - is_du
    net_associe = net_societe * (1 - TAUX_PFU) if distribue else net_societe
    return {
        "valeur_nette_comptable": valeur_nette_comptable,
        "plus_value_brute": brute,
        "is_du": is_du,
        "net_societe": net_societe,
        "net": net_associe,
    }


def comparer_sci(
    loyers_annuels, charges_deductibles, amortissement_annuel, tmi,
    prix_acquisition, prix_cession, annees_detention,
    frais_acquisition=0, travaux_plus_value=0, amortissements_cumules=None, distribue=True,
):
    """
    Compare, sur toute la durée de détention, le total perçu par l'associé
    (revenus locatifs annuels cumulés + plus-value nette de cession) entre
    une SCI à l'IR et une SCI à l'IS. amortissements_cumules : si non
    fourni, vaut amortissement_annuel x annees_detention (hypothèse d'un
    amortissement linéaire et constant sur toute la période).
    """
    if amortissements_cumules is None:
        amortissements_cumules = amortissement_annuel * annees_detention

    revenu_ir = revenu_net_sci_ir(loyers_annuels, charges_deductibles, tmi)
    revenu_is = revenu_net_sci_is(loyers_annuels, charges_deductibles, amortissement_annuel, distribue)
    pv_ir = plus_value_nette_sci_ir(prix_cession, prix_acquisition, annees_detention, frais_acquisition, travaux_plus_value)
    pv_is = plus_value_nette_sci_is(prix_cession, prix_acquisition, amortissements_cumules, distribue)

    cumul_revenus_ir = revenu_ir["net"] * annees_detention
    cumul_revenus_is = revenu_is["net"] * annees_detention

    return {
        "revenu_annuel_ir": revenu_ir["net"],
        "revenu_annuel_is": revenu_is["net"],
        "cumul_revenus_ir": cumul_revenus_ir,
        "cumul_revenus_is": cumul_revenus_is,
        "plus_value_nette_ir": pv_ir["net"],
        "plus_value_nette_is": pv_is["net"],
        "total_ir": cumul_revenus_ir + pv_ir["net"],
        "total_is": cumul_revenus_is + pv_is["net"],
    }


if __name__ == "__main__":
    r = comparer_sci(
        loyers_annuels=36_000, charges_deductibles=8_000, amortissement_annuel=10_000, tmi=0.30,
        prix_acquisition=400_000, prix_cession=600_000, annees_detention=15,
    )
    print(f"Revenu net annuel  - IR : {r['revenu_annuel_ir']:,.0f} € | IS (distribué) : {r['revenu_annuel_is']:,.0f} €")
    print(f"Cumulé sur 15 ans  - IR : {r['cumul_revenus_ir']:,.0f} € | IS : {r['cumul_revenus_is']:,.0f} €")
    print(f"Plus-value nette   - IR : {r['plus_value_nette_ir']:,.0f} € | IS : {r['plus_value_nette_is']:,.0f} €")
    print(f"TOTAL perçu        - IR : {r['total_ir']:,.0f} € | IS : {r['total_is']:,.0f} €")
