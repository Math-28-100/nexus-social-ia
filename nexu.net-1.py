import streamlit as st
import random
import hashlib
from datetime import datetime
from groq import Groq

# =====================================================================
# 1. CONFIGURATION & SÉCURITÉ CRYPTO
# =====================================================================
st.set_page_config(page_title="Nexus AI - Réseau Social Universel", page_icon="🌍", layout="wide")


def hacher_mot_de_passe(password):
    """Sécurise les mots de passe avant stockage."""
    return hashlib.sha256(password.encode()).hexdigest()


# Récupération sécurisée de la clé API Groq
cle_par_defaut = ""
try:
    if "GROQ_API_KEY" in st.secrets:
        cle_par_defaut = st.secrets["GROQ_API_KEY"]
except Exception:
    pass


# =====================================================================
# 2. BASE DE DONNÉES GLOBALE EN MÉMOIRE (Partagée)
# =====================================================================
@st.cache_resource
def initialiser_base_globale():
    return {
        "utilisateurs": {},  # {email: {"pseudo": pseudo, "mdp": hashed_password}}
        "publications": {},  # {email: {"pseudo": pseudo, "statut": texte, "humeur": string, "maj": heure}}
        "fil_actualite": []  # Historique des analyses et connexions IA
    }


db = initialiser_base_globale()

# Gestion de la session utilisateur locale
if "utilisateur_connecte" not in st.session_state:
    st.session_state.utilisateur_connecte = None  # Stockera l'email de l'utilisateur connecté

# =====================================================================
# 3. SYSTÈME D'AUTHENTIFICATION COMPLÈTE (E-mail + Mot de passe)
# =====================================================================
if st.session_state.utilisateur_connecte is None:
    st.title("🌍 Bienvenue sur Nexus AI")
    st.caption("Le premier réseau social universel interconnecté par une Intelligence Artificielle de haut niveau.")

    onglet_connexion, onglet_inscription = st.tabs(["🔒 Connexion", "📝 Créer un compte"])

    with onglet_connexion:
        with st.form("form_connexion"):
            email_login = st.text_input("Adresse E-mail").strip().lower()
            mdp_login = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Se connecter"):
                if email_login in db["utilisateurs"] and db["utilisateurs"][email_login]["mdp"] == hacher_mot_de_passe(
                        mdp_login):
                    st.session_state.utilisateur_connecte = email_login
                    st.success(f"Ravi de vous revoir, {db['utilisateurs'][email_login]['pseudo']} !")
                    st.rerun()
                else:
                    st.error("Identifiants incorrects ou compte inexistant.")

    with onglet_inscription:
        with st.form("form_inscription"):
            nouveau_pseudo = st.text_input("Choisissez un Pseudo").strip()
            nouvel_email = st.text_input("Votre Adresse E-mail").strip().lower()
            nouveau_mdp = st.text_input("Choisissez un mot de passe", type="password")
            confirmer_mdp = st.text_input("Confirmez le mot de passe", type="password")

            if st.form_submit_button("Créer mon compte"):
                if not nouveau_pseudo or not nouvel_email or not nouveau_mdp:
                    st.error("Tous les champs sont obligatoires.")
                elif "@" not in nouvel_email:
                    st.error("Veuillez entrer une adresse e-mail valide.")
                elif nouvel_email in db["utilisateurs"]:
                    st.error("Cette adresse e-mail est déjà associée à un compte.")
                elif nouveau_mdp != confirmer_mdp:
                    st.error("Les mots de passe ne correspondent pas.")
                else:
                    db["utilisateurs"][nouvel_email] = {
                        "pseudo": nouveau_pseudo,
                        "mdp": hacher_mot_de_passe(nouveau_mdp)
                    }
                    st.success("Compte créé avec succès ! Connectez-vous dès maintenant.")
    st.stop()  # Bloque l'application si l'utilisateur n'est pas authentifié

# =====================================================================
# 4. INTERFACE UTILISATEUR & GRANDE ZONE D'EXPRESSION LIBRE
# =====================================================================
email_actuel = st.session_state.utilisateur_connecte
pseudo_actuel = db["utilisateurs"][email_actuel]["pseudo"]

