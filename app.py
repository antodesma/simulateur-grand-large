"""
Interface Streamlit - Simulateur rémunération dirigeant / holding
Grand Large Patrimoine - projet de stage

Rassemble les modules fiscalite.py, trajectoire.py et simulation.py dans
une interface cliquable. Outil informatif uniquement - voir le bandeau de
non-responsabilité en haut de page.
"""

import os

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Export PNG des graphiques (synthèse PDF) : kaleido a besoin d'un Chrome.
# Sur l'environnement de développement Claude, un Chromium est déjà
# installé à ce chemin précis mais jamais détecté automatiquement par
# kaleido - on ne force BROWSER_PATH que si ce chemin existe vraiment, pour
# ne jamais interférer avec le Chrome que kaleido trouve normalement sur la
# machine d'Antonin (ou n'importe quelle autre machine de déploiement).
_CHROMIUM_SANDBOX_DEV = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
if "BROWSER_PATH" not in os.environ and os.path.exists(_CHROMIUM_SANDBOX_DEV):
    os.environ["BROWSER_PATH"] = _CHROMIUM_SANDBOX_DEV

from fiscalite import (
    applique_abattement_salaire,
    brut_depuis_cout_total,
    calcul_ir,
    calcul_is,
    charges_sur_brut,
    net_apres_dividende,
    net_apres_salaire,
    TAUX_PFU,
)
from simulation import simulation_comparaison
from assurance_vie import (
    net_apres_rachat,
    prelevement_990_i,
    taxation_transmission,
    ABATTEMENT_757_B_GLOBAL,
    ABATTEMENT_990_I_PAR_BENEFICIAIRE,
    SEUIL_VERSEMENTS_TAUX_REDUIT,
)
from paniers import CLASSES_ACTIFS, PANIERS, rendement_volatilite_panier
from trajectoire import comparer
from demembrement import comparer_transmission, pourcentage_usufruit
from succession import ABATTEMENT_TIERS, comparer_liens_parente
from ifi import ABATTEMENT_RESIDENCE_PRINCIPALE, BAREME_IFI, SEUIL_ASSUJETTISSEMENT_IFI, synthese_ifi
from sci import comparer_sci
from per import comparer_per, economie_impot_per, montant_deductible, plafond_deduction_salarie, plafond_deduction_tns
from pacte_dutreil import (
    calcul_transmission_dutreil,
    CONDITIONS_PACTE_DUTREIL,
    DUREE_ENGAGEMENT_COLLECTIF_ANNEES,
    DUREE_ENGAGEMENT_INDIVIDUEL_ANNEES,
    DUREE_FONCTION_DIRECTION_APRES_TRANSMISSION_ANNEES,
    SEUILS_ENGAGEMENT_COLLECTIF,
    TAUX_EXONERATION_DUTREIL,
)
from fiscalite_tns import (
    TAUX_IR_SEUL_PFU,
    cotisations_tns,
    net_apres_dividende_tns,
    net_apres_remuneration_tns,
    seuil_dividendes_sans_cotisations,
)
from export_pdf import generer_pdf_scenario
from glossaire import termes_glossaire
from optimisation import analyse_sensibilite, repartition_optimale
from regle_fiscale import regle_du_jour
from veille import (
    CHECKLIST_RAFRAICHISSEMENT,
    DATE_MISE_A_JOUR,
    TOUTES_SECTIONS,
    UNIVERS_PARTENAIRES,
)

# --- Charte Grand Large Patrimoine (relevée sur grandlargepatrimoine.fr) ---
# --glp-brand: #03001C · --glp-brand-hover: #0a0633 · --glp-white: #FFFFFF
# Titres en "Libre Caslon Display" (serif), corps en sans-serif système.
# Site volontairement monochrome (navy + blanc) - les couleurs de données
# ci-dessous restent la palette validée accessibilité (skill dataviz),
# utilisée seulement pour distinguer des séries dans les graphiques.
NAVY = "#03001C"
NAVY_HOVER = "#0a0633"
CREME = "#f7f5ef"

# Palette catégorielle resserrée - moins saturée que les couleurs "défaut
# de librairie de graphiques" d'origine (bleu/orange vifs type Bootstrap),
# plus proche d'un nuancier de gestion de patrimoine (encre, bronze, pétrole,
# or bruni). Revalidée avec le script du skill dataviz (bande de clarté,
# plancher de chroma, séparation daltonisme, contraste sur fond clair) :
# tout passe, y compris le contraste de l'or bruni qui échouait avant d'être
# assombri d'un cran.
COULEUR_SALAIRE = "#2e5c94"        # slot catégoriel 1 - bleu encre
COULEUR_DIVIDENDE = "#b5672e"      # slot catégoriel 2 - bronze
COULEUR_DEMEMBREMENT = "#1b8f6f"   # slot catégoriel 3 - pétrole
COULEUR_JAUNE = "#ad7d1f"          # slot catégoriel 4 - or bruni
COULEUR_MAGENTA = "#c15f82"        # slot catégoriel 5 - vieux rose
# Une couleur par section de la Note Grand Large (même ordre que
# TOUTES_SECTIONS), pour que chaque solution GLP garde la même identité
# visuelle partout dans l'onglet - jamais recyclée, jamais au hasard.
COULEURS_SECTIONS_VEILLE = [COULEUR_SALAIRE, COULEUR_DIVIDENDE, COULEUR_DEMEMBREMENT, COULEUR_JAUNE, COULEUR_MAGENTA]
# Une couleur fixe par classe d'actifs des paniers de solutions - même ordre
# catégoriel que ci-dessus, jamais recyclé en fonction du panier affiché,
# pour que "Immobilier" soit toujours le même bronze d'un panier à l'autre.
COULEURS_CLASSES_ACTIFS = {
    "epargne_securisee": COULEUR_SALAIRE,
    "immobilier_non_cote": COULEUR_DIVIDENDE,
    "marches_financiers": COULEUR_DEMEMBREMENT,
    "investissements_non_cotes": COULEUR_JAUNE,
}
LIBELLES_COURTS_CLASSES_ACTIFS = {
    "epargne_securisee": "Épargne sécurisée",
    "immobilier_non_cote": "Immobilier",
    "marches_financiers": "Actions",
    "investissements_non_cotes": "Non coté",
}
COULEUR_ALERTE = "#fab219"  # accent uniquement (texte en noir dessus pour le contraste) - cf. skill dataviz
ENCRE_PRIMAIRE = NAVY
ENCRE_SECONDAIRE = "#4a4860"
ENCRE_MUTED = "#8b899c"
GRILLE = "#e7e5dd"
SURFACE = "#fcfcfb"
SURFACE_CARTE = "#ffffff"
BORDURE = "rgba(3,0,28,0.10)"

