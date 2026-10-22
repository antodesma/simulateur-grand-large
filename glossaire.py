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
    "Pacte Dutreil": (
        "Dispositif (article 787 B du CGI) qui exonère 75 % de la valeur d'une entreprise transmise "
        "par donation ou succession, sous conditions de conservation des titres (engagement collectif "
        "puis individuel) et d'exercice d'une fonction de direction - seul le quart restant est soumis "
        "aux droits de donation classiques."
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
    "Rachat (assurance-vie)": (
        "Retrait (partiel ou total) effectué par le souscripteur de son "
        "vivant sur un contrat d'assurance-vie. Seule la part de gains "
        "(intérêts, plus-values) comprise dans le rachat est taxée - le "
        "capital initialement versé ne l'est jamais."
    ),
    "PFU (assurance-vie)": (
        "Régime d'imposition des gains rachetés sur un contrat "
        "d'assurance-vie (versements à partir du 27/09/2017) : 12,8 % "
        "avant 8 ans, ou 7,5 % après 8 ans dans la limite de 150 000 € de "
        "versements cumulés - dans les deux cas, 17,2 % de prélèvements "
        "sociaux s'ajoutent toujours, sans abattement."
    ),
    "Article 990 I du CGI": (
        "Régime de taxation au décès des sommes transmises par "
        "assurance-vie issues de versements effectués AVANT les 70 ans du "
        "souscripteur : abattement de 152 500 € par bénéficiaire, puis "
        "20 % jusqu'à 700 000 €, 31,25 % au-delà."
    ),
    "Article 757 B du CGI": (
        "Régime de taxation au décès des sommes transmises par "
        "assurance-vie issues de versements effectués APRÈS les 70 ans du "
        "souscripteur : seules les primes versées sont taxables (les "
        "gains sont exonérés), après un abattement de 30 500 € partagé "
        "entre tous les bénéficiaires, puis taxation au barème des droits "
        "de succession classique."
    ),
    "Lien de parenté (succession)": (
        "Ce qui détermine en premier lieu le montant des droits de "
        "succession : conjoint et partenaire pacsé sont totalement "
        "exonérés, un enfant bénéficie du barème le plus favorable après "
        "les 100 000 € d'abattement, les liens plus éloignés (frère/sœur, "
        "neveu/nièce, tiers) subissent un abattement réduit et un taux "
        "souvent fixe et élevé."
    ),
    "Article 796-0 bis du CGI": (
        "Exonération totale des droits de succession pour le conjoint "
        "survivant et le partenaire de PACS, quel que soit le montant "
        "hérité - instaurée par la loi TEPA de 2007."
    ),
    "IFI": (
        "Impôt sur la fortune immobilière - remplace l'ISF depuis 2018. "
        "Ne porte plus que sur le patrimoine immobilier (hors biens "
        "professionnels), dû dès que ce patrimoine net taxable dépasse "
        "1 300 000 € au 1er janvier."
    ),
    "Décote (IFI)": (
        "Mécanisme qui lisse l'entrée dans l'IFI pour un patrimoine net "
        "taxable compris entre 1 300 000 € et 1 400 000 € - sans elle, "
        "franchir le seuil de quelques euros ferait basculer "
        "immédiatement dans tout le barème progressif."
    ),
    "Biens professionnels (IFI)": (
        "Biens exclus de l'assiette de l'IFI lorsqu'ils sont affectés à "
        "l'activité professionnelle principale du dirigeant (ex. une "
        "holding animatrice de son groupe) - sous conditions précises, "
        "souvent source de contentieux avec l'administration fiscale."
    ),
}


def termes_glossaire(cles):
    """Renvoie la liste (cle, definition) pour les clés demandées, dans
    l'ordre de GLOSSAIRE plutôt que dans l'ordre d'appel - évite une
    erreur silencieuse si une clé est mal orthographiée (elle est alors
    simplement absente du résultat)."""
    return [(cle, GLOSSAIRE[cle]) for cle in GLOSSAIRE if cle in cles]
