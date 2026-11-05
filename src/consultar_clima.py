import argparse
import os
from datetime import date
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

from configuracao import LATITUDE_REFERENCIA, LONGITUDE_REFERENCIA


def consultar_observacoes(
    conexao,
    data_observacao,
    latitude,
    longitude,
):
    comando_sql = """
        SELECT
            data_observacao,
            variavel,
            valor,
            unidade,
            fonte,
            referencia_temporal
        FROM silver.observacao_meteorologica_diaria
        WHERE data_observacao = %(data_observacao)s
          AND latitude = %(latitude)s
          AND longitude = %(longitude)s
          AND fonte = 'NASA_POWER'
          AND referencia_temporal = 'UTC'
        ORDER BY variavel;
    """

    parametros = {
        "data_observacao": data_observacao,
        "latitude": latitude,
        "longitude": longitude,
    }

    with conexao.cursor(row_factory=dict_row) as cursor:
        cursor.execute(comando_sql, parametros)
        return cursor.fetchall()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Consulta observacoes meteorologicas de Chapeco"
    )

    parser.add_argument(
        "--data",
        type=date.fromisoformat,
        required=True,
        help="Data da observacao, por exemplo: 2024-02-01",
    )

    argumentos = parser.parse_args()

    raiz_projeto = Path(__file__).resolve().parent.parent
    load_dotenv(raiz_projeto / ".env")

    with psycopg.connect(
        host=os.environ["PGHOST"],
        port=int(os.environ["PGPORT"]),
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        connect_timeout=10,
    ) as conexao:
        registros = consultar_observacoes(
            conexao,
            data_observacao=argumentos.data,
            latitude=LATITUDE_REFERENCIA,
            longitude=LONGITUDE_REFERENCIA,
        )

    print(f"Observacoes encontradas: {len(registros)}")

    for registro in registros:
        print(registro)