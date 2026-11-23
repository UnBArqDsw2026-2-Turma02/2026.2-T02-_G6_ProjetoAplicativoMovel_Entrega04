from threading import Lock

from aplicativo.dominio.modelos import Cidadao, ResultadoOperacao, TipoDocumentoSNE
from aplicativo.infraestrutura.mocks import ApiSneMock
from aplicativo.padroes.strategy.validacao_documento_sne import ContextoValidacaoDocumentoSNE, DadosDocumentoSNE


class SneFacade:
    def __init__(self, api_sne: ApiSneMock, contexto_validacao: ContextoValidacaoDocumentoSNE) -> None:
        self._api_sne = api_sne
        self._contexto_validacao = contexto_validacao
        self._trava_adesoes = Lock()

    def consultar_situacao(self, cidadao: Cidadao) -> dict:
        adesao = self._api_sne.consultar_adesao(cidadao.cpf)
        return {"aderiu": adesao is not None, "adesao": adesao}

    def aderir(
        self, cidadao: Cidadao, tipo_documento: TipoDocumentoSNE, dados_documento: DadosDocumentoSNE
    ) -> ResultadoOperacao:
        with self._trava_adesoes:
            if cidadao.aderiu_sne:
                return ResultadoOperacao(False, "Você já aderiu ao SNE.", self.consultar_situacao(cidadao))

            identificador_documento = self._contexto_validacao.validar(tipo_documento, cidadao, dados_documento)
            adesao = self._api_sne.registrar_adesao(cidadao.cpf, tipo_documento.value, identificador_documento)
            cidadao.aderiu_sne = True
            return ResultadoOperacao(
                True,
                f"Adesão ao SNE confirmada com {identificador_documento}. Protocolo {adesao['protocolo']}.",
                {"aderiu": True, "adesao": adesao},
            )
