from datetime import datetime
import time
import requests
import urllib.parse
import base64

from src.database.conexao import get_connection


URL = "https://ciram.epagri.sc.gov.br/agroconnect/busca.jsp"

CHAVE_FIXA = "1A853d23"
LPTYA = "CbkYTPgEQbNLja"

TIMEOUT_SEGUNDOS = 60
PAUSA_ENTRE_REQUISICOES_SEGUNDOS = 2


MUNICIPIOS_BACIA = {
    "Rio do Sul",
    "Agronômica",
    "Aurora",
    "Lontras",
    "Laurentino",
    "Rio do Oeste",
    "Trombudo Central",
    "Agrolândia",
    "Atalanta",
    "Petrolândia",
    "Ituporanga",
    "Chapadão do Lageado",
    "Imbuia",
    "Vidal Ramos",
    "Leoberto Leal",
    "José Boiteux",
    "Taió",
    "Salete",
    "Rio do Campo",
    "Santa Terezinha",
    "Mirim Doce",
    "Pouso Redondo",
    "Benedito Novo",
}


VARIAVEIS_COLETA = [
    {
        "nome_variavel": "Precipitação Total",
        "cd_variavel": 271,
        "grupo": 4,
        "unidade": "mm",
        "janelas": [1, 12, 24],
    },
    {
        "nome_variavel": "Temperatura Instantânea",
        "cd_variavel": 192,
        "grupo": 3,
        "unidade": "°C",
        "janelas": [1],
    },
]


def gerar_keyy() -> str:
    return str(int(time.time() * 1000))[:-5]


def prrtyc(keyy: str) -> str:
    resultado = ""
    indice = 0

    for i in range(0, len(LPTYA), 2):
        resultado += keyy[indice]
        resultado += LPTYA[i:i + 2]
        indice += 1

    resultado += str(indice)
    return resultado


def swtu258(texto: str) -> str:
    texto_decodificado = base64.b64decode(texto).decode("utf-8", errors="ignore")
    return urllib.parse.unquote(texto_decodificado)


