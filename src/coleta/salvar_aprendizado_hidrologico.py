from src.database.conexao import get_connection


def buscar_tendencia_hidrologica(cursor):
    cursor.execute("""
        SELECT
            calculado_em,
            pico_impacto_mm,
            horario_pico,
            intensidade_prevista,
            tendencia_rio
        FROM vw_tendencia_hidrologica
        LIMIT 1;
    """)

    return cursor.fetchone()


def buscar_ultimo_nivel_rio(cursor):
    cursor.execute("""
        SELECT
            data_hora,
            nivel_metros
        FROM leituras_rio
        ORDER BY data_hora DESC
        LIMIT 1;
    """)

    return cursor.fetchone()


def salvar_aprendizado():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        tendencia = buscar_tendencia_hidrologica(cursor)
        nivel_rio = buscar_ultimo_nivel_rio(cursor)

        if not tendencia:
            print("Nenhum dado encontrado em vw_tendencia_hidrologica.")
            return

        if not nivel_rio:
            print("Nenhum dado encontrado em leituras_rio.")
            return

        calculado_em, pico_impacto_mm, horario_pico, intensidade_prevista, tendencia_rio = tendencia
        data_hora_nivel, nivel_metros = nivel_rio

        cursor.execute("""
            INSERT INTO historico_aprendizado_hidrologico (
                data_hora_snapshot,
                horario_pico_previsto,
                pico_impacto_mm,
                intensidade_prevista,
                tendencia_rio,
                nivel_rio_momento
            )
            VALUES (%s, %s, %s, %s, %s, %s);
        """, (
            calculado_em,
            horario_pico,
            pico_impacto_mm,
            intensidade_prevista,
            tendencia_rio,
            nivel_metros,
        ))

        conn.commit()

        print("Aprendizado hidrológico salvo com sucesso.")
        print(f"Snapshot: {calculado_em}")
        print(f"Nível atual: {nivel_metros} m")
        print(f"Pico impacto: {pico_impacto_mm} mm")
        print(f"Horário pico previsto: {horario_pico}")
        print(f"Intensidade: {intensidade_prevista}")
        print(f"Tendência: {tendencia_rio}")

    except Exception as e:
        conn.rollback()
        print(f"Erro ao salvar aprendizado hidrológico: {e}")
        raise

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    salvar_aprendizado()