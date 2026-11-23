import re

from pydantic import BaseModel, Field, field_validator

from aplicativo.configuracao import PRIMEIRO_EXERCICIO_EMITIVEL, obter_exercicio_atual
from aplicativo.dominio.modelos import TipoDocumentoSNE


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


class RespostaOperacao(BaseModel):
    sucesso: bool
    mensagem: str
    dados: dict = Field(default_factory=dict)
