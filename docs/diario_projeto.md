# Flood Monitor Alto Vale

## 1. Objetivo da POC

Criar uma base histórica própria para monitoramento do nível do rio em Rio do Sul/SC e região do Alto Vale do Itajaí.

A ideia inicial é coletar, armazenar e analisar dados reais de nível do rio e chuva observada. Em uma segunda etapa, o projeto deverá cruzar esses dados com previsões meteorológicas em milímetros de chuva nas cidades que influenciam a bacia hidrográfica da região.

## 2. Motivação

Rio do Sul e outras cidades do Alto Vale e Vale do Itajaí sofrem historicamente com enchentes. A proposta desta POC é iniciar uma base própria de dados a partir de hoje, sem depender inicialmente de histórico antigo.

Com o tempo, essa base poderá apoiar análises como:

- comportamento do nível do rio;
- velocidade de subida ou descida;
- impacto da chuva local;
- impacto da chuva em cidades a montante;
- criação de alertas;
- projeções simples de nível futuro;
- evolução futura para modelos estatísticos ou IA.

## 3. Arquitetura atual

Fluxo implementado até o momento:

```text
Site Defesa Civil Rio do Sul
        ↓
Python - coleta dos dados
        ↓
Tratamento dos dados
        ↓
Supabase PostgreSQL
        ↓
Base histórica própria

--comando para rodar o coleta_rio: python -m src.coleta.executar_coleta_automatica
--comando para rodar o coleta_previsao_chuva: python -m src.coleta.coletar_previsao_chuva

4. Evolução da Arquitetura (Versão Atual)

A arquitetura evoluiu de uma coleta manual para um pipeline automatizado em nuvem.

🔄 Fluxo atual completo

APIs externas (Defesa Civil + Open-Meteo + outras fontes)
        ↓
Python (coleta de dados)
        ↓
Tratamento e padronização
        ↓
Supabase PostgreSQL (armazenamento)
        ↓
Views SQL (camada analítica)
        ↓
Snapshot de previsões (histórico para avaliação)
        ↓
GitHub Actions (execução automática)

5. Coletas implementadas
🌊 Nível do rio
Fonte: Defesa Civil
Frequência: a cada execução do pipeline
Armazenamento: tabela histórica
🌧️ Previsão de chuva
Fonte: Open-Meteo + simulação adicional (multi-fonte)
Dados: chuva por hora (mm)
Cobertura: cidades da bacia hidrográfica
🏗️ Barragens
Fonte: API via GraphQL
Dados:
capacidade atual
capacidade máxima
nível percentual
montante/jusante
🚨 Defesa Civil (boletins)
Fonte: API WordPress
Objetivo: enriquecer contexto de eventos
6. Camada analítica (SQL)

Foram criadas views para facilitar análise:

📊 vw_previsao_enchente
Junta:
nível atual do rio
chuva prevista
status das barragens
Calcula:
risco (NORMAL, etc)
maior cheia histórica
📊 vw_previsao_enchente_resumo
Consolida:
maior percentual de barragens
status resumido
risco geral
📊 vw_previsao_nivel_rio
Primeira lógica de previsão:
nível atual
chuva prevista
subida estimada
nível futuro estimado
7. Snapshot de previsões (fundamental para ML)

Foi implementada a tabela:
snapshots_previsao_rio

Objetivo:

Registrar cada previsão gerada ao longo do tempo.

Por que isso é importante:

Permite futuramente calcular:

erro da previsão
melhoria contínua
ajuste de modelos

👉 Isso é base de Machine Learning real (aprendizado com histórico)

8. Automação do pipeline
🔁 Execução automática via GitHub Actions

Arquivo:

.github/workflows/pipeline.yml
Configuração:
schedule:
  - cron: "*/30 * * * *"

👉 Significa:
Execução a cada 30 minutos

⚙️ Execução do pipeline

Script utilizado:

python -m src.coleta.executar_pipeline_once

Esse script executa:

Coleta nível do rio
Coleta previsão de chuva
Coleta barragens
Coleta Defesa Civil
Salva snapshot da previsão
9. Banco de dados
Plataforma: Supabase (PostgreSQL)
Conexão via:
DATABASE_URL (GitHub Secrets)
SSL obrigatório
10. Status atual do projeto

✅ Pipeline automatizado na nuvem
✅ Execução sem dependência de máquina local
✅ Base histórica sendo construída
✅ Primeira lógica de previsão implementada
✅ Snapshot para avaliação futura
⚙️ Estrutura pronta para ML