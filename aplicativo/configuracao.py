import os
from datetime import date
from pathlib import Path

PASTA_APLICATIVO = Path(__file__).resolve().parent
PASTA_TEMPLATES = PASTA_APLICATIVO / "apresentacao" / "templates"
PASTA_ESTATICOS = PASTA_APLICATIVO / "apresentacao" / "estaticos"

NOME_APLICATIVO = "Dirigindo Meu Carro"
NOME_COOKIE_SESSAO = "sessao_cidadao"
PRIMEIRO_EXERCICIO_EMITIVEL = 2000

ENDERECO_SERVIDOR = os.getenv("ENDERECO_SERVIDOR", "127.0.0.1")
PORTA_PADRAO = int(os.getenv("PORTA_SERVIDOR", "8000"))


def obter_exercicio_atual() -> int:
    return date.today().year
