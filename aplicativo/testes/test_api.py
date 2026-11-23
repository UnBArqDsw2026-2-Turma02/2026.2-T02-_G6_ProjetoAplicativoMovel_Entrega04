import pytest
from fastapi.testclient import TestClient

from aplicativo.principal import criar_aplicacao

CPF_COMPRADOR_HABILITADO = "987.654.321-09"


@pytest.fixture
def cliente_anonimo() -> TestClient:
    return TestClient(criar_aplicacao())


@pytest.fixture
def cliente(cliente_anonimo: TestClient) -> TestClient:
    cliente_anonimo.post("/entrar/gov")
    return cliente_anonimo


def test_login_gov_redireciona_para_inicio(cliente_anonimo: TestClient) -> None:
    resposta = cliente_anonimo.post("/entrar/gov", follow_redirects=False)
    assert resposta.status_code == 303
    assert resposta.headers["location"] == "/inicio"
    token_sessao = resposta.cookies["sessao_cidadao"]
    assert len(token_sessao) >= 32
    assert "12345678901" not in token_sessao


def test_sem_sessao_paginas_redirecionam_e_api_retorna_401(cliente_anonimo: TestClient) -> None:
    pagina = cliente_anonimo.get("/inicio", follow_redirects=False)
    assert pagina.status_code == 303
    assert pagina.headers["location"] == "/"
    assert cliente_anonimo.get("/api/v1/cidadao/infracoes").status_code == 401
    assert cliente_anonimo.put("/api/v1/ufs/DF/veiculos/JKA1234/endereco", json={}).status_code in (401, 422)


def test_cookie_forjado_com_cpf_nao_autentica(cliente_anonimo: TestClient) -> None:
    cliente_anonimo.cookies.set("sessao_cidadao", "98765432109")
    assert cliente_anonimo.get("/api/v1/cidadao").status_code == 401


def test_sair_encerra_a_sessao(cliente: TestClient) -> None:
    assert cliente.get("/api/v1/cidadao").status_code == 200
    cliente.post("/sair")
    assert cliente.get("/api/v1/cidadao").status_code == 401
    assert cliente.get("/inicio", follow_redirects=False).status_code == 303


def test_veiculo_de_outro_proprietario_retorna_403(cliente: TestClient) -> None:
    assert cliente.get("/api/v1/ufs/DF/veiculos/RST5U67").status_code == 403
    assert cliente.post("/api/v1/ufs/DF/veiculos/RST5U67/crlve", json={"exercicio": 2026}).status_code == 403
    placas_listadas = {veiculo["placa"] for veiculo in cliente.get("/api/v1/ufs/DF/veiculos").json()["veiculos"]}
    assert "RST5U67" not in placas_listadas


def test_crlve_de_exercicio_futuro_e_rejeitado(cliente: TestClient) -> None:
    resposta = cliente.post("/api/v1/ufs/DF/veiculos/JKA1234/crlve", json={"exercicio": 2099})
    assert resposta.status_code == 422


def test_desconto_aplicado_nao_pode_ser_trocado(cliente: TestClient) -> None:
    primeiro = cliente.post("/api/v1/cidadao/infracoes/INF-003/descontos", json={"percentual": 20})
    assert primeiro.status_code == 200
    repetido = cliente.post("/api/v1/cidadao/infracoes/INF-003/descontos", json={"percentual": 20})
    assert repetido.status_code == 422
    resumo = cliente.get("/api/v1/cidadao/infracoes").json()["resumo"]
    assert resumo["quantidade_com_desconto_disponivel"] == 1


def test_paginas_principais_carregam(cliente: TestClient) -> None:
    for caminho in [
        "/",
        "/inicio",
        "/inicio?uf=GO",
        "/veiculos/DF/JKA1234",
        "/veiculos/DF/JKA1234/crlve",
        "/veiculos/DF/JKA1234/endereco",
        "/veiculos/DF/JKA1234/transferencia",
        "/transferencias",
        "/infracoes",
        "/infracoes/INF-001",
        "/sne",
        "/habilitacao",
    ]:
        assert cliente.get(caminho).status_code == 200, caminho


