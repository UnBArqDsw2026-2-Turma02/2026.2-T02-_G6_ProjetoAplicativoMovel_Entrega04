import sys

import uvicorn

from aplicativo.configuracao import ENDERECO_SERVIDOR, PORTA_PADRAO


def iniciar_servidor() -> None:
    porta = int(sys.argv[1]) if len(sys.argv) > 1 else PORTA_PADRAO
    print(f"Aplicativo escutando em http://{ENDERECO_SERVIDOR}:{porta} (acesse por http://127.0.0.1:{porta})")
    uvicorn.run("aplicativo.principal:criar_aplicacao", factory=True, host=ENDERECO_SERVIDOR, port=porta)


if __name__ == "__main__":
    iniciar_servidor()
