from fastapi import APIRouter, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from aplicativo.apresentacao.dependencias import CidadaoAtual, CidadaoOpcional, ConteinerDependencia
from aplicativo.apresentacao.renderizador import renderizar_pagina
from aplicativo.configuracao import NOME_COOKIE_SESSAO
from aplicativo.dominio.excecoes import RecursoNaoEncontrado

roteador_paginas = APIRouter(include_in_schema=False)

MODELOS_POR_ABA = {
    "consultas": "veiculo.html",
    "crlve": "crlve.html",
    "endereco": "endereco.html",
    "transferencia": "transferencia.html",
}


@roteador_paginas.get("/", response_class=HTMLResponse, response_model=None)
def exibir_login(requisicao: Request, cidadao: CidadaoOpcional) -> HTMLResponse | RedirectResponse:
    if cidadao is not None:
        return RedirectResponse("/inicio", status_code=status.HTTP_303_SEE_OTHER)
    return renderizar_pagina(requisicao, "login.html")


@roteador_paginas.post("/entrar/gov")
def entrar_com_gov(conteiner: ConteinerDependencia) -> RedirectResponse:
    cidadao = conteiner.gateway_autenticacao.autenticar()
    token_sessao = conteiner.repositorio_sessoes.criar_sessao(cidadao.cpf)
    resposta = RedirectResponse("/inicio", status_code=status.HTTP_303_SEE_OTHER)
    resposta.set_cookie(NOME_COOKIE_SESSAO, token_sessao, httponly=True, samesite="lax")
    return resposta


@roteador_paginas.post("/sair")
def sair(requisicao: Request, conteiner: ConteinerDependencia) -> RedirectResponse:
    conteiner.repositorio_sessoes.encerrar_sessao(requisicao.cookies.get(NOME_COOKIE_SESSAO, ""))
    resposta = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    resposta.delete_cookie(NOME_COOKIE_SESSAO)
    return resposta


@roteador_paginas.get("/inicio", response_class=HTMLResponse)
def exibir_inicio(
    requisicao: Request, cidadao: CidadaoAtual, conteiner: ConteinerDependencia, uf: str = "DF"
) -> HTMLResponse:
    contexto = {
        "unidades_federativas": conteiner.servicos_veiculos.listar_unidades_federativas(),
        "base": conteiner.servicos_veiculos.listar_veiculos(uf, cidadao),
        "resumo_infracoes": conteiner.infracoes_facade.resumir_infracoes(cidadao),
    }
    return renderizar_pagina(requisicao, "inicio.html", cidadao, contexto)


def renderizar_servico_do_veiculo(
    requisicao: Request,
    uf: str,
    placa: str,
    cidadao: CidadaoAtual,
    conteiner: ConteinerDependencia,
    aba_ativa: str,
) -> HTMLResponse:
    situacao = conteiner.servicos_veiculos.consultar_situacao(uf, placa, cidadao)
    contexto = {"uf": uf.upper(), "aba_ativa": aba_ativa, **situacao}
    return renderizar_pagina(requisicao, MODELOS_POR_ABA[aba_ativa], cidadao, contexto)


@roteador_paginas.get("/veiculos/{uf}/{placa}", response_class=HTMLResponse)
def exibir_veiculo(
    requisicao: Request, uf: str, placa: str, cidadao: CidadaoAtual, conteiner: ConteinerDependencia
) -> HTMLResponse:
    return renderizar_servico_do_veiculo(requisicao, uf, placa, cidadao, conteiner, "consultas")


@roteador_paginas.get("/veiculos/{uf}/{placa}/{aba}", response_class=HTMLResponse)
def exibir_servico_do_veiculo(
    requisicao: Request, uf: str, placa: str, aba: str, cidadao: CidadaoAtual, conteiner: ConteinerDependencia
) -> HTMLResponse:
    if aba not in MODELOS_POR_ABA or aba == "consultas":
        raise RecursoNaoEncontrado(f"O serviço '{aba}' não existe para veículos.")
    return renderizar_servico_do_veiculo(requisicao, uf, placa, cidadao, conteiner, aba)


@roteador_paginas.get("/transferencias", response_class=HTMLResponse)
def exibir_transferencias(requisicao: Request, cidadao: CidadaoAtual, conteiner: ConteinerDependencia) -> HTMLResponse:
    contexto = {"transferencias": conteiner.servicos_veiculos.listar_transferencias_concluidas(cidadao)}
    return renderizar_pagina(requisicao, "transferencias.html", cidadao, contexto)


@roteador_paginas.get("/infracoes", response_class=HTMLResponse)
def exibir_infracoes(requisicao: Request, cidadao: CidadaoAtual, conteiner: ConteinerDependencia) -> HTMLResponse:
    contexto = {
        "resumo": conteiner.infracoes_facade.resumir_infracoes(cidadao),
        "infracoes": conteiner.infracoes_facade.listar_infracoes(cidadao),
    }
    return renderizar_pagina(requisicao, "infracoes.html", cidadao, contexto)


@roteador_paginas.get("/infracoes/{identificador}", response_class=HTMLResponse)
def exibir_infracao(
    requisicao: Request, identificador: str, cidadao: CidadaoAtual, conteiner: ConteinerDependencia
) -> HTMLResponse:
    contexto = {"infracao": conteiner.infracoes_facade.detalhar_infracao(cidadao, identificador)}
    return renderizar_pagina(requisicao, "infracao.html", cidadao, contexto)


@roteador_paginas.get("/infracoes/{identificador}/boleto", response_class=HTMLResponse)
def exibir_boleto(
    requisicao: Request, identificador: str, cidadao: CidadaoAtual, conteiner: ConteinerDependencia
) -> HTMLResponse:
    infracao = conteiner.infracoes_facade.detalhar_infracao(cidadao, identificador)
    if infracao["boleto"] is None:
        raise RecursoNaoEncontrado("Gere o boleto na tela da infração antes de abri-lo.")
    return renderizar_pagina(requisicao, "boleto.html", cidadao, {"infracao": infracao, "boleto": infracao["boleto"]})


@roteador_paginas.get("/habilitacao", response_class=HTMLResponse)
def exibir_habilitacao(requisicao: Request, cidadao: CidadaoAtual, conteiner: ConteinerDependencia) -> HTMLResponse:
    contexto = {"habilitacao": conteiner.servicos_habilitacao.descrever(cidadao)}
    return renderizar_pagina(requisicao, "habilitacao.html", cidadao, contexto)


@roteador_paginas.get("/sne", response_class=HTMLResponse)
def exibir_sne(requisicao: Request, cidadao: CidadaoAtual, conteiner: ConteinerDependencia) -> HTMLResponse:
    contexto = {"situacao_sne": conteiner.sne_facade.consultar_situacao(cidadao)}
    return renderizar_pagina(requisicao, "sne.html", cidadao, contexto)
