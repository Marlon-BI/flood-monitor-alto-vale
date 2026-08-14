import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from src.coleta import salvar_barragem_taio


class TestSalvarBarragemTaio(unittest.TestCase):
    def test_buscar_ultima_leitura_filtra_por_barragem_e_fonte(self):
        cursor = MagicMock()
        cursor.fetchone.return_value = (datetime(2026, 8, 14, 7, 0),)

        resultado = salvar_barragem_taio.buscar_ultima_leitura(cursor)

        cursor.execute.assert_called_once()
        sql, params = cursor.execute.call_args[0]
        self.assertIn("MAX(data_hora)", sql)
        self.assertIn("barragem_id = %s", sql)
        self.assertIn("fonte = %s", sql)
        self.assertEqual(params, (salvar_barragem_taio.BARRAGEM_ID, salvar_barragem_taio.FONTE))
        self.assertEqual(resultado, datetime(2026, 8, 14, 7, 0))

    @patch("src.coleta.salvar_barragem_taio.coletar_dados")
    @patch("src.coleta.salvar_barragem_taio.get_connection")
    def test_grava_com_on_conflict_idempotente_e_fonte_correta(self, mock_get_connection, mock_coletar):
        conn = MagicMock()
        cursor = MagicMock()
        cursor.fetchone.return_value = (None,)
        cursor.rowcount = 1
        conn.cursor.return_value = cursor
        mock_get_connection.return_value = conn

        mock_coletar.return_value = [
            {"barragem_id": 2, "codigo_estacao": "TAIO-DC-API", "data_hora": datetime(2026, 8, 14, 7, 0),
             "montante_m": 10.7, "jusante_m": None, "comportas_abertas": 0, "comportas_fechadas": 7,
             "extravasor_m": None, "nivel_percentual": None, "nivel_vertido_m": None, "chuva_mm": 0.0},
        ]

        salvar_barragem_taio.salvar_dados()

        mock_coletar.assert_called_once_with(ultima_leitura_local=None)
        insert_sql, insert_params = cursor.execute.call_args_list[1][0]
        self.assertIn("ON CONFLICT (barragem_id, data_hora, fonte)", insert_sql)
        self.assertIn("DO UPDATE SET", insert_sql)
        self.assertEqual(insert_params[-1], salvar_barragem_taio.FONTE)

        conn.commit.assert_called_once()
        conn.rollback.assert_not_called()
        cursor.close.assert_called_once()
        conn.close.assert_called_once()

    @patch("src.coleta.salvar_barragem_taio.coletar_dados")
    @patch("src.coleta.salvar_barragem_taio.get_connection")
    def test_rollback_e_fecha_conexao_em_erro(self, mock_get_connection, mock_coletar):
        conn = MagicMock()
        cursor = MagicMock()
        cursor.fetchone.return_value = (None,)
        cursor.execute.side_effect = [None, RuntimeError("falha ao inserir")]
        conn.cursor.return_value = cursor
        mock_get_connection.return_value = conn

        mock_coletar.return_value = [
            {"barragem_id": 2, "codigo_estacao": "TAIO-DC-API", "data_hora": datetime(2026, 8, 14, 7, 0),
             "montante_m": 10.7, "jusante_m": None, "comportas_abertas": 0, "comportas_fechadas": 7,
             "extravasor_m": None, "nivel_percentual": None, "nivel_vertido_m": None, "chuva_mm": 0.0},
        ]

        with self.assertRaises(RuntimeError):
            salvar_barragem_taio.salvar_dados()

        conn.rollback.assert_called_once()
        conn.commit.assert_not_called()
        cursor.close.assert_called_once()
        conn.close.assert_called_once()

    @patch("src.coleta.salvar_barragem_taio.coletar_dados")
    @patch("src.coleta.salvar_barragem_taio.get_connection")
    def test_sem_registros_novos_nao_insere_e_ainda_commita(self, mock_get_connection, mock_coletar):
        conn = MagicMock()
        cursor = MagicMock()
        cursor.fetchone.return_value = (datetime(2026, 8, 14, 7, 0),)
        conn.cursor.return_value = cursor
        mock_get_connection.return_value = conn
        mock_coletar.return_value = []

        salvar_barragem_taio.salvar_dados()

        self.assertEqual(cursor.execute.call_count, 1)  # só o SELECT MAX
        conn.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
