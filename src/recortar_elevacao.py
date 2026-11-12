import argparse
import json
from pathlib import Path

import rasterio

from inspecionar_elevacao import verificar_acesso_https
from inspecionar_raster import inspecionar_raster
from recortar_cena import recortar_cena


def recortar_elevacao(arquivo_pagina, id_item, arquivo_saida):
    arquivo_pagina = Path(arquivo_pagina)
    arquivo_saida = Path(arquivo_saida)

    if arquivo_saida.exists():
        raise FileExistsError(
            f"O arquivo de saida ja existe: {arquivo_saida}"
        )

    pagina = json.loads(
        arquivo_pagina.read_text(encoding="utf-8")
    )

    arquivo_consulta = arquivo_pagina.parent / "consulta.json"

    consulta = json.loads(
        arquivo_consulta.read_text(encoding="utf-8")
    )

    geometria = consulta["criterios"]["intersects"]

    item_encontrado = None

    for item in pagina["features"]:
        if item["id"] == id_item:
            item_encontrado = item
            break

    if item_encontrado is None:
        raise ValueError(f"Item nao encontrado na pagina: {id_item}")

    endereco_s3 = item_encontrado["assets"]["data"]["href"]
    endereco_https, _ = verificar_acesso_https(endereco_s3)

    recortar_cena(
        endereco_https,
        geometria,
        arquivo_saida,
    )

    with rasterio.open(arquivo_saida, "r+") as destino:
        destino.update_tags(
            fonte="Copernicus DEM GLO-30",
            id_item=id_item,
            asset="data",
            endereco_origem=endereco_s3,
            pagina_origem=str(arquivo_pagina.resolve()),
            unidade="meter",
        )

    print(f"Recorte salvo em: {arquivo_saida.resolve()}")

    metadados = inspecionar_raster(arquivo_saida)

    for campo, valor in metadados.items():
        print(f"{campo}: {valor}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Recorta dados de elevacao pelo poligono da consulta"
    )

    parser.add_argument("--pagina", type=Path, required=True)
    parser.add_argument("--id-item", required=True)
    parser.add_argument("--saida", type=Path, required=True)

    argumentos = parser.parse_args()

    recortar_elevacao(
        argumentos.pagina,
        argumentos.id_item,
        argumentos.saida,
    )