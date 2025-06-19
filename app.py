
import streamlit as st
import time
import threading
from fusion_bot import FusionBot
from estrategias import estrategia_6em7digit, estrategia_0matador, estrategia_4acima

st.set_page_config(page_title="Fusion Pro", layout="centered")
st.title("🤖 Fusion Pro - Robô Deriv")

st.markdown("### Conecte sua conta Deriv")
token = st.text_input("🔑 Cole seu Token da Deriv (real ou demo)", type="password")

estrategia_nome = st.selectbox("🎯 Estratégia", ["6em7Digit", "0Matador", "4acima"])
stake = st.number_input("💵 Stake inicial (USD)", value=1.0, step=0.1)
use_martingale = st.checkbox("🎲 Usar Martingale", value=True)
fator_martingale = st.number_input("🧮 Fator Martingale", value=2.0)
max_loss = st.number_input("⛔ Limite de perda (USD)", value=50.0)
max_profit = st.number_input("✅ Meta de lucro (USD)", value=100.0)
max_loss_seq = st.number_input("🔁 Máx. perdas seguidas", value=4)

if "bot" not in st.session_state:
    st.session_state.bot = None
if "thread" not in st.session_state:
    st.session_state.thread = None

col1, col2 = st.columns(2)
start = col1.button("🚀 Iniciar Robô")
stop = col2.button("🛑 Parar Robô")

def iniciar_bot():
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

def monitorar_bot():
    container = st.empty()
    while st.session_state.bot and st.session_state.bot.running:
        with container.container():
            st.info(f"📊 Status: {'Rodando' if st.session_state.bot.rodando else 'Parado'}")
            st.write("Histórico de operações (últimas 10):")
            st.table(st.session_state.bot.historico_operacoes[-10:])
        time.sleep(2)

if start and token:
    if not st.session_state.bot or not st.session_state.bot.running:
        iniciar_bot()
        st.session_state.thread = threading.Thread(target=monitorar_bot)
        st.session_state.thread.start()
    else:
        st.warning("Robô já está rodando!")

if stop and st.session_state.bot:
    st.session_state.bot.parar()
    st.success("Robô parado com sucesso!")