st.set_page_config(page_title="Grand Large · Simulateur patrimonial", layout="wide", page_icon="⛵")

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Libre+Caslon+Display&family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, "Segoe UI", system-ui, sans-serif;
        color: {ENCRE_PRIMAIRE};
    }}

    /* Masque le chrome générique Streamlit (menu, badge Deploy, footer) */
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    [data-testid="stToolbar"] {{ visibility: hidden; }}
    [data-testid="stDecoration"] {{ display: none; }}
    /* La barre d'en-tête Streamlit (au-dessus du bandeau et de la sidebar) ne
       sert ici qu'à replier la barre latérale : on la rend transparente et
       fine plutôt que de laisser une bande vide visible. */
    [data-testid="stHeader"] {{
        background: transparent;
        box-shadow: none;
        height: 2.75rem;
    }}

    .block-container {{ padding-top: 2rem; max-width: 1150px; }}

    .stApp {{ background: #ffffff; }}

    .bandeau {{
        background: linear-gradient(120deg, {NAVY} 0%, {NAVY_HOVER} 100%);
        border-radius: 0;
        padding: 2.1rem 2.1rem 1.9rem;
        margin-bottom: 1.6rem;
        color: #ffffff;
        border-bottom: 2px solid rgba(255,255,255,0.15);
        position: relative;
        overflow: hidden;
    }}
    .bandeau .motif-voile {{
        position: absolute;
        top: -18px;
        right: 28px;
        opacity: 0.14;
        pointer-events: none;
    }}
    .bandeau .label {{
        text-transform: uppercase;
        letter-spacing: 0.14em;
        font-size: 0.68rem;
        color: rgba(255,255,255,0.55);
        font-weight: 500;
        margin-bottom: 0.5rem;
    }}
    .bandeau h1 {{
        font-family: 'Libre Caslon Display', serif;
        font-size: 2.1rem;
        font-weight: 400;
        margin: 0 0 0.5rem 0;
        color: #ffffff;
        letter-spacing: 0.01em;
    }}
    .bandeau p {{
        margin: 0;
        color: rgba(255,255,255,0.75);
        font-size: 0.93rem;
        line-height: 1.5;
        max-width: 640px;
    }}

    .bloc-disclaimer {{
        background: #ffffff;
        border: 1px solid {BORDURE};
        border-left: 3px solid {NAVY};
        border-radius: 0;
        padding: 0.85rem 1.1rem;
        color: {ENCRE_SECONDAIRE};
        font-size: 0.88rem;
        margin-bottom: 1.3rem;
    }}

    .entete-section {{
        margin: 0.2rem 0 1.4rem 0;
    }}
    .entete-section .titre {{
        font-family: 'Libre Caslon Display', serif;
        font-weight: 400;
        font-size: 1.55rem;
        color: {NAVY};
        margin: 0 0 0.15rem 0;
        line-height: 1.2;
    }}
    .entete-section .sous-titre {{
        font-family: 'Libre Caslon Display', serif;
        font-weight: 400;
        font-size: 0.98rem;
        color: {ENCRE_MUTED};
        margin: 0;
        font-style: italic;
    }}

    /* Titre de sous-section (ex. "Panier de solutions", "Composition du
       panier") : plus visible qu'un st.caption gris de la taille du texte
       courant, mais plus discret que le gros titre de l'onglet. */
    .titre-sous-section {{
        font-family: 'Libre Caslon Display', serif;
        font-weight: 400;
        font-size: 1.2rem;
        color: {NAVY};
        margin: 1.1rem 0 0.3rem 0;
        line-height: 1.25;
    }}

    .filet {{
        border: none;
        border-top: 1px solid {BORDURE};
        margin: 1.1rem 0;
    }}

    .etape-numerotee {{
        display: flex;
        align-items: baseline;
        gap: 0.9rem;
        padding: 0.75rem 0;
        border-bottom: 1px solid {BORDURE};
    }}
    .etape-numerotee:last-child {{ border-bottom: none; }}
    .etape-numerotee .numero {{
        font-family: 'Libre Caslon Display', serif;
        color: {NAVY};
        font-size: 0.95rem;
        font-weight: 400;
        min-width: 1.6rem;
    }}
    .etape-numerotee .texte {{
        color: {ENCRE_SECONDAIRE};
        font-size: 0.88rem;
        line-height: 1.5;
    }}

    .tuile {{
        background: #ffffff;
        border: 1px solid {BORDURE};
        border-radius: 0;
        padding: 1rem 1.2rem;
        height: 100%;
    }}
    .tuile .tuile-titre {{
        font-weight: 600;
        font-size: 0.86rem;
        color: {NAVY};
        margin-bottom: 0.4rem;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }}

    .carte-kpi {{
        background: #ffffff;
        border: 1px solid {BORDURE};
        border-radius: 0;
        padding: 1.1rem 1.3rem;
        height: 100%;
        transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
    }}
    .carte-kpi:hover {{
        transform: translateY(-3px);
        box-shadow: 0 10px 24px rgba(3,0,28,0.09);
        border-color: {NAVY};
    }}
    .carte-kpi .accent {{
        display: inline-block;
        width: 28px; height: 3px;
        margin-bottom: 0.6rem;
    }}
    .carte-kpi .label {{
        color: {ENCRE_MUTED};
        font-size: 0.8rem;
        margin-bottom: 0.2rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }}
    .carte-kpi .valeur {{
        font-family: 'Libre Caslon Display', serif;
        color: {ENCRE_PRIMAIRE};
        font-size: 1.85rem;
        font-weight: 400;
        font-variant-numeric: tabular-nums;
    }}
    .carte-kpi .sous-texte {{
        color: {ENCRE_SECONDAIRE};
        font-size: 0.85rem;
        line-height: 1.4;
        margin-top: 0.4rem;
    }}

    [data-testid="stMetricValue"] {{ font-variant-numeric: tabular-nums; }}

    h2, h3 {{ color: {ENCRE_PRIMAIRE}; font-family: 'Libre Caslon Display', serif; font-weight: 400; }}

    /* Streamlit a changé le balisage de ses onglets (data-testid="stTab",
       plus l'ancien data-baseweb="tab" que ciblaient ces règles) - le style
       ci-dessous ne s'appliquait donc à aucun onglet inactif, seul
       [aria-selected="true"] matchait par coïncidence. D'où des onglets
       inactifs quasi invisibles, repérés sur une capture d'écran réelle. */
    [role="tablist"] {{
        gap: 10px;
        border-bottom: none;
    }}
    [data-testid="stTab"] {{
        font-weight: 600 !important;
        font-size: 1rem !important;
        padding: 10px 20px !important;
        height: auto !important;
        background: {CREME} !important;
        border: 1.5px solid rgba(3,0,28,0.35) !important;
        border-radius: 0 !important;
        color: {ENCRE_SECONDAIRE} !important;
        box-shadow: none !important;
        cursor: pointer;
        transition: background-color 0.15s ease, color 0.15s ease, border-color 0.15s ease;
    }}
    [data-testid="stTab"] p {{ color: inherit !important; }}
    [data-testid="stTab"]:hover {{
        background: #ffffff !important;
        border-color: {NAVY} !important;
        color: {NAVY} !important;
    }}
    [data-testid="stTab"][aria-selected="true"] {{
        background: {NAVY} !important;
        border-color: {NAVY} !important;
        color: #ffffff !important;
    }}

    /* Deux poids plutôt qu'un seul : le CSV est une donnée brute
       (secondaire, contour), le PDF est le livrable fini qu'on montre
       réellement à un client (primaire, plein) - une vraie hiérarchie
       entre les deux actions, pas juste une couleur appliquée partout. */
    .stButton button, .stDownloadButton button {{
        border-radius: 0;
        border: 1.5px solid {NAVY};
        background-color: #ffffff;
        color: {NAVY};
        font-weight: 600;
        letter-spacing: 0.01em;
        padding: 0.5rem 1.15rem;
        transition: background-color 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
    }}
    .stButton button:hover, .stDownloadButton button:hover {{
        background-color: {CREME};
        border-color: {NAVY};
        color: {NAVY};
        transform: translateY(-1px);
    }}
    .stButton button[kind="primary"], .stDownloadButton button[kind="primary"] {{
        background-color: {NAVY};
        border-color: {NAVY};
        color: #ffffff;
    }}
    .stButton button[kind="primary"]:hover, .stDownloadButton button[kind="primary"]:hover {{
        background-color: {NAVY_HOVER};
        border-color: {NAVY_HOVER};
        color: #ffffff;
        box-shadow: 0 8px 18px rgba(3,0,28,0.22);
    }}
    .stButton button:active, .stDownloadButton button:active {{
        transform: translateY(0);
        box-shadow: none;
    }}
    .stButton button:focus-visible, .stDownloadButton button:focus-visible {{
        outline: 2px solid {NAVY};
        outline-offset: 2px;
    }}

    /* Dépliables (st.expander) : le chrome gris par défaut de Streamlit ne
       correspond à aucune autre surface de l'outil - on l'aligne sur la
       même famille que .bloc-disclaimer / .tuile (fond blanc, filet fin,
       accent marine à gauche) plutôt que de le laisser générique. */
    [data-testid="stExpander"] {{
        border: 1px solid {BORDURE};
        border-left: 3px solid {NAVY};
        border-radius: 0;
        background: #ffffff;
    }}
    [data-testid="stExpander"] summary {{
        background: #ffffff;
        padding: 0.9rem 1.15rem;
        font-weight: 600;
        font-size: 0.92rem;
        color: {NAVY};
    }}
    [data-testid="stExpander"] summary:hover {{
        color: {NAVY_HOVER};
        background: {CREME};
    }}
    [data-testid="stExpander"] summary svg {{
        fill: {NAVY};
    }}
    /* Onglets (st.tabs) : 9 onglets avec le style par défaut de Streamlit
       finissent minuscules et tassés - on agrandit le texte et l'espace
       cliquable, et on marque l'onglet actif par un soulignement marine
       plutôt que par la seule couleur, pour qu'il reste repérable même
       en parcourant rapidement. */
    [data-baseweb="tab-list"] {{
        gap: 4px;
    }}
    [data-baseweb="tab-list"] button[data-baseweb="tab"] {{
        height: auto;
        padding: 0.7rem 1.1rem;
        font-size: 1rem;
        font-weight: 600;
        color: {ENCRE_SECONDAIRE};
    }}
    [data-baseweb="tab-list"] button[data-baseweb="tab"][aria-selected="true"] {{
        color: {NAVY};
    }}
    [data-baseweb="tab-list"] button[data-baseweb="tab"][aria-selected="true"] > div {{
        border-bottom: 3px solid {NAVY};
    }}
    [data-testid="stExpanderDetails"] {{
        padding: 0.1rem 1.15rem 1.05rem;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


def rgba_depuis_hex(hex_color, alpha):
    """Convertit une couleur hexadécimale (#rrggbb) en chaîne rgba(...) avec
    la transparence demandée - utilisé pour les zones remplies (bandes
    P10-P90, aires) à une opacité cohérente avec le reste de l'outil."""
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def fmt_euro(montant, signe=False):
    """Formate un montant en euros à la française : espace fine insécable
    comme séparateur de milliers (40 288 €), pas de virgule anglo-saxonne
    (40,288 €). signe=True ajoute un + explicite devant un montant positif
    (+3 787 €)."""
    gabarit = "{:+,.0f} €" if signe else "{:,.0f} €"
    return gabarit.format(montant).replace(",", " ")


def carte_kpi(label, valeur, couleur, sous_texte=""):
    st.markdown(
        f"""
        <div class="carte-kpi">
            <div class="accent" style="background:{couleur};"></div>
            <div class="label">{label}</div>
            <div class="valeur">{valeur}</div>
            <div class="sous-texte">{sous_texte}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def entete_section(titre, sous_titre=""):
    """En-tête à deux niveaux (gros titre serif + sous-titre serif italique),
    repris du gabarit de titre de section du site grandlargepatrimoine.fr."""
    st.markdown(
        f"""
        <div class="entete-section">
            <div class="titre">{titre}</div>
            <div class="sous-titre">{sous_titre}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def pitch_usage(texte):
    """Phrase d'accroche en haut d'un onglet : le problème concret que
    rencontre le client, suivi de ce que fait cet onglet pour y répondre."""
    st.markdown(
        f"""
        <div style="background:{SURFACE_CARTE}; border-left:3px solid {NAVY};
                     padding:12px 18px; margin:0.6rem 0 1.1rem 0; font-size:0.95rem;
                     color:{ENCRE_SECONDAIRE}; line-height:1.5;">
            {texte}
        </div>
        """,
        unsafe_allow_html=True,
    )


def avertissement_compliance(titre, texte):
    """Encart jaune/ambre pour un avertissement de compliance qui doit
    sauter aux yeux (ex. "ceci n'est pas la grille d'allocation réelle de
    Grand Large Patrimoine") - un simple st.caption se noie dans le reste
    du texte explicatif, alors que ce type de nuance est précisément celle
    qu'un lecteur pressé doit voir en premier, pas en dernier."""
    st.markdown(
        f"""
        <div style="background:#fef8ea; border-left:3px solid {COULEUR_ALERTE};
                     padding:12px 18px; margin:0.8rem 0; font-size:0.9rem;
                     color:{ENCRE_PRIMAIRE}; line-height:1.5;">
            <strong>⚠ {titre}</strong><br>{texte}
        </div>
        """,
        unsafe_allow_html=True,
    )


def titre_sous_section(texte):
    """Titre de sous-section à l'intérieur d'un onglet (ex. "Panier de
    solutions") - plus affirmé qu'un st.caption (qui a la même taille que le
    texte courant et passe inaperçu), sans rivaliser avec le grand titre
    d'onglet posé par entete_section."""
    st.markdown(f'<div class="titre-sous-section">{texte}</div>', unsafe_allow_html=True)


def etapes_numerotees(etapes):
    """Liste numérotée avec filets fins entre chaque étape — motif repris de
    « La Méthode Grand Large » sur le site (01. Comprendre / 02. Structurer...)."""
    lignes = "".join(
        f'<div class="etape-numerotee">'
        f'<div class="numero">{i:02d}.</div>'
        f'<div class="texte">{texte}</div>'
        f"</div>"
        for i, texte in enumerate(etapes, start=1)
    )
    st.markdown(f"<div>{lignes}</div>", unsafe_allow_html=True)


def glossaire_expander(cles, titre="Glossaire des termes utilisés ici"):
    """Dépliable (ouvert par défaut) listant les définitions des termes
    techniques pertinents pour l'onglet en cours - pour un lecteur
    non-initié (le dirigeant lui-même, ou un membre de sa famille)."""
    with st.expander(titre, expanded=True):
        for cle, definition in termes_glossaire(cles):
            st.markdown(f"**{cle}** — {definition}")


if "montant_input" not in st.session_state:
    st.session_state["montant_input"] = 80_000
if "profit_input" not in st.session_state:
    st.session_state["profit_input"] = 50_000

st.markdown(
    """
    <div class="bandeau">
        <svg class="motif-voile" width="190" height="190" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M50 8 L50 72 L18 72 Z" stroke="#ffffff" stroke-width="1.4" fill="none"/>
            <path d="M50 20 L50 72 L74 72 Z" stroke="#ffffff" stroke-width="1.4" fill="none"/>
            <line x1="50" y1="8" x2="50" y2="78" stroke="#ffffff" stroke-width="1.4"/>
            <path d="M12 78 Q50 92 88 78" stroke="#ffffff" stroke-width="1.4" fill="none"/>
        </svg>
        <div class="label">Simulateur patrimonial</div>
        <h1>Rémunération, holding & transmission</h1>
        <p>Compare salaire, dividende, capitalisation en holding et démembrement de propriété — avec les hypothèses toujours visibles et modifiables.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="bloc-disclaimer">Outil informatif à usage pédagogique, construit sur des '
    'hypothèses explicites (détaillées dans chaque section). Il ne constitue ni un conseil '
    'fiscal ni un conseil en investissement personnalisé, et ne remplace pas l\'analyse '
    'd\'un professionnel.</div>',
    unsafe_allow_html=True,
)

with st.expander("Comment utiliser ce simulateur (à lire en premier)", expanded=True):
    etapes_numerotees([
        "Onglet « Rémunération annuelle » : pour une année donnée, salaire ou dividende — lequel laisse le plus net en poche au dirigeant ? Saisissez le montant réellement disponible du client.",
        "Onglet « Trajectoire pluriannuelle » : sur plusieurs années, vaut-il mieux sortir l'argent chaque année ou le laisser capitaliser dans une holding ? Avec l'incertitude du rendement (fourchette P10-P90), pas un chiffre unique.",
        "Onglet « Démembrement de propriété » : pour transmettre un bien aux enfants, comparez donation en pleine propriété et donation de la seule nue-propriété.",
        "Onglet « Succession » : au décès, combien reste-t-il net selon qui hérite - conjoint, enfant, frère ou sœur, ou un tiers sans lien de parenté ?",
        "Onglet « Assurance-vie » : combien reste-t-il net lors d'un rachat, ou pour les bénéficiaires à la transmission - selon l'âge du souscripteur au moment des versements ?",
        "Onglet « IFI » : le patrimoine immobilier (hors résidence principale partiellement abattue, hors biens professionnels) dépasse-t-il le seuil d'assujettissement, et pour combien ?",
        "Onglet « SCI (IS vs IR) » : pour détenir un bien locatif en société, IS (amortissement, double imposition) ou IR (pas d'amortissement, abattement durée de détention) - lequel laisse le plus au terme ?",
        "Onglet « PER » : verser sur un plan d'épargne retraite plutôt que percevoir en net - troisième levier d'arbitrage de la rémunération, à côté du salaire et du dividende.",
        "Onglet « Note Grand Large » : les chiffres de marché et seuils réglementaires utilisés ailleurs dans l'outil, sourcés et datés.",
        "Dans chaque onglet, les montants se modifient librement — aucun résultat n'est figé, tout se recalcule en direct.",
    ])

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs(
    ["Rémunération annuelle", "Trajectoire pluriannuelle", "Démembrement de propriété", "Succession", "Assurance-vie", "IFI", "SCI (IS vs IR)", "PER", "Note Grand Large"]
)

# Barre d'outils Plotly activée (zoom rectangle, panoramique, réinitialiser,
# export PNG) - seuls les boutons de sélection (lasso/rectangle de sélection
# de points, inutiles sur des courbes/barres) et le logo Plotly sont retirés.
# scrollZoom désactivé (False) : zoomer à la molette captait le défilement de
# la page dès que la souris survolait un graphique en faisant simplement
# défiler la page - gênant en usage normal. Le zoom reste possible via la
# barre d'outils (icône loupe puis rectangle de sélection).
CONFIG_GRAPHIQUE = {
    "displayModeBar": True,
    "displaylogo": False,
    "modeBarButtonsToRemove": ["select2d", "lasso2d", "autoScale2d"],
    "scrollZoom": False,
}


POLICE_TITRE_GRAPHIQUE = "Libre Caslon Display, Georgia, serif"
POLICE_CORPS_GRAPHIQUE = "Inter, -apple-system, Segoe UI, sans-serif"


def _mise_en_forme_graphique(fig, titre, y_titre):
    fig.update_layout(
        title=dict(text=titre, font=dict(family=POLICE_TITRE_GRAPHIQUE, size=20, color=ENCRE_PRIMAIRE)),
        plot_bgcolor=SURFACE_CARTE,
        paper_bgcolor=SURFACE_CARTE,
        font=dict(family=POLICE_CORPS_GRAPHIQUE, color=ENCRE_SECONDAIRE, size=14),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.08, xanchor="left", x=0,
            font=dict(family=POLICE_CORPS_GRAPHIQUE, color=ENCRE_SECONDAIRE, size=13),
            # groupclick="togglegroup" : cliquer "Direct" ou "Holding" dans la
            # légende masque/affiche toute la série (ligne + fourchette P10-P90),
            # pas seulement la ligne médiane - un double-clic isole cette seule
            # série en masquant toutes les autres (comportement natif Plotly).
            groupclick="togglegroup",
        ),
        margin=dict(t=100, l=10, r=10, b=10),
        hovermode="x unified",
        # dragmode=False : cliquer-glisser sur le graphique ne déclenche plus
        # de rectangle de sélection/zoom accidentel (gênant en usage normal,
        # ex. en essayant juste de survoler le graphique). Le zoom reste
        # possible via la barre d'outils (CONFIG_GRAPHIQUE).
        dragmode=False,
        # Infobulle en carte marine pleine plutôt que le cadre blanc/gris par
        # défaut de Plotly - qui est l'un des signaux les plus "logiciel de
        # calcul" d'un graphique autrement soigné.
        hoverlabel=dict(
            bgcolor=NAVY, bordercolor=NAVY,
            font=dict(family=POLICE_CORPS_GRAPHIQUE, color="#ffffff", size=13),
        ),
        separators=". ",  # convention française : point décimal, espace pour les milliers
        # Barre d'outils (zoom/export) discrète et dans la charte - plutôt que
        # les icônes bleu vif par défaut de Plotly, hors charte.
        modebar=dict(bgcolor="rgba(0,0,0,0)", color=ENCRE_MUTED, activecolor=NAVY),
    )
    fig.update_yaxes(
        title=dict(text=y_titre, font=dict(family=POLICE_CORPS_GRAPHIQUE, size=13, color=ENCRE_MUTED)),
        gridcolor=GRILLE, gridwidth=1, zeroline=False, showline=False,
        tickformat=",.0f", ticksuffix=" €", tickfont=dict(family=POLICE_CORPS_GRAPHIQUE, size=12, color=ENCRE_MUTED),
    )
    # Pas de quadrillage vertical : c'est lui qui donne aux graphiques leur
    # air de capture Excel. Seule une ligne de base fine signale l'axe des
    # catégories - jamais un cadre complet autour du tracé.
    fig.update_xaxes(
        showgrid=False, zeroline=False,
        showline=True, linecolor=BORDURE, linewidth=1,
        tickfont=dict(family=POLICE_CORPS_GRAPHIQUE, size=13, color=ENCRE_SECONDAIRE),
    )
    # Texte au-dessus des barres/cascades (montants) : en encre secondaire
    # plutôt qu'en noir plein - les totaux (barres pleines) restent lisibles
    # sans que chaque valeur intermédiaire ne crie au même niveau que le
    # titre. N'affecte que les traces qui affichent du texte (bar,
    # waterfall) - sans effet sur les courbes.
    fig.update_traces(textfont=dict(family=POLICE_CORPS_GRAPHIQUE, size=13, color=ENCRE_SECONDAIRE))
    # Coins arrondis sur les barres - rendu plus actuel qu'un rectangle plein.
    fig.update_traces(marker=dict(cornerradius=6), selector=dict(type="bar"))
    return fig


# --- Onglet 1 : comparaison simple salaire vs dividende sur une année ---
with tab1:
    entete_section(
        "Salaire vs dividende, sur une année",
        "Part fiscale unique — barèmes 2026 (revenus 2025)",
    )
    pitch_usage(
        "<strong>Vous dirigez une entreprise et hésitez sur la manière de vous verser de "
        "l'argent ?</strong> Salaire ou dividende ne laissent pas le même montant net en "
        "poche, pour un même coût pour l'entreprise. Entrez un montant, cet onglet calcule "
        "les deux et vous montre lequel est le plus avantageux, et de combien."
    )

    forme_juridique = st.radio(
        "Forme juridique du dirigeant",
        ["SASU (président, assimilé salarié)", "SARL (gérant majoritaire, TNS)"],
        horizontal=True,
    )
    est_sarl = forme_juridique.startswith("SARL")
    st.caption(
        "Le régime social change tout : le président de SASU est assimilé salarié (charges "
        "patronales + salariales), le gérant majoritaire de SARL est travailleur non salarié "
        "- TNS (cotisations propres, globalement moins élevées, pour des droits sociaux moindres)."
        if not est_sarl else
        "Travailleur non salarié (TNS) : pas de distinction charges patronales/salariales, le "
        "gérant paie lui-même ses cotisations sur la rémunération versée par la société. Les "
        "dividendes au-delà de 10% du capital social (+ compte courant + primes d'émission) "
        "sont réintégrés dans l'assiette des cotisations (article L131-6 du code de la sécurité "
        "sociale) : voir « Comment lire ce scénario »."
    )

    montant = st.number_input(
        "Montant disponible dans l'entreprise (€, coût total avant répartition)",
        min_value=0, max_value=1_000_000, step=5_000, key="montant_input",
    )
    st.caption(f"→ {fmt_euro(montant)}")

    if est_sarl:
        with st.expander("Comment lire ce scénario (SARL / gérant majoritaire)", expanded=True):
            st.markdown(
                "- **Rémunération** : la société verse une rémunération au gérant, intégralement "
                "déductible de l'IS - pas de charges patronales séparées comme en SASU, le gérant "
                "paie lui-même l'ensemble de ses cotisations TNS dessus.\n"
                "- **Dividende** : l'IS est payé d'abord, puis le dividende distribuable est séparé "
                "en deux parts - celle sous le seuil des 10% du capital social (+ compte courant + "
                "primes d'émission) reste au PFU classique (31,4%), celle au-delà est réintégrée "
                "dans l'assiette des cotisations TNS (et ne supporte plus que 12,8% d'impôt sur le "
                "revenu, la CSG-CRDS étant déjà comprise dans les cotisations).\n"
                "- **Capital social faible** (cas fréquent en SARL) → le seuil des 10% est vite "
                "atteint, et une grande partie du dividende finit cotisée comme un revenu "
                "professionnel : saisissez le capital réel du client ci-dessous, ça change beaucoup "
                "le résultat."
            )
        col_cap1, col_cap2 = st.columns(2)
        capital_social = col_cap1.number_input("Capital social de la SARL (€)", min_value=1, max_value=5_000_000, value=10_000, step=1_000)
        compte_courant_moyen = col_cap2.number_input("Solde moyen du compte courant d'associé (€, optionnel)", min_value=0, max_value=5_000_000, value=0, step=5_000)
        seuil_div = seuil_dividendes_sans_cotisations(capital_social, compte_courant_moyen)
        st.caption(f"→ Seuil de dividende non cotisé : {fmt_euro(seuil_div)} par an (10% de {fmt_euro(capital_social + compte_courant_moyen)}).")

        net_salaire = net_apres_remuneration_tns(montant)
        resultat_div_tns = net_apres_dividende_tns(montant, capital_social, compte_courant_moyen)
        # net_total seul omet la cotisation TNS minimale forfaitaire, due même à
        # rémunération nulle tant que le gérant reste affilié (cf. fiscalite_tns.py) :
        # on la retranche ici pour que le scénario "100% dividende" soit réellement complet.
        net_dividende = resultat_div_tns["net_total"] - cotisations_tns(0)
    else:
        net_salaire = net_apres_salaire(montant)
        net_dividende = net_apres_dividende(montant)

    meilleur = "la rémunération" if est_sarl and net_salaire > net_dividende else "le salaire" if net_salaire > net_dividende else "le dividende"
    ecart = abs(net_salaire - net_dividende)
    libelle_salaire = "Net en poche si rémunération" if est_sarl else "Net en poche si salaire"

    col1, col2, col3 = st.columns(3)
    with col1:
        carte_kpi(
            libelle_salaire, fmt_euro(net_salaire), COULEUR_SALAIRE,
            f"Ce que le dirigeant garde vraiment, une fois toutes les charges et l'impôt payés, "
            f"s'il se verse {fmt_euro(montant)} en {'rémunération' if est_sarl else 'salaire'}.",
        )
    with col2:
        carte_kpi(
            "Net en poche si dividende", fmt_euro(net_dividende), COULEUR_DIVIDENDE,
            f"Ce que le dirigeant garde vraiment après l'impôt sur les sociétés payé par "
            f"l'entreprise, puis l'impôt sur le dividende qui lui est versé.",
        )
    with col3:
        carte_kpi(
            "Écart", fmt_euro(ecart), ENCRE_MUTED,
            f"{fmt_euro(ecart)} de plus en poche en choisissant {meilleur} plutôt que l'autre "
            f"option, pour ce même montant de départ.",
        )

    st.write("")

    fig1 = go.Figure()
    fig1.add_bar(
        x=["Rémunération" if est_sarl else "Salaire", "Dividende"], y=[net_salaire, net_dividende],
        marker_color=[COULEUR_SALAIRE, COULEUR_DIVIDENDE],
        text=[fmt_euro(net_salaire), fmt_euro(net_dividende)],
        textposition="outside", width=0.5,
        hovertemplate="%{x} : %{y:,.0f} €<extra></extra>",
    )
    fig1 = _mise_en_forme_graphique(fig1, f"Pour {fmt_euro(montant)} disponibles", "Net en poche (€)")
    # Marge au-dessus de la barre la plus haute : sans ça, l'étiquette de
    # valeur ("outside") et l'infobulle au survol ("x unified", positionnée
    # en haut du tracé) se chevauchent et deviennent illisibles.
    fig1.update_yaxes(range=[0, max(net_salaire, net_dividende, 1) * 1.22])
    fig1.update_xaxes(showgrid=False)
    st.plotly_chart(fig1, width="stretch", config=CONFIG_GRAPHIQUE)

    # --- Optimiseur de répartition (pas forcément 100%/0%) ---
    st.write("")
    st.markdown("### Trouver la meilleure répartition entre les deux")
    st.caption(
        "Rien n'oblige à choisir 100 % d'un côté : à cause des effets de seuil (plafond "
        "de la sécurité sociale, tranches de l'impôt, seuil de dividende non cotisé en "
        "SARL), une répartition intermédiaire laisse parfois plus de net en poche que "
        "les deux options pures."
    )

    libelle_opt_part = "rémunération" if est_sarl else "salaire"
    capital_opt = capital_social if est_sarl else 10_000
    compte_courant_opt = compte_courant_moyen if est_sarl else 0.0
    resultat_opt = repartition_optimale(montant, est_sarl, capital_opt, compte_courant_opt)
    pourcentages_opt = [p for p, _ in resultat_opt["points"]]
    nets_opt = [n for _, n in resultat_opt["points"]]
    gain_opt = resultat_opt["gain_vs_extremes"]
    optimum_est_un_extreme = resultat_opt["meilleur_p_pct"] in (0, 100)

    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        carte_kpi(
            "Répartition optimale",
            f"{resultat_opt['meilleur_p_pct']} % {libelle_opt_part} / {100 - resultat_opt['meilleur_p_pct']} % dividende",
            NAVY,
            f"Pour {fmt_euro(montant)} disponibles, c'est la répartition qui laisse le plus de net en "
            f"poche : {fmt_euro(resultat_opt['meilleur_net'])}.",
        )
    with col_opt2:
        gain_relatif = gain_opt / montant if montant else 0
        carte_kpi(
            "Gain vs. la meilleure option pure",
            fmt_euro(gain_opt) if gain_opt > 1 else "Aucun",
            COULEUR_JAUNE if gain_opt > 1 else ENCRE_MUTED,
            (
                f"{fmt_euro(gain_opt)} de plus qu'en se limitant à la meilleure des deux options "
                f"braquées (100 % {libelle_opt_part} ou 100 % dividende)."
                + (
                    " Gain modeste en proportion : l'intérêt est surtout de montrer l'effet de seuil, "
                    "pas un levier à lui seul décisif."
                    if 0 < gain_relatif < 0.005 else ""
                )
                if gain_opt > 1 else
                f"Ici, une des deux options pures (100 % {libelle_opt_part} ou 100 % dividende) est "
                f"déjà optimale - pas de gain à répartir pour ce montant."
            ),
        )

    if not optimum_est_un_extreme:
        fig_opt = go.Figure()
        fig_opt.add_scatter(
            x=pourcentages_opt, y=nets_opt, mode="lines",
            line=dict(color=NAVY, width=3, shape="linear"),
            fill="tozeroy", fillcolor=rgba_depuis_hex(NAVY, 0.07),
            showlegend=False,
            hovertemplate=f"%{{x}} %% {libelle_opt_part} : %{{y:,.0f}} €<extra></extra>",
        )
        fig_opt.add_scatter(
            x=[0], y=[resultat_opt["net_100_dividende"]], mode="markers",
            marker=dict(size=9, color=COULEUR_DIVIDENDE, line=dict(color=SURFACE_CARTE, width=2)),
            showlegend=False, hoverinfo="skip",
        )
        fig_opt.add_scatter(
            x=[100], y=[resultat_opt["net_100_salaire"]], mode="markers",
            marker=dict(size=9, color=COULEUR_SALAIRE, line=dict(color=SURFACE_CARTE, width=2)),
            showlegend=False, hoverinfo="skip",
        )
        fig_opt.add_scatter(
            x=[resultat_opt["meilleur_p_pct"]], y=[resultat_opt["meilleur_net"]], mode="markers+text",
            marker=dict(size=12, symbol="diamond", color=NAVY, line=dict(color=SURFACE_CARTE, width=2)),
            text=[f"  {fmt_euro(resultat_opt['meilleur_net'])}"], textposition="top right",
            textfont=dict(size=14, color=NAVY),
            showlegend=False, hoverinfo="skip", cliponaxis=False,
        )
        fig_opt.add_vline(x=resultat_opt["meilleur_p_pct"], line=dict(color=ENCRE_MUTED, width=1.2, dash="dot"))
        fig_opt = _mise_en_forme_graphique(
            fig_opt, f"Net en poche selon la part allouée en {libelle_opt_part}", "Net en poche (€)"
        )
        fig_opt.update_xaxes(title=f"% alloué en {libelle_opt_part}", ticksuffix=" %", range=[-2, 108])
        # Plage Y fixée explicitement : le remplissage "tozeroy" ferait sinon
        # redescendre l'autorange jusqu'à 0, ce qui écraserait visuellement
        # la courbe (l'intérêt du graphique est justement de montrer les
        # petites variations entre répartitions, pas l'ordre de grandeur).
        etendue_y = max(nets_opt) - min(nets_opt)
        marge_y = etendue_y * 0.12 if etendue_y > 0 else max(nets_opt) * 0.01
        fig_opt.update_yaxes(range=[min(nets_opt) - marge_y, max(nets_opt) + marge_y * 2.2])
        fig_opt.update_layout(margin=dict(r=70))
        st.plotly_chart(fig_opt, width="stretch", config=CONFIG_GRAPHIQUE)
        st.caption(
            f"Point dividende pur (0 %) en orange, {libelle_opt_part} pur (100 %) en bleu, optimum en "
            f"losange marine. La courbe n'est pas lissée volontairement : les coudes marquent les "
            f"effets de seuil (plafond de la sécurité sociale, tranches de l'impôt...)."
        )

    # --- Analyse de sensibilité (tornade) ---
    titre_sous_section("Sensibilité du résultat")
    st.caption(
        "Quel paramètre fait le plus bouger le net en poche optimal, toutes choses égales par "
        "ailleurs ? Chaque hypothèse haute/basse est un test de robustesse, pas une prévision - "
        "certains paramètres (taux d'IS, abattement forfaitaire) ne changent pas du jour au lendemain "
        "dans la réalité."
    )
    capital_social_sensibilite = capital_social if est_sarl else 10_000
    compte_courant_sensibilite = compte_courant_moyen if est_sarl else 0.0
    resultats_sensibilite = analyse_sensibilite(montant, est_sarl, capital_social_sensibilite, compte_courant_sensibilite)
    baseline_sensibilite = resultat_opt["meilleur_net"]

    # En-dessous de ce seuil, l'écart est traité comme négligeable (un simple
    # résidu d'arrondi du balayage à 1 point de pourcentage) plutôt qu'un
    # véritable effet - certaines combinaisons mettent légitimement un
    # paramètre hors-jeu pour ce scénario précis (ex. le taux d'IS normal n'a
    # aucune prise quand le dividende optimal reste sous le seuil des 42 500€
    # taxés à taux réduit, ou quand la répartition optimale est déjà à 100%
    # d'un seul côté) : mieux vaut l'annoncer explicitement qu'afficher une
    # barre invisible qui aurait l'air d'un bug d'affichage.
    SEUIL_EFFET_NEGLIGEABLE = 15

    donnees_tornade = list(reversed(resultats_sensibilite))  # plus grande amplitude en haut du graphique
    categories_tornade = [d["parametre"] for d in donnees_tornade]
    textes_bas, textes_haut, valeurs_bas, valeurs_haut = [], [], [], []
    sans_effet = []
    for d in donnees_tornade:
        if d["type"] == "categoriel":
            lib_bas, lib_haut = d["libelle_bas"], d["libelle_haut"]
        elif d["type"] == "pourcentage":
            lib_bas, lib_haut = f"taux à {d['param_bas']:.0%}", f"taux à {d['param_haut']:.0%}"
        else:
            lib_bas, lib_haut = f"à {fmt_euro(d['param_bas'])}", f"à {fmt_euro(d['param_haut'])}"
        textes_bas.append(lib_bas)
        textes_haut.append(lib_haut)
        valeurs_bas.append(d["valeur_bas"])
        valeurs_haut.append(d["valeur_haut"])
        sans_effet.append(abs(d["valeur_haut"] - d["valeur_bas"]) < SEUIL_EFFET_NEGLIGEABLE)

    fig_tornade = go.Figure()
    fig_tornade.add_bar(
        y=categories_tornade, x=[v - baseline_sensibilite for v in valeurs_bas], base=baseline_sensibilite,
        orientation="h", name="Hypothèse basse", marker_color=COULEUR_DEMEMBREMENT,
        customdata=list(zip(textes_bas, valeurs_bas)),
        hovertemplate="<b>%{y}</b><br>%{customdata[0]} : %{customdata[1]:,.0f} €<extra></extra>",
        text=["" if sa else fmt_euro(v) for sa, v in zip(sans_effet, valeurs_bas)], textposition="outside",
        textfont=dict(family=POLICE_CORPS_GRAPHIQUE, size=12, color=COULEUR_DEMEMBREMENT),
    )
    fig_tornade.add_bar(
        y=categories_tornade, x=[v - baseline_sensibilite for v in valeurs_haut], base=baseline_sensibilite,
        orientation="h", name="Hypothèse haute", marker_color=COULEUR_MAGENTA,
        customdata=list(zip(textes_haut, valeurs_haut)),
        hovertemplate="<b>%{y}</b><br>%{customdata[0]} : %{customdata[1]:,.0f} €<extra></extra>",
        text=["" if sa else fmt_euro(v) for sa, v in zip(sans_effet, valeurs_haut)], textposition="outside",
        textfont=dict(family=POLICE_CORPS_GRAPHIQUE, size=12, color=COULEUR_MAGENTA),
    )
    for categorie, est_sans_effet in zip(categories_tornade, sans_effet):
        if est_sans_effet:
            fig_tornade.add_annotation(
                x=baseline_sensibilite, y=categorie, text="<i>sans effet pour ce scénario</i>",
                showarrow=False, xanchor="left", xshift=14, align="left",
                font=dict(family=POLICE_CORPS_GRAPHIQUE, size=12, color=ENCRE_MUTED),
            )
    fig_tornade.add_vline(
        x=baseline_sensibilite, line=dict(color=ENCRE_MUTED, width=1.4, dash="dot"),
        annotation_text="Scénario actuel", annotation_position="top",
        annotation_font=dict(family=POLICE_CORPS_GRAPHIQUE, size=12, color=ENCRE_MUTED),
    )
    fig_tornade = _mise_en_forme_graphique(fig_tornade, "Sensibilité du net en poche optimal", "")
    fig_tornade.update_yaxes(
        title=None, showgrid=False, zeroline=False, showline=False,
        tickfont=dict(family=POLICE_CORPS_GRAPHIQUE, size=13, color=ENCRE_SECONDAIRE),
    )
    valeurs_toutes = valeurs_bas + valeurs_haut + [baseline_sensibilite]
    etendue_tornade = max(valeurs_toutes) - min(valeurs_toutes)
    marge_tornade = etendue_tornade * 0.22 if etendue_tornade > 0 else max(valeurs_toutes) * 0.02
    fig_tornade.update_xaxes(
        title=dict(text="Net en poche (€)", font=dict(family=POLICE_CORPS_GRAPHIQUE, size=13, color=ENCRE_MUTED)),
        gridcolor=GRILLE, gridwidth=1, zeroline=False, showline=False,
        tickformat=",.0f", ticksuffix=" €", tickfont=dict(family=POLICE_CORPS_GRAPHIQUE, size=12, color=ENCRE_MUTED),
        range=[min(valeurs_toutes) - marge_tornade, max(valeurs_toutes) + marge_tornade],
    )
    fig_tornade.update_layout(height=140 + 80 * len(categories_tornade), margin=dict(l=10, r=10, t=100, b=10))
    st.plotly_chart(fig_tornade, width="stretch", config=CONFIG_GRAPHIQUE)
    st.caption(
        f"Scénario actuel (ligne pointillée) : {fmt_euro(baseline_sensibilite)} de net en poche "
        f"optimal, pour {fmt_euro(montant)} disponibles en {forme_juridique.split(' (')[0]}. Barres "
        f"triées par amplitude d'impact décroissante - le paramètre du haut est celui qui fait le "
        f"plus bouger le résultat."
    )

    # --- Comparateur direct des 4 scénarios (SASU et SARL), sans bascule ---
    if est_sarl:
        capital_social_comparateur = capital_social
        compte_courant_comparateur = compte_courant_moyen
        net_salaire_sasu = net_apres_salaire(montant)
        net_dividende_sasu = net_apres_dividende(montant)
        net_remuneration_sarl = net_salaire
        net_dividende_sarl = net_dividende
    else:
        capital_social_comparateur = 10_000
        compte_courant_comparateur = 0
        net_salaire_sasu = net_salaire
        net_dividende_sasu = net_dividende
        net_remuneration_sarl = net_apres_remuneration_tns(montant)
        net_dividende_sarl = (
            net_apres_dividende_tns(montant, capital_social_comparateur, compte_courant_comparateur)["net_total"]
            - cotisations_tns(0)
        )

    with st.expander("Comparer les 4 scénarios (SASU et SARL) sans changer de forme juridique"):
        if not est_sarl:
            st.caption(
                f"Valeurs SARL calculées avec un capital social par défaut de "
                f"{fmt_euro(capital_social_comparateur)} (choisissez « SARL » ci-dessus pour saisir le "
                f"capital réel du client)."
            )
        fig_comparateur = go.Figure()
        fig_comparateur.add_bar(
            x=["SASU\nsalaire", "SASU\ndividende", "SARL\nrémunération", "SARL\ndividende"],
            y=[net_salaire_sasu, net_dividende_sasu, net_remuneration_sarl, net_dividende_sarl],
            marker_color=[COULEUR_SALAIRE, COULEUR_DIVIDENDE, COULEUR_SALAIRE, COULEUR_DIVIDENDE],
            marker_opacity=[
                1.0 if not est_sarl else 0.4,
                1.0 if not est_sarl else 0.4,
                1.0 if est_sarl else 0.4,
                1.0 if est_sarl else 0.4,
            ],
            text=[fmt_euro(v) for v in [net_salaire_sasu, net_dividende_sasu, net_remuneration_sarl, net_dividende_sarl]],
            textposition="outside", width=0.6,
            hovertemplate="%{x} : %{y:,.0f} €<extra></extra>",
        )
        fig_comparateur = _mise_en_forme_graphique(
            fig_comparateur, f"Net en poche pour {fmt_euro(montant)}, selon la forme juridique", "Net en poche (€)"
        )
        fig_comparateur.update_xaxes(showgrid=False)
        fig_comparateur.update_yaxes(
            range=[0, max(net_salaire_sasu, net_dividende_sasu, net_remuneration_sarl, net_dividende_sarl, 1) * 1.22]
        )
        st.plotly_chart(fig_comparateur, width="stretch", config=CONFIG_GRAPHIQUE)
        st.caption(
            "Le scénario actuellement sélectionné ci-dessus apparaît en couleur pleine, l'autre en "
            "transparence - pour comparer les deux formes juridiques sans changer le réglage."
        )

    if est_sarl:
        cotisations_remuneration = cotisations_tns(montant)
        net_avant_abattement = montant - cotisations_remuneration
        net_imposable = applique_abattement_salaire(net_avant_abattement)
        abattement = net_avant_abattement - net_imposable
        ir_salaire = calcul_ir(net_imposable)

        with st.expander("Voir la cascade du calcul — scénario rémunération", expanded=False):
            fig_cascade = go.Figure(go.Waterfall(
                orientation="v",
                measure=["absolute", "relative", "relative", "total"],
                x=["Coût total\nentreprise", "Cotisations\nTNS", "Impôt sur\nle revenu", "Net en poche"],
                y=[montant, -cotisations_remuneration, -ir_salaire, net_salaire],
                text=[fmt_euro(v) for v in [montant, cotisations_remuneration, ir_salaire, net_salaire]],
                textposition="outside",
                connector=dict(line=dict(color=GRILLE, width=1)),
                decreasing=dict(marker=dict(color="#e34948")),
                increasing=dict(marker=dict(color=COULEUR_DIVIDENDE)),
                totals=dict(marker=dict(color=COULEUR_SALAIRE)),
            ))
            fig_cascade = _mise_en_forme_graphique(
                fig_cascade, "De 100 % du coût entreprise au net réellement en poche (scénario rémunération)", "Montant (€)"
            )
            fig_cascade.update_xaxes(showgrid=False)
            st.plotly_chart(fig_cascade, width="stretch", config=CONFIG_GRAPHIQUE)
            st.caption(
                "Pas de distinction charges patronales/salariales en TNS : une seule cotisation "
                "globale, payée par le gérant. L'abattement forfaitaire de 10 % n'apparaît pas ici : "
                "il réduit la base imposable, pas directement la trésorerie."
            )

        is_du_dividende_tns = calcul_is(montant)
        impot_dividende_hors_is_tns = (
            resultat_div_tns["part_sous_seuil"] * TAUX_PFU
            + resultat_div_tns["part_au_dela"] * TAUX_IR_SEUL_PFU
        )
        cotisations_exces_tns = resultat_div_tns["cotisations_exces"]
        cotisation_minimale_tns = cotisations_tns(0)
        impot_total_dividende_tns = is_du_dividende_tns + impot_dividende_hors_is_tns

        with st.expander("Voir la cascade du calcul — scénario dividende", expanded=False):
            fig_cascade_div = go.Figure(go.Waterfall(
                orientation="v",
                measure=["absolute", "relative", "relative", "relative", "relative", "total"],
                x=["Coût total\nentreprise", "IS\n(société)", "Impôt sur le\ndividende", "Cotisations TNS\n(part > seuil)", "Cotisation TNS\nminimale", "Net en poche"],
                y=[montant, -is_du_dividende_tns, -impot_dividende_hors_is_tns, -cotisations_exces_tns, -cotisation_minimale_tns, net_dividende],
                text=[fmt_euro(v) for v in [montant, is_du_dividende_tns, impot_dividende_hors_is_tns, cotisations_exces_tns, cotisation_minimale_tns, net_dividende]],
                textposition="outside",
                connector=dict(line=dict(color=GRILLE, width=1)),
                decreasing=dict(marker=dict(color="#e34948")),
                increasing=dict(marker=dict(color=COULEUR_DIVIDENDE)),
                totals=dict(marker=dict(color=COULEUR_DIVIDENDE)),
            ))
            fig_cascade_div = _mise_en_forme_graphique(
                fig_cascade_div, "De 100 % du coût entreprise au net réellement en poche (scénario dividende)", "Montant (€)"
            )
            fig_cascade_div.update_xaxes(showgrid=False)
            st.plotly_chart(fig_cascade_div, width="stretch", config=CONFIG_GRAPHIQUE)
            st.caption(
                "« Cotisation TNS minimale » : due pour maintenir l'affiliation du gérant majoritaire "
                "au régime TNS, même s'il ne se verse aucune rémunération - un dividende à 100 % ne "
                "supprime pas cette cotisation plancher. « Cotisations TNS (part > seuil) » : uniquement "
                "la part du dividende qui dépasse 10 % du capital social (+ compte courant), réintégrée "
                "dans l'assiette TNS - nulle "
                "si le dividende reste sous ce seuil."
            )
        df_detail = pd.DataFrame(
            {
                "Rémunération": [
                    montant, cotisations_remuneration, abattement, ir_salaire, net_salaire,
                ],
                "Dividende": [
                    montant, resultat_div_tns["cotisations_exces"] + cotisation_minimale_tns, None,
                    impot_total_dividende_tns, net_dividende,
                ],
            },
            index=[
                "Coût total entreprise", "Cotisations TNS", "Abattement 10% frais pro.",
                "Impôt total (IR seul en rémunération, IS + IR en dividende)", "Net final en poche",
            ],
        )
    else:
        brut = brut_depuis_cout_total(montant)
        charges_employeur, charges_salarie = charges_sur_brut(brut)
        net_avant_abattement = brut - charges_salarie
        net_imposable = applique_abattement_salaire(net_avant_abattement)
        abattement = net_avant_abattement - net_imposable
        ir_salaire = calcul_ir(net_imposable)

        is_du = calcul_is(montant)
        distribuable = montant - is_du
        pfu_montant = distribuable * TAUX_PFU

        with st.expander("Voir la cascade du calcul — scénario salaire", expanded=False):
            fig_cascade = go.Figure(go.Waterfall(
                orientation="v",
                measure=["absolute", "relative", "relative", "relative", "total"],
                x=["Coût total\nentreprise", "Charges\npatronales", "Charges\nsalariales", "Impôt sur\nle revenu", "Net en poche"],
                y=[montant, -charges_employeur, -charges_salarie, -ir_salaire, net_salaire],
                text=[fmt_euro(v) for v in [montant, charges_employeur, charges_salarie, ir_salaire, net_salaire]],
                textposition="outside",
                connector=dict(line=dict(color=GRILLE, width=1)),
                decreasing=dict(marker=dict(color="#e34948")),
                increasing=dict(marker=dict(color=COULEUR_DIVIDENDE)),
                totals=dict(marker=dict(color=COULEUR_SALAIRE)),
            ))
            fig_cascade = _mise_en_forme_graphique(
                fig_cascade, "De 100 % du coût entreprise au net réellement en poche (scénario salaire)", "Montant (€)"
            )
            fig_cascade.update_xaxes(showgrid=False)
            st.plotly_chart(fig_cascade, width="stretch", config=CONFIG_GRAPHIQUE)
            st.caption(
                "L'abattement forfaitaire de 10 % n'apparaît pas ici : il réduit la base imposable, "
                "pas directement la trésorerie — son effet est déjà intégré dans la barre « Impôt sur le revenu »."
            )

        with st.expander("Voir la cascade du calcul — scénario dividende", expanded=False):
            fig_cascade_div = go.Figure(go.Waterfall(
                orientation="v",
                measure=["absolute", "relative", "relative", "total"],
                x=["Coût total\nentreprise", "IS\n(société)", "PFU sur le\ndividende (30 %)", "Net en poche"],
                y=[montant, -is_du, -pfu_montant, net_dividende],
                text=[fmt_euro(v) for v in [montant, is_du, pfu_montant, net_dividende]],
                textposition="outside",
                connector=dict(line=dict(color=GRILLE, width=1)),
                decreasing=dict(marker=dict(color="#e34948")),
                increasing=dict(marker=dict(color=COULEUR_DIVIDENDE)),
                totals=dict(marker=dict(color=COULEUR_DIVIDENDE)),
            ))
            fig_cascade_div = _mise_en_forme_graphique(
                fig_cascade_div, "De 100 % du coût entreprise au net réellement en poche (scénario dividende)", "Montant (€)"
            )
            fig_cascade_div.update_xaxes(showgrid=False)
            st.plotly_chart(fig_cascade_div, width="stretch", config=CONFIG_GRAPHIQUE)
            st.caption(
                "Le PFU (prélèvement forfaitaire unique, 30 %) se décompose en 12,8 % d'impôt sur le "
                "revenu et 17,2 % de prélèvements sociaux, prélevés en une fois sur le dividende versé."
            )

        df_detail = pd.DataFrame(
            {
                "Salaire": [
                    montant, charges_employeur, brut, charges_salarie, abattement, ir_salaire, net_salaire,
                ],
                "Dividende": [
                    montant, None, None, None, None, is_du + pfu_montant, net_dividende,
                ],
            },
            index=[
                "Coût total entreprise", "Charges patronales (déduites)", "Salaire brut",
                "Charges salariales", "Abattement 10% frais pro.", "Impôt total",
                "Net final en poche",
            ],
        )

    with st.expander("Voir le détail du calcul, étape par étape"):
        # Pré-formatage en chaînes : st.dataframe (grille interactive) n'honore
        # pas toujours le na_rep d'un Styler pandas et affichait "None".
        st.dataframe(
            df_detail.map(lambda v: fmt_euro(v) if pd.notna(v) else "—"),
            width="stretch",
        )

    col_csv, col_pdf = st.columns(2)
    with col_csv:
        st.download_button(
            "Télécharger ce scénario (CSV)",
            data=df_detail.to_csv().encode("utf-8"),
            file_name=f"scenario_remuneration_{montant}.csv",
            mime="text/csv",
        )
    with col_pdf:
        lignes_pdf = [["Poste"] + list(df_detail.columns)] + [
            [str(poste)] + [fmt_euro(v) if pd.notna(v) else "—" for v in ligne]
            for poste, ligne in zip(df_detail.index, df_detail.values)
        ]
        hypotheses_pdf = (
            [
                "Gérant majoritaire de SARL, travailleur non salarié (TNS) : pas de distinction "
                "charges patronales/salariales, cotisations payées en totalité par le gérant.",
                f"Seuil de dividende non réintégré dans l'assiette TNS : {fmt_euro(seuil_div)} par an "
                f"(10 % du capital social + compte courant d'associé, article L131-6 du code de la "
                f"sécurité sociale).",
                f"Scénario dividende : inclut la cotisation TNS minimale forfaitaire "
                f"({fmt_euro(cotisation_minimale_tns)}), due pour maintenir l'affiliation du gérant "
                f"majoritaire même sans rémunération versée.",
                "Simplifications documentées (progressivité maladie/famille interpolée, assiette "
                "CSG-CRDS sans abattement non confirmé) : voir le code source, à vérifier avec un "
                "expert-comptable.",
            ]
            if est_sarl else
            [
                "Président de SASU, assimilé salarié : charges patronales et salariales calculées "
                "par tranche de PASS.",
                "Abattement forfaitaire de 10 % pour frais professionnels, barème IR 2026 (revenus "
                "2025), part fiscale unique.",
                "Dividende : IS (15 %/25 %) payé par la société, puis PFU (30 %) sur le montant "
                "distribué au dirigeant.",
            ]
        )
        pdf_bytes = generer_pdf_scenario(
            titre="Salaire vs dividende, sur une année",
            sous_titre=f"{forme_juridique} — pour {fmt_euro(montant)} disponibles",
            kpis=[
                (libelle_salaire, fmt_euro(net_salaire)),
                ("Net en poche si dividende", fmt_euro(net_dividende)),
                ("Écart", f"{fmt_euro(ecart)} en faveur de {meilleur}"),
            ],
            lignes_tableau=lignes_pdf,
            hypotheses=hypotheses_pdf,
        )
        st.download_button(
            "Télécharger la synthèse (PDF)",
            data=pdf_bytes,
            file_name=f"synthese_remuneration_{montant}.pdf",
            mime="application/pdf",
            type="primary",
        )

    glossaire_expander(["Assimilé salarié", "TNS", "PASS", "Assiette", "PFU", "IS", "IR", "Abattement"])

# --- Onglet 2 : trajectoire pluriannuelle avec risque ---
with tab2:
    entete_section(
        "Garder l'argent en direct vs le laisser capitaliser dans une holding",
        "Simulation Monte-Carlo, fourchette P10–P90, sur plusieurs années",
    )
    pitch_usage(
        "<strong>Faut-il sortir l'argent de l'entreprise chaque année, ou le laisser "
        "capitaliser dans une holding ?</strong> Sur plusieurs années, la fiscalité et le "
        "rendement du placement changent la donne. Cet onglet compare les deux trajectoires "
        "dans le temps, avec l'incertitude du marché incluse — pas un chiffre unique, une "
        "fourchette réaliste."
    )

    # --- Forme juridique du dirigeant (cohérence avec l'onglet 1) - défini
    # avant l'expander d'hypothèses ci-dessous, qui s'y réfère.
    titre_sous_section("Forme juridique du dirigeant")
    forme_juridique_traj = st.radio(
        "Forme juridique du dirigeant (trajectoire)",
        ["SASU (président, assimilé salarié)", "SARL (gérant majoritaire, TNS)"],
        horizontal=True, label_visibility="collapsed", key="forme_juridique_traj",
    )
    est_sarl_traj = forme_juridique_traj.startswith("SARL")
    if est_sarl_traj:
        st.caption(
            "Chaque distribution (en direct, comme à la sortie finale de la holding) suit le même "
            "régime TNS du gérant majoritaire que sur l'onglet « Rémunération annuelle » - la part "
            "qui dépasse 10 % du capital social + compte courant est réintégrée dans l'assiette des "
            "cotisations sociales (article L131-6 du code de la sécurité sociale)."
        )
        col_cap1_traj, col_cap2_traj = st.columns(2)
        capital_social_traj = col_cap1_traj.number_input(
            "Capital social de la SARL (€)", min_value=1, max_value=5_000_000,
            value=10_000, step=1_000, key="capital_social_traj",
        )
        compte_courant_moyen_traj = col_cap2_traj.number_input(
            "Solde moyen du compte courant d'associé (€, optionnel)", min_value=0, max_value=5_000_000,
            value=0, step=5_000, key="compte_courant_traj",
        )
        seuil_div_traj = seuil_dividendes_sans_cotisations(capital_social_traj, compte_courant_moyen_traj)
        st.caption(f"→ Seuil de dividende non cotisé : {fmt_euro(seuil_div_traj)} par an.")
    else:
        capital_social_traj, compte_courant_moyen_traj = 10_000, 0.0

    with st.expander("Hypothèses de ce scénario (à lire avant de tirer des conclusions)", expanded=True):
        st.markdown(
            "- Le profit annuel avant impôt est supposé constant sur tout l'horizon.\n"
            "- **Scénario direct** : chaque année, le profit est distribué en "
            "dividende (IS puis PFU), le net rejoint un capital personnel "
            "réinvesti ; les gains de ce placement sont eux-mêmes taxés "
            "chaque année au PFU.\n"
            "- **Scénario holding** : le profit reste dans la société, ne "
            "paie que l'IS, et se réinvestit sans frottement fiscal annuel "
            "supplémentaire (hypothèse de capitalisation interne). Tout ne "
            "sort qu'à la fin, en dividende (PFU à la sortie).\n"
            + (
                "- **Gérant majoritaire de SARL (TNS)** : chaque distribution (en direct comme à la "
                "sortie de la holding) applique le même mécanisme de réintégration que sur l'onglet "
                "« Rémunération annuelle » - la part du dividende qui dépasse 10 % du capital social "
                "+ compte courant est cotisée comme un revenu professionnel. La sortie de la holding "
                "est traitée comme une distribution unique l'année de la sortie, pas étalée sur "
                "l'horizon.\n"
                if est_sarl_traj else ""
            )
            + "- Le rendement n'est pas une prévision : la simulation tire des "
            "centaines de trajectoires aléatoires autour d'une moyenne et "
            "d'une volatilité choisies, pour montrer une fourchette de "
            "résultats plutôt qu'un chiffre unique."
        )

    col1, col2 = st.columns(2)
    with col1:
        profit_annuel = st.number_input("Profit annuel réinvesti (€)", min_value=1_000, max_value=500_000, step=1_000, key="profit_input")
        st.caption(f"→ {fmt_euro(profit_annuel)}")
    horizon = col2.slider("Horizon (années)", min_value=2, max_value=25, value=10)

    # Le sélecteur de panier prend toute la largeur de la page : avec 4
    # options ("Prudent", "Équilibré", "Dynamique", "Sur mesure") dans une
    # colonne d'1/3 de largeur, les boutons du segmented_control débordaient
    # et étaient tronqués ("Sur m...", bouton actif coupé à gauche).
    titre_sous_section("Panier de solutions")
    # segmented_control plutôt que selectbox : un vrai groupe de boutons à
    # cliquer, sans champ de saisie où taper un texte libre qui ne
    # correspond à aucune option.
    profil = st.segmented_control(
        "Panier de solutions (hypothèse, pas une recommandation)",
        list(PANIERS.keys()) + ["Sur mesure"],
        default="Prudent",
        label_visibility="collapsed",
    )
    if profil is None:
        profil = "Prudent"

    st.caption(
        "Chaque panier combine les 4 grandes familles de solutions Grand Large Patrimoine (épargne "
        "sécurisée, immobilier, placements financiers, non coté), avec un rendement moyen sourcé par classe."
    )
    avertissement_compliance(
        "Répartition illustrative, pas une grille réelle",
        "La répartition entre classes de chaque panier est une construction pédagogique pour cet outil. "
        "Elle ne reflète PAS l'allocation modèle réelle et confidentielle de Grand Large Patrimoine - "
        "à ne jamais présenter comme telle devant un client ou Pierre.",
    )

    profil_slug = {"Prudent": "prudent", "Équilibré": "equilibre", "Dynamique": "dynamique", "Sur mesure": "sur_mesure"}[profil]

    CLES_CLASSES_ACTIFS = list(CLASSES_ACTIFS.keys())
    rendements_personnalises = None

    if profil == "Sur mesure":
        # Les 4 curseurs sont tous librement déplaçables (contrairement à la
        # version précédente : 3 curseurs libres + un 4e en lecture seule,
        # jugée confuse). Déplacer un curseur réajuste automatiquement les 3
        # autres, proportionnellement à leur poids relatif actuel, pour que
        # la somme reste TOUJOURS exactement 100 % - jamais de dépassement à
        # avertir, jamais de renormalisation silencieuse à expliquer après coup.
        st.caption(
            "Répartition entre les 4 classes d'actifs - déplacez n'importe quel curseur, les trois "
            "autres se réajustent automatiquement pour que la somme reste toujours 100 % :"
        )

        def _cle_session_sm(cle):
            return f"sm_poids_{cle}"

        if _cle_session_sm(CLES_CLASSES_ACTIFS[0]) not in st.session_state:
            valeurs_defaut_sm = {
                "epargne_securisee": 30, "immobilier_non_cote": 30,
                "marches_financiers": 25, "investissements_non_cotes": 15,
            }
            for cle in CLES_CLASSES_ACTIFS:
                st.session_state[_cle_session_sm(cle)] = valeurs_defaut_sm[cle]

        def _rebalancer_sur_mesure(cle_modifiee):
            """Callback on_change : répartit (100 - nouvelle valeur) sur les 3
            autres curseurs, au prorata de leurs poids relatifs actuels, avec
            correction d'arrondi sur le plus grand pour une somme exacte."""
            nouvelle_valeur = st.session_state[_cle_session_sm(cle_modifiee)]
            autres = [c for c in CLES_CLASSES_ACTIFS if c != cle_modifiee]
            valeurs_autres = {c: st.session_state[_cle_session_sm(c)] for c in autres}
            reste_a_distribuer = 100 - nouvelle_valeur
            somme_autres = sum(valeurs_autres.values())
            if somme_autres <= 0:
                part_egale = reste_a_distribuer / len(autres)
                nouvelles_valeurs = {c: part_egale for c in autres}
            else:
                nouvelles_valeurs = {c: valeurs_autres[c] / somme_autres * reste_a_distribuer for c in autres}
            arrondis = {c: int(round(v)) for c, v in nouvelles_valeurs.items()}
            ecart_arrondi = reste_a_distribuer - sum(arrondis.values())
            cle_la_plus_grande = max(arrondis, key=lambda c: arrondis[c])
            arrondis[cle_la_plus_grande] += ecart_arrondi
            for c, v in arrondis.items():
                st.session_state[_cle_session_sm(c)] = max(0, v)

        colonnes_sliders_sm = st.columns(4)
        for col_slider, cle in zip(colonnes_sliders_sm, CLES_CLASSES_ACTIFS):
            col_slider.slider(
                f"{LIBELLES_COURTS_CLASSES_ACTIFS[cle]} (%)", 0, 100,
                key=_cle_session_sm(cle), on_change=_rebalancer_sur_mesure, args=(cle,),
            )

        ponderations = {cle: st.session_state[_cle_session_sm(cle)] / 100 for cle in CLES_CLASSES_ACTIFS}

        with st.expander("Personnaliser aussi les rendements moyens par classe (optionnel)", expanded=False):
            st.caption(
                "Par défaut, chaque classe utilise son rendement moyen sourcé (détail plus bas). Changez "
                "une valeur pour tester votre propre hypothèse - elle n'est alors plus une donnée de "
                "marché sourcée, mais une estimation manuelle que vous assumez."
            )
            rendements_personnalises = {}
            colonnes_rendements_sm = st.columns(4)
            for col_rendement, cle in zip(colonnes_rendements_sm, CLES_CLASSES_ACTIFS):
                classe = CLASSES_ACTIFS[cle]
                rendements_personnalises[cle] = col_rendement.number_input(
                    f"{LIBELLES_COURTS_CLASSES_ACTIFS[cle]} (%)",
                    min_value=-10.0, max_value=30.0,
                    value=round(classe.rendement_moyen * 100, 2),
                    step=0.1, format="%.1f",
                    key=f"sm_rendement_{cle}",
                ) / 100
            rendements_modifies = any(
                abs(rendements_personnalises[cle] - CLASSES_ACTIFS[cle].rendement_moyen) > 0.0005
                for cle in CLES_CLASSES_ACTIFS
            )
            if rendements_modifies:
                st.warning(
                    "Au moins un rendement a été modifié manuellement : ce n'est plus une donnée sourcée, "
                    "mais votre propre hypothèse de travail - à ne jamais présenter comme un chiffre de marché."
                )
    else:
        ponderations = PANIERS[profil]

    resultat_panier = rendement_volatilite_panier(ponderations, rendements_override=rendements_personnalises)
    rendement_moyen = resultat_panier["rendement_moyen"]
    volatilite = resultat_panier["volatilite"]

    titre_sous_section("Composition du panier")
    classes_affichees = [cle for cle in CLES_CLASSES_ACTIFS if ponderations.get(cle, 0) > 0.001]
    fig_panier = go.Figure(
        go.Pie(
            labels=[LIBELLES_COURTS_CLASSES_ACTIFS[cle] for cle in classes_affichees],
            values=[ponderations[cle] * 100 for cle in classes_affichees],
            customdata=[
                f"{(rendements_personnalises or {}).get(cle, CLASSES_ACTIFS[cle].rendement_moyen):.1%}"
                for cle in classes_affichees
            ],
            hole=0.58,
            sort=False,
            marker=dict(
                colors=[COULEURS_CLASSES_ACTIFS[cle] for cle in classes_affichees],
                line=dict(color="#ffffff", width=2),
            ),
            textinfo="percent",
            textfont=dict(family=POLICE_CORPS_GRAPHIQUE, size=13, color="#ffffff"),
            hovertemplate="<b>%{label}</b><br>%{percent} du panier<br>Rendement moyen : %{customdata}<extra></extra>",
        )
    )
    fig_panier.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5,
            font=dict(family=POLICE_CORPS_GRAPHIQUE, size=13, color=ENCRE_SECONDAIRE),
        ),
        margin=dict(t=10, b=10, l=10, r=10),
        height=300,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=POLICE_CORPS_GRAPHIQUE, color=ENCRE_SECONDAIRE),
        modebar=dict(bgcolor="rgba(0,0,0,0)", color=ENCRE_MUTED, activecolor=NAVY),
    )
    # Chiffre central dans le "trou" du donut : le rendement moyen pondéré
    # du panier, pour que ce chiffre saute aux yeux sans survoler le
    # graphique ni lire la légende textuelle en dessous.
    fig_panier.add_annotation(
        text=(
            f"<span style='font-family:{POLICE_TITRE_GRAPHIQUE}; font-size:26px; color:{NAVY};'>"
            f"<b>{rendement_moyen:.1%}</b></span><br>"
            f"<span style='font-family:{POLICE_CORPS_GRAPHIQUE}; font-size:12px; color:{ENCRE_MUTED};'>rendement moyen</span>"
        ),
        showarrow=False, x=0.5, y=0.5,
    )
    st.plotly_chart(fig_panier, width="stretch", config=CONFIG_GRAPHIQUE)

    # Équivalent texte du camembert (accessibilité, et vue "table" pour qui
    # préfère lire des chiffres plutôt qu'une forme).
    libelles_composition = " / ".join(
        f"{poids:.0%} {CLASSES_ACTIFS[cle].libelle}" for cle, poids in ponderations.items() if poids > 0.001
    )
    st.caption(f"Détail : {libelles_composition}")
    st.caption(f"Volatilité du panier : {volatilite:.1%} (approximation prudente, voir note méthodologique ci-dessous).")

    with st.expander("Hypothèses de rendement par classe d'actifs", expanded=False):
        for cle, classe in CLASSES_ACTIFS.items():
            poids_classe = ponderations.get(cle, 0)
            if poids_classe <= 0:
                continue
            rendement_classe = classe.rendement_moyen
            source_rendement = classe.source_rendement
            modifie = False
            if rendements_personnalises and abs(rendements_personnalises.get(cle, rendement_classe) - rendement_classe) > 0.0005:
                rendement_classe = rendements_personnalises[cle]
                source_rendement = "Hypothèse manuelle (modifiée par vous, ce n'est plus une donnée sourcée)"
                modifie = True
            st.markdown(
                f"**{classe.libelle}** — poids {poids_classe:.0%} dans ce panier · "
                f"rendement moyen {rendement_classe:.1%}{' ⚙️ modifié' if modifie else ''} · "
                f"volatilité illustrative {classe.volatilite:.0%}  \n"
                f"Source : {source_rendement}."
                + (f"  \n⚠️ {classe.avertissement}" if classe.avertissement else "")
            )
        st.caption(
            "La volatilité du panier est une simple moyenne pondérée des volatilités par classe, pas un vrai "
            "calcul de variance de portefeuille (il faudrait une matrice de corrélations entre classes). "
            "C'est une approximation prudente : la volatilité réelle d'un portefeuille diversifié est en "
            "général inférieure à cette moyenne (effet de la diversification), jamais supérieure."
        )

    resultat_simu = simulation_comparaison(
        profit_annuel=profit_annuel,
        rendement_moyen=rendement_moyen,
        volatilite=volatilite,
        horizon_annees=horizon,
        nb_simulations=1500,
        graine=42,
        est_sarl=est_sarl_traj,
        capital_social=capital_social_traj,
        compte_courant_moyen=compte_courant_moyen_traj,
    )

    # Comparateur optionnel avec un second panier : pour montrer l'arbitrage
    # risque/rendement directement sur le graphique, sans dupliquer tout le
    # dispositif (profit/horizon restent ceux du panier principal ci-dessus -
    # seuls le rendement moyen et la volatilité changent). Les paniers fixes
    # autres que celui déjà sélectionné comme panier principal, jamais "Sur
    # mesure" (propre à l'utilisateur, pas une référence stable à comparer).
    titre_sous_section("Comparer avec un second panier (optionnel)")
    paniers_comparables = [nom for nom in PANIERS if nom != profil]
    panier_comparaison = st.segmented_control(
        "Comparer avec un second panier",
        ["Aucun"] + paniers_comparables,
        default="Aucun",
        label_visibility="collapsed",
        key="panier_comparaison",
    )
    resultat_simu_cmp = None
    if panier_comparaison and panier_comparaison != "Aucun":
        resultat_panier_cmp = rendement_volatilite_panier(PANIERS[panier_comparaison])
        resultat_simu_cmp = simulation_comparaison(
            profit_annuel=profit_annuel,
            rendement_moyen=resultat_panier_cmp["rendement_moyen"],
            volatilite=resultat_panier_cmp["volatilite"],
            horizon_annees=horizon,
            nb_simulations=1500,
            graine=42,  # même graine : les deux paniers sont comparés sur les mêmes tirages de marché
            est_sarl=est_sarl_traj,
            capital_social=capital_social_traj,
            compte_courant_moyen=compte_courant_moyen_traj,
        )
        st.caption(
            f"Panier « {panier_comparaison} » affiché en tirets, pour comparaison - rendement moyen "
            f"{resultat_panier_cmp['rendement_moyen']:.1%}, volatilité {resultat_panier_cmp['volatilite']:.1%}. "
            f"Seules ses médianes sont affichées (pas sa fourchette P10-P90), pour que le graphique reste lisible."
        )

    annees = list(range(1, horizon + 1))

    valeur_finale_directe = resultat_simu["directe"][50][-1]
    valeur_finale_holding = resultat_simu["holding"][50][-1]
    # Les deux étiquettes de fin de ligne : si les valeurs finales sont trop
    # proches l'une de l'autre, les décaler verticalement pour qu'elles ne se
    # chevauchent pas (sinon illisible quand direct et holding convergent).
    ecart_relatif_final = abs(valeur_finale_holding - valeur_finale_directe) / max(valeur_finale_directe, 1)
    decalage_label = 0 if ecart_relatif_final > 0.04 else (valeur_finale_directe + valeur_finale_holding) * 0.018

    fig2 = go.Figure()
    # Ordre des séries (légende + infobulle unifiée) : la plus forte en fin
    # d'horizon en premier - jamais un ordre de code arbitraire qui peut
    # afficher le scénario le plus faible au-dessus du plus fort et laisser
    # croire à une hiérarchie inversée.
    series_fig2 = [
        {"cle": "directe", "nom": "Direct", "couleur": COULEUR_SALAIRE, "valeur_finale": valeur_finale_directe},
        {"cle": "holding", "nom": "Holding", "couleur": COULEUR_DIVIDENDE, "valeur_finale": valeur_finale_holding},
    ]
    series_fig2.sort(key=lambda s: s["valeur_finale"], reverse=True)
    for serie in series_fig2:
        cle, nom, couleur = serie["cle"], serie["nom"], serie["couleur"]
        # Médiane d'abord (le chiffre qui compte le plus), puis la fourchette
        # P10-P90 juste en dessous dans l'infobulle - avec son propre texte
        # labellisé, plutôt que hoverinfo="skip" qui ne montrait aucun chiffre
        # pour le haut/bas de la fourchette au survol.
        fig2.add_scatter(
            x=annees, y=resultat_simu[cle][50], mode="lines", name=nom, legendgroup=cle,
            line=dict(color=couleur, width=3, shape="spline", smoothing=0.3),
            hovertemplate=f"{nom} (médiane) : %{{y:,.0f}} €<extra></extra>",
        )
        fig2.add_scatter(
            x=annees, y=resultat_simu[cle][90], mode="lines", line=dict(width=0),
            legendgroup=cle, showlegend=False,
            hovertemplate=f"{nom} (optimiste, P90) : %{{y:,.0f}} €<extra></extra>",
        )
        fig2.add_scatter(
            x=annees, y=resultat_simu[cle][10], mode="lines", line=dict(width=0), fill="tonexty",
            fillcolor=rgba_depuis_hex(couleur, 0.12), legendgroup=cle, showlegend=False,
            hovertemplate=f"{nom} (pessimiste, P10) : %{{y:,.0f}} €<extra></extra>",
        )

    # Panier de comparaison (optionnel) : seulement les médianes, en tirets,
    # sans fourchette P10-P90 ni remplissage - sinon 4 bandes superposées
    # rendraient le graphique illisible. Même logique de tri par valeur
    # finale décroissante que pour le panier principal.
    if resultat_simu_cmp is not None:
        series_fig2_cmp = [
            {"cle": "directe", "nom": "Direct", "couleur": COULEUR_SALAIRE, "valeur_finale": resultat_simu_cmp["directe"][50][-1]},
            {"cle": "holding", "nom": "Holding", "couleur": COULEUR_DIVIDENDE, "valeur_finale": resultat_simu_cmp["holding"][50][-1]},
        ]
        series_fig2_cmp.sort(key=lambda s: s["valeur_finale"], reverse=True)
        for serie in series_fig2_cmp:
            cle, nom, couleur = serie["cle"], serie["nom"], serie["couleur"]
            fig2.add_scatter(
                x=annees, y=resultat_simu_cmp[cle][50], mode="lines",
                name=f"{nom} ({panier_comparaison})", legendgroup=f"{cle}_cmp",
                line=dict(color=couleur, width=2, dash="dot", shape="spline", smoothing=0.3),
                hovertemplate=f"{nom} ({panier_comparaison}, médiane) : %{{y:,.0f}} €<extra></extra>",
            )
            fig2.add_scatter(
                x=[horizon], y=[serie["valeur_finale"]], mode="markers+text",
                legendgroup=f"{cle}_cmp", showlegend=False,
                marker=dict(size=7, symbol="diamond", color=couleur, line=dict(color=SURFACE_CARTE, width=1.5)),
                text=[f"  {fmt_euro(serie['valeur_finale'])}"], textposition="middle right",
                textfont=dict(size=12, color=couleur), hoverinfo="skip", cliponaxis=False,
            )

    # Points + étiquettes de valeur en bout de ligne - pour lire le résultat
    # final sans survoler le graphique. legendgroup="directe"/"holding" :
    # indispensable pour qu'isoler une série depuis la légende (groupclick=
    # "togglegroup") masque aussi son étiquette de fin de ligne, pas
    # seulement sa courbe et sa fourchette.
    fig2.add_scatter(
        x=[horizon], y=[valeur_finale_directe], mode="markers+text", legendgroup="directe", showlegend=False,
        marker=dict(size=9, color=COULEUR_SALAIRE, line=dict(color=SURFACE_CARTE, width=2)),
        text=[f"  {fmt_euro(valeur_finale_directe)}"], textposition="middle right",
        textfont=dict(size=14, color=COULEUR_SALAIRE), hoverinfo="skip",
        cliponaxis=False,
    )
    fig2.add_scatter(
        x=[horizon], y=[valeur_finale_holding + decalage_label], mode="markers+text", legendgroup="holding", showlegend=False,
        marker=dict(size=9, color=COULEUR_DIVIDENDE, line=dict(color=SURFACE_CARTE, width=2)),
        text=[f"  {fmt_euro(valeur_finale_holding)}"], textposition="middle right",
        textfont=dict(size=14, color=COULEUR_DIVIDENDE), hoverinfo="skip",
        cliponaxis=False,
    )
    fig2 = _mise_en_forme_graphique(fig2, "Direct vs holding — médiane et fourchette de résultats (P10-P90)", "Net si sortie à cette date (€)")
    fig2.update_xaxes(title="Année", range=[annees[0] - 0.3, horizon + horizon * 0.22])
    fig2.update_layout(margin=dict(r=90))

    resultat_det = comparer(
        profit_annuel, rendement_moyen, horizon,
        est_sarl=est_sarl_traj, capital_social=capital_social_traj, compte_courant_moyen=compte_courant_moyen_traj,
    )
    if resultat_det["annee_croisement"]:
        fig2.add_vline(
            x=resultat_det["annee_croisement"],
            line=dict(color=ENCRE_MUTED, width=1.4, dash="dot"),
            annotation_text=f"  Croisement : année {resultat_det['annee_croisement']}",
            annotation_position="top right" if resultat_det["annee_croisement"] <= horizon / 2 else "top left",
            annotation=dict(font=dict(size=12, color=ENCRE_SECONDAIRE), yshift=-6),
        )

    st.plotly_chart(fig2, width="stretch", config=CONFIG_GRAPHIQUE)
    st.caption(
        "Les zones autour des lignes montrent la fourchette P10-P90 (80 % des trajectoires simulées) - "
        "survolez le graphique pour voir les trois chiffres (médiane, optimiste P90, pessimiste P10) à "
        "n'importe quelle année, ou utilisez la loupe de la barre d'outils pour zoomer sur une période. "
        "La ligne pleine est la médiane, pas une prévision garantie."
    )

    ecart_mediane_final = resultat_simu["holding"][50][-1] - resultat_simu["directe"][50][-1]

    col1, col2 = st.columns(2)
    with col1:
        if resultat_det["annee_croisement"]:
            carte_kpi(
                "Croisement (scénario central, sans aléa)",
                f"Année {resultat_det['annee_croisement']}",
                COULEUR_DIVIDENDE,
                f"À partir de cette année, dans le scénario central (rendement moyen, sans tenir "
                f"compte du hasard), garder l'argent en holding devient plus avantageux que le "
                f"sortir chaque année en direct.",
            )
        else:
            carte_kpi(
                "Croisement (scénario central)", "Aucun", ENCRE_MUTED,
                f"Sur {horizon} ans, dans le scénario central, la holding ne devient jamais plus "
                f"avantageuse que la détention directe — sortir l'argent chaque année reste "
                f"préférable sur cet horizon.",
            )
    with col2:
        faveur = "la holding" if ecart_mediane_final > 0 else "la détention directe"
        carte_kpi(
            "Écart médian en fin d'horizon",
            fmt_euro(ecart_mediane_final, signe=True),
            COULEUR_DIVIDENDE if ecart_mediane_final > 0 else COULEUR_SALAIRE,
            f"Au bout de {horizon} ans, la moitié des trajectoires simulées donnent un résultat "
            f"au moins aussi bon en faveur de {faveur} — ce n'est pas une garantie, juste la "
            f"tendance centrale (voir la fourchette P10-P90 sur le graphique).",
        )

    df_trajectoire = pd.DataFrame(
        {
            "Année": annees,
            "Direct P10": resultat_simu["directe"][10],
            "Direct médiane": resultat_simu["directe"][50],
            "Direct P90": resultat_simu["directe"][90],
            "Holding P10": resultat_simu["holding"][10],
            "Holding médiane": resultat_simu["holding"][50],
            "Holding P90": resultat_simu["holding"][90],
        }
    )
    st.write("")
    col_csv2, col_pdf2 = st.columns(2)
    with col_csv2:
        st.download_button(
            "Télécharger cette trajectoire (CSV)",
            data=df_trajectoire.to_csv(index=False).encode("utf-8"),
            file_name=f"trajectoire_{profil_slug}_{horizon}ans.csv",
            mime="text/csv",
        )
    with col_pdf2:
        annees_cles = sorted(set([1, horizon // 2 or 1, horizon]))
        lignes_pdf_trajectoire = [["Année", "Direct (médiane)", "Holding (médiane)"]] + [
            [
                str(annee),
                fmt_euro(resultat_simu["directe"][50][annee - 1]),
                fmt_euro(resultat_simu["holding"][50][annee - 1]),
            ]
            for annee in annees_cles
        ]

        # Détail par classe d'actifs du panier retenu - même contenu que
        # l'expander "Hypothèses de rendement" de l'interface, pour que la
        # synthèse PDF emportée en rendez-vous tienne seule, sans écran.
        lignes_pdf_classes = [["Classe d'actifs", "Poids", "Rendement moyen", "Source"]]
        for cle_classe, classe in CLASSES_ACTIFS.items():
            poids_classe = ponderations.get(cle_classe, 0)
            if poids_classe <= 0.001:
                continue
            rendement_classe = classe.rendement_moyen
            source_classe = classe.source_rendement
            if rendements_personnalises and abs(rendements_personnalises.get(cle_classe, rendement_classe) - rendement_classe) > 0.0005:
                rendement_classe = rendements_personnalises[cle_classe]
                source_classe = "Hypothèse manuelle (modifiée par l'utilisateur)"
            lignes_pdf_classes.append([
                classe.libelle, f"{poids_classe:.0%}", f"{rendement_classe:.1%}", source_classe,
            ])

        # Image du donut de composition - best-effort : l'export PNG dépend
        # d'un Chrome que kaleido sait trouver (présent sur la plupart des
        # machines, ou téléchargeable via `plotly_get_chrome`). S'il est
        # introuvable, la synthèse PDF reste générée, simplement sans image.
        image_panier_png = None
        try:
            image_panier_png = fig_panier.to_image(format="png", width=420, height=340, scale=2)
        except Exception:
            image_panier_png = None

        pdf_bytes_trajectoire = generer_pdf_scenario(
            titre="Direct vs holding, sur plusieurs années",
            sous_titre=(
                f"Profit annuel {fmt_euro(profit_annuel)} — horizon {horizon} ans — panier {profil} — "
                f"{forme_juridique_traj.split(' (')[0]}"
            ),
            kpis=[
                (
                    "Croisement (scénario central)",
                    f"Année {resultat_det['annee_croisement']}" if resultat_det["annee_croisement"] else "Aucun",
                ),
                ("Écart médian en fin d'horizon", fmt_euro(ecart_mediane_final, signe=True)),
            ],
            lignes_tableau=lignes_pdf_trajectoire,
            image_png=image_panier_png,
            legende_image=(
                f"Composition du panier « {profil} » retenu pour cette simulation - rendement moyen "
                f"pondéré {rendement_moyen:.1%}, volatilité {volatilite:.1%} (répartition illustrative, "
                f"pas la grille réelle de Grand Large Patrimoine)."
            ),
            titre_tableau_secondaire="Détail par classe d'actifs",
            lignes_tableau_secondaire=lignes_pdf_classes,
            hypotheses=[
                "Profit annuel avant impôt supposé constant sur tout l'horizon.",
                "Scénario direct : profit distribué en dividende chaque année (IS puis PFU), "
                "réinvesti et taxé au PFU chaque année sur ses propres gains.",
                "Scénario holding : profit conservé dans la société, ne paie que l'IS, capitalise "
                "sans frottement fiscal annuel supplémentaire ; tout ne sort qu'en fin d'horizon, "
                "en dividende (PFU à la sortie).",
            ] + (
                [
                    f"Gérant majoritaire de SARL (TNS) : chaque distribution au-delà de "
                    f"{fmt_euro(seuil_div_traj)} par an (10 % du capital social + compte courant) est "
                    f"réintégrée dans l'assiette des cotisations sociales, y compris la sortie finale "
                    f"de la holding, traitée comme une distribution unique l'année de la sortie."
                ]
                if est_sarl_traj else []
            ) + [
                "Le rendement n'est pas une prévision : fourchette P10-P90 issue d'une simulation "
                "Monte-Carlo (1500 tirages), pas un chiffre garanti.",
            ],
        )
        st.download_button(
            "Télécharger la synthèse (PDF)",
            data=pdf_bytes_trajectoire,
            file_name=f"synthese_trajectoire_{profil_slug}_{horizon}ans.pdf",
            mime="application/pdf",
            type="primary",
        )

    glossaire_expander(["Holding", "PFU", "IS", "TNS", "Monte-Carlo (simulation)", "P10 / P50 / P90"])

# --- Onglet 3 : démembrement de propriété ---
with tab3:
    entete_section(
        "Donation en pleine propriété vs donation de la nue-propriété",
        "Ligne directe, abattement de 100 000 € disponible — barème de l'article 669 du CGI",
    )
    pitch_usage(
        "<strong>Vous voulez transmettre un bien à vos enfants sans attendre, en limitant "
        "les droits à payer ?</strong> Donner seulement la nue-propriété (et garder "
        "l'usufruit) coûte moins cher en droits de donation que donner le bien en pleine "
        "propriété. Cet onglet chiffre l'économie exacte, selon l'âge du donateur et la "
        "valeur du bien."
    )

    with st.expander("Comment lire ce scénario", expanded=True):
        st.markdown(
            "- **Pleine propriété** : l'enfant reçoit tout, les droits de "
            "donation portent sur la valeur totale du bien.\n"
            "- **Nue-propriété seule** : le parent garde l'usufruit (l'usage "
            "du bien, ou les revenus qu'il génère) jusqu'à son décès ; les "
            "droits de donation ne portent que sur la valeur réduite de la "
            "nue-propriété, qui dépend de l'âge du parent au moment de la "
            "donation (barème fiscal, pas une estimation économique).\n"
            "- **Au décès du parent**, l'usufruit s'éteint et l'enfant devient "
            "plein propriétaire **sans droit supplémentaire** (article 1133 "
            "du CGI).\n"
            "- **L'abattement de 100 000 € est individuel : par parent, et par "
            "enfant** (article 779 du CGI, source service-public.gouv.fr). Un "
            "enfant qui a ses deux parents vivants peut donc recevoir jusqu'à "
            "200 000 € en franchise de droits, et ce total se multiplie par le "
            "nombre d'enfants si le bien leur est transmis à parts égales — "
            "d'où les deux curseurs ci-dessous, qui changent fortement le "
            "résultat.\n"
            "- **Contrepartie** : avec la nue-propriété seule, l'enfant "
            "n'a pas l'usage ou les revenus du bien avant l'extinction de "
            "l'usufruit — ce n'est pas strictement equivalent à une pleine "
            "propriété immédiate, c'est un arbitrage fiscal contre un "
            "arbitrage de jouissance."
        )

    col1, col2 = st.columns(2)
    with col1:
        valeur_bien = st.number_input("Valeur du bien transmis (€, pleine propriété)", min_value=0, max_value=10_000_000, value=400_000, step=10_000)
        st.caption(f"→ {fmt_euro(valeur_bien)}")
    age_donateur = col2.slider("Âge du donateur au moment de la donation", min_value=18, max_value=99, value=65)

    col3, col4 = st.columns(2)
    nombre_enfants = col3.number_input("Nombre d'enfants bénéficiaires (bien transmis à parts égales)", min_value=1, max_value=10, value=1, step=1)
    nombre_donateurs = col4.radio(
        "Donation faite par",
        options=[1, 2],
        format_func=lambda n: "un seul parent" if n == 1 else "les deux parents conjointement",
        horizontal=True,
    )

    resultat_demembrement = comparer_transmission(valeur_bien, age_donateur, nombre_enfants, nombre_donateurs)
    nombre_parts = nombre_enfants * nombre_donateurs
    st.caption(
        f"Abattement total disponible pour cette transmission : {fmt_euro(100_000 * nombre_parts)} "
        f"({nombre_enfants} enfant(s) × {nombre_donateurs} donateur(s) × 100 000 €, renouvelable tous les 15 ans)."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        carte_kpi(
            "Droits si pleine propriété", fmt_euro(resultat_demembrement['droits_pleine_propriete']), COULEUR_SALAIRE,
            "Ce que l'enfant devrait payer à l'État s'il reçoit le bien en pleine propriété, après "
            "abattement.",
        )
    with col2:
        carte_kpi(
            "Droits si nue-propriété seule", fmt_euro(resultat_demembrement['droits_demembrement']), COULEUR_DEMEMBREMENT,
            "Ce que l'enfant devrait payer à l'État s'il ne reçoit que la nue-propriété, le parent "
            "gardant l'usufruit jusqu'à son décès.",
        )
    with col3:
        carte_kpi(
            "Économie de droits",
            fmt_euro(resultat_demembrement['economie_droits']),
            ENCRE_MUTED,
            f"Ce que la famille évite de payer en choisissant la nue-propriété plutôt que la pleine "
            f"propriété (à {age_donateur} ans, l'usufruit représente "
            f"{resultat_demembrement['pourcentage_usufruit']:.0%} de la valeur du bien).",
        )

    st.write("")

    fig3 = go.Figure()
    fig3.add_bar(
        x=["Pleine propriété", "Nue-propriété seule"],
        y=[resultat_demembrement["droits_pleine_propriete"], resultat_demembrement["droits_demembrement"]],
        marker_color=[COULEUR_SALAIRE, COULEUR_DEMEMBREMENT],
        text=[fmt_euro(resultat_demembrement['droits_pleine_propriete']), fmt_euro(resultat_demembrement['droits_demembrement'])],
        textposition="outside", width=0.5,
        hovertemplate="%{x} : %{y:,.0f} €<extra></extra>",
    )
    fig3 = _mise_en_forme_graphique(fig3, f"Droits de donation pour {fmt_euro(valeur_bien)} transmis", "Droits de donation (€)")
    fig3.update_xaxes(showgrid=False)
    fig3.update_yaxes(range=[0, max(resultat_demembrement["droits_pleine_propriete"], resultat_demembrement["droits_demembrement"], 1) * 1.22])
    st.plotly_chart(fig3, width="stretch", config=CONFIG_GRAPHIQUE)

    with st.expander("Voir le barème officiel de l'usufruit (article 669 du CGI)"):
        ages_bareme = list(range(0, 100))
        parts_usufruit = [pourcentage_usufruit(a) * 100 for a in ages_bareme]
        fig_bareme = go.Figure()
        fig_bareme.add_scatter(
            x=ages_bareme, y=parts_usufruit, mode="lines", line=dict(color=COULEUR_DEMEMBREMENT, width=2.5, shape="hv"),
            name="Part usufruit", hovertemplate="%{x} ans : %{y:.0f} %<extra></extra>",
        )
        fig_bareme.add_scatter(
            x=[age_donateur], y=[pourcentage_usufruit(age_donateur) * 100], mode="markers",
            marker=dict(color=NAVY, size=11, line=dict(color="#ffffff", width=1.5)),
            name=f"Donateur ({age_donateur} ans)", hovertemplate="%{x} ans : %{y:.0f} %<extra></extra>",
        )
        fig_bareme = _mise_en_forme_graphique(fig_bareme, "Barème officiel : part de l'usufruit selon l'âge du donateur", "Part usufruit (%)")
        fig_bareme.update_xaxes(title="Âge du donateur")
        fig_bareme.update_yaxes(ticksuffix=" %", tickformat=".0f")
        st.plotly_chart(fig_bareme, width="stretch", config=CONFIG_GRAPHIQUE)
        st.caption(
            "Barème fiscal forfaitaire par tranche d'âge (article 669 du CGI) — ce n'est pas une "
            "estimation économique de la valeur de l'usufruit, qui dépendrait du rendement réel du bien."
        )

    with st.expander("Voir le détail du calcul"):
        df_demembrement = pd.DataFrame(
            {
                "Valeur": [
                    valeur_bien,
                    resultat_demembrement["valeur_usufruit"],
                    resultat_demembrement["valeur_nue_propriete"],
                    100_000 * nombre_parts,
                    resultat_demembrement["droits_pleine_propriete"],
                    resultat_demembrement["droits_demembrement"],
                    resultat_demembrement["economie_droits"],
                ]
            },
            index=[
                "Valeur du bien (pleine propriété)",
                f"Valeur de l'usufruit ({resultat_demembrement['pourcentage_usufruit']:.0%})",
                f"Valeur de la nue-propriété ({1 - resultat_demembrement['pourcentage_usufruit']:.0%})",
                f"Abattement total ({nombre_enfants} enfant(s) × {nombre_donateurs} donateur(s))",
                "Droits si donation en pleine propriété",
                "Droits si donation de la nue-propriété",
                "Économie de droits",
            ],
        )
        st.dataframe(df_demembrement.style.format(fmt_euro), width="stretch")

    col_csv3, col_pdf3 = st.columns(2)
    with col_csv3:
        st.download_button(
            "Télécharger ce scénario (CSV)",
            data=df_demembrement.to_csv().encode("utf-8"),
            file_name=f"demembrement_{valeur_bien}_{nombre_enfants}enf_{age_donateur}ans.csv",
            mime="text/csv",
        )
    with col_pdf3:
        lignes_pdf_demembrement = [["Poste", "Valeur"]] + [
            [str(poste), fmt_euro(valeur)]
            for poste, valeur in zip(df_demembrement.index, df_demembrement["Valeur"])
        ]
        pdf_bytes_demembrement = generer_pdf_scenario(
            titre="Donation en pleine propriété vs donation de la nue-propriété",
            sous_titre=f"Bien de {fmt_euro(valeur_bien)} — donateur de {age_donateur} ans — barème article 669 du CGI",
            kpis=[
                ("Droits si pleine propriété", fmt_euro(resultat_demembrement["droits_pleine_propriete"])),
                ("Droits si nue-propriété seule", fmt_euro(resultat_demembrement["droits_demembrement"])),
                ("Économie de droits", fmt_euro(resultat_demembrement["economie_droits"])),
            ],
            lignes_tableau=lignes_pdf_demembrement,
            hypotheses=[
                "Nue-propriété seule : le parent garde l'usufruit jusqu'à son décès ; les droits de "
                "donation ne portent que sur la valeur réduite de la nue-propriété (barème fiscal "
                "par tranche d'âge, article 669 du CGI).",
                "Au décès du parent, l'usufruit s'éteint sans droit supplémentaire (article 1133 "
                "du CGI).",
                f"Abattement de 100 000 € par parent et par enfant (article 779 du CGI) : "
                f"{fmt_euro(100_000 * nombre_parts)} au total pour {nombre_enfants} enfant(s) et "
                f"{nombre_donateurs} donateur(s).",
                "Avec la nue-propriété seule, l'enfant n'a pas l'usage ou les revenus du bien avant "
                "l'extinction de l'usufruit — un arbitrage fiscal contre un arbitrage de jouissance.",
            ],
        )
        st.download_button(
            "Télécharger la synthèse (PDF)",
            data=pdf_bytes_demembrement,
            file_name=f"synthese_demembrement_{valeur_bien}.pdf",
            mime="application/pdf",
            type="primary",
        )

    glossaire_expander(["Démembrement de propriété", "Usufruit", "Nue-propriété", "Abattement"])

    st.markdown('<hr class="filet">', unsafe_allow_html=True)
    st.markdown("### Transmettre une entreprise : le Pacte Dutreil")
    pitch_usage(
        "<strong>Le client veut transmettre son entreprise à ses enfants, pas un bien "
        "immobilier ou financier ?</strong> Le Pacte Dutreil exonère 75 % de la valeur "
        "transmise avant tout calcul de droits, sous conditions de conservation des titres "
        "et de direction effective. Cet onglet chiffre l'économie - il ne vérifie pas que "
        "les conditions sont réunies."
    )

    col_dut1, col_dut2 = st.columns(2)
    with col_dut1:
        valeur_entreprise = st.number_input(
            "Valeur de l'entreprise transmise (€)", min_value=0, max_value=50_000_000,
            value=2_000_000, step=50_000,
        )
        st.caption(f"→ {fmt_euro(valeur_entreprise)}")
    with col_dut2:
        st.caption(
            f"Répartition réutilisée depuis la transmission de bien ci-dessus : "
            f"{nombre_enfants} enfant(s), {nombre_donateurs} donateur(s) "
            f"({fmt_euro(100_000 * nombre_enfants * nombre_donateurs)} d'abattement total, "
            f"renouvelable tous les 15 ans)."
        )

    resultat_dutreil = calcul_transmission_dutreil(valeur_entreprise, nombre_enfants, nombre_donateurs)

    col_dut_kpi1, col_dut_kpi2, col_dut_kpi3 = st.columns(3)
    with col_dut_kpi1:
        carte_kpi(
            "Droits sans le Pacte Dutreil", fmt_euro(resultat_dutreil["droits_sans_dutreil"]), ENCRE_MUTED,
            "Ce que la famille paierait si l'entreprise était transmise comme un bien ordinaire, sans "
            "aucune exonération particulière.",
        )
    with col_dut_kpi2:
        carte_kpi(
            "Droits avec le Pacte Dutreil", fmt_euro(resultat_dutreil["droits_avec_dutreil"]), COULEUR_DEMEMBREMENT,
            f"Seuls {fmt_euro(resultat_dutreil['valeur_taxable_apres_dutreil'])} restent taxables "
            f"({100 - TAUX_EXONERATION_DUTREIL*100:.0f} % de la valeur), le reste étant exonéré.",
        )
    with col_dut_kpi3:
        carte_kpi(
            "Économie de droits", fmt_euro(resultat_dutreil["economie"]), NAVY,
            f"Ce que le Pacte Dutreil fait économiser à la famille, si les conditions ci-dessous sont "
            f"réunies.",
        )

    fig_dutreil = go.Figure()
    fig_dutreil.add_bar(
        x=["Sans Pacte Dutreil", "Avec Pacte Dutreil"],
        y=[resultat_dutreil["droits_sans_dutreil"], resultat_dutreil["droits_avec_dutreil"]],
        marker_color=[ENCRE_MUTED, COULEUR_DEMEMBREMENT],
        text=[fmt_euro(resultat_dutreil["droits_sans_dutreil"]), fmt_euro(resultat_dutreil["droits_avec_dutreil"])],
        textposition="outside", width=0.5,
        hovertemplate="%{x} : %{y:,.0f} €<extra></extra>",
    )
    fig_dutreil = _mise_en_forme_graphique(
        fig_dutreil, f"Droits de donation pour {fmt_euro(valeur_entreprise)} d'entreprise transmise", "Droits de donation (€)"
    )
    fig_dutreil.update_xaxes(showgrid=False)
    fig_dutreil.update_yaxes(
        range=[0, max(resultat_dutreil["droits_sans_dutreil"], resultat_dutreil["droits_avec_dutreil"], 1) * 1.22]
    )
    st.plotly_chart(fig_dutreil, width="stretch", config=CONFIG_GRAPHIQUE)

    with st.expander("Conditions à vérifier avant toute mise en œuvre", expanded=True):
        st.markdown(
            f"- Seuils de détention pour l'engagement collectif : **"
            f"{SEUILS_ENGAGEMENT_COLLECTIF['non cotée']['droits_financiers']:.0%} des droits financiers et "
            f"{SEUILS_ENGAGEMENT_COLLECTIF['non cotée']['droits_de_vote']:.0%} des droits de vote** pour une "
            f"société non cotée (**"
            f"{SEUILS_ENGAGEMENT_COLLECTIF['cotée']['droits_financiers']:.0%}** et **"
            f"{SEUILS_ENGAGEMENT_COLLECTIF['cotée']['droits_de_vote']:.0%}** si elle est cotée).\n"
            f"- Engagement collectif de conservation : **{DUREE_ENGAGEMENT_COLLECTIF_ANNEES} ans** minimum, "
            f"puis engagement individuel de **{DUREE_ENGAGEMENT_INDIVIDUEL_ANNEES} ans** par donataire "
            f"(ce délai individuel est passé de 4 à 6 ans pour les transmissions à compter du "
            f"21 février 2026 - à vérifier si l'acte est antérieur).\n"
            f"- Fonction de direction exercée par l'un des signataires pendant l'engagement collectif, "
            f"puis par l'un des donataires (ou un signataire) pendant les "
            f"**{DUREE_FONCTION_DIRECTION_APRES_TRANSMISSION_ANNEES} ans** suivant la transmission.\n"
            f"- Un engagement « réputé acquis » dispense de pacte signé si le dirigeant détient seul, ou "
            f"avec son foyer fiscal, les seuils requis depuis plus de 2 ans et exerce depuis plus de "
            f"2 ans une fonction de direction."
        )
        st.caption(
            "Ce module calcule l'économie SI ces conditions sont réunies - il ne les vérifie pas. "
            "Chaque situation doit être validée avec un avocat fiscaliste ou un notaire avant toute "
            "mise en œuvre (article 787 B du CGI)."
        )

    col_csv_dut, col_pdf_dut = st.columns(2)
    df_dutreil = pd.DataFrame(
        {
            "Valeur": [
                resultat_dutreil["valeur_entreprise"],
                resultat_dutreil["valeur_exoneree"],
                resultat_dutreil["valeur_taxable_apres_dutreil"],
                resultat_dutreil["droits_sans_dutreil"],
                resultat_dutreil["droits_avec_dutreil"],
                resultat_dutreil["economie"],
            ]
        },
        index=[
            "Valeur de l'entreprise transmise",
            f"Valeur exonérée ({TAUX_EXONERATION_DUTREIL:.0%})",
            "Valeur taxable après Dutreil",
            "Droits sans le Pacte Dutreil",
            "Droits avec le Pacte Dutreil",
            "Économie de droits",
        ],
    )
    with col_csv_dut:
        st.download_button(
            "Télécharger ce scénario (CSV)",
            data=df_dutreil.to_csv().encode("utf-8"),
            file_name=f"pacte_dutreil_{valeur_entreprise}.csv",
            mime="text/csv",
        )
    with col_pdf_dut:
        lignes_pdf_dutreil = [["Poste", "Valeur"]] + [
            [str(poste), fmt_euro(valeur)] for poste, valeur in zip(df_dutreil.index, df_dutreil["Valeur"])
        ]
        pdf_bytes_dutreil = generer_pdf_scenario(
            titre="Transmission d'entreprise avec le Pacte Dutreil",
            sous_titre=f"Entreprise valorisée {fmt_euro(valeur_entreprise)} — article 787 B du CGI",
            kpis=[
                ("Droits sans le Pacte Dutreil", fmt_euro(resultat_dutreil["droits_sans_dutreil"])),
                ("Droits avec le Pacte Dutreil", fmt_euro(resultat_dutreil["droits_avec_dutreil"])),
                ("Économie de droits", fmt_euro(resultat_dutreil["economie"])),
            ],
            lignes_tableau=lignes_pdf_dutreil,
            hypotheses=[
                f"Exonération de {TAUX_EXONERATION_DUTREIL:.0%} de la valeur transmise, sous conditions "
                f"(article 787 B du CGI) - voir le détail des conditions dans l'outil.",
                "Calcul SI les conditions sont réunies : ce document ne vérifie pas leur respect, à "
                "valider avec un avocat fiscaliste ou un notaire.",
                f"Abattement de 100 000 € par parent et par enfant appliqué sur la valeur résiduelle "
                f"après exonération ({nombre_enfants} enfant(s), {nombre_donateurs} donateur(s)).",
            ],
        )
        st.download_button(
            "Télécharger la synthèse (PDF)",
            data=pdf_bytes_dutreil,
            file_name=f"synthese_dutreil_{valeur_entreprise}.pdf",
            mime="application/pdf",
            type="primary",
        )

    glossaire_expander(["Pacte Dutreil", "Abattement", "Holding"], titre="Glossaire — Pacte Dutreil")


# --- Onglet 4 : succession hors donation (droits selon le lien de parenté) ---
with tab4:
    entete_section(
        "Succession : qui hérite, et combien lui reste-t-il ?",
        "Droits de succession selon le lien de parenté avec le défunt — articles 777, 779 et 796-0 bis du CGI",
    )
    pitch_usage(
        "<strong>Le client se demande ce qu'il resterait à ses proches s'il venait à "
        "disparaître ?</strong> Le lien de parenté change presque tout : le conjoint ne "
        "paie rien, un enfant paie peu après abattement, mais un frère, un neveu ou un "
        "tiers sans lien de parenté peuvent perdre plus de la moitié de ce qu'ils "
        "reçoivent. Cet onglet chiffre l'écart, sur une même masse successorale."
    )

    with st.expander("Comment lire ce calcul", expanded=True):
        st.markdown(
            "- **Conjoint survivant ou partenaire pacsé** : exonération **totale**, quel "
            "que soit le montant (article 796-0 bis du CGI, depuis la loi TEPA de 2007).\n"
            "- **Enfant (ligne directe)** : même barème et même abattement de "
            "**100 000 € par enfant** qu'une donation en ligne directe (article 777 du "
            "CGI) - voir l'onglet « Démembrement de propriété ».\n"
            "- **Frère ou sœur** : abattement de **15 932 €**, puis 35 % jusqu'à "
            "24 430 € de base taxable, 45 % au-delà. Une exonération totale existe sous "
            "conditions cumulatives strictes (célibataire, veuf, divorcé ou séparé de "
            "corps, de plus de 50 ans ou infirme, domicilié avec le défunt depuis plus de "
            "5 ans - article 796-0 ter du CGI) - **non modélisée ici**, à vérifier au cas "
            "par cas.\n"
            "- **Neveu ou nièce** : abattement de **7 967 €**, taux fixe de **55 %**.\n"
            "- **Autre personne sans lien de parenté** (concubin non pacsé, tiers) : "
            "abattement de **1 594 €**, taux fixe de **60 %**.\n"
            "- Ce module ne tient pas compte d'une assurance-vie transmise en parallèle "
            "(voir l'onglet « Assurance-vie »), ni de donations antérieures de moins de "
            "15 ans qui réduiraient l'abattement encore disponible."
        )

    col_suc1, col_suc2 = st.columns(2)
    with col_suc1:
        valeur_succession = st.number_input(
            "Masse successorale à comparer (€)", min_value=0, max_value=20_000_000,
            value=500_000, step=10_000,
        )
        st.caption(f"→ {fmt_euro(valeur_succession)}")
    with col_suc2:
        nombre_enfants_succession = st.number_input(
            "Si elle revient aux enfants, nombre d'enfants (abattement de 100 000€ chacun)",
            min_value=1, max_value=10, value=2, step=1,
        )

    resultats_succession = comparer_liens_parente(valeur_succession, nombre_enfants_succession)

    st.caption(
        "Chaque ligne du graphique suppose que la **totalité** de la masse successorale "
        "revient à ce seul lien de parenté (sauf « Enfant », répartie entre "
        f"{nombre_enfants_succession} enfant(s)) - pour isoler l'effet du lien de parenté, "
        "pas un partage réel entre plusieurs héritiers de rangs différents."
    )

    fig_succession = go.Figure()
    fig_succession.add_bar(
        y=[r["lien"] for r in resultats_succession],
        x=[r["net"] for r in resultats_succession],
        orientation="h",
        marker_color=[NAVY, COULEUR_DEMEMBREMENT, COULEUR_SALAIRE, COULEUR_JAUNE, COULEUR_MAGENTA],
        text=[fmt_euro(r["net"]) for r in resultats_succession],
        textposition="outside",
        hovertemplate="%{y} : net %{x:,.0f} €<extra></extra>",
    )
    fig_succession = _mise_en_forme_graphique(
        fig_succession, f"Net reçu sur {fmt_euro(valeur_succession)} de succession, selon le lien de parenté", ""
    )
    fig_succession.update_yaxes(title=None, showgrid=False)
    fig_succession.update_xaxes(
        title=dict(text="Net reçu (€)", font=dict(family=POLICE_CORPS_GRAPHIQUE, size=13, color=ENCRE_MUTED)),
        range=[0, valeur_succession * 1.22],
    )
    fig_succession.update_layout(height=380)
    st.plotly_chart(fig_succession, width="stretch", config=CONFIG_GRAPHIQUE)

    col_kpi_s1, col_kpi_s2, col_kpi_s3 = st.columns(3)
    conjoint_vs_tiers = next(r for r in resultats_succession if r["lien"] == "Conjoint survivant / partenaire pacsé")
    enfant_vs = next(r for r in resultats_succession if r["lien"] == "Enfant (ligne directe)")
    tiers_vs = next(r for r in resultats_succession if r["lien"] == "Autre (sans lien de parenté)")
    with col_kpi_s1:
        carte_kpi(
            "Conjoint / partenaire pacsé", fmt_euro(conjoint_vs_tiers["net"]), NAVY,
            "Exonération totale - rien n'est prélevé, quel que soit le montant.",
        )
    with col_kpi_s2:
        carte_kpi(
            f"{nombre_enfants_succession} enfant(s)", fmt_euro(enfant_vs["net"]), COULEUR_DEMEMBREMENT,
            f"Taux effectif de {enfant_vs['taux_effectif']:.1%}, après {fmt_euro(100_000 * nombre_enfants_succession)} "
            f"d'abattement cumulé.",
        )
    with col_kpi_s3:
        carte_kpi(
            "Tiers sans lien de parenté", fmt_euro(tiers_vs["net"]), COULEUR_MAGENTA,
            f"Taux effectif de {tiers_vs['taux_effectif']:.1%} - seulement {fmt_euro(ABATTEMENT_TIERS)} d'abattement, "
            f"puis 60 % de taux fixe.",
        )

    with st.expander("Voir le détail du calcul, lien par lien"):
        df_succession = pd.DataFrame(
            {
                "Droits": [r["droits"] for r in resultats_succession],
                "Net reçu": [r["net"] for r in resultats_succession],
                "Taux effectif": [r["taux_effectif"] for r in resultats_succession],
            },
            index=[r["lien"] for r in resultats_succession],
        )
        st.dataframe(
            df_succession.style.format({"Droits": fmt_euro, "Net reçu": fmt_euro, "Taux effectif": "{:.1%}".format}),
            width="stretch",
        )

    col_csv_suc, col_pdf_suc = st.columns(2)
    with col_csv_suc:
        st.download_button(
            "Télécharger ce scénario (CSV)",
            data=df_succession.to_csv().encode("utf-8"),
            file_name=f"succession_{valeur_succession}.csv",
            mime="text/csv",
        )
    with col_pdf_suc:
        lignes_pdf_succession = [["Lien de parenté", "Droits", "Net reçu"]] + [
            [r["lien"], fmt_euro(r["droits"]), fmt_euro(r["net"])] for r in resultats_succession
        ]
        pdf_bytes_succession = generer_pdf_scenario(
            titre="Succession : droits selon le lien de parenté",
            sous_titre=f"Masse successorale de {fmt_euro(valeur_succession)} — articles 777, 779 et 796-0 bis du CGI",
            kpis=[
                ("Conjoint / partenaire pacsé", fmt_euro(conjoint_vs_tiers["net"])),
                (f"{nombre_enfants_succession} enfant(s)", fmt_euro(enfant_vs["net"])),
                ("Tiers sans lien de parenté", fmt_euro(tiers_vs["net"])),
            ],
            lignes_tableau=lignes_pdf_succession,
            hypotheses=[
                "Conjoint survivant ou partenaire pacsé : exonération totale (article 796-0 bis "
                "du CGI), quel que soit le montant hérité.",
                f"Enfant : abattement de 100 000 € par enfant (article 779 du CGI), masse "
                f"répartie ici entre {nombre_enfants_succession} enfant(s).",
                "Frère/sœur : abattement de 15 932 €, puis 35 %/45 % ; neveu/nièce : abattement "
                "de 7 967 €, taux fixe de 55 % ; tiers sans lien de parenté : abattement de "
                "1 594 €, taux fixe de 60 %.",
                "Chaque ligne suppose que la masse successorale entière revient à ce seul lien "
                "de parenté - ne tient pas compte d'un partage réel entre héritiers de rangs "
                "différents, ni d'une assurance-vie ou de donations antérieures transmises en "
                "parallèle.",
            ],
        )
        st.download_button(
            "Télécharger la synthèse (PDF)",
            data=pdf_bytes_succession,
            file_name=f"synthese_succession_{valeur_succession}.pdf",
            mime="application/pdf",
            type="primary",
        )

    glossaire_expander(
        ["Lien de parenté (succession)", "Article 796-0 bis du CGI", "Abattement"],
        titre="Glossaire — Succession",
    )


# --- Onglet 5 : assurance-vie (rachat du vivant, transmission au décès) ---
with tab5:
    entete_section(
        "Assurance-vie : rachat et transmission",
        "Régime du PFU pour les rachats (versements à partir du 27/09/2017) — articles 990 I et 757 B du CGI pour la transmission",
    )
    pitch_usage(
        "<strong>Le client a un contrat d'assurance-vie et veut savoir combien il en reste, "
        "net ?</strong> Que ce soit pour un retrait de son vivant (rachat) ou pour ce que "
        "ses bénéficiaires toucheront à son décès, la fiscalité dépend surtout de deux "
        "choses : l'ancienneté du contrat pour un rachat, l'âge du souscripteur au moment "
        "des versements pour une transmission."
    )

    titre_sous_section("Rachat du vivant")
    with st.expander("Comment lire ce calcul", expanded=True):
        st.markdown(
            "- Seule la **part de gains** (intérêts, plus-values) comprise dans le rachat "
            "est taxée - le capital initialement versé ne l'est jamais, quelle que soit "
            "l'ancienneté.\n"
            "- **17,2 % de prélèvements sociaux** sont toujours dus sur ces gains, sans "
            "aucun abattement.\n"
            "- **Avant 8 ans** : 12,8 % d'impôt sur le revenu (régime du PFU), sans "
            "abattement.\n"
            "- **Après 8 ans** : un abattement annuel de **4 600 €** (personne seule) ou "
            "**9 200 €** (couple marié ou pacsé) s'applique d'abord, puis le taux tombe à "
            "**7,5 %** tant que les versements cumulés sur le contrat restent sous "
            f"**{fmt_euro(SEUIL_VERSEMENTS_TAUX_REDUIT)}** - au-delà, le taux remonte à 12,8 % "
            "sur la part de gains excédant ce seuil de versements.\n"
            "- Ce module couvre les versements effectués à partir du 27/09/2017 (régime "
            "très majoritaire aujourd'hui) - le régime antérieur (PFL dégressif ou option "
            "barème de l'IR) n'est pas modélisé ici."
        )

    col_rachat1, col_rachat2 = st.columns(2)
    with col_rachat1:
        montant_gains_rachat = st.number_input(
            "Part de gains comprise dans le rachat (€)", min_value=0, max_value=5_000_000,
            value=20_000, step=1_000,
        )
        st.caption(f"→ {fmt_euro(montant_gains_rachat)}")
        anciennete_contrat = st.slider("Ancienneté du contrat (années)", min_value=0, max_value=40, value=10)
    with col_rachat2:
        versements_cumules_rachat = st.number_input(
            "Total des versements cumulés sur le contrat (€)", min_value=0, max_value=10_000_000,
            value=100_000, step=10_000,
        )
        st.caption(f"→ {fmt_euro(versements_cumules_rachat)}")
        if anciennete_contrat >= 8:
            abattement_foyer_rachat = st.radio(
                "Abattement annuel (contrat de 8 ans ou plus)", options=[4_600, 9_200],
                format_func=lambda v: f"{fmt_euro(v)} (personne seule)" if v == 4_600 else f"{fmt_euro(v)} (couple marié/pacsé)",
                horizontal=True,
            )
        else:
            abattement_foyer_rachat = 0
            st.radio(
                "Abattement annuel", options=[0], format_func=lambda v: "0 € - aucun abattement avant 8 ans de contrat",
                horizontal=True, disabled=True,
            )

    resultat_rachat = net_apres_rachat(
        montant_gains_rachat, anciennete_contrat, versements_cumules_rachat, abattement_foyer_rachat
    )

    col_kpi_r1, col_kpi_r2, col_kpi_r3 = st.columns(3)
    with col_kpi_r1:
        carte_kpi(
            "Impôt sur le revenu", fmt_euro(resultat_rachat["ir"]), COULEUR_SALAIRE,
            f"Taux de {resultat_rachat['taux_ir_applique']:.1%} appliqué sur "
            f"{fmt_euro(resultat_rachat['base_imposable_ir'])} de base imposable.",
        )
    with col_kpi_r2:
        carte_kpi(
            "Prélèvements sociaux", fmt_euro(resultat_rachat["prelevements_sociaux"]), COULEUR_JAUNE,
            "17,2 % sur la totalité des gains rachetés, sans abattement - toujours dus.",
        )
    with col_kpi_r3:
        carte_kpi(
            "Net perçu sur les gains", fmt_euro(resultat_rachat["net"]), COULEUR_DEMEMBREMENT,
            f"Sur {fmt_euro(montant_gains_rachat)} de gains rachetés "
            f"({resultat_rachat['net'] / montant_gains_rachat:.0%} conservé) - le capital "
            f"versé initialement, lui, n'est jamais taxé."
            if montant_gains_rachat else "Aucun gain racheté - rien à taxer.",
        )

    fig_rachat = go.Figure()
    fig_rachat.add_bar(
        x=["Gains rachetés", "Impôt sur le revenu", "Prélèvements sociaux", "Net perçu"],
        y=[montant_gains_rachat, -resultat_rachat["ir"], -resultat_rachat["prelevements_sociaux"], resultat_rachat["net"]],
        marker_color=[ENCRE_MUTED, COULEUR_SALAIRE, COULEUR_JAUNE, COULEUR_DEMEMBREMENT],
        text=[fmt_euro(v) for v in [montant_gains_rachat, resultat_rachat["ir"], resultat_rachat["prelevements_sociaux"], resultat_rachat["net"]]],
        textposition="outside", width=0.5,
        hovertemplate="%{x} : %{y:,.0f} €<extra></extra>",
    )
    fig_rachat = _mise_en_forme_graphique(fig_rachat, "Décomposition du rachat", "Montant (€)")
    fig_rachat.update_xaxes(showgrid=False)
    st.plotly_chart(fig_rachat, width="stretch", config=CONFIG_GRAPHIQUE)

    st.markdown('<hr class="filet">', unsafe_allow_html=True)
    titre_sous_section("Transmission au décès")
    with st.expander("Comment lire ce calcul", expanded=True):
        st.markdown(
            "- **Versements effectués avant les 70 ans du souscripteur (article 990 I du "
            "CGI)** : abattement de **152 500 €**, individuel, **par bénéficiaire** — "
            "capital et gains compris. Au-delà, 20 % jusqu'à 700 000 € de base taxable, "
            "puis 31,25 %.\n"
            "- **Versements effectués après les 70 ans du souscripteur (article 757 B du "
            "CGI)** : seules les **primes versées** sont taxables (les gains sont "
            "intégralement exonérés), après un abattement de **30 500 €** — celui-ci est "
            "GLOBAL, partagé entre tous les bénéficiaires (et non individuel comme le "
            "990 I). Le solde est ensuite réintégré dans la succession et taxé au même "
            "barème que les droits de succession en ligne directe (voir l'onglet "
            "« Démembrement de propriété »).\n"
            "- C'est **l'âge au moment du VERSEMENT** qui compte, pas l'âge au décès : un "
            "contrat ouvert à 60 ans avec des versements réguliers peut relever des deux "
            "régimes à la fois, contrat par contrat, voire versement par versement.\n"
            "- Ce module traite le contrat isolément, sans l'additionner à d'éventuels "
            "autres biens déjà transmis au même bénéficiaire — il suppose l'abattement de "
            "succession de 100 000 € (article 779 du CGI) encore disponible en totalité."
        )

    col_trans1, col_trans2 = st.columns(2)
    with col_trans1:
        capital_transmis = st.number_input(
            "Capital transmis à ce bénéficiaire (€, versements + gains)", min_value=0, max_value=10_000_000,
            value=400_000, step=10_000,
        )
        st.caption(f"→ {fmt_euro(capital_transmis)}")
        age_versement = st.slider("Âge du souscripteur au moment des versements", min_value=18, max_value=99, value=65)
    with col_trans2:
        if age_versement >= 70:
            part_primes_transmission = st.number_input(
                "Dont part des primes versées (hors gains, €)", min_value=0, max_value=capital_transmis,
                value=min(capital_transmis, int(capital_transmis * 0.85)), step=10_000,
            )
            st.caption(f"→ {fmt_euro(part_primes_transmission)}")
            nombre_beneficiaires_transmission = st.number_input(
                "Nombre de bénéficiaires (abattement de 30 500€ partagé entre eux)",
                min_value=1, max_value=10, value=1, step=1,
            )
        else:
            part_primes_transmission = None
            st.caption(
                f"Abattement de {fmt_euro(ABATTEMENT_990_I_PAR_BENEFICIAIRE)} par bénéficiaire "
                "(article 990 I), indépendant du nombre de bénéficiaires - mais entrez-le quand "
                "même ci-dessous pour voir le total transmis à la famille entière."
            )
            nombre_beneficiaires_transmission = st.number_input(
                "Nombre de bénéficiaires (si le capital ci-dessus est réparti également entre eux)",
                min_value=1, max_value=10, value=1, step=1,
            )

    resultat_transmission = taxation_transmission(
        capital_transmis, age_versement, part_primes_transmission, nombre_beneficiaires_transmission
    )

    col_kpi_t1, col_kpi_t2, col_kpi_t3 = st.columns(3)
    with col_kpi_t1:
        carte_kpi(
            "Régime applicable", resultat_transmission["article"], NAVY,
            f"Versements effectués à {age_versement} ans - "
            + ("avant" if age_versement < 70 else "après") + " les 70 ans du souscripteur.",
        )
    with col_kpi_t2:
        carte_kpi(
            "Prélèvement total", fmt_euro(resultat_transmission["prelevement"]), COULEUR_SALAIRE,
            "Droits dus par ce bénéficiaire sur ce contrat, tous abattements appliqués.",
        )
    with col_kpi_t3:
        carte_kpi(
            "Net pour le bénéficiaire", fmt_euro(resultat_transmission["net_beneficiaire"]), COULEUR_DEMEMBREMENT,
            (f"Sur {fmt_euro(capital_transmis)} transmis "
             f"({resultat_transmission['net_beneficiaire'] / capital_transmis:.0%} conservé).")
            if capital_transmis else "Aucun capital transmis à ce bénéficiaire.",
        )

    if nombre_beneficiaires_transmission > 1:
        net_famille = resultat_transmission["net_beneficiaire"] * nombre_beneficiaires_transmission
        capital_famille = capital_transmis * nombre_beneficiaires_transmission
        st.caption(
            f"Pour les **{nombre_beneficiaires_transmission} bénéficiaires** (si chacun reçoit ce "
            f"même montant) : {fmt_euro(capital_famille)} transmis au total, {fmt_euro(net_famille)} "
            "net au total, une fois les droits de chacun payés."
        )

    fig_transmission = go.Figure()
    fig_transmission.add_bar(
        x=["Capital transmis", "Prélèvement", "Net bénéficiaire"],
        y=[capital_transmis, -resultat_transmission["prelevement"], resultat_transmission["net_beneficiaire"]],
        marker_color=[ENCRE_MUTED, COULEUR_SALAIRE, COULEUR_DEMEMBREMENT],
        text=[fmt_euro(v) for v in [capital_transmis, resultat_transmission["prelevement"], resultat_transmission["net_beneficiaire"]]],
        textposition="outside", width=0.5,
        hovertemplate="%{x} : %{y:,.0f} €<extra></extra>",
    )
    fig_transmission = _mise_en_forme_graphique(
        fig_transmission, f"Transmission par assurance-vie ({resultat_transmission['article']})", "Montant (€)"
    )
    fig_transmission.update_xaxes(showgrid=False)
    st.plotly_chart(fig_transmission, width="stretch", config=CONFIG_GRAPHIQUE)

    col_csv_av, col_pdf_av = st.columns(2)
    df_assurance_vie = pd.DataFrame(
        {
            "Valeur": [
                montant_gains_rachat,
                resultat_rachat["ir"],
                resultat_rachat["prelevements_sociaux"],
                resultat_rachat["net"],
                capital_transmis,
                resultat_transmission["prelevement"],
                resultat_transmission["net_beneficiaire"],
            ]
        },
        index=[
            "Rachat - part de gains rachetée",
            "Rachat - impôt sur le revenu",
            "Rachat - prélèvements sociaux",
            "Rachat - net perçu",
            "Transmission - capital transmis",
            f"Transmission - prélèvement ({resultat_transmission['article']})",
            "Transmission - net bénéficiaire",
        ],
    )
    with col_csv_av:
        st.download_button(
            "Télécharger ce scénario (CSV)",
            data=df_assurance_vie.to_csv().encode("utf-8"),
            file_name=f"assurance_vie_{montant_gains_rachat}_{capital_transmis}.csv",
            mime="text/csv",
        )
    with col_pdf_av:
        lignes_pdf_av = [["Poste", "Valeur"]] + [
            [str(poste), fmt_euro(valeur)] for poste, valeur in zip(df_assurance_vie.index, df_assurance_vie["Valeur"])
        ]
        pdf_bytes_av = generer_pdf_scenario(
            titre="Assurance-vie : rachat et transmission",
            sous_titre=f"Rachat de {fmt_euro(montant_gains_rachat)} de gains ({anciennete_contrat} ans) — transmission de {fmt_euro(capital_transmis)} ({resultat_transmission['article']})",
            kpis=[
                ("Net perçu au rachat", fmt_euro(resultat_rachat["net"])),
                ("Régime de transmission", resultat_transmission["article"]),
                ("Net pour le bénéficiaire", fmt_euro(resultat_transmission["net_beneficiaire"])),
            ],
            lignes_tableau=lignes_pdf_av,
            hypotheses=[
                "Rachat : seule la part de gains est taxée ; régime du PFU pour les versements "
                "à partir du 27/09/2017 (12,8 % avant 8 ans ; 7,5 % après 8 ans sous "
                f"{fmt_euro(SEUIL_VERSEMENTS_TAUX_REDUIT)} de versements cumulés, 12,8 % au-delà) ; "
                "17,2 % de prélèvements sociaux toujours dus, sans abattement.",
                "Transmission : article 990 I du CGI si les versements ont été faits avant les "
                "70 ans du souscripteur (abattement de 152 500 € par bénéficiaire) ; article "
                "757 B si après 70 ans (seules les primes sont taxables, abattement global de "
                "30 500 € partagé entre bénéficiaires, puis barème des droits de succession).",
                "Transmission : ce contrat est traité isolément, sans l'additionner à "
                "d'éventuels autres biens déjà transmis au même bénéficiaire.",
            ],
        )
        st.download_button(
            "Télécharger la synthèse (PDF)",
            data=pdf_bytes_av,
            file_name=f"synthese_assurance_vie_{capital_transmis}.pdf",
            mime="application/pdf",
            type="primary",
        )

    glossaire_expander(
        ["Rachat (assurance-vie)", "PFU (assurance-vie)", "Article 990 I du CGI", "Article 757 B du CGI", "Abattement"],
        titre="Glossaire — Assurance-vie",
    )


# --- Onglet 6 : IFI (impôt sur la fortune immobilière) ---
with tab6:
    entete_section(
        "IFI : patrimoine immobilier et seuil d'assujettissement",
        "Barème progressif, décote et abattement de 30 % sur la résidence principale — articles 964, 973 et 977 du CGI",
    )
    pitch_usage(
        "<strong>Le client a un patrimoine immobilier conséquent et se demande s'il est "
        "assujetti à l'IFI, et pour combien ?</strong> Le seuil (1,3 M€) et le barème "
        "progressif (qui démarre, lui, à 800 000 €) sont deux choses différentes - cet "
        "onglet calcule l'un et l'autre, avec l'abattement de 30 % sur la résidence "
        "principale et la décote qui lisse l'entrée dans l'impôt."
    )

    with st.expander("Comment lire ce calcul", expanded=True):
        st.markdown(
            "- **Seuil d'assujettissement : 1 300 000 €** de patrimoine immobilier net "
            "taxable (article 964 du CGI) - en-dessous, aucun IFI, même pas sur la "
            "fraction au-dessus de 800 000 €.\n"
            "- **Une fois ce seuil franchi**, le barème progressif s'applique dès "
            "**800 001 €** (article 977 du CGI) : 0,5 % jusqu'à 1,3 M€, 0,7 % jusqu'à "
            "2,57 M€, 1 % jusqu'à 5 M€, 1,25 % jusqu'à 10 M€, 1,5 % au-delà.\n"
            "- **Résidence principale** : abattement de **30 %** sur sa valeur (article "
            "973 du CGI) - uniquement si détenue en direct, pas via une SCI. Les autres "
            "biens immobiliers (résidences secondaires, locatifs, parts de SCI non "
            "professionnelle) sont retenus à 100 %.\n"
            "- **Décote** entre 1,3 M€ et 1,4 M€ de patrimoine net taxable : lisse l'effet "
            "de seuil à l'entrée dans l'IFI.\n"
            "- **Biens professionnels** (ex. une holding animatrice où le dirigeant exerce "
            "sa fonction principale) : **exclus de l'assiette**, sous conditions précises "
            "- ce module suppose que ce tri est déjà fait et ne demande que le patrimoine "
            "immobilier NON professionnel.\n"
            "- Ce module ne modélise pas le plafonnement de l'IFI (IFI + IR de l'année "
            "précédente ≤ 75 % des revenus de cette même année, article 979 du CGI), qui "
            "dépend de l'ensemble des revenus du foyer."
        )

    col_ifi1, col_ifi2 = st.columns(2)
    with col_ifi1:
        valeur_residence_ifi = st.number_input(
            "Valeur de la résidence principale (€, détenue en direct)", min_value=0, max_value=20_000_000,
            value=1_200_000, step=50_000,
        )
        st.caption(f"→ {fmt_euro(valeur_residence_ifi)}")
        valeur_autres_biens_ifi = st.number_input(
            "Autres biens immobiliers (€, résidences secondaires, locatifs, parts de SCI non professionnelle)",
            min_value=0, max_value=50_000_000, value=800_000, step=50_000,
        )
        st.caption(f"→ {fmt_euro(valeur_autres_biens_ifi)}")
    with col_ifi2:
        dettes_ifi = st.number_input(
            "Dettes déductibles (€, emprunts immobiliers restant dus...)", min_value=0, max_value=20_000_000,
            value=300_000, step=25_000,
        )
        st.caption(f"→ {fmt_euro(dettes_ifi)}")
        st.caption(
            f"L'abattement de {ABATTEMENT_RESIDENCE_PRINCIPALE:.0%} ne s'applique qu'à la "
            f"résidence principale détenue en direct ; le seuil d'assujettissement est de "
            f"{fmt_euro(SEUIL_ASSUJETTISSEMENT_IFI)}."
        )

    resultat_ifi = synthese_ifi(valeur_residence_ifi, valeur_autres_biens_ifi, dettes_ifi)

    col_kpi_ifi1, col_kpi_ifi2, col_kpi_ifi3 = st.columns(3)
    with col_kpi_ifi1:
        carte_kpi(
            "Patrimoine net taxable", fmt_euro(resultat_ifi["assiette"]), ENCRE_MUTED,
            f"Après abattement de 30 % sur la résidence principale et déduction des dettes - "
            + ("assujetti à l'IFI." if resultat_ifi["assujetti"] else "sous le seuil de 1 300 000 €, pas d'IFI."),
        )
    with col_kpi_ifi2:
        carte_kpi(
            "IFI brut (avant décote)", fmt_euro(resultat_ifi["ifi_brut"]), COULEUR_SALAIRE,
            f"Décote appliquée : {fmt_euro(resultat_ifi['decote'])}." if resultat_ifi["decote"] > 0
            else "Pas de décote (hors de la fourchette 1,3 M€ - 1,4 M€).",
        )
    with col_kpi_ifi3:
        carte_kpi(
            "IFI net dû", fmt_euro(resultat_ifi["ifi_net"]), COULEUR_DEMEMBREMENT,
            "Montant dû au titre de l'IFI, décote déduite.",
        )

    fig_ifi = go.Figure()
    fig_ifi.add_bar(
        x=["Patrimoine net taxable", "IFI brut", "Décote", "IFI net dû"],
        y=[resultat_ifi["assiette"], resultat_ifi["ifi_brut"], -resultat_ifi["decote"], resultat_ifi["ifi_net"]],
        marker_color=[ENCRE_MUTED, COULEUR_SALAIRE, COULEUR_JAUNE, COULEUR_DEMEMBREMENT],
        text=[fmt_euro(v) for v in [resultat_ifi["assiette"], resultat_ifi["ifi_brut"], resultat_ifi["decote"], resultat_ifi["ifi_net"]]],
        textposition="outside", width=0.5,
        hovertemplate="%{x} : %{y:,.0f} €<extra></extra>",
    )
    fig_ifi = _mise_en_forme_graphique(fig_ifi, "Décomposition de l'IFI", "Montant (€)")
    fig_ifi.update_xaxes(showgrid=False)
    st.plotly_chart(fig_ifi, width="stretch", config=CONFIG_GRAPHIQUE)

    with st.expander("Voir le barème officiel (article 977 du CGI)"):
        df_bareme_ifi = pd.DataFrame(
            {"Taux": [f"{taux:.2%}" for _, taux in BAREME_IFI]},
            index=[
                "Jusqu'à 800 000 €", "De 800 001 € à 1 300 000 €", "De 1 300 001 € à 2 570 000 €",
                "De 2 570 001 € à 5 000 000 €", "De 5 000 001 € à 10 000 000 €", "Au-delà de 10 000 000 €",
            ],
        )
        st.dataframe(df_bareme_ifi, width="stretch")

    col_csv_ifi, col_pdf_ifi = st.columns(2)
    df_ifi = pd.DataFrame(
        {
            "Valeur": [
                valeur_residence_ifi, valeur_autres_biens_ifi, dettes_ifi,
                resultat_ifi["assiette"], resultat_ifi["ifi_brut"], resultat_ifi["decote"], resultat_ifi["ifi_net"],
            ]
        },
        index=[
            "Résidence principale (valeur brute)", "Autres biens immobiliers", "Dettes déductibles",
            "Patrimoine net taxable", "IFI brut", "Décote", "IFI net dû",
        ],
    )
    with col_csv_ifi:
        st.download_button(
            "Télécharger ce scénario (CSV)",
            data=df_ifi.to_csv().encode("utf-8"),
            file_name=f"ifi_{int(resultat_ifi['assiette'])}.csv",
            mime="text/csv",
        )
    with col_pdf_ifi:
        lignes_pdf_ifi = [["Poste", "Valeur"]] + [
            [str(poste), fmt_euro(valeur)] for poste, valeur in zip(df_ifi.index, df_ifi["Valeur"])
        ]
        pdf_bytes_ifi = generer_pdf_scenario(
            titre="IFI : patrimoine immobilier et seuil d'assujettissement",
            sous_titre=f"Patrimoine net taxable de {fmt_euro(resultat_ifi['assiette'])} — articles 964, 973 et 977 du CGI",
            kpis=[
                ("Patrimoine net taxable", fmt_euro(resultat_ifi["assiette"])),
                ("IFI brut", fmt_euro(resultat_ifi["ifi_brut"])),
                ("IFI net dû", fmt_euro(resultat_ifi["ifi_net"])),
            ],
            lignes_tableau=lignes_pdf_ifi,
            hypotheses=[
                f"Seuil d'assujettissement de {fmt_euro(SEUIL_ASSUJETTISSEMENT_IFI)} (article 964 du CGI) ; "
                "au-delà, barème progressif à partir de 800 000 € (article 977 du CGI).",
                f"Abattement de {ABATTEMENT_RESIDENCE_PRINCIPALE:.0%} sur la résidence principale détenue en "
                "direct (article 973 du CGI) ; autres biens immobiliers retenus à 100 %.",
                "Décote appliquée entre 1,3 M€ et 1,4 M€ de patrimoine net taxable pour lisser l'entrée dans l'impôt.",
                "Les biens professionnels (ex. holding animatrice) sont supposés déjà exclus du montant saisi - "
                "ce module ne les qualifie pas lui-même.",
                "Le plafonnement de l'IFI (article 979 du CGI, lié aux revenus du foyer) n'est pas modélisé ici.",
            ],
        )
        st.download_button(
            "Télécharger la synthèse (PDF)",
            data=pdf_bytes_ifi,
            file_name=f"synthese_ifi_{int(resultat_ifi['assiette'])}.pdf",
            mime="application/pdf",
            type="primary",
        )

    glossaire_expander(["IFI", "Décote (IFI)", "Biens professionnels (IFI)", "Abattement"], titre="Glossaire — IFI")


# --- Onglet 7 : SCI à l'IS vs à l'IR (détention immobilière en société) ---
with tab7:
    entete_section(
        "SCI : à l'impôt sur le revenu ou à l'impôt sur les sociétés ?",
        "Revenus locatifs annuels et plus-value de cession, cumulés sur la durée de détention",
    )
    pitch_usage(
        "<strong>Le client détient (ou va détenir) un bien locatif en société et hésite entre "
        "l'IR et l'IS ?</strong> L'IS permet d'amortir le bien (moins d'impôt chaque année), mais "
        "perd l'abattement pour durée de détention à la revente et subit une double imposition dès "
        "que l'argent sort vers l'associé. L'IR, c'est l'inverse. Cet onglet cumule les deux effets "
        "sur toute la période de détention."
    )

    with st.expander("Comment lire ce calcul", expanded=True):
        st.markdown(
            "- **SCI à l'IR** (transparente) : les loyers sont taxés chaque année directement chez "
            "l'associé, à son taux marginal d'imposition (TMI) + 17,2 % de prélèvements sociaux - "
            "**pas d'amortissement déductible**. À la revente, la plus-value bénéficie d'un "
            "**abattement pour durée de détention** : exonération totale d'impôt sur le revenu après "
            "**22 ans**, de prélèvements sociaux après **30 ans**.\n"
            "- **SCI à l'IS** : le résultat (loyers moins charges **moins l'amortissement** du bien, "
            "lui déductible) est taxé à l'IS dans la société, puis, si distribué à l'associé, "
            "**re-taxé au PFU** - double imposition. À la revente, **pas d'abattement durée de "
            "détention** : la plus-value se calcule sur la valeur nette comptable (après "
            "amortissements déjà déduits), souvent bien plus élevée pour un bien ancien très amorti.\n"
            "- Ce module suppose un résultat positif chaque année (pas de report de déficit foncier "
            "ou fiscal d'une année sur l'autre), et ne modélise ni la CFE, ni les droits "
            "d'enregistrement de 5 % dus sur une cession de parts de SCI."
        )

    col_sci1, col_sci2 = st.columns(2)
    with col_sci1:
        loyers_sci = st.number_input("Loyers annuels perçus (€)", min_value=0, max_value=1_000_000, value=36_000, step=1_000)
        st.caption(f"→ {fmt_euro(loyers_sci)}")
        charges_sci = st.number_input(
            "Charges déductibles (€/an, intérêts d'emprunt, entretien, taxe foncière, assurance, gestion)",
            min_value=0, max_value=1_000_000, value=8_000, step=500,
        )
        st.caption(f"→ {fmt_euro(charges_sci)}")
        amortissement_sci = st.number_input(
            "Amortissement annuel du bien (€, déductible à l'IS uniquement)", min_value=0, max_value=200_000,
            value=10_000, step=500,
        )
        st.caption(f"→ {fmt_euro(amortissement_sci)}")
        tmi_sci = st.radio(
            "Taux marginal d'imposition du foyer (pour l'IR)", options=[0.0, 0.11, 0.30, 0.41, 0.45],
            format_func=lambda t: f"{t:.0%}", horizontal=True, index=2,
        )
    with col_sci2:
        prix_acquisition_sci = st.number_input("Prix d'acquisition du bien (€)", min_value=0, max_value=20_000_000, value=400_000, step=10_000)
        st.caption(f"→ {fmt_euro(prix_acquisition_sci)}")
        prix_cession_sci = st.number_input("Prix de cession envisagé (€)", min_value=0, max_value=20_000_000, value=600_000, step=10_000)
        st.caption(f"→ {fmt_euro(prix_cession_sci)}")
        annees_detention_sci = st.slider("Durée de détention avant cession (années)", min_value=1, max_value=35, value=15)
        distribue_sci = st.checkbox(
            "SCI à l'IS : distribuer chaque année le résultat (sinon, il capitalise dans la société)",
            value=True,
        )

    resultat_sci = comparer_sci(
        loyers_sci, charges_sci, amortissement_sci, tmi_sci,
        prix_acquisition_sci, prix_cession_sci, annees_detention_sci,
        distribue=distribue_sci,
    )

    col_kpi_sci1, col_kpi_sci2, col_kpi_sci3 = st.columns(3)
    with col_kpi_sci1:
        carte_kpi(
            "Total perçu - SCI à l'IR", fmt_euro(resultat_sci["total_ir"]), COULEUR_SALAIRE,
            f"Revenus cumulés sur {annees_detention_sci} ans ({fmt_euro(resultat_sci['cumul_revenus_ir'])}) "
            f"+ plus-value nette de cession ({fmt_euro(resultat_sci['plus_value_nette_ir'])}).",
        )
    with col_kpi_sci2:
        carte_kpi(
            "Total perçu - SCI à l'IS", fmt_euro(resultat_sci["total_is"]), COULEUR_DEMEMBREMENT,
            f"Revenus cumulés sur {annees_detention_sci} ans ({fmt_euro(resultat_sci['cumul_revenus_is'])}) "
            f"+ plus-value nette de cession ({fmt_euro(resultat_sci['plus_value_nette_is'])}).",
        )
    with col_kpi_sci3:
        ecart_sci = resultat_sci["total_ir"] - resultat_sci["total_is"]
        carte_kpi(
            "Écart IR − IS", fmt_euro(ecart_sci, signe=True), NAVY,
            ("La SCI à l'IR laisse plus au terme, dans ce scénario." if ecart_sci > 0
             else "La SCI à l'IS laisse plus au terme, dans ce scénario." if ecart_sci < 0
             else "Les deux régimes laissent exactement le même total, dans ce scénario."),
        )

    fig_sci = go.Figure()
    fig_sci.add_bar(
        x=["SCI à l'IR", "SCI à l'IS"],
        y=[resultat_sci["cumul_revenus_ir"], resultat_sci["cumul_revenus_is"]],
        name="Revenus cumulés", marker_color=COULEUR_SALAIRE,
        hovertemplate="%{x} : %{y:,.0f} €<extra>Revenus cumulés</extra>",
    )
    fig_sci.add_bar(
        x=["SCI à l'IR", "SCI à l'IS"],
        y=[resultat_sci["plus_value_nette_ir"], resultat_sci["plus_value_nette_is"]],
        name="Plus-value nette de cession", marker_color=COULEUR_DEMEMBREMENT,
        hovertemplate="%{x} : %{y:,.0f} €<extra>Plus-value nette</extra>",
    )
    fig_sci = _mise_en_forme_graphique(
        fig_sci, f"Total perçu sur {annees_detention_sci} ans, IR vs IS", "Montant (€)"
    )
    fig_sci.update_layout(barmode="stack")
    fig_sci.update_xaxes(showgrid=False)
    st.plotly_chart(fig_sci, width="stretch", config=CONFIG_GRAPHIQUE)

    with st.expander("Voir le détail du calcul"):
        df_sci = pd.DataFrame(
            {
                "SCI à l'IR": [resultat_sci["revenu_annuel_ir"], resultat_sci["cumul_revenus_ir"], resultat_sci["plus_value_nette_ir"], resultat_sci["total_ir"]],
                "SCI à l'IS": [resultat_sci["revenu_annuel_is"], resultat_sci["cumul_revenus_is"], resultat_sci["plus_value_nette_is"], resultat_sci["total_is"]],
            },
            index=["Revenu net annuel", f"Revenus cumulés ({annees_detention_sci} ans)", "Plus-value nette de cession", "Total perçu"],
        )
        st.dataframe(df_sci.style.format(fmt_euro), width="stretch")

    col_csv_sci, col_pdf_sci = st.columns(2)
    with col_csv_sci:
        st.download_button(
            "Télécharger ce scénario (CSV)",
            data=df_sci.to_csv().encode("utf-8"),
            file_name=f"sci_{prix_acquisition_sci}_{annees_detention_sci}ans.csv",
            mime="text/csv",
        )
    with col_pdf_sci:
        lignes_pdf_sci = [["Poste", "SCI à l'IR", "SCI à l'IS"]] + [
            [str(poste), fmt_euro(ir), fmt_euro(is_)]
            for poste, ir, is_ in zip(df_sci.index, df_sci["SCI à l'IR"], df_sci["SCI à l'IS"])
        ]
        pdf_bytes_sci = generer_pdf_scenario(
            titre="SCI : à l'impôt sur le revenu ou à l'impôt sur les sociétés ?",
            sous_titre=f"Bien de {fmt_euro(prix_acquisition_sci)}, cédé {fmt_euro(prix_cession_sci)} après {annees_detention_sci} ans de détention",
            kpis=[
                ("Total perçu - SCI à l'IR", fmt_euro(resultat_sci["total_ir"])),
                ("Total perçu - SCI à l'IS", fmt_euro(resultat_sci["total_is"])),
                ("Écart IR − IS", fmt_euro(ecart_sci, signe=True)),
            ],
            lignes_tableau=lignes_pdf_sci,
            hypotheses=[
                "SCI à l'IR : pas d'amortissement déductible, loyers taxés au TMI du foyer + 17,2 % de "
                "prélèvements sociaux ; plus-value avec abattement pour durée de détention (exonération "
                "totale IR après 22 ans, prélèvements sociaux après 30 ans).",
                "SCI à l'IS : amortissement du bien déductible chaque année ; résultat taxé à l'IS puis, "
                "si distribué, re-taxé au PFU - double imposition ; plus-value de cession calculée sur la "
                "valeur nette comptable (après amortissements déjà déduits), sans abattement durée de "
                "détention.",
                "Hypothèse d'un résultat positif chaque année (pas de report de déficit modélisé), hors "
                "CFE et droits d'enregistrement sur cession de parts.",
            ],
        )
        st.download_button(
            "Télécharger la synthèse (PDF)",
            data=pdf_bytes_sci,
            file_name=f"synthese_sci_{prix_acquisition_sci}.pdf",
            mime="application/pdf",
            type="primary",
        )

    glossaire_expander(
        ["SCI", "Amortissement", "Abattement pour durée de détention", "IS", "PFU"],
        titre="Glossaire — SCI",
    )


# --- Onglet 8 : PER (plan d'épargne retraite) - troisième levier de l'arbitrage rémunération ---
with tab8:
    entete_section(
        "PER : verser plutôt que percevoir en net ?",
        "Économie d'impôt immédiate, capitalisation en franchise d'impôt, fiscalité différée à la sortie",
    )
    pitch_usage(
        "<strong>Le dirigeant a déjà arbitré salaire/dividende sur le premier onglet - et s'il en "
        "versait une partie sur un PER plutôt que de l'encaisser en net ?</strong> Le versement "
        "réduit le revenu imposable tout de suite (dans la limite d'un plafond), et le capital brut "
        "fructifie sans frottement fiscal annuel jusqu'à la sortie - où versements et gains sont "
        "alors taxés séparément."
    )

    with st.expander("Comment lire ce calcul", expanded=True):
        st.markdown(
            "- **Plafond de déduction** : 10 % des revenus professionnels nets pour un salarié ou "
            "assimilé salarié (président de SASU), plafonné à 10 % de **8 PASS** ; 10 % du bénéfice "
            "plus 15 % supplémentaires sur la fraction comprise entre 1 et 8 PASS pour un TNS (gérant "
            "majoritaire de SARL) - un plafond structurellement plus généreux.\n"
            "- **À l'entrée** : le montant déductible procure une économie d'impôt immédiate égale à "
            "ce montant multiplié par la TMI actuelle.\n"
            "- **À la sortie en capital** (ce module ne traite pas la sortie en rente) : si les "
            "versements ont été déduits, ils sont réintégrés au revenu imposable et taxés au barème "
            "IR, à la TMI du moment - **sans prélèvements sociaux**. S'ils n'ont pas été déduits, ils "
            "sont totalement exonérés. Les **gains**, eux, sont toujours taxés au **PFU de 31,4 %**, "
            "déduits ou non.\n"
            "- Ce module ne modélise ni la sortie en rente viagère, ni le PER d'entreprise "
            "(abondement employeur, forfait social), ni les cas de déblocage anticipé, ni la "
            "mutualisation des plafonds entre conjoints."
        )

    col_per1, col_per2 = st.columns(2)
    with col_per1:
        statut_per = st.radio(
            "Statut du dirigeant", options=["Assimilé salarié (SASU)", "TNS (SARL, gérant majoritaire)"],
            horizontal=True,
        )
        revenu_per = st.number_input(
            "Revenu professionnel net / bénéfice de l'année (€)", min_value=0, max_value=1_000_000,
            value=70_000, step=1_000,
        )
        st.caption(f"→ {fmt_euro(revenu_per)}")
        if statut_per.startswith("Assimilé"):
            plafond_per = plafond_deduction_salarie(revenu_per)
        else:
            plafond_per = plafond_deduction_tns(revenu_per)
        st.caption(f"Plafond de déduction disponible : **{fmt_euro(plafond_per)}**")
        versement_per = st.number_input(
            "Montant versé sur le PER cette année (€)", min_value=0, max_value=200_000,
            value=min(10_000, int(plafond_per)), step=500,
        )
        st.caption(f"→ {fmt_euro(versement_per)}")
        deduit_per = st.checkbox("Opter pour la déduction fiscale à l'entrée (par défaut)", value=True)
    with col_per2:
        tmi_entree_per = st.radio(
            "TMI actuelle (à l'entrée)", options=[0.11, 0.30, 0.41, 0.45],
            format_func=lambda t: f"{t:.0%}", horizontal=True, index=2,
        )
        tmi_sortie_per = st.radio(
            "TMI anticipée à la sortie (souvent plus basse à la retraite)", options=[0.0, 0.11, 0.30, 0.41, 0.45],
            format_func=lambda t: f"{t:.0%}", horizontal=True, index=1,
        )
        rendement_per = st.slider(
            "Rendement annuel moyen du support (%)", min_value=0.0, max_value=8.0, value=4.0, step=0.5,
        ) / 100
        duree_per = st.slider("Durée avant la sortie (années)", min_value=1, max_value=40, value=20)

    montant_deductible_per = montant_deductible(versement_per, plafond_per)
    if versement_per > plafond_per:
        st.warning(
            f"Le versement dépasse le plafond de déduction disponible : seuls {fmt_euro(montant_deductible_per)} "
            f"sont déductibles, le solde ({fmt_euro(versement_per - montant_deductible_per)}) ne procure aucune "
            "économie d'impôt à l'entrée (mais reste versé sur le PER et bénéficie de la même fiscalité de sortie)."
        )

    resultat_per = comparer_per(
        versement_per, tmi_entree_per, tmi_sortie_per, rendement_per, duree_per,
        deduit=deduit_per,
    )
    economie_per = economie_impot_per(montant_deductible_per, tmi_entree_per) if deduit_per else 0.0

    col_kpi_per1, col_kpi_per2, col_kpi_per3 = st.columns(3)
    with col_kpi_per1:
        carte_kpi(
            "Économie d'impôt immédiate", fmt_euro(economie_per), COULEUR_SALAIRE,
            f"{fmt_euro(montant_deductible_per)} déductibles à {tmi_entree_per:.0%} de TMI." if deduit_per
            else "Option de non-déduction choisie : aucune économie d'impôt à l'entrée.",
        )
    with col_kpi_per2:
        carte_kpi(
            f"Net perçu après {duree_per} ans - avec PER", fmt_euro(resultat_per["net_per"]), COULEUR_DEMEMBREMENT,
            f"Capital brut {fmt_euro(versement_per)} capitalisé à {rendement_per:.1%}/an, "
            f"fiscalité de sortie + économie d'impôt immédiate réinvestie.",
        )
    with col_kpi_per3:
        carte_kpi(
            "Écart vs encaissement net immédiat", fmt_euro(resultat_per["ecart"], signe=True), NAVY,
            ("Le PER laisse plus au terme, dans ce scénario." if resultat_per["ecart"] > 0
             else "Encaisser en net puis placer laisse plus au terme, dans ce scénario." if resultat_per["ecart"] < 0
             else "Les deux options laissent exactement le même total, dans ce scénario."),
        )

    fig_per = go.Figure()
    fig_per.add_bar(
        x=["Avec PER", "Sans PER (net immédiat puis placement)"],
        y=[resultat_per["net_per"], resultat_per["net_sans_per"]],
        marker_color=[COULEUR_DEMEMBREMENT, COULEUR_SALAIRE],
        hovertemplate="%{x} : %{y:,.0f} €<extra></extra>",
    )
    fig_per = _mise_en_forme_graphique(
        fig_per, f"Net perçu après {duree_per} ans, PER vs encaissement immédiat", "Montant net (€)"
    )
    fig_per.update_xaxes(showgrid=False)
    st.plotly_chart(fig_per, width="stretch", config=CONFIG_GRAPHIQUE)

    with st.expander("Voir le détail du calcul"):
        df_per = pd.DataFrame(
            {
                "Avec PER": [
                    versement_per, economie_per, resultat_per["gains_per"],
                    resultat_per["net_per"],
                ],
                "Sans PER": [
                    versement_per * (1 - tmi_entree_per), 0.0, resultat_per["gains_sans_per"],
                    resultat_per["net_sans_per"],
                ],
            },
            index=["Capital investi au départ", "Économie d'impôt immédiate", "Gains générés", "Net perçu après sortie"],
        )
        st.dataframe(df_per.style.format(fmt_euro), width="stretch")

    col_csv_per, col_pdf_per = st.columns(2)
    with col_csv_per:
        st.download_button(
            "Télécharger ce scénario (CSV)",
            data=df_per.to_csv().encode("utf-8"),
            file_name=f"per_{versement_per}_{duree_per}ans.csv",
            mime="text/csv",
        )
    with col_pdf_per:
        lignes_pdf_per = [["Poste", "Avec PER", "Sans PER"]] + [
            [str(poste), fmt_euro(avec), fmt_euro(sans)]
            for poste, avec, sans in zip(df_per.index, df_per["Avec PER"], df_per["Sans PER"])
        ]
        pdf_bytes_per = generer_pdf_scenario(
            titre="PER : verser plutôt que percevoir en net ?",
            sous_titre=f"{fmt_euro(versement_per)} versés, TMI {tmi_entree_per:.0%} → {tmi_sortie_per:.0%}, sur {duree_per} ans",
            kpis=[
                ("Économie d'impôt immédiate", fmt_euro(economie_per)),
                (f"Net perçu après {duree_per} ans - avec PER", fmt_euro(resultat_per["net_per"])),
                ("Écart vs encaissement net immédiat", fmt_euro(resultat_per["ecart"], signe=True)),
            ],
            lignes_tableau=lignes_pdf_per,
            hypotheses=[
                "Plafond de déduction : 10 % des revenus professionnels nets (salarié, max 8 PASS) ou "
                "10 % du bénéfice + 15 % entre 1 et 8 PASS (TNS).",
                "Sortie en capital uniquement (pas de rente viagère) : versements déduits taxés au "
                "barème IR à la TMI de sortie, sans prélèvements sociaux ; gains toujours taxés au PFU "
                "de 31,4 %.",
                "Scénario « sans PER » : encaissement net immédiat au TMI actuel, puis placement au "
                "même rendement avec fiscalité PFU uniquement à la sortie (simplification, pas de "
                "fiscalité annuelle intermédiaire).",
            ],
        )
        st.download_button(
            "Télécharger la synthèse (PDF)",
            data=pdf_bytes_per,
            file_name=f"synthese_per_{versement_per}.pdf",
            mime="application/pdf",
            type="primary",
        )

    glossaire_expander(
        ["PER", "Plafond de déduction (PER)", "TMI", "PFU"],
        titre="Glossaire — PER",
    )


# --- Onglet 9 : veille marchés & produits, calée sur les solutions GLP ---
with tab9:
    entete_section(
        "Note Grand Large",
        "Veille marchés & produits, organisée autour des solutions affichées sur grandlargepatrimoine.fr",
    )
    pitch_usage(
        "<strong>Avant un rendez-vous client, besoin des derniers chiffres "
        "qui parlent directement de ses solutions ?</strong> Cette page les rassemble, sourcés, datés, "
        "classés par solution Grand Large Patrimoine - avec pour chacun une ligne sur ce qu'il change "
        "concrètement en entretien."
    )

    regle = regle_du_jour()
    st.markdown(
        f"""
        <div style="background:#ffffff; border:1px dashed {NAVY}; padding:14px 18px; margin-bottom:1rem;">
            <div style="font-size:0.78rem; color:{ENCRE_MUTED}; text-transform:uppercase;
                        letter-spacing:0.04em; margin-bottom:4px;">Règle fiscale niche du jour</div>
            <div style="font-weight:600; font-size:0.98rem; color:{ENCRE_PRIMAIRE};">{regle['titre']}</div>
            <div style="font-size:0.88rem; color:{ENCRE_SECONDAIRE}; margin-top:4px; line-height:1.45;">{regle['explication']}</div>
            <div style="font-size:0.78rem; color:{ENCRE_MUTED}; margin-top:6px;">Référence : {regle['reference']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_instantane, col_action = st.columns([3, 1])
    with col_instantane:
        st.markdown(
            f"""
            <div style="background:#ffffff; border:1px solid {BORDURE}; border-left:3px solid {NAVY};
                        padding:14px 18px; border-radius:0; font-size:0.92rem;
                        color:{ENCRE_SECONDAIRE}; height:100%;">
                <strong>Instantané du {DATE_MISE_A_JOUR}</strong> — données publiques, sourcées, figées à cette
                date. Pas un flux en direct : chaque chiffre vient d'une source citée, vérifiée à la main.
                Aucun de ces chiffres ne constitue un conseil en investissement ; les acteurs cités sont ceux
                que Grand Large Patrimoine mentionne lui-même sur son site (architecture ouverte, aucun
                produit maison).
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_action:
        st.markdown(
            f"""
            <div style="border:1px dashed {BORDURE}; padding:14px 16px; height:100%;
                        display:flex; flex-direction:column; justify-content:center; text-align:center;">
                <div style="font-size:0.78rem; color:{ENCRE_MUTED}; text-transform:uppercase;
                            letter-spacing:0.04em; margin-bottom:4px;">Pas un flux en direct</div>
                <div style="font-size:0.85rem; color:{ENCRE_SECONDAIRE};">Pour rafraîchir : checklist ci-dessous ↓</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")

    def entete_sous_section(titre, solution_glp, couleur):
        st.markdown(
            f"""
            <div style="margin-top:0.3rem;">
                <div style="width:32px; height:4px; background:{couleur}; margin-bottom:0.5rem;"></div>
                <div style="font-family:'Libre Caslon Display', serif; font-weight:400;
                            font-size:1.55rem; color:{NAVY}; line-height:1.15;">{titre}</div>
                <div style="display:inline-flex; align-items:center; gap:6px; margin-top:0.35rem;
                            font-size:0.82rem; color:{ENCRE_SECONDAIRE};">
                    <span style="width:7px; height:7px; border-radius:50%; background:{couleur};
                                 display:inline-block;"></span>
                    Solution Grand Large Patrimoine concernée : <strong>{solution_glp}</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    for i, section in enumerate(TOUTES_SECTIONS):
        couleur_section = COULEURS_SECTIONS_VEILLE[i % len(COULEURS_SECTIONS_VEILLE)]
        st.markdown('<hr class="filet">', unsafe_allow_html=True)
        entete_sous_section(section.titre, section.solution_glp, couleur_section)
        st.write("")

        for ind in section.indicateurs:
            bordure = COULEUR_ALERTE if not ind.fiable else couleur_section
            etiquette = (
                '<span style="background:#fff4de; color:#6b4a00; font-size:0.72rem; font-weight:600; '
                'padding:2px 8px; border-radius:10px; margin-left:8px; white-space:nowrap;">À RECOUPER AVANT DIFFUSION</span>'
                if not ind.fiable
                else ""
            )
            commentaire_html = (
                f'<div style="font-size:0.85rem; color:{ENCRE_SECONDAIRE}; margin-top:6px; line-height:1.4;">{ind.commentaire}</div>'
                if ind.commentaire
                else ""
            )
            lecture_html = (
                f'<div style="font-size:0.82rem; color:{NAVY}; margin-top:6px; line-height:1.4; font-style:italic;">'
                f'En rendez-vous : {ind.lecture}</div>'
                if ind.lecture
                else ""
            )
            # Tout sur une seule ligne, sans retour à la ligne ni indentation :
            # une ligne blanche (ou seulement des espaces, comme {etiquette} vide)
            # au milieu d'un bloc HTML coupe le bloc pour le parseur Markdown de
            # Streamlit, et le reste s'affiche alors en texte brut échappé.
            carte_html = (
                f'<div style="background:#ffffff; border:1px solid {GRILLE}; '
                f'border-left:3px solid {bordure}; border-radius:0; padding:14px 18px; margin-bottom:10px; '
                f'box-shadow:0 1px 2px rgba(3,0,28,0.03);">'
                f'<div style="display:flex; align-items:center; flex-wrap:wrap; gap:4px;">'
                f'<span style="font-weight:600; font-size:0.95rem; color:{ENCRE_PRIMAIRE};">{ind.libelle}</span>{etiquette}'
                f'</div>'
                f'<div style="font-size:1.4rem; font-family:\'Libre Caslon Display\', serif; '
                f'color:{ENCRE_PRIMAIRE}; margin-top:4px;">{ind.valeur}</div>'
                f'{commentaire_html}'
                f'{lecture_html}'
                f'<div style="font-size:0.78rem; color:{ENCRE_MUTED}; margin-top:8px; border-top:1px solid {GRILLE}; padding-top:6px;">'
                f'Source : {ind.source} — {ind.date_donnee}'
                f'</div>'
                f'</div>'
            )
            st.markdown(carte_html, unsafe_allow_html=True)

        if section.note_methodo:
            st.caption(f"🕒 Fraîcheur des données : {section.note_methodo}")

        st.write("")

    st.markdown('<hr class="filet">', unsafe_allow_html=True)
    st.markdown(
        f'<div style="font-family:\'Libre Caslon Display\', serif; font-weight:400; '
        f'font-size:1.2rem; color:{NAVY}; margin-bottom:0.1rem;">Univers de partenaires cité par Grand Large Patrimoine</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Architecture ouverte : liste de référence relevée sur grandlargepatrimoine.fr, utile pour "
        "resituer un nom entendu en réunion — pas une recommandation ni un classement."
    )
    col_gauche, col_droite = st.columns(2)
    categories = list(UNIVERS_PARTENAIRES.items())
    for i, (categorie, acteurs) in enumerate(categories):
        cible = col_gauche if i % 2 == 0 else col_droite
        with cible:
            st.markdown(
                f'<div class="tuile" style="margin-bottom:0.9rem;">'
                f'<div class="tuile-titre">{categorie}</div>'
                f'<div style="font-size:0.88rem; color:{ENCRE_SECONDAIRE};">{", ".join(acteurs)}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )

    with st.expander("Checklist de rafraîchissement — à suivre avant toute utilisation", expanded=True):
        etapes_numerotees(CHECKLIST_RAFRAICHISSEMENT)

st.markdown('<hr class="filet" style="margin-top:2.5rem;">', unsafe_allow_html=True)
st.caption("Grand Large Patrimoine — simulateur patrimonial, projet réalisé par Antonin Desmazures.")
