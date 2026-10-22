"""
Module copilote - assistant pédagogique IA intégré au simulateur.

Répond aux questions sur les mécanismes fiscaux couverts par l'outil et
sur la logique de calcul des différents modules, en s'appuyant sur le
glossaire déjà vérifié et sourcé du simulateur (glossaire.py) plutôt que
sur des chiffres récités de mémoire par le modèle - ce qui limite le
risque d'erreur numérique.

Garde-fous volontaires :
- jamais de conseil en investissement personnalisé, jamais de
  recommandation de produit ou de prestataire précis ;
- le copilote ne voit pas les montants actuellement saisis par
  l'utilisateur dans les autres onglets (aucun état partagé n'est câblé
  en v1) - pour une question sur un résultat chiffré, l'utilisateur doit
  copier-coller les montants affichés ;
- rappel systématique, dans le prompt système, qu'il s'agit d'un outil
  pédagogique interne et non d'un conseil réglementé.

Grand Large Patrimoine - projet de stage.
"""

from glossaire import GLOSSAIRE

MODELE = "claude-sonnet-5"
MAX_TOKENS_REPONSE = 900
NB_MESSAGES_HISTORIQUE_MAX = 11  # tronque l'historique pour limiter le coût - nombre IMPAIR
# volontairement : l'historique alterne toujours user/assistant/user/... et se
# termine toujours par le message "user" qu'on vient d'ajouter avant d'appeler
# repondre(). En ne gardant que les N derniers messages, un N pair ferait
# commencer la liste tronquée par un message "assistant" (l'API Anthropic exige
# que la conversation débute par "user") - un N impair préserve cette parité.

# Reprend les intitulés déjà affichés dans l'expander d'accueil de app.py
# ("Comment utiliser ce simulateur") - dupliqué ici à dessein pour éviter
# tout import circulaire (app.py importe ce module, pas l'inverse).
DESCRIPTION_MODULES = """
- Rémunération annuelle : pour une année donnée, salaire ou dividende - lequel laisse le plus net en poche au dirigeant (SASU assimilé salarié vs SARL gérant majoritaire TNS) ?
- Trajectoire pluriannuelle : sur plusieurs années, sortir l'argent chaque année ou le laisser capitaliser dans une holding - avec une fourchette Monte-Carlo (P10-P50-P90), pas un chiffre unique.
- Démembrement de propriété : pour transmettre un bien, donation en pleine propriété ou de la seule nue-propriété (barème de l'article 669 du CGI selon l'âge de l'usufruitier).
- Succession : au décès, combien reste-t-il net selon le lien de parenté avec l'héritier (conjoint, enfant, frère/sœur, tiers).
- Assurance-vie : net au rachat (PFU, abattement après 8 ans) et net à la transmission pour le bénéficiaire (article 990 I avant 70 ans, article 757 B après 70 ans).
- IFI : impôt sur la fortune immobilière - barème, décote, abattement de 30 % sur la résidence principale, exclusion des biens professionnels.
- SCI (IS vs IR) : détenir un bien locatif en société - IS (amortissement, double imposition à la sortie) ou IR (pas d'amortissement, abattement pour durée de détention).
- PER : plan d'épargne retraite - plafond de déduction (salarié ou TNS), économie d'impôt à l'entrée, fiscalité à la sortie en capital.
- Note Grand Large : veille marchés et seuils réglementaires sourcés et datés, organisée par solution Grand Large Patrimoine.
""".strip()


def cle_api_configuree(secrets) -> bool:
    """
    Vérifie qu'une vraie clef semble présente dans st.secrets - sans
    jamais la journaliser ni la renvoyer. `secrets` est st.secrets,
    passé en paramètre pour ne pas importer streamlit ici.
    """
    cle = secrets.get("ANTHROPIC_API_KEY", "") if secrets else ""
    return bool(cle) and cle.strip() not in ("", "colle-ta-clef-ici") and cle.startswith("sk-ant-")


def construire_prompt_systeme() -> str:
    glossaire_txt = "\n".join(f"- {terme} : {definition}" for terme, definition in GLOSSAIRE.items())
    return f"""Tu es le copilote pédagogique intégré au simulateur patrimonial interne de Grand Large Patrimoine (cabinet de gestion de patrimoine / family office, Paris).

Ton rôle : aider un collaborateur du cabinet (ou un visiteur du simulateur) à comprendre les mécanismes fiscaux français couverts par l'outil et la logique de calcul de chaque module - jamais produire un conseil personnalisé.

Règles strictes, à respecter dans toutes tes réponses :
1. Tu ne donnes jamais de conseil en investissement personnalisé, jamais de recommandation de produit, de contrat ou de prestataire précis. Si on te le demande, rappelle que ceci est un outil pédagogique et oriente vers un conseiller du cabinet.
2. Pour tout chiffre, taux ou seuil réglementaire, appuie-toi en priorité sur le glossaire ci-dessous (vérifié et sourcé par l'équipe) plutôt que sur ta mémoire générale. En cas de doute ou de chiffre non couvert par le glossaire, dis-le explicitement plutôt que d'inventer un montant.
3. Tu ne vois pas les montants actuellement saisis par l'utilisateur dans les autres onglets du simulateur. S'il te pose une question sur un résultat chiffré précis, demande-lui de copier-coller les montants affichés à l'écran.
4. Réponses courtes et directes, en français, sans jargon superflu - un paragraphe ou une courte liste suffisent dans la plupart des cas.
5. Tu peux citer l'article de loi ou le régime fiscal concerné quand c'est utile (ils figurent dans le glossaire), mais sans warning juridique systématique à chaque réponse - un rappel en fin d'échange suffit si le sujet s'y prête.

Glossaire de référence du simulateur :
{glossaire_txt}

Modules du simulateur (pour situer une question dans le bon onglet) :
{DESCRIPTION_MODULES}
"""


def repondre(historique: list[dict], cle_api: str) -> str:
    """
    Appelle l'API Anthropic avec l'historique de conversation (liste de
    dicts {"role": "user"/"assistant", "content": str}) et renvoie le
    texte de la réponse. Lève une exception en cas d'erreur API - à
    gérer par l'appelant (app.py) pour afficher un message clair sans
    jamais exposer la clef.
    """
    import anthropic

    client = anthropic.Anthropic(api_key=cle_api)
    messages_tronques = historique[-NB_MESSAGES_HISTORIQUE_MAX:]
    reponse = client.messages.create(
        model=MODELE,
        max_tokens=MAX_TOKENS_REPONSE,
        system=construire_prompt_systeme(),
        messages=[{"role": m["role"], "content": m["content"]} for m in messages_tronques],
    )
    return reponse.content[0].text
