
import websocket
import json
import threading
import time
from estrategias import estrategia_6em7digit, estrategia_0matador, estrategia_4acima

class FusionBot:
    def __init__(self, token, stake, use_martingale, fator_martingale, max_loss, max_profit, max_loss_seq, estrategia):
        self.token = token
        self.stake_inicial = stake
        self.stake = stake
        self.use_martingale = use_martingale
        self.fator_martingale = fator_martingale
        self.max_loss = max_loss
        self.max_profit = max_profit
        self.max_loss_seq = max_loss_seq
        self.estrategia = estrategia
        self.running = False
        self.rodando = False
        self.digitos = []
        self.historico_operacoes = []
        self.lucro_total = 0
        self.perdas_seguidas = 0
        self.contrato_ativo = False
        self.ws = None
        self.contract_id = None
        self.logs = []

    def log(self, mensagem):
        print(mensagem)
        self.logs.append(f"{time.strftime('%H:%M:%S')} - {mensagem}")
        if len(self.logs) > 100:
            self.logs.pop(0)

    def iniciar(self):
        self.running = True
        threading.Thread(target=self._run).start()

    def parar(self):
        self.running = False
        self.rodando = False
        self.log("🛑 Robô parado manualmente.")
        if self.ws:
            self.ws.close()

    def _run(self):
        self.ws = websocket.WebSocketApp(
            "wss://ws.derivws.com/websockets/v3?app_id=1089",
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        self.ws.run_forever()

    def on_open(self, ws):
        self.log("🔌 Conectando com Deriv...")
        ws.send(json.dumps({ "authorize": self.token }))

    def on_message(self, ws, message):
        data = json.loads(message)

        if "error" in data:
            self.log("❌ Erro: " + data["error"]["message"])
            self.parar()
            return

        if "authorize" in data:
            self.rodando = True
            self.log("✅ Conectado à Deriv com sucesso.")
            ws.send(json.dumps({ "ticks": "R_100" }))

        if "tick" in data:
            self.processar_tick(data["tick"]["quote"])

        if "buy" in data:
            self.contract_id = data["buy"]["contract_id"]
            self.contrato_ativo = True
            preco = float(data["buy"]["buy_price"])
            self.log(f"📤 Ordem enviada | Stake: ${preco:.2f} | Over 3")
            self.historico_operacoes.append({
                "entrada": self.estrategia,
                "status": "AGUARDANDO",
                "preco": preco
            })
            ws.send(json.dumps({
                "proposal_open_contract": 1,
                "contract_id": self.contract_id
            }))

        if "proposal_open_contract" in data:
            contrato = data["proposal_open_contract"]
            if contrato.get("is_expired", False):
                self.avaliar_resultado(contrato)
                self.contract_id = None
                self.contrato_ativo = False

    def processar_tick(self, quote):
        digito = int(str(quote)[-1])
        self.digitos.append(digito)
        if len(self.digitos) > 50:
            self.digitos.pop(0)

        self.log(f"📥 Tick recebido: {quote} => Dígito: {digito}")

        if self.running and not self.contrato_ativo and len(self.digitos) >= 8:
            if self.verificar_entrada():
                self.log("✅ Padrão identificado. Enviando ordem...")
                self.enviar_ordem(self.ws)
            else:
                self.log("⏳ Padrão ainda não identificado. Aguardando...")

    def verificar_entrada(self):
        if self.estrategia == "6em7Digit":
            return estrategia_6em7digit(self.digitos)
        elif self.estrategia == "0Matador":
            return estrategia_0matador(self.digitos)
        elif self.estrategia == "4acima":
            return estrategia_4acima(self.digitos)
        return False

    def enviar_ordem(self, ws):
        ordem = {
            "buy": "1",
            "price": str(round(self.stake, 2)),
            "parameters": {
                "amount": str(round(self.stake, 2)),
                "basis": "stake",
                "contract_type": "DIGITOVER",
                "barrier": "3",
                "currency": "USD",
                "duration": "1",
                "duration_unit": "t",
                "symbol": "R_100"
            }
        }
        ws.send(json.dumps(ordem))

    def avaliar_resultado(self, contrato):
        lucro = contrato.get("profit", 0.0)
        resultado = "WIN" if lucro > 0 else "LOSS"
        self.historico_operacoes[-1]["status"] = resultado
        self.historico_operacoes[-1]["lucro"] = lucro
        self.lucro_total += lucro
        self.log(f"🎯 Resultado: {resultado} | Lucro: ${lucro:.2f}")

        if resultado == "WIN":
            self.perdas_seguidas = 0
            self.stake = self.stake_inicial
            self.log("🎲 Resetando stake para valor inicial.")
        else:
            self.perdas_seguidas += 1
            if self.use_martingale:
                self.stake *= self.fator_martingale
                self.log(f"⚠️ Aplicando Martingale. Nova stake: ${self.stake:.2f}")

        if self.lucro_total <= -self.max_loss or self.lucro_total >= self.max_profit or self.perdas_seguidas >= self.max_loss_seq:
            self.log("🛑 Critério de parada atingido.")
            self.parar()

    def on_error(self, ws, error):
        self.log(f"❌ Erro WebSocket: {error}")

    def on_close(self, ws, code, msg):
        self.rodando = False
        self.log("🔌 Conexão encerrada.")
