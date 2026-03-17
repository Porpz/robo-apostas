import streamlit as st
import requests
from datetime import datetime, timedelta

API_TOKEN = "845305378d0846c7b4ce6e9b12652ffd"

st.set_page_config(page_title="Robô PRO", layout="wide")
st.title("⚽ Robô PRO de Apostas")

HEADERS = {"X-Auth-Token": API_TOKEN}


@st.cache_data(ttl=300)
def buscar_jogos_brasileirao(inicio, fim):
    url = f"https://api.football-data.org/v4/competitions/BSA/matches?dateFrom={inicio}&dateTo={fim}"
    r = requests.get(url, headers=HEADERS, timeout=20)
    return r.status_code, r.json() if r.status_code == 200 else {}


@st.cache_data(ttl=300)
def buscar_partidas_time(team_id):
    url = f"https://api.football-data.org/v4/teams/{team_id}/matches?status=FINISHED&limit=50"
    r = requests.get(url, headers=HEADERS, timeout=20)

    if r.status_code == 429:
        return 429, {}
    if r.status_code != 200:
        return r.status_code, {}

    return 200, r.json()


def estatisticas_time(team_id):
    status, dados = buscar_partidas_time(team_id)

    if status != 200:
        return {"erro": status}

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

        if len(casa_feitos) >= 10 and len(fora_feitos) >= 10:
            break

    return {
        "casa_feitos": casa_feitos,
        "casa_sofridos": casa_sofridos,
        "fora_feitos": fora_feitos,
        "fora_sofridos": fora_sofridos
    }


def media(lista):
    return round(sum(lista) / len(lista), 2) if lista else 0.0


def odd_justa(prob_percent):
    if prob_percent <= 0:
        return 0.0
    return round(100 / prob_percent, 2)


def analisar_jogo(stats_casa, stats_fora):
    casa_feitos = stats_casa["casa_feitos"]
    casa_sofridos = stats_casa["casa_sofridos"]
    fora_feitos = stats_fora["fora_feitos"]
    fora_sofridos = stats_fora["fora_sofridos"]

    media_casa_feitos = media(casa_feitos)
    media_casa_sofridos = media(casa_sofridos)
    media_fora_feitos = media(fora_feitos)
    media_fora_sofridos = media(fora_sofridos)

    # modelo mais preciso cruzando ataque e defesa
    expectativa_gols_casa = round((media_casa_feitos + media_fora_sofridos) / 2, 2)
    expectativa_gols_fora = round((media_fora_feitos + media_casa_sofridos) / 2, 2)
    gols_esperados = round(expectativa_gols_casa + expectativa_gols_fora, 2)

    # padrões históricos casa/fora
    over25_casa = sum(1 for f, s in zip(casa_feitos, casa_sofridos) if (f + s) >= 3)
    over25_fora = sum(1 for f, s in zip(fora_feitos, fora_sofridos) if (f + s) >= 3)
    total_jogos_over25 = len(casa_feitos) + len(fora_feitos)
    base_over25 = int(((over25_casa + over25_fora) / total_jogos_over25) * 100) if total_jogos_over25 else 0

    btts_casa = sum(1 for f, s in zip(casa_feitos, casa_sofridos) if f > 0 and s > 0)
    btts_fora = sum(1 for f, s in zip(fora_feitos, fora_sofridos) if f > 0 and s > 0)
    total_jogos_btts = len(casa_feitos) + len(fora_feitos)
    base_btts = int(((btts_casa + btts_fora) / total_jogos_btts) * 100) if total_jogos_btts else 0

    over15_casa = sum(1 for f, s in zip(casa_feitos, casa_sofridos) if (f + s) >= 2)
    over15_fora = sum(1 for f, s in zip(fora_feitos, fora_sofridos) if (f + s) >= 2)
    total_jogos_over15 = len(casa_feitos) + len(fora_feitos)
    base_over15 = int(((over15_casa + over15_fora) / total_jogos_over15) * 100) if total_jogos_over15 else 0

    # ajuste por gols esperados
    ajuste_over15 = min(int((gols_esperados / 1.8) * 10), 15)
    ajuste_over25 = min(int((gols_esperados / 2.6) * 12), 18)
    ajuste_btts = min(int(((expectativa_gols_casa + expectativa_gols_fora) / 2.4) * 10), 15)

    prob_over15 = min(base_over15 + ajuste_over15, 95)
    prob_over25 = min(base_over25 + ajuste_over25, 90)
    prob_btts = min(base_btts + ajuste_btts, 85)

    if prob_over25 >= 72 and prob_btts >= 62:
        sinal = "🔥 JOGO MUITO FORTE"
        mercado = "Over 2.5 / Ambas Marcam"
        confianca = "Alta"
    elif prob_over25 >= 63:
        sinal = "⚡ JOGO BOM"
        mercado = "Over 2.5"
        confianca = "Média"
    elif prob_over15 >= 78:
        sinal = "✅ JOGO INTERESSANTE"
        mercado = "Over 1.5"
        confianca = "Média"
    else:
        sinal = "🧊 JOGO FRACO"
        mercado = "Evitar ou analisar melhor"
        confianca = "Baixa"

    return {
        "media_casa_feitos": media_casa_feitos,
        "media_casa_sofridos": media_casa_sofridos,
        "media_fora_feitos": media_fora_feitos,
        "media_fora_sofridos": media_fora_sofridos,
        "expectativa_gols_casa": expectativa_gols_casa,
        "expectativa_gols_fora": expectativa_gols_fora,
        "gols_esperados": gols_esperados,
        "prob_over15": prob_over15,
        "prob_over25": prob_over25,
        "prob_btts": prob_btts,
        "odd_justa_over15": odd_justa(prob_over15),
        "odd_justa_over25": odd_justa(prob_over25),
        "odd_justa_btts": odd_justa(prob_btts),
        "sinal": sinal,
        "mercado": mercado,
        "confianca": confianca
    }


