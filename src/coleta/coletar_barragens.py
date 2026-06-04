import requests
from datetime import datetime
from src.database.conexao import get_connection

URL_GRAPHQL = "https://monitoramento.defesacivil.sc.gov.br/graphql"
FONTE = "Defesa Civil SC GraphQL"

BARRAGENS = {
    "DCSC-00042": {
        "nome": "Barragem Norte",
        "cidade": "José Boiteux",
        "barragem_id": 3,
    },
    "DCSC-00040": {
        "nome": "Barragem Oeste",
        "cidade": "Taió",
        "barragem_id": 2,
    },
    "DCSC-00038": {
        "nome": "Barragem Sul",
        "cidade": "Ituporanga",
        "barragem_id": 1,
    },
}

QUERY = """
query Tags_data {
  tags_data(clients: ["secretaria-de-defesa-civil"]) {
    qualle_meteorologia {
      codigo
      timestamp
      data {
        barramento {
          nivel {
            percentual { value }
            montante { value }
            jusante { value }
            vertido { value }
          }
          capacidade {
            atual { value }
            maxima { value }
          }
        }
      }
    }
  }
}
"""


def pegar(dicionario, *chaves):
    atual = dicionario

    for chave in chaves:
        if atual is None:
            return None

        atual = atual.get(chave)

    return atual


def pegar_value(dicionario, *chaves):
    return pegar(dicionario, *chaves, "value")


def converter_data_hora(valor):
    if not valor:
        return None

    try:
        return datetime.fromisoformat(
            valor.replace("Z", "+00:00")
        )
    except Exception:
        return None


def coletar_barragens():

    response = requests.post(
        URL_GRAPHQL,
        json={"query": QUERY},
        headers={"Content-Type": "application/json"},
        timeout=60,
    )

    response.raise_for_status()

    payload = response.json()

    if payload.get("errors"):
        print(payload["errors"])
        return []

    estacoes = (
        payload
        .get("data", {})
        .get("tags_data", {})
        .get("qualle_meteorologia", [])
    )

    registros = []

    for estacao in estacoes:

        codigo = estacao.get("codigo")

        if codigo not in BARRAGENS:
            continue

        barramento = pegar(
            estacao,
            "data",
            "barramento"
        )

        if not barramento:
            continue

        cfg = BARRAGENS[codigo]

        registros.append({
            "barragem_id": cfg["barragem_id"],
            "codigo_estacao": codigo,
            "data_hora": converter_data_hora(
                estacao.get("timestamp")
            ),
            "capacidade_atual_hm3": pegar_value(
                barramento,
                "capacidade",
                "atual"
            ),
            "capacidade_maxima_hm3": pegar_value(
                barramento,
                "capacidade",
                "maxima"
            ),
            "montante_m": pegar_value(
                barramento,
                "nivel",
                "montante"
            ),
            "jusante_m": pegar_value(
                barramento,
                "nivel",
                "jusante"
            ),
            "nivel_percentual": pegar_value(
                barramento,
                "nivel",
                "percentual"
            ),
            "nivel_vertido_m": pegar_value(
                barramento,
                "nivel",
                "vertido"
            ),
        })

    return registros


def salvar_barragens(registros):

    conn = get_connection()
    cursor = conn.cursor()

    total = 0

    for r in registros:

        cursor.execute("""
            INSERT INTO hidro_leituras_barragens (
                barragem_id,
                codigo_estacao,
                data_hora,
                capacidade_atual_hm3,
                capacidade_maxima_hm3,
                montante_m,
                jusante_m,
                nivel_percentual,
                nivel_vertido_m,
                fonte
            )
            VALUES (
                %s,%s,%s,%s,%s,%s,%s,%s,%s,%s
            )
            ON CONFLICT (
                barragem_id,
                data_hora,
                fonte
            )
            DO UPDATE SET
                codigo_estacao = EXCLUDED.codigo_estacao,
                capacidade_atual_hm3 = EXCLUDED.capacidade_atual_hm3,
                capacidade_maxima_hm3 = EXCLUDED.capacidade_maxima_hm3,
                montante_m = EXCLUDED.montante_m,
                jusante_m = EXCLUDED.jusante_m,
                nivel_percentual = EXCLUDED.nivel_percentual,
                nivel_vertido_m = EXCLUDED.nivel_vertido_m;
        """, (
            r["barragem_id"],
            r["codigo_estacao"],
            r["data_hora"],
            r["capacidade_atual_hm3"],
            r["capacidade_maxima_hm3"],
            r["montante_m"],
            r["jusante_m"],
            r["nivel_percentual"],
            r["nivel_vertido_m"],
            FONTE
        ))

        total += cursor.rowcount

    conn.commit()

    cursor.close()
    conn.close()

    print(f"Registros salvos/atualizados: {total}")


if __name__ == "__main__":

    print("Coletando dados reais das barragens...")

    dados = coletar_barragens()

    for item in dados:
        print(item)

    salvar_barragens(dados)