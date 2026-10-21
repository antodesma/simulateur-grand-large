"""
Module démembrement de propriété - Transmission en pleine propriété vs
donation de la nue-propriété (usufruit conservé par le donateur).
Grand Large Patrimoine - projet de stage

IMPORTANT : outil informatif uniquement, ne constitue pas un conseil
fiscal ou juridique personnalisé. Barèmes vérifiés en octobre 2026.

PRINCIPE :
Un parent qui transmet un bien peut soit le donner en pleine propriété
(l'enfant en a l'usage et la pleine valeur immédiatement, mais les droits
de donation portent sur la valeur totale), soit n'en donner que la
nue-propriété en conservant l'usufruit (l'enfant devient propriétaire
"en attente", les droits de donation ne portent que sur la valeur réduite
de la nue-propriété selon l'âge du donateur). Au décès du donateur,
l'usufruit s'éteint et l'enfant récupère la pleine propriété SANS droit
supplémentaire (article 1133 du CGI : "la réunion de l'usufruit à la
nue-propriété ne donne lieu à aucune perception de droits" - sous réserve
de l'article 1020 CGI pour certains immeubles, et à condition que l'usufruit
ne soit pas constitué pour la circonstance - réserve classique, cf. abus de
droit si démembrement artificiel).

CE QUE CE MODULE NE FAIT PAS : il ne choisit pas pour l'utilisateur, ne
prend pas en compte sa situation personnelle complète (autres donations
antérieures, démembrements croisés, pacte Dutreil, etc.), et ne remplace
pas un acte notarié.
"""

# --- Barème de l'article 669 du CGI (source : BOFiP) ---
# Chaque tuple (age_max, pourcentage_usufruit) : la tranche s'applique
# jusqu'à cet âge inclus.
BAREME_USUFRUIT_669 = [
    (20, 0.90),   # moins de 21 ans révolus
    (30, 0.80),   # 21 à 30 ans
    (40, 0.70),   # 31 à 40 ans
    (50, 0.60),   # 41 à 50 ans
    (60, 0.50),   # 51 à 60 ans
    (70, 0.40),   # 61 à 70 ans
    (80, 0.30),   # 71 à 80 ans
    (90, 0.20),   # 81 à 90 ans
    (float("inf"), 0.10),  # plus de 91 ans
]

# --- Droits de donation en ligne directe (parent -> enfant) ---
# Source : service-public.gouv.fr (barème identique donations/successions
# en ligne directe). Abattement renouvelable tous les 15 ans.
ABATTEMENT_DONATION_LIGNE_DIRECTE = 100_000

BAREME_DROITS_DONATION_LIGNE_DIRECTE = [
    (8_072, 0.05),
    (12_109, 0.10),
    (15_932, 0.15),
    (552_324, 0.20),
    (902_838, 0.30),
    (1_805_677, 0.40),
    (float("inf"), 0.45),
]


def pourcentage_usufruit(age):
    """Renvoie le pourcentage (valeur usufruit / valeur pleine propriété) selon l'âge."""
    for age_max, pct in BAREME_USUFRUIT_669:
        if age <= age_max:
            return pct
    return 0.10


def valeur_usufruit_nue_propriete(age, valeur_pleine_propriete):
    """
    Décompose la valeur d'un bien en valeur d'usufruit et valeur de
    nue-propriété, selon l'âge de l'usufruitier au moment de la donation.
    """
    pct_usufruit = pourcentage_usufruit(age)
    valeur_usufruit = valeur_pleine_propriete * pct_usufruit
    valeur_nue_propriete = valeur_pleine_propriete * (1 - pct_usufruit)
    return valeur_usufruit, valeur_nue_propriete


def calcul_droits_donation(valeur_transmise, abattement=ABATTEMENT_DONATION_LIGNE_DIRECTE):
    """
    Droits de donation en ligne directe, par tranches, après abattement.
    Même logique que l'IR : chaque tranche n'est taxée qu'une fois.
    """
    base_taxable = max(0, valeur_transmise - abattement)
    droits = 0.0
    borne_precedente = 0
    for borne, taux in BAREME_DROITS_DONATION_LIGNE_DIRECTE:
        tranche = max(0, min(base_taxable, borne) - borne_precedente)
        droits += tranche * taux
        if base_taxable <= borne:
            break
        borne_precedente = borne
    return droits


