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

COULEUR_SALAIRE = "#2a78d6"    # slot catégoriel 1 - bleu
COULEUR_DIVIDENDE = "#eb6834"  # slot catégoriel 2 - orange
COULEUR_DEMEMBREMENT = "#1baf7a"  # slot catégoriel 3 - aqua
ENCRE_PRIMAIRE = NAVY
ENCRE_SECONDAIRE = "#4a4860"
ENCRE_MUTED = "#8b899c"
GRILLE = "#e7e5dd"
SURFACE = "#fcfcfb"
SURFACE_CARTE = "#ffffff"
BORDURE = "rgba(3,0,28,0.10)"

# --- Profils clients illustratifs (typologies affichées par Grand Large   ---
# --- Patrimoine sur leur site : dirigeants en cession, familles           ---
# --- patrimoniales, professions libérales). Chiffres d'exemple, aucune    ---
# --- donnée réelle de client - juste pour pré-remplir une démo cohérente. ---
PROFILS_CLIENT = {
    "Dirigeant en cession": {"montant": 300_000, "profit_annuel": 80_000},
    "Famille patrimoniale": {"montant": 80_000, "profit_annuel": 50_000},
    "Profession libérale": {"montant": 60_000, "profit_annuel": 35_000},
}

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

    .block-container {{ padding-top: 2rem; max-width: 1150px; }}

    .bandeau {{
        background: linear-gradient(120deg, {NAVY} 0%, {NAVY_HOVER} 100%);
        border-radius: 4px;
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
        background: {CREME};
        border: 1px solid {BORDURE};
        border-left: 3px solid {NAVY};
        border-radius: 4px;
        padding: 0.85rem 1.1rem;
        color: {ENCRE_SECONDAIRE};
        font-size: 0.88rem;
        margin-bottom: 1.3rem;
    }}

    .carte-kpi {{
        background: {SURFACE_CARTE};
        border: 1px solid {BORDURE};
        border-radius: 4px;
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
        color: {ENCRE_MUTED};
        font-size: 0.78rem;
        margin-top: 0.25rem;
    }}

    section[data-testid="stSidebar"] {{
        background: {CREME};
        border-right: 1px solid {BORDURE};
    }}
    section[data-testid="stSidebar"] h3 {{
        font-family: 'Libre Caslon Display', serif;
        font-weight: 400;
        color: {NAVY};
    }}

    [data-testid="stMetricValue"] {{ font-variant-numeric: tabular-nums; }}

    h2, h3 {{ color: {ENCRE_PRIMAIRE}; font-family: 'Libre Caslon Display', serif; font-weight: 400; }}

    .stTabs [data-baseweb="tab"] {{ font-weight: 500; }}
    .stTabs [aria-selected="true"] {{ color: {NAVY} !important; }}
    .stTabs [data-baseweb="tab-highlight"] {{ background-color: {NAVY} !important; }}

    .stButton button, .stDownloadButton button {{
        border-radius: 3px;
        border-color: {NAVY};
        color: {NAVY};
    }}
    .stButton button:hover, .stDownloadButton button:hover {{
        background-color: {NAVY};
        color: #ffffff;
        border-color: {NAVY};
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


def fmt_euro(montant):
    """Formate un montant en euros à la française : espace comme séparateur
    de milliers (40 288 €), pas de virgule anglo-saxonne (40,288 €)."""
    return f"{montant:,.0f} €".replace(",", " ")


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


def _appliquer_profil_client():
    choix = st.session_state["persona_select"]
    if choix in PROFILS_CLIENT:
        st.session_state["montant_input"] = PROFILS_CLIENT[choix]["montant"]
        st.session_state["profit_input"] = PROFILS_CLIENT[choix]["profit_annuel"]


if "montant_input" not in st.session_state:
    st.session_state["montant_input"] = 80_000
if "profit_input" not in st.session_state:
    st.session_state["profit_input"] = 50_000

with st.sidebar:
    st.markdown("### Grand Large Patrimoine")
    st.caption("Outil de simulation patrimoniale — projet de stage")
    st.markdown("---")
    st.selectbox(
        "Profil client (pré-remplit les montants)",
        ["Personnalisé"] + list(PROFILS_CLIENT.keys()),
        key="persona_select",
        on_change=_appliquer_profil_client,
    )
    st.caption("Archétypes illustratifs, calés sur les typologies affichées par Grand Large Patrimoine — aucune donnée réelle de client.")
    st.markdown("---")
    st.markdown(
        "**Ce que fait l'outil**\n\n"
        "Compare, pour un dirigeant de société, différentes façons de "
        "sortir ou de conserver de l'argent dans l'entreprise — et montre "
        "l'effet du temps et du risque sur ces choix.\n\n"
        "**Ce que l'outil ne fait pas**\n\n"
        "Il ne recommande aucune décision, aucun produit, aucun montant. "
        "Chaque hypothèse est affichée et modifiable."
    )
    st.markdown("---")
    st.caption("Projet réalisé par Antonin Desmazures")

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

tab1, tab2, tab3, tab4 = st.tabs(
    ["Rémunération annuelle", "Trajectoire pluriannuelle", "Démembrement de propriété", "Note Grand Large"]
)

CONFIG_GRAPHIQUE = {"displayModeBar": False}


def _mise_en_forme_graphique(fig, titre, y_titre):
    fig.update_layout(
        title=dict(text=titre, font=dict(size=16, color=ENCRE_PRIMAIRE)),
        plot_bgcolor=SURFACE_CARTE,
        paper_bgcolor=SURFACE_CARTE,
        font=dict(color=ENCRE_SECONDAIRE, size=13),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(color=ENCRE_SECONDAIRE)),
        margin=dict(t=70, l=10, r=10, b=10),
        hovermode="x unified",
        separators=". ",  # convention française : point décimal, espace pour les milliers
    )
    fig.update_yaxes(title=y_titre, gridcolor=GRILLE, zeroline=False, tickformat=",.0f", ticksuffix=" €")
    fig.update_xaxes(gridcolor=GRILLE, zeroline=False)
    return fig


# --- Onglet 1 : comparaison simple salaire vs dividende sur une année ---
with tab1:
    st.subheader("Salaire vs dividende, sur une année")
    st.caption(
        "Hypothèse : dirigeant de SASU, assimilé salarié, part fiscale unique "
        "(célibataire sans enfant, pas d'autre revenu). Barèmes 2026 (revenus 2025)."
    )

    montant = st.number_input(
        "Montant disponible dans l'entreprise (€, coût total avant répartition)",
        min_value=0, max_value=1_000_000, step=5_000, key="montant_input",
    )

    net_salaire = net_apres_salaire(montant)
    net_dividende = net_apres_dividende(montant)
    meilleur = "le salaire" if net_salaire > net_dividende else "le dividende"
    ecart = abs(net_salaire - net_dividende)

    col1, col2, col3 = st.columns(3)
    with col1:
        carte_kpi("Net en poche si salaire", fmt_euro(net_salaire), COULEUR_SALAIRE)
    with col2:
        carte_kpi("Net en poche si dividende", fmt_euro(net_dividende), COULEUR_DIVIDENDE)
    with col3:
        carte_kpi("Écart", fmt_euro(ecart), ENCRE_MUTED, f"en faveur de {meilleur}")

    st.write("")

    fig1 = go.Figure()
    fig1.add_bar(
        x=["Salaire", "Dividende"], y=[net_salaire, net_dividende],
        marker_color=[COULEUR_SALAIRE, COULEUR_DIVIDENDE],
        text=[fmt_euro(net_salaire), fmt_euro(net_dividende)],
        textposition="outside", width=0.5,
        hovertemplate="%{x} : %{y:,.0f} €<extra></extra>",
    )
    fig1 = _mise_en_forme_graphique(fig1, f"Pour {fmt_euro(montant)} disponibles", "Net en poche (€)")
    fig1.update_xaxes(showgrid=False)
    st.plotly_chart(fig1, width="stretch", config=CONFIG_GRAPHIQUE)

    brut = brut_depuis_cout_total(montant)
    charges_employeur, charges_salarie = charges_sur_brut(brut)
    net_avant_abattement = brut - charges_salarie
    net_imposable = applique_abattement_salaire(net_avant_abattement)
    abattement = net_avant_abattement - net_imposable
    ir_salaire = calcul_ir(net_imposable)

    is_du = calcul_is(montant)
    distribuable = montant - is_du
    pfu_montant = distribuable * TAUX_PFU

    with st.expander("Voir la cascade du calcul (du coût total entreprise au net en poche)", expanded=False):
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

    st.download_button(
        "Télécharger ce scénario (CSV)",
        data=df_detail.to_csv().encode("utf-8"),
        file_name=f"scenario_remuneration_{montant}.csv",
        mime="text/csv",
    )

# --- Onglet 2 : trajectoire pluriannuelle avec risque ---
with tab2:
    st.subheader("Garder l'argent en direct vs le laisser capitaliser dans une holding")

    with st.expander("Hypothèses de ce scénario (à lire avant de tirer des conclusions)"):
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
    profit_annuel = col1.number_input("Profit annuel réinvesti (€)", min_value=1_000, max_value=500_000, step=1_000, key="profit_input")
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

    fig2 = go.Figure()
    fig2.add_scatter(x=annees, y=resultat_simu["holding"][90], mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip")
    fig2.add_scatter(x=annees, y=resultat_simu["holding"][10], mode="lines", line=dict(width=0), fill="tonexty",
                      fillcolor="rgba(235,104,52,0.15)", name="Holding (P10-P90)", hoverinfo="skip")
    fig2.add_scatter(x=annees, y=resultat_simu["directe"][90], mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip")
    fig2.add_scatter(x=annees, y=resultat_simu["directe"][10], mode="lines", line=dict(width=0), fill="tonexty",
                      fillcolor="rgba(42,120,214,0.15)", name="Direct (P10-P90)", hoverinfo="skip")
    fig2.add_scatter(x=annees, y=resultat_simu["directe"][50], mode="lines", name="Direct (médiane)",
                      line=dict(color=COULEUR_SALAIRE, width=2.5), hovertemplate="Direct : %{y:,.0f} €<extra></extra>")
    fig2.add_scatter(x=annees, y=resultat_simu["holding"][50], mode="lines", name="Holding (médiane)",
                      line=dict(color=COULEUR_DIVIDENDE, width=2.5), hovertemplate="Holding : %{y:,.0f} €<extra></extra>")
    fig2 = _mise_en_forme_graphique(fig2, "Direct vs holding — médiane et fourchette de résultats (P10-P90)", "Net si sortie à cette date (€)")
    fig2.update_xaxes(title="Année")

    resultat_det = comparer(profit_annuel, rendement_moyen, horizon)
    if resultat_det["annee_croisement"]:
        fig2.add_vline(
            x=resultat_det["annee_croisement"],
            line=dict(color=ENCRE_MUTED, width=1.4, dash="dot"),
            annotation_text=f"  Croisement (scénario central) : année {resultat_det['annee_croisement']}",
            annotation_position="top",
            annotation=dict(font=dict(size=11, color=ENCRE_SECONDAIRE)),
        )

    st.plotly_chart(fig2, width="stretch", config=CONFIG_GRAPHIQUE)

    ecart_mediane_final = resultat_simu["holding"][50][-1] - resultat_simu["directe"][50][-1]

    col1, col2 = st.columns(2)
    with col1:
        if resultat_det["annee_croisement"]:
            carte_kpi(
                "Croisement (scénario central, sans aléa)",
                f"Année {resultat_det['annee_croisement']}",
                COULEUR_DIVIDENDE,
                "la holding dépasse le direct à partir de cette année",
            )
        else:
            carte_kpi("Croisement (scénario central)", "Aucun", ENCRE_MUTED, "la holding ne dépasse pas le direct sur cet horizon")
    with col2:
        carte_kpi(
            "Écart médian en fin d'horizon",
            f"{ecart_mediane_final:+,.0f} €",
            COULEUR_DIVIDENDE if ecart_mediane_final > 0 else COULEUR_SALAIRE,
            f"en faveur de {'la holding' if ecart_mediane_final > 0 else 'la détention directe'} — jamais garanti (voir P10-P90)",
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
    st.download_button(
        "Télécharger cette trajectoire (CSV)",
        data=df_trajectoire.to_csv(index=False).encode("utf-8"),
        file_name=f"trajectoire_{profil}_{horizon}ans.csv",
        mime="text/csv",
    )

# --- Onglet 3 : démembrement de propriété ---
with tab3:
    st.subheader("Donation en pleine propriété vs donation de la nue-propriété")
    st.caption(
        "Hypothèse : donation en ligne directe (parent → enfant), abattement de "
        "100 000 € non consommé par une donation antérieure de moins de 15 ans. "
        "Barème de l'article 669 du CGI (source BOFiP)."
    )

    with st.expander("Comment lire ce scénario"):
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
            "- **Contrepartie** : avec la nue-propriété seule, l'enfant "
            "n'a pas l'usage ou les revenus du bien avant l'extinction de "
            "l'usufruit — ce n'est pas strictement equivalent à une pleine "
            "propriété immédiate, c'est un arbitrage fiscal contre un "
            "arbitrage de jouissance."
        )

    col1, col2 = st.columns(2)
    valeur_bien = col1.number_input("Valeur du bien transmis (€, pleine propriété)", min_value=0, max_value=10_000_000, value=400_000, step=10_000)
    age_donateur = col2.slider("Âge du donateur au moment de la donation", min_value=18, max_value=99, value=65)

    resultat_demembrement = comparer_transmission(valeur_bien, age_donateur)

    col1, col2, col3 = st.columns(3)
    with col1:
        carte_kpi("Droits si pleine propriété", fmt_euro(resultat_demembrement['droits_pleine_propriete']), COULEUR_SALAIRE)
    with col2:
        carte_kpi("Droits si nue-propriété seule", fmt_euro(resultat_demembrement['droits_demembrement']), COULEUR_DEMEMBREMENT)
    with col3:
        carte_kpi(
            "Économie de droits",
            fmt_euro(resultat_demembrement['economie_droits']),
            ENCRE_MUTED,
            f"part usufruit à {age_donateur} ans : {resultat_demembrement['pourcentage_usufruit']:.0%}",
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
                    resultat_demembrement["droits_pleine_propriete"],
                    resultat_demembrement["droits_demembrement"],
                    resultat_demembrement["economie_droits"],
                ]
            },
            index=[
                "Valeur du bien (pleine propriété)",
                f"Valeur de l'usufruit ({resultat_demembrement['pourcentage_usufruit']:.0%})",
                f"Valeur de la nue-propriété ({1 - resultat_demembrement['pourcentage_usufruit']:.0%})",
                "Droits si donation en pleine propriété",
                "Droits si donation de la nue-propriété",
                "Économie de droits",
            ],
        )
        st.dataframe(df_demembrement.style.format(fmt_euro), width="stretch")

    st.download_button(
        "Télécharger ce scénario (CSV)",
        data=df_demembrement.to_csv().encode("utf-8"),
        file_name=f"demembrement_{valeur_bien}_{age_donateur}ans.csv",
        mime="text/csv",
    )


# --- Onglet 4 : veille marchés & produits, calée sur les solutions GLP ---
with tab4:
    st.subheader("Note Grand Large — veille marchés & produits")
    st.caption(
        "Indicateurs de marché et seuils réglementaires organisés autour des solutions affichées sur "
        "grandlargepatrimoine.fr, pour une veille qui parle directement le langage de leurs métiers."
    )

    st.markdown(
        f"""
        <div style="background:{CREME}; border-left:4px solid {NAVY}; padding:14px 18px;
                    border-radius:6px; margin-bottom:18px; font-size:0.92rem; color:{ENCRE_SECONDAIRE};">
            <strong>Instantané du {DATE_MISE_A_JOUR}</strong> — données publiques, sourcées, figées à cette
            date. Pas un flux en direct : voir la checklist de rafraîchissement en bas de page avant toute
            réutilisation. Aucun de ces chiffres ne constitue un conseil en investissement ; les acteurs
            cités sont ceux que Grand Large Patrimoine mentionne lui-même sur son site (architecture
            ouverte, aucun produit maison).
        </div>
        """,
        unsafe_allow_html=True,
    )

    COULEUR_ALERTE = "#fab219"  # accent uniquement (texte en noir dessus pour le contraste) - cf. skill dataviz

    for section in TOUTES_SECTIONS:
        st.markdown(f"#### {section.titre}")
        st.caption(f"Solution Grand Large Patrimoine concernée : {section.solution_glp}")

        for ind in section.indicateurs:
            bordure = COULEUR_ALERTE if not ind.fiable else GRILLE
            etiquette = (
                '<span style="background:#fff4de; color:#6b4a00; font-size:0.72rem; font-weight:600; '
                'padding:2px 8px; border-radius:10px; margin-left:8px;">À RECOUPER AVANT DIFFUSION</span>'
                if not ind.fiable
                else ""
            )
            commentaire_html = (
                f'<div style="font-size:0.85rem; color:{ENCRE_SECONDAIRE}; margin-top:4px;">{ind.commentaire}</div>'
                if ind.commentaire
                else ""
            )
            # Tout sur une seule ligne, sans retour à la ligne ni indentation :
            # une ligne blanche (ou seulement des espaces, comme {etiquette} vide)
            # au milieu d'un bloc HTML coupe le bloc pour le parseur Markdown de
            # Streamlit, et le reste s'affiche alors en texte brut échappé.
            carte_html = (
                f'<div style="background:{SURFACE_CARTE}; border:1px solid {GRILLE}; '
                f'border-left:3px solid {bordure}; border-radius:6px; padding:12px 16px; margin-bottom:8px;">'
                f'<div style="display:flex; align-items:center; flex-wrap:wrap;">'
                f'<span style="font-weight:600; color:{ENCRE_PRIMAIRE};">{ind.libelle}</span>{etiquette}'
                f'</div>'
                f'<div style="font-size:1.05rem; color:{ENCRE_PRIMAIRE}; margin-top:2px;">{ind.valeur}</div>'
                f'{commentaire_html}'
                f'<div style="font-size:0.78rem; color:{ENCRE_MUTED}; margin-top:6px;">'
                f'Source : {ind.source} — {ind.date_donnee}'
                f'</div>'
                f'</div>'
            )
            st.markdown(carte_html, unsafe_allow_html=True)

        if section.note_methodo:
            st.caption(f"Fraîcheur des données : {section.note_methodo}")

        st.write("")

    st.markdown("#### Univers de partenaires cité par Grand Large Patrimoine")
    st.caption(
        "Architecture ouverte : liste de référence relevée sur grandlargepatrimoine.fr, utile pour "
        "resituer un nom entendu en réunion — pas une recommandation ni un classement."
    )
    col_gauche, col_droite = st.columns(2)
    categories = list(UNIVERS_PARTENAIRES.items())
    for i, (categorie, acteurs) in enumerate(categories):
        cible = col_gauche if i % 2 == 0 else col_droite
        with cible:
            st.markdown(f"**{categorie}**")
            st.markdown(", ".join(acteurs))
            st.write("")

    with st.expander("Checklist de rafraîchissement — à suivre avant toute utilisation"):
        for etape in CHECKLIST_RAFRAICHISSEMENT:
            st.markdown(f"- {etape}")
