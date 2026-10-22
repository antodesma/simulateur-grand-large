"""
Module per - PER (plan d'épargne retraite individuel) : plafond de
déduction des versements volontaires, économie d'impôt à l'entrée,
fiscalité de la sortie en capital, comparaison avec un placement
classique à montant brut identique.
Grand Large Patrimoine - projet de stage

IMPORTANT : outil informatif uniquement, ne constitue pas un conseil
fiscal ou juridique personnalisé. Barèmes vérifiés en octobre 2026.
Sources :
- Plafond de déduction salarié (10 % des revenus professionnels nets,
  dans la limite de 8 PASS) : article 163 quatervicies du CGI.
- Plafond de déduction TNS/indépendant (10 % du bénéfice dans la limite
  de 8 PASS, + 15 % supplémentaires sur la fraction du bénéfice comprise
  entre 1 et 8 PASS) : article 154 bis du CGI.
- Fiscalité de sortie en capital (versements déduits : barème IR sans
  prélèvements sociaux ; versements non déduits : exonération totale ;
  gains : PFU à 31,4 % dans tous les cas, soit 12,8 % IR + 18,6 %
  prélèvements sociaux, taux 2026) : moneyvox.fr, mise à jour du
  27/05/2026, recoupé avec le taux TAUX_PFU déjà utilisé dans
  fiscalite.py pour les dividendes.

PRINCIPE :
Un versement volontaire sur un PER réduit le revenu imposable de
l'année (dans la limite d'un plafond), ce qui procure une économie
d'impôt immédiate au taux marginal d'imposition (TMI) actuel. En
contrepartie, à la sortie (en principe à la retraite), le capital
correspondant aux versements déduits est réintégré dans le revenu
imposable et taxé au barème IR - au TMI de CE moment-là, souvent plus
bas qu'en activité - tandis que les gains générés sont, eux, toujours
taxés au PFU. C'est le troisième levier d'arbitrage de la rémunération
du dirigeant, à côté du salaire et du dividende : plutôt que de
percevoir la totalité en net immédiat (et de la placer ensuite sur un
support classique), une partie peut être versée sur un PER pour
différer l'impôt pendant que le capital brut fructifie.

CE QUE CE MODULE NE FAIT PAS : il ne modélise pas la sortie en rente
viagère (seule la sortie en capital est traitée), ni le cas particulier
du PER d'entreprise (PERECO/PERO, abondement employeur, forfait social),
ni les cas de déblocage anticipé (achat de la résidence principale,
accidents de la vie), ni la mutualisation des plafonds au sein d'un
couple marié ou pacsé.
"""

from fiscalite import TAUX_PFU, PASS_2026

# --- Plafond de déduction des versements volontaires ---
TAUX_DEDUCTION_SALARIE = 0.10
TAUX_DEDUCTION_TNS_BASE = 0.10
TAUX_DEDUCTION_TNS_SUPPLEMENTAIRE = 0.15
NB_PASS_PLAFOND = 8


def plafond_deduction_salarie(revenu_net_professionnel, pass_value=PASS_2026):
    """
    Plafond de déduction pour un salarié ou assimilé salarié (président de
    SASU) : 10 % des revenus professionnels nets, avec un plancher garanti
    de 10 % d'un PASS (même sans revenu) et un plafond de 10 % de 8 PASS.
    Par simplification, utilise le PASS de l'année en cours plutôt que
    celui de l'année précédente (N-1), normalement applicable.
    """
    plancher = TAUX_DEDUCTION_SALARIE * pass_value
    plafond_max = TAUX_DEDUCTION_SALARIE * NB_PASS_PLAFOND * pass_value
    base = TAUX_DEDUCTION_SALARIE * max(0.0, revenu_net_professionnel)
    return min(max(base, plancher), plafond_max)


def plafond_deduction_tns(benefice, pass_value=PASS_2026):
    """
    Plafond de déduction pour un travailleur non salarié (gérant
    majoritaire de SARL, indépendant) : 10 % du bénéfice dans la limite de
    8 PASS, plus 15 % supplémentaires sur la fraction du bénéfice comprise
    entre 1 et 8 PASS - un plafond structurellement plus généreux que
    celui du salarié, avec le même plancher garanti de 10 % d'un PASS.
    """
    base_plafonnee = min(max(0.0, benefice), NB_PASS_PLAFOND * pass_value)
    part_10 = TAUX_DEDUCTION_TNS_BASE * base_plafonnee
    fraction_superieure = max(0.0, base_plafonnee - pass_value)
    part_15 = TAUX_DEDUCTION_TNS_SUPPLEMENTAIRE * fraction_superieure
    plancher = TAUX_DEDUCTION_TNS_BASE * pass_value
    return max(part_10 + part_15, plancher)


