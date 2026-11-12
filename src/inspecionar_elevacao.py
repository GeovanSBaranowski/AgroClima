import argparse
import json
from pathlib import Path
from urllib.parse import urlparse

import requests

from inspecionar_raster import inspecionar_raster


def inspecionar_pagina(arquivo_pagina):
    dados = json.loads(
        arquivo_pagina.read_text(encoding="utf-8")
    )

    if dados.get("type") != "FeatureCollection":
        raise ValueError("A pagina precisa ser uma FeatureCollection")

    for item in dados["features"]:
        asset = item["assets"]["data"]

        print(f"Identificador: {item['id']}")
        print(f"Tipo do arquivo: {asset.get('type')}")
        print(f"Endereco: {asset.get('href')}")
        print(f"Metadados das bandas: {asset.get('raster:bands')}")
        print()

        endereco_https, status = verificar_acesso_https(asset["href"])

        print(f"Endereco HTTPS: {endereco_https}")
        print(f"Status HTTPS: {status}")

        metadados_raster = inspecionar_raster(endereco_https)

        print("Informacoes do raster:")

        for campo, valor in metadados_raster.items():
            print(f"  {campo}: {valor}")


def verificar_acesso_https(endereco_s3):
    partes = urlparse(endereco_s3)

    if partes.scheme != "s3" or partes.netloc != "copernicus-dem-30m":
        raise ValueError("Endereco nao pertence ao bucket esperado")

    endereco_https = (
        "https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com"
        f"{partes.path}"
    )

    resposta = requests.head(
        endereco_https,
        timeout=30,
        allow_redirects=True,
    )
    resposta.raise_for_status()

    return endereco_https, resposta.status_code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Inspeciona uma pagina da consulta de elevacao"
    )

    parser.add_argument(
        "--pagina",
        type=Path,
        required=True,
        help="Pagina JSON salva pela consulta",
    )

    argumentos = parser.parse_args()

    inspecionar_pagina(argumentos.pagina)