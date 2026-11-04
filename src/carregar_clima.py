import json
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

from normalizar_clima import normalizar_observacoes


def carregar_observacoes(conexao, registros, arquivo_origem):

    comando_sql = """INSERT INTO silver.observacao_meteorologica_diaria (
                    data_observacao,
                    latitude,
                    longitude,
                    variavel,
                    valor,
                    unidade,
                    fonte,
                    referencia_temporal,
                    arquivo_origem
                )
                VALUES (
                    %(data_observacao)s,
                    %(latitude)s,
                    %(longitude)s,
                    %(variavel)s,
                    %(valor)s,
                    %(unidade)s,
                    %(fonte)s,
                    %(referencia_temporal)s,
                    %(arquivo_origem)s
                )
                ON CONFLICT (
                    data_observacao,
                    latitude,
                    longitude,
                    variavel,
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

            registros = normalizar_observacoes(dados)

            inseridos = carregar_observacoes(
                conexao,
                registros,
                arquivo_raw.name
            )

            total_inseridos += inseridos

    print(f"Carga confirmada: {total_inseridos} novos registros.")
