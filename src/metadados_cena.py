import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def obter_data_cena_utc(dados, id_cena):
    cenas_encontradas = [
        cena
        for cena in dados["features"]
        if cena["id"] == id_cena
    ]

    if len(cenas_encontradas) != 1:
        raise ValueError(
            f"Era esperada uma cena com o identificador: {id_cena}"
        )

    propriedades = cenas_encontradas[0]["properties"]
    data_hora = propriedades.get("datetime")

    if not isinstance(data_hora, str) or not data_hora:
        raise ValueError("A cena nao informa uma data de observacao")

    try:
        instante = datetime.fromisoformat(data_hora)
    except ValueError as erro:
        raise ValueError(
            f"Data de observacao invalida: {data_hora}"
        ) from erro

    if instante.tzinfo is None or instante.utcoffset() is None:
        raise ValueError("A data da cena precisa informar o fuso horario")

    return instante.astimezone(timezone.utc).date()  # noqa: UP017


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Consulta a data UTC de uma cena no catalogo"
    )

    parser.add_argument("--pagina", type=Path, required=True)
    parser.add_argument("--id-cena", required=True)

    argumentos = parser.parse_args()

    dados = json.loads(
        argumentos.pagina.read_text(encoding="utf-8")
    )

    data_cena = obter_data_cena_utc(
        dados,
        argumentos.id_cena,
    )

    print(f"Cena: {argumentos.id_cena}")
    print(f"Data de observacao UTC: {data_cena.isoformat()}")