# Barre latérale : Gestion du profil et publication
st.sidebar.title(f"👤 {pseudo_actuel}")
GROQ_API_KEY = st.sidebar.text_input("🔑 Clé API Groq", type="password", value=cle_par_defaut)
MODEL = "llama-3.3-70b-versatile"

st.sidebar.markdown("---")
st.sidebar.subheader("✍️ Exprimez-vous librement")
st.sidebar.caption("Propositions, recherches, projets pro, coups de main personnels... L'IA s'occupe du reste.")

# Récupération sécurisée avec valeurs par défaut exactes pour éviter le plantage .index()
liste_humeurs = ["Neutre 😶", "Besoin d'aide 🆘", "Motivé 🚀", "Créatif 🎨", "Business 💼", "Sociable 🍻", "Philosophique 🤔"]
publication_actuelle = db["publications"].get(email_actuel, {"statut": "", "humeur": "Neutre 😶"})

with st.sidebar.form("gestion_publication"):
    # Protection contre les crashs : calcul de l'index sécurisé
    humeur_sauvegardee = publication_actuelle.get("humeur", "Neutre 😶")
    index_defaut = liste_humeurs.index(humeur_sauvegardee) if humeur_sauvegardee in liste_humeurs else 0

    humeur = st.selectbox("Votre humeur / contexte :", liste_humeurs, index=index_defaut)

    # LA GRANDE CASE UNIVERSELLE D'EXPRESSION
    statut_libre = st.text_area(
        "Que recherchez-vous ou que proposez-vous aujourd'hui ?",
        value=publication_actuelle["statut"],
        height=250,
        placeholder="Ex: Je cherche un associé pour monter une startup de livraison de café, mais je cherche aussi quelqu'un pour garder mon chat ce week-end et un partenaire pour jouer aux échecs..."
    )

    if st.form_submit_button("⚡ Mettre à jour mon statut"):
        if statut_libre.strip():
            db["publications"][email_actuel] = {
                "pseudo": pseudo_actuel,
                "humeur": humeur,
                "statut": statut_libre,
                "maj": datetime.now().strftime("%H:%M")
            }
            st.sidebar.success("Votre statut a été mis à jour sur le réseau !")
            st.rerun()
        else:
            st.sidebar.error("Votre texte ne peut pas être vide.")

if st.sidebar.button("🚪 Déconnexion", type="secondary"):
    st.session_state.utilisateur_connecte = None
    st.rerun()

# =====================================================================
# 5. FIL D'ACTUALITÉ ET MOTEUR DE CORRÉLATION IA SOPHISTIQUÉ
# =====================================================================
st.title("⚡ L'Écosystème Nexus AI")
st.caption(f"Connecté en tant que : **{pseudo_actuel}** ({email_actuel}) • Mode Libre & Universel")

onglet_mur, onglet_cerveau_ia = st.tabs(["📜 Le Mur Global", "🧠 Matchmaking IA Multi-Intentions"])

# --- ONGLET 1 : LE MUR DE PUBLICATIONS STYLE RÉSEAU SOCIAL ---
with onglet_mur:
    st.subheader("🌐 Ce qui se passe sur le réseau en temps réel")
    if not db["publications"]:
        st.info("Le réseau est calme pour le moment. Remplissez votre zone d'expression à gauche pour commencer !")
    else:
        # Affichage sous forme de cartes d'actualités claires et scannables
        for email_pub, data_pub in reversed(list(db["publications"].items())):
            est_mon_post = (email_pub == email_actuel)
            titre_carte = f"⭐ {data_pub['pseudo']} (Vous)" if est_mon_post else f"👤 {data_pub['pseudo']}"

            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"### {titre_carte}")
                    st.caption(f"Posté à {data_pub['maj']}")
                with col2:
                    st.markdown(f"**Statut :** `{data_pub['humeur']}`")

                st.markdown("---")
                st.write(data_pub['statut'])

