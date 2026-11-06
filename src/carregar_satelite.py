import argparse
import json
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

from normalizar_satelite import normalizar_cenas


def carregar_cenas(conexao, registros, arquivo_origem):
    if not registros:
        return 0

    comando_sql = """
        INSERT INTO silver.cena_satelite (
            colecao,
            id_cena,
            data_hora_observacao,
            plataforma,
            nuvens_cena_percentual,
            url_visual,
            url_classificacao,
            arquivo_origem
        )
        VALUES (
            %(colecao)s,
            %(id_cena)s,
            %(data_hora_observacao)s,
            %(plataforma)s,
            %(nuvens_cena_percentual)s,
            %(url_visual)s,
            %(url_classificacao)s,
            %(arquivo_origem)s
        )
        ON CONFLICT (colecao, id_cena)
        DO NOTHING;
    """

    linhas = [
        {**registro, "arquivo_origem": arquivo_origem}
        for registro in registros
    ]

    with conexao.cursor() as cursor:
        cursor.executemany(comando_sql, linhas)
        return cursor.rowcount


if __name__ == "__main__":
    raiz_projeto = Path(__file__).resolve().parent.parent

    parser = argparse.ArgumentParser(
        description="Carrega metadados de cenas no PostgreSQL"
    )

    parser.add_argument(
        "--pasta",
        type=Path,
        required=True,
        help="Pasta da consulta, dentro do projeto",
    )

    argumentos = parser.parse_args()

    pasta_execucao = (raiz_projeto / argumentos.pasta).resolve()

    if not pasta_execucao.is_dir():
        raise FileNotFoundError(
            f"Pasta nao encontrada: {pasta_execucao}"
        )

    if not pasta_execucao.is_relative_to(raiz_projeto):
        raise ValueError(
            "A pasta da consulta precisa estar dentro do projeto"
        )

    arquivos = sorted(pasta_execucao.glob("pagina_*.json"))

    if not arquivos:
        raise FileNotFoundError(
            f"Nenhuma pagina encontrada em {pasta_execucao}"
        )

    load_dotenv(raiz_projeto / ".env")

    total_inseridos = 0

    with psycopg.connect(
        host=os.environ["PGHOST"],
        port=int(os.environ["PGPORT"]),
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        connect_timeout=10,
    ) as conexao:
        for arquivo_raw in arquivos:
            dados = json.loads(
                arquivo_raw.read_text(encoding="utf-8")
            )

            registros = normalizar_cenas(dados)

            arquivo_origem = arquivo_raw.relative_to(
                raiz_projeto
            ).as_posix()

            inseridos = carregar_cenas(
                conexao,
                registros,
                arquivo_origem,
            )

            total_inseridos += inseridos

    print(f"Carga confirmada: {total_inseridos} novas cenas.")