from datetime import timedelta
from src.database.conexao import get_connection


def buscar_nivel_proximo(cursor, data_referencia):
    cursor.execute("""
        SELECT nivel_metros
        FROM leituras_rio
        WHERE data_hora >= %s
        ORDER BY data_hora ASC
        LIMIT 1;
    """, (data_referencia,))

    resultado = cursor.fetchone()
    return resultado[0] if resultado else None


def atualizar_aprendizado():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            data_hora_snapshot
        FROM historico_aprendizado_hidrologico
        WHERE
            nivel_rio_6h_depois IS NULL
            OR nivel_rio_12h_depois IS NULL
            OR nivel_rio_24h_depois IS NULL
        ORDER BY data_hora_snapshot;
    """)

    registros = cursor.fetchall()

    atualizados = 0

    for registro_id, snapshot in registros:

        data_6h = snapshot + timedelta(hours=6)
        data_12h = snapshot + timedelta(hours=12)
        data_24h = snapshot + timedelta(hours=24)

        nivel_6h = buscar_nivel_proximo(cursor, data_6h)
        nivel_12h = buscar_nivel_proximo(cursor, data_12h)
        nivel_24h = buscar_nivel_proximo(cursor, data_24h)

        cursor.execute("""
            UPDATE historico_aprendizado_hidrologico
            SET
                nivel_rio_6h_depois = COALESCE(nivel_rio_6h_depois, %s),
                nivel_rio_12h_depois = COALESCE(nivel_rio_12h_depois, %s),
                nivel_rio_24h_depois = COALESCE(nivel_rio_24h_depois, %s)
            WHERE id = %s;
        """, (
            nivel_6h,
            nivel_12h,
            nivel_24h,
            registro_id
        ))

        atualizados += 1

    conn.commit()

    cursor.close()
    conn.close()

    print("Atualização finalizada.")
    print(f"Registros processados: {atualizados}")


if __name__ == "__main__":
    atualizar_aprendizado()