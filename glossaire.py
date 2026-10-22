"""
Module glossaire - définitions courtes des termes techniques utilisés
dans l'outil, pour un lecteur non-initié (le dirigeant lui-même, ou un
membre de sa famille). Chaque onglet n'affiche que les termes qui le
concernent, dans l'ordre où ils apparaissent dans ce module.
Grand Large Patrimoine - projet de stage
"""

GLOSSAIRE = {
    "PASS": (
        "Plafond annuel de la Sécurité sociale - un seuil de revenu fixé "
        "chaque année par l'État, utilisé comme référence pour calculer de "
        "nombreuses cotisations sociales (46 368 € en 2026)."
    ),
    "Assimilé salarié": (
        "Statut social du président de SASU : il cotise comme un salarié "
        "classique (charges patronales + salariales) et a les mêmes droits "
        "sociaux, sans toutefois cotiser à l'assurance chômage."
    ),
    "TNS": (
        "Travailleur non salarié - statut social du gérant majoritaire de "
        "SARL (et des indépendants en général). Il paie lui-même "
        "l'intégralité de ses cotisations sociales sur sa rémunération, "
        "sans distinction patronale/salariale. Cotisations globalement "
        "moins élevées que le régime assimilé salarié, en contrepartie de "
        "droits sociaux moindres (retraite notamment)."
    ),
    "Assiette": (
        "La base de calcul sur laquelle s'applique un taux de cotisation "
        "ou d'impôt - par exemple, l'assiette des cotisations TNS est en "
        "principe la rémunération professionnelle versée au gérant."
    ),
    "PFU": (
        "Prélèvement forfaitaire unique (la « flat tax ») - régime "
        "d'imposition par défaut des dividendes et de la plupart des "
        "revenus du capital, au taux global de 30 % (12,8 % d'impôt sur le "
        "revenu + 17,2 % de prélèvements sociaux)."
    ),
    "IS": (
        "Impôt sur les sociétés - impôt payé par l'entreprise sur son "
        "bénéfice, avant toute distribution au dirigeant (15 % jusqu'à "
        "42 500 € de bénéfice, 25 % au-delà, barème 2026)."
    ),
    "IR": (
        "Impôt sur le revenu - impôt payé par une personne physique (le "
        "dirigeant) sur ses revenus personnels, selon un barème progressif "
        "par tranches."
    ),
    "Abattement": (
        "Une réduction appliquée à un montant avant de calculer l'impôt ou "
        "les droits dus dessus - par exemple l'abattement forfaitaire de "
        "10 % pour frais professionnels sur un salaire, ou l'abattement de "
        "100 000 € par parent et par enfant sur une donation."
    ),
    "Démembrement de propriété": (
        "Séparation de la pleine propriété d'un bien en deux droits "
        "distincts : l'usufruit (l'usage du bien, ou les revenus qu'il "
        "génère) et la nue-propriété (le droit de devenir plein "
        "propriétaire à l'extinction de l'usufruit, en général au décès de "
        "l'usufruitier)."
    ),
    "Usufruit": (
        "Le droit d'utiliser un bien ou d'en percevoir les revenus (loyers, "
        "dividendes...), sans en être le propriétaire définitif. S'éteint "
        "en général au décès de l'usufruitier."
    ),
    "Nue-propriété": (
        "Le droit de devenir plein propriétaire d'un bien à l'extinction "
        "de l'usufruit qui le grève, sans droit supplémentaire à payer à ce "
        "moment-là (article 1133 du CGI)."
    ),
    "Holding": (
        "Société qui détient des parts d'une ou plusieurs autres sociétés "
        "(ici, l'entreprise opérationnelle du dirigeant), utilisée pour "
        "faire capitaliser des bénéfices sans les distribuer immédiatement "
        "au dirigeant - et donc sans frottement fiscal personnel annuel."
    ),
    "Monte-Carlo (simulation)": (
        "Méthode qui teste des centaines de trajectoires de rendement "
        "tirées au hasard autour d'une moyenne et d'une volatilité "
        "choisies, pour donner une fourchette de résultats plausibles "
        "plutôt qu'un chiffre unique présenté comme certain."
    ),
    "P10 / P50 / P90": (
        "Percentiles d'une simulation : P50 est la médiane (la moitié des "
        "trajectoires font mieux, l'autre moitié moins bien), P10 et P90 "
        "délimitent une fourchette où se trouvent 80 % des trajectoires "
        "simulées."
    ),
}


def termes_glossaire(cles):
    """Renvoie la liste (cle, definition) pour les clés demandées, dans
    l'ordre de GLOSSAIRE plutôt que dans l'ordre d'appel - évite une
    erreur silencieuse si une clé est mal orthographiée (elle est alors
    simplement absente du résultat)."""
    return [(cle, GLOSSAIRE[cle]) for cle in GLOSSAIRE if cle in cles]
