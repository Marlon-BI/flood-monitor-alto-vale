from datetime import datetime
import requests
from bs4 import BeautifulSoup

URL = "https://defesacivil.riodosul.sc.gov.br/index.php?r=externo/metragem"


def converter_data(data_str):
    # Exemplo: '02/05 09H'
    data_str = data_str.replace("H", "")

    ano_atual = datetime.now().year
    data_completa = f"{data_str}/{ano_atual}"

    return datetime.strptime(data_completa, "%d/%m %H/%Y")


def to_float(valor):
    try:
        return float(valor.replace(",", "."))
    except:
        return None


def coletar_dados():
    response = requests.get(URL)

    soup = BeautifulSoup(response.text, "html.parser")

    tabela = soup.find("table")
    linhas = tabela.find_all("tr")

    dados = []

    for linha in linhas[1:]:
        colunas = linha.find_all("td")

        if len(colunas) >= 4:
            dados.append({
                "data_hora": converter_data(colunas[0].text.strip()),
                "nivel_metros": to_float(colunas[1].text.strip()),
                "variacao": to_float(colunas[2].text.strip()),
                "chuva_mm": to_float(colunas[3].text.strip())
            })

    return dados


if __name__ == "__main__":
    dados = coletar_dados()

    print("\n=== DADOS TRATADOS ===\n")

    for d in dados[:5]:
        print(d)