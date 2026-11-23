from abc import ABC, abstractmethod
from enum import Enum

from aplicativo.padroes.state.habilitacao import Habilitacao

CATEGORIAS_EXISTENTES = ("A", "AB", "ACC", "ACC+B", "C", "D", "E")
CATEGORIAS_PRESENCIAIS = ("C", "D", "E")
CATEGORIAS_PERMITIDAS_POR_ATUAL = {
    "B": ("ACC+B", "AB"),
    "A": ("AB",),
    "ACC": ("A", "AB", "ACC+B"),
}


class ResultadoAlteracaoCategoria(str, Enum):
    ACEITA = "aceita"
    RECUSADA = "recusada"
    ENCAMINHADA_AO_DETRAN = "encaminhada_ao_detran"


class OrgaoDeTransito:
    def __init__(self, unidade_federativa: str) -> None:
        self.unidade_federativa = unidade_federativa

    def encaminhar_atendimento_presencial(self) -> str:
        return f"Procure o Detran-{self.unidade_federativa} para obter essa categoria."


class SolicitacaoAlteracaoCategoria:
    def __init__(self, habilitacao: Habilitacao, categoria_desejada: str) -> None:
        self.habilitacao = habilitacao
        self.categoria_desejada = categoria_desejada
        self.resultado: ResultadoAlteracaoCategoria | None = None
        self.motivo = ""

    def validar_elegibilidade(self, primeiro_validador: "ValidadorAlteracaoCategoria") -> ResultadoAlteracaoCategoria:
        self.resultado = primeiro_validador.validar(self)
        return self.resultado


class ValidadorAlteracaoCategoria(ABC):
    def __init__(self) -> None:
        self._proximo: ValidadorAlteracaoCategoria | None = None

    def definir_proximo(self, proximo: "ValidadorAlteracaoCategoria") -> "ValidadorAlteracaoCategoria":
        self._proximo = proximo
        return proximo

    def validar(self, solicitacao: SolicitacaoAlteracaoCategoria) -> ResultadoAlteracaoCategoria:
        resultado = self.tratar(solicitacao)
        if resultado is not None:
            return resultado
        if self._proximo is not None:
            return self._proximo.validar(solicitacao)
        return ResultadoAlteracaoCategoria.ACEITA

    @abstractmethod
    def tratar(self, solicitacao: SolicitacaoAlteracaoCategoria) -> ResultadoAlteracaoCategoria | None: ...


class ValidadorDetran(ValidadorAlteracaoCategoria):
    def __init__(self, orgao_de_transito: OrgaoDeTransito) -> None:
        super().__init__()
        self._orgao_de_transito = orgao_de_transito

    def tratar(self, solicitacao: SolicitacaoAlteracaoCategoria) -> ResultadoAlteracaoCategoria | None:
        if solicitacao.categoria_desejada in CATEGORIAS_PRESENCIAIS:
            solicitacao.motivo = self._orgao_de_transito.encaminhar_atendimento_presencial()
            return ResultadoAlteracaoCategoria.ENCAMINHADA_AO_DETRAN
        return None


class ValidadorCompatibilidade(ValidadorAlteracaoCategoria):
    def tratar(self, solicitacao: SolicitacaoAlteracaoCategoria) -> ResultadoAlteracaoCategoria | None:
        categoria_atual = solicitacao.habilitacao.categoria
        categorias_permitidas = CATEGORIAS_PERMITIDAS_POR_ATUAL.get(categoria_atual, ())
        if solicitacao.categoria_desejada not in categorias_permitidas:
            solicitacao.motivo = (
                f"A categoria {solicitacao.categoria_desejada} não está disponível para quem tem {categoria_atual}."
            )
            return ResultadoAlteracaoCategoria.RECUSADA
        return None


class ValidadorBloqueios(ValidadorAlteracaoCategoria):
    def tratar(self, solicitacao: SolicitacaoAlteracaoCategoria) -> ResultadoAlteracaoCategoria | None:
        if solicitacao.habilitacao.possui_bloqueio_ativo():
            motivos = ", ".join(solicitacao.habilitacao.bloqueios_ativos)
            solicitacao.motivo = f"Habilitação com bloqueio ativo: {motivos}."
            return ResultadoAlteracaoCategoria.RECUSADA
        return None


def montar_cadeia_validacao(orgao_de_transito: OrgaoDeTransito) -> ValidadorAlteracaoCategoria:
    primeiro_validador = ValidadorDetran(orgao_de_transito)
    primeiro_validador.definir_proximo(ValidadorCompatibilidade()).definir_proximo(ValidadorBloqueios())
    return primeiro_validador
