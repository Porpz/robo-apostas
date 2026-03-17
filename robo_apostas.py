import streamlit as st
import requests
from datetime import datetime, timedelta

API_TOKEN = "845305378d0846c7b4ce6e9b12652ffd"

st.set_page_config(page_title="Robô de Lucro", layout="wide")
st.title("⚽ Robô Profissional de Apostas (Foco em Lucro)")


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
        over_casa = sum(1 for x in stats_casa["casa_feitos"] if x >= 2)
        over_fora = sum(1 for x in stats_fora["fora_feitos"] if x >= 2)

        btts_casa = sum(1 for f, s in zip(stats_casa["casa_feitos"], stats_casa["casa_sofridos"]) if f > 0 and s > 0)
        btts_fora = sum(1 for f, s in zip(stats_fora["fora_feitos"], stats_fora["fora_sofridos"]) if f > 0 and s > 0)

        # probabilidade simples
        prob_over25 = int(((over_casa + over_fora) / 20) * 100)
        prob_btts = int(((btts_casa + btts_fora) / 20) * 100)

        st.write("---")
        st.write(f"{casa} x {fora}")

        # 🔥 leitura do jogo
        if prob_over25 > 65 and prob_btts > 60:
            st.success("🔥 JOGO MUITO FORTE")

        elif prob_over25 > 60:
            st.info("⚡ JOGO BOM PARA OVER")

        elif prob_over25 < 40:
            st.warning("🧊 JOGO FRACO")

        # dados
        st.write(f"🏠 {casa} (CASA)")
        st.write("Feitos:", stats_casa["casa_feitos"])
        st.write("Sofridos:", stats_casa["casa_sofridos"])

        st.write(f"🚗 {fora} (FORA)")
        st.write("Feitos:", stats_fora["fora_feitos"])
        st.write("Sofridos:", stats_fora["fora_sofridos"])

        st.write("📊 Prob Over 2.5:", prob_over25,"%")
        st.write("🤝 Prob Ambas Marcam:", prob_btts,"%")

        # 💰 ODDS E VALUE
        if prob_over25 > 0:

            odd_justa = round(100 / prob_over25, 2)
            st.write("💰 Odd justa Over 2.5:", odd_justa)

            odd_usuario = st.number_input(
                f"Digite a odd da casa ({casa} x {fora})",
                min_value=1.01,
                step=0.01,
                key=casa+fora
            )

            if odd_usuario > odd_justa:
                st.success("🔥 VALUE BET DETECTADA")
            elif odd_usuario > 1.01:
                st.error("❌ Sem valor")


if st.button("🔎 ANALISAR JOGOS"):
    analisar()
