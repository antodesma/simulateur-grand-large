"""
Module "Note Grand Large" - veille marchés et produits.
Grand Large Patrimoine - projet de stage

IMPORTANT : ce module ne fait AUCUN appel réseau automatique. Il fige un
instantané de données de marché et de seuils réglementaires, vérifiés
manuellement et sourcés, à une date donnée (DATE_MISE_A_JOUR). Il doit être
rafraîchi à la main avant chaque utilisation - voir la checklist à la fin
de ce fichier. Présenter une donnée de marché vieille de plusieurs semaines
comme "à jour" serait trompeur ; la date de mise à jour est donc affichée
bien en évidence partout où ces chiffres sont montrés.

Ce module n'émet aucune recommandation d'investissement : il rassemble des
indicateurs de marché publics et des seuils réglementaires, organisés
autour des 6 solutions affichées par Grand Large Patrimoine sur son site
(grandlargepatrimoine.fr), pour que la veille parle directement le langage
de leurs métiers plutôt que d'être un digest macro générique.
"""

from dataclasses import dataclass, field


DATE_MISE_A_JOUR = "21 octobre 2026"


@dataclass
class Indicateur:
    libelle: str
    valeur: str
    date_donnee: str
    source: str
    commentaire: str = ""
    lecture: str = ""  # "pourquoi ça compte" - l'usage concret en rendez-vous, jamais un conseil en investissement
    fiable: bool = True  # False si les sources divergent significativement


@dataclass
class SectionVeille:
    titre: str
    solution_glp: str  # la solution GLP correspondante, pour ancrer la veille à leur métier
    indicateurs: list = field(default_factory=list)
    note_methodo: str = ""


# --- 1. Marchés financiers & taux --------------------------------------
# Rattaché à "Placements financiers" (comptes-titres, mandats, produits
# structurés, PEA) : ces indicateurs conditionnent directement l'univers
# d'investissement de cette solution.
SECTION_MARCHES = SectionVeille(
    titre="Marchés financiers & taux",
    solution_glp="Placements financiers",
    indicateurs=[
        Indicateur(
            libelle="CAC 40",
            valeur="7 876,70 points (+0,49 % sur la séance)",
            date_donnee="21 octobre 2026",
            source="TradingEconomics (cotation CFD, à recouper avec une source officielle avant diffusion)",
            commentaire="Niveau proche des plus hauts historiques de l'indice.",
            lecture=(
                "Sert à répondre calmement à un client qui s'inquiète ou s'enthousiasme sur ses lignes "
                "actions ; la proximité des plus hauts n'est ni un signal d'achat ni un signal de vente en soi."
            ),
            fiable=False,
        ),
        Indicateur(
            libelle="OAT France 10 ans",
            valeur="≈ 4,9 % - 5,0 %",
            date_donnee="20 octobre 2026",
            source="TradingEconomics / presse financière - les sources divergent sur la 2e décimale",
            commentaire=(
                "En nette hausse par rapport au début d'année 2026 (environ 3,6 % en janvier). "
                "Pertinent pour la tarification des produits structurés et l'arbitrage fonds euros / obligataire direct."
            ),
            lecture=(
                "Utile pour expliquer pourquoi les nouveaux produits structurés affichent des taux garantis "
                "plus attractifs qu'il y a un an."
            ),
            fiable=False,
        ),
        Indicateur(
            libelle="Taux de dépôt BCE",
            valeur="2,50 %",
            date_donnee="décision du 10 septembre 2026, effective au 16 septembre 2026",
            source="Banque de France (Taux_directeurs.pdf) ; relayé par la presse spécialisée crédit",
            lecture="Point de repère pour toute discussion sur le coût du crédit (immobilier, avance sur titres) avec un client.",
        ),
        Indicateur(
            libelle="Fourchette cible Fed Funds (Réserve fédérale US)",
            valeur="3,75 % - 4,00 %",
            date_donnee="décision FOMC des 15-16 septembre 2026 (+25 pb)",
            source="Presse financière spécialisée (boursenews.ma), à recouper avec le communiqué officiel du FOMC",
            lecture="Pertinent pour un client exposé aux marchés américains ou au dollar dans son allocation.",
        ),
    ],
    note_methodo=(
        "Les niveaux de marché (actions, taux) bougent en continu : à rafraîchir le jour-même de toute "
        "utilisation face à un client ou à Pierre, jamais présenté au-delà de quelques jours sans revérification."
    ),
)

