import streamlit as st
import requests
from datetime import datetime, timedelta
import pandas as pd

API_TOKEN = "845305378d0846c7b4ce6e9b12652ffd"

st.set_page_config(page_title="Robô PRO", layout="wide")
st.title("⚽ Robô PRO de Apostas")

HEADERS = {"X-Auth-Token": API_TOKEN}

if "analisar" not in st.session_state:
    st.session_state.analisar = False

if "historico" not in st.session_state:
    st.session_state.historico = []

st.markdown("""
<style>
.card {
    background-color: #111827;
    padding: 18px;
    border-radius: 16px;
    margin-bottom: 18px;
    border: 1px solid #374151;
    box-shadow: 0 4px 12px rgba(0,0,0,0.25);
}
.badge {
    display: inline-block;
    padding: 6px 10px;
    border-radius: 999px;
    font-size: 13px;
    font-weight: 700;
    margin-right: 8px;
    margin-bottom: 8px;
}
.badge-strong {
    background: #065f46;
    color: #d1fae5;
}
.badge-good {
    background: #1e3a8a;
    color: #dbeafe;
}
.badge-weak {
    background: #7f1d1d;
    color: #fee2e2;
}
.stat-box {
    background: #1f2937;
    padding: 10px 12px;
    border-radius: 12px;
    margin-bottom: 8px;
}
.small-title {
    font-size: 12px;
    color: #9ca3af;
    margin-bottom: 4px;
}
.big-number {
    font-size: 20px;
    font-weight: 700;
}
hr.custom {
    border: none;
    border-top: 1px solid #374151;
    margin: 14px 0;
}
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=300)
def buscar_jogos_brasileirao(inicio, fim):
    url = f"https://api.football-data.org/v4/competitions/BSA/matches?dateFrom={inicio}&dateTo={fim}"
    r = requests.get(url, headers=HEADERS, timeout=20)
    return r.status_code, r.json() if r.status_code == 200 else {}


@st.cache_data(ttl=300)
def buscar_historico_brasileirao():
    url = "https://api.football-data.org/v4/competitions/BSA/matches?status=FINISHED"
    r = requests.get(url, headers=HEADERS, timeout=20)
    return r.status_code, r.json() if r.status_code == 200 else {}


def construir_stats_time(team_id, matches):
    matches_ordenadas = sorted(matches, key=lambda j: j.get("utcDate", ""), reverse=True)

    gerais_feitos = []
    gerais_sofridos = []
    casa_feitos = []
    casa_sofridos = []
    fora_feitos = []
    fora_sofridos = []

    for j in matches_ordenadas:
        home_goals = j["score"]["fullTime"]["home"]
        away_goals = j["score"]["fullTime"]["away"]

        if home_goals is None or away_goals is None:
            continue

        if j["homeTeam"]["id"] == team_id:
            feitos = home_goals
            sofridos = away_goals

            if len(casa_feitos) < 10:
                casa_feitos.append(feitos)
                casa_sofridos.append(sofridos)

        elif j["awayTeam"]["id"] == team_id:
            feitos = away_goals
            sofridos = home_goals

            if len(fora_feitos) < 10:
                fora_feitos.append(feitos)
                fora_sofridos.append(sofridos)
        else:
            continue

        if len(gerais_feitos) < 10:
            gerais_feitos.append(feitos)
            gerais_sofridos.append(sofridos)

        if (
            len(gerais_feitos) >= 10 and
            len(casa_feitos) >= 10 and
            len(fora_feitos) >= 10
        ):
            break

    return {
        "gerais_feitos": gerais_feitos,
        "gerais_sofridos": gerais_sofridos,
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

    expectativa_gols_casa = round((media_casa_feitos + media_fora_sofridos) / 2, 2)
    expectativa_gols_fora = round((media_fora_feitos + media_casa_sofridos) / 2, 2)
    gols_esperados = round(expectativa_gols_casa + expectativa_gols_fora, 2)

    over25_casa = sum(1 for f, s in zip(casa_feitos, casa_sofridos) if (f + s) >= 3)
    over25_fora = sum(1 for f, s in zip(fora_feitos, fora_sofridos) if (f + s) >= 3)
    total_over25 = len(casa_feitos) + len(fora_feitos)
    base_over25 = int(((over25_casa + over25_fora) / total_over25) * 100) if total_over25 else 0

    btts_casa = sum(1 for f, s in zip(casa_feitos, casa_sofridos) if f > 0 and s > 0)
    btts_fora = sum(1 for f, s in zip(fora_feitos, fora_sofridos) if f > 0 and s > 0)
    total_btts = len(casa_feitos) + len(fora_feitos)
    base_btts = int(((btts_casa + btts_fora) / total_btts) * 100) if total_btts else 0

    over15_casa = sum(1 for f, s in zip(casa_feitos, casa_sofridos) if (f + s) >= 2)
    over15_fora = sum(1 for f, s in zip(fora_feitos, fora_sofridos) if (f + s) >= 2)
    total_over15 = len(casa_feitos) + len(fora_feitos)
    base_over15 = int(((over15_casa + over15_fora) / total_over15) * 100) if total_over15 else 0

    ajuste_over15 = min(int((gols_esperados - 1.5) * 8), 8) if gols_esperados > 1.5 else 0
    ajuste_over25 = min(int((gols_esperados - 2.2) * 10), 10) if gols_esperados > 2.2 else 0
    ajuste_btts = min(int(min(expectativa_gols_casa, expectativa_gols_fora) * 8), 8)

    prob_over15 = min(max(base_over15 + ajuste_over15, 5), 85)
    prob_over25 = min(max(base_over25 + ajuste_over25, 5), 75)
    prob_btts = min(max(base_btts + ajuste_btts, 5), 68)

    if prob_over25 >= 68 and prob_btts >= 58:
        sinal = "🔥 JOGO MUITO FORTE"
        mercado = "Over 2.5 / Ambas Marcam"
        confianca = "Alta"
        badge = "strong"
    elif prob_over25 >= 60:
        sinal = "⚡ JOGO BOM"
        mercado = "Over 2.5"
        confianca = "Média"
        badge = "good"
    elif prob_over15 >= 72:
        sinal = "✅ JOGO INTERESSANTE"
        mercado = "Over 1.5"
        confianca = "Média"
        badge = "good"
    else:
        sinal = "🧊 JOGO FRACO"
        mercado = "Evitar ou analisar melhor"
        confianca = "Baixa"
        badge = "weak"

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
        "confianca": confianca,
        "badge": badge
    }


def lista_texto(lista):
    return ", ".join(map(str, lista)) if lista else "Sem dados"


def registrar_historico(jogo, mercado, odd_usuario, odd_justa_modelo, stake):
    edge = round(((odd_usuario / odd_justa_modelo) - 1) * 100, 2) if odd_justa_modelo > 0 else 0
    st.session_state.historico.append({
        "Jogo": jogo,
        "Mercado": mercado,
        "Odd da casa": odd_usuario,
        "Odd justa": odd_justa_modelo,
        "Edge %": edge,
        "Stake": stake,
        "Resultado": "Pendente",
        "Lucro": 0.0
    })


def atualizar_resultado_aposta(index, resultado):
    aposta = st.session_state.historico[index]
    stake = float(aposta["Stake"])
    odd = float(aposta["Odd da casa"])

    aposta["Resultado"] = resultado

    if resultado == "Green":
        aposta["Lucro"] = round((stake * odd) - stake, 2)
    elif resultado == "Red":
        aposta["Lucro"] = round(-stake, 2)
    else:
        aposta["Lucro"] = 0.0


def mostrar_value(jogo, nome_mercado, odd_modelo, chave):
    odd_usuario = st.number_input(
        f"Odd da casa para {nome_mercado}",
        min_value=1.01,
        step=0.01,
        key=f"{chave}_odd"
    )

    stake = st.number_input(
        f"Stake para {nome_mercado}",
        min_value=0.0,
        step=1.0,
        key=f"{chave}_stake"
    )

    st.write(f"Odd justa: {odd_modelo}")

    if odd_usuario > 1.01:
        edge = round(((odd_usuario / odd_modelo) - 1) * 100, 2) if odd_modelo > 0 else 0

        if odd_usuario > odd_modelo:
            st.success(f"💰 VALUE BET | +{edge}%")
        else:
            st.warning(f"❌ Sem valor | {edge}%")

        if st.button(f"Salvar no histórico - {nome_mercado}", key=f"{chave}_save"):
            registrar_historico(jogo, nome_mercado, odd_usuario, odd_modelo, stake)
            st.success("Aposta salva no histórico.")


def mostrar_painel_lucro():
    st.subheader("📊 Painel de Lucro")

    if not st.session_state.historico:
        st.info("Nenhuma aposta no histórico ainda.")
        return

    total_apostas = len(st.session_state.historico)
    total_stake = sum(float(a["Stake"]) for a in st.session_state.historico)
    lucro_total = sum(float(a["Lucro"]) for a in st.session_state.historico)

    greens = sum(1 for a in st.session_state.historico if a["Resultado"] == "Green")
    reds = sum(1 for a in st.session_state.historico if a["Resultado"] == "Red")
    resolvidas = greens + reds

    taxa_acerto = round((greens / resolvidas) * 100, 2) if resolvidas > 0 else 0.0
    roi = round((lucro_total / total_stake) * 100, 2) if total_stake > 0 else 0.0

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.metric("Apostas", total_apostas)
    with c2:
        st.metric("Total apostado", f"R$ {total_stake:.2f}")
    with c3:
        st.metric("Lucro", f"R$ {lucro_total:.2f}")
    with c4:
        st.metric("ROI", f"{roi:.2f}%")
    with c5:
        st.metric("Taxa acerto", f"{taxa_acerto:.2f}%")

    st.write(f"✅ Greens: {greens} | ❌ Reds: {reds} | ⏳ Pendentes: {total_apostas - resolvidas}")


def analisar():
    hoje = datetime.utcnow()
    inicio = hoje.strftime("%Y-%m-%d")
    fim = (hoje + timedelta(days=1)).strftime("%Y-%m-%d")

    status_jogos, dados_jogos = buscar_jogos_brasileirao(inicio, fim)
    status_hist, dados_hist = buscar_historico_brasileirao()

    if status_jogos == 429 or status_hist == 429:
        st.error("Erro API 429: limite atingido. Espere 1 a 2 minutos e teste novamente.")
        return

    if status_jogos != 200 or status_hist != 200:
        st.error("Erro ao buscar dados do Brasileirão.")
        return

    historico_matches = dados_hist.get("matches", [])
    jogos = []

    for j in dados_jogos.get("matches", []):
        if j.get("status") not in ["SCHEDULED", "TIMED"]:
            continue

        casa = j["homeTeam"]["name"]
        fora = j["awayTeam"]["name"]
        id_casa = j["homeTeam"]["id"]
        id_fora = j["awayTeam"]["id"]

        stats_casa = construir_stats_time(id_casa, historico_matches)
        stats_fora = construir_stats_time(id_fora, historico_matches)

        analise = analisar_jogo(stats_casa, stats_fora)

        score = analise["prob_over15"] + analise["prob_over25"] + analise["prob_btts"]

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

    mostrar_painel_lucro()

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
        jogo_nome = item["jogo"]

        badge_class = (
            "badge-strong" if a["badge"] == "strong"
            else "badge-good" if a["badge"] == "good"
            else "badge-weak"
        )

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f"<h3>⚽ {jogo_nome}</h3>", unsafe_allow_html=True)
        st.markdown(
            f'<span class="badge {badge_class}">{a["sinal"]}</span>'
            f'<span class="badge badge-good">Mercado: {a["mercado"]}</span>'
            f'<span class="badge badge-good">Confiança: {a["confianca"]}</span>',
            unsafe_allow_html=True
        )

        st.write(
            f"**Base usada:** {casa} em casa: {len(stats_casa['casa_feitos'])} jogos | "
            f"{fora} fora: {len(stats_fora['fora_feitos'])} jogos | "
            f"{casa} gerais: {len(stats_casa['gerais_feitos'])} jogos | "
            f"{fora} gerais: {len(stats_fora['gerais_feitos'])} jogos"
        )

        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown('<div class="stat-box"><div class="small-title">Gols esperados</div>'
                        f'<div class="big-number">{a["gols_esperados"]}</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="stat-box"><div class="small-title">Prob Over 2.5</div>'
                        f'<div class="big-number">{a["prob_over25"]}%</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown('<div class="stat-box"><div class="small-title">Prob Ambas</div>'
                        f'<div class="big-number">{a["prob_btts"]}%</div></div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"### 🏠 {casa} (CASA)")
            st.write(f"⚽ Gols feitos em casa: {lista_texto(stats_casa['casa_feitos'])}")
            st.write(f"🥅 Gols sofridos em casa: {lista_texto(stats_casa['casa_sofridos'])}")
            st.write(f"⚽ Últimos 10 gerais feitos: {lista_texto(stats_casa['gerais_feitos'])}")
            st.write(f"🥅 Últimos 10 gerais sofridos: {lista_texto(stats_casa['gerais_sofridos'])}")
            st.write(f"Média feitos em casa: {a['media_casa_feitos']}")
            st.write(f"Média sofridos em casa: {a['media_casa_sofridos']}")

        with col2:
            st.markdown(f"### ✈️ {fora} (FORA)")
            st.write(f"⚽ Gols feitos fora: {lista_texto(stats_fora['fora_feitos'])}")
            st.write(f"🥅 Gols sofridos fora: {lista_texto(stats_fora['fora_sofridos'])}")
            st.write(f"⚽ Últimos 10 gerais feitos: {lista_texto(stats_fora['gerais_feitos'])}")
            st.write(f"🥅 Últimos 10 gerais sofridos: {lista_texto(stats_fora['gerais_sofridos'])}")
            st.write(f"Média feitos fora: {a['media_fora_feitos']}")
            st.write(f"Média sofridos fora: {a['media_fora_sofridos']}")

        st.markdown('<hr class="custom">', unsafe_allow_html=True)
        st.markdown("### 💰 Value Bet")
        v1, v2, v3 = st.columns(3)

        with v1:
            mostrar_value(jogo_nome, "Over 1.5", a["odd_justa_over15"], f"{casa}_{fora}_over15")
        with v2:
            mostrar_value(jogo_nome, "Over 2.5", a["odd_justa_over25"], f"{casa}_{fora}_over25")
        with v3:
            mostrar_value(jogo_nome, "Ambas Marcam", a["odd_justa_btts"], f"{casa}_{fora}_btts")

        st.markdown('</div>', unsafe_allow_html=True)

    st.subheader("📒 Histórico de Apostas")

    if st.session_state.historico:
        for i, aposta in enumerate(st.session_state.historico):
            st.markdown(f"**{aposta['Jogo']}** | {aposta['Mercado']}")
            st.write(
                f"Odd casa: {aposta['Odd da casa']} | Odd justa: {aposta['Odd justa']} | "
                f"Stake: R$ {float(aposta['Stake']):.2f} | Edge: {aposta['Edge %']}% | "
                f"Resultado: {aposta['Resultado']} | Lucro: R$ {float(aposta['Lucro']):.2f}"
            )

            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("✅ Green", key=f"green_{i}"):
                    atualizar_resultado_aposta(i, "Green")
            with c2:
                if st.button("❌ Red", key=f"red_{i}"):
                    atualizar_resultado_aposta(i, "Red")
            with c3:
                if st.button("⏳ Pendente", key=f"pend_{i}"):
                    atualizar_resultado_aposta(i, "Pendente")

            st.divider()

        df = pd.DataFrame(st.session_state.historico)
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Baixar histórico em CSV",
            csv,
            file_name="historico_apostas.csv",
            mime="text/csv"
        )
    else:
        st.info("Nenhuma aposta salva no histórico ainda.")


if st.button("🔎 ANALISAR JOGOS"):
    st.session_state.analisar = True

if st.session_state.analisar:
    analisar()
