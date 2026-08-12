from src.database.conexao import get_connection


def buscar_tendencia_hidrologica(cursor):
    cursor.execute("""
        SELECT
            calculado_em,
            pico_impacto_mm,
            horario_pico,
            intensidade_prevista,
            tendencia_rio
        FROM app_hidro_tendencia
        LIMIT 1;
    """)

    return cursor.fetchone()


def buscar_ultimo_nivel_rio(cursor):
    cursor.execute("""
        SELECT
            data_hora,
            nivel_metros
        FROM hidro_leituras_rio
        ORDER BY data_hora DESC
        LIMIT 1;
    """)

    return cursor.fetchone()


def buscar_resumo_epagri_observada(cursor):
    cursor.execute("""
        WITH ultimos AS (
            SELECT DISTINCT ON (codigo_estacao, nome_variavel, janela_horas)
                codigo_estacao,
                municipio,
                nome_variavel,
                janela_horas,
                valor,
                coletado_em
            FROM hidro_epagri_ciram_snapshot_variaveis
            WHERE nome_variavel IN ('Precipitação Total', 'Temperatura Instantânea')
            ORDER BY codigo_estacao, nome_variavel, janela_horas, coletado_em DESC
        )
        SELECT
            AVG(valor) FILTER (
                WHERE nome_variavel = 'Precipitação Total'
                  AND janela_horas = 1
            ) AS chuva_1h_media_mm,

            AVG(valor) FILTER (
                WHERE nome_variavel = 'Precipitação Total'
                  AND janela_horas = 12
            ) AS chuva_12h_media_mm,

            AVG(valor) FILTER (
                WHERE nome_variavel = 'Precipitação Total'
                  AND janela_horas = 24
            ) AS chuva_24h_media_mm,

            MAX(valor) FILTER (
                WHERE nome_variavel = 'Precipitação Total'
                  AND janela_horas = 24
            ) AS chuva_24h_max_mm
        FROM ultimos;
    """)

    return cursor.fetchone()


def buscar_resumo_epagri_prevista(cursor):
    cursor.execute("""
        WITH ultima_rodada AS (
            SELECT MAX(pasta_modelo) AS pasta_modelo
            FROM hidro_previsao_epagri_ciram_ocr
            WHERE modelo = 'GFS'
        ),
        previsao AS (
            SELECT
                p.codigo_ibge,
                p.municipio,
                p.data_previsao,
                p.chuva_mm,
                ROW_NUMBER() OVER (
                    PARTITION BY p.codigo_ibge
                    ORDER BY p.data_previsao
                ) AS dia_ordem
            FROM hidro_previsao_epagri_ciram_ocr p
            INNER JOIN ultima_rodada u
                ON p.pasta_modelo = u.pasta_modelo
            WHERE p.modelo = 'GFS'
        )
        SELECT
            AVG(chuva_mm) FILTER (
                WHERE dia_ordem <= 1
            ) AS chuva_prevista_24h_mm,

            AVG(chuva_mm) FILTER (
                WHERE dia_ordem <= 2
            ) AS chuva_prevista_48h_mm,

            AVG(chuva_mm) FILTER (
                WHERE dia_ordem <= 3
            ) AS chuva_prevista_72h_mm,

            AVG(chuva_mm) FILTER (
                WHERE dia_ordem <= 5
            ) AS chuva_prevista_5d_mm
        FROM previsao;
    """)

    return cursor.fetchone()


def salvar_aprendizado():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        tendencia = buscar_tendencia_hidrologica(cursor)
        nivel_rio = buscar_ultimo_nivel_rio(cursor)
        epagri_obs = buscar_resumo_epagri_observada(cursor)
        epagri_prev = buscar_resumo_epagri_prevista(cursor)

        if not tendencia:
            print("Nenhum dado encontrado em app_hidro_tendencia.")
            return

        if not nivel_rio:
            print("Nenhum dado encontrado em hidro_leituras_rio.")
            return

        calculado_em, pico_impacto_mm, horario_pico, intensidade_prevista, tendencia_rio = tendencia
        data_hora_nivel, nivel_metros = nivel_rio

        chuva_obs_1h = epagri_obs[0] if epagri_obs else None
        chuva_obs_12h = epagri_obs[1] if epagri_obs else None
        chuva_obs_24h = epagri_obs[2] if epagri_obs else None
        chuva_obs_24h_max = epagri_obs[3] if epagri_obs else None

        chuva_prev_24h = epagri_prev[0] if epagri_prev else None
        chuva_prev_48h = epagri_prev[1] if epagri_prev else None
        chuva_prev_72h = epagri_prev[2] if epagri_prev else None
        chuva_prev_5d = epagri_prev[3] if epagri_prev else None

        fonte_previsao_prioritaria = (
            "EPAGRI/CIRAM"
            if chuva_prev_24h is not None
            else "APP_HIDRO_TENDENCIA"
        )

        cursor.execute("""
            INSERT INTO hidro_historico_aprendizado (
                data_hora_snapshot,
                horario_pico_previsto,
                pico_impacto_mm,
                intensidade_prevista,
                tendencia_rio,
                nivel_rio_momento,

                chuva_epagri_observada_1h_mm,
                chuva_epagri_observada_12h_mm,
                chuva_epagri_observada_24h_mm,
                chuva_epagri_observada_24h_max_mm,

                chuva_epagri_prevista_24h_mm,
                chuva_epagri_prevista_48h_mm,
                chuva_epagri_prevista_72h_mm,
                chuva_epagri_prevista_5d_mm,
                fonte_previsao_prioritaria
            )
            VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            );
        """, (
            calculado_em,
            horario_pico,
            pico_impacto_mm,
            intensidade_prevista,
            tendencia_rio,
            nivel_metros,

            chuva_obs_1h,
            chuva_obs_12h,
            chuva_obs_24h,
            chuva_obs_24h_max,

            chuva_prev_24h,
            chuva_prev_48h,
            chuva_prev_72h,
            chuva_prev_5d,
            fonte_previsao_prioritaria,
        ))

        conn.commit()

        print("Aprendizado hidrológico salvo com sucesso.")
        print(f"Snapshot: {calculado_em}")
        print(f"Nível atual: {nivel_metros} m")
        print(f"Pico impacto: {pico_impacto_mm} mm")
        print(f"Horário pico previsto: {horario_pico}")
        print(f"Intensidade: {intensidade_prevista}")
        print(f"Tendência: {tendencia_rio}")
        print(f"EPAGRI observada 1h média: {chuva_obs_1h} mm")
        print(f"EPAGRI observada 24h média: {chuva_obs_24h} mm")
        print(f"EPAGRI observada 24h máxima: {chuva_obs_24h_max} mm")
        print(f"EPAGRI prevista 24h média: {chuva_prev_24h} mm")
        print(f"EPAGRI prevista 5d média: {chuva_prev_5d} mm")
        print(f"Fonte previsão prioritária: {fonte_previsao_prioritaria}")

    except Exception as e:
        conn.rollback()
        print(f"Erro ao salvar aprendizado hidrológico: {e}")
        raise

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    salvar_aprendizado()