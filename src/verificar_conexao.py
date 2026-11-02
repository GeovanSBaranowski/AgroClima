import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

raiz_projeto = Path(__file__).resolve().parent.parent
load_dotenv(raiz_projeto / ".env")

print(
    "Destino:",
    repr(os.environ["PGHOST"]),
    repr(os.environ["PGPORT"]),
    repr(os.environ["PGDATABASE"]),
)

with psycopg.connect(
    host=os.environ["PGHOST"],
    port=int(os.environ["PGPORT"]),
    dbname=os.environ["PGDATABASE"],
    user=os.environ["PGUSER"],
    password=os.environ["PGPASSWORD"],
    connect_timeout=10,
) as conexao, conexao.cursor() as cursor:
    cursor.execute("SELECT current_database(), current_user;")
    resultado = cursor.fetchone()

    print(resultado)