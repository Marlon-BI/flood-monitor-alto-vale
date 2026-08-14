import unittest
from datetime import datetime
from unittest.mock import patch

from src.coleta import coletar_barragem_ituporanga as mod
from tests.coleta._fixtures import carregar_texto


class TestExtrairRegistros(unittest.TestCase):
    def setUp(self):
        self.html_fixture = carregar_texto("ituporanga", "nivel_rio.html")

    def test_extrai_todas_as_linhas_de_dados_da_fixture(self):
        registros = mod.extrair_registros(self.html_fixture)
        self.assertEqual(len(registros), 5)

    def test_casa_colunas_pelo_cabecalho_nao_por_indice(self):
        registros = mod.extrair_registros(self.html_fixture)
        mais_recente = max(registros, key=lambda r: r["data_hora"])

        self.assertEqual(mais_recente["data_hora"], datetime(2026, 8, 13, 7, 0))
        self.assertEqual(mais_recente["montante_m"], 18.7)
        self.assertEqual(mais_recente["jusante_m"], 1.0)
        self.assertEqual(mais_recente["comportas_abertas"], 0)
        self.assertEqual(mais_recente["comportas_fechadas"], 5)

    def test_numeros_com_virgula_decimal_sao_convertidos(self):
        registros = mod.extrair_registros(self.html_fixture)
        alvo = next(r for r in registros if r["data_hora"] == datetime(2026, 8, 12, 17, 0))
        self.assertAlmostEqual(alvo["jusante_m"], 2.67)

    def test_html_sem_tabela_esperada_devolve_lista_vazia(self):
        registros = mod.extrair_registros("<html><body><p>sem tabela</p></body></html>")
        self.assertEqual(registros, [])

    def test_barragem_id_fixo_igual_ao_usado_em_coletar_barragens(self):
        registros = mod.extrair_registros(self.html_fixture)
        self.assertTrue(all(r["barragem_id"] == mod.BARRAGEM_ID for r in registros))
        self.assertEqual(mod.BARRAGEM_ID, 1)


class TestColetarDados(unittest.TestCase):
    def setUp(self):
        self.html_fixture = carregar_texto("ituporanga", "nivel_rio.html")

    @patch("src.coleta.coletar_barragem_ituporanga._buscar_html")
    def test_sem_leitura_anterior_devolve_todos_os_registros(self, mock_buscar):
        mock_buscar.return_value = self.html_fixture

        dados = mod.coletar_dados(ultima_leitura_local=None)

        self.assertEqual(len(dados), 5)

    @patch("src.coleta.coletar_barragem_ituporanga._buscar_html")
    def test_filtra_apenas_registros_mais_novos_que_ultima_leitura(self, mock_buscar):
        mock_buscar.return_value = self.html_fixture

        ultima_leitura = datetime(2026, 8, 12, 7, 0)
        dados = mod.coletar_dados(ultima_leitura_local=ultima_leitura)

        self.assertTrue(all(d["data_hora"] > ultima_leitura for d in dados))
        self.assertEqual(len(dados), 2)

    @patch("src.coleta.coletar_barragem_ituporanga._buscar_html")
    def test_registros_ordenados_ascendente(self, mock_buscar):
        mock_buscar.return_value = self.html_fixture

        dados = mod.coletar_dados()

        datas = [d["data_hora"] for d in dados]
        self.assertEqual(datas, sorted(datas))

    @patch("src.coleta.coletar_barragem_ituporanga.coletar_dados")
    def test_main_imprime_dados_sem_acessar_site_real(self, mock_coletar_dados):
        mock_coletar_dados.return_value = [
            {"barragem_id": 1, "data_hora": datetime(2026, 8, 13, 7, 0), "montante_m": 18.7,
             "jusante_m": 1.0, "comportas_abertas": 0, "comportas_fechadas": 5,
             "extravasor_m": 0.0, "nivel_vertido_m": 0.0, "codigo_estacao": "ITUPORANGA-NIVELRIO",
             "nivel_percentual": None, "chuva_mm": None},
        ]

        mod.main()

        mock_coletar_dados.assert_called_once_with()


class TestRequestsComRetry(unittest.TestCase):
    @patch("src.coleta.coletar_barragem_ituporanga.time.sleep")
    @patch("src.coleta.coletar_barragem_ituporanga.requests.get")
    def test_falha_em_todas_tentativas_levanta_erro_especifico(self, mock_get, mock_sleep):
        import requests
        mock_get.side_effect = requests.ConnectionError("timeout simulado")

        with self.assertRaises(mod.ItuporangaColetaError):
            mod._buscar_html()

        self.assertEqual(mock_get.call_count, mod.TENTATIVAS)

    @patch("src.coleta.coletar_barragem_ituporanga.time.sleep")
    @patch("src.coleta.coletar_barragem_ituporanga.requests.get")
    def test_recupera_apos_falha_temporaria(self, mock_get, mock_sleep):
        import requests
        from unittest.mock import MagicMock

        resposta_ok = MagicMock()
        resposta_ok.text = "<html>ok</html>"
        resposta_ok.raise_for_status.return_value = None

        mock_get.side_effect = [requests.ConnectionError("falha temporaria"), resposta_ok]

        resultado = mod._buscar_html()

        self.assertEqual(resultado, "<html>ok</html>")
        self.assertEqual(mock_get.call_count, 2)


if __name__ == "__main__":
    unittest.main()