def test_swagger_e_pagina_de_arquitetura_foram_removidos(cliente: TestClient) -> None:
    for caminho in ["/docs", "/redoc", "/openapi.json", "/arquitetura"]:
        assert cliente.get(caminho).status_code == 404, caminho


def test_boleto_e_gerado_uma_vez_e_acompanha_o_desconto(cliente: TestClient) -> None:
    assert cliente.get("/infracoes/INF-001/boleto").status_code == 404
    primeiro = cliente.post("/api/v1/cidadao/infracoes/INF-001/boleto")
    assert primeiro.status_code == 200
    boleto = primeiro.json()["dados"]["boleto"]
    assert boleto["valor_a_pagar"] == 130.16
    repetido = cliente.post("/api/v1/cidadao/infracoes/INF-001/boleto").json()["dados"]["boleto"]
    assert repetido["identificador"] == boleto["identificador"]
    cliente.post("/api/v1/cidadao/infracoes/INF-001/descontos", json={"percentual": 20})
    boleto_atualizado = cliente.get("/api/v1/cidadao/infracoes/INF-001").json()["boleto"]
    assert boleto_atualizado["percentual_desconto"] == 20
    assert boleto_atualizado["valor_a_pagar"] == 104.13
    assert cliente.get("/infracoes/INF-001/boleto").status_code == 200


def test_boleto_de_infracao_paga_e_recusado(cliente: TestClient) -> None:
    assert cliente.post("/api/v1/cidadao/infracoes/INF-004/boleto").status_code == 422


def test_indicacao_de_condutor_gera_protocolo_unico(cliente: TestClient) -> None:
    corpo = {"cpf_condutor": CPF_COMPRADOR_HABILITADO, "numero_cnh_condutor": "11122233344", "declaracao_aceita": True}
    resposta = cliente.post("/api/v1/cidadao/infracoes/INF-001/indicacao-condutor", json=corpo)
    assert resposta.status_code == 200
    assert resposta.json()["dados"]["indicacao"]["protocolo"].startswith("IND-")
    assert cliente.post("/api/v1/cidadao/infracoes/INF-001/indicacao-condutor", json=corpo).status_code == 422
    proprio_cpf = {**corpo, "cpf_condutor": "123.456.789-01"}
    assert cliente.post("/api/v1/cidadao/infracoes/INF-003/indicacao-condutor", json=proprio_cpf).status_code == 422
    sem_declaracao = {**corpo, "declaracao_aceita": False}
    assert cliente.post("/api/v1/cidadao/infracoes/INF-003/indicacao-condutor", json=sem_declaracao).status_code == 422


def test_ppd_sem_impedimento_vira_definitiva_e_avisa_observadores(cliente: TestClient) -> None:
    habilitacao = cliente.get("/api/v1/cidadao/habilitacao").json()
    assert habilitacao["situacao"] == "PPD Ativa"
    assert habilitacao["notificacoes"] == []
    resposta = cliente.post("/api/v1/cidadao/habilitacao/conclusao-ppd")
    assert resposta.json()["dados"]["situacao"] == "Definitiva"
    habilitacao = cliente.get("/api/v1/cidadao/habilitacao").json()
    assert {notificacao["canal"] for notificacao in habilitacao["notificacoes"]} == {"Push", "E-mail"}
    assert len(habilitacao["auditoria"]) == 1
    assert cliente.post("/api/v1/cidadao/habilitacao/conclusao-ppd").status_code == 409


