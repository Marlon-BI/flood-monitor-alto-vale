# Flood Monitor Alto Vale

## 1. Visão Geral do Projeto

O Flood Monitor Alto Vale é uma plataforma experimental de monitoramento hidrológico em tempo real voltada para Rio do Sul/SC e região do Alto Vale do Itajaí.

O projeto tem como objetivo construir uma base histórica própria e um modelo inteligente de análise hidrológica utilizando:

- nível do rio;
- chuva observada;
- previsão meteorológica;
- comportamento das barragens;
- velocidade de subida/descida;
- aprendizado baseado em histórico;
- contexto climático regional.

A proposta é evoluir gradualmente de um monitoramento operacional para um sistema de apoio à prevenção de enchentes e análise de risco hidrológico.

---

# 2. Objetivos do Projeto

## Objetivos atuais

- Coletar dados em tempo real.
- Construir base histórica própria.
- Monitorar tendência do rio.
- Gerar projeções hidrológicas futuras.
- Consolidar múltiplas fontes de dados.
- Disponibilizar dashboard público responsivo.

## Objetivos futuros

- Machine Learning hidrológico avançado.
- Sistema de alertas personalizados.
- Cadastro por endereço/CEP.
- Alertas via WhatsApp e e-mail.
- Painel administrativo.
- APIs públicas.
- Integração com Defesa Civil.
- Monetização via patrocinadores.

---

# 3. Motivação

Rio do Sul e diversas cidades do Alto Vale sofrem historicamente com enchentes severas.

Embora existam sistemas públicos de monitoramento, muitos dados permanecem descentralizados ou pouco acessíveis à população.

O projeto busca centralizar e transformar esses dados em uma plataforma:

- acessível;
- visual;
- automatizada;
- histórica;
- inteligente;
- escalável.

---

# 4. Arquitetura Atual

## Fluxo completo

```text
Defesa Civil
Open-Meteo
APIs hidrológicas
Boletins meteorológicos
        ↓
Python (coletores automatizados)
        ↓
Tratamento e padronização
        ↓
Supabase PostgreSQL
        ↓
Views analíticas SQL
        ↓
Modelo hidrológico
        ↓
Dashboard público (Lovable)