from abc import ABC, abstractmethod

from aplicativo.dominio.modelos import ResultadoConsulta, Veiculo


def formatar_valor(valor: float) -> str:
    valor_formatado = f"{valor:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return f"R$ {valor_formatado}"


class Consulta(ABC):
    @abstractmethod
    def executar(self, veiculo: Veiculo) -> ResultadoConsulta: ...


class ConsultaDebitos(Consulta):
    def executar(self, veiculo: Veiculo) -> ResultadoConsulta:
        itens = [
            f"{debito.descricao}: {formatar_valor(debito.valor)}{' (vencido)' if debito.vencido else ' (a vencer)'}"
            for debito in veiculo.debitos
        ]
        return ResultadoConsulta("Débitos", itens, veiculo.valor_total_debitos)


class ConsultaRestricoes(Consulta):
    def executar(self, veiculo: Veiculo) -> ResultadoConsulta:
        return ResultadoConsulta("Restrições", [restricao.descricao for restricao in veiculo.restricoes])


class ConsultaFinanciamentos(Consulta):
    def executar(self, veiculo: Veiculo) -> ResultadoConsulta:
        return ResultadoConsulta("Financiamentos", list(veiculo.financiamentos))


class ConsultaPendenciasImpeditivas(Consulta):
    def executar(self, veiculo: Veiculo) -> ResultadoConsulta:
        pendencias = [f"Débito vencido: {debito.descricao}" for debito in veiculo.debitos_vencidos]
        pendencias += [f"Restrição: {restricao.descricao}" for restricao in veiculo.restricoes]
        if not veiculo.licenciamento_em_dia:
            pendencias.append("Licenciamento do exercício não quitado")
        valor_vencido = round(sum(debito.valor for debito in veiculo.debitos_vencidos), 2)
        return ResultadoConsulta("Nada Consta", pendencias, valor_vencido)


class ConsultaCreator(ABC):
    @abstractmethod
    def criar_consulta(self) -> Consulta: ...

    def consultar(self, veiculo: Veiculo) -> ResultadoConsulta:
        consulta = self.criar_consulta()
        return consulta.executar(veiculo)


class DebitosCreator(ConsultaCreator):
    def criar_consulta(self) -> Consulta:
        return ConsultaDebitos()


class RestricoesCreator(ConsultaCreator):
    def criar_consulta(self) -> Consulta:
        return ConsultaRestricoes()


class FinanciamentosCreator(ConsultaCreator):
    def criar_consulta(self) -> Consulta:
        return ConsultaFinanciamentos()


class NadaConstaCreator(ConsultaCreator):
    def criar_consulta(self) -> Consulta:
        return ConsultaPendenciasImpeditivas()


CRIADORES_DE_CONSULTA: dict[str, type[ConsultaCreator]] = {
    "debitos": DebitosCreator,
    "restricoes": RestricoesCreator,
    "financiamentos": FinanciamentosCreator,
    "nada_consta": NadaConstaCreator,
}
