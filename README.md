# 2026.2 - T02 - G6 - Projeto Aplicativo Móvel - Entrega 04

Repositório da Entrega 04 do grupo **Dirigindo Meu Carro** na disciplina Arquitetura e Desenho de Software (FGA0208, UnB). Ele contém:

- **`docs/`**: documentação publicada no GitHub Pages (Docsify), com o Documento de Arquitetura de Software (DAS) do recorte estudado do aplicativo DETRAN-DF Digital;
- **`aplicativo/`**: o MVP executável em FastAPI, organizado pelas camadas da Representação Arquitetural e pelos padrões de projeto da Entrega 03.

GitHub Pages: <https://unbarqdsw2026-2-turma02.github.io/2026.2-T02-_G6_ProjetoAplicativoMovel_Entrega04/>

## Executando com Docker

Com o Docker Desktop aberto, na raiz do repositório:

```shell
docker compose up --build
```

| Serviço | Endereço |
|--|--|
| Aplicativo (MVP) | <http://127.0.0.1:8000> |
| API (Swagger) | <http://127.0.0.1:8000/docs> |
| Documentação (Docsify via Nginx) | <http://127.0.0.1:3000> |

## Executando sem Docker

### Aplicativo

Requisito: Python 3.10 ou superior.

```shell
pip install -r aplicativo/requirements.txt
python -m aplicativo
```

Mais detalhes, dados de teste e rotas da API estão em [`aplicativo/README.md`](aplicativo/README.md).

### Documentação

A documentação é gerada pelo [Docsify](https://docsify.js.org/), que carrega os arquivos Markdown e os exibe como site, sem gerar HTML estático.

```shell
npm i docsify-cli -g
docsify serve ./docs
```

Sem o Node.js, qualquer servidor estático funciona, por exemplo: `python -m http.server 3000 --directory docs`.
