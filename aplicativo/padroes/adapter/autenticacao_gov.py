from abc import ABC, abstractmethod

from aplicativo.dominio.modelos import Cidadao
from aplicativo.infraestrutura.mocks import ProvedorIdentidadeGovMock, RepositorioCidadaosMemoria


class GatewayAutenticacao(ABC):
    @abstractmethod
    def autenticar(self) -> Cidadao: ...

    @abstractmethod
    def nivel_da_conta(self) -> str: ...


class AutenticacaoGovBrAdapter(GatewayAutenticacao):
    def __init__(
        self, provedor_identidade: ProvedorIdentidadeGovMock, repositorio_cidadaos: RepositorioCidadaosMemoria
    ) -> None:
        self._provedor_identidade = provedor_identidade
        self._repositorio_cidadaos = repositorio_cidadaos

    def autenticar(self) -> Cidadao:
        token_identidade = self._provedor_identidade.emitir_token_simulado()
        cidadao_cadastrado = self._repositorio_cidadaos.buscar_por_cpf(token_identidade["sub"])
        if cidadao_cadastrado is not None:
            return cidadao_cadastrado
        novo_cidadao = Cidadao(
            cpf=token_identidade["sub"], nome=token_identidade["name"], email=token_identidade["email"]
        )
        self._repositorio_cidadaos.salvar(novo_cidadao)
        return novo_cidadao

    def nivel_da_conta(self) -> str:
        return self._provedor_identidade.emitir_token_simulado()["reliability"]
