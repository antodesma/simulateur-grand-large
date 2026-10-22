"""
Module IFI - Impôt sur la fortune immobilière.
Grand Large Patrimoine - projet de stage

IMPORTANT : outil informatif uniquement, ne constitue pas un conseil
fiscal ou juridique personnalisé. Barèmes vérifiés en octobre 2026.
Source : articles 964, 973 et 977 du CGI (voir moicombien.fr pour une
synthèse à jour, recoupée avec le barème officiel).

PRINCIPE :
L'IFI remplace l'ISF depuis 2018 et ne porte plus que sur le patrimoine
IMMOBILIER (hors biens professionnels qualifiés comme tels), pas sur
l'ensemble du patrimoine. Il est dû dès que ce patrimoine immobilier net
taxable dépasse 1 300 000 € au 1er janvier de l'année - mais, une fois ce
seuil franchi, le barème progressif s'applique dès 800 001 €, pas depuis
le premier euro (même logique de seuil d'assujettissement vs barème
progressif que pour l'IR).

CE QUE CE MODULE NE FAIT PAS : il ne qualifie pas lui-même un bien de
"professionnel" (holding animatrice, bien loué en location meublée
professionnelle, etc. - sujets à conditions précises et contentieux
fréquent) ; il suppose que l'utilisateur a déjà fait ce tri et saisit
directement le patrimoine immobilier NON professionnel. Il ne modélise
pas non plus le plafonnement de l'IFI (IFI + impôts sur le revenu de
l'année précédente ne peut excéder 75 % des revenus de cette même année,
article 979 du CGI) - mécanisme utile mais qui dépend de l'ensemble des
revenus du foyer, hors périmètre de ce calculateur.
"""

SEUIL_ASSUJETTISSEMENT_IFI = 1_300_000  # en-deçà, pas d'IFI du tout (article 964 du CGI)

ABATTEMENT_RESIDENCE_PRINCIPALE = 0.30  # article 973 du CGI - résidence principale détenue en direct uniquement

# --- Barème progressif (article 977 du CGI) ---
BAREME_IFI = [
    (800_000, 0.0),
    (1_300_000, 0.005),
    (2_570_000, 0.007),
    (5_000_000, 0.01),
    (10_000_000, 0.0125),
    (float("inf"), 0.015),
]

# --- Décote pour un patrimoine net taxable entre 1 300 000 € et 1 400 000 € ---
# Lisse l'effet de seuil à l'entrée dans l'IFI (sans elle, franchir 1,3 M€ de
# quelques euros ferait basculer instantanément dans tout le barème).
DECOTE_SEUIL_BAS = 1_300_000
DECOTE_SEUIL_HAUT = 1_400_000
DECOTE_CONSTANTE = 17_500
DECOTE_TAUX = 0.0125


def assiette_ifi(valeur_residence_principale=0, valeur_autres_biens_immobiliers=0, dettes_deductibles=0):
    """
    Patrimoine immobilier net taxable : la résidence principale bénéficie
    d'un abattement de 30 % (si détenue en direct - pas via une SCI),
    les autres biens immobiliers (résidences secondaires, locatifs, parts
    de SCI non professionnelle...) sont retenus à 100 %, et les dettes
    réellement déductibles (emprunts immobiliers restant dus notamment)
    viennent en diminution.
    """
    valeur_residence_apres_abattement = valeur_residence_principale * (1 - ABATTEMENT_RESIDENCE_PRINCIPALE)
    brut = valeur_residence_apres_abattement + valeur_autres_biens_immobiliers
    return max(0, brut - dettes_deductibles)


def _calcul_par_tranches(base_taxable, bareme):
    droits = 0.0
    borne_precedente = 0
    for borne, taux in bareme:
        tranche = max(0, min(base_taxable, borne) - borne_precedente)
        droits += tranche * taux
        if base_taxable <= borne:
            break
        borne_precedente = borne
    return droits


def calcul_ifi_brut(patrimoine_net_taxable):
    """IFI avant décote, barème progressif par tranches (article 977 du CGI)."""
    return _calcul_par_tranches(patrimoine_net_taxable, BAREME_IFI)


def decote_ifi(patrimoine_net_taxable):
    """
    Décote applicable uniquement entre 1 300 000 € et 1 400 000 € de
    patrimoine net taxable : 17 500 € - 1,25 % x patrimoine, qui s'annule
    exactement à 1 400 000 €.
    """
    if patrimoine_net_taxable < DECOTE_SEUIL_BAS or patrimoine_net_taxable > DECOTE_SEUIL_HAUT:
        return 0.0
    return max(0.0, DECOTE_CONSTANTE - DECOTE_TAUX * patrimoine_net_taxable)


def calcul_ifi(patrimoine_net_taxable):
    """
    IFI net dû : 0 si le patrimoine net taxable est sous le seuil
    d'assujettissement de 1 300 000 € (pas d'IFI du tout, pas même sur la
    fraction au-dessus de 800 000 €) ; sinon, barème progressif moins la
    décote éventuelle (entre 1,3 M€ et 1,4 M€).
    """
    if patrimoine_net_taxable < SEUIL_ASSUJETTISSEMENT_IFI:
        return 0.0
    return max(0.0, calcul_ifi_brut(patrimoine_net_taxable) - decote_ifi(patrimoine_net_taxable))


def synthese_ifi(valeur_residence_principale=0, valeur_autres_biens_immobiliers=0, dettes_deductibles=0):
    """Point d'entrée unique : renvoie l'assiette et l'IFI dû, avec le détail du calcul."""
    assiette = assiette_ifi(valeur_residence_principale, valeur_autres_biens_immobiliers, dettes_deductibles)
    assujetti = assiette >= SEUIL_ASSUJETTISSEMENT_IFI
    ifi_brut = calcul_ifi_brut(assiette) if assujetti else 0.0
    decote = decote_ifi(assiette) if assujetti else 0.0
    return {
        "assiette": assiette,
        "assujetti": assujetti,
        "ifi_brut": ifi_brut,
        "decote": decote,
        "ifi_net": max(0.0, ifi_brut - decote),
    }


if __name__ == "__main__":
    for residence, autres, dettes in [(800_000, 900_000, 200_000), (1_350_000, 0, 0), (3_000_000, 2_000_000, 500_000)]:
        r = synthese_ifi(residence, autres, dettes)
        print(f"Résidence {residence:,.0f} € + autres biens {autres:,.0f} € - dettes {dettes:,.0f} €")
        print(f"  Assiette nette taxable : {r['assiette']:,.0f} € (assujetti : {r['assujetti']})")
        print(f"  IFI brut : {r['ifi_brut']:,.0f} € | Décote : {r['decote']:,.0f} € | IFI net dû : {r['ifi_net']:,.0f} €\n")
