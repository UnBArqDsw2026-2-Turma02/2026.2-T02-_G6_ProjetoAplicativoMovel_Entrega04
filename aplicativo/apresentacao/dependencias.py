from typing import Annotated

from fastapi import Depends, Request
from fastapi.responses import JSONResponse

from aplicativo.aplicacao.conteiner import ConteinerAplicacao
from aplicativo.configuracao import NOME_COOKIE_SESSAO
from aplicativo.dominio.excecoes import SessaoNaoAutenticada
from aplicativo.dominio.modelos import Cidadao, ResultadoOperacao


def obter_conteiner(requisicao: Request) -> ConteinerAplicacao:
    return requisicao.app.state.conteiner


ConteinerDependencia = Annotated[ConteinerAplicacao, Depends(obter_conteiner)]


def obter_cidadao_da_sessao(requisicao: Request, conteiner: ConteinerDependencia) -> Cidadao | None:
    token_sessao = requisicao.cookies.get(NOME_COOKIE_SESSAO, "")
    cpf_da_sessao = conteiner.repositorio_sessoes.buscar_cpf(token_sessao)
    if cpf_da_sessao is None:
        return None
    return conteiner.repositorio_cidadaos.buscar_por_cpf(cpf_da_sessao)


def obter_cidadao_atual(
    cidadao_da_sessao: Annotated[Cidadao | None, Depends(obter_cidadao_da_sessao)],
) -> Cidadao:
    if cidadao_da_sessao is None:
        raise SessaoNaoAutenticada("Entre com sua conta gov.br para continuar.")
    return cidadao_da_sessao


CidadaoAtual = Annotated[Cidadao, Depends(obter_cidadao_atual)]
CidadaoOpcional = Annotated[Cidadao | None, Depends(obter_cidadao_da_sessao)]


def responder_operacao(resultado: ResultadoOperacao, status_sucesso: int = 200) -> JSONResponse:
    if resultado.sucesso:
        return JSONResponse(
            status_code=status_sucesso,
            content={"sucesso": True, "mensagem": resultado.mensagem, "dados": resultado.dados},
        )
    return JSONResponse(status_code=422, content={"erro": resultado.mensagem, "dados": resultado.dados})
