"""
Module succession - Droits de succession (hors donation), selon le lien
de parenté entre le défunt et l'héritier.
Grand Large Patrimoine - projet de stage

IMPORTANT : outil informatif uniquement, ne constitue pas un conseil
fiscal ou juridique personnalisé. Barèmes vérifiés en octobre 2026.
Sources : service-public.gouv.fr, auguste-patrimoine.fr, legare.fr
(articles 777, 779, 796-0 bis et 796-0 ter du CGI).

PRINCIPE :
Les droits de succession dépendent avant tout du lien de parenté avec le
défunt :
- Conjoint survivant ou partenaire pacsé : exonération TOTALE, quel que
  soit le montant hérité (article 796-0 bis du CGI, depuis la loi TEPA
  de 2007) - à la différence d'une donation entre vifs entre époux ou
  partenaires, qui reste taxée (hors succession, donc hors champ de ce
  module).
- Enfant (ligne directe) : même barème ET même abattement de 100 000 €
  qu'une donation en ligne directe (article 777 du CGI - les deux
  partagent légalement le même barème). Ce module réutilise directement
  calcul_droits_donation_famille de demembrement.py plutôt que de
  dupliquer une seconde copie du même barème.
- Frère/sœur : abattement de 15 932 €, puis barème propre à deux tranches
  (35 % / 45 %). Une exonération totale existe par ailleurs sous
  conditions cumulatives strictes (célibataire, veuf, divorcé ou séparé
  de corps, âgé de plus de 50 ans ou infirme, domicilié avec le défunt
  depuis plus de 5 ans - article 796-0 ter du CGI) - NON modélisée ici,
  à vérifier au cas par cas.
- Neveu/nièce : abattement de 7 967 €, taux fixe de 55 %.
- Toute autre personne (sans lien de parenté, concubin non pacsé) :
  abattement de 1 594 €, taux fixe de 60 %.

CE QUE CE MODULE NE FAIT PAS : il ne tient pas compte d'une assurance-vie
transmise en parallèle (voir assurance_vie.py, qui suppose justement cet
abattement de 100 000 € encore disponible en totalité pour ne pas compter
deux fois le même abattement), ni des donations antérieures de moins de
15 ans qui réduiraient l'abattement encore disponible, ni du rapport civil
des donations antérieures à la succession.
"""

from demembrement import ABATTEMENT_DONATION_LIGNE_DIRECTE, calcul_droits_donation_famille

ABATTEMENT_SUCCESSION_LIGNE_DIRECTE = ABATTEMENT_DONATION_LIGNE_DIRECTE  # 100 000 € - article 779 du CGI

ABATTEMENT_FRERE_SOEUR = 15_932
BAREME_FRERE_SOEUR = [
    (24_430, 0.35),
    (float("inf"), 0.45),
]

ABATTEMENT_NEVEU_NIECE = 7_967
TAUX_NEVEU_NIECE = 0.55

ABATTEMENT_TIERS = 1_594
TAUX_TIERS = 0.60

CONJOINT = "Conjoint survivant / partenaire pacsé"
ENFANT = "Enfant (ligne directe)"
FRERE_SOEUR = "Frère ou sœur"
NEVEU_NIECE = "Neveu ou nièce"
TIERS = "Autre (sans lien de parenté)"

LIENS_PARENTE = [CONJOINT, ENFANT, FRERE_SOEUR, NEVEU_NIECE, TIERS]


def _calcul_par_tranches(base_taxable, bareme):
    """Même logique que calcul_droits_donation dans demembrement.py :
    barème progressif par tranches, chaque tranche n'étant taxée qu'une
    fois."""
    droits = 0.0
    borne_precedente = 0
    for borne, taux in bareme:
        tranche = max(0, min(base_taxable, borne) - borne_precedente)
        droits += tranche * taux
        if base_taxable <= borne:
            break
        borne_precedente = borne
    return droits


def calcul_droits_succession(valeur_transmise, lien_parente, nombre_enfants=1):
    """
    Droits de succession dus sur valeur_transmise, selon le lien de
    parenté avec le défunt.

    Pour lien_parente = ENFANT, valeur_transmise est la masse successorale
    TOTALE revenant aux enfants, répartie à parts égales entre
    nombre_enfants (chacun bénéficiant de son propre abattement de
    100 000 €) - voir calcul_droits_donation_famille. Pour tous les
    autres liens, valeur_transmise est la part reçue par UN SEUL héritier.
    """
    if lien_parente == CONJOINT:
        return 0.0
    if lien_parente == ENFANT:
        return calcul_droits_donation_famille(
            valeur_transmise, nombre_enfants=nombre_enfants, nombre_donateurs=1,
            abattement=ABATTEMENT_SUCCESSION_LIGNE_DIRECTE,
        )
    if lien_parente == FRERE_SOEUR:
        base_taxable = max(0, valeur_transmise - ABATTEMENT_FRERE_SOEUR)
        return _calcul_par_tranches(base_taxable, BAREME_FRERE_SOEUR)
    if lien_parente == NEVEU_NIECE:
        base_taxable = max(0, valeur_transmise - ABATTEMENT_NEVEU_NIECE)
        return base_taxable * TAUX_NEVEU_NIECE
    if lien_parente == TIERS:
        base_taxable = max(0, valeur_transmise - ABATTEMENT_TIERS)
        return base_taxable * TAUX_TIERS
    raise ValueError(f"Lien de parenté inconnu : {lien_parente!r}")


def comparer_liens_parente(valeur_transmise, nombre_enfants=1):
    """
    Calcule les droits dus, pour une même valeur successorale, SI elle
    revenait en totalité à chacun des liens de parenté possibles l'un
    après l'autre - pour visualiser l'écart (souvent considérable) selon
    qui hérite. Pour la ligne "Enfant", la valeur est répartie entre
    nombre_enfants (c'est un scénario réaliste à plusieurs héritiers) ;
    pour les autres liens, un seul héritier reçoit toute la valeur.
    """
    resultats = []
    for lien in LIENS_PARENTE:
        droits = calcul_droits_succession(valeur_transmise, lien, nombre_enfants)
        resultats.append({
            "lien": lien,
            "droits": droits,
            "net": valeur_transmise - droits,
            "taux_effectif": droits / valeur_transmise if valeur_transmise else 0.0,
        })
    return resultats


if __name__ == "__main__":
    valeur = 500_000
    print(f"Succession de {valeur:,.0f} € - droits selon le lien de parenté avec le défunt :\n")
    for r in comparer_liens_parente(valeur, nombre_enfants=2):
        print(f"{r['lien']:<40} droits {r['droits']:>12,.0f} € (taux effectif {r['taux_effectif']:.1%}) -> net {r['net']:>12,.0f} €")
