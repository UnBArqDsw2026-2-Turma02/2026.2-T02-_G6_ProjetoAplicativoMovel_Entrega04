import secrets
from copy import deepcopy
from uuid import uuid4

from aplicativo.dominio.dados_demonstracao import (
    CPF_CIDADAO_DEMONSTRACAO,
    NOME_CIDADAO_DEMONSTRACAO,
    criar_autos_de_infracao,
    criar_cidadaos,
)
from aplicativo.dominio.modelos import Cidadao


def gerar_protocolo(prefixo: str) -> str:
    return f"{prefixo}-{uuid4().hex[:8].upper()}"


class RepositorioCidadaosMemoria:
    def __init__(self, cidadaos: list[Cidadao]) -> None:
        self._cidadaos_por_cpf = {cidadao.cpf: cidadao for cidadao in cidadaos}

    def buscar_por_cpf(self, cpf: str) -> Cidadao | None:
        return self._cidadaos_por_cpf.get(cpf)

    def salvar(self, cidadao: Cidadao) -> None:
        self._cidadaos_por_cpf[cidadao.cpf] = cidadao


class RepositorioSessoesMemoria:
    def __init__(self) -> None:
        self._cpf_por_token: dict[str, str] = {}

    def criar_sessao(self, cpf: str) -> str:
        self._cpf_por_token = {token: cpf_salvo for token, cpf_salvo in self._cpf_por_token.items() if cpf_salvo != cpf}
        token_sessao = secrets.token_urlsafe(32)
        self._cpf_por_token[token_sessao] = cpf
        return token_sessao

    def buscar_cpf(self, token_sessao: str) -> str | None:
        return self._cpf_por_token.get(token_sessao)

    def encerrar_sessao(self, token_sessao: str) -> None:
        self._cpf_por_token.pop(token_sessao, None)


class ProvedorIdentidadeGovMock:
    def emitir_token_simulado(self) -> dict:
        return {
            "sub": CPF_CIDADAO_DEMONSTRACAO,
            "name": NOME_CIDADAO_DEMONSTRACAO,
            "email": "ana.moreira@exemplo.com",
            "amr": ["passwd"],
            "reliability": "prata",
        }


class ApiOrgaoAutuadorMock:
    def __init__(self, autos_de_infracao: list[dict]) -> None:
        self._autos_por_codigo = {auto["auto"]: deepcopy(auto) for auto in autos_de_infracao}

    def consultar_autos(self, documento_condutor: str) -> list[dict]:
        return [
            deepcopy(auto) for auto in self._autos_por_codigo.values() if auto["doc_condutor"] == documento_condutor
        ]

    def registrar_beneficio(self, codigo_auto: str, percentual: int) -> dict:
        self._autos_por_codigo[codigo_auto]["pct_beneficio"] = str(percentual)
        return {"cod_retorno": "00", "protocolo": gerar_protocolo("DESC")}


class ApiSneMock:
    def __init__(self) -> None:
        self._adesoes_por_cpf: dict[str, dict] = {}

    def consultar_adesao(self, cpf: str) -> dict | None:
        return self._adesoes_por_cpf.get(cpf)

    def registrar_adesao(self, cpf: str, tipo_documento: str, identificador_documento: str) -> dict:
        adesao = {
            "protocolo": gerar_protocolo("SNE"),
            "tipo_documento": tipo_documento,
            "identificador_documento": identificador_documento,
        }
        self._adesoes_por_cpf[cpf] = adesao
        return adesao


def criar_repositorio_cidadaos() -> RepositorioCidadaosMemoria:
    return RepositorioCidadaosMemoria(criar_cidadaos())


def criar_api_orgao_autuador() -> ApiOrgaoAutuadorMock:
    return ApiOrgaoAutuadorMock(criar_autos_de_infracao())
