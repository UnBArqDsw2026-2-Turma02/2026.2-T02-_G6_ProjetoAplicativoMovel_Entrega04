import logging
from abc import ABC, abstractmethod
from datetime import datetime

registrador = logging.getLogger(__name__)

SITUACOES_VALIDAS = ("PPD Ativa", "Definitiva", "Cassada")

MENSAGENS_POR_SITUACAO = {
    "PPD Ativa": "Sua Permissão Para Dirigir está ativa. Mantenha-se sem infrações graves por 12 meses.",
    "Definitiva": "Parabéns! Sua CNH agora é definitiva.",
    "Cassada": "Sua Permissão Para Dirigir foi cassada. Procure o Detran para reiniciar a 1ª habilitação.",
}


def registrar_momento() -> str:
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


class Observador(ABC):
    @abstractmethod
    def atualizar(self, acompanhamento: "AcompanhamentoHabilitacao") -> None: ...


class AcompanhamentoHabilitacao:
    def __init__(self, nome_condutor: str, situacao: str = "PPD Ativa") -> None:
        if situacao not in SITUACOES_VALIDAS:
            raise ValueError(f"Situação inválida: {situacao}")
        self.nome_condutor = nome_condutor
        self._situacao = situacao
        self._observadores: list[Observador] = []

    @property
    def situacao(self) -> str:
        return self._situacao

    def adicionar(self, observador: Observador) -> None:
        if observador not in self._observadores:
            self._observadores.append(observador)

    def remover(self, observador: Observador) -> None:
        if observador in self._observadores:
            self._observadores.remove(observador)

    def notificar(self) -> None:
        for observador in list(self._observadores):
            try:
                observador.atualizar(self)
            except Exception:
                registrador.exception("Falha ao notificar %s", type(observador).__name__)

    def mudar_situacao(self, nova_situacao: str) -> None:
        if nova_situacao not in SITUACOES_VALIDAS:
            raise ValueError(f"Situação inválida: {nova_situacao}")
        if nova_situacao == self._situacao:
            return
        self._situacao = nova_situacao
        self.notificar()


class NotificacaoPush(Observador):
    def __init__(self) -> None:
        self.enviadas: list[dict] = []

    def atualizar(self, acompanhamento: AcompanhamentoHabilitacao) -> None:
        self.enviadas.append(
            {
                "canal": "Push",
                "mensagem": MENSAGENS_POR_SITUACAO[acompanhamento.situacao],
                "momento": registrar_momento(),
            }
        )


class NotificacaoEmail(Observador):
    def __init__(self) -> None:
        self.enviadas: list[dict] = []

    def atualizar(self, acompanhamento: AcompanhamentoHabilitacao) -> None:
        self.enviadas.append(
            {
                "canal": "E-mail",
                "mensagem": f"Para {acompanhamento.nome_condutor}: habilitação {acompanhamento.situacao}",
                "momento": registrar_momento(),
            }
        )


class HistoricoAuditoria(Observador):
    def __init__(self) -> None:
        self.registros: list[dict] = []

    def atualizar(self, acompanhamento: AcompanhamentoHabilitacao) -> None:
        self.registros.append(
            {
                "descricao": f"{acompanhamento.nome_condutor} -> {acompanhamento.situacao}",
                "momento": registrar_momento(),
            }
        )