# --- 2. Immobilier patrimonial -------------------------------------------
SECTION_IMMOBILIER = SectionVeille(
    titre="Immobilier patrimonial",
    solution_glp="Immobilier patrimonial",
    indicateurs=[
        Indicateur(
            libelle="Taux de distribution moyen des SCPI (TDVM), marché 2025",
            valeur="4,91 %",
            date_donnee="données annuelles 2025",
            source="ASPIM (Association française des Sociétés de Placement Immobilier)",
            commentaire=(
                "Moyenne de marché, tous secteurs confondus (bureaux, commerces, santé, logistique). "
                "Les SCPI gérées par les sociétés citées par Grand Large Patrimoine (Sofidy, La Française REM, "
                "Primonial REIM, Perial AM, Amundi Immobilier, Norma Capital) peuvent s'écarter sensiblement "
                "de cette moyenne, à la hausse comme à la baisse : ce chiffre sert de repère de marché, pas "
                "de performance d'un véhicule en particulier."
            ),
            lecture=(
                "Permet de resituer la performance d'une SCPI proposée face à la moyenne du marché, "
                "sans se prononcer sur un véhicule en particulier."
            ),
        ),
    ],
    note_methodo=(
        "Le TDVM 2025 est une donnée annuelle publiée en début d'année suivante : fiable jusqu'à la "
        "publication des chiffres 2026 (attendue vers février-mars 2027)."
    ),
)

# --- 3. Investissements non cotés ---------------------------------------
SECTION_NON_COTE = SectionVeille(
    titre="Investissements non cotés",
    solution_glp="Investissements non cotés",
    indicateurs=[
        Indicateur(
            libelle="TRI net du capital-investissement français depuis l'origine",
            valeur="11,3 % par an",
            date_donnee="étude parue le 8 juillet 2025",
            source="France Invest / EY, étude annuelle de performance nette",
            lecture=(
                "Point de comparaison utile pour expliquer la logique de diversification vers le non coté, "
                "en rappelant systématiquement l'horizon de blocage (8-12 ans) et le risque de perte en capital."
            ),
        ),
        Indicateur(
            libelle="TRI net du capital-investissement français sur 10 ans",
            valeur="entre 12,4 % et 12,7 % selon les tableaux de l'étude (incohérence interne au document)",
            date_donnee="étude parue le 8 juillet 2025",
            source="France Invest / EY",
            commentaire=(
                "À comparer, dans la même étude, au CAC 40 (8,9 % sur 10 ans) et au CAC All Tradable "
                "(8,3 % sur 10 ans) : l'écart illustre la prime d'illiquidité mise en avant par la classe "
                "d'actifs, mais ne doit jamais être présenté sans rappeler l'horizon de blocage (8-12 ans) "
                "et le risque de perte en capital."
            ),
            lecture="Chiffre à manier avec précaution (incohérence interne à l'étude) ; illustre un écart de marché, pas une promesse de performance.",
            fiable=False,
        ),
    ],
    note_methodo=(
        "Étude annuelle (millésime 2025, publiée juillet 2025) : prochaine édition attendue mi-2026, "
        "à vérifier avant toute réutilisation après cette date."
    ),
)

# --- 4. Épargne réglementée / assurance-vie ------------------------------
SECTION_EPARGNE = SectionVeille(
    titre="Assurance-vie & épargne",
    solution_glp="Placements financiers",
    indicateurs=[
        Indicateur(
            libelle="Rendement moyen des fonds euros, marché 2025",
            valeur="2,60 % (France Assureurs) / 2,63 % (ACPR)",
            date_donnee="données annuelles 2025, publiées en 2026",
            source="France Assureurs ; ACPR",
            commentaire=(
                "Rendement moyen de marché, avant prélèvements sociaux et fiscalité. Les contrats distribués "
                "par Grand Large Patrimoine (Spirica, Generali Patrimoine, Cardif, Oradea pour le droit "
                "français ; Lombard International, OneLife, Wealins, Baloise Lux au Luxembourg) peuvent "
                "verser des rendements différents de cette moyenne."
            ),
            lecture="Point de départ pour toute conversation sur la part d'un contrat à garder en fonds euros plutôt qu'en unités de compte.",
        ),
    ],
    note_methodo="Donnée annuelle, stable jusqu'à la publication des chiffres 2026 (début 2027).",
)

