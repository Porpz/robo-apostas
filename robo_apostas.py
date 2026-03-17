import streamlit as st
import requests
from datetime import datetime, timedelta

API_TOKEN = "845305378d0846c7b4ce6e9b12652ffd"

st.set_page_config(page_title="Robô PRO", layout="wide")
st.title("⚽ Robô PRO de Apostas")

LIGAS = {
    "BSA": "Brasileirão Série A"
}

def estatisticas_time(team_id):
    headers = {"X-Auth-Token": API_TOKEN}
    url = f"https://api.football-data.org/v4/teams/{team_id}/matches?status=FINISHED&limit=30"

    try:
        r = requests.get(url, headers=headers, timeout=15)

        if r.status_code != 200:
            return {}

        dados = r.json()

        casa_feitos = []
        casa_sofridos = []
        fora_feitos = []
        fora_sofridos = []

        for j in dados.get("matches", []):
            home_goals = j["score"]["fullTime"]["home"]
            away_goals = j["score"]["fullTime"]["away"]

            if home_goals is None or away_goals is None:
                continue

            if j["homeTeam"]["id"] == team_id:
                if len(casa_feitos) < 10:
                    casa_feitos.append(home_goals)
                    casa_sofridos.append(away_goals)
            else:
                if len(fora_feitos) < 10:
                    fora_feitos.append(away_goals)
                    fora_sofridos.append(home_goals)

        return {
            "casa_feitos": casa_feitos,
            "casa_sofridos": casa_sofridos,
            "fora_feitos": fora_feitos,
            "fora_sofridos": fora_sofridos
        }

    except Exception:
        return {}

def analisar():
    headers = {"X-Auth-Token": API_TOKEN}

    hoje = datetime.utcnow()
    inicio = hoje.strftime("%Y-%m-%d")
    fim = (hoje + timedelta(days=1)).strftime("%Y-%m-%d")

    url = f"https://api.football-data.org/v4/competitions/BSA/matches?dateFrom={inicio}&dateTo={fim}"

    try:
        r = requests.get(url, headers=headers, timeout=15)

        if r.status_code != 200:
            st.error(f"Erro API: {r.status_code}")
            return

        dados = r.json()
        jogos = []

        for j in dados.get("matches", []):
            if j.get("status") not in ["SCHEDULED", "TIMED"]:
                continue

            casa = j["homeTeam"]["name"]
            fora = j["awayTeam"]["name"]

            id_casa = j["homeTeam"]["id"]
            id_fora = j["awayTeam"]["id"]

            stats_casa = estatisticas_time(id_casa)
            stats_fora = estatisticas_time(id_fora)

            if not stats_casa or not stats_fora:
                continue

            casa_media_m = (
                sum(stats_casa["casa_feitos"]) / len(stats_casa["casa_feitos"])
                if stats_casa["casa_feitos"] else 0
            )
            casa_media_s = (
                sum(stats_casa["casa_sofridos"]) / len(stats_casa["casa_sofridos"])
                if stats_casa["casa_sofridos"] else 0
            )
            fora_media_m = (
                sum(stats_fora["fora_feitos"]) / len(stats_fora["fora_feitos"])
                if stats_fora["fora_feitos"] else 0
            )
            fora_media_s = (
                sum(stats_fora["fora_sofridos"]) / len(stats_fora["fora_sofridos"])
                if stats_fora["fora_sofridos"] else 0
            )

            prob_over25 = min(int(((casa_media_m + fora_media_m) / 2.5) * 100), 90)
            prob_btts = min(int(((casa_media_m + fora_media_m) / 2.4) * 100), 85)

            if prob_over25 > 65 and prob_btts > 60:
                sinal = "🔥 JOGO MUITO FORTE"
            elif prob_over25 > 55:
                sinal = "⚡ JOGO BOM"
            else:
                sinal = "🧊 JOGO FRACO"

            jogos.append({
                "jogo": f"{casa} x {fora}",
                "sinal": sinal,
                "prob_over25": prob_over25,
                "prob_btts": prob_btts,
                "stats_casa": stats_casa,
                "stats_fora": stats_fora,
                "casa": casa,
                "fora": fora
            })

        if not jogos:
            st.warning("Nenhum jogo encontrado")
            return

        for j in jogos:
            st.divider()
            st.subheader(f"⚽ {j['jogo']}")
            st.write(j["sinal"])

            st.write(f"🏠 {j['casa']} (CASA)")
            st.write("⚽ Gols feitos:", ", ".join(map(str, j["stats_casa"]["casa_feitos"])) or "Sem dados")
            st.write("🥅 Gols sofridos:", ", ".join(map(str, j["stats_casa"]["casa_sofridos"])) or "Sem dados")

            st.write(f"✈️ {j['fora']} (FORA)")
            st.write("⚽ Gols feitos:", ", ".join(map(str, j["stats_fora"]["fora_feitos"])) or "Sem dados")
            st.write("🥅 Gols sofridos:", ", ".join(map(str, j["stats_fora"]["fora_sofridos"])) or "Sem dados")

            st.write(f"📊 Prob Over 2.5: {j['prob_over25']}%")
            st.write(f"🤝 Prob Ambas Marcam: {j['prob_btts']}%")

    except Exception as e:
        st.error(f"Erro ao analisar: {e}")

if st.button("🔎 ANALISAR JOGOS"):
    analisar()
