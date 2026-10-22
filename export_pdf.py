"""
Module export_pdf - génère un export PDF one-pager par scénario, en plus
du CSV déjà proposé dans chaque onglet. Mise en page sobre, dans le même
esprit que l'outil : hypothèses toujours visibles, aucune recommandation
chiffrée mise en avant.
Grand Large Patrimoine - projet de stage
"""

import io
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

NAVY = colors.HexColor("#03001C")
ENCRE_SECONDAIRE = colors.HexColor("#4a4860")
GRILLE = colors.HexColor("#e7e5dd")
CREME = colors.HexColor("#f7f5ef")


def _styles():
    base = getSampleStyleSheet()
    eyebrow = ParagraphStyle(
        "EyebrowGLP", parent=base["Normal"], textColor=ENCRE_SECONDAIRE,
        fontSize=8, fontName="Helvetica", spaceAfter=2,
    )
    titre = ParagraphStyle(
        "TitreGLP", parent=base["Title"], textColor=NAVY, fontSize=17,
        leading=20, spaceAfter=3,
    )
    sous_titre = ParagraphStyle(
        "SousTitreGLP", parent=base["Normal"], textColor=ENCRE_SECONDAIRE,
        fontSize=10, fontName="Helvetica-Oblique", spaceAfter=14,
    )
    corps = ParagraphStyle("CorpsGLP", parent=base["Normal"], fontSize=9, leading=13)
    disclaimer = ParagraphStyle(
        "DisclaimerGLP", parent=base["Normal"], fontSize=7.5,
        textColor=ENCRE_SECONDAIRE, spaceBefore=4, leading=10,
    )
    return eyebrow, titre, sous_titre, corps, disclaimer


def generer_pdf_scenario(
    titre, sous_titre, kpis, lignes_tableau, hypotheses,
    image_png=None, legende_image="",
    titre_tableau_secondaire="", lignes_tableau_secondaire=None,
):
    """
    Construit un PDF one-pager générique pour un scénario de l'outil.

    - titre, sous_titre : texte d'en-tête (repris de entete_section() dans
      l'interface Streamlit).
    - kpis : liste de tuples (label, valeur déjà formatée en euros/texte).
    - lignes_tableau : liste de listes (la première ligne est l'en-tête),
      déjà formatée en chaînes (pas de calcul fait ici).
    - hypotheses : liste de phrases (les mêmes avertissements que l'onglet
      correspondant dans l'interface).
    - image_png : bytes PNG optionnels (ex. le donut de composition d'un
      panier), insérés après le tableau principal, avec sa legende_image en
      légende sous l'image.
    - titre_tableau_secondaire, lignes_tableau_secondaire : second tableau
      optionnel (ex. détail par classe d'actifs), affiché après l'image,
      même format que lignes_tableau.

    Renvoie les bytes du PDF, à passer tels quels à st.download_button.
    """
    tampon = io.BytesIO()
    doc = SimpleDocTemplate(
        tampon, pagesize=A4,
        topMargin=1.8 * cm, bottomMargin=1.6 * cm, leftMargin=2 * cm, rightMargin=2 * cm,
    )
    eyebrow_style, titre_style, sous_titre_style, corps_style, disclaimer_style = _styles()
    elements = []

    elements.append(Paragraph("SIMULATEUR PATRIMONIAL — GRAND LARGE PATRIMOINE", eyebrow_style))
    elements.append(Paragraph(titre, titre_style))
    if sous_titre:
        elements.append(Paragraph(sous_titre, sous_titre_style))

    if kpis:
        data_kpi = [
            [Paragraph(f"<b>{label}</b>", corps_style) for label, _ in kpis],
            [Paragraph(valeur, corps_style) for _, valeur in kpis],
        ]
        largeur_colonne = (17.0 * cm) / len(kpis)
        table_kpi = Table(data_kpi, colWidths=[largeur_colonne] * len(kpis))
        table_kpi.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), CREME),
            ("BOX", (0, 0), (-1, -1), 0.6, GRILLE),
            ("INNERGRID", (0, 0), (-1, -1), 0.6, GRILLE),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(Spacer(1, 4))
        elements.append(table_kpi)
        elements.append(Spacer(1, 16))

    if lignes_tableau:
        lignes_formatees = [
            [Paragraph(str(cellule), corps_style) for cellule in ligne]
            for ligne in lignes_tableau
        ]
        table_detail = Table(lignes_formatees, hAlign="LEFT")
        table_detail.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("TEXTCOLOR", (0, 0), (-1, 0), NAVY),
            ("LINEBELOW", (0, 0), (-1, 0), 0.9, NAVY),
            ("LINEBELOW", (0, 1), (-1, -1), 0.4, GRILLE),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(table_detail)
        elements.append(Spacer(1, 16))

    if image_png:
        # Largeur fixe, hauteur recalculée pour garder les proportions du
        # PNG d'origine (le donut Plotly est généré en 420x320, mais on ne
        # dépend pas de ce chiffre en dur ici).
        image_io = io.BytesIO(image_png)
        largeur_cible = 8.5 * cm
        lecteur_taille = ImageReader(image_io)
        largeur_px, hauteur_px = lecteur_taille.getSize()
        hauteur_cible = largeur_cible * (hauteur_px / largeur_px)
        image_io.seek(0)
        image_pdf = Image(image_io, width=largeur_cible, height=hauteur_cible)
        image_pdf.hAlign = "CENTER"
        elements.append(image_pdf)
        if legende_image:
            elements.append(Paragraph(legende_image, disclaimer_style))
        elements.append(Spacer(1, 14))

    if lignes_tableau_secondaire:
        if titre_tableau_secondaire:
            elements.append(Paragraph(f"<b>{titre_tableau_secondaire}</b>", corps_style))
            elements.append(Spacer(1, 4))
        lignes_secondaires_formatees = [
            [Paragraph(str(cellule), corps_style) for cellule in ligne]
            for ligne in lignes_tableau_secondaire
        ]
        table_secondaire = Table(lignes_secondaires_formatees, hAlign="LEFT")
        table_secondaire.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("TEXTCOLOR", (0, 0), (-1, 0), NAVY),
            ("LINEBELOW", (0, 0), (-1, 0), 0.9, NAVY),
            ("LINEBELOW", (0, 1), (-1, -1), 0.4, GRILLE),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(table_secondaire)
        elements.append(Spacer(1, 16))

    if hypotheses:
        elements.append(Paragraph("<b>Hypothèses de ce scénario</b>", corps_style))
        elements.append(Spacer(1, 3))
        for hypothese in hypotheses:
            elements.append(Paragraph(f"— {hypothese}", corps_style))
        elements.append(Spacer(1, 10))

    elements.append(Paragraph(
        "Outil informatif à usage pédagogique, construit sur des hypothèses explicites. Il ne "
        "constitue ni un conseil fiscal, ni un conseil juridique, ni un conseil en investissement "
        "personnalisé, et ne remplace pas l'analyse d'un professionnel.",
        disclaimer_style,
    ))
    elements.append(Paragraph(
        f"Généré le {date.today().strftime('%d/%m/%Y')} — simulateur Grand Large Patrimoine.",
        disclaimer_style,
    ))

    doc.build(elements)
    return tampon.getvalue()
