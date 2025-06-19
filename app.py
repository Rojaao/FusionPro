
import streamlit as st
from fusion_bot import FusionBot
from estrategias import estrategia_6em7digit, estrategia_0matador, estrategia_4acima

st.set_page_config(page_title="Fusion Pro", layout="centered")
st.title("🤖 Fusion Pro - Robô Deriv")

st.markdown("### Conecte sua conta Deriv")
token = st.text_input("🔑 Cole seu Token da Deriv (real ou demo)", type="password")

# Estratégia
estrategia_nome = st.selectbox("🎯 Estratégia", ["6em7Digit", "0Matador", "4acima"])
stake = st.number_input("💵 Stake inicial (USD)", value=1.0, step=0.1)
use_martingale = st.checkbox("🎲 Usar Martingale", value=True)
fator_martingale = st.number_input("🧮 Fator Martingale", value=2.0)
max_loss = st.number_input("⛔ Limite de perda (USD)", value=50.0)
max_profit = st.number_input("✅ Meta de lucro (USD)", value=100.0)
max_loss_seq = st.number_input("🔁 Máx. perdas seguidas", value=4)

if "bot" not in st.session_state:
    st.session_state.bot = None

col1, col2 = st.columns(2)
start = col1.button("🚀 Iniciar Robô")
stop = col2.button("🛑 Parar Robô")

if start and token:
    with st.spinner("Conectando e iniciando o robô..."):
        st.session_state.bot = FusionBot(
            token=token,
            stake=stake,
            use_martingale=use_martingale,
            fator_martingale=fator_martingale,
            max_loss=max_loss,
            max_profit=max_profit,
            max_loss_seq=max_loss_seq,
            estrategia=estrategia_nome
        )
        st.session_state.bot.iniciar()

if stop and st.session_state.bot:
    st.session_state.bot.parar()
    st.success("Robô parado com sucesso!")

if st.session_state.bot:
    st.info(f"📊 Status: {'Rodando' if st.session_state.bot.rodando else 'Parado'}")
    st.write("Histórico de operações:")
    st.table(st.session_state.bot.historico_operacoes[-10:])  # últimas 10
