
import websocket
import json
import threading
import time
from estrategias import estrategia_6em7digit, estrategia_0matador, estrategia_4acima

class FusionBot:
    def __init__(self, token, stake, use_martingale, fator_martingale, max_loss, max_profit, max_loss_seq, estrategia):
        self.token = token
        self.stake = stake
        self.stake_atual = stake
        self.use_martingale = use_martingale
        self.fator_martingale = fator_martingale
        self.max_loss = max_loss
        self.max_profit = max_profit
        self.max_loss_seq = max_loss_seq
        self.estrategia = estrategia
        self.running = False
        self.rodando = False
        self.lista_digitos = []
        self.lucro_total = 0
        self.perdas_seguidas = 0
        self.historico_operacoes = []
        self.ws = None
        self.contrato_id = None

    def iniciar(self):
        self.running = True
        threading.Thread(target=self.run).start()

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
        auth = { "authorize": self.token }
        ws.send(json.dumps(auth))

    def on_message(self, ws, message):
        data = json.loads(message)

        if "error" in data:
            print("Erro:", data["error"]["message"])
            self.parar()
            return

        if "authorize" in data:
            self.rodando = True
            ws.send(json.dumps({ "ticks": "R_100" }))

        if "tick" in data:
            tick = data["tick"]["quote"]
            digito = int(str(tick)[-1])
            self.lista_digitos.append(digito)
            if len(self.lista_digitos) > 50:
                self.lista_digitos.pop(0)

            if self.running and self.contrato_id is None:
                if self.verificar_entrada():
                    self.enviar_ordem(ws)

        if "buy" in data:
            self.contrato_id = data["buy"]["contract_id"]
            self.historico_operacoes.append({
                "entrada": self.estrategia,
                "status": "AGUARDANDO",
                "preco": data["buy"]["buy_price"]
            })
            proposal_req = {
                "proposal_open_contract": 1,
                "contract_id": self.contrato_id
            }
            ws.send(json.dumps(proposal_req))

        if "proposal_open_contract" in data:
            contract = data["proposal_open_contract"]
            if contract["is_expired"]:
                lucro = contract["profit"]
                status = "WIN" if lucro > 0 else "LOSS"
                self.historico_operacoes[-1]["status"] = status
                self.lucro_total += lucro
                if status == "WIN":
                    self.perdas_seguidas = 0
                    self.stake_atual = self.stake
                else:
                    self.perdas_seguidas += 1
                    if self.use_martingale:
                        self.stake_atual *= self.fator_martingale

                self.contrato_id = None

                if self.lucro_total <= -self.max_loss or self.lucro_total >= self.max_profit or self.perdas_seguidas >= self.max_loss_seq:
                    self.parar()

    def on_error(self, ws, error):
        print("Erro WebSocket:", error)

    def on_close(self, ws, close_status_code, close_msg):
        self.rodando = False

    def verificar_entrada(self):
        if self.estrategia == "6em7Digit":
            return estrategia_6em7digit(self.lista_digitos)
        elif self.estrategia == "0Matador":
            return estrategia_0matador(self.lista_digitos)
        elif self.estrategia == "4acima":
            return estrategia_4acima(self.lista_digitos)
        return False

    def enviar_ordem(self, ws):
        ordem = {
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
        ws.send(json.dumps(ordem))
