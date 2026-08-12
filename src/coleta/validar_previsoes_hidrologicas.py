from src.database.conexao import get_connection


def validar_previsoes():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO hidro_validacao_previsoes (
                data_hora_snapshot,
                data_hora_nivel_rio,
                horizonte_horas,
                nivel_atual,
                nivel_previsto_ajustado,
                nivel_real_m,
                erro_absoluto_m,
                erro_absoluto_cm,
                qualidade_modelo,
                validado_em
            )
            SELECT
                e.data_hora_snapshot,
                e.data_hora_nivel_rio,
                24 AS horizonte_horas,
                e.nivel_atual,
                e.nivel_previsto_ajustado,
                e.nivel_real_m,
                e.erro_absoluto,
                e.erro_absoluto * 100,
                e.qualidade_modelo,
                NOW()
            FROM app_hidro_erro_previsao e
            WHERE e.nivel_real_m IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1
                  FROM hidro_validacao_previsoes v
                  WHERE v.data_hora_snapshot = e.data_hora_snapshot
                    AND v.horizonte_horas = 24
              );
        """)

        qtd = cursor.rowcount
        conn.commit()

        print("Validação de previsões hidrológicas finalizada.")
        print(f"Registros inseridos: {qtd}")

    except Exception as erro:
        conn.rollback()
        print(f"Erro ao validar previsões hidrológicas: {erro}")
        raise

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    validar_previsoes()