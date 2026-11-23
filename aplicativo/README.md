# Dirigindo Meu Carro - MVP da Entrega 04

Evolução do [MVP da Entrega 03](https://unbarqdsw2026-2-turma02.github.io/2026.2-T02-_G6_ProjetoAplicativoMovel_Entrega03/#/Base/Relatorios/SubEquipe_01/Projeto_Geral/1.1.1.ProjetoGeral), agora em **FastAPI**, com front-end em **Tailwind CSS** e **Alpine.js**, e com o código organizado pelas camadas da [Representação Arquitetural do DAS](../docs/Base/Relatorios/1.1.1.DAS.md) e pelos padrões de projeto.

Todos os dados são simulados. O login gov.br é um mock: o botão autentica um cidadão de demonstração e abre a tela inicial, sem solicitar nenhum dado.

A relação do código com o DAS (camadas, casos de uso e padrões) está na página [1.1.3. Aplicativo (MVP)](../docs/Base/Relatorios/1.1.3.AplicativoMVP.md) do GitPages.

## Como executar

As telas carregam Tailwind CSS e Alpine.js por CDN, então o navegador precisa estar conectado à internet.

### Opção 1: um clique (recomendado)

Requisito: [Python 3.10 ou superior](https://www.python.org/downloads/).

| Sistema | O que fazer |
|--|--|
| Windows | Dois cliques em `executar.bat`, na raiz do repositório |
| Linux ou macOS | `./executar.sh` no terminal, na raiz do repositório |

O script cria o ambiente virtual `.venv`, instala as dependências e abre o navegador em <http://127.0.0.1:8000>. Para usar outra porta: `executar.bat 8001` ou `./executar.sh 8001`.

### Opção 2: Docker

Requisito: [Docker Desktop](https://www.docker.com/products/docker-desktop/) aberto.

```bash
docker compose up --build
```

| Serviço | Endereço | O que é |
|--|--|--|
| `aplicativo` | <http://127.0.0.1:8000> | MVP em FastAPI |
| `documentacao` | <http://127.0.0.1:3000> | GitPages (Docsify) servido por Nginx |

Para encerrar: `Ctrl+C` e depois `docker compose down`. Para subir apenas o app: `docker compose up --build aplicativo`.

### Opção 3: Python manual

Requisito: Python 3.10 ou superior. Execute a partir da **raiz do repositório**:

```bash
pip install -r aplicativo/requirements.txt
python -m aplicativo
```

Depois, abra <http://127.0.0.1:8000>. Para usar outra porta: `python -m aplicativo 8001`.

### Variáveis de ambiente

| Variável | Padrão | Uso |
|--|--|--|
| `ENDERECO_SERVIDOR` | `127.0.0.1` (no Docker: `0.0.0.0`) | Interface em que o servidor escuta |
| `PORTA_SERVIDOR` | `8000` | Porta do servidor |
| `ABRIR_NAVEGADOR` | `1` (no Docker: `0`) | Abre o navegador automaticamente ao iniciar |

### Testes e padrões de código

```bash
pip install -r aplicativo/requirements-dev.txt
python -m pytest aplicativo/testes
python -m ruff check aplicativo
```

O código segue a PEP 8 (verificada pelo Ruff, com linha de até 120 caracteres), usa nomes descritivos em português e anotações de tipo em todas as funções.

## Estrutura

```
aplicativo/
├── principal.py              criação da aplicação FastAPI e tratamento de erros
├── configuracao.py           caminhos, nome do app e constantes
├── apresentacao/             rotas de páginas, API REST, esquemas, templates e JS
├── aplicacao/                serviços de veículos e de habilitação e contêiner de dependências
├── dominio/                  entidades, exceções e dados de demonstração
├── infraestrutura/           mocks do gov.br, do órgão autuador, de boletos, do protocolo de indicação e do SNE
└── padroes/
    ├── multiton/             BaseDetranMultiton (uma base por UF)
    ├── factory_method/       Creators de consultas e de serviços
    ├── prototype/            CRLVe clonado a partir do modelo-base
    ├── adapter/              gov.br, órgão autuador, boletos e protocolo de indicação de condutor
    ├── strategy/             políticas de desconto e validação de documento do SNE
    ├── facade/               InfracoesFacade e SneFacade
    ├── state/                situações da habilitação: PPD Ativa, Definitiva e Cassada
    ├── observer/             avisos por push, e-mail e auditoria quando a situação muda
    └── chain_of_responsibility/  validadores da mudança de categoria
```

### Front-end reutilizável

| Arquivo | Conteúdo |
|--|--|
| `templates/componentes/_cabeca.html` | Fontes, Tailwind e as classes do tema (`cartao`, `botao-primario`, `botao-destaque`, `campo`, `selo-*`) |
| `templates/componentes/_macros.html` | Macros Jinja disponíveis em todas as telas como `ui.*`: cabeçalho, indicador, atalho, placa, campo, botão de envio, dica e estado vazio |
| `estaticos/app.js` | `chamarApi`, `comEnvio` (envio com aviso de sucesso ou erro, reaproveitado por todos os formulários) e um componente Alpine por tela |

Paleta: azul como cor principal, amarelo para destaques e verde para sucesso. Os cartões têm cantos pouco arredondados, sombra e crescem ao passar o mouse.

## Funcionalidades

| Tela | Caso de uso | Padrões |
|--|--|--|
| Login gov.br (simulado) | Autenticação | Adapter |
| Início | Escolha da UF e dos veículos | Multiton |
| Consultas do veículo | UC01 - débitos, restrições, financiamentos e nada consta | Factory Method |
| CRLV-e | UC02 - emissão com bloqueio por pendências e prova dos clones | Factory Method + Prototype |
| Endereço | UC03 - alteração com as regras do DF | Factory Method + Multiton |
| Transferência | UC04/UC07 - elegibilidade para a TEI, com vistoria de 90 dias | Factory Method |
| Transferências | UC06 - histórico apenas de transferências concluídas | Multiton |
| Infrações | Consulta, detalhes e descontos de 20% e 40% | Facade + Adapter + Strategy |
| Boleto da infração | Geração, atualização com desconto, copiar código, imprimir/salvar PDF e compartilhar | Facade + Adapter |
| Indicação de condutor | Protocolo do condutor responsável pela infração | Adapter |
| Habilitação | Período da PPD, avisos de mudança de situação e mudança de categoria | State + Observer + Chain of Responsibility |
| SNE | Adesão validada por CNH ou CRLV | Facade + Strategy |

A execução da TEI (UC05) **não** foi implementada: a ordem entre aceite, pagamento e efetivação continua sendo uma lacuna do levantamento (Entrega 02).

## API REST (`/api/v1`)

| Método | Rota | Descrição |
|--|--|--|
| GET | `/ufs` | UFs disponíveis |
| GET | `/ufs/{uf}/veiculos` | Veículos da base da UF |
| GET | `/ufs/{uf}/veiculos/{placa}` | Situação do veículo (UC01) |
| PUT | `/ufs/{uf}/veiculos/{placa}/endereco` | Alteração de endereço (UC03) |
| POST | `/ufs/{uf}/veiculos/{placa}/crlve` | Emissão do CRLV-e (UC02) |
| POST | `/ufs/{uf}/veiculos/{placa}/elegibilidade-tei` | Elegibilidade para a TEI (UC04/UC07) |
| GET | `/documentos/crlve/prototipo` | Estado do protótipo e dos clones |
| GET | `/cidadao` | Cidadão autenticado |
| GET | `/cidadao/transferencias` | Transferências concluídas (UC06) |
| GET | `/cidadao/infracoes` | Infrações e resumo |
| GET | `/cidadao/infracoes/{id}` | Detalhe da infração |
| POST | `/cidadao/infracoes/{id}/descontos` | Solicitação de desconto |
| POST | `/cidadao/infracoes/{id}/boleto` | Geração do boleto |
| POST | `/cidadao/infracoes/{id}/indicacao-condutor` | Indicação do condutor |
| GET | `/cidadao/habilitacao` | Situação da habilitação, avisos e pedidos de categoria |
| POST | `/cidadao/habilitacao/infracoes` | Registro de infração simulada no histórico da PPD |
| POST | `/cidadao/habilitacao/conclusao-ppd` | Conclusão do período da PPD |
| POST | `/cidadao/habilitacao/reinicio` | Nova PPD após a cassação |
| POST | `/cidadao/habilitacao/alteracoes-categoria` | Validação da mudança de categoria |
| GET | `/cidadao/sne` | Situação da adesão ao SNE |
| POST | `/cidadao/sne/adesao` | Adesão ao SNE |

## Dados de demonstração

| UF | Placa | Cenário |
|--|--|--|
| DF | JKA1234 | Regular, com vistoria válida: emite CRLV-e e está apto à TEI |
| DF | ABC1D23 | Débitos vencidos e restrição judicial: tudo bloqueado |
| DF | XYZ9A87 | Alienação fiduciária: emite CRLV-e, mas não pode usar a TEI |
| DF | QWE2B45 | Débito a vencer e vistoria vencida: TEI exige nova vistoria |
| DF | LMN7O89 | Licenciamento pendente e DUT físico |
| GO | GOA1B23 | Base de GO (outra instância do Multiton), fora da TEI do DF |

- **Compradores para a TEI:** CPF 987.654.321-09 (cadastro completo) e CPF 111.222.333-44 (sem biometria).
- **Adesão ao SNE por CNH:** CNH 04512345678, código 98765.
- **Adesão ao SNE por CRLV:** placa JKA1234, RENAVAM 11111111111, número de segurança 54321.
- **Indicação de condutor:** CPF 987.654.321-09 e qualquer CNH com 11 dígitos.
- **Habilitação:** a PPD da cidadã de demonstração foi emitida há mais de 12 meses, com uma infração leve. Concluir o período leva a "Definitiva"; registrar antes uma infração grave leva a "Cassada".

Os dados ficam em memória e voltam ao estado inicial quando o servidor reinicia.