def test_ppd_com_infracao_grave_e_cassada_e_bloqueia_categoria(cliente: TestClient) -> None:
    cliente.post("/api/v1/cidadao/habilitacao/infracoes", json={"gravidade": "grave"})
    assert cliente.post("/api/v1/cidadao/habilitacao/conclusao-ppd").json()["dados"]["situacao"] == "Cassada"
    assert cliente.post("/api/v1/cidadao/habilitacao/infracoes", json={"gravidade": "leve"}).status_code == 409
    solicitacao = cliente.post("/api/v1/cidadao/habilitacao/alteracoes-categoria", json={"categoria_desejada": "AB"})
    assert solicitacao.json()["dados"]["solicitacao"]["resultado"] == "recusada"
    assert cliente.post("/api/v1/cidadao/habilitacao/reinicio").status_code == 200
    assert cliente.get("/api/v1/cidadao/habilitacao").json()["situacao"] == "PPD Ativa"


def test_cadeia_de_alteracao_de_categoria(cliente: TestClient) -> None:
    resultados = {
        categoria: cliente.post(
            "/api/v1/cidadao/habilitacao/alteracoes-categoria", json={"categoria_desejada": categoria}
        ).json()["dados"]["solicitacao"]["resultado"]
        for categoria in ["AB", "C", "A"]
    }
    assert resultados == {"AB": "aceita", "C": "encaminhada_ao_detran", "A": "recusada"}
    invalida = cliente.post("/api/v1/cidadao/habilitacao/alteracoes-categoria", json={"categoria_desejada": "Z"})
    assert invalida.status_code == 422


def test_veiculo_inexistente_retorna_404(cliente: TestClient) -> None:
    assert cliente.get("/api/v1/ufs/DF/veiculos/AAA0000").status_code == 404
    assert cliente.get("/veiculos/DF/AAA0000").status_code == 404
    assert cliente.get("/api/v1/ufs/SP/veiculos").status_code == 404


def test_multiton_mantem_uma_base_por_uf(cliente: TestClient) -> None:
    base_df = cliente.get("/api/v1/ufs/DF/veiculos").json()
    base_df_novamente = cliente.get("/api/v1/ufs/df/veiculos").json()
    base_go = cliente.get("/api/v1/ufs/GO/veiculos").json()
    assert base_df["identificador_base"] == base_df_novamente["identificador_base"]
    assert base_df["identificador_base"] != base_go["identificador_base"]


def test_emissao_crlve_gera_clones_independentes(cliente: TestClient) -> None:
    primeira = cliente.post("/api/v1/ufs/DF/veiculos/JKA1234/crlve", json={"exercicio": 2026})
    segunda = cliente.post("/api/v1/ufs/DF/veiculos/QWE2B45/crlve", json={"exercicio": 2026})
    assert primeira.status_code == 201
    assert segunda.status_code == 201
    estado = cliente.get("/api/v1/documentos/crlve/prototipo").json()
    assert len(estado["documentos"]) == 2
    assert estado["prototipo_permanece_vazio"]
    assert estado["todos_independentes"]


def test_emissao_crlve_bloqueada_com_pendencias(cliente: TestClient) -> None:
    resposta = cliente.post("/api/v1/ufs/DF/veiculos/ABC1D23/crlve", json={"exercicio": 2026})
    assert resposta.status_code == 422
    assert resposta.json()["dados"]["pendencias"]


def test_alteracao_de_endereco(cliente: TestClient) -> None:
    corpo = {"uf": "df", "cep": "70.000-100", "logradouro": "SQN 210 Bloco C", "caixa_postal": False}
    resposta = cliente.put("/api/v1/ufs/DF/veiculos/JKA1234/endereco", json=corpo)
    assert resposta.status_code == 200
    assert resposta.json()["dados"]["endereco"]["cep"] == "70000-100"
    bloqueada = cliente.put("/api/v1/ufs/DF/veiculos/ABC1D23/endereco", json=corpo)
    assert bloqueada.status_code == 422
    fora_do_df = cliente.put("/api/v1/ufs/DF/veiculos/JKA1234/endereco", json={**corpo, "uf": "GO"})
    assert fora_do_df.status_code == 422


