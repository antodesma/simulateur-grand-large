"""
Module paniers.py - Paniers de solutions Grand Large Patrimoine pour la
simulation Monte-Carlo de l'onglet "Trajectoire pluriannuelle".
Grand Large Patrimoine - projet de stage

POURQUOI CE MODULE :
Les profils "prudent / équilibré / dynamique" de simulation.py sont des
hypothèses abstraites, détachées de toute classe d'actifs réelle. Ce module
les remplace par des combinaisons des 4 grandes familles de solutions
réellement proposées par Grand Large Patrimoine (épargne sécurisée,
immobilier patrimonial, placements financiers, investissements non cotés),
pour que la simulation parle directement le métier de l'entreprise.

CE QUI EST SOURCÉ, CE QUI NE L'EST PAS :
- Le RENDEMENT MOYEN de chaque classe d'actifs est une donnée de marché
  publique et sourcée (voir CLASSES_ACTIFS ci-dessous - mêmes chiffres et
  mêmes sources que la "Note Grand Large", veille.py, pour ne jamais avoir
  deux versions différentes du même chiffre dans l'outil).
- La VOLATILITÉ de chaque classe est une hypothèse illustrative (comme déjà
  pour les anciens profils prudent/équilibré/dynamique) : aucune source ne
  publie une volatilité unique et incontestable par classe d'actifs
  patrimoniale, contrairement à un rendement moyen de marché.
- Les PANIERS (répartitions entre classes) sont des constructions
  pédagogiques illustratives, choisies pour cet outil - ILS NE REPRÉSENTENT
  PAS une grille d'allocation modèle réelle de Grand Large Patrimoine, qui
  reste propriétaire et confidentielle. Ne jamais présenter un panier comme
  "la" répartition recommandée par Grand Large Patrimoine.

La volatilité d'un panier est calculée comme une simple moyenne pondérée
des volatilités de chaque classe (pas un vrai calcul de variance de
portefeuille, qui demanderait une matrice de corrélations entre classes
que nous n'avons pas). C'est une approximation PRUDENTE : la volatilité
réelle d'un portefeuille diversifié est en général inférieure ou égale à
cette moyenne pondérée (effet amortisseur de la diversification, sauf
corrélation parfaite entre toutes les classes) - l'outil ne sous-estime
donc jamais le risque par cette simplification, au pire il le surestime
légèrement.
"""

from dataclasses import dataclass


@dataclass
class ClasseActif:
    libelle: str
    rendement_moyen: float
    volatilite: float
    source_rendement: str
    avertissement: str = ""  # mis en avant pour les classes à horizon de blocage / risque de perte en capital


# Mêmes chiffres, mêmes sources que veille.py (SECTION_IMMOBILIER,
# SECTION_NON_COTE, SECTION_EPARGNE) - à resynchroniser ensemble si l'un
# des deux fichiers est mis à jour avec une donnée plus récente.
CLASSES_ACTIFS = {
    "epargne_securisee": ClasseActif(
        libelle="Épargne sécurisée (fonds euros)",
        rendement_moyen=0.0260,
        volatilite=0.01,
        source_rendement="France Assureurs, rendement moyen des fonds euros, marché 2025",
    ),
    "immobilier_non_cote": ClasseActif(
        libelle="Immobilier patrimonial (SCPI)",
        rendement_moyen=0.0491,
        volatilite=0.04,
        source_rendement="ASPIM, taux de distribution moyen des SCPI (TDVM), marché 2025",
        avertissement=(
            "Moyenne de marché tous secteurs confondus - une SCPI précise peut s'écarter "
            "sensiblement de cette moyenne, à la hausse comme à la baisse."
        ),
    ),
    "marches_financiers": ClasseActif(
        libelle="Placements financiers (actions)",
        rendement_moyen=0.089,
        volatilite=0.16,
        source_rendement="France Invest / EY, TRI annualisé du CAC 40 sur 10 ans, étude parue le 8 juillet 2025",
    ),
    "investissements_non_cotes": ClasseActif(
        libelle="Investissements non cotés (private equity, dette privée)",
        rendement_moyen=0.113,
        volatilite=0.20,
        source_rendement="France Invest / EY, TRI net du capital-investissement français depuis l'origine, étude parue le 8 juillet 2025",
        avertissement=(
            "Horizon de blocage typique de 8 à 12 ans et risque de perte en capital - "
            "jamais à présenter sans rappeler ces deux points."
        ),
    ),
}

# Paniers illustratifs - construits pour cet outil à titre pédagogique.
# Ne reflètent PAS une allocation modèle réelle de Grand Large Patrimoine.
PANIERS = {
    "Prudent": {
        "epargne_securisee": 0.65,
        "immobilier_non_cote": 0.20,
        "marches_financiers": 0.12,
        "investissements_non_cotes": 0.03,
    },
    "Équilibré": {
        "epargne_securisee": 0.30,
        "immobilier_non_cote": 0.30,
        "marches_financiers": 0.25,
        "investissements_non_cotes": 0.15,
    },
    "Dynamique": {
        "epargne_securisee": 0.10,
        "immobilier_non_cote": 0.20,
        "marches_financiers": 0.40,
        "investissements_non_cotes": 0.30,
    },
}


def rendement_volatilite_panier(ponderations, rendements_override=None):
    """
    ponderations : dict {clé de CLASSES_ACTIFS : poids}, cense sommer à 1.0
    (tolérance de flottant gérée par l'appelant - voir normaliser_ponderations).
    rendements_override : dict optionnel {clé : rendement_moyen manuel}, pour
    le mode "sur mesure" de l'interface où l'utilisateur remplace le
    rendement sourcé d'une classe par sa propre hypothèse de travail. Les
    classes absentes de ce dict gardent leur rendement sourcé (CLASSES_ACTIFS).
    La volatilité n'est jamais remplaçable par cette voie : elle reste une
    hypothèse illustrative de l'outil, jamais une donnée de marché unique
    qu'un utilisateur pourrait légitimement "corriger".
    Renvoie {"rendement_moyen": ..., "volatilite": ...} - moyennes pondérées,
    voir le docstring du module pour la limite de l'approximation sur la
    volatilité.
    """
    rendements_override = rendements_override or {}
    rendement = sum(
        poids * rendements_override.get(cle, CLASSES_ACTIFS[cle].rendement_moyen)
        for cle, poids in ponderations.items()
    )
    volatilite = sum(poids * CLASSES_ACTIFS[cle].volatilite for cle, poids in ponderations.items())
    return {"rendement_moyen": rendement, "volatilite": volatilite}


def normaliser_ponderations(ponderations):
    """Remet une somme de poids à exactement 1.0 (les sliders de l'interface
    travaillent en pourcentages entiers, qui ne somment pas toujours
    exactement à 100 après arrondi) - sans normalisation, la simulation
    sous-pondérerait ou sur-pondérerait silencieusement le rendement total."""
    total = sum(ponderations.values())
    if total <= 0:
        raise ValueError("La somme des pondérations doit être strictement positive.")
    return {cle: poids / total for cle, poids in ponderations.items()}


if __name__ == "__main__":
    for nom_panier, ponderations in PANIERS.items():
        resultat = rendement_volatilite_panier(ponderations)
        print(
            f"Panier {nom_panier:12s} - rendement moyen {resultat['rendement_moyen']:.2%}, "
            f"volatilité {resultat['volatilite']:.2%}"
        )
