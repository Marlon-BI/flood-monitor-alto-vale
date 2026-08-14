import unittest
from datetime import datetime
from unittest.mock import patch

from src.coleta import coletar_barragem_taio
from tests.coleta._fixtures import carregar_json


class TestColetarBarragemTaio(unittest.TestCase):
    def setUp(self):
        self.payload_fixture = carregar_json("uniparking", "taio_historico.json")

    @patch("src.coleta.coletar_barragem_taio.cliente.buscar_historico")
    def test_sem_leitura_anterior_devolve_todos_os_registros_da_fixture(self, mock_buscar):
        mock_buscar.return_value = self.payload_fixture

        dados = coletar_barragem_taio.coletar_dados(ultima_leitura_local=None)

        self.assertEqual(len(dados), len(self.payload_fixture))

    @patch("src.coleta.coletar_barragem_taio.cliente.buscar_historico")
    def test_registros_ordenados_ascendente_por_data_hora(self, mock_buscar):
        mock_buscar.return_value = self.payload_fixture

        dados = coletar_barragem_taio.coletar_dados(ultima_leitura_local=None)

        datas = [d["data_hora"] for d in dados]
        self.assertEqual(datas, sorted(datas))

    @patch("src.coleta.coletar_barragem_taio.cliente.buscar_historico")
    def test_filtra_apenas_registros_mais_novos_que_ultima_leitura(self, mock_buscar):
        mock_buscar.return_value = self.payload_fixture

        ultima_leitura = datetime(2026, 8, 13, 12, 0, 0)
        dados = coletar_barragem_taio.coletar_dados(ultima_leitura_local=ultima_leitura)

        self.assertTrue(all(d["data_hora"] > ultima_leitura for d in dados))
        self.assertLess(len(dados), len(self.payload_fixture))

    @patch("src.coleta.coletar_barragem_taio.cliente.buscar_historico")
    def test_comportas_abertas_fechadas_vem_separadas_e_como_inteiro(self, mock_buscar):
        mock_buscar.return_value = self.payload_fixture

        dados = coletar_barragem_taio.coletar_dados()

        for d in dados:
            self.assertIsInstance(d["comportas_abertas"], int)
            self.assertIsInstance(d["comportas_fechadas"], int)

    @patch("src.coleta.coletar_barragem_taio.cliente.buscar_historico")
    def test_jusante_vazio_vira_none_nao_zero(self, mock_buscar):
        mock_buscar.return_value = [
            {"data": "2026-08-14T07:01:28", "montante": "10.7", "jusante": "",
             "comportaAberta": "0", "comportaFechada": "7", "chuva": "0.0"}
        ]

        dados = coletar_barragem_taio.coletar_dados()

        self.assertIsNone(dados[0]["jusante_m"])
        self.assertNotEqual(dados[0]["jusante_m"], 0)

    @patch("src.coleta.coletar_barragem_taio.cliente.buscar_historico")
    def test_registro_sem_campo_data_e_descartado(self, mock_buscar):
        mock_buscar.return_value = [
            {"montante": "10.7", "jusante": "", "comportaAberta": "0", "comportaFechada": "7"},
        ]

        dados = coletar_barragem_taio.coletar_dados()

        self.assertEqual(dados, [])

    @patch("src.coleta.coletar_barragem_taio.cliente.buscar_historico")
    def test_barragem_id_fixo_igual_ao_usado_em_coletar_barragens(self, mock_buscar):
        mock_buscar.return_value = self.payload_fixture

        dados = coletar_barragem_taio.coletar_dados()

        self.assertTrue(all(d["barragem_id"] == coletar_barragem_taio.BARRAGEM_ID for d in dados))
        self.assertEqual(coletar_barragem_taio.BARRAGEM_ID, 2)

    @patch("src.coleta.coletar_barragem_taio.coletar_dados")
    def test_main_imprime_dados_sem_acessar_api_real(self, mock_coletar_dados):
        mock_coletar_dados.return_value = [
            {"barragem_id": 2, "data_hora": datetime(2026, 8, 14, 7, 0), "montante_m": 10.7,
             "jusante_m": None, "comportas_abertas": 0, "comportas_fechadas": 7,
             "chuva_mm": 0.0, "codigo_estacao": "TAIO-DC-API", "extravasor_m": None,
             "nivel_percentual": None, "nivel_vertido_m": None},
        ]

        coletar_barragem_taio.main()

        mock_coletar_dados.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
