import streamlit as st
import requests
from datetime import datetime, timedelta

API_TOKEN = "845305378d0846c7b4ce6e9b12652ffd"

st.set_page_config(page_title="Robô PRO", layout="wide")
st.title("⚽ Robô Inteligente de Apostas")


def analisar_padrao(lista):
    over = sum(1 for x in lista if x >= 2)
    return over


def analisar_btts(feitos, sofridos):
    return sum(1 for f, s in zip(feitos, sofridos) if f > 0 and s > 0)


def estatisticas_time(team_id):

    headers = {"X-Auth-Token": API_TOKEN}
    url = f"https://api.football-data.org/v4/teams/{team_id}/matches?status=FINISHED&limit=30"

    try:
        r = requests.get(url, headers=headers)

        if r.status_code != 200:
            return {}

        dados = r.json()

        casa_feitos = []
        casa_sofridos = []
        fora_feitos = []
        fora_sofridos = []

        for j in dados.get("matches", []):

            if j["score"]["fullTime"]["home"] is None:
                continue

            if j["homeTeam"]["id"] == team_id:

                if len(casa_feitos) < 10:
                    casa_feitos.append(j["score"]["fullTime"]["home"])
                    casa_sofridos.append(j["score"]["fullTime"]["away"])

            else:

                if len(fora_feitos) < 10:
                    fora_feitos.append(j["score"]["fullTime"]["away"])
                    fora_sofridos.append(j["score"]["fullTime"]["home"])

        return {
            "casa_feitos": casa_feitos,
            "casa_sofridos": casa_sofridos,
            "fora_feitos": fora_feitos,
            "fora_sofridos": fora_sofridos
        }

    except:
        return {}


def analisar():

    headers = {"X-Auth-Token": API_TOKEN}

    hoje = datetime.utcnow()
    inicio = hoje.strftime("%Y-%m-%d")
    fim = (hoje + timedelta(days=1)).strftime("%Y-%m-%d")

    url = f"https://api.football-data.org/v4/competitions/BSA/matches?dateFrom={inicio}&dateTo={fim}"

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        st.error("Erro API")
        return

    dados = r.json()

    for j in dados.get("matches", []):

        if j.get("status") not in ["SCHEDULED","TIMED"]:
            continue

        casa = j["homeTeam"]["name"]
        fora = j["awayTeam"]["name"]

        id_casa = j["homeTeam"]["id"]
        id_fora = j["awayTeam"]["id"]

        stats_casa = estatisticas_time(id_casa)
        stats_fora = estatisticas_time(id_fora)

        if not stats_casa or not stats_fora:
            continue

        # padrões
        over_casa = analisar_padrao(stats_casa["casa_feitos"])
        over_fora = analisar_padrao(stats_fora["fora_feitos"])

        btts_casa = analisar_btts(stats_casa["casa_feitos"], stats_casa["casa_sofridos"])
        btts_fora = analisar_btts(stats_fora["fora_feitos"], stats_fora["fora_sofridos"])

        st.write("---")
        st.write(f"{casa} x {fora}")

        # 🔥 DETECÇÃO
        if over_casa >= 7 and over_fora >= 6:
            st.write("🔥 OVER MUITO FORTE")

        if btts_casa >= 6 and btts_fora >= 6:
            st.write("🤝 AMBAS MUITO FORTE")

        if over_casa <= 3 and over_fora <= 3:
            st.write("🧊 JOGO FRACO")

        # dados
        st.write(f"🏠 {casa}")
        st.write("Feitos:", stats_casa["casa_feitos"])
        st.write("Sofridos:", stats_casa["casa_sofridos"])

        st.write(f"🚗 {fora}")
        st.write("Feitos:", stats_fora["fora_feitos"])
        st.write("Sofridos:", stats_fora["fora_sofridos"])


if st.button("🔎 ANALISAR JOGOS"):
    analisar()
