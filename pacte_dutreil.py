"""
Module pacte_dutreil.py - Transmission d'entreprise avec le Pacte Dutreil
(article 787 B du Code général des impôts).
Grand Large Patrimoine - projet de stage

IMPORTANT : outil informatif uniquement, ne constitue pas un conseil
fiscal ou juridique personnalisé. Le Pacte Dutreil est un dispositif à
conditions - ce module calcule l'économie de droits SI les conditions
sont réunies, il ne vérifie pas leur respect. Chaque situation (société
opérationnelle vs holding, pacte signé vs engagement réputé acquis,
exercice effectif de la fonction de direction) doit être validée avec un
avocat fiscaliste ou un notaire avant toute mise en œuvre.

PRINCIPE :
Transmettre les titres d'une entreprise (donation ou succession) ouvre
droit, sous conditions, à une exonération de 75% de la valeur transmise
avant application du barème des droits de mutation à titre gratuit.
Seul le quart restant de la valeur est soumis aux droits de donation
(abattement en ligne directe de l'article 779 du CGI, puis barème
progressif - même logique que pour une transmission "classique").

Sources (vérifiées le 22 octobre 2026, deux sources concordantes) :
- Seuils de détention pour l'engagement collectif de conservation (ECC) :
  17% des droits financiers et 34% des droits de vote pour une société
  non cotée ; 10% et 20% pour une société cotée.
- Durée de l'ECC : 2 ans minimum à compter de l'enregistrement du pacte.
- Durée de l'engagement individuel de conservation (EIC), à la suite de
  l'ECC : 6 ans pour les transmissions à compter du 21 février 2026
  (contre 4 ans auparavant - la loi a changé en cours d'année 2026).
  Durée totale de conservation : 8 ans.
- Fonction de direction : exercée par l'un des signataires pendant l'ECC,
  puis par l'un des donataires (ou un signataire) pendant les 3 années
  suivant la transmission.
- Taux d'exonération : 75% de la valeur transmise.
- Un engagement "réputé acquis" dispense de pacte signé si le dirigeant
  détient seul (ou avec son foyer fiscal) les seuils requis depuis plus
  de 2 ans et exerce depuis plus de 2 ans une fonction de direction.
"""

from demembrement import calcul_droits_donation_famille, ABATTEMENT_DONATION_LIGNE_DIRECTE

TAUX_EXONERATION_DUTREIL = 0.75

SEUILS_ENGAGEMENT_COLLECTIF = {
    "non cotée": {"droits_financiers": 0.17, "droits_de_vote": 0.34},
    "cotée": {"droits_financiers": 0.10, "droits_de_vote": 0.20},
}

DUREE_ENGAGEMENT_COLLECTIF_ANNEES = 2
DUREE_ENGAGEMENT_INDIVIDUEL_ANNEES = 6  # depuis le 21 février 2026 (était 4 ans avant)
DUREE_TOTALE_CONSERVATION_ANNEES = DUREE_ENGAGEMENT_COLLECTIF_ANNEES + DUREE_ENGAGEMENT_INDIVIDUEL_ANNEES
DUREE_FONCTION_DIRECTION_APRES_TRANSMISSION_ANNEES = 3

CONDITIONS_PACTE_DUTREIL = [
    "Engagement collectif de conservation (ECC) d'au moins 2 ans, en cours au jour de la transmission, "
    "portant sur au moins 17 % des droits financiers et 34 % des droits de vote (10 % et 20 % si la "
    "société est cotée).",
    "Engagement individuel de conservation (EIC) de 6 ans supplémentaires par chaque donataire à "
    "l'expiration de l'engagement collectif - 8 ans de conservation au total (ce délai est passé de "
    "4 à 6 ans pour les transmissions à compter du 21 février 2026).",
    "Exercice d'une fonction de direction par l'un des signataires de l'engagement collectif pendant "
    "sa durée, puis par l'un des donataires (ou un signataire) pendant les 3 années suivant la "
    "transmission.",
    "À défaut de pacte signé formellement, un engagement « réputé acquis » est possible si le dirigeant "
    "détient seul, ou avec son foyer fiscal, les seuils requis depuis plus de 2 ans et exerce depuis "
    "plus de 2 ans une fonction de direction.",
]


def calcul_transmission_dutreil(
    valeur_entreprise,
    nombre_enfants=1,
    nombre_donateurs=1,
    abattement=ABATTEMENT_DONATION_LIGNE_DIRECTE,
):
    """
    Compare les droits de donation d'une transmission d'entreprise avec et
    sans l'exonération Dutreil de 75%, pour une famille de nombre_enfants
    enfants et nombre_donateurs parent(s) donateur(s). Réutilise le même
    barème et la même logique d'abattement par enfant/par parent que le
    module démembrement, puisque l'abattement de l'article 779 du CGI et
    le barème progressif s'appliquent de façon identique, que la valeur
    transmise soit ou non réduite par le Pacte Dutreil.
    """
    valeur_exoneree = valeur_entreprise * TAUX_EXONERATION_DUTREIL
    valeur_taxable_apres_dutreil = valeur_entreprise - valeur_exoneree

    droits_sans_dutreil = calcul_droits_donation_famille(
        valeur_entreprise, nombre_enfants, nombre_donateurs, abattement
    )
    droits_avec_dutreil = calcul_droits_donation_famille(
        valeur_taxable_apres_dutreil, nombre_enfants, nombre_donateurs, abattement
    )

    return {
        "valeur_entreprise": valeur_entreprise,
        "valeur_exoneree": valeur_exoneree,
        "valeur_taxable_apres_dutreil": valeur_taxable_apres_dutreil,
        "nombre_enfants": nombre_enfants,
        "nombre_donateurs": nombre_donateurs,
        "droits_sans_dutreil": droits_sans_dutreil,
        "droits_avec_dutreil": droits_avec_dutreil,
        "economie": droits_sans_dutreil - droits_avec_dutreil,
    }


if __name__ == "__main__":
    resultat = calcul_transmission_dutreil(valeur_entreprise=2_000_000, nombre_enfants=2, nombre_donateurs=2)
    print(f"Entreprise valorisée {resultat['valeur_entreprise']:,.0f} €, "
          f"{resultat['nombre_enfants']} enfant(s), {resultat['nombre_donateurs']} parent(s) donateur(s)")
    print(f"Valeur exonérée (75 %)         : {resultat['valeur_exoneree']:,.0f} €")
    print(f"Valeur taxable après Dutreil   : {resultat['valeur_taxable_apres_dutreil']:,.0f} €")
    print(f"Droits sans le Pacte Dutreil   : {resultat['droits_sans_dutreil']:,.0f} €")
    print(f"Droits avec le Pacte Dutreil   : {resultat['droits_avec_dutreil']:,.0f} €")
    print(f"Économie de droits             : {resultat['economie']:,.0f} €")
