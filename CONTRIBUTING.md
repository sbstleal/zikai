# Guia de Contribuição e Padrões de Projeto (Git Conventions)

Este documento estabelece o guia oficial de padronização para versionamento, nomenclatura de commits, ramificações (*branches*), fluxo de trabalho e organização do repositório **ZikAI - Paraíba**.

---

## 1. Padrão de Nomenclatura de Commits (Conventional Commits)

Todas as mensagens de commit deste repositório devem seguir a especificação [Conventional Commits](https://www.conventionalcommits.org/pt-br/v1.0.0/):

```
<tipo>(<escopo>): <descrição sucinta no imperativo/presente>

[corpo opcional detalhando a motivação e mudanças]

[rodapé opcional com referências a issues ou breaking changes]
```

### 1.1 Tipos Permitidos (`<tipo>`)

| Tipo | Finalidade | Exemplo |
| :--- | :--- | :--- |
| **`feat`** | Adição de uma nova funcionalidade no sistema ou pipeline | `feat(api): adicionar integração com endpoint da infodengue` |
| **`fix`** | Correção de um bug ou erro de processamento/código | `fix(pipeline): tratar valores nulos em dados climáticos` |
| **`docs`** | Alterações em documentações, monografia, LaTeX ou README | `docs(monografia): adicionar fundamentação teórica sobre arboviroses` |
| **`ml`** | Treinamento, engenharia de atributos ou avaliação de modelos de IA | `ml(forecast): implementar modelo xgboost para previsão a 4 semanas` |
| **`refactor`** | Mudança no código que não altera comportamento nem conserta bugs | `refactor(backend): modularizar rotas dos controladores de alertas` |
| **`perf`** | Melhorias focadas em ganho de desempenho | `perf(etl): paralelizar requisições para os 223 municípios da PB` |
| **`test`** | Adição ou refatoração de testes unitários ou de integração | `test(ml): adicionar teste de validação temporal cruzada` |
| **`chore`** | Tarefas de manutenção, dependências e configurações gerais | `chore(deps): atualizar versão da biblioteca scikit-learn` |
| **`ci`** | Alterações em fluxos de integração contínua (ex: GitHub Actions) | `ci(github): configurar pipeline de verificação de testes` |

### 1.2 Escopos Sugeridos (`<escopo>`)

* `api`: Serviços e endpoints de backend.
* `pipeline`: Ingestão, ETL e processamento de dados da PB.
* `ml`: Modelos de inteligência artificial, hiperparâmetros e métricas.
* `dashboard` / `ui`: Componentes de interface e mapas no frontend.
* `monografia`: Capítulos, texto acadêmico e bibliografia do TCC.
* `geo`: Manipulação de malhas do IBGE e dados geoespaciais.

---

## 2. Padrão de Nomenclatura de Branches (*Git Branching Strategy*)

Adotamos uma versão simplificada e robusta baseada no **GitHub Flow / Git Flow**:

* **`main`**: Ramo estável com as versões consolidadas do código e monografia.
* **`develop`**: Ramo de integração dos desenvolvimentos em andamento.
* **Branches de funcionalidade / trabalho**: Devem partir de `develop` (ou `main`) seguindo o padrão:
  * `feat/<nome-curto>` (Ex: `feat/infodengue-extractor`, `feat/mapa-paraiba`)
  * `ml/<nome-curto>` (Ex: `ml/prophet-baseline`, `ml/risk-classifier`)
  * `fix/<nome-curto>` (Ex: `fix/geojson-codarea-parser`)
  * `docs/<nome-curto>` (Ex: `docs/capitulo-metodologia`)
  * `refactor/<nome-curto>` (Ex: `refactor/etl-module`)

---

## 3. Boas Práticas do Repositório

1. **Nunca commitar dados pesados ou credenciais**:
   * Arquivos `.csv`, `.parquet`, modelos pesados (`.pkl`) e senhas/chaves estão bloqueados no `.gitignore`.
   * Scripts devem buscar os dados ou salvá-los localmente em `data/raw` e `data/processed`.
2. **Commits atômicos**:
   * Faça commits frequentes e focados em uma única responsabilidade.
3. **Padrão de Código**:
   * Python: PEP 8, com formatação via `black` ou `ruff`.
   * JavaScript / TypeScript: ESLint + Prettier.
