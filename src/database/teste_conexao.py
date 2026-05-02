from src.database.conexao import get_connection

try:
    conn = get_connection()
    print("Conectado com sucesso!")
    conn.close()
except Exception as e:
    print("Erro ao conectar:", e)