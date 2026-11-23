class ErroDeNegocio(Exception):
    pass


class RecursoNaoEncontrado(ErroDeNegocio):
    pass


class EntradaInvalida(ErroDeNegocio):
    pass


class SessaoNaoAutenticada(ErroDeNegocio):
    pass


class AcessoNegado(ErroDeNegocio):
    pass


class OperacaoNaoPermitida(ErroDeNegocio):
    pass


class ErroIntegracao(ErroDeNegocio):
    pass
