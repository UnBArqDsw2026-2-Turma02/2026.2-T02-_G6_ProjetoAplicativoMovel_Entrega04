from datetime import date, timedelta

from aplicativo.dominio.modelos import (
    Cidadao,
    Debito,
    DocumentoTransferencia,
    Endereco,
    Restricao,
    SituacaoTransferencia,
    TipoRestricao,
    Transferencia,
    Veiculo,
    Vistoria,
)

CPF_CIDADAO_DEMONSTRACAO = "12345678901"
CPF_COMPRADOR_HABILITADO = "98765432109"
CPF_COMPRADOR_SEM_BIOMETRIA = "11122233344"
NOME_CIDADAO_DEMONSTRACAO = "Ana Beatriz Moreira"


def criar_cidadaos() -> list[Cidadao]:
    return [
        Cidadao(
            cpf=CPF_CIDADAO_DEMONSTRACAO,
            nome=NOME_CIDADAO_DEMONSTRACAO,
            email="ana.moreira@exemplo.com",
            numero_cnh="04512345678",
            codigo_seguranca_cnh="98765",
        ),
        Cidadao(cpf=CPF_COMPRADOR_HABILITADO, nome="Carlos Eduardo Lima", email="carlos.lima@exemplo.com"),
        Cidadao(
            cpf=CPF_COMPRADOR_SEM_BIOMETRIA,
            nome="Bruno Costa",
            email="bruno.costa@exemplo.com",
            biometria_valida=False,
        ),
    ]


def criar_veiculos(unidade_federativa: str) -> list[Veiculo]:
    hoje = date.today()
    veiculos_por_unidade_federativa = {
        "DF": [
            Veiculo(
                placa="JKA1234",
                renavam="11111111111",
                marca_modelo="Fiat Argo Drive 1.0",
                ano_modelo=2022,
                cor="Branco",
                cpf_proprietario=CPF_CIDADAO_DEMONSTRACAO,
                nome_proprietario=NOME_CIDADAO_DEMONSTRACAO,
                endereco=Endereco("DF", "70000-000", "SQS 308 Bloco A"),
                numero_seguranca_crv="54321",
                vistoria=Vistoria("ECV Asa Sul", hoje - timedelta(days=30)),
            ),
            Veiculo(
                placa="ABC1D23",
                renavam="98765432100",
                marca_modelo="Volkswagen Gol 1.6",
                ano_modelo=2019,
                cor="Prata",
                cpf_proprietario=CPF_CIDADAO_DEMONSTRACAO,
                nome_proprietario=NOME_CIDADAO_DEMONSTRACAO,
                endereco=Endereco("DF", "70100-000", "CLN 204 Bloco B"),
                numero_seguranca_crv="11223",
                debitos=[Debito("IPVA 2026", 1250.00), Debito("Multa de trânsito", 195.23)],
                restricoes=[Restricao("Restrição judicial (RENAJUD)", TipoRestricao.JUDICIAL)],
            ),
            Veiculo(
                placa="XYZ9A87",
                renavam="55555555555",
                marca_modelo="Chevrolet Onix 1.0",
                ano_modelo=2023,
                cor="Preto",
                cpf_proprietario=CPF_CIDADAO_DEMONSTRACAO,
                nome_proprietario=NOME_CIDADAO_DEMONSTRACAO,
                endereco=Endereco("DF", "70200-000", "QI 15 Lago Sul"),
                numero_seguranca_crv="44556",
                financiamentos=["Alienação fiduciária - Banco Demonstração S.A."],
            ),
            Veiculo(
                placa="QWE2B45",
                renavam="33333333333",
                marca_modelo="Hyundai HB20 1.0",
                ano_modelo=2021,
                cor="Vermelho",
                cpf_proprietario=CPF_CIDADAO_DEMONSTRACAO,
                nome_proprietario=NOME_CIDADAO_DEMONSTRACAO,
                endereco=Endereco("DF", "71900-000", "Rua 12 Norte, Águas Claras"),
                numero_seguranca_crv="77889",
                debitos=[Debito("IPVA 2027 - 1ª parcela", 480.50, vencido=False)],
                vistoria=Vistoria("ECV Taguatinga", hoje - timedelta(days=150)),
            ),
            Veiculo(
                placa="LMN7O89",
                renavam="66666666666",
                marca_modelo="Honda Fit 1.5",
                ano_modelo=2018,
                cor="Azul",
                cpf_proprietario=CPF_CIDADAO_DEMONSTRACAO,
                nome_proprietario=NOME_CIDADAO_DEMONSTRACAO,
                endereco=Endereco("DF", "72000-000", "QNM 40, Ceilândia"),
                numero_seguranca_crv="99001",
                documento_transferencia=DocumentoTransferencia.DUT,
                licenciamento_em_dia=False,
            ),
            Veiculo(
                placa="RST5U67",
                renavam="77777777777",
                marca_modelo="Renault Sandero 1.6",
                ano_modelo=2020,
                cor="Branco",
                cpf_proprietario=CPF_COMPRADOR_HABILITADO,
                nome_proprietario="Carlos Eduardo Lima",
                endereco=Endereco("DF", "70300-000", "SHN Quadra 1"),
                numero_seguranca_crv="31313",
            ),
        ],
        "GO": [
            Veiculo(
                placa="GOA1B23",
                renavam="22222222222",
                marca_modelo="Toyota Corolla 2.0",
                ano_modelo=2020,
                cor="Cinza",
                cpf_proprietario=CPF_CIDADAO_DEMONSTRACAO,
                nome_proprietario=NOME_CIDADAO_DEMONSTRACAO,
                endereco=Endereco("GO", "74000-000", "Setor Bueno, Goiânia"),
                numero_seguranca_crv="12121",
            ),
        ],
    }
    return veiculos_por_unidade_federativa.get(unidade_federativa, [])