def ack3uk(texto: str, keyy: str) -> str:
    separador = prrtyc(keyy)
    posicao = texto.find(separador)

    if posicao == -1:
        raise RuntimeError(f"Separador não encontrado na resposta EPAGRI/CIRAM: {separador}")

    payload = texto[:posicao]
    payload = swtu258(payload)

    chave = CHAVE_FIXA + keyy
    chars = list(payload)

    indice_chave = 0

    for i in range((len(chars) + 1) // 2):
        if indice_chave >= len(chave):
            indice_chave = 0

        esquerda = chr(ord(chars[i]) ^ ord(chave[indice_chave]))
        direita = chr(ord(chars[len(chars) - 1 - i]) ^ ord(chave[indice_chave]))

        chars[i] = direita
        chars[len(chars) - 1 - i] = esquerda

        indice_chave += 1

    return "".join(chars)


def normalizar_float(valor: str) -> float:
    return float(str(valor).strip().replace(",", "."))


def buscar_variavel_epagri(
    nome_variavel: str,
    cd_variavel: int,
    grupo: int,
    unidade: str,
    janela_horas: int,
) -> list[dict]:
    keyy = gerar_keyy()
    hoje = datetime.now().strftime("%d-%m-%Y")

    params = {
        "cd_estacao": "0",
        "cd_cultura": "0",
        "produto": "horario",
        "cd_variavel": str(cd_variavel),
        "grupo": str(grupo),
        "data": hoje,
        "nhoras": str(janela_horas),
        "estado_": "0",
        "tipoEstacao_": "todas",
        "dt": str(int(time.time() * 1000)),
        "date": "5444643225600",
        "idestacao": "Sentinel",
        "ka": keyy,
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://ciram.epagri.sc.gov.br/agroconnect/",
        "X-Requested-With": "XMLHttpRequest",
    }

    response = requests.post(
        URL,
        params=params,
        headers=headers,
        timeout=TIMEOUT_SEGUNDOS,
    )

    response.raise_for_status()

    retorno = ack3uk(response.text.strip(), keyy)

    registros = []

    for linha in retorno.split(";;"):
        linha = linha.strip()

        if not linha:
            continue

        campos = linha.split(",")

        if len(campos) < 9:
            continue

        try:
            codigo_estacao = int("".join(filter(str.isdigit, campos[0])))
            nome_estacao = campos[1].strip()
            longitude = normalizar_float(campos[2])
            latitude = normalizar_float(campos[3])
            valor = normalizar_float(campos[4])
            municipio = campos[5].strip()
            periodo_descricao = campos[6].strip()
            altitude_m = normalizar_float(campos[7])
            proprietario = campos[8].strip().replace("EEagri", "Epagri")
        except Exception as erro:
            print(f"Linha ignorada por erro de parse: {linha} | erro={erro}")
            continue

        if municipio not in MUNICIPIOS_BACIA:
            continue

        registros.append({
            "codigo_estacao": codigo_estacao,
            "nome_estacao": nome_estacao,
            "municipio": municipio,
            "latitude": latitude,
            "longitude": longitude,
            "altitude_m": altitude_m,
            "proprietario": proprietario,
            "nome_variavel": nome_variavel,
            "cd_variavel": cd_variavel,
            "grupo": grupo,
            "janela_horas": janela_horas,
            "valor": valor,
            "unidade": unidade,
            "periodo_descricao": periodo_descricao,
        })

    return registros


def atualizar_estacao(cursor, item: dict) -> None:
    cursor.execute("""
        INSERT INTO public.hidro_estacoes_epagri_ciram (
            codigo_estacao,
            nome_estacao,
            municipio,
            latitude,
            longitude,
            altitude_m,
            proprietario,
            fonte,
            ativa,
            dentro_bacia,
            atualizado_em
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'EPAGRI/CIRAM', TRUE, TRUE, NOW())
        ON CONFLICT (codigo_estacao) DO UPDATE SET
            nome_estacao = EXCLUDED.nome_estacao,
            municipio = EXCLUDED.municipio,
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude,
            altitude_m = EXCLUDED.altitude_m,
            proprietario = EXCLUDED.proprietario,
            ativa = TRUE,
            dentro_bacia = TRUE,
            atualizado_em = NOW();
    """, (
        item["codigo_estacao"],
        item["nome_estacao"],
        item["municipio"],
        item["latitude"],
        item["longitude"],
        item["altitude_m"],
        item["proprietario"],
    ))


def inserir_snapshot_variavel(cursor, item: dict, data_referencia) -> None:
    cursor.execute("""
        INSERT INTO public.hidro_epagri_ciram_snapshot_variaveis (
            codigo_estacao,
            nome_estacao,
            municipio,
            latitude,
            longitude,
            altitude_m,
            proprietario,
            nome_variavel,
            cd_variavel,
            grupo,
            janela_horas,
            valor,
            unidade,
            periodo_descricao,
            data_referencia,
            fonte,
            coletado_em
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'EPAGRI/CIRAM', NOW());
    """, (
        item["codigo_estacao"],
        item["nome_estacao"],
        item["municipio"],
        item["latitude"],
        item["longitude"],
        item["altitude_m"],
        item["proprietario"],
        item["nome_variavel"],
        item["cd_variavel"],
        item["grupo"],
        item["janela_horas"],
        item["valor"],
        item["unidade"],
        item["periodo_descricao"],
        data_referencia,
    ))


def inserir_snapshot_chuva_24h_compatibilidade(cursor, item: dict, data_referencia) -> None:
    if item["nome_variavel"] != "Precipitação Total" or item["janela_horas"] != 24:
        return

    cursor.execute("""
        INSERT INTO public.hidro_chuva_epagri_ciram_snapshot (
            codigo_estacao,
            nome_estacao,
            municipio,
            latitude,
            longitude,
            altitude_m,
            proprietario,
            data_referencia,
            periodo_descricao,
            chuva_24h_mm,
            fonte,
            coletado_em
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'EPAGRI/CIRAM', NOW());
    """, (
        item["codigo_estacao"],
        item["nome_estacao"],
        item["municipio"],
        item["latitude"],
        item["longitude"],
        item["altitude_m"],
        item["proprietario"],
        data_referencia,
        item["periodo_descricao"],
        item["valor"],
    ))


def salvar_no_banco(registros: list[dict]) -> None:
    conn = get_connection()
    cursor = conn.cursor()

    data_referencia = datetime.now().date()

    for item in registros:
        atualizar_estacao(cursor, item)
        inserir_snapshot_variavel(cursor, item, data_referencia)
        inserir_snapshot_chuva_24h_compatibilidade(cursor, item, data_referencia)

    conn.commit()
    cursor.close()
    conn.close()


def executar_coleta() -> None:
    print("Iniciando coleta EPAGRI/CIRAM...")

    todos_registros = []

    for variavel in VARIAVEIS_COLETA:
        for janela_horas in variavel["janelas"]:
            print(
                f"Coletando {variavel['nome_variavel']} "
                f"| janela={janela_horas}h..."
            )

            try:
                registros = buscar_variavel_epagri(
                    nome_variavel=variavel["nome_variavel"],
                    cd_variavel=variavel["cd_variavel"],
                    grupo=variavel["grupo"],
                    unidade=variavel["unidade"],
                    janela_horas=janela_horas,
                )

                print(f"Registros encontrados: {len(registros)}")
                todos_registros.extend(registros)

            except requests.exceptions.RequestException as erro:
                print(
                    f"Erro de rede/API ao coletar "
                    f"{variavel['nome_variavel']} {janela_horas}h: {erro}"
                )

            except Exception as erro:
                print(
                    f"Erro inesperado ao coletar "
                    f"{variavel['nome_variavel']} {janela_horas}h: {erro}"
                )

            time.sleep(PAUSA_ENTRE_REQUISICOES_SEGUNDOS)

    print(f"Total de registros para salvar: {len(todos_registros)}")

    if todos_registros:
        salvar_no_banco(todos_registros)
        print("Coleta EPAGRI/CIRAM salva com sucesso.")
    else:
        print("Nenhum registro encontrado para salvar.")


if __name__ == "__main__":
    executar_coleta()