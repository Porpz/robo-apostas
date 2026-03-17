import streamlit as st
import requests
from datetime import datetime, timedelta

API_KEY = "SEU_TOKEN_AQUI"

headers = {
    "x-apisports-key": API_KEY
}

# =========================
# FUNÇÃO BUSCAR JOGOS
# =========================
def buscar_jogos():
    hoje = datetime.now().strftime("%Y-%m-%d")

    url = f"https://v3.football.api-sports.io/fixtures?date={hoje}"

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        st.error(f"Erro API: {response.status_code}")
        return []

    dados = response.json()

    jogos_filtrados = []

    ligas_desejadas = [
        71,   # Brasileirão Série A
        72,   # Série B
        13,   # Libertadores
        11    # Sul-Americana
    ]

    for jogo in dados["response"]:
        liga_id = jogo["league"]["id"]

        if liga_id in ligas_desejadas:
            jogos_filtrados.append(jogo)

    return jogos_filtrados


# =========================
# FUNÇÃO PEGAR ÚLTIMOS JOGOS
# =========================
def ultimos_jogos(time_id):
    url = f"https://v3.football.api-sports.io/fixtures?team={time_id}&last=10"

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return []

    return response.json()["response"]


# =========================
# FUNÇÃO CALCULAR ESTATÍSTICAS
# =========================
def calcular_stats(time_id, is_home=True):
    jogos = ultimos_jogos(time_id)

    feitos = []
    sofridos = []

    for jogo in jogos:
        if is_home:
            if jogo["teams"]["home"]["id"] == time_id:
                feitos.append(jogo["goals"]["home"])
                sofridos.append(jogo["goals"]["away"])
        else:
            if jogo["teams"]["away"]["id"] == time_id:
                feitos.append(jogo["goals"]["away"])
                sofridos.append(jogo["goals"]["home"])

    return feitos, sofridos


# =========================
# INTERFACE
# =========================
st.title("🤖 ROBÔ PROFISSIONAL DE APOSTAS")

if st.button("🔎 ANALISAR JOGOS"):

    st.write("Buscando jogos...")

    jogos = buscar_jogos()

    if not jogos:
        st.warning("Nenhum jogo encontrado hoje.")
    else:
        for jogo in jogos:

            casa = jogo["teams"]["home"]["name"]
            fora = jogo["teams"]["away"]["name"]

            casa_id = jogo["teams"]["home"]["id"]
            fora_id = jogo["teams"]["away"]["id"]

            st.divider()
            st.subheader(f"⚽ {casa} x {fora}")

            # =========================
            # TIME CASA
            # =========================
            feitos_casa, sofridos_casa = calcular_stats(casa_id, True)

            st.write(f"🏠 {casa}")

            if feitos_casa:
                st.write("⚽ Gols feitos:", ", ".join(map(str, feitos_casa)))
                st.write("🥅 Gols sofridos:", ", ".join(map(str, sofridos_casa)))
            else:
                st.write("Sem dados suficientes")

            # =========================
            # TIME FORA
            # =========================
            feitos_fora, sofridos_fora = calcular_stats(fora_id, False)

            st.write(f"✈️ {fora}")

            if feitos_fora:
                st.write("⚽ Gols feitos:", ", ".join(map(str, feitos_fora)))
                st.write("🥅 Gols sofridos:", ", ".join(map(str, sofridos_fora)))
            else:
                st.write("Sem dados suficientes")
