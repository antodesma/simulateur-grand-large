"""
Module assurance-vie - Fiscalité des contrats d'assurance-vie : rachat
(retrait du vivant) et transmission au décès du souscripteur.
Grand Large Patrimoine - projet de stage

IMPORTANT : outil informatif uniquement, ne constitue pas un conseil
fiscal ou juridique personnalisé. Barèmes vérifiés en octobre 2026.
Sources : previssima.fr (fiscalité des rachats, régime du PFU post-
27/09/2017) et neofa.com (articles 990 I et 757 B du CGI, transmission).

CE QUE CE MODULE SIMPLIFIE (documenté explicitement, dans l'esprit des
autres modules de cet outil) :
- Rachat : seuls les contrats ouverts (ou les versements effectués) À
  PARTIR du 27/09/2017 sont couverts (régime du prélèvement forfaitaire
  unique - PFU - très majoritaire pour tout contrat souscrit aujourd'hui).
  Le régime antérieur (prélèvement forfaitaire libératoire dégressif, ou
  option pour le barème de l'IR) ne concerne que des versements antérieurs
  à cette date sur des contrats déjà existants - il n'est pas modélisé ici.
  Au-delà du seuil de 150 000 € de versements, ce module applique par
  simplification le taux majoré (12,8 %) à la totalité de la part de gains
  rachetée, plutôt qu'une ventilation fine prorata des versements dans le
  temps (non disponible sans l'historique détaillé du contrat).
- Transmission, article 757 B (versements effectués après les 70 ans du
  souscripteur) : ce module traite le contrat d'assurance-vie isolément,
  sans l'additionner à d'éventuels autres biens successoraux déjà transmis
  au même bénéficiaire - il suppose donc l'abattement de succession de
  100 000 € en ligne directe (article 779 du CGI) encore disponible en
  totalité pour ce bénéficiaire. Réutilise le même barème progressif que
  demembrement.py (donations et successions en ligne directe partagent
  légalement le même barème - source : service-public.gouv.fr).
"""

from demembrement import ABATTEMENT_DONATION_LIGNE_DIRECTE, calcul_droits_donation

# --- Fiscalité du rachat (retrait du vivant) ---
# Ne porte que sur la part de GAINS (intérêts) comprise dans le rachat -
# le capital initialement versé n'est jamais taxé, seul ce qu'il a produit
# l'est. Régime applicable aux versements effectués à partir du 27/09/2017.
TAUX_PRELEVEMENTS_SOCIAUX = 0.172  # toujours dus, sans abattement, quelle que soit l'ancienneté

TAUX_IR_RACHAT_MOINS_8_ANS = 0.128
TAUX_IR_RACHAT_PLUS_8_ANS_SOUS_SEUIL = 0.075
TAUX_IR_RACHAT_PLUS_8_ANS_AU_DELA_SEUIL = 0.128
SEUIL_VERSEMENTS_TAUX_REDUIT = 150_000  # porte sur le total des VERSEMENTS, pas sur l'encours

ABATTEMENT_RACHAT_ANNUEL_SEUL = 4_600
ABATTEMENT_RACHAT_ANNUEL_COUPLE = 9_200

# --- Fiscalité de la transmission au décès ---
# Article 990 I du CGI : versements effectués AVANT les 70 ans du souscripteur.
ABATTEMENT_990_I_PAR_BENEFICIAIRE = 152_500
SEUIL_990_I_TAUX_REDUIT = 700_000  # au-delà de l'abattement
TAUX_990_I_REDUIT = 0.20
TAUX_990_I_MAJORE = 0.3125

# Article 757 B du CGI : versements effectués APRÈS les 70 ans du souscripteur.
# Seules les PRIMES VERSÉES (hors gains, intégralement exonérés) sont
# taxables, après un abattement GLOBAL (partagé entre tous les bénéficiaires,
# contrairement au 990 I qui est individuel) de :
ABATTEMENT_757_B_GLOBAL = 30_500


