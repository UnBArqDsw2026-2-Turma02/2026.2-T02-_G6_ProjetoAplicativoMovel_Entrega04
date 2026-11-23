from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from aplicativo.apresentacao.dependencias import CidadaoAtual, ConteinerDependencia, responder_operacao
from aplicativo.apresentacao.esquemas import (
    RequisicaoAlteracaoEndereco,
    RequisicaoElegibilidadeTEI,
    RequisicaoEmissaoCRLVe,
    RespostaOperacao,
)
from aplicativo.dominio.modelos import Endereco

roteador_veiculos = APIRouter(prefix="/api/v1", tags=["Veículos"])


@roteador_veiculos.get("/ufs", summary="Lista as UFs com base de dados disponível")
def listar_unidades_federativas(conteiner: ConteinerDependencia) -> list[str]:
    return conteiner.servicos_veiculos.listar_unidades_federativas()


@roteador_veiculos.get("/ufs/{uf}/veiculos", summary="Lista os veículos da base da UF (Multiton)")
def listar_veiculos(uf: str, cidadao: CidadaoAtual, conteiner: ConteinerDependencia) -> dict:
    return conteiner.servicos_veiculos.listar_veiculos(uf, cidadao)


@roteador_veiculos.get("/ufs/{uf}/veiculos/{placa}", summary="UC01 - Consulta débitos, restrições e financiamentos")
def consultar_situacao_veiculo(uf: str, placa: str, cidadao: CidadaoAtual, conteiner: ConteinerDependencia) -> dict:
    return conteiner.servicos_veiculos.consultar_situacao(uf, placa, cidadao)


@roteador_veiculos.put(
    "/ufs/{uf}/veiculos/{placa}/endereco",
    summary="UC03 - Altera o endereço do veículo",
    response_model=RespostaOperacao,
)
def alterar_endereco(
    uf: str,
    placa: str,
    requisicao: RequisicaoAlteracaoEndereco,
    cidadao: CidadaoAtual,
    conteiner: ConteinerDependencia,
) -> JSONResponse:
    novo_endereco = Endereco(requisicao.uf, requisicao.cep_formatado, requisicao.logradouro, requisicao.caixa_postal)
    return responder_operacao(conteiner.servicos_veiculos.alterar_endereco(uf, placa, cidadao, novo_endereco))


@roteador_veiculos.post(
    "/ufs/{uf}/veiculos/{placa}/crlve",
    summary="UC02 - Emite o CRLV-e por clonagem do protótipo",
    status_code=status.HTTP_201_CREATED,
    response_model=RespostaOperacao,
)
def emitir_crlve(
    uf: str,
    placa: str,
    requisicao: RequisicaoEmissaoCRLVe,
    cidadao: CidadaoAtual,
    conteiner: ConteinerDependencia,
) -> JSONResponse:
    resultado = conteiner.servicos_veiculos.emitir_crlve(uf, placa, cidadao, requisicao.exercicio)
    return responder_operacao(resultado, status.HTTP_201_CREATED)


@roteador_veiculos.post(
    "/ufs/{uf}/veiculos/{placa}/elegibilidade-tei",
    summary="UC04/UC07 - Verifica a elegibilidade para a Transferência Eletrônica Inteligente",
    response_model=RespostaOperacao,
)
def verificar_elegibilidade_tei(
    uf: str,
    placa: str,
    requisicao: RequisicaoElegibilidadeTEI,
    cidadao: CidadaoAtual,
    conteiner: ConteinerDependencia,
) -> JSONResponse:
    resultado = conteiner.servicos_veiculos.verificar_elegibilidade_tei(uf, placa, cidadao, requisicao.cpf_comprador)
    return responder_operacao(resultado)


@roteador_veiculos.get("/documentos/crlve/prototipo", summary="Estado do protótipo e dos CRLV-e emitidos (Prototype)")
def descrever_prototipo_crlve(cidadao: CidadaoAtual, conteiner: ConteinerDependencia) -> dict:
    return conteiner.servicos_veiculos.descrever_estado_prototipo(cidadao)
