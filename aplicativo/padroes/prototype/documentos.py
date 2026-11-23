from abc import ABC, abstractmethod
from copy import deepcopy
from datetime import datetime
from threading import Lock
from uuid import uuid4

from aplicativo.dominio.modelos import DadosEmissao


class DocumentoVeicular(ABC):
    @abstractmethod
    def clonar(self) -> "DocumentoVeicular": ...

    @abstractmethod
    def preencher(self, dados_emissao: DadosEmissao) -> None: ...

    @abstractmethod
    def para_dicionario(self) -> dict: ...


class CRLVe(DocumentoVeicular):
    def __init__(self) -> None:
        self.tipo = "CRLV-e"
        self.orgao_emissor = "Órgão Executivo de Trânsito (simulado)"
        self.versao_layout = "2026.1"
        self.placa: str | None = None
        self.renavam: str | None = None
        self.exercicio: int | None = None
        self.marca_modelo: str | None = None
        self.nome_proprietario: str | None = None
        self.codigo_autenticacao: str | None = None
        self.emitido_em: datetime | None = None

    def clonar(self) -> "CRLVe":
        return deepcopy(self)

    def preencher(self, dados_emissao: DadosEmissao) -> None:
        self.placa = dados_emissao.placa
        self.renavam = dados_emissao.renavam
        self.exercicio = dados_emissao.exercicio
        self.marca_modelo = dados_emissao.marca_modelo
        self.nome_proprietario = dados_emissao.nome_proprietario
        self.codigo_autenticacao = uuid4().hex[:12].upper()
        self.emitido_em = datetime.now()

    def para_dicionario(self) -> dict:
        return {
            "tipo": self.tipo,
            "orgao_emissor": self.orgao_emissor,
            "versao_layout": self.versao_layout,
            "placa": self.placa,
            "renavam": self.renavam,
            "exercicio": self.exercicio,
            "marca_modelo": self.marca_modelo,
            "nome_proprietario": self.nome_proprietario,
            "codigo_autenticacao": self.codigo_autenticacao,
            "emitido_em": self.emitido_em.strftime("%d/%m/%Y %H:%M") if self.emitido_em else None,
            "identificador_objeto": id(self),
        }


class EmissorCRLVe:
    def __init__(self, prototipo: DocumentoVeicular) -> None:
        self._prototipo = prototipo

    def emitir(self, dados_emissao: DadosEmissao) -> DocumentoVeicular:
        documento = self._prototipo.clonar()
        documento.preencher(dados_emissao)
        return documento


class RegistroDocumentosEmitidos:
    def __init__(self) -> None:
        self._documentos: list[DocumentoVeicular] = []
        self._trava = Lock()

    def registrar(self, documento: DocumentoVeicular) -> None:
        with self._trava:
            self._documentos.append(documento)

    def listar(self) -> list[DocumentoVeicular]:
        with self._trava:
            return list(self._documentos)

    def limpar(self) -> None:
        with self._trava:
            self._documentos.clear()


PROTOTIPO_CRLVE = CRLVe()
registro_documentos_emitidos = RegistroDocumentosEmitidos()
