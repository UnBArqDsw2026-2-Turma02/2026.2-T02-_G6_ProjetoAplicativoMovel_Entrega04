from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum

from aplicativo.dominio.excecoes import OperacaoNaoPermitida
from aplicativo.padroes.observer.acompanhamento_habilitacao import AcompanhamentoHabilitacao

DIAS_VALIDADE_PPD = 365
BLOQUEIO_PPD_CASSADA = "PPD cassada"


class Gravidade(str, Enum):
    LEVE = "leve"
    MEDIA = "media"
    GRAVE = "grave"
    GRAVISSIMA = "gravissima"


@dataclass(frozen=True)
class InfracaoHabilitacao:
    codigo: str
    gravidade: Gravidade
    data: date


class TransicaoInvalida(OperacaoNaoPermitida):
    pass


class EstadoHabilitacao(ABC):
    nome = ""

    def ao_entrar(self, habilitacao: "Habilitacao") -> None:
        return None

    @abstractmethod
    def registrar_infracao(self, habilitacao: "Habilitacao", infracao: InfracaoHabilitacao) -> None: ...

    @abstractmethod
    def concluir_prazo(self, habilitacao: "Habilitacao", data_referencia: date) -> None: ...

    @abstractmethod
    def pode_dirigir(self) -> bool: ...


class PPDAtiva(EstadoHabilitacao):
    nome = "PPD Ativa"

    def registrar_infracao(self, habilitacao: "Habilitacao", infracao: InfracaoHabilitacao) -> None:
        habilitacao.historico_infracoes.append(infracao)

    def concluir_prazo(self, habilitacao: "Habilitacao", data_referencia: date) -> None:
        if data_referencia < habilitacao.data_limite_ppd:
            data_limite = habilitacao.data_limite_ppd.strftime("%d/%m/%Y")
            raise TransicaoInvalida(f"O prazo de 12 meses da PPD ainda não terminou (limite: {data_limite}).")
        if self._possui_impedimento(habilitacao):
            habilitacao.mudar_estado(Cassada())
        else:
            habilitacao.mudar_estado(Definitiva())

    def pode_dirigir(self) -> bool:
        return True

    @staticmethod
    def _possui_impedimento(habilitacao: "Habilitacao") -> bool:
        gravidades = [infracao.gravidade for infracao in habilitacao.historico_infracoes]
        possui_grave = any(gravidade in (Gravidade.GRAVE, Gravidade.GRAVISSIMA) for gravidade in gravidades)
        reincidiu_em_media = gravidades.count(Gravidade.MEDIA) > 1
        return possui_grave or reincidiu_em_media


class Definitiva(EstadoHabilitacao):
    nome = "Definitiva"

    def registrar_infracao(self, habilitacao: "Habilitacao", infracao: InfracaoHabilitacao) -> None:
        habilitacao.historico_infracoes.append(infracao)

    def concluir_prazo(self, habilitacao: "Habilitacao", data_referencia: date) -> None:
        raise TransicaoInvalida("A habilitação já é definitiva: não há prazo de PPD a concluir.")

    def pode_dirigir(self) -> bool:
        return True


class Cassada(EstadoHabilitacao):
    nome = "Cassada"

    def ao_entrar(self, habilitacao: "Habilitacao") -> None:
        habilitacao.bloqueios_ativos.append(BLOQUEIO_PPD_CASSADA)

    def registrar_infracao(self, habilitacao: "Habilitacao", infracao: InfracaoHabilitacao) -> None:
        raise TransicaoInvalida("Habilitação cassada: não aceita novos registros.")

    def concluir_prazo(self, habilitacao: "Habilitacao", data_referencia: date) -> None:
        raise TransicaoInvalida("Habilitação cassada: estado final.")

    def pode_dirigir(self) -> bool:
        return False


class Habilitacao:
    def __init__(
        self,
        numero_registro: str,
        categoria: str,
        data_emissao_ppd: date,
        acompanhamento: AcompanhamentoHabilitacao,
    ) -> None:
        self.numero_registro = numero_registro
        self.categoria = categoria
        self.data_emissao_ppd = data_emissao_ppd
        self.data_limite_ppd = data_emissao_ppd + timedelta(days=DIAS_VALIDADE_PPD)
        self.historico_infracoes: list[InfracaoHabilitacao] = []
        self.bloqueios_ativos: list[str] = []
        self.acompanhamento = acompanhamento
        self._estado: EstadoHabilitacao = PPDAtiva()

    @property
    def situacao(self) -> str:
        return self._estado.nome

    def mudar_estado(self, novo_estado: EstadoHabilitacao) -> None:
        self._estado = novo_estado
        novo_estado.ao_entrar(self)
        self.acompanhamento.mudar_situacao(novo_estado.nome)

    def registrar_infracao(self, infracao: InfracaoHabilitacao) -> None:
        self._estado.registrar_infracao(self, infracao)

    def concluir_prazo(self, data_referencia: date) -> None:
        self._estado.concluir_prazo(self, data_referencia)

    def pode_dirigir(self) -> bool:
        return self._estado.pode_dirigir()

    def possui_bloqueio_ativo(self) -> bool:
        return bool(self.bloqueios_ativos)
