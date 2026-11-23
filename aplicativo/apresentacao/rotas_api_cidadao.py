from fastapi import APIRouter
from fastapi.responses import JSONResponse

from aplicativo.apresentacao.dependencias import CidadaoAtual, ConteinerDependencia, responder_operacao
from aplicativo.apresentacao.esquemas import (
    RequisicaoAdesaoSNE,
    RequisicaoDesconto,
    RequisicaoIndicacaoCondutor,
    RespostaOperacao,
)
from aplicativo.padroes.strategy.validacao_documento_sne import DadosDocumentoSNE

roteador_cidadao = APIRouter(prefix="/api/v1/cidadao", tags=["Cidadão"])


@roteador_cidadao.get("", summary="Dados do cidadão autenticado (Adapter gov.br simulado)")
def obter_cidadao(cidadao: CidadaoAtual, conteiner: ConteinerDependencia) -> dict:
    return {
        "nome": cidadao.nome,
        "cpf_mascarado": cidadao.cpf_mascarado,
        "email": cidadao.email,
        "aderiu_sne": cidadao.aderiu_sne,
        "nivel_conta_gov": conteiner.gateway_autenticacao.nivel_da_conta(),
    }


@roteador_cidadao.get("/transferencias", summary="UC06 - Lista as transferências concluídas do cidadão")
def listar_transferencias(cidadao: CidadaoAtual, conteiner: ConteinerDependencia) -> list[dict]:
    return conteiner.servicos_veiculos.listar_transferencias_concluidas(cidadao)


@roteador_cidadao.get("/infracoes", tags=["Infrações"], summary="Lista as infrações do condutor (Facade)")
def listar_infracoes(cidadao: CidadaoAtual, conteiner: ConteinerDependencia) -> dict:
    return {
        "resumo": conteiner.infracoes_facade.resumir_infracoes(cidadao),
        "infracoes": conteiner.infracoes_facade.listar_infracoes(cidadao),
    }


@roteador_cidadao.get("/infracoes/{identificador}", tags=["Infrações"], summary="Detalha uma infração")
def detalhar_infracao(identificador: str, cidadao: CidadaoAtual, conteiner: ConteinerDependencia) -> dict:
    return conteiner.infracoes_facade.detalhar_infracao(cidadao, identificador)


@roteador_cidadao.post(
    "/infracoes/{identificador}/descontos",
    tags=["Infrações"],
    summary="Solicita desconto conforme a política do órgão (Strategy)",
    response_model=RespostaOperacao,
)
def solicitar_desconto(
    identificador: str, requisicao: RequisicaoDesconto, cidadao: CidadaoAtual, conteiner: ConteinerDependencia
) -> JSONResponse:
    resultado = conteiner.infracoes_facade.solicitar_desconto(
        cidadao, identificador, requisicao.percentual, requisicao.termo_aceito
    )
    return responder_operacao(resultado)


@roteador_cidadao.post(
    "/infracoes/{identificador}/boleto",
    tags=["Infrações"],
    summary="Gera o boleto da infração (Adapter da API de boletos)",
    response_model=RespostaOperacao,
)
def solicitar_boleto(identificador: str, cidadao: CidadaoAtual, conteiner: ConteinerDependencia) -> JSONResponse:
    return responder_operacao(conteiner.infracoes_facade.solicitar_boleto(cidadao, identificador))


@roteador_cidadao.post(
    "/infracoes/{identificador}/indicacao-condutor",
    tags=["Infrações"],
    summary="Indica o condutor responsável (Adapter do protocolo legado)",
    response_model=RespostaOperacao,
)
def indicar_condutor(
    identificador: str,
    requisicao: RequisicaoIndicacaoCondutor,
    cidadao: CidadaoAtual,
    conteiner: ConteinerDependencia,
) -> JSONResponse:
    resultado = conteiner.infracoes_facade.indicar_condutor(
        cidadao, identificador, requisicao.cpf_condutor, requisicao.numero_cnh_condutor
    )
    return responder_operacao(resultado)


@roteador_cidadao.get("/sne", tags=["SNE"], summary="Situação de adesão ao SNE")
def consultar_adesao_sne(cidadao: CidadaoAtual, conteiner: ConteinerDependencia) -> dict:
    return conteiner.sne_facade.consultar_situacao(cidadao)


@roteador_cidadao.post(
    "/sne/adesao",
    tags=["SNE"],
    summary="Adere ao SNE validando CNH ou CRLV (Strategy)",
    response_model=RespostaOperacao,
)
def aderir_sne(requisicao: RequisicaoAdesaoSNE, cidadao: CidadaoAtual, conteiner: ConteinerDependencia) -> JSONResponse:
    dados_documento = DadosDocumentoSNE(
        numero_cnh=requisicao.numero_cnh,
        codigo_seguranca_cnh=requisicao.codigo_seguranca_cnh,
        placa=requisicao.placa,
        renavam=requisicao.renavam,
        numero_seguranca_crv=requisicao.numero_seguranca_crv,
    )
    return responder_operacao(conteiner.sne_facade.aderir(cidadao, requisicao.tipo_documento, dados_documento))
