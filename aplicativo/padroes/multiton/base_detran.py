from threading import Lock
from typing import ClassVar

from aplicativo.dominio.dados_demonstracao import criar_transferencias, criar_veiculos
from aplicativo.dominio.excecoes import RecursoNaoEncontrado
from aplicativo.dominio.modelos import Transferencia, Veiculo

UNIDADES_FEDERATIVAS_DISPONIVEIS = ("DF", "GO")


class BaseDetranMultiton:
    _instancias: ClassVar[dict[str, "BaseDetranMultiton"]] = {}
    _trava_criacao: ClassVar[Lock] = Lock()

    def __init__(self, unidade_federativa: str) -> None:
        self.unidade_federativa = unidade_federativa
        self._veiculos_por_placa = {veiculo.placa: veiculo for veiculo in criar_veiculos(unidade_federativa)}
        self._transferencias = criar_transferencias(unidade_federativa)

    @classmethod
    def obter_instancia(cls, unidade_federativa: str) -> "BaseDetranMultiton":
        unidade_normalizada = unidade_federativa.strip().upper()
        if unidade_normalizada not in UNIDADES_FEDERATIVAS_DISPONIVEIS:
            raise RecursoNaoEncontrado(
                f"UF {unidade_normalizada} indisponível. Opções: {', '.join(UNIDADES_FEDERATIVAS_DISPONIVEIS)}."
            )
        with cls._trava_criacao:
            if unidade_normalizada not in cls._instancias:
                cls._instancias[unidade_normalizada] = cls(unidade_normalizada)
            return cls._instancias[unidade_normalizada]

    @classmethod
    def reiniciar_instancias(cls) -> None:
        with cls._trava_criacao:
            cls._instancias.clear()

    def listar_veiculos(self) -> list[Veiculo]:
        return list(self._veiculos_por_placa.values())

    def buscar_veiculo(self, placa: str) -> Veiculo:
        veiculo = self._veiculos_por_placa.get(placa.strip().upper())
        if veiculo is None:
            raise RecursoNaoEncontrado(f"Veículo {placa.upper()} não encontrado na base de {self.unidade_federativa}.")
        return veiculo

    def listar_transferencias(self) -> list[Transferencia]:
        return list(self._transferencias)