def calcul_droits_donation_famille(
    valeur_transmise,
    nombre_enfants=1,
    nombre_donateurs=1,
    abattement=ABATTEMENT_DONATION_LIGNE_DIRECTE,
):
    """
    Droits de donation en ligne directe pour une famille, en tenant compte
    du fait que l'abattement de l'article 779 du CGI s'applique PAR ENFANT
    ET PAR PARENT (et non une seule fois pour toute la transmission) :
    un enfant avec ses deux parents vivants peut recevoir jusqu'à
    200 000 € (2 x 100 000 €) en franchise de droits, et ce montant se
    multiplie par le nombre d'enfants si le bien leur est transmis à parts
    égales. On répartit donc la valeur transmise en autant de parts
    (enfants x donateurs) et on applique le barème progressif, abattement
    compris, à chaque part séparément - puis on additionne.
    Source : service-public.gouv.fr (art. 779 et 784 du CGI).
    """
    nombre_enfants = max(1, nombre_enfants)
    nombre_donateurs = max(1, nombre_donateurs)
    nombre_parts = nombre_enfants * nombre_donateurs
    valeur_par_part = valeur_transmise / nombre_parts
    droits_par_part = calcul_droits_donation(valeur_par_part, abattement)
    return droits_par_part * nombre_parts


def comparer_transmission(
    valeur_bien,
    age_donateur,
    nombre_enfants=1,
    nombre_donateurs=1,
    abattement=ABATTEMENT_DONATION_LIGNE_DIRECTE,
):
    """
    Compare les droits de donation entre une transmission en pleine
    propriété et une donation de la seule nue-propriété (usufruit
    conservé par le donateur jusqu'à son décès), pour une famille de
    nombre_enfants enfants, la donation étant faite par nombre_donateurs
    parent(s) (1 = un seul parent donateur, 2 = les deux parents donnent
    conjointement, chacun avec son propre abattement).
    """
    valeur_usufruit, valeur_nue_propriete = valeur_usufruit_nue_propriete(age_donateur, valeur_bien)
    droits_pleine_propriete = calcul_droits_donation_famille(
        valeur_bien, nombre_enfants, nombre_donateurs, abattement
    )
    droits_demembrement = calcul_droits_donation_famille(
        valeur_nue_propriete, nombre_enfants, nombre_donateurs, abattement
    )
    return {
        "valeur_bien": valeur_bien,
        "nombre_enfants": nombre_enfants,
        "nombre_donateurs": nombre_donateurs,
        "pourcentage_usufruit": pourcentage_usufruit(age_donateur),
        "valeur_usufruit": valeur_usufruit,
        "valeur_nue_propriete": valeur_nue_propriete,
        "droits_pleine_propriete": droits_pleine_propriete,
        "droits_demembrement": droits_demembrement,
        "economie_droits": droits_pleine_propriete - droits_demembrement,
    }


if __name__ == "__main__":
    resultat = comparer_transmission(valeur_bien=400_000, age_donateur=65, nombre_enfants=2, nombre_donateurs=2)
    print(f"Bien de {resultat['valeur_bien']:,.0f} €, donateur de 65 ans, {resultat['nombre_enfants']} enfant(s), {resultat['nombre_donateurs']} parent(s) donateur(s)")
    print(f"Part usufruit : {resultat['pourcentage_usufruit']:.0%} -> nue-propriété transmise : {resultat['valeur_nue_propriete']:,.0f} €")
    print(f"Droits si donation en pleine propriété : {resultat['droits_pleine_propriete']:,.0f} €")
    print(f"Droits si donation de la nue-propriété  : {resultat['droits_demembrement']:,.0f} €")
    print(f"Économie de droits                      : {resultat['economie_droits']:,.0f} €")
    print("Rappel : au décès du donateur, l'usufruit s'éteint et l'enfant")
    print("récupère la pleine propriété sans droit supplémentaire (art. 1133 CGI).")
