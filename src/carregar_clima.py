import json
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

from normalizar_clima import normalizar_temperaturas


def carregar_temperaturas(conexao, registros, arquivo_origem):

    comando_sql = """INSERT INTO silver.temperatura_diaria (
                    data_observacao,
                    latitude,
                    longitude,
                    temperatura_c,
                    fonte,
                    referencia_temporal,
                    arquivo_origem
                )
                VALUES (
                    %(data_observacao)s,
                    %(latitude)s,
                    %(longitude)s,
                    %(temperatura_c)s,
                    %(fonte)s,
                    %(referencia_temporal)s,
                    %(arquivo_origem)s
                )
                ON CONFLICT (
                    data_observacao,
                    latitude,
                    longitude,
                    fonte,
                    referencia_temporal
                )
                DO NOTHING;"""

    linhas = [
        {**registro, "arquivo_origem": arquivo_origem}
        for registro in registros
    ]

    with conexao.cursor() as cursor:
        cursor.executemany(comando_sql, linhas)
        return cursor.rowcount

if __name__ == "__main__":
    raiz_projeto = Path(__file__).resolve().parent.parent
    load_dotenv(raiz_projeto/ ".env")
    
    pasta_raw = raiz_projeto / "data" / "raw" / "nasa_power"
    arquivos = sorted(pasta_raw.glob("*.json"))

    if not arquivos:
        raise FileNotFoundError(f"Nenhum JSON encontrado na pasta {pasta_raw}")

    total_inseridos = 0

    with psycopg.connect(
        host=os.environ["PGHOST"],
        port=int(os.environ["PGPORT"]),
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        connect_timeout=10
    ) as conexao:
        for arquivo_raw in arquivos:
            dados = json.loads(
                arquivo_raw.read_text(encoding="utf-8")
            )

            registros = normalizar_temperaturas(dados)

            inseridos = carregar_temperaturas(
                conexao,
                registros,
                arquivo_raw.name
            )

            total_inseridos += inseridos

    print(f"Carga confirmada: {total_inseridos} novos registros.")
