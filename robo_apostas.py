import streamlit as st
import requests
from datetime import datetime, timedelta

API_TOKEN = "845305378d0846c7b4ce6e9b12652ffd"

LIGAS = {
    "BSA": "Brasileirão Série A",
    "BRC": "Copa do Brasil",
    "CLI": "Libertadores",
    "CSA": "Sul-Americana"
}

st.set_page_config(page_title="Robô de Apostas", layout="wide")

st.title("⚽ Robô Profissional de Análise de Apostas")

def estatisticas_time(team_id):

    headers = {"X-Auth-Token": API_TOKEN}

    url = f"https://api.football-data.org/v4/teams/{team_id}/matches?status=FINISHED&limit=10"

    r = requests.get(url, headers=headers)

    gols_marcados = 0
    gols_sofridos = 0
    jogos = 0

    if r.status_code != 200:
        return 1.2,1.2

    dados = r.json()

    for j in dados["matches"]:

        if j["homeTeam"]["id"] == team_id:
            gm = j["score"]["fullTime"]["home"]
            gs = j["score"]["fullTime"]["away"]
        else:
            gm = j["score"]["fullTime"]["away"]
            gs = j["score"]["fullTime"]["home"]

        if gm is None:
            continue

        gols_marcados += gm
        gols_sofridos += gs
        jogos += 1

    if jogos == 0:
        return 1.2,1.2

    return gols_marcados/jogos, gols_sofridos/jogos


def analisar():

    headers = {"X-Auth-Token": API_TOKEN}

    hoje = datetime.utcnow()

    inicio = hoje.strftime("%Y-%m-%d")
    fim = (hoje + timedelta(days=7)).strftime("%Y-%m-%d")

    top_over25 = []
    top_btts = []
    top_over15 = []

    for codigo, nome in LIGAS.items():

        url = f"https://api.football-data.org/v4/competitions/{codigo}/matches?dateFrom={inicio}&dateTo={fim}"

        r = requests.get(url, headers=headers)

        if r.status_code != 200:
            continue

        dados = r.json()

        for j in dados["matches"]:

            if j["status"] not in ["SCHEDULED","TIMED"]:
                continue

            casa = j["homeTeam"]["name"]
            fora = j["awayTeam"]["name"]

            id_casa = j["homeTeam"]["id"]
            id_fora = j["awayTeam"]["id"]

            ataque_casa,defesa_casa = estatisticas_time(id_casa)
            ataque_fora,defesa_fora = estatisticas_time(id_fora)

            gols_esperados = (
                ataque_casa*0.4 +
                ataque_fora*0.4 +
                defesa_casa*0.1 +
                defesa_fora*0.1
            )

            prob_over15 = min(int((gols_esperados/2)*100),95)
            prob_over25 = min(int((gols_esperados/3)*100),90)
            prob_btts = min(int(((ataque_casa+ataque_fora)/3)*100),85)

            odd_justa_over25 = round(100/prob_over25,2) if prob_over25>0 else 0

            jogo_info = {
                "jogo": f"{casa} x {fora}",
                "liga": nome,
                "gols": round(gols_esperados,2),
                "over15": prob_over15,
                "over25": prob_over25,
                "btts": prob_btts,
                "odd_justa": odd_justa_over25
            }

            if prob_over25 > 55:
                top_over25.append(jogo_info)

            if prob_btts > 65:
                top_btts.append(jogo_info)

            if prob_over15 > 75:
                top_over15.append(jogo_info)

    st.subheader("⭐ TOP OVER 2.5")

    for j in top_over25[:10]:

        st.write("---")
        st.write(j["jogo"])
        st.write(j["liga"])
        st.write("⚽ Gols esperados:",j["gols"])
        st.write("📊 Probabilidade Over 2.5:",j["over25"],"%")
        st.write("💰 Odd justa mínima:",j["odd_justa"])

    st.subheader("🤝 TOP AMBAS MARCAM")

    for j in top_btts[:10]:

        st.write("---")
        st.write(j["jogo"])
        st.write(j["liga"])
        st.write("🤝 Probabilidade:",j["btts"],"%")

    st.subheader("⚽ TOP OVER 1.5")

    for j in top_over15[:10]:

        st.write("---")
        st.write(j["jogo"])
        st.write(j["liga"])
        st.write("📈 Probabilidade:",j["over15"],"%")

if st.button("🔎 ANALISAR JOGOS"):
    analisar()
