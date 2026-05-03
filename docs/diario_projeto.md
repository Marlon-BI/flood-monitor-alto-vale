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