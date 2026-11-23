from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from threading import Lock

from aplicativo.dominio.excecoes import RecursoNaoEncontrado
from aplicativo.dominio.modelos import Cidadao, ResultadoOperacao
from aplicativo.padroes.chain_of_responsibility.alteracao_categoria import (
    CATEGORIAS_EXISTENTES,
    OrgaoDeTransito,
    ResultadoAlteracaoCategoria,
    SolicitacaoAlteracaoCategoria,
    montar_cadeia_validacao,
)
from aplicativo.padroes.observer.acompanhamento_habilitacao import (
    AcompanhamentoHabilitacao,
    HistoricoAuditoria,
    NotificacaoEmail,
    NotificacaoPush,
)
from aplicativo.padroes.state.habilitacao import Gravidade, Habilitacao, InfracaoHabilitacao

UNIDADE_FEDERATIVA_ATENDIMENTO = "DF"
CATEGORIA_DEMONSTRACAO = "B"
DIAS_DESDE_EMISSAO_DEMONSTRACAO = 400

MENSAGENS_POR_RESULTADO = {
    ResultadoAlteracaoCategoria.ACEITA: "Solicitação aceita. Siga para os exames da nova categoria.",
    ResultadoAlteracaoCategoria.RECUSADA: "Solicitação recusada.",
    ResultadoAlteracaoCategoria.ENCAMINHADA_AO_DETRAN: "Solicitação encaminhada ao atendimento presencial.",
}


@dataclass
class ProntuarioCondutor:
    habilitacao: Habilitacao
    notificacao_push: NotificacaoPush = field(default_factory=NotificacaoPush)
    notificacao_email: NotificacaoEmail = field(default_factory=NotificacaoEmail)
    historico_auditoria: HistoricoAuditoria = field(default_factory=HistoricoAuditoria)
    solicitacoes_categoria: list[dict] = field(default_factory=list)

    def inscrever_observadores(self) -> None:
        for observador in (self.notificacao_push, self.notificacao_email, self.historico_auditoria):
            self.habilitacao.acompanhamento.adicionar(observador)


def criar_habilitacao(cidadao: Cidadao, data_emissao_ppd: date, categoria: str) -> Habilitacao:
    acompanhamento = AcompanhamentoHabilitacao(cidadao.nome)
    return Habilitacao(cidadao.numero_cnh or cidadao.cpf, categoria, data_emissao_ppd, acompanhamento)


def criar_prontuario_demonstracao(cidadao: Cidadao) -> ProntuarioCondutor:
    hoje = date.today()
    habilitacao = criar_habilitacao(
        cidadao, hoje - timedelta(days=DIAS_DESDE_EMISSAO_DEMONSTRACAO), CATEGORIA_DEMONSTRACAO
    )
    habilitacao.registrar_infracao(InfracaoHabilitacao("AIT-7781", Gravidade.LEVE, hoje - timedelta(days=210)))
    prontuario = ProntuarioCondutor(habilitacao)
    prontuario.inscrever_observadores()
    return prontuario


def ordenar_por_momento(registro: dict) -> datetime:
    return datetime.strptime(registro["momento"], "%d/%m/%Y %H:%M:%S")


