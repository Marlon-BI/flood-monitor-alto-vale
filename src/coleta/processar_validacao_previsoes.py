import os
from datetime import timedelta

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL não encontrada no ambiente.")


def classificar_qualidade(erro_abs_cm: float) -> str:
    if erro_abs_cm <= 5:
        return "EXCELENTE"
    if erro_abs_cm <= 10:
        return "BOA"
    if erro_abs_cm <= 20:
        return "MODERADA"
    return "FRACA"


def main():
    engine = create_engine(DATABASE_URL)

    print("Processando validação de previsões antigas...")

    with engine.begin() as conn:
        snapshots = conn.execute(
            text("""
                SELECT
                    id,
                    data_hora_snapshot,
                    horario_previsto,
                    nivel_previsto_ajustado
                FROM hidro_snapshots_previsao_rio
                WHERE nivel_real_m IS NULL
                  AND horario_previsto <= NOW()
                  AND nivel_previsto_ajustado IS NOT NULL
                ORDER BY horario_previsto ASC
                LIMIT 200;
            """)
        ).mappings().all()

        print(f"Snapshots pendentes encontrados: {len(snapshots)}")

        processados = 0

        for snap in snapshots:
            horario_previsto = snap["horario_previsto"]

            leitura_real = conn.execute(
                text("""
                    SELECT
                        data_hora,
                        nivel_real_m
                    FROM historico_real_nivel_rio
                    WHERE data_hora BETWEEN :inicio AND :fim
                    ORDER BY ABS(EXTRACT(EPOCH FROM (data_hora - :horario_previsto)))
                    LIMIT 1;
                """),
                {
                    "inicio": horario_previsto - timedelta(minutes=45),
                    "fim": horario_previsto + timedelta(minutes=45),
                    "horario_previsto": horario_previsto,
                },
            ).mappings().first()

            if not leitura_real:
                continue

            nivel_real = float(leitura_real["nivel_real_m"])
            nivel_previsto = float(snap["nivel_previsto_ajustado"])

            erro_m = nivel_previsto - nivel_real
            erro_cm = erro_m * 100
            erro_absoluto_cm = abs(erro_cm)
            qualidade = classificar_qualidade(erro_absoluto_cm)

            conn.execute(
                text("""
                    UPDATE hidro_snapshots_previsao_rio
                    SET
                        nivel_real_m = :nivel_real_m,
                        erro_m = :erro_m,
                        erro_cm = :erro_cm,
                        erro_absoluto_cm = :erro_absoluto_cm,
                        qualidade_modelo = :qualidade_modelo,
                        validado_em = NOW()
                    WHERE id = :id;
                """),
                {
                    "id": snap["id"],
                    "nivel_real_m": nivel_real,
                    "erro_m": round(erro_m, 4),
                    "erro_cm": round(erro_cm, 2),
                    "erro_absoluto_cm": round(erro_absoluto_cm, 2),
                    "qualidade_modelo": qualidade,
                },
            )

            processados += 1

        print(f"Previsões validadas: {processados}")


if __name__ == "__main__":
    main()