def net_apres_rachat(montant_rachat_part_gains, anciennete_annees, versements_cumules=0,
                      abattement_annuel=ABATTEMENT_RACHAT_ANNUEL_SEUL):
    """
    Net perçu sur la part de GAINS d'un rachat (partiel ou total), pour un
    contrat dont les versements relèvent du régime du PFU (à partir du
    27/09/2017 - la grande majorité des contrats souscrits aujourd'hui).

    montant_rachat_part_gains : la part d'intérêts/plus-values comprise
    dans le montant racheté (le capital initial n'est jamais taxé).
    anciennete_annees : âge du contrat en années.
    versements_cumules : total des versements déjà faits sur le contrat -
    détermine si le taux réduit de 7,5 % s'applique en entier (en-dessous
    de 150 000 €) au-delà de 8 ans d'ancienneté.
    abattement_annuel : 4 600 € (personne seule) ou 9 200 € (couple marié
    ou pacsé, imposition commune) - uniquement au-delà de 8 ans, et à
    répartir sur l'ensemble des rachats de l'année si plusieurs contrats.
    """
    prelevements_sociaux = montant_rachat_part_gains * TAUX_PRELEVEMENTS_SOCIAUX

    if anciennete_annees < 8:
        base_imposable = montant_rachat_part_gains
        taux_ir = TAUX_IR_RACHAT_MOINS_8_ANS
    else:
        base_imposable = max(0, montant_rachat_part_gains - abattement_annuel)
        if versements_cumules <= SEUIL_VERSEMENTS_TAUX_REDUIT:
            taux_ir = TAUX_IR_RACHAT_PLUS_8_ANS_SOUS_SEUIL
        else:
            taux_ir = TAUX_IR_RACHAT_PLUS_8_ANS_AU_DELA_SEUIL

    ir = base_imposable * taux_ir
    return {
        "montant_rachat_part_gains": montant_rachat_part_gains,
        "base_imposable_ir": base_imposable,
        "taux_ir_applique": taux_ir,
        "ir": ir,
        "prelevements_sociaux": prelevements_sociaux,
        "net": montant_rachat_part_gains - ir - prelevements_sociaux,
    }


def prelevement_990_i(capital_transmis, abattement=ABATTEMENT_990_I_PAR_BENEFICIAIRE):
    """
    Taxation au décès des sommes (capital + gains) issues de versements
    effectués AVANT les 70 ans du souscripteur (article 990 I du CGI) :
    abattement de 152 500 € PAR BÉNÉFICIAIRE, puis 20 % jusqu'à 700 000 €
    (après abattement), 31,25 % au-delà.
    """
    base_taxable = max(0, capital_transmis - abattement)
    part_reduite = min(base_taxable, SEUIL_990_I_TAUX_REDUIT)
    part_majoree = max(0, base_taxable - SEUIL_990_I_TAUX_REDUIT)
    return part_reduite * TAUX_990_I_REDUIT + part_majoree * TAUX_990_I_MAJORE


def prelevement_757_b(primes_versees, nombre_beneficiaires=1,
                       abattement_global=ABATTEMENT_757_B_GLOBAL,
                       abattement_succession=ABATTEMENT_DONATION_LIGNE_DIRECTE):
    """
    Taxation au décès des sommes issues de versements effectués APRÈS les
    70 ans du souscripteur (article 757 B du CGI) : seule la part des
    PRIMES VERSÉES est taxable (les gains sont intégralement exonérés),
    après un abattement de 30 500 € GLOBAL (réparti au prorata entre tous
    les bénéficiaires, contrairement au 990 I qui est individuel) ; le
    solde est réintégré fictivement dans la succession et taxé au barème
    progressif en ligne directe (même barème que les donations - voir
    demembrement.py), abattement de succession de 100 000 € compris.

    primes_versees : part des PRIMES SEULES (hors gains) revenant à CE
    bénéficiaire (déjà répartie si plusieurs bénéficiaires).
    nombre_beneficiaires : sert à répartir l'abattement global de 30 500 €
    au prorata du nombre de bénéficiaires (répartition simplifiée à parts
    égales - en pratique, elle se fait au prorata des parts de chacun).
    """
    nombre_beneficiaires = max(1, nombre_beneficiaires)
    abattement_part = abattement_global / nombre_beneficiaires
    base_taxable = max(0, primes_versees - abattement_part)
    droits_succession = calcul_droits_donation(base_taxable, abattement=abattement_succession)
    return {
        "primes_versees": primes_versees,
        "abattement_applique": abattement_part,
        "base_taxable_apres_abattement_757b": base_taxable,
        "droits_succession": droits_succession,
        "net_beneficiaire": primes_versees - droits_succession,
    }


