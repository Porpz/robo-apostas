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
st.title("⚽ Robô Profissional de Apostas")

def estatisticas_time(team_id):

    headers = {"X-Auth-Token": API_TOKEN}
    url = f"https://api.football-data.org/v4/teams/{team_id}/matches?status=FINISHED&limit=8"

    try:
        r = requests.get(url, headers=headers, timeout=15)

        if r.status_code != 200:
            return 1.2,1.2

        dados = r.json()

        gm, gs, jogos = 0, 0, 0

        for j in dados.get("matches", []):

            if j["homeTeam"]["id"] == team_id:
                g_m = j["score"]["fullTime"]["home"]
                g_s = j["score"]["fullTime"]["away"]
            else:
                g_m = j["score"]["fullTime"]["away"]
                g_s = j["score"]["fullTime"]["home"]

            if g_m is None:
                continue

            gm += g_m
            gs += g_s
            jogos += 1

        if jogos == 0:
            return 1.2,1.2

        return gm/jogos, gs/jogos

    except:
        return 1.2,1.2


def analisar():

    headers = {"X-Auth-Token": API_TOKEN}

    hoje = datetime.utcnow()

    # 🔥 AGORA SÓ 2 DIAS
    inicio = hoje.strftime("%Y-%m-%d")
    fim = (hoje + timedelta(days=1)).strftime("%Y-%m-%d")

    ranking = []

    for codigo, nome in LIGAS.items():

        url = f"https://api.football-data.org/v4/competitions/{codigo}/matches?dateFrom={inicio}&dateTo={fim}"

        try:
            r = requests.get(url, headers=headers, timeout=15)

            if r.status_code != 200:
                continue

            dados = r.json()

            for j in dados.get("matches", []):

                if j.get("status") not in ["SCHEDULED","TIMED"]:
                    continue

                casa = j["homeTeam"]["name"]
                fora = j["awayTeam"]["name"]

                id_casa = j["homeTeam"]["id"]
                id_fora = j["awayTeam"]["id"]

                ataque_casa,defesa_casa = estatisticas_time(id_casa)
                ataque_fora,defesa_fora = estatisticas_time(id_fora)

                # 🧠 cálculo melhorado
                gols = (
                    ataque_casa*0.45 +
                    ataque_fora*0.45 +
                    defesa_casa*0.05 +
                    defesa_fora*0.05
                )

                prob_over15 = min(int((gols/2)*100),95)
                prob_over25 = min(int((gols/2.8)*100),90)
                prob_btts = min(int(((ataque_casa+ataque_fora)/2.6)*100),85)

                odd_justa = round(100/prob_over25,2) if prob_over25>0 else 0

                score = prob_over15 + prob_over25 + prob_btts

                # 🔥 DETECÇÃO JOGO FORTE
                forte = ""
                if prob_over25 > 65 and prob_btts > 60:
                    forte = "🔥 JOGO MUITO FORTE"

                elif prob_over25 > 60:
                    forte = "⚡ JOGO FORTE"

                jogo = {
                    "jogo": f"{casa} x {fora}",
                    "liga": nome,
                    "gols": round(gols,2),
                    "over15": prob_over15,
                    "over25": prob_over25,
                    "btts": prob_btts,
                    "odd": odd_justa,
                    "score": score,
                    "forte": forte
                }

                # filtro inteligente
                if prob_over15 > 65:
                    ranking.append(jogo)

        except:
            continue

    # ordena melhor
    ranking.sort(key=lambda x: x["score"], reverse=True)

    if not ranking:
        st.warning("Nenhum jogo encontrado nos próximos 2 dias")
        return

    st.subheader("⭐ TOP APOSTAS (HOJE E AMANHÃ)")

    for j in ranking[:10]:

        st.write("---")
        st.write(j["jogo"])
        st.write(j["liga"])

        if j["forte"]:
            st.write(j["forte"])

        st.write("⚽ Gols esperados:", j["gols"])
        st.write("📈 Over 1.5:", j["over15"],"%")
        st.write("📊 Over 2.5:", j["over25"],"%")
        st.write("🤝 Ambas marcam:", j["btts"],"%")
        st.write("💰 Odd justa:", j["odd"])
        st.write("⭐ Score:", j["score"])


if st.button("🔎 ANALISAR JOGOS"):
    analisar()