def montant_deductible(versement, plafond_disponible):
    """Part d'un versement effectivement déductible : le versement lui-même,
    plafonné au plafond de déduction disponible."""
    return min(max(0.0, versement), max(0.0, plafond_disponible))


def economie_impot_per(montant_deductible_calc, tmi_entree):
    """Économie d'impôt immédiate procurée par la déduction, à la TMI actuelle."""
    return montant_deductible_calc * tmi_entree


def fiscalite_sortie_capital(capital_verse, gains, deduit=True, tmi_sortie=0.0):
    """
    Fiscalité d'une sortie en capital (hors rente viagère) : la part
    correspondant aux versements est taxée au barème IR au TMI de la
    sortie si elle a été déduite à l'entrée (sans prélèvements sociaux),
    totalement exonérée sinon. Les gains générés par le contrat sont, eux,
    toujours taxés au PFU de 31,4 %, que les versements aient été déduits
    ou non.
    """
    impot_versements = capital_verse * tmi_sortie if deduit else 0.0
    impot_gains = gains * TAUX_PFU
    net = (capital_verse + gains) - impot_versements - impot_gains
    return {
        "impot_versements": impot_versements,
        "impot_gains": impot_gains,
        "net": net,
    }


def comparer_per(montant_brut, tmi_entree, tmi_sortie, rendement_annuel, duree_annees, deduit=True):
    """
    Compare, pour un même montant brut disponible avant impôt, deux
    trajectoires sur la durée de détention :
    - PER : le montant brut intégral est versé sur le PER (en franchise
      d'impôt immédiate si déduit), capitalise sans frottement fiscal
      annuel, et n'est taxé qu'à la sortie (versements au barème IR si
      déduits, gains au PFU). L'économie d'impôt immédiate est comptée à
      part, comme un gain disponible dès l'année du versement.
    - Sans PER : le montant brut est d'abord taxé au TMI actuel comme un
      revenu ordinaire (donc perçu net), puis ce montant net est placé sur
      un support classique qui capitalise au même rendement, dont les
      gains sont taxés au PFU à la sortie (simplification : pas de
      fiscalité annuelle intermédiaire, comme un contrat d'assurance-vie
      conservé plus de 8 ans).
    """
    # --- Scénario PER ---
    capital_final_per = montant_brut * (1 + rendement_annuel) ** duree_annees
    gains_per = capital_final_per - montant_brut
    sortie_per = fiscalite_sortie_capital(montant_brut, gains_per, deduit=deduit, tmi_sortie=tmi_sortie)
    economie_immediate = montant_brut * tmi_entree if deduit else 0.0
    net_per = sortie_per["net"] + economie_immediate

    # --- Scénario sans PER ---
    net_investi_sans_per = montant_brut * (1 - tmi_entree)
    capital_final_sans_per = net_investi_sans_per * (1 + rendement_annuel) ** duree_annees
    gains_sans_per = capital_final_sans_per - net_investi_sans_per
    impot_gains_sans_per = gains_sans_per * TAUX_PFU
    net_sans_per = capital_final_sans_per - impot_gains_sans_per

    return {
        "capital_final_per": capital_final_per,
        "gains_per": gains_per,
        "economie_immediate": economie_immediate,
        "net_per": net_per,
        "capital_final_sans_per": capital_final_sans_per,
        "gains_sans_per": gains_sans_per,
        "net_sans_per": net_sans_per,
        "ecart": net_per - net_sans_per,
    }


if __name__ == "__main__":
    print(f"Plafond salarié (revenu net 70 000 €)  : {plafond_deduction_salarie(70_000):,.0f} €")
    print(f"Plafond salarié (revenu net 400 000 €) : {plafond_deduction_salarie(400_000):,.0f} € (plafonné)")
    print(f"Plafond TNS (bénéfice 120 000 €)       : {plafond_deduction_tns(120_000):,.0f} €")
    print(f"Plafond TNS (bénéfice 400 000 €)       : {plafond_deduction_tns(400_000):,.0f} € (plafonné)")

    r = comparer_per(
        montant_brut=10_000, tmi_entree=0.41, tmi_sortie=0.11,
        rendement_annuel=0.04, duree_annees=20, deduit=True,
    )
    print(f"\nTMI 41% -> 11% à la sortie, 10 000 € bruts, 4%/an sur 20 ans :")
    print(f"  Net PER      : {r['net_per']:,.0f} €")
    print(f"  Net sans PER : {r['net_sans_per']:,.0f} €")
    print(f"  Écart        : {r['ecart']:,.0f} €")
