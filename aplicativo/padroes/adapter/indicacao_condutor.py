from dataclasses import dataclass
from typing import Protocol

from aplicativo.dominio.excecoes import EntradaInvalida, ErroIntegracao
from aplicativo.infraestrutura.mocks import ServicoIndicacaoLegadoMock

SITUACAO_ENVIO_CONFIRMADO = "RECEBIDO"


@dataclass(frozen=True)
class PedidoIndicacao:
    auto: str
    requerente_id: str
    condutor_id: str
    anexos: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not all((self.auto.strip(), self.requerente_id.strip(), self.condutor_id.strip())):
            raise EntradaInvalida("Auto, requerente e condutor são obrigatórios.")


@dataclass(frozen=True)
class ReciboProtocolo:
    numero: str
    situacao: str


class PortaProtocolo(Protocol):
    def protocolar(self, pedido: PedidoIndicacao) -> ReciboProtocolo: ...


class AdaptadorProtocoloLegado:
    def __init__(self, servico_legado: ServicoIndicacaoLegadoMock) -> None:
        self._servico_legado = servico_legado

    def protocolar(self, pedido: PedidoIndicacao) -> ReciboProtocolo:
        dados_legados = {
            "numero_auto": pedido.auto,
            "id_solicitante": pedido.requerente_id,
            "id_indicado": pedido.condutor_id,
            "documentos": list(pedido.anexos),
        }
        resposta = self._servico_legado.registrar_indicacao(dados_legados)
        numero_protocolo = resposta.get("numero_protocolo")
        situacao_envio = resposta.get("status_envio")
        if not isinstance(numero_protocolo, str) or not numero_protocolo.strip():
            raise ErroIntegracao("O serviço de indicação respondeu sem número de protocolo.")
        if situacao_envio != SITUACAO_ENVIO_CONFIRMADO:
            raise ErroIntegracao(f"O envio da indicação não foi confirmado: {situacao_envio!r}.")
        return ReciboProtocolo(numero=numero_protocolo, situacao="RECEBIDA")