def criar_transferencias(unidade_federativa: str) -> list[Transferencia]:
    if unidade_federativa != "DF":
        return []
    return [
        Transferencia(
            placa="PQR4S56",
            marca_modelo="Renault Kwid 1.0",
            cpf_vendedor=CPF_CIDADAO_DEMONSTRACAO,
            cpf_comprador=CPF_COMPRADOR_HABILITADO,
            data=date(2026, 3, 14),
            situacao=SituacaoTransferencia.CONCLUIDA,
        ),
        Transferencia(
            placa="XYZ9A87",
            marca_modelo="Chevrolet Onix 1.0",
            cpf_vendedor=CPF_COMPRADOR_HABILITADO,
            cpf_comprador=CPF_CIDADAO_DEMONSTRACAO,
            data=date(2025, 8, 2),
            situacao=SituacaoTransferencia.CONCLUIDA,
        ),
        Transferencia(
            placa="STU1V23",
            marca_modelo="Fiat Mobi 1.0",
            cpf_vendedor=CPF_CIDADAO_DEMONSTRACAO,
            cpf_comprador=CPF_COMPRADOR_SEM_BIOMETRIA,
            data=date(2026, 11, 1),
            situacao=SituacaoTransferencia.EM_ANDAMENTO,
        ),
    ]


def criar_autos_de_infracao() -> list[dict]:
    hoje = date.today()
    return [
        {
            "auto": "INF-001",
            "doc_condutor": CPF_CIDADAO_DEMONSTRACAO,
            "placa_veic": "ABC1D23",
            "desc": "Transitar em velocidade superior à máxima permitida em até 20%",
            "enq": "745-50",
            "loc": "EPTG, km 10, sentido Taguatinga",
            "dt_infr": (hoje - timedelta(days=20)).isoformat(),
            "dt_venc": (hoje + timedelta(days=25)).isoformat(),
            "vlr": "130.16",
            "sit": "AV",
            "org_id": "ORG-001",
            "org_nome": "Órgão Autuador Distrital",
            "org_sne": "S",
            "org_cdt": "S",
            "pct_beneficio": "0",
        },
        {
            "auto": "INF-002",
            "doc_condutor": CPF_CIDADAO_DEMONSTRACAO,
            "placa_veic": "ABC1D23",
            "desc": "Estacionar em local proibido pela sinalização",
            "enq": "554-10",
            "loc": "SCS Quadra 2",
            "dt_infr": (hoje - timedelta(days=90)).isoformat(),
            "dt_venc": (hoje - timedelta(days=30)).isoformat(),
            "vlr": "195.23",
            "sit": "VE",
            "org_id": "ORG-002",
            "org_nome": "Órgão Autuador Municipal B",
            "org_sne": "N",
            "org_cdt": "S",
            "pct_beneficio": "0",
        },
        {
            "auto": "INF-003",
            "doc_condutor": CPF_CIDADAO_DEMONSTRACAO,
            "placa_veic": "QWE2B45",
            "desc": "Avançar o sinal vermelho do semáforo",
            "enq": "605-01",
            "loc": "Avenida Hélio Prates, Taguatinga",
            "dt_infr": (hoje - timedelta(days=12)).isoformat(),
            "dt_venc": (hoje + timedelta(days=40)).isoformat(),
            "vlr": "293.47",
            "sit": "AV",
            "org_id": "ORG-003",
            "org_nome": "Órgão Autuador Rodoviário C",
            "org_sne": "N",
            "org_cdt": "S",
            "pct_beneficio": "0",
        },
        {
            "auto": "INF-004",
            "doc_condutor": CPF_CIDADAO_DEMONSTRACAO,
            "placa_veic": "JKA1234",
            "desc": "Deixar de usar o cinto de segurança",
            "enq": "518-51",
            "loc": "Eixo Monumental",
            "dt_infr": (hoje - timedelta(days=200)).isoformat(),
            "dt_venc": (hoje - timedelta(days=140)).isoformat(),
            "vlr": "195.23",
            "sit": "PG",
            "org_id": "ORG-001",
            "org_nome": "Órgão Autuador Distrital",
            "org_sne": "S",
            "org_cdt": "S",
            "pct_beneficio": "0",
        },
        {
            "auto": "INF-005",
            "doc_condutor": CPF_CIDADAO_DEMONSTRACAO,
            "placa_veic": "XYZ9A87",
            "desc": "Conduzir o veículo com o licenciamento vencido",
            "enq": "659-92",
            "loc": "Rodovia de demonstração, km 32",
            "dt_infr": (hoje - timedelta(days=5)).isoformat(),
            "dt_venc": (hoje + timedelta(days=55)).isoformat(),
            "vlr": "293.47",
            "sit": "AV",
            "org_id": "ORG-004",
            "org_nome": "Órgão Autuador Municipal D",
            "org_sne": "N",
            "org_cdt": "N",
            "pct_beneficio": "0",
        },
    ]
