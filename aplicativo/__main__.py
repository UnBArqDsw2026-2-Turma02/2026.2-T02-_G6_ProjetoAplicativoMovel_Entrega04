import sys
import threading
import webbrowser

import uvicorn

from aplicativo.configuracao import ABRIR_NAVEGADOR, ENDERECO_SERVIDOR, PORTA_PADRAO

SEGUNDOS_ATE_ABRIR_NAVEGADOR = 1.5


def iniciar_servidor() -> None:
    porta = int(sys.argv[1]) if len(sys.argv) > 1 else PORTA_PADRAO
    endereco_local = f"http://127.0.0.1:{porta}"
    print(f"Aplicativo escutando em http://{ENDERECO_SERVIDOR}:{porta} (acesse por {endereco_local})")
    print("Para encerrar, pressione Ctrl+C.")
    if ABRIR_NAVEGADOR:
        threading.Timer(SEGUNDOS_ATE_ABRIR_NAVEGADOR, webbrowser.open, args=[endereco_local]).start()
    uvicorn.run("aplicativo.principal:criar_aplicacao", factory=True, host=ENDERECO_SERVIDOR, port=porta)


if __name__ == "__main__":
    iniciar_servidor()
