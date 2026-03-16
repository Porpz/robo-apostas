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

st.title("⚽ Robô de Análise de Apostas")

def estatisticas_time(team_id):

    headers = {"X-Auth-Token": API_TOKEN}

    url = f"https://api.football-data.org/v4/teams/{team_id}/matches?status=FINISHED&limit=10"

    r = requests.get(url, headers=headers)

    gols_marcados = 0
    gols_sofridos = 0
    jogos = 0
    ultimos = []

    if r.status_code != 200:
        return 1.2,1.2,[1,1,1,1,1]

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
        ultimos.append(gm+gs)

        jogos += 1

    if jogos == 0:
        return 1.2,1.2,[1,1,1,1,1]

    return gols_marcados/jogos, gols_sofridos/jogos, ultimos[:5]


def simular(gols):

    placares = []

    if gols >= 1.5:
        placares.append("1x1")
    if gols >= 2:
        placares.append("2x1")
    if gols >= 2.3:
        placares.append("2x2")
    if gols >= 2.6:
        placares.append("3x1")
    if gols >= 3:
        placares.append("3x2")

    prob_over = int((gols/4)*100)

    return prob_over, placares


def analisar():

    headers = {"X-Auth-Token": API_TOKEN}

    hoje = datetime.utcnow()

    inicio = hoje.strftime("%Y-%m-%d")
    fim = (hoje + timedelta(days=10)).strftime("%Y-%m-%d")

    ranking = []

    for codigo, nome in LIGAS.items():

        url = f"https://api.football-data.org/v4/competitions/{codigo}/matches?dateFrom={inicio}&dateTo={fim}"

        r = requests.get(url, headers=headers)

        if r.status_code != 200:
            st.write("Erro API:", r.status_code)
            continue

        dados = r.json()

        for j in dados["matches"]:

            if j["status"] not in ["SCHEDULED","TIMED"]:
                continue

            casa = j["homeTeam"]["name"]
            fora = j["awayTeam"]["name"]

            id_casa = j["homeTeam"]["id"]
            id_fora = j["awayTeam"]["id"]

            ataque_casa,defesa_casa,gols_casa = estatisticas_time(id_casa)
            ataque_fora,defesa_fora,gols_fora = estatisticas_time(id_fora)

            ritmo = (sum(gols_casa)+sum(gols_fora))/10

            if ritmo < 1.3:
                continue

            gols_esperados = (
                ataque_casa*0.35 +
                ataque_fora*0.35 +
                defesa_casa*0.15 +
                defesa_fora*0.15 +
                ritmo*0.5
            )

            prob_over, placares = simular(gols_esperados)

            prob_btts = int(((ataque_casa + ataque_fora)/4)*100)

            prob = int((gols_esperados/3.5)*100)

            score = round((prob/10),1)

            ranking.append((score,casa,fora,nome,prob_over,prob_btts,placares,gols_esperados,j))

    ranking.sort(reverse=True)

    st.subheader("⭐ TOP APOSTAS")

    for i,jogo in enumerate(ranking[:15]):

        data = jogo[8]["utcDate"][:10]
        hora = jogo[8]["utcDate"][11:16]

        st.write("---")
        st.write(f"### {jogo[1]} x {jogo[2]}")
        st.write(jogo[3])
        st.write(f"{data} {hora}")

        st.write("⚽ Gols esperados:", round(jogo[7],2))
        st.write("📊 Probabilidade Over 2.5:", jogo[4],"%")
        st.write("🤝 Probabilidade Ambas Marcam:", jogo[5],"%")

        st.write("🎯 Placares prováveis:", ", ".join(jogo[6]))
        st.write("⭐ Score da aposta:", jogo[0],"/10")


if st.button("🔎 ANALISAR JOGOS"):
    analisar()