# --- ONGLET 2 : MOTEUR IA CENTRAL DE HAUT NIVEAU ---
with onglet_cerveau_ia:
    st.subheader("🧠 Analyse croisée algorithmique")
    st.caption(
        "Activez l'IA pour analyser la sémantique profonde, décrypter les besoins cachés et faire interagir deux profils.")

    if st.button("🔄 Lancer une interconnexion intelligente", type="primary", use_container_width=True):
        if len(db["publications"]) < 2:
            st.warning(
                "Il faut au moins 2 publications de membres différents sur le réseau pour lancer l'analyse smentique.")
        elif not GROQ_API_KEY:
            st.error(
                "Veuillez ajouter votre clé API Groq dans la barre latérale pour activer le cerveau de l'application.")
        else:
            with st.spinner("Analyse psychologique, sémantique et contextuelle des profils..."):
                # Sélectionner deux profils aléatoires distincts si possible
                emails_disponibles = list(db["publications"].keys())
                e1, e2 = random.sample(emails_disponibles, 2)
                p1, p2 = db["publications"][e1], db["publications"][e2]

                client = Groq(api_key=GROQ_API_KEY)

                # PROMPT ULTRA SOPHISTIQUÉ POUR COMPRENDRE LA LOGIQUE ET ADAPTER LE TON
                prompt_systeme = """
                Tu es l'intelligence centrale de Nexus AI, un réseau social universel (pro et perso).
                Ton rôle est d'analyser deux publications brutes, d'en comprendre la logique profonde (intentions, besoins explicites et implicites, offres de services, affinités humaines) et de générer une simulation de rencontre ou d'alliance d'un niveau d'ingénierie sociale exceptionnel.

                Tu dois détecter TOUTES les passerelles possibles : commerciales, amicales, entraide au quotidien, ou passions communes.

                Structure ta réponse de manière très soignée :
                1. ANALYSE DES COMPATIBILITÉS : Détaille brièvement les points communs logiques ou les opportunités d'entraide.
                2. INTERACTION SIMULÉE : Rédige un dialogue percutant, naturel et hyper réaliste (4-5 répliques max) entre les deux membres (ou leurs avatars IA) basé sur leurs écrits. Adapte le ton : détendu pour du perso, affûté pour du business, empathique pour de l'entraide.
                3. RECOMMANDATION FINALE : Termine strictement par une ligne commençant par 'CONCLUSION DE L'ALGORYTHME :' résumant l'action concrète qu'ils doivent faire.
                """

                prompt_utilisateur = f"""
                Membres à interconnecter :

                Profil A : {p1['pseudo']}
                Humeur / Contexte : {p1['humeur']}
                Texte libre : "{p1['statut']}"

                ---

                Profil B : {p2['pseudo']}
                Humeur / Contexte : {p2['humeur']}
                Texte libre : "{p2['statut']}"
                """

                try:
                    reponse = client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": prompt_systeme},
                            {"role": "user", "content": prompt_utilisateur}
                        ],
                        model=MODEL,
                        temperature=0.75,
                        max_tokens=1200
                    )
                    analyse_complete = reponse.choices[0].message.content

                    # Enregistrement dans l'historique commun
                    db["fil_actualite"].append({
                        "heure": datetime.now().strftime("%H:%M"),
                        "membres": f"{p1['pseudo']} 💖 {p2['pseudo']}",
                        "analyse": analyse_complete
                    })
                    st.toast("🎯 L'IA a détecté une synergie de profils !")
                except Exception as e:
                    st.error(f"Erreur du moteur Groq : {e}")

    # Affichage de l'historique des interactions générées par l'IA
    if db["fil_actualite"]:
        for item in reversed(db["fil_actualite"]):
            with st.chat_message("ai", avatar="🧠"):
                st.markdown(f"#### 📡 Alliance Sémantique : {item['membres']} — *générée à {item['heure']}*")

                # Mise en forme propre des conclusions de l'IA
                lignes = item['analyse'].split("\n")
                for l in lignes:
                    if "CONCLUSION DE L'ALGORYTHME" in l.upper() or "CONCLUSION DE L'ALGORITHME" in l.upper():
                        st.info(f"💡 **{l}**")
                    elif l.strip():
                        st.write(l)
    else:
        st.caption("Aucune analyse croisée n'a encore été lancée. Cliquez sur le bouton ci-dessus pour éveiller l'IA.")