class ServicosHabilitacao:
    def __init__(self) -> None:
        self._prontuarios_por_cpf: dict[str, ProntuarioCondutor] = {}
        self._cadeia_validacao = montar_cadeia_validacao(OrgaoDeTransito(UNIDADE_FEDERATIVA_ATENDIMENTO))
        self._trava = Lock()

    def _obter_prontuario(self, cidadao: Cidadao) -> ProntuarioCondutor:
        if not cidadao.numero_cnh:
            raise RecursoNaoEncontrado("Não há habilitação registrada para este cidadão.")
        if cidadao.cpf not in self._prontuarios_por_cpf:
            self._prontuarios_por_cpf[cidadao.cpf] = criar_prontuario_demonstracao(cidadao)
        return self._prontuarios_por_cpf[cidadao.cpf]

    def descrever(self, cidadao: Cidadao) -> dict:
        with self._trava:
            prontuario = self._obter_prontuario(cidadao)
            habilitacao = prontuario.habilitacao
            hoje = date.today()
            notificacoes = prontuario.notificacao_push.enviadas + prontuario.notificacao_email.enviadas
            return {
                "numero_registro": habilitacao.numero_registro,
                "categoria": habilitacao.categoria,
                "situacao": habilitacao.situacao,
                "pode_dirigir": habilitacao.pode_dirigir(),
                "data_emissao_ppd": habilitacao.data_emissao_ppd.strftime("%d/%m/%Y"),
                "data_limite_ppd": habilitacao.data_limite_ppd.strftime("%d/%m/%Y"),
                "prazo_ppd_concluido": hoje >= habilitacao.data_limite_ppd,
                "bloqueios_ativos": list(habilitacao.bloqueios_ativos),
                "historico_infracoes": [
                    {
                        "codigo": infracao.codigo,
                        "gravidade": infracao.gravidade.value,
                        "data": infracao.data.strftime("%d/%m/%Y"),
                    }
                    for infracao in habilitacao.historico_infracoes
                ],
                "notificacoes": sorted(notificacoes, key=ordenar_por_momento, reverse=True),
                "auditoria": list(reversed(prontuario.historico_auditoria.registros)),
                "solicitacoes_categoria": list(reversed(prontuario.solicitacoes_categoria)),
                "categorias_existentes": list(CATEGORIAS_EXISTENTES),
                "gravidades": [gravidade.value for gravidade in Gravidade],
            }

    def registrar_infracao(self, cidadao: Cidadao, gravidade: Gravidade) -> ResultadoOperacao:
        with self._trava:
            habilitacao = self._obter_prontuario(cidadao).habilitacao
            codigo = f"AIT-{len(habilitacao.historico_infracoes) + 1:04d}"
            habilitacao.registrar_infracao(InfracaoHabilitacao(codigo, gravidade, date.today()))
            return ResultadoOperacao(True, f"Infração {gravidade.value} {codigo} registrada no histórico.")

    def concluir_periodo_ppd(self, cidadao: Cidadao) -> ResultadoOperacao:
        with self._trava:
            habilitacao = self._obter_prontuario(cidadao).habilitacao
            habilitacao.concluir_prazo(date.today())
            return ResultadoOperacao(
                True,
                f"Período da PPD concluído. Situação atual: {habilitacao.situacao}.",
                {"situacao": habilitacao.situacao},
            )

    def iniciar_nova_habilitacao(self, cidadao: Cidadao) -> ResultadoOperacao:
        with self._trava:
            prontuario = self._obter_prontuario(cidadao)
            if prontuario.habilitacao.pode_dirigir():
                return ResultadoOperacao(False, "Só é possível reiniciar a 1ª habilitação após a cassação da PPD.")
            prontuario.habilitacao = criar_habilitacao(cidadao, date.today(), prontuario.habilitacao.categoria)
            prontuario.inscrever_observadores()
            prontuario.habilitacao.acompanhamento.notificar()
            return ResultadoOperacao(True, "Nova Permissão Para Dirigir iniciada.")

    def solicitar_alteracao_categoria(self, cidadao: Cidadao, categoria_desejada: str) -> ResultadoOperacao:
        with self._trava:
            prontuario = self._obter_prontuario(cidadao)
            solicitacao = SolicitacaoAlteracaoCategoria(prontuario.habilitacao, categoria_desejada)
            resultado = solicitacao.validar_elegibilidade(self._cadeia_validacao)
            registro = {
                "categoria_atual": prontuario.habilitacao.categoria,
                "categoria_desejada": categoria_desejada,
                "resultado": resultado.value,
                "motivo": solicitacao.motivo,
                "data": date.today().strftime("%d/%m/%Y"),
            }
            prontuario.solicitacoes_categoria.append(registro)
            return ResultadoOperacao(True, MENSAGENS_POR_RESULTADO[resultado], {"solicitacao": registro})