def mostrar_lista_rotulo(rotulo, lista):
    if lista:
        st.write(f"{rotulo} {', '.join(map(str, lista))}")
    else:
        st.write(f"{rotulo} Sem dados")


def mostrar_value(nome_mercado, prob, odd_modelo, chave):
    odd_usuario = st.number_input(
        f"Odd da casa para {nome_mercado}",
        min_value=1.01,
        step=0.01,
        key=chave
    )

    st.write(f"Odd justa {nome_mercado}: {odd_modelo}")

    if odd_usuario > 1.01:
        edge = round(((odd_usuario / odd_modelo) - 1) * 100, 2) if odd_modelo > 0 else 0

        if odd_usuario > odd_modelo:
            st.success(f"💰 VALUE BET DETECTADA | Valor: +{edge}%")
        else:
            st.warning(f"❌ Sem valor | Diferença: {edge}%")


def analisar():
    hoje = datetime.utcnow()
    inicio = hoje.strftime("%Y-%m-%d")
    fim = (hoje + timedelta(days=1)).strftime("%Y-%m-%d")

    status, dados = buscar_jogos_brasileirao(inicio, fim)

    if status == 429:
        st.error("Erro API 429: limite atingido. Espere 1 a 2 minutos e teste novamente.")
        return

    if status != 200:
        st.error(f"Erro API: {status}")
        return

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

        if stats_casa.get("erro") == 429 or stats_fora.get("erro") == 429:
            st.error("Erro API 429 nas estatísticas dos times. Espere 1 a 2 minutos e teste novamente.")
            return

        if "erro" in stats_casa or "erro" in stats_fora:
            continue

        analise = analisar_jogo(stats_casa, stats_fora)

        score = (
            analise["prob_over15"] +
            analise["prob_over25"] +
            analise["prob_btts"]
        )

        jogos.append({
            "jogo": f"{casa} x {fora}",
            "casa": casa,
            "fora": fora,
            "stats_casa": stats_casa,
            "stats_fora": stats_fora,
            "analise": analise,
            "score": score
        })

    jogos.sort(key=lambda x: x["score"], reverse=True)

    if not jogos:
        st.warning("Nenhum jogo encontrado para hoje e amanhã.")
        return

    st.subheader("⭐ TOP APOSTAS")

    for item in jogos[:10]:
        casa = item["casa"]
        fora = item["fora"]
        stats_casa = item["stats_casa"]
        stats_fora = item["stats_fora"]
        a = item["analise"]

        st.divider()
        st.subheader(f"⚽ {item['jogo']}")
        st.write(a["sinal"])
        st.write(f"**Mercado principal:** {a['mercado']}")
        st.write(f"**Confiança:** {a['confianca']}")
        st.write(
            f"**Base usada:** {casa} em casa: {len(stats_casa['casa_feitos'])} jogos | "
            f"{fora} fora: {len(stats_fora['fora_feitos'])} jogos"
        )

        col1, col2 = st.columns(2)

        with col1:
            st.write(f"### 🏠 {casa} (CASA)")
            mostrar_lista_rotulo("⚽ Gols feitos:", stats_casa["casa_feitos"])
            mostrar_lista_rotulo("🥅 Gols sofridos:", stats_casa["casa_sofridos"])
            st.write(f"Média feitos: {a['media_casa_feitos']}")
            st.write(f"Média sofridos: {a['media_casa_sofridos']}")

        with col2:
            st.write(f"### ✈️ {fora} (FORA)")
            mostrar_lista_rotulo("⚽ Gols feitos:", stats_fora["fora_feitos"])
            mostrar_lista_rotulo("🥅 Gols sofridos:", stats_fora["fora_sofridos"])
            st.write(f"Média feitos: {a['media_fora_feitos']}")
            st.write(f"Média sofridos: {a['media_fora_sofridos']}")

        st.write(f"**⚽ Expectativa de gols do {casa}:** {a['expectativa_gols_casa']}")
        st.write(f"**⚽ Expectativa de gols do {fora}:** {a['expectativa_gols_fora']}")
        st.write(f"**⚽ Gols esperados totais:** {a['gols_esperados']}")
        st.write(f"**📈 Prob Over 1.5:** {a['prob_over15']}%")
        st.write(f"**📊 Prob Over 2.5:** {a['prob_over25']}%")
        st.write(f"**🤝 Prob Ambas Marcam:** {a['prob_btts']}%")

        st.write("### 💰 Value Bet")
        c1, c2, c3 = st.columns(3)

        with c1:
            mostrar_value("Over 1.5", a["prob_over15"], a["odd_justa_over15"], f"{casa}_{fora}_over15")
        with c2:
            mostrar_value("Over 2.5", a["prob_over25"], a["odd_justa_over25"], f"{casa}_{fora}_over25")
        with c3:
            mostrar_value("Ambas Marcam", a["prob_btts"], a["odd_justa_btts"], f"{casa}_{fora}_btts")


if st.button("🔎 ANALISAR JOGOS"):
    analisar()
