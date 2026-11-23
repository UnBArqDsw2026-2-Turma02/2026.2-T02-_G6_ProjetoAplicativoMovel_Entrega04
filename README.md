# 2026.2 - T02 - G6 - Projeto Aplicativo Móvel - Entrega 04

Repositório da Entrega 04 do grupo **Dirigindo Meu Carro** na disciplina Arquitetura e Desenho de Software (FGA0208, UnB).

- **`aplicativo/`**: o MVP executável em FastAPI, organizado pelas camadas da Representação Arquitetural e pelos padrões de projeto da Entrega 03.
- **`docs/`**: a documentação do GitHub Pages, com o Documento de Arquitetura de Software (DAS) do recorte estudado do aplicativo DETRAN-DF Digital.

GitHub Pages: <https://unbarqdsw2026-2-turma02.github.io/2026.2-T02-_G6_ProjetoAplicativoMovel_Entrega04/>

## Como rodar o aplicativo

Precisa só do [Python 3.10 ou superior](https://www.python.org/downloads/) e de internet (para instalar as dependências e carregar o visual).

| Sistema | O que fazer |
|--|--|
| **Windows** | Dê dois cliques em `executar.bat` |
| **Linux ou macOS** | No terminal, na pasta do repositório: `./executar.sh` |

O script cria um ambiente virtual (`.venv`), instala as dependências e abre o navegador em <http://127.0.0.1:8000>. Na tela inicial, clique em **Entrar com gov.br**: o login é simulado e não pede nenhum dado. Para encerrar, pressione `Ctrl+C` no terminal.

Da segunda vez em diante, o mesmo script abre o aplicativo direto. Para usar outra porta: `executar.bat 8001` ou `./executar.sh 8001`.

### Com Docker (opcional)

Com o Docker Desktop aberto:

```shell
docker compose up --build
```

Sobe o aplicativo em <http://127.0.0.1:8000> e a documentação em <http://127.0.0.1:3000>.

### O que testar

| Tela | Experimente |
|--|--|
| Início | Abrir o veículo `JKA1234` (regular) e o `ABC1D23` (com pendências) |
| CRLV-e | Emitir o documento e ver a prova do Prototype |
| Transferência | CPF do comprador `987.654.321-09` (apto) ou `111.222.333-44` (sem biometria) |
| Infrações | Aplicar desconto, gerar o boleto e indicar o condutor (CPF `987.654.321-09`) |
| SNE | Aderir com a CNH `04512345678` e o código `98765` |
| Habilitação | Concluir o período da PPD, ou antes registrar uma infração grave para ver a cassação |

Manual completo, rotas da API e estrutura do código: [`aplicativo/README.md`](aplicativo/README.md).

## Como ver a documentação localmente

A documentação usa o [Docsify](https://docsify.js.org/), que lê os arquivos Markdown direto da pasta `docs/`. Qualquer servidor estático serve:

```shell
python -m http.server 3000 --directory docs
```

Depois, abra <http://127.0.0.1:3000>. Com o Node.js instalado, também é possível usar `npx docsify-cli serve docs`.
