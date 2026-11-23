from abc import ABC, abstractmethod

from aplicativo.dominio.modelos import Infracao, SituacaoInfracao


class PoliticaDesconto(ABC):
    nome: str

    @abstractmethod
    def percentuais_disponiveis(self) -> list[int]: ...


class PoliticaOrgaoAderenteSNE(PoliticaDesconto):
    nome = "Órgão aderente ao SNE"

    def percentuais_disponiveis(self) -> list[int]:
        return [20, 40]


class PoliticaDescontoCDT(PoliticaDesconto):
    nome = "Desconto de 20% pela Carteira Digital de Trânsito"

    def percentuais_disponiveis(self) -> list[int]:
        return [20]


class PoliticaSomenteConsulta(PoliticaDesconto):
    nome = "Sem desconto disponível"

    def percentuais_disponiveis(self) -> list[int]:
        return []


class ContextoBeneficioInfracao:
    def __init__(self) -> None:
        self._politica: PoliticaDesconto = PoliticaSomenteConsulta()

    def definir_politica(self, politica: PoliticaDesconto) -> None:
        self._politica = politica

    @property
    def politica(self) -> PoliticaDesconto:
        return self._politica

    def percentuais_disponiveis(self) -> list[int]:
        return self._politica.percentuais_disponiveis()


def selecionar_politica_desconto(infracao: Infracao) -> PoliticaDesconto:
    if infracao.situacao != SituacaoInfracao.A_VENCER:
        return PoliticaSomenteConsulta()
    if infracao.orgao_autuador.aderiu_sne:
        return PoliticaOrgaoAderenteSNE()
    if infracao.orgao_autuador.oferece_desconto_cdt:
        return PoliticaDescontoCDT()
    return PoliticaSomenteConsulta()
