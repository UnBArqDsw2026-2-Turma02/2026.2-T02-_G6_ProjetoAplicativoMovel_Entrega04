# Dirigindo Meu Carro

**Código da Disciplina**: FGA0208<br>
**Número do Grupo**: Dirigindo Meu Carro<br>
**Entrega**: 04<br>

## Alunos
|Matrícula | Aluno |
| -- | -- |
| 23/2025730  |  [Edson Pereira Roldão Filho](https://github.com/edso-n) |
| 23/1012100  |  [Felipe Henrique Oliveira Sousa](https://github.com/fhenrique77) |
| 24/1025336  |  [Matheus Pinheiro](https://github.com/matheus-06) |
| 23/1037727 |  [Ricardo Henrique Silva Rodrigues](https://github.com/R1K4S) |
| 23/2007016  |  [Yuri Souza de Andrade Castro Silva](https://github.com/y123yuri) |

## Sobre 
Esta entrega consolida as Entregas [01](https://unbarqdsw2026-2-turma02.github.io/2026.2-T02-_G6_ProjetoAplicativoMovel_Entrega01/), [02](https://unbarqdsw2026-2-turma02.github.io/2026.2-T02-_G6_ProjetoAplicativoMovel_Entrega02/) e [03](https://unbarqdsw2026-2-turma02.github.io/2026.2-T02-_G6_ProjetoAplicativoMovel_Entrega03/#/) no [Documento de Arquitetura de Software](/Base/Relatorios/1.1.1.DAS.md) do recorte estudado do aplicativo DETRAN-DF Digital e entrega um [aplicativo executável (MVP)](/Base/Relatorios/1.1.3.AplicativoMVP.md) que materializa a arquitetura proposta, com os padrões Multiton, Factory Method, Prototype, Adapter, Facade e Strategy.

## Screenshots da Terceira Entrega
Adicione 2 ou mais screenshots em termos de artefatos realizados na entrega.

## Há algo a ser executado?

(X) SIM

( ) NÃO

O MVP fica na pasta `aplicativo/`. Com o Docker Desktop aberto, na raiz do repositório:

```bash
docker compose up --build
```

- Aplicativo: <http://127.0.0.1:8000> (API em <http://127.0.0.1:8000/docs>)
- Esta documentação: <http://127.0.0.1:3000>

Sem Docker, com Python 3.10 ou superior: `pip install -r aplicativo/requirements.txt` e `python -m aplicativo`. O manual completo está na página [1.1.3. Aplicativo (MVP)](/Base/Relatorios/1.1.3.AplicativoMVP.md).

## Informações Complementares 
Quaisquer outras informações adicionais podem ser descritas nessa seção.

## Histórico de Versão

| Versão |    Data    | Alterações                           | Autor |
| :----: | :--------: | ------------------------------------ | ----- |
|  1.0 | 04/11/2026 | Criação do esqueleto inicial a partir do template da disciplina| [Edson](https://github.com/edso-n)|
|  1.1 | 22/11/2026 | Seção Sobre e manual de execução do MVP | [Yuri](https://github.com/y123yuri)|