def taxation_transmission(capital_transmis, age_versement, part_primes_versees=None, nombre_beneficiaires=1):
    """
    Point d'entrée unique : calcule la taxation au décès d'un contrat
    d'assurance-vie pour UN bénéficiaire, selon que les versements ont été
    faits avant ou après les 70 ans du souscripteur (c'est l'ÂGE AU MOMENT
    DU VERSEMENT qui compte, pas l'âge au décès).

    capital_transmis : capital transmis à ce bénéficiaire (versements +
    gains, déjà réparti si plusieurs bénéficiaires).
    part_primes_versees : part des PRIMES SEULES dans ce capital -
    nécessaire uniquement si age_versement >= 70 (article 757 B) ; si non
    fournie dans ce cas, on suppose par défaut que tout le capital transmis
    correspond à des primes (hypothèse la plus défavorable - les gains sont
    en réalité souvent surestimés dans ce cas par excès de prudence).
    """
    if age_versement < 70:
        prelevement = prelevement_990_i(capital_transmis)
        return {
            "article": "990 I",
            "capital_transmis": capital_transmis,
            "prelevement": prelevement,
            "net_beneficiaire": capital_transmis - prelevement,
        }

    primes = part_primes_versees if part_primes_versees is not None else capital_transmis
    detail = prelevement_757_b(primes, nombre_beneficiaires)
    gains_exoneres = capital_transmis - primes
    return {
        "article": "757 B",
        "capital_transmis": capital_transmis,
        "primes_versees": primes,
        "gains_exoneres": gains_exoneres,
        "prelevement": detail["droits_succession"],
        "net_beneficiaire": detail["net_beneficiaire"] + gains_exoneres,
    }


if __name__ == "__main__":
    print("--- Rachat, contrat de 10 ans, 20 000 € de gains, 300 000 € de versements cumulés ---")
    r = net_apres_rachat(20_000, anciennete_annees=10, versements_cumules=300_000)
    print(f"Base imposable à l'IR : {r['base_imposable_ir']:,.0f} € (taux {r['taux_ir_applique']:.1%})")
    print(f"IR : {r['ir']:,.0f} € | Prélèvements sociaux : {r['prelevements_sociaux']:,.0f} €")
    print(f"Net perçu sur les gains rachetés : {r['net']:,.0f} € (sur {r['montant_rachat_part_gains']:,.0f} €)")

    print("\n--- Transmission, versements à 65 ans, 400 000 € transmis à un bénéficiaire ---")
    t1 = taxation_transmission(400_000, age_versement=65)
    print(f"Article {t1['article']} : prélèvement {t1['prelevement']:,.0f} € -> net {t1['net_beneficiaire']:,.0f} €")

    print("\n--- Transmission, versements à 75 ans, 400 000 € dont 350 000 € de primes, 1 bénéficiaire ---")
    t2 = taxation_transmission(400_000, age_versement=75, part_primes_versees=350_000)
    print(f"Article {t2['article']} : prélèvement {t2['prelevement']:,.0f} € -> net {t2['net_beneficiaire']:,.0f} €")