# --- 5. Fiscalité & seuils réglementaires du dirigeant / transmission ----
# Pas des "marchés" au sens strict, mais tout aussi volatile pour un family
# office : plafonds, barèmes et dates-limites qui changent chaque année ou
# au gré des lois de finances. Repris ici depuis fiscalite.py/demembrement.py
# (déjà vérifiés et testés dans l'outil) pour que la note de veille serve
# aussi de pense-bête réglementaire, sans dupliquer une deuxième source de
# vérité : les seuils ci-dessous DOIVENT rester synchronisés avec les
# constantes des modules de simulation.
SECTION_FISCALITE = SectionVeille(
    titre="Seuils réglementaires - dirigeant, transmission",
    solution_glp="Ingénierie fiscale et sociale du dirigeant / Transmission et structuration familiale",
    indicateurs=[
        Indicateur(
            libelle="PASS (plafond annuel de la sécurité sociale) 2026",
            valeur="48 060 € / an (4 005 € / mois)",
            date_donnee="exercice 2026",
            source="Sécurité sociale - arrêté annuel (repris dans fiscalite.py : PASS_2026)",
            lecture="Sert à recalculer rapidement un plafond de cotisation ou un seuil social pendant un rendez-vous.",
        ),
        Indicateur(
            libelle="Abattement forfaitaire 10 % frais professionnels",
            valeur="plancher 509 € - plafond 14 555 €",
            date_donnee="revenus 2025, déclaration 2026",
            source="Code général des impôts (repris dans fiscalite.py)",
            lecture="Rarement déterminant seul, mais utile pour vérifier une déclaration de revenus d'un dirigeant assimilé salarié.",
        ),
        Indicateur(
            libelle="Exonération régime mère-fille (remontée de dividendes en holding)",
            valeur="95 % (quote-part de frais et charges de 5 % réintégrée)",
            date_donnee="en vigueur",
            source="Code général des impôts - cité sur la page GLP \"Ingénierie fiscale et sociale du dirigeant\"",
            lecture="Argument clé pour expliquer l'intérêt d'une holding qui perçoit les dividendes de la société opérationnelle.",
        ),
        Indicateur(
            libelle="Pacte Dutreil - abattement transmission d'entreprise",
            valeur="75 % de la valeur transmise, sous engagement collectif puis individuel de conservation",
            date_donnee="en vigueur",
            source="Code général des impôts - cité sur la page GLP \"Transmission et structuration familiale\"",
            lecture="À mentionner dès qu'un client évoque la transmission de son entreprise à ses enfants.",
        ),
        Indicateur(
            libelle="Apport-cession (article 150-0 B ter du CGI)",
            valeur="report d'imposition de la plus-value sous condition de réinvestissement de 60 % dans une activité économique sous 24 mois",
            date_donnee="en vigueur",
            source="Code général des impôts - cité sur la page GLP \"Ingénierie fiscale et sociale du dirigeant\"",
            lecture="Utile quand un client envisage de céder des titres après les avoir apportés à une holding.",
        ),
        Indicateur(
            libelle="Abattement donation en ligne directe (parent → enfant)",
            valeur="100 000 € par parent et par enfant, renouvelable tous les 15 ans",
            date_donnee="en vigueur",
            source="Code général des impôts (repris dans demembrement.py : ABATTEMENT_DONATION_LIGNE_DIRECTE)",
            lecture="Le chiffre le plus souvent cité en premier rendez-vous transmission.",
        ),
        Indicateur(
            libelle="Abattement donation grand-parent → petit-enfant",
            valeur="31 865 €, renouvelable tous les 15 ans",
            date_donnee="en vigueur",
            source="Code général des impôts - cité sur la page GLP \"Transmission et structuration familiale\"",
            lecture="À mentionner quand un client veut aussi transmettre à ses petits-enfants, en plus de ses enfants.",
        ),
    ],
    note_methodo=(
        "Ces seuils changent typiquement une fois par an (loi de finances, votée en décembre). "
        "Point de vigilance : revérifier systématiquement à chaque nouvelle loi de finances, et à chaque "
        "fois que fiscalite.py ou demembrement.py sont mis à jour, pour que cette note reste synchronisée "
        "avec l'outil de simulation."
    ),
)

