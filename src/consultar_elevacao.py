import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

from consultar_satelite import coletar_paginas


def consultar_colecao():
    url = (
        "https://earth-search.aws.element84.com/v1/"
        "collections/cop-dem-glo-30"
    )

    resposta = requests.get(url, timeout=30)
    resposta.raise_for_status()

    return resposta.json()


def buscar_elevacao(geometria):
    url = "https://earth-search.aws.element84.com/v1/search"

    criterios = {
        "collections": ["cop-dem-glo-30"],
        "intersects": geometria,
        "limit": 10,
    }

    resposta = requests.post(
        url,
        json=criterios,
        timeout=30,
    )
    resposta.raise_for_status()

    return resposta.json()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Consulta dados de elevacao para uma area"
    )

    parser.add_argument(
        "--consulta",
        type=Path,
        required=True,
        help="Arquivo consulta.json com o poligono da area",
    )

    argumentos = parser.parse_args()

    consulta_original = json.loads(
        argumentos.consulta.read_text(encoding="utf-8")
    )

    geometria = consulta_original["criterios"]["intersects"]

    url = "https://earth-search.aws.element84.com/v1/search"

    criterios = {
        "collections": ["cop-dem-glo-30"],
        "intersects": geometria,
        "limit": 10,
    }

    instante_coleta = datetime.now(timezone.utc)  # noqa: UP017
    identificador = instante_coleta.strftime("%Y%m%dT%H%M%S%fZ")

    raiz_projeto = Path(__file__).resolve().parent.parent

    pasta_execucao = (
        raiz_projeto
        / "data"
        / "raw"
        / "copernicus_dem"
        / identificador
    )

    pasta_execucao.mkdir(parents=True, exist_ok=True)

    registro_consulta = {
        "coletado_em": instante_coleta.isoformat(),
        "endpoint": url,
        "metodo": "POST",
        "consulta_origem": str(argumentos.consulta),
        "criterios": criterios,
    }

    arquivo_consulta = pasta_execucao / "consulta.json"

    arquivo_consulta.write_text(
        json.dumps(
            registro_consulta,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Consulta salva em: {arquivo_consulta}")

    total_itens = coletar_paginas(
        url,
        criterios,
        pasta_execucao,
    )

    print(f"Coleta concluida: {total_itens} itens de elevacao.")
    print(f"Paginas salvas em: {pasta_execucao}")