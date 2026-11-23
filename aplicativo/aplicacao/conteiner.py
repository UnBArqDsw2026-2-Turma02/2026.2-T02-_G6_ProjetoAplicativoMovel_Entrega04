from dataclasses import dataclass

from aplicativo.aplicacao.servicos_veiculos import ServicosVeiculos
from aplicativo.dominio.modelos import TipoDocumentoSNE
from aplicativo.infraestrutura.mocks import (
    ApiSneMock,
    ProvedorIdentidadeGovMock,
    RepositorioCidadaosMemoria,
    RepositorioSessoesMemoria,
    criar_api_orgao_autuador,
    criar_repositorio_cidadaos,
)
from aplicativo.padroes.adapter.autenticacao_gov import AutenticacaoGovBrAdapter, GatewayAutenticacao
from aplicativo.padroes.adapter.orgao_autuador import OrgaoAutuadorAdapter
from aplicativo.padroes.facade.infracoes_facade import InfracoesFacade
from aplicativo.padroes.facade.sne_facade import SneFacade
from aplicativo.padroes.multiton.base_detran import BaseDetranMultiton
from aplicativo.padroes.prototype.documentos import registro_documentos_emitidos
from aplicativo.padroes.strategy.validacao_documento_sne import (
    ContextoValidacaoDocumentoSNE,
    EstrategiaValidacaoCNH,
    EstrategiaValidacaoCRLV,
)


@dataclass
class ConteinerAplicacao:
    repositorio_cidadaos: RepositorioCidadaosMemoria
    repositorio_sessoes: RepositorioSessoesMemoria
    gateway_autenticacao: GatewayAutenticacao
    servicos_veiculos: ServicosVeiculos
    infracoes_facade: InfracoesFacade
    sne_facade: SneFacade


def criar_conteiner() -> ConteinerAplicacao:
    BaseDetranMultiton.reiniciar_instancias()
    registro_documentos_emitidos.limpar()

    repositorio_cidadaos = criar_repositorio_cidadaos()
    contexto_validacao_sne = ContextoValidacaoDocumentoSNE(
        {
            TipoDocumentoSNE.CNH: EstrategiaValidacaoCNH(),
            TipoDocumentoSNE.CRLV: EstrategiaValidacaoCRLV("DF"),
        }
    )
    return ConteinerAplicacao(
        repositorio_cidadaos=repositorio_cidadaos,
        repositorio_sessoes=RepositorioSessoesMemoria(),
        gateway_autenticacao=AutenticacaoGovBrAdapter(ProvedorIdentidadeGovMock(), repositorio_cidadaos),
        servicos_veiculos=ServicosVeiculos(repositorio_cidadaos),
        infracoes_facade=InfracoesFacade(OrgaoAutuadorAdapter(criar_api_orgao_autuador())),
        sne_facade=SneFacade(ApiSneMock(), contexto_validacao_sne),
    )
