import re

from pydantic import BaseModel, Field, field_validator

from aplicativo.configuracao import PRIMEIRO_EXERCICIO_EMITIVEL, obter_exercicio_atual
from aplicativo.dominio.modelos import TipoDocumentoSNE
from aplicativo.padroes.chain_of_responsibility.alteracao_categoria import CATEGORIAS_EXISTENTES
from aplicativo.padroes.state.habilitacao import Gravidade


def manter_apenas_digitos(valor: object) -> str:
    return re.sub(r"\D", "", str(valor or ""))


class RequisicaoAlteracaoEndereco(BaseModel):
    uf: str = Field(min_length=2, max_length=2, description="UF do novo endereço")
    cep: str = Field(pattern=r"^\d{8}$", description="CEP com 8 dígitos")
    logradouro: str = Field(min_length=3, max_length=120)
    caixa_postal: bool = False

    @field_validator("uf", mode="before")
    @classmethod
    def normalizar_uf(cls, valor: object) -> str:
        return str(valor or "").strip().upper()

    @field_validator("cep", mode="before")
    @classmethod
    def normalizar_cep(cls, valor: object) -> str:
        return manter_apenas_digitos(valor)

    @property
    def cep_formatado(self) -> str:
        return f"{self.cep[:5]}-{self.cep[5:]}"


class RequisicaoEmissaoCRLVe(BaseModel):
    exercicio: int = Field(default_factory=obter_exercicio_atual, ge=PRIMEIRO_EXERCICIO_EMITIVEL)

    @field_validator("exercicio")
    @classmethod
    def impedir_exercicio_futuro(cls, valor: int) -> int:
        exercicio_atual = obter_exercicio_atual()
        if valor > exercicio_atual:
            raise ValueError(f"o exercício não pode ser posterior a {exercicio_atual}")
        return valor


class RequisicaoElegibilidadeTEI(BaseModel):
    cpf_comprador: str = Field(pattern=r"^\d{11}$", description="CPF do comprador com 11 dígitos")

    @field_validator("cpf_comprador", mode="before")
    @classmethod
    def normalizar_cpf(cls, valor: object) -> str:
        return manter_apenas_digitos(valor)


class RequisicaoDesconto(BaseModel):
    percentual: int = Field(ge=1, le=100)
    termo_aceito: bool = False


class RequisicaoAdesaoSNE(BaseModel):
    tipo_documento: TipoDocumentoSNE
    numero_cnh: str = ""
    codigo_seguranca_cnh: str = ""
    placa: str = ""
    renavam: str = ""
    numero_seguranca_crv: str = ""


class RequisicaoIndicacaoCondutor(BaseModel):
    cpf_condutor: str = Field(pattern=r"^\d{11}$", description="CPF do condutor indicado")
    numero_cnh_condutor: str = Field(pattern=r"^\d{11}$", description="Número da CNH do condutor indicado")
    declaracao_aceita: bool

    @field_validator("cpf_condutor", "numero_cnh_condutor", mode="before")
    @classmethod
    def normalizar_documento(cls, valor: object) -> str:
        return manter_apenas_digitos(valor)

    @field_validator("declaracao_aceita")
    @classmethod
    def exigir_declaracao(cls, valor: bool) -> bool:
        if not valor:
            raise ValueError("é preciso confirmar a declaração de responsabilidade")
        return valor


class RequisicaoInfracaoHabilitacao(BaseModel):
    gravidade: Gravidade


class RequisicaoAlteracaoCategoria(BaseModel):
    categoria_desejada: str

    @field_validator("categoria_desejada", mode="before")
    @classmethod
    def validar_categoria(cls, valor: object) -> str:
        categoria = str(valor or "").strip().upper()
        if categoria not in CATEGORIAS_EXISTENTES:
            raise ValueError(f"use uma das categorias {', '.join(CATEGORIAS_EXISTENTES)}")
        return categoria


class RespostaOperacao(BaseModel):
    sucesso: bool
    mensagem: str
    dados: dict = Field(default_factory=dict)
