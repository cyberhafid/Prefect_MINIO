import os
import time

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
FASTAPI_PORT = os.getenv("FASTAPI_PORT", "8000")
API_URL = f"http://mon_api:{FASTAPI_PORT}"
st.set_page_config(page_title="Iris Predictor", page_icon="🌸")

st.title("🌸 Classification des Iris")
st.write(
    "Entrez les caractéristiques de la fleur pour obtenir une prédiction en temps réel via l'API."
)

# 1. Formulaire de saisie
with st.sidebar:
    st.header("Paramètres de la fleur")
    sl = st.slider("Longueur Sépale (cm)", 4.0, 8.0, 5.1)
    sw = st.slider("Largeur Sépale (cm)", 2.0, 5.0, 3.5)
    pl = st.slider("Longueur Pétale (cm)", 1.0, 7.0, 1.4)
    pw = st.slider("Largeur Pétale (cm)", 0.1, 3.0, 0.2)

# 2. Bouton de prédiction
if st.button("Prédire l'espèce"):
    payload = {
        "sepal_length": sl,
        "sepal_width": sw,
        "petal_length": pl,
        "petal_width": pw,
    }

    try:
        with st.spinner("Envoi au worker..."):
            response = requests.post(
                f"{API_URL}/predict",
                json=payload,
                timeout=30,  # ← échoue proprement si l'API ne répond pas
            )
            response.raise_for_status()
            task_id = response.json()["task_id"]

        st.info(f"Tâche soumise : `{task_id}`")

        # 2. Polling (boucle d'attente) pour le résultat
        result_placeholder = st.empty()
        result = None

        with st.spinner("Interrogation du modèle..."):
            for _ in range(20):
                poll = requests.get(f"{API_URL}/result/{task_id}")
                poll.raise_for_status()
                data = poll.json()

                result_placeholder.caption(f"Statut : `{data['status']}`")

                if data["status"] == "SUCCESS":
                    result = data["result"]
                    break
                elif data["status"] == "FAILURE":
                    st.error("La tâche Celery a échoué côté worker.")
                    st.stop()

                time.sleep(0.5)

        result_placeholder.empty()

        # 3. Résultat
        if result:
            st.success(f"Résultat : **{result['prediction'].upper()}**")
            col1, col2 = st.columns(2)
            col1.metric("Version du modèle", result["model_version"])
            col2.metric("Index de classe", result["class_index"])
        else:
            st.warning("⏱️ Timeout : le worker n'a pas répondu en 10s.")

    except Exception as e:
        st.error(f"Erreur de connexion à l'API : {e}")
