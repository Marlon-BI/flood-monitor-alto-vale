# INLIFT Sentinel

## 1. Visão Geral do Projeto

O **INLIFT Sentinel** é uma plataforma inteligente de apoio à tomada de decisão para monitoramento, prevenção, preparação, resposta e gestão de eventos climáticos, ambientais e operacionais.

O projeto nasceu a partir de estudos locais realizados em Rio do Sul/SC e na região do Alto Vale do Itajaí, com foco inicial em enchentes, monitoramento hidrológico, barragens, áreas de risco e operação de Defesa Civil.

Apesar da origem hidrológica, o Sentinel foi concebido para ser uma plataforma modular, escalável e adaptável a diferentes realidades climáticas e territoriais. Sua arquitetura permite aplicação em cenários como:

* chuvas intensas;
* enchentes e inundações;
* deslizamentos;
* estiagens e secas prolongadas;
* baixa umidade do ar;
* monitoramento ambiental;
* gestão de recursos hídricos;
* gestão de crise;
* infraestrutura crítica;
* operações de Defesa Civil;
* apoio à população em situações de risco.

A proposta é consolidar dados dispersos em uma visão centralizada, operacional e inteligente, apoiando gestores públicos, órgãos de resposta, concessionárias, empresas e população.

---

## 2. Objetivos do Projeto

### Objetivos atuais

* Coletar dados hidrológicos, meteorológicos, geoespaciais e operacionais.
* Construir uma base histórica própria.
* Monitorar nível do rio, chuva, barragens e tendência hidrológica.
* Gerar projeções futuras com base em dados históricos e previsões meteorológicas.
* Consolidar múltiplas fontes de dados em um banco único.
* Disponibilizar painéis operacionais e executivos.
* Apoiar a tomada de decisão em cenários de risco.
* Estruturar uma base técnica reutilizável para diferentes municípios, estados e regiões.

### Objetivos futuros

* Integração com WhatsApp.
* Aplicativo do cidadão.
* IA preditiva avançada.
* Sensores IoT reais.
* Integração com CPRM.
* Replay de crise.
* Sistema de alertas personalizados.
* Cadastro por endereço, bairro ou área de risco.
* Painel administrativo.
* APIs públicas e privadas.
* Integração com Defesa Civil, prefeituras e órgãos estaduais.
* Expansão para outros cenários climáticos, como seca, estiagem e baixa umidade.
* Adaptação multilíngue para uso no Brasil ou fora do Brasil.

---

## 3. Motivação

Eventos climáticos extremos, enchentes, deslizamentos, estiagens e crises ambientais impactam diretamente a população, a infraestrutura urbana, a economia e a capacidade de resposta dos municípios.

Em muitas regiões, os dados necessários para tomada de decisão existem, mas estão descentralizados, pouco integrados ou difíceis de interpretar rapidamente.

O INLIFT Sentinel busca transformar esse cenário por meio de uma plataforma:

* acessível;
* visual;
* automatizada;
* histórica;
* inteligente;
* geoespacial;
* operacional;
* escalável;
* adaptável a diferentes realidades.

O objetivo não é substituir alertas oficiais ou órgãos responsáveis, mas fornecer uma camada tecnológica de apoio à decisão, análise territorial, monitoramento contínuo e gestão operacional.

---

## 4. Arquitetura Atual

### Fluxo completo

```text
Fontes externas
Defesa Civil SC
Defesa Civil Rio do Sul
Open-Meteo
Boletins meteorológicos
Bases GIS
MDT / dados geoespaciais
        ↓
Python
Coletores automatizados
Processamento
Validação
Aprendizado hidrológico
        ↓
Supabase PostgreSQL / PostGIS
Tabelas hidro_*
Tabelas geo_*
Tabelas op_*
Tabelas sim_*
Tabelas cmd_*
        ↓
Views analíticas SQL
Views app_*
Views GeoJSON
Views operacionais
        ↓
Motor hidrológico e preditivo
Projeção de nível
Tendência
Risco
Cenários
        ↓
Aplicação web
Lovable / Front-end operacional
        ↓
Usuários finais
Defesa Civil
Prefeituras
Gabinete
Secretarias
Bombeiros
Concessionárias
População
```

---

## 5. Principais Camadas do Sistema

### Camada de Coleta

Responsável por executar os scripts Python que consomem fontes externas e salvam dados padronizados no banco.

Principais grupos:

* coleta de nível do rio;
* coleta de chuva observada;
* coleta de previsão meteorológica;
* coleta de barragens;
* coleta de boletins oficiais;
* snapshots de previsão;
* aprendizado hidrológico;
* validação das previsões.

---

### Camada Hidrológica

Responsável por armazenar e processar dados relacionados a rio, chuva, barragens e previsão.

Exemplos de estruturas:

* `hidro_leituras_rio`
* `hidro_previsao_chuva`
* `hidro_chuva_defesa_civil`
* `hidro_leituras_barragens`
* `hidro_snapshots_previsao_rio`
* `hidro_historico_aprendizado`

---

### Camada Geoespacial

Responsável por armazenar dados territoriais e operacionais em formato espacial.

Exemplos de camadas:

* bairros;
* hidrografia;
* áreas de risco;
* manchas de inundação;
* perímetro urbano;
* sistema viário;
* eixo de logradouros;
* edificações;
* pontos cotados.

---

### Camada Operacional

Responsável por apoiar ações de resposta e gestão de crise.

Exemplos de estruturas:

* ocorrências operacionais;
* rotas interditadas;
* evacuações;
* abrigos;
* alertas emitidos;
* comunicados operacionais;
* obras de mitigação.

---

### Camada de Simulação

Responsável por representar cenários operacionais e impactos previstos.

Exemplos:

* cenários por cota;
* pessoas afetadas;
* famílias afetadas;
* bairros afetados;
* rotas interditadas;
* abrigos necessários;
* infraestruturas em risco.

---

### Camada de Aplicação

Responsável por entregar os dados já tratados para o front-end.

Exemplos:

* `app_status_pipeline`
* `app_dashboard_principal`
* `app_barragens_consolidadas`
* `app_centro_operacional_mapa`
* `app_cenario_operacional_atual`
* `app_resumo_geoespacial_operacional`
* `app_projecao_nivel_rio`

---

## 6. Aviso de Responsabilidade

O INLIFT Sentinel é uma plataforma experimental e evolutiva de apoio à análise, monitoramento e tomada de decisão.

A plataforma não substitui alertas oficiais da Defesa Civil, Corpo de Bombeiros, prefeituras, órgãos estaduais, órgãos federais ou autoridades competentes.

Em situações de emergência, devem ser sempre seguidos os canais oficiais de atendimento e orientação.
