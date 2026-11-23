from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from aplicativo.apresentacao.icones import renderizar_icone
from aplicativo.configuracao import NOME_APLICATIVO, PASTA_TEMPLATES, obter_exercicio_atual
from aplicativo.dominio.modelos import Cidadao


def formatar_moeda(valor: float) -> str:
    valor_formatado = f"{valor:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return f"R$ {valor_formatado}"


modelos_html = Jinja2Templates(directory=str(PASTA_TEMPLATES))
modelos_html.env.filters["moeda"] = formatar_moeda
modelos_html.env.globals["icone"] = renderizar_icone


def renderizar_pagina(
    requisicao: Request,
    nome_modelo: str,
    cidadao: Cidadao | None = None,
    contexto: dict | None = None,
    status_resposta: int = 200,
) -> HTMLResponse:
    contexto_completo = {
        "nome_aplicativo": NOME_APLICATIVO,
        "exercicio_atual": obter_exercicio_atual(),
        "cidadao": cidadao,
        "caminho_atual": requisicao.url.path,
        **(contexto or {}),
    }
    return modelos_html.TemplateResponse(requisicao, nome_modelo, contexto_completo, status_code=status_resposta)
