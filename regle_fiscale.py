"""
"Règle fiscale niche du jour" - module de la Note Grand Large.

Liste de mécanismes fiscaux et patrimoniaux stables, choisis parce qu'ils
sont souvent mal connus ou mal expliqués (contre-intuitifs, confondus avec
un autre dispositif), pas parce qu'ils changent souvent. Volontairement
différent des "Seuils réglementaires" de veille.py : ici, le mécanisme
compte plus que le chiffre, pour limiter le risque de péremption.

Aucun appel réseau, aucune donnée datée : une rotation déterministe (jour
de l'année) choisit l'entrée du jour, affichée uniquement à titre
pédagogique - jamais comme un conseil personnalisé.
"""

from dataclasses import dataclass
from datetime import date


@dataclass
class RegleFiscale:
    titre: str
    explication: str
    reference: str


REGLES = [
    RegleFiscale(
        titre="L'antériorité fiscale d'une assurance-vie se compte depuis l'ouverture du contrat, pas depuis chaque versement",
        explication=(
            "Un client pense parfois que verser de l'argent aujourd'hui sur un vieux contrat repart "
            "à zéro côté fiscalité. Faux : l'abattement après 8 ans s'apprécie à la date d'ouverture "
            "du contrat, quelle que soit la date des versements. D'où l'intérêt de garder un contrat "
            "ancien ouvert, même peu alimenté, plutôt que d'en ouvrir un nouveau."
        ),
        reference="Article 125-0 A du Code général des impôts",
    ),
    RegleFiscale(
        titre="La cession de la résidence principale est exonérée de plus-value, sans aucune condition de remploi",
        explication=(
            "Contrairement à d'autres régimes de faveur, l'exonération de la résidence principale ne "
            "demande ni durée de détention minimale, ni réinvestissement du prix de vente : c'est une "
            "exonération totale et automatique, dès lors que le logement est bien la résidence "
            "principale du vendeur au jour de la cession."
        ),
        reference="Article 150 U, II-1° du Code général des impôts",
    ),
    RegleFiscale(
        titre="Le régime du quotient permet de lisser l'impôt sur un revenu exceptionnel",
        explication=(
            "Une indemnité de départ, une plus-value professionnelle ou tout revenu \"exceptionnel\" "
            "par nature peut être imposé comme s'il était étalé sur plusieurs années, pour éviter de "
            "faire basculer tout le revenu de l'année dans la tranche marginale la plus haute. Un "
            "réflexe à vérifier systématiquement face à un revenu inhabituel."
        ),
        reference="Article 163-0 A du Code général des impôts",
    ),
    RegleFiscale(
        titre="Le quasi-usufruit permet à l'usufruitier de disposer librement du capital, contre une simple créance de restitution",
        explication=(
            "Sur une somme d'argent ou un compte-titres démembré, l'usufruitier peut consommer le "
            "capital (pas seulement les revenus), à charge pour lui - ou sa succession - de restituer "
            "l'équivalent aux nus-propriétaires au dénouement. Un outil de souplesse très utilisé en "
            "transmission, mais qui laisse une dette à la succession s'il n'est pas anticipé."
        ),
        reference="Article 587 du Code civil",
    ),
    RegleFiscale(
        titre="Le don familial de sommes d'argent est un abattement distinct, cumulable avec l'abattement classique de donation",
        explication=(
            "Au-delà de l'abattement habituel (parent-enfant ou grand-parent-petit-enfant), un don "
            "d'argent remis en pleine propriété ouvre droit à un abattement supplémentaire, sous "
            "conditions d'âge du donateur et de lien de parenté. Un dispositif souvent oublié parce "
            "qu'il est confondu avec l'abattement de droit commun, alors qu'il s'y ajoute."
        ),
        reference="Article 790 G du Code général des impôts",
    ),
    RegleFiscale(
        titre="Les titres d'une société peuvent être exclus de l'assiette de l'IFI s'ils sont qualifiés de « biens professionnels »",
        explication=(
            "Un dirigeant qui exerce une fonction de direction effective dans sa société et en tire "
            "l'essentiel de ses revenus professionnels peut voir ses titres sortir entièrement de "
            "l'assiette de l'impôt sur la fortune immobilière - à condition que la société exerce une "
            "activité industrielle, commerciale, artisanale, agricole ou libérale, et pas seulement "
            "une activité de gestion de patrimoine privé."
        ),
        reference="Article 975 du Code général des impôts",
    ),
    RegleFiscale(
        titre="Donner la seule nue-propriété d'une SCI réduit l'assiette taxable à la valeur de la nue-propriété, pas à celle du bien",
        explication=(
            "Transmettre des parts de SCI en démembrement suit la même logique que démembrer "
            "directement un bien : les droits de donation se calculent sur la seule valeur de la "
            "nue-propriété transmise (barème de l'article 669 du CGI), l'usufruitier conservant "
            "l'usage ou les revenus locatifs de son vivant."
        ),
        reference="Article 669 du Code général des impôts",
    ),
    RegleFiscale(
        titre="Une holding « animatrice » n'a pas le même traitement fiscal qu'une holding purement patrimoniale",
        explication=(
            "Les régimes de faveur attachés à l'outil professionnel (Pacte Dutreil, exonération IFI "
            "des biens professionnels) ne s'appliquent, pour une société holding, que si elle participe "
            "activement à la conduite de la politique de son groupe et au contrôle de ses filiales - "
            "pas si elle se contente de détenir des participations sans s'impliquer dans leur gestion."
        ),
        reference="Doctrine administrative BOFiP - notion de holding animatrice",
    ),
]


def regle_du_jour(aujourdhui=None):
    """Sélectionne une règle de façon déterministe selon le jour de l'année
    (pas d'état à sauvegarder, pas d'aléatoire : la même date donne toujours
    la même règle)."""
    aujourdhui = aujourdhui or date.today()
    index = aujourdhui.toordinal() % len(REGLES)
    regle = REGLES[index]
    return {"titre": regle.titre, "explication": regle.explication, "reference": regle.reference}
