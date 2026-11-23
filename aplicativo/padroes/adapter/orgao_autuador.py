from abc import ABC, abstractmethod
from datetime import date

from aplicativo.dominio.excecoes import RecursoNaoEncontrado
from aplicativo.dominio.modelos import Infracao, OrgaoAutuador, SituacaoInfracao
from aplicativo.infraestrutura.mocks import ApiOrgaoAutuadorMock

SITUACOES_POR_CODIGO = {
    "AV": SituacaoInfracao.A_VENCER,
    "VE": SituacaoInfracao.VENCIDA,
    "PG": SituacaoInfracao.PAGA,
}


class GatewayInfracoes(ABC):
    @abstractmethod
    def listar_por_cpf(self, cpf: str) -> list[Infracao]: ...

    @abstractmethod
    def buscar(self, cpf: str, identificador_infracao: str) -> Infracao: ...

    @abstractmethod
    def enviar_solicitacao_desconto(self, infracao: Infracao, percentual: int) -> str: ...


class OrgaoAutuadorAdapter(GatewayInfracoes):
    def __init__(self, api_orgao_autuador: ApiOrgaoAutuadorMock) -> None:
        self._api_orgao_autuador = api_orgao_autuador

    def listar_por_cpf(self, cpf: str) -> list[Infracao]:
        autos = self._api_orgao_autuador.consultar_autos(cpf)
        return [self._converter_auto(auto) for auto in autos]

    def buscar(self, cpf: str, identificador_infracao: str) -> Infracao:
        for infracao in self.listar_por_cpf(cpf):
            if infracao.identificador == identificador_infracao.upper():
                return infracao
        raise RecursoNaoEncontrado(f"Infração {identificador_infracao} não encontrada para este condutor.")

    def enviar_solicitacao_desconto(self, infracao: Infracao, percentual: int) -> str:
        resposta = self._api_orgao_autuador.registrar_beneficio(infracao.identificador, percentual)
        return resposta["protocolo"]

    @staticmethod
    def _converter_auto(auto: dict) -> Infracao:
        return Infracao(
            identificador=auto["auto"],
            cpf_condutor=auto["doc_condutor"],
            placa=auto["placa_veic"],
            descricao=auto["desc"],
            codigo_enquadramento=auto["enq"],
            local=auto["loc"],
            data_cometimento=date.fromisoformat(auto["dt_infr"]),
            vencimento=date.fromisoformat(auto["dt_venc"]),
            valor_original=float(auto["vlr"]),
            situacao=SITUACOES_POR_CODIGO[auto["sit"]],
            orgao_autuador=OrgaoAutuador(
                identificador=auto["org_id"],
                nome=auto["org_nome"],
                aderiu_sne=auto["org_sne"] == "S",
                oferece_desconto_cdt=auto["org_cdt"] == "S",
            ),
            percentual_desconto_aplicado=int(auto["pct_beneficio"]),
        )
