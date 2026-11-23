from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum

DIAS_VALIDADE_VISTORIA = 90


class TipoRestricao(str, Enum):
    JUDICIAL = "judicial"
    ADMINISTRATIVA = "administrativa"


class DocumentoTransferencia(str, Enum):
    ATPV_E = "ATPV-e"
    DUT = "DUT"


class SituacaoTransferencia(str, Enum):
    CONCLUIDA = "concluida"
    EM_ANDAMENTO = "em_andamento"


class SituacaoInfracao(str, Enum):
    A_VENCER = "a_vencer"
    VENCIDA = "vencida"
    PAGA = "paga"


class TipoDocumentoSNE(str, Enum):
    CNH = "cnh"
    CRLV = "crlv"


@dataclass
class Endereco:
    uf: str
    cep: str
    logradouro: str = ""
    caixa_postal: bool = False


@dataclass
class Debito:
    descricao: str
    valor: float
    vencido: bool = True


@dataclass
class Restricao:
    descricao: str
    tipo: TipoRestricao


@dataclass
class Vistoria:
    ecv: str
    data_realizacao: date

    def esta_valida(self, data_referencia: date) -> bool:
        dias_desde_a_vistoria = data_referencia - self.data_realizacao
        return timedelta(0) <= dias_desde_a_vistoria <= timedelta(days=DIAS_VALIDADE_VISTORIA)


@dataclass
class Veiculo:
    placa: str
    renavam: str
    marca_modelo: str
    ano_modelo: int
    cor: str
    cpf_proprietario: str
    nome_proprietario: str
    endereco: Endereco
    numero_seguranca_crv: str = ""
    licenciamento_em_dia: bool = True
    documento_transferencia: DocumentoTransferencia = DocumentoTransferencia.ATPV_E
    debitos: list[Debito] = field(default_factory=list)
    restricoes: list[Restricao] = field(default_factory=list)
    financiamentos: list[str] = field(default_factory=list)
    vistoria: Vistoria | None = None

    @property
    def debitos_vencidos(self) -> list[Debito]:
        return [debito for debito in self.debitos if debito.vencido]

    @property
    def valor_total_debitos(self) -> float:
        return round(sum(debito.valor for debito in self.debitos), 2)

    @property
    def possui_pendencias_impeditivas(self) -> bool:
        return bool(self.debitos_vencidos or self.restricoes or not self.licenciamento_em_dia)

    def possui_restricao(self, tipo_restricao: TipoRestricao) -> bool:
        return any(restricao.tipo == tipo_restricao for restricao in self.restricoes)


@dataclass
class Cidadao:
    cpf: str
    nome: str
    email: str
    pessoa_fisica: bool = True
    cadastro_ativo: bool = True
    biometria_valida: bool = True
    numero_cnh: str = ""
    codigo_seguranca_cnh: str = ""
    aderiu_sne: bool = False

    @property
    def primeiro_nome(self) -> str:
        return self.nome.split()[0]

    @property
    def cpf_mascarado(self) -> str:
        return f"***.{self.cpf[3:6]}.{self.cpf[6:9]}-**"


@dataclass
class Transferencia:
    placa: str
    marca_modelo: str
    cpf_vendedor: str
    cpf_comprador: str
    data: date
    situacao: SituacaoTransferencia


@dataclass
class OrgaoAutuador:
    identificador: str
    nome: str
    aderiu_sne: bool
    oferece_desconto_cdt: bool


@dataclass
class Infracao:
    identificador: str
    cpf_condutor: str
    placa: str
    descricao: str
    codigo_enquadramento: str
    local: str
    data_cometimento: date
    vencimento: date
    valor_original: float
    situacao: SituacaoInfracao
    orgao_autuador: OrgaoAutuador
    percentual_desconto_aplicado: int = 0

    def valor_com_desconto(self, percentual: int) -> float:
        return round(self.valor_original * (100 - percentual) / 100, 2)

    @property
    def valor_a_pagar(self) -> float:
        return self.valor_com_desconto(self.percentual_desconto_aplicado)


@dataclass
class ResultadoConsulta:
    tipo: str
    itens: list[str] = field(default_factory=list)
    valor_total: float = 0.0

    @property
    def limpo(self) -> bool:
        return not self.itens


@dataclass
class ResultadoOperacao:
    sucesso: bool
    mensagem: str
    dados: dict = field(default_factory=dict)


@dataclass
class DadosEmissao:
    placa: str
    renavam: str
    exercicio: int
    marca_modelo: str
    nome_proprietario: str
