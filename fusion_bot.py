
import websocket
import json
import threading
import time
from estrategias import estrategia_6em7digit, estrategia_0matador, estrategia_4acima

class FusionBot:
    def __init__(self, token, stake, use_martingale, fator_martingale, max_loss, max_profit, max_loss_seq, estrategia):
        self.token = token
        self.stake = stake
        self.use_martingale = use_martingale
        self.fator_martingale = fator_martingale
        self.max_loss = max_loss
        self.max_profit = max_profit
        self.max_loss_seq = max_loss_seq
        self.estrategia = estrategia
        self.ws = None
        self.running = False
        self.rodando = False
        self.historico_operacoes = []
        self.saldo = 0
        self.perdas_seguidas = 0
        self.lucro_total = 0
        self.stake_atual = stake
        self.lista_digitos = []

    def iniciar(self):
        self.running = True
        thread = threading.Thread(target=self.run)
        thread.start()

    def parar(self):
        self.running = False
        self.rodando = False
        if self.ws:
            self.ws.close()

    def run(self):
        self.ws = websocket.WebSocketApp(
            "wss://ws.derivws.com/websockets/v3?app_id=1089",
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        self.ws.run_forever()

    def on_open(self, ws):
        auth = {"authorize": self.token}
        ws.send(json.dumps(auth))
        self.rodando = True
        ticks = {"ticks": "R_100"}
        ws.send(json.dumps(ticks))

    def on_message(self, ws, message):
        data = json.loads(message)
        if "tick" in data:
            ultimo_digito = int(str(data["tick"]["quote"])[-1])
            self.lista_digitos.append(ultimo_digito)
            if len(self.lista_digitos) > 50:
                self.lista_digitos.pop(0)

            if self.running and len(self.lista_digitos) >= 8:
                if self.verificar_entrada():
                    self.enviar_ordem(ws)

        elif "buy" in data:
            self.historico_operacoes.append({"entrada": data["buy"]["contract_type"], "status": "AGUARDANDO", "preco": data["buy"]["buy_price"]})
        elif "proposal_open_contract" in data:
            status = data["proposal_open_contract"]["status"]
            lucro = data["proposal_open_contract"]["profit"]
            if status == "won":
                self.lucro_total += lucro
                self.perdas_seguidas = 0
                self.stake_atual = self.stake
                self.historico_operacoes[-1]["status"] = "WIN"
            elif status == "lost":
                self.lucro_total -= self.stake_atual
                self.perdas_seguidas += 1
                self.historico_operacoes[-1]["status"] = "LOSS"
                if self.use_martingale:
                    self.stake_atual *= self.fator_martingale

            if self.lucro_total <= -self.max_loss or self.lucro_total >= self.max_profit or self.perdas_seguidas >= self.max_loss_seq:
                self.parar()

    def on_error(self, ws, error): pass
    def on_close(self, ws, close_status_code, close_msg): self.rodando = False

    def verificar_entrada(self):
        if self.estrategia == "6em7Digit":
            return estrategia_6em7digit(self.lista_digitos)
        elif self.estrategia == "0Matador":
            return estrategia_0matador(self.lista_digitos)
        elif self.estrategia == "4acima":
            return estrategia_4acima(self.lista_digitos)
        return False

    def enviar_ordem(self, ws):
        proposal = {
            "buy": "1",
            "price": str(round(self.stake_atual, 2)),
            "parameters": {
                "amount": str(round(self.stake_atual, 2)),
                "basis": "stake",
                "contract_type": "DIGITOVER",
                "currency": "USD",
                "duration": "1",
                "duration_unit": "t",
                "symbol": "R_100",
                "barrier": "3"
            }
        }
        ws.send(json.dumps(proposal))
