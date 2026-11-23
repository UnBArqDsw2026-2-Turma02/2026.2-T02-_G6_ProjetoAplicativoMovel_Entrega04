from abc import ABC, abstractmethod
from dataclasses import dataclass

from aplicativo.dominio.excecoes import EntradaInvalida, RecursoNaoEncontrado
from aplicativo.dominio.modelos import Cidadao, TipoDocumentoSNE
from aplicativo.padroes.multiton.base_detran import BaseDetranMultiton


@dataclass
class DadosDocumentoSNE:
    numero_cnh: str = ""
    codigo_seguranca_cnh: str = ""
    placa: str = ""
    renavam: str = ""
    numero_seguranca_crv: str = ""


class EstrategiaValidacaoDocumentoSNE(ABC):
    @abstractmethod
    def validar(self, cidadao: Cidadao, dados_documento: DadosDocumentoSNE) -> str: ...


class EstrategiaValidacaoCNH(EstrategiaValidacaoDocumentoSNE):
    def validar(self, cidadao: Cidadao, dados_documento: DadosDocumentoSNE) -> str:
        cnh_confere = dados_documento.numero_cnh.strip() == cidadao.numero_cnh
        codigo_confere = dados_documento.codigo_seguranca_cnh.strip() == cidadao.codigo_seguranca_cnh
        if not (cidadao.numero_cnh and cnh_confere and codigo_confere):
            raise EntradaInvalida("Número da CNH ou código de segurança não conferem com o seu cadastro.")
        return f"CNH {cidadao.numero_cnh}"


class EstrategiaValidacaoCRLV(EstrategiaValidacaoDocumentoSNE):
    def __init__(self, unidade_federativa: str) -> None:
        self._unidade_federativa = unidade_federativa

    def validar(self, cidadao: Cidadao, dados_documento: DadosDocumentoSNE) -> str:
        base_detran = BaseDetranMultiton.obter_instancia(self._unidade_federativa)
        try:
            veiculo = base_detran.buscar_veiculo(dados_documento.placa)
        except RecursoNaoEncontrado:
            raise EntradaInvalida("Veículo não encontrado para o documento informado.") from None
        documento_confere = (
            veiculo.cpf_proprietario == cidadao.cpf
            and veiculo.renavam == dados_documento.renavam.strip()
            and veiculo.numero_seguranca_crv == dados_documento.numero_seguranca_crv.strip()
        )
        if not documento_confere:
            raise EntradaInvalida("Placa, RENAVAM ou número de segurança do CRV não conferem com o seu cadastro.")
        return f"CRLV {veiculo.placa}/{veiculo.renavam}"


class ContextoValidacaoDocumentoSNE:
    def __init__(self, estrategias_por_tipo: dict[TipoDocumentoSNE, EstrategiaValidacaoDocumentoSNE]) -> None:
        self._estrategias_por_tipo = estrategias_por_tipo

    def validar(self, tipo_documento: TipoDocumentoSNE, cidadao: Cidadao, dados_documento: DadosDocumentoSNE) -> str:
        estrategia = self._estrategias_por_tipo.get(tipo_documento)
        if estrategia is None:
            raise EntradaInvalida(f"Tipo de documento {tipo_documento} não suportado para a adesão ao SNE.")
        return estrategia.validar(cidadao, dados_documento)
