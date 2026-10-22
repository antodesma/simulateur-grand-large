"""
Interface Streamlit - Simulateur rémunération dirigeant / holding
Grand Large Patrimoine - projet de stage

Rassemble les modules fiscalite.py, trajectoire.py et simulation.py dans
une interface cliquable. Outil informatif uniquement - voir le bandeau de
non-responsabilité en haut de page.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

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
from simulation import PROFILS, simulation_comparaison
from trajectoire import comparer
from demembrement import comparer_transmission, pourcentage_usufruit
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
from optimisation import repartition_optimale
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
        "Onglet « Note Grand Large » : les chiffres de marché et seuils réglementaires utilisés ailleurs dans l'outil, sourcés et datés.",
        "Dans chaque onglet, les montants se modifient librement — aucun résultat n'est figé, tout se recalcule en direct.",
    ])

tab1, tab2, tab3, tab4 = st.tabs(
    ["Rémunération annuelle", "Trajectoire pluriannuelle", "Démembrement de propriété", "Note Grand Large"]
)

CONFIG_GRAPHIQUE = {"displayModeBar": False}


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
        ),
        margin=dict(t=100, l=10, r=10, b=10),
        hovermode="x unified",
        # Infobulle en carte marine pleine plutôt que le cadre blanc/gris par
        # défaut de Plotly - qui est l'un des signaux les plus "logiciel de
        # calcul" d'un graphique autrement soigné.
        hoverlabel=dict(
            bgcolor=NAVY, bordercolor=NAVY,
            font=dict(family=POLICE_CORPS_GRAPHIQUE, color="#ffffff", size=13),
        ),
        separators=". ",  # convention française : point décimal, espace pour les milliers
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
            "- Le rendement n'est pas une prévision : la simulation tire des "
            "centaines de trajectoires aléatoires autour d'une moyenne et "
            "d'une volatilité choisies, pour montrer une fourchette de "
            "résultats plutôt qu'un chiffre unique."
        )

    col1, col2, col3 = st.columns(3)
    with col1:
        profit_annuel = st.number_input("Profit annuel réinvesti (€)", min_value=1_000, max_value=500_000, step=1_000, key="profit_input")
        st.caption(f"→ {fmt_euro(profit_annuel)}")
    horizon = col2.slider("Horizon (années)", min_value=2, max_value=25, value=10)
    profil = col3.selectbox("Profil de rendement (hypothèse, pas une recommandation)", list(PROFILS.keys()) + ["personnalisé"])

    if profil == "personnalisé":
        rendement_moyen = st.slider("Rendement moyen hypothétique (%)", 0.0, 15.0, 5.0) / 100
        volatilite = st.slider("Volatilité hypothétique (%)", 0.0, 25.0, 8.0) / 100
    else:
        rendement_moyen = PROFILS[profil]["rendement_moyen"]
        volatilite = PROFILS[profil]["volatilite"]
        st.caption(f"Profil {profil} : rendement moyen {rendement_moyen:.0%}, volatilité {volatilite:.0%} (hypothèses illustratives)")

    resultat_simu = simulation_comparaison(
        profit_annuel=profit_annuel,
        rendement_moyen=rendement_moyen,
        volatilite=volatilite,
        horizon_annees=horizon,
        nb_simulations=1500,
        graine=42,
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
    # Bandes P10-P90 : un seul liséré par série dans la légende (le lien
    # entre bande et médiane se fait par la couleur, pas par deux entrées).
    fig2.add_scatter(
        x=annees, y=resultat_simu["holding"][90], mode="lines", line=dict(width=0),
        legendgroup="holding", showlegend=False, hoverinfo="skip",
    )
    fig2.add_scatter(
        x=annees, y=resultat_simu["holding"][10], mode="lines", line=dict(width=0), fill="tonexty",
        fillcolor=rgba_depuis_hex(COULEUR_DIVIDENDE, 0.12), legendgroup="holding", showlegend=False, hoverinfo="skip",
    )
    fig2.add_scatter(
        x=annees, y=resultat_simu["directe"][90], mode="lines", line=dict(width=0),
        legendgroup="direct", showlegend=False, hoverinfo="skip",
    )
    fig2.add_scatter(
        x=annees, y=resultat_simu["directe"][10], mode="lines", line=dict(width=0), fill="tonexty",
        fillcolor=rgba_depuis_hex(COULEUR_SALAIRE, 0.12), legendgroup="direct", showlegend=False, hoverinfo="skip",
    )
    fig2.add_scatter(
        x=annees, y=resultat_simu["directe"][50], mode="lines", name="Direct", legendgroup="direct",
        line=dict(color=COULEUR_SALAIRE, width=3, shape="spline", smoothing=0.3),
        hovertemplate="Direct : %{y:,.0f} €<extra></extra>",
    )
    fig2.add_scatter(
        x=annees, y=resultat_simu["holding"][50], mode="lines", name="Holding", legendgroup="holding",
        line=dict(color=COULEUR_DIVIDENDE, width=3, shape="spline", smoothing=0.3),
        hovertemplate="Holding : %{y:,.0f} €<extra></extra>",
    )
    # Points + étiquettes de valeur en bout de ligne - pour lire le résultat
    # final sans survoler le graphique.
    fig2.add_scatter(
        x=[horizon], y=[valeur_finale_directe], mode="markers+text",
        marker=dict(size=9, color=COULEUR_SALAIRE, line=dict(color=SURFACE_CARTE, width=2)),
        text=[f"  {fmt_euro(valeur_finale_directe)}"], textposition="middle right",
        textfont=dict(size=14, color=COULEUR_SALAIRE), showlegend=False, hoverinfo="skip",
        cliponaxis=False,
    )
    fig2.add_scatter(
        x=[horizon], y=[valeur_finale_holding + decalage_label], mode="markers+text",
        marker=dict(size=9, color=COULEUR_DIVIDENDE, line=dict(color=SURFACE_CARTE, width=2)),
        text=[f"  {fmt_euro(valeur_finale_holding)}"], textposition="middle right",
        textfont=dict(size=14, color=COULEUR_DIVIDENDE), showlegend=False, hoverinfo="skip",
        cliponaxis=False,
    )
    fig2 = _mise_en_forme_graphique(fig2, "Direct vs holding — médiane et fourchette de résultats (P10-P90)", "Net si sortie à cette date (€)")
    fig2.update_xaxes(title="Année", range=[annees[0] - 0.3, horizon + horizon * 0.22])
    fig2.update_layout(margin=dict(r=90))

    resultat_det = comparer(profit_annuel, rendement_moyen, horizon)
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
        "la ligne pleine est la médiane, pas une prévision garantie."
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
            file_name=f"trajectoire_{profil}_{horizon}ans.csv",
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
        pdf_bytes_trajectoire = generer_pdf_scenario(
            titre="Direct vs holding, sur plusieurs années",
            sous_titre=f"Profit annuel {fmt_euro(profit_annuel)} — horizon {horizon} ans — profil {profil}",
            kpis=[
                (
                    "Croisement (scénario central)",
                    f"Année {resultat_det['annee_croisement']}" if resultat_det["annee_croisement"] else "Aucun",
                ),
                ("Écart médian en fin d'horizon", fmt_euro(ecart_mediane_final, signe=True)),
            ],
            lignes_tableau=lignes_pdf_trajectoire,
            hypotheses=[
                "Profit annuel avant impôt supposé constant sur tout l'horizon.",
                "Scénario direct : profit distribué en dividende chaque année (IS puis PFU), "
                "réinvesti et taxé au PFU chaque année sur ses propres gains.",
                "Scénario holding : profit conservé dans la société, ne paie que l'IS, capitalise "
                "sans frottement fiscal annuel supplémentaire ; tout ne sort qu'en fin d'horizon, "
                "en dividende (PFU à la sortie).",
                "Le rendement n'est pas une prévision : fourchette P10-P90 issue d'une simulation "
                "Monte-Carlo (1500 tirages), pas un chiffre garanti.",
            ],
        )
        st.download_button(
            "Télécharger la synthèse (PDF)",
            data=pdf_bytes_trajectoire,
            file_name=f"synthese_trajectoire_{profil}_{horizon}ans.pdf",
            mime="application/pdf",
            type="primary",
        )

    glossaire_expander(["Holding", "PFU", "IS", "Monte-Carlo (simulation)", "P10 / P50 / P90"])

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


# --- Onglet 4 : veille marchés & produits, calée sur les solutions GLP ---
with tab4:
    entete_section(
        "Note Grand Large",
        "Veille marchés & produits, organisée autour des solutions affichées sur grandlargepatrimoine.fr",
    )
    pitch_usage(
        "<strong>Avant un rendez-vous client ou un point avec Pierre, besoin des derniers chiffres "
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
