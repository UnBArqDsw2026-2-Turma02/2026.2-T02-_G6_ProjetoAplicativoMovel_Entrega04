from abc import ABC, abstractmethod
from datetime import date

from aplicativo.dominio.modelos import Boleto, Infracao, SituacaoBoleto
from aplicativo.infraestrutura.mocks import ApiBoletoMock

SITUACOES_POR_STATUS = {
    "PROCESSANDO": SituacaoBoleto.PROCESSANDO,
    "PRONTO": SituacaoBoleto.PRONTO,
}


class GatewayBoleto(ABC):
    @abstractmethod
    def consultar(self, identificador_infracao: str) -> Boleto | None: ...

    @abstractmethod
    def emitir(self, infracao: Infracao, vencimento: date) -> Boleto: ...

    @abstractmethod
    def atualizar_desconto(self, identificador_infracao: str, percentual: int) -> Boleto: ...


class BoletoApiAdapter(GatewayBoleto):
    def __init__(self, api_boleto: ApiBoletoMock) -> None:
        self._api_boleto = api_boleto

    def consultar(self, identificador_infracao: str) -> Boleto | None:
        registro = self._api_boleto.consultar_boleto(identificador_infracao)
        return self._converter_registro(registro) if registro else None

    def emitir(self, infracao: Infracao, vencimento: date) -> Boleto:
        registro = self._api_boleto.emitir_boleto(
            infracao.identificador,
            infracao.identificador,
            vencimento.isoformat(),
            infracao.valor_original,
            infracao.percentual_desconto_aplicado,
        )
        return self._converter_registro(registro)

    def atualizar_desconto(self, identificador_infracao: str, percentual: int) -> Boleto:
        return self._converter_registro(self._api_boleto.atualizar_desconto(identificador_infracao, percentual))

    @staticmethod
    def _converter_registro(registro: dict) -> Boleto:
        return Boleto(
            identificador=registro["boletoId"],
            identificador_infracao=registro["idInfracao"],
            numero_auto=registro["numeroAuto"],
            vencimento=date.fromisoformat(registro["dataVencimento"]),
            valor_original=float(registro["valorOriginal"]),
            percentual_desconto=int(registro["percentualDesconto"]),
            codigo_pagamento=registro["codigoPagamento"],
            nome_arquivo=registro["arquivoPDF"],
            situacao=SITUACOES_POR_STATUS[registro["status"]],
        )
