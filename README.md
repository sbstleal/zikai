# ZikAI - Paraíba 🦟📊🤖

> **Sistema Inteligente de Monitoramento e Previsão de Arboviroses Utilizando Inteligência Artificial no Estado da Paraíba**
> 
> *Trabalho de Conclusão de Curso (TCC)*

---

## 🎯 Sobre o Projeto

O **ZikAI - Paraíba** é uma plataforma acadêmica e tecnológica de apoio à tomada de decisão em vigilância epidemiológica. O sistema integra dados governamentais abertos sobre arboviroses (**Dengue, Zika e Chikungunya**) e variáveis climáticas e demográficas dos **223 municípios do Estado da Paraíba**, aplicando técnicas de **Aprendizado de Máquina (Machine Learning)** para:

1. **Prever a incidência de casos** para as próximas 2 a 4 semanas epidemiológicas (*Time-Series Forecasting*).
2. **Classificar o risco de surtos epidemiológicos** por município, categorizando os níveis de alerta (Verde, Amarelo, Laranja, Vermelho).
3. **Disponibilizar um Painel Interativo Georreferenciado** com mapas coropléticos e curvas de tendência para gestores de saúde pública e comunidade acadêmica.

---

## 🏛️ Contexto e Relevância para a Paraíba

O Estado da Paraíba possui uma posição histórica e estratégica na vigilância de arboviroses no Brasil:
* Durante a epidemia de 2015/2016, a Paraíba esteve no epicentro global da descoberta e correlação entre o **Zika vírus e a Síndrome da Microcefalia Congênita**, com pesquisas pioneiras em Campina Grande e João Pessoa.
* O estado apresenta grande diversidade climática (desde o clima litorâneo úmido na Zona da Mata até o semiárido no Sertão e Cariri), influenciando a dinâmica sazonal e os criadouros do mosquito *Aedes aegypti*.
* A antecipação de surtos via **Sistemas de Alerta Precoce (*Early Warning Systems*)** possibilita intervenções preventivas direcionadas (alocação de agentes de endemias, insumos e leitos hospitalares), minimizando impactos no Sistema Único de Saúde (SUS).

---

## 🌐 Fontes de Dados Públicas Governamentais

* **[InfoDengue (Fiocruz / FGV)](https://info.dengue.mat.br/)**: API REST pública com dados semanais epidemiológicos (casos notificados, estimados, $R_t$, nível de alerta) e meteorológicos (temperatura mínima/média/máxima, umidade) para todos os municípios da PB.
* **[IBGE - Serviço de Malhas Geográficas](https://servicodados.ibge.gov.br/)**: Malha vetorial oficial (GeoJSON) dos 223 municípios paraibanos (código UF `25`).
* **[IBGE Cidades](https://cidades.ibge.gov.br/)**: Indicadores socioeconômicos e demográficos (população e densidade demográfica).

---

## 🏗️ Estrutura do Repositório

```plaintext
zikai/
├── data/
│   ├── raw/                 # Cache de respostas brutas das APIs (GeoJSON, JSON)
│   └── processed/           # Datasets consolidados e tratados para ML
├── data_pipeline/           # Módulos de extração e ingestão (InfoDengue + IBGE)
│   ├── ibge.py              # Cliente para malha vetorial e municípios da PB
│   ├── infodengue.py        # Cliente para séries epidemiológicas e climáticas
│   └── pipeline.py          # Orquestrador da extração e carga no banco SQL
├── backend/
│   └── app/
│       └── db/              # Camada de Banco de Dados SQL (PostgreSQL / SQLite)
│           ├── models.py    # Modelos relacionais (Municipios, Registros, Previsoes)
│           ├── session.py   # Conexão e sessão com banco
│           └── repository.py# Operações de inserção e consulta
├── ml/
│   ├── notebooks/           # Análise exploratória de dados (EDA) e prototipação
│   ├── src/                 # Scripts modulares de ML (feature engineering, treino e teste)
│   └── models/              # Modelos treinados salvos (.joblib, .pt)
├── frontend/                # Aplicação web e dashboard em React / Vite / TailwindCSS
├── tests/                   # Testes automatizados com pytest
├── docs/
│   ├── monografia/          # Textos acadêmicos, capítulos e referências bibliográficas
│   └── diagramas/           # Diagramas de arquitetura, fluxo de dados e DER
├── .gitignore               # Arquivos ignorados pelo Git
├── CONTRIBUTING.md          # Padrões de commits, branches e fluxo de trabalho
└── README.md                # Apresentação do projeto
```

---

## 🌿 Padrões de Projeto e Versionamento

Este projeto adota:
* **Commits Semânticos**: [Conventional Commits](CONTRIBUTING.md) (`feat:`, `fix:`, `docs:`, `ml:`, etc.).
* **Estratégia de Ramificação**: `main` (estável), `develop` (desenvolvimento) e branches por funcionalidade (`feat/*`, `ml/*`).
* Consulte [`CONTRIBUTING.md`](CONTRIBUTING.md) para diretrizes completas de contribuição e nomenclatura.

---

## 🤖 Machine Learning

Esta seção descreve como treinar os modelos de previsão e classificação de risco.

### Treinamento
Execute o script de treinamento:
```powershell
python -m ml.src.train data/processed/pb_arboviroses_features.csv --output-dir ml/models --test-weeks 12
```
- **`--output-dir`**: diretório onde os arquivos `.joblib` e o relatório `metrics.json` serão salvos.
- **`--test-weeks`**: número de semanas reservadas para o conjunto de teste (padrão: 12).

### Estrutura dos artefatos
- `ml/models/regression_<modelo>.joblib` – modelo de regressão (Ridge ou RandomForest) que prevê o número de casos na próxima semana (`alvo_casos_1sem`).
- `ml/models/classification_<modelo>.joblib` – modelo de classificação que prevê o risco (`alvo_risco_1sem`).
- `ml/models/metrics.json` – relatório com as métricas de desempenho (MAE, RMSE, R², acurácia e F1).

### Testes
Um teste automatizado foi adicionado em `tests/test_ml.py` que verifica:
- Execução bem‑sucedida do script de treinamento em um subconjunto dos dados.
- Criação dos arquivos de modelo e do relatório de métricas.

> **Importante:** antes de rodar os testes certifique‑se de que as dependências estão instaladas:
> ```powershell
> pip install -r requirements.txt
> ```

---

## 👥 Autoria e Licença

Desenvolvido como Trabalho de Conclusão de Curso (TCC).  
Licença: MIT.


## ⚙️ Inicialização automática

Ao iniciar a API, o backend verifica os arquivos de catálogo em `data/raw/` (preferencialmente `pb_municipios_ibge_merged.json`) e popula ou sincroniza a tabela `municipios` automaticamente com nome, microrregião, mesorregião, população estimada e coordenadas geográficas (latitude e longitude). Isso garante que o endpoint `/api/municipios` sempre retorne dados completos sem a necessidade de intervenção manual.

Caso deseje desativar esse comportamento, basta definir a variável de ambiente `POPULATE_MUNICIPIOS=false` antes de iniciar o contêiner.