def test_elegibilidade_tei_por_cenario(cliente: TestClient) -> None:
    def verificar(placa: str, uf: str = "DF", cpf: str = CPF_COMPRADOR_HABILITADO) -> dict:
        resposta = cliente.post(f"/api/v1/ufs/{uf}/veiculos/{placa}/elegibilidade-tei", json={"cpf_comprador": cpf})
        assert resposta.status_code == 200
        return resposta.json()["dados"]

    assert verificar("JKA1234")["proximo_passo"] == "execucao_tei"
    assert verificar("QWE2B45")["proximo_passo"] == "providenciar_vistoria"
    assert verificar("XYZ9A87")["proximo_passo"] == "procedimento_tradicional"
    assert verificar("LMN7O89")["proximo_passo"] == "procedimento_tradicional"
    assert verificar("GOA1B23", uf="GO")["proximo_passo"] == "procedimento_tradicional"
    assert verificar("JKA1234", cpf="11122233344")["proximo_passo"] == "procedimento_tradicional"


def test_cpf_invalido_retorna_mensagem_amigavel(cliente: TestClient) -> None:
    resposta = cliente.post("/api/v1/ufs/DF/veiculos/JKA1234/elegibilidade-tei", json={"cpf_comprador": "123"})
    assert resposta.status_code == 422
    assert "cpf_comprador" in resposta.json()["erro"]


def test_transferencias_mostram_apenas_concluidas(cliente: TestClient) -> None:
    transferencias = cliente.get("/api/v1/cidadao/transferencias").json()
    assert {transferencia["placa"] for transferencia in transferencias} == {"PQR4S56", "XYZ9A87"}


def test_desconto_de_40_exige_sne_e_termo(cliente: TestClient) -> None:
    sem_sne = cliente.post("/api/v1/cidadao/infracoes/INF-001/descontos", json={"percentual": 40, "termo_aceito": True})
    assert sem_sne.status_code == 422

    adesao = cliente.post(
        "/api/v1/cidadao/sne/adesao",
        json={"tipo_documento": "cnh", "numero_cnh": "04512345678", "codigo_seguranca_cnh": "98765"},
    )
    assert adesao.status_code == 200

    sem_termo = cliente.post(
        "/api/v1/cidadao/infracoes/INF-001/descontos", json={"percentual": 40, "termo_aceito": False}
    )
    assert sem_termo.status_code == 422

    aplicado = cliente.post(
        "/api/v1/cidadao/infracoes/INF-001/descontos", json={"percentual": 40, "termo_aceito": True}
    )
    assert aplicado.status_code == 200
    assert aplicado.json()["dados"]["infracao"]["valor_a_pagar"] == 78.10


def test_politicas_de_desconto_por_orgao(cliente: TestClient) -> None:
    infracoes = {
        infracao["identificador"]: infracao for infracao in cliente.get("/api/v1/cidadao/infracoes").json()["infracoes"]
    }
    percentuais = {
        identificador: [opcao["percentual"] for opcao in infracao["opcoes_desconto"]]
        for identificador, infracao in infracoes.items()
    }
    assert percentuais == {"INF-001": [20, 40], "INF-002": [], "INF-003": [20], "INF-004": [], "INF-005": []}


def test_adesao_sne_por_crlv_valida_documento(cliente: TestClient) -> None:
    invalida = cliente.post(
        "/api/v1/cidadao/sne/adesao",
        json={"tipo_documento": "crlv", "placa": "JKA1234", "renavam": "11111111111", "numero_seguranca_crv": "00000"},
    )
    assert invalida.status_code == 422
    valida = cliente.post(
        "/api/v1/cidadao/sne/adesao",
        json={"tipo_documento": "crlv", "placa": "JKA1234", "renavam": "11111111111", "numero_seguranca_crv": "54321"},
    )
    assert valida.status_code == 200
    assert cliente.get("/api/v1/cidadao/sne").json()["aderiu"]
