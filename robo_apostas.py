import streamlit as st
import requests
from datetime import datetime, timedelta

API_TOKEN = "845305378d0846c7b4ce6e9b12652ffd"

LIGAS = {
    "BSA": "Brasileirão Série A",
    "BRC": "Copa do Brasil",
    "CLI": "Libertadores",
    "CSA": "Sul-Americana",
    "CL": "Champions League"
}

st.set_page_config(page_title="Robô de Apostas", layout="wide")
st.title("⚽ Robô Profissional de Análise de Apostas")


def estatisticas_time(team_id):
    headers = {"X-Auth-Token": API_TOKEN}
    url = f"https://api.football-data.org/v4/teams/{team_id}/matches?status=FINISHED&limit=8"

    try:
        r = requests.get(url, headers=headers, timeout=20)

        if r.status_code != 200:
            return 1.2, 1.2

        dados = r.json()

        gols_marcados = 0
        gols_sofridos = 0
        jogos = 0

        for j in dados.get("matches", []):
            if j["homeTeam"]["id"] == team_id:
                gm = j["score"]["fullTime"]["home"]
                gs = j["score"]["fullTime"]["away"]
            else:
                gm = j["score"]["fullTime"]["away"]
                gs = j["score"]["fullTime"]["home"]

            if gm is None or gs is None:
                continue

            gols_marcados += gm
            gols_sofridos += gs
            jogos += 1

        if jogos == 0:
            return 1.2, 1.2

        return gols_marcados / jogos, gols_sofridos / jogos

    except Exception:
        return 1.2, 1.2


def analisar():
    headers = {"X-Auth-Token": API_TOKEN}

    hoje = datetime.utcnow()
    inicio = hoje.strftime("%Y-%m-%d")
    fim = (hoje + timedelta(days=7)).strftime("%Y-%m-%d")

    over25 = []
    btts = []
    over15 = []
    ranking = []

    erros_api = []

    for codigo, nome in LIGAS.items():
        url = f"https://api.football-data.org/v4/competitions/{codigo}/matches?dateFrom={inicio}&dateTo={fim}"

        try:
            r = requests.get(url, headers=headers, timeout=20)

            if r.status_code != 200:
                erros_api.append(f"{nome}: erro API {r.status_code}")
                continue

            dados = r.json()

            for j in dados.get("matches", []):
                if j.get("status") not in ["SCHEDULED", "TIMED"]:
                    continue

                casa = j["homeTeam"]["name"]
                fora = j["awayTeam"]["name"]

                id_casa = j["homeTeam"]["id"]
                id_fora = j["awayTeam"]["id"]

                ataque_casa, defesa_casa = estatisticas_time(id_casa)
                ataque_fora, defesa_fora = estatisticas_time(id_fora)

                gols_esperados = (
                    ataque_casa * 0.45 +
                    ataque_fora * 0.45 +
                    defesa_casa * 0.05 +
                    defesa_fora * 0.05
                )

                prob_over15 = min(int((gols_esperados / 2) * 100), 95)
                prob_over25 = min(int((gols_esperados / 2.8) * 100), 90)
                prob_btts = min(int(((ataque_casa + ataque_fora) / 2.6) * 100), 85)

                odd_over25 = round(100 / prob_over25, 2) if prob_over25 > 0 else 0

                jogo = {
                    "jogo": f"{casa} x {fora}",
                    "liga": nome,
                    "gols": round(gols_esperados, 2),
                    "over15": prob_over15,
                    "over25": prob_over25,
                    "btts": prob_btts,
                    "odd": odd_over25
                }

                if prob_over25 > 55:
                    over25.append(jogo)

                if prob_btts > 55:
                    btts.append(jogo)

                if prob_over15 > 70:
                    over15.append(jogo)

                score_total = prob_over25 + prob_btts + prob_over15
                ranking.append((score_total, jogo))

        except Exception as e:
            erros_api.append(f"{nome}: {str(e)}")

    ranking.sort(key=lambda x: x[0], reverse=True)
    over25.sort(key=lambda x: x["over25"], reverse=True)
    btts.sort(key=lambda x: x["btts"], reverse=True)
    over15.sort(key=lambda x: x["over15"], reverse=True)

    if erros_api:
        st.warning("Algumas ligas deram erro:")
        for erro in erros_api:
            st.write("-", erro)

    if not ranking:
        st.error("Nenhum jogo encontrado no período analisado.")
        return

    st.subheader("⭐ TOP 10 APOSTAS DO DIA")

    for score, j in ranking[:10]:
        st.write("---")
        st.write(j["jogo"])
        st.write(j["liga"])
        st.write("⚽ Gols esperados:", j["gols"])
        st.write("📈 Over 1.5:", f'{j["over15"]}%')
        st.write("📊 Over 2.5:", f'{j["over25"]}%')
        st.write("🤝 Ambas marcam:", f'{j["btts"]}%')
        st.write("💰 Odd justa Over 2.5:", j["odd"])
        st.write("⭐ Score total:", score)

    st.subheader("📊 TOP OVER 2.5")

    for j in over25[:10]:
        st.write("---")
        st.write(j["jogo"])
        st.write(j["liga"])
        st.write("Probabilidade:", f'{j["over25"]}%')
        st.write("Odd justa:", j["odd"])

    st.subheader("🤝 TOP AMBAS MARCAM")

    for j in btts[:10]:
        st.write("---")
        st.write(j["jogo"])
        st.write(j["liga"])
        st.write("Probabilidade:", f'{j["btts"]}%')

    st.subheader("⚽ TOP OVER 1.5")

    for j in over15[:10]:
        st.write("---")
        st.write(j["jogo"])
        st.write(j["liga"])
        st.write("Probabilidade:", f'{j["over15"]}%')


if st.button("🔎 ANALISAR JOGOS"):
    analisar()
