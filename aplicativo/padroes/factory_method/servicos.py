from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

from aplicativo.dominio.modelos import (
    Cidadao,
    DadosEmissao,
    DocumentoTransferencia,
    Endereco,
    ResultadoOperacao,
    TipoRestricao,
)
from aplicativo.padroes.factory_method.consultas import NadaConstaCreator
from aplicativo.padroes.multiton.base_detran import BaseDetranMultiton
from aplicativo.padroes.prototype.documentos import (
    PROTOTIPO_CRLVE,
    EmissorCRLVe,
    registro_documentos_emitidos,
)

UNIDADE_FEDERATIVA_ATENDIDA = "DF"


@dataclass
class RequisitoTransferencia:
    descricao: str
    atendido: bool


class ServicoDetran(ABC):
    def __init__(self, base_detran: BaseDetranMultiton) -> None:
        self._base_detran = base_detran

    @abstractmethod
    def executar(self, placa: str, dados_requisicao: dict) -> ResultadoOperacao: ...


class ServicoAlteracaoEndereco(ServicoDetran):
    def executar(self, placa: str, dados_requisicao: dict) -> ResultadoOperacao:
        veiculo = self._base_detran.buscar_veiculo(placa)
        novo_endereco: Endereco = dados_requisicao["novo_endereco"]

        if novo_endereco.uf != UNIDADE_FEDERATIVA_ATENDIDA:
            return ResultadoOperacao(
                False, "O novo endereço deve estar no Distrito Federal. Mudança de UF segue outro fluxo."
            )
        if novo_endereco.caixa_postal:
            return ResultadoOperacao(False, "O endereço não pode ser uma caixa postal.")
        if veiculo.debitos_vencidos:
            return ResultadoOperacao(False, "Quite os débitos vencidos antes de alterar o endereço.")
        if veiculo.restricoes:
            return ResultadoOperacao(
                False, "Veículos com restrição administrativa ou judicial não podem alterar o endereço."
            )

        veiculo.endereco = novo_endereco
        return ResultadoOperacao(
            True,
            f"Endereço do veículo {veiculo.placa} atualizado sem cobrança.",
            {"endereco": {"uf": novo_endereco.uf, "cep": novo_endereco.cep, "logradouro": novo_endereco.logradouro}},
        )


class ServicoEmissaoCRLVe(ServicoDetran):
    def executar(self, placa: str, dados_requisicao: dict) -> ResultadoOperacao:
        veiculo = self._base_detran.buscar_veiculo(placa)
        nada_consta = NadaConstaCreator().consultar(veiculo)
        if not nada_consta.limpo:
            return ResultadoOperacao(
                False,
                "Emissão bloqueada: existem pendências impeditivas no veículo.",
                {"pendencias": nada_consta.itens},
            )

        dados_emissao = DadosEmissao(
            placa=veiculo.placa,
            renavam=veiculo.renavam,
            exercicio=dados_requisicao["exercicio"],
            marca_modelo=veiculo.marca_modelo,
            nome_proprietario=veiculo.nome_proprietario,
        )
        documento = EmissorCRLVe(PROTOTIPO_CRLVE).emitir(dados_emissao)
        registro_documentos_emitidos.registrar(documento)
        return ResultadoOperacao(
            True, f"CRLV-e {dados_emissao.exercicio} emitido.", {"documento": documento.para_dicionario()}
        )


class ServicoVerificacaoElegibilidadeTEI(ServicoDetran):
    def executar(self, placa: str, dados_requisicao: dict) -> ResultadoOperacao:
        veiculo = self._base_detran.buscar_veiculo(placa)
        vendedor: Cidadao = dados_requisicao["vendedor"]
        comprador: Cidadao | None = dados_requisicao["comprador"]
        data_referencia: date = dados_requisicao.get("data_referencia", date.today())

        requisitos = [
            RequisitoTransferencia("Vendedor é o proprietário do veículo", veiculo.cpf_proprietario == vendedor.cpf),
            RequisitoTransferencia(
                "Vendedor pessoa física com cadastro ativo e biometria válida",
                vendedor.pessoa_fisica and vendedor.cadastro_ativo and vendedor.biometria_valida,
            ),
            RequisitoTransferencia(
                "Comprador pessoa física com cadastro ativo e biometria válida",
                comprador is not None
                and comprador.cpf != vendedor.cpf
                and comprador.pessoa_fisica
                and comprador.cadastro_ativo
                and comprador.biometria_valida,
            ),
            RequisitoTransferencia(
                "Veículo registrado no DF e permanecendo na frota do DF",
                self._base_detran.unidade_federativa == UNIDADE_FEDERATIVA_ATENDIDA,
            ),
            RequisitoTransferencia(
                "Documento ativo é o ATPV-e (o DUT físico não atende)",
                veiculo.documento_transferencia == DocumentoTransferencia.ATPV_E,
            ),
            RequisitoTransferencia(
                "Sem restrição judicial impeditiva", not veiculo.possui_restricao(TipoRestricao.JUDICIAL)
            ),
            RequisitoTransferencia(
                "Sem restrição administrativa impeditiva",
                not veiculo.possui_restricao(TipoRestricao.ADMINISTRATIVA),
            ),
            RequisitoTransferencia("Sem alienação fiduciária ativa", not veiculo.financiamentos),
            RequisitoTransferencia("Débitos vencidos quitados", not veiculo.debitos_vencidos),
        ]
        elegivel = all(requisito.atendido for requisito in requisitos)
        vistoria_valida = veiculo.vistoria is not None and veiculo.vistoria.esta_valida(data_referencia)
        requisitos_nao_atendidos = [requisito.descricao for requisito in requisitos if not requisito.atendido]

        if not elegivel:
            mensagem = "Veículo não elegível para a TEI. A transferência deve seguir o procedimento tradicional."
            proximo_passo = "procedimento_tradicional"
        elif not vistoria_valida:
            mensagem = (
                "Requisitos atendidos, mas é preciso realizar vistoria em uma ECV credenciada (validade de 90 dias)."
            )
            proximo_passo = "providenciar_vistoria"
        else:
            mensagem = "Transferência apta a seguir para a execução da TEI."
            proximo_passo = "execucao_tei"

        return ResultadoOperacao(
            True,
            mensagem,
            {
                "elegivel": elegivel,
                "vistoria_valida": vistoria_valida,
                "proximo_passo": proximo_passo,
                "requisitos": [
                    {"descricao": requisito.descricao, "atendido": requisito.atendido} for requisito in requisitos
                ],
                "requisitos_nao_atendidos": requisitos_nao_atendidos,
            },
        )


class ServicoCreator(ABC):
    def __init__(self, unidade_federativa: str) -> None:
        self._base_detran = BaseDetranMultiton.obter_instancia(unidade_federativa)

    @abstractmethod
    def criar_servico(self) -> ServicoDetran: ...

    def processar(self, placa: str, dados_requisicao: dict) -> ResultadoOperacao:
        servico = self.criar_servico()
        return servico.executar(placa, dados_requisicao)


class AlteracaoEnderecoCreator(ServicoCreator):
    def criar_servico(self) -> ServicoDetran:
        return ServicoAlteracaoEndereco(self._base_detran)


class EmissaoCRLVeCreator(ServicoCreator):
    def criar_servico(self) -> ServicoDetran:
        return ServicoEmissaoCRLVe(self._base_detran)


class VerificacaoElegibilidadeTEICreator(ServicoCreator):
    def criar_servico(self) -> ServicoDetran:
        return ServicoVerificacaoElegibilidadeTEI(self._base_detran)