# --- 6. Univers de partenaires cité par Grand Large Patrimoine -----------
# Pas des indicateurs chiffrés : une liste de référence des acteurs
# nommément cités sur grandlargepatrimoine.fr (architecture ouverte, donc
# aucun produit maison), pour qu'Antonin puisse resituer immédiatement un
# nom entendu en réunion dans la bonne case métier.
UNIVERS_PARTENAIRES = {
    "Assurance-vie française": ["Spirica", "Generali Patrimoine", "Cardif", "Oradea"],
    "Assurance-vie luxembourgeoise (dès 250 k€)": ["Lombard International", "OneLife", "Wealins", "Baloise Lux"],
    "Mandats de gestion": [
        "Carmignac", "Edmond de Rothschild AM", "Rothschild & Co AM",
        "Lazard Frères Gestion", "La Financière de l'Échiquier",
    ],
    "Émetteurs de produits structurés": ["BNP Paribas", "Société Générale", "Natixis", "Goldman Sachs"],
    "SCPI / OPCI": ["Sofidy", "La Française REM", "Primonial REIM", "Perial AM", "Amundi Immobilier", "Norma Capital"],
    "Private equity": [
        "Eurazeo", "Ardian", "PAI Partners", "Tikehau Capital",
        "Andera Partners", "Five Arrows (Rothschild & Co)", "Bridgepoint",
    ],
    "Dette privée": ["Tikehau", "ICG", "Pemberton", "Ares", "Apollo"],
    "Infrastructures": ["Ardian Infrastructure", "Meridiam", "Antin Infrastructure Partners", "EQT Infrastructure"],
}

TOUTES_SECTIONS = [
    SECTION_MARCHES,
    SECTION_IMMOBILIER,
    SECTION_NON_COTE,
    SECTION_EPARGNE,
    SECTION_FISCALITE,
]


# --- Checklist de rafraîchissement --------------------------------------
# À suivre AVANT toute utilisation de cette note devant un client ou Pierre.
CHECKLIST_RAFRAICHISSEMENT = [
    "CAC 40 et taux (OAT, BCE, Fed) : revérifier le jour-même (source officielle : Banque de France, BCE, Fed).",
    "Fonds euros et SCPI (TDVM) : données annuelles - revérifier qu'aucune publication plus récente "
    "(France Assureurs, ACPR, ASPIM) n'est sortie entre-temps.",
    "Performance capital-investissement (France Invest/EY) : revérifier qu'aucune étude plus récente n'a été publiée.",
    "Seuils fiscaux (PASS, abattements, Dutreil, 150-0 B ter) : revérifier après chaque loi de finances "
    "(votée en général en décembre) et resynchroniser avec fiscalite.py / demembrement.py si un seuil change.",
    "Ne jamais présenter un chiffre marqué fiable=False sans le recouper avec une source officielle d'abord.",
    "Mettre à jour DATE_MISE_A_JOUR dans ce fichier à chaque rafraîchissement.",
]


if __name__ == "__main__":
    print(f"Note Grand Large - instantané du {DATE_MISE_A_JOUR}\n")
    for section in TOUTES_SECTIONS:
        print(f"== {section.titre} ({section.solution_glp}) ==")
        for ind in section.indicateurs:
            drapeau = " [À RECOUPER]" if not ind.fiable else ""
            print(f"- {ind.libelle} : {ind.valeur}{drapeau}")
            print(f"  source : {ind.source} ({ind.date_donnee})")
        print()
