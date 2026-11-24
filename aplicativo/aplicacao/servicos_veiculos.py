from dataclasses import asdict
from threading import Lock

from aplicativo.dominio.excecoes import AcessoNegado
from aplicativo.dominio.modelos import Cidadao, Endereco, ResultadoOperacao, SituacaoTransferencia, Veiculo
from aplicativo.infraestrutura.mocks import RepositorioCidadaosMemoria
from aplicativo.padroes.factory_method.consultas import CRIADORES_DE_CONSULTA
from aplicativo.padroes.factory_method.servicos import (
    AlteracaoEnderecoCreator,
    EmissaoCRLVeCreator,
    VerificacaoElegibilidadeTEICreator,
)
from aplicativo.padroes.multiton.base_detran import UNIDADES_FEDERATIVAS_DISPONIVEIS, BaseDetranMultiton
from aplicativo.padroes.prototype.documentos import PROTOTIPO_CRLVE, registro_documentos_emitidos


def descrever_veiculo(veiculo: Veiculo) -> dict:
    return {
        "placa": veiculo.placa,
        "renavam": veiculo.renavam,
        "marca_modelo": veiculo.marca_modelo,
        "ano_modelo": veiculo.ano_modelo,
        "cor": veiculo.cor,
        "nome_proprietario": veiculo.nome_proprietario,
        "endereco": asdict(veiculo.endereco),
        "documento_transferencia": veiculo.documento_transferencia.value,
        "licenciamento_em_dia": veiculo.licenciamento_em_dia,
        "valor_total_debitos": veiculo.valor_total_debitos,
        "quantidade_restricoes": len(veiculo.restricoes),
        "possui_financiamento": bool(veiculo.financiamentos),
        "possui_pendencias_impeditivas": veiculo.possui_pendencias_impeditivas,
    }


class ServicosVeiculos:
    def __init__(self, repositorio_cidadaos: RepositorioCidadaosMemoria) -> None:
        self._repositorio_cidadaos = repositorio_cidadaos
        self._trava_alteracoes = Lock()

    @staticmethod
    def listar_unidades_federativas() -> list[str]:
        return list(UNIDADES_FEDERATIVAS_DISPONIVEIS)

    @staticmethod
    def listar_veiculos(unidade_federativa: str, cidadao: Cidadao) -> dict:
        base_detran = BaseDetranMultiton.obter_instancia(unidade_federativa)
        veiculos_do_cidadao = [
            veiculo for veiculo in base_detran.listar_veiculos() if veiculo.cpf_proprietario == cidadao.cpf
        ]
        return {
            "unidade_federativa": base_detran.unidade_federativa,
            "identificador_base": id(base_detran),
            "veiculos": [descrever_veiculo(veiculo) for veiculo in veiculos_do_cidadao],
        }

    @staticmethod
    def obter_veiculo_do_cidadao(unidade_federativa: str, placa: str, cidadao: Cidadao) -> Veiculo:
        veiculo = BaseDetranMultiton.obter_instancia(unidade_federativa).buscar_veiculo(placa)
        if veiculo.cpf_proprietario != cidadao.cpf:
            raise AcessoNegado(f"O veículo {veiculo.placa} não pertence ao cidadão autenticado.")
        return veiculo

    def consultar_situacao(self, unidade_federativa: str, placa: str, cidadao: Cidadao) -> dict:
        veiculo = self.obter_veiculo_do_cidadao(unidade_federativa, placa, cidadao)
        consultas = {}
        for nome_consulta, classe_creator in CRIADORES_DE_CONSULTA.items():
            resultado = classe_creator().consultar(veiculo)
            consultas[nome_consulta] = {
                "tipo": resultado.tipo,
                "itens": resultado.itens,
                "limpo": resultado.limpo,
                "valor_total": resultado.valor_total,
            }
        return {"veiculo": descrever_veiculo(veiculo), "consultas": consultas}

    def alterar_endereco(
        self, unidade_federativa: str, placa: str, cidadao: Cidadao, novo_endereco: Endereco
    ) -> ResultadoOperacao:
        self.obter_veiculo_do_cidadao(unidade_federativa, placa, cidadao)
        with self._trava_alteracoes:
            return AlteracaoEnderecoCreator(unidade_federativa).processar(placa, {"novo_endereco": novo_endereco})

    def emitir_crlve(self, unidade_federativa: str, placa: str, cidadao: Cidadao, exercicio: int) -> ResultadoOperacao:
        self.obter_veiculo_do_cidadao(unidade_federativa, placa, cidadao)
        return EmissaoCRLVeCreator(unidade_federativa).processar(placa, {"exercicio": exercicio})

    def verificar_elegibilidade_tei(
        self, unidade_federativa: str, placa: str, vendedor: Cidadao, cpf_comprador: str
    ) -> ResultadoOperacao:
        self.obter_veiculo_do_cidadao(unidade_federativa, placa, vendedor)
        comprador = self._repositorio_cidadaos.buscar_por_cpf(cpf_comprador)
        return VerificacaoElegibilidadeTEICreator(unidade_federativa).processar(
            placa, {"vendedor": vendedor, "comprador": comprador}
        )

    def listar_transferencias_concluidas(self, cidadao: Cidadao) -> list[dict]:
        transferencias_do_cidadao = []
        for unidade_federativa in UNIDADES_FEDERATIVAS_DISPONIVEIS:
            for transferencia in BaseDetranMultiton.obter_instancia(unidade_federativa).listar_transferencias():
                participa = cidadao.cpf in (transferencia.cpf_vendedor, transferencia.cpf_comprador)
                if participa and transferencia.situacao == SituacaoTransferencia.CONCLUIDA:
                    transferencias_do_cidadao.append(
                        {
                            "placa": transferencia.placa,
                            "marca_modelo": transferencia.marca_modelo,
                            "data": transferencia.data.strftime("%d/%m/%Y"),
                            "papel": "Vendedor" if transferencia.cpf_vendedor == cidadao.cpf else "Comprador",
                            "unidade_federativa": unidade_federativa,
                        }
                    )
        return transferencias_do_cidadao

    @staticmethod
    def descrever_estado_prototipo(cidadao: Cidadao) -> dict:
        placas_do_cidadao = {
            veiculo.placa
            for unidade_federativa in UNIDADES_FEDERATIVAS_DISPONIVEIS
            for veiculo in BaseDetranMultiton.obter_instancia(unidade_federativa).listar_veiculos()
            if veiculo.cpf_proprietario == cidadao.cpf
        }
        documentos = [
            documento.para_dicionario()
            for documento in registro_documentos_emitidos.listar()
            if documento.para_dicionario()["placa"] in placas_do_cidadao
        ]
        identificadores = [documento["identificador_objeto"] for documento in documentos]
        prototipo = PROTOTIPO_CRLVE.para_dicionario()
        return {
            "prototipo": prototipo,
            "documentos": documentos,
            "prototipo_permanece_vazio": prototipo["placa"] is None,
            "todos_independentes": len(set(identificadores)) == len(identificadores)
            and prototipo["identificador_objeto"] not in identificadores,
        }
