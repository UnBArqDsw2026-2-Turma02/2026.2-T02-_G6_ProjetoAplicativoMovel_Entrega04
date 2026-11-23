from datetime import date
from threading import Lock

from aplicativo.dominio.modelos import Boleto, Cidadao, Infracao, ResultadoOperacao, SituacaoInfracao
from aplicativo.padroes.adapter.boleto import GatewayBoleto
from aplicativo.padroes.adapter.indicacao_condutor import PedidoIndicacao, PortaProtocolo
from aplicativo.padroes.adapter.orgao_autuador import GatewayInfracoes
from aplicativo.padroes.strategy.politicas_desconto import ContextoBeneficioInfracao, selecionar_politica_desconto

PERCENTUAL_EXCLUSIVO_SNE = 40


class InfracoesFacade:
    def __init__(
        self,
        gateway_infracoes: GatewayInfracoes,
        gateway_boleto: GatewayBoleto,
        porta_indicacao: PortaProtocolo,
    ) -> None:
        self._gateway_infracoes = gateway_infracoes
        self._gateway_boleto = gateway_boleto
        self._porta_indicacao = porta_indicacao
        self._indicacoes_por_infracao: dict[str, dict] = {}
        self._trava_solicitacoes = Lock()

    def listar_infracoes(self, cidadao: Cidadao) -> list[dict]:
        infracoes = self._gateway_infracoes.listar_por_cpf(cidadao.cpf)
        infracoes_ordenadas = sorted(
            infracoes, key=lambda infracao: (infracao.situacao != SituacaoInfracao.A_VENCER, infracao.vencimento)
        )
        return [self._descrever_infracao(infracao, cidadao) for infracao in infracoes_ordenadas]

    def detalhar_infracao(self, cidadao: Cidadao, identificador_infracao: str) -> dict:
        infracao = self._gateway_infracoes.buscar(cidadao.cpf, identificador_infracao)
        return self._descrever_infracao(infracao, cidadao)

    def resumir_infracoes(self, cidadao: Cidadao) -> dict:
        infracoes = self._gateway_infracoes.listar_por_cpf(cidadao.cpf)
        infracoes_em_aberto = [infracao for infracao in infracoes if infracao.situacao != SituacaoInfracao.PAGA]
        return {
            "quantidade_total": len(infracoes),
            "quantidade_em_aberto": len(infracoes_em_aberto),
            "quantidade_com_desconto_disponivel": sum(
                1
                for infracao in infracoes
                if not infracao.percentual_desconto_aplicado and self._calcular_percentuais(infracao, cidadao)
            ),
            "valor_em_aberto": round(sum(infracao.valor_a_pagar for infracao in infracoes_em_aberto), 2),
        }

    def solicitar_desconto(
        self, cidadao: Cidadao, identificador_infracao: str, percentual: int, termo_aceito: bool
    ) -> ResultadoOperacao:
        with self._trava_solicitacoes:
            return self._processar_solicitacao_desconto(cidadao, identificador_infracao, percentual, termo_aceito)

    def _processar_solicitacao_desconto(
        self, cidadao: Cidadao, identificador_infracao: str, percentual: int, termo_aceito: bool
    ) -> ResultadoOperacao:
        infracao = self._gateway_infracoes.buscar(cidadao.cpf, identificador_infracao)
        percentuais_disponiveis = self._calcular_percentuais(infracao, cidadao, incluir_exclusivos_sne=True)

        if infracao.situacao != SituacaoInfracao.A_VENCER:
            return ResultadoOperacao(False, "Desconto indisponível para infração vencida ou paga.")
        if infracao.percentual_desconto_aplicado:
            return ResultadoOperacao(
                False, f"Esta infração já tem desconto de {infracao.percentual_desconto_aplicado}% aplicado."
            )
        if percentual not in percentuais_disponiveis:
            return ResultadoOperacao(False, f"O desconto de {percentual}% não está disponível para esta infração.")
        if percentual == PERCENTUAL_EXCLUSIVO_SNE and not cidadao.aderiu_sne:
            return ResultadoOperacao(False, "Faça a adesão ao SNE para usar o desconto de 40%.")
        if percentual == PERCENTUAL_EXCLUSIVO_SNE and not termo_aceito:
            return ResultadoOperacao(False, "O desconto de 40% exige o aceite do termo de reconhecimento da infração.")

        protocolo = self._gateway_infracoes.enviar_solicitacao_desconto(infracao, percentual)
        if self._gateway_boleto.consultar(infracao.identificador):
            self._gateway_boleto.atualizar_desconto(infracao.identificador, percentual)
        infracao_atualizada = self._gateway_infracoes.buscar(cidadao.cpf, identificador_infracao)
        return ResultadoOperacao(
            True,
            f"Desconto de {percentual}% aplicado. Protocolo {protocolo}.",
            {"protocolo": protocolo, "infracao": self._descrever_infracao(infracao_atualizada, cidadao)},
        )

    def solicitar_boleto(self, cidadao: Cidadao, identificador_infracao: str) -> ResultadoOperacao:
        with self._trava_solicitacoes:
            infracao = self._gateway_infracoes.buscar(cidadao.cpf, identificador_infracao)
            if infracao.situacao == SituacaoInfracao.PAGA:
                return ResultadoOperacao(False, "Não é possível solicitar boleto para infração paga.")
            boleto_existente = self._gateway_boleto.consultar(infracao.identificador)
            if boleto_existente:
                return ResultadoOperacao(
                    True,
                    "Já existe um boleto para esta infração. Nenhum novo pedido foi enviado.",
                    {"boleto": self._descrever_boleto(boleto_existente)},
                )
            vencimento = max(infracao.vencimento, date.today())
            boleto = self._gateway_boleto.emitir(infracao, vencimento)
            return ResultadoOperacao(True, "Boleto gerado.", {"boleto": self._descrever_boleto(boleto)})

    def obter_boleto(self, cidadao: Cidadao, identificador_infracao: str) -> dict | None:
        infracao = self._gateway_infracoes.buscar(cidadao.cpf, identificador_infracao)
        boleto = self._gateway_boleto.consultar(infracao.identificador)
        return self._descrever_boleto(boleto) if boleto else None

    def indicar_condutor(
        self, cidadao: Cidadao, identificador_infracao: str, cpf_condutor: str, numero_cnh_condutor: str
    ) -> ResultadoOperacao:
        with self._trava_solicitacoes:
            infracao = self._gateway_infracoes.buscar(cidadao.cpf, identificador_infracao)
            if infracao.situacao == SituacaoInfracao.PAGA:
                return ResultadoOperacao(False, "Não é possível indicar condutor para infração paga.")
            if infracao.identificador in self._indicacoes_por_infracao:
                return ResultadoOperacao(False, "Já existe uma indicação de condutor para esta infração.")
            if cpf_condutor == cidadao.cpf:
                return ResultadoOperacao(False, "O condutor indicado deve ser outra pessoa.")
            pedido = PedidoIndicacao(
                auto=infracao.identificador,
                requerente_id=cidadao.cpf,
                condutor_id=cpf_condutor,
                anexos=(f"cnh_{numero_cnh_condutor}.pdf",),
            )
            recibo = self._porta_indicacao.protocolar(pedido)
            indicacao = {
                "protocolo": recibo.numero,
                "situacao": recibo.situacao,
                "cpf_condutor_mascarado": f"***.{cpf_condutor[3:6]}.{cpf_condutor[6:9]}-**",
                "data": date.today().strftime("%d/%m/%Y"),
            }
            self._indicacoes_por_infracao[infracao.identificador] = indicacao
            return ResultadoOperacao(
                True,
                f"Indicação recebida. Protocolo {recibo.numero}. O recebimento não significa aprovação.",
                {"indicacao": indicacao},
            )

    @staticmethod
    def _descrever_boleto(boleto: Boleto) -> dict:
        return {
            "identificador": boleto.identificador,
            "numero_auto": boleto.numero_auto,
            "situacao": boleto.situacao.value,
            "vencimento": boleto.vencimento.strftime("%d/%m/%Y"),
            "valor_original": boleto.valor_original,
            "percentual_desconto": boleto.percentual_desconto,
            "valor_desconto": boleto.valor_desconto,
            "valor_a_pagar": boleto.valor_a_pagar,
            "codigo_pagamento": boleto.codigo_pagamento,
            "nome_arquivo": boleto.nome_arquivo,
        }

    def _calcular_percentuais(
        self, infracao: Infracao, cidadao: Cidadao, incluir_exclusivos_sne: bool = False
    ) -> list[int]:
        contexto_beneficio = ContextoBeneficioInfracao()
        contexto_beneficio.definir_politica(selecionar_politica_desconto(infracao))
        percentuais = contexto_beneficio.percentuais_disponiveis()
        if incluir_exclusivos_sne or cidadao.aderiu_sne:
            return percentuais
        return [percentual for percentual in percentuais if percentual != PERCENTUAL_EXCLUSIVO_SNE]

    def _descrever_infracao(self, infracao: Infracao, cidadao: Cidadao) -> dict:
        politica = selecionar_politica_desconto(infracao)
        percentuais_da_politica = politica.percentuais_disponiveis()
        boleto = self._gateway_boleto.consultar(infracao.identificador)
        return {
            "identificador": infracao.identificador,
            "placa": infracao.placa,
            "descricao": infracao.descricao,
            "codigo_enquadramento": infracao.codigo_enquadramento,
            "local": infracao.local,
            "data_cometimento": infracao.data_cometimento.strftime("%d/%m/%Y"),
            "vencimento": infracao.vencimento.strftime("%d/%m/%Y"),
            "situacao": infracao.situacao.value,
            "orgao_autuador": infracao.orgao_autuador.nome,
            "orgao_aderiu_sne": infracao.orgao_autuador.aderiu_sne,
            "politica_desconto": politica.nome,
            "valor_original": infracao.valor_original,
            "percentual_desconto_aplicado": infracao.percentual_desconto_aplicado,
            "valor_a_pagar": infracao.valor_a_pagar,
            "boleto": self._descrever_boleto(boleto) if boleto else None,
            "indicacao_condutor": self._indicacoes_por_infracao.get(infracao.identificador),
            "opcoes_desconto": [
                {
                    "percentual": percentual,
                    "valor_final": infracao.valor_com_desconto(percentual),
                    "exige_sne": percentual == PERCENTUAL_EXCLUSIVO_SNE,
                    "liberado": percentual != PERCENTUAL_EXCLUSIVO_SNE or cidadao.aderiu_sne,
                }
                for percentual in percentuais_da_politica
            ],
        }
