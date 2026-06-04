from src.database.conexao import get_connection


def salvar_snapshot():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO hidro_snapshots_previsao_rio (
            data_hora_nivel_rio,
            nivel_atual,
            chuva_total_bacia_24h_mm,
            subida_estimada_m,
            nivel_previsto_m,
            maior_percentual_barragem,
            fator_barragem,
            nivel_previsto_ajustado,
            maior_cheia_historica
        )
        SELECT
            data_hora_projecao AS data_hora_nivel_rio,
            nivel_atual,
            impacto_ponderado_mm AS chuva_total_bacia_24h_mm,
            ajuste_tendencia_m AS subida_estimada_m,
            nivel_previsto AS nivel_previsto_m,
            NULL::numeric AS maior_percentual_barragem,
            NULL::numeric AS fator_barragem,
            nivel_previsto AS nivel_previsto_ajustado,
            NULL::numeric AS maior_cheia_historica
        FROM app_projecao_nivel_rio;
    """)

    conn.commit()
    cursor.close()
    conn.close()

    print("Snapshot da previsão salvo com sucesso.")


if __name__ == "__main__":
    salvar_snapshot()