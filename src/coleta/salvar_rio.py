from src.database.conexao import get_connection
from src.coleta.coletar_rio import coletar_dados


def salvar_dados():
    dados = coletar_dados()

    conn = get_connection()
    cursor = conn.cursor()

    inseridos = 0

    for d in dados:
        cursor.execute(
            """
            INSERT INTO leituras_rio (
                data_hora,
                nivel_metros,
                variacao,
                chuva_mm
            )
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (data_hora, fonte) DO NOTHING;
            """,
            (
                d["data_hora"],
                d["nivel_metros"],
                d["variacao"],
                d["chuva_mm"],
            ),
        )

        inseridos += cursor.rowcount

    conn.commit()
    cursor.close()
    conn.close()

    print(f"Processo finalizado. Registros inseridos: {inseridos}")


if __name__ == "__main__":
    salvar_dados()