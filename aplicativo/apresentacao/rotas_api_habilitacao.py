from fastapi import APIRouter
from fastapi.responses import JSONResponse

from aplicativo.apresentacao.dependencias import CidadaoAtual, ConteinerDependencia, responder_operacao
from aplicativo.apresentacao.esquemas import (
    RequisicaoAlteracaoCategoria,
    RequisicaoInfracaoHabilitacao,
    RespostaOperacao,
)

roteador_habilitacao = APIRouter(prefix="/api/v1/cidadao/habilitacao", tags=["Habilitação"])


@roteador_habilitacao.get("", summary="Situação da habilitação, notificações e solicitações")
def consultar_habilitacao(cidadao: CidadaoAtual, conteiner: ConteinerDependencia) -> dict:
    return conteiner.servicos_habilitacao.descrever(cidadao)


@roteador_habilitacao.post(
    "/infracoes", summary="Registra infração simulada no histórico (State)", response_model=RespostaOperacao
)
def registrar_infracao(
    requisicao: RequisicaoInfracaoHabilitacao, cidadao: CidadaoAtual, conteiner: ConteinerDependencia
) -> JSONResponse:
    return responder_operacao(conteiner.servicos_habilitacao.registrar_infracao(cidadao, requisicao.gravidade))


@roteador_habilitacao.post(
    "/conclusao-ppd", summary="Conclui o período da PPD (State e Observer)", response_model=RespostaOperacao
)
def concluir_periodo_ppd(cidadao: CidadaoAtual, conteiner: ConteinerDependencia) -> JSONResponse:
    return responder_operacao(conteiner.servicos_habilitacao.concluir_periodo_ppd(cidadao))


@roteador_habilitacao.post("/reinicio", summary="Inicia nova PPD após a cassação", response_model=RespostaOperacao)
def iniciar_nova_habilitacao(cidadao: CidadaoAtual, conteiner: ConteinerDependencia) -> JSONResponse:
    return responder_operacao(conteiner.servicos_habilitacao.iniciar_nova_habilitacao(cidadao))


@roteador_habilitacao.post(
    "/alteracoes-categoria",
    summary="Valida a alteração de categoria (Chain of Responsibility)",
    response_model=RespostaOperacao,
)
def solicitar_alteracao_categoria(
    requisicao: RequisicaoAlteracaoCategoria, cidadao: CidadaoAtual, conteiner: ConteinerDependencia
) -> JSONResponse:
    resultado = conteiner.servicos_habilitacao.solicitar_alteracao_categoria(cidadao, requisicao.categoria_desejada)
    return responder_operacao(resultado)
