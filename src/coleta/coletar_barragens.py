import requests
from src.database.conexao import get_connection


URL_GRAPHQL = "https://monitoramento.defesacivil.sc.gov.br/graphql"

BARRAGENS = {
    "DCSC-00042": "Barragem Norte",
    "DCSC-00040": "Barragem Oeste",
    "DCSC-00038": "Barragem Sul",
}


def get_valor(estacao, chave):
    return estacao.get(f"Data/Barramento/{chave}/Value")


def coletar_barragens():
    query = """
    {
      estacao_getEstacao
    }
    """

    response = requests.post(URL_GRAPHQL, json={"query": query}, timeout=60)
    response.raise_for_status()

    data = response.json()["data"]["estacao_getEstacao"]

    dados = []

    for codigo, nome in BARRAGENS.items():
        estacao = data.get(codigo)

        if not estacao:
            print(f"Barragem não encontrada na API: {codigo}")
            continue

        dados.append({
            "codigo_estacao": codigo,
            "nome": nome,
            "capacidade_atual_hm3": get_valor(estacao, "BarramentoCapacidadeAtual"),
            "capacidade_maxima_hm3": get_valor(estacao, "BarramentoCapacidadeMaxima"),
            "montante_m": get_valor(estacao, "BarramentoNivelMontante"),
            "jusante_m": get_valor(estacao, "BarramentoNivelJusante"),
            "nivel_percentual": get_valor(estacao, "BarramentoNivelPercentual"),
            "nivel_vertido_m": get_valor(estacao, "BarramentoNivelVertido"),
        })

    return dados


def salvar_barragens(dados):
    conn = get_connection()
    cursor = conn.cursor()

    inseridos = 0

    for d in dados:
        cursor.execute("""
            INSERT INTO leituras_barragens (
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
            SELECT
                id,
                %s,
                NOW(),
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                'Defesa Civil SC GraphQL'
            FROM barragens
            WHERE nome = %s
            ON CONFLICT (barragem_id, data_hora, fonte) DO NOTHING;
        """, (
            d["codigo_estacao"],
            d["capacidade_atual_hm3"],
            d["capacidade_maxima_hm3"],
            d["montante_m"],
            d["jusante_m"],
            d["nivel_percentual"],
            d["nivel_vertido_m"],
            d["nome"],
        ))

        inseridos += cursor.rowcount

    conn.commit()
    cursor.close()
    conn.close()

    print(f"Registros inseridos: {inseridos}")


if __name__ == "__main__":
    print("Coletando dados reais das barragens...")
    dados = coletar_barragens()

    for d in dados:
        print(d)

    salvar_barragens(dados)