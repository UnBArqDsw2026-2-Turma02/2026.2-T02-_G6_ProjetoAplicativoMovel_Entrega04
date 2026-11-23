from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from aplicativo.aplicacao.conteiner import criar_conteiner
from aplicativo.apresentacao.renderizador import renderizar_pagina
from aplicativo.apresentacao.rotas_api_cidadao import roteador_cidadao
from aplicativo.apresentacao.rotas_api_habilitacao import roteador_habilitacao
from aplicativo.apresentacao.rotas_api_veiculos import roteador_veiculos
from aplicativo.apresentacao.rotas_paginas import roteador_paginas
from aplicativo.configuracao import NOME_APLICATIVO, PASTA_ESTATICOS
from aplicativo.dominio.excecoes import (
    AcessoNegado,
    EntradaInvalida,
    ErroDeNegocio,
    ErroIntegracao,
    OperacaoNaoPermitida,
    RecursoNaoEncontrado,
    SessaoNaoAutenticada,
)

STATUS_ENTRADA_INVALIDA = 422

STATUS_POR_ERRO = {
    RecursoNaoEncontrado: status.HTTP_404_NOT_FOUND,
    EntradaInvalida: STATUS_ENTRADA_INVALIDA,
    SessaoNaoAutenticada: status.HTTP_401_UNAUTHORIZED,
    AcessoNegado: status.HTTP_403_FORBIDDEN,
    OperacaoNaoPermitida: status.HTTP_409_CONFLICT,
    ErroIntegracao: status.HTTP_502_BAD_GATEWAY,
}


def requisicao_e_da_api(requisicao: Request) -> bool:
    return requisicao.url.path.startswith("/api/")


async def tratar_erro_de_negocio(requisicao: Request, erro: ErroDeNegocio) -> Response:
    status_resposta = next(
        (status_erro for tipo_erro, status_erro in STATUS_POR_ERRO.items() if isinstance(erro, tipo_erro)),
        status.HTTP_400_BAD_REQUEST,
    )
    if requisicao_e_da_api(requisicao):
        return JSONResponse(status_code=status_resposta, content={"erro": str(erro)})
    if isinstance(erro, SessaoNaoAutenticada):
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    return renderizar_pagina(requisicao, "erro.html", contexto={"mensagem": str(erro)}, status_resposta=status_resposta)


async def tratar_erro_de_validacao(requisicao: Request, erro: RequestValidationError) -> JSONResponse:
    primeiro_erro = erro.errors()[0]
    campo = primeiro_erro["loc"][-1]
    return JSONResponse(
        status_code=STATUS_ENTRADA_INVALIDA,
        content={"erro": f"Campo '{campo}' inválido: {primeiro_erro['msg']}"},
    )


def criar_aplicacao() -> FastAPI:
    aplicacao = FastAPI(
        title=f"{NOME_APLICATIVO} - API",
        description="MVP acadêmico inspirado em serviços digitais de trânsito. Todos os dados são simulados.",
        version="4.0.0",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    aplicacao.state.conteiner = criar_conteiner()
    aplicacao.mount("/estaticos", StaticFiles(directory=str(PASTA_ESTATICOS)), name="estaticos")
    aplicacao.include_router(roteador_paginas)
    aplicacao.include_router(roteador_veiculos)
    aplicacao.include_router(roteador_cidadao)
    aplicacao.include_router(roteador_habilitacao)
    aplicacao.add_exception_handler(ErroDeNegocio, tratar_erro_de_negocio)
    aplicacao.add_exception_handler(RequestValidationError, tratar_erro_de_validacao)
    return aplicacao
