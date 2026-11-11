import argparse
import json
from pathlib import Path

import rasterio


def obter_asset(dados, id_cena, asset):
    for cena in dados["features"]:
        if cena["id"] == id_cena:
            return cena["assets"][asset]

    raise ValueError(f"Cena nao encontrada nesta pagina: {id_cena}")


def obter_url_asset(dados, id_cena, asset):
    return obter_asset(dados, id_cena, asset)["href"]


def obter_url_visual(dados, id_cena):
    return obter_url_asset(dados, id_cena, "visual")

def inspecionar_raster(url):
    with rasterio.Env(GDAL_HTTP_TIMEOUT="30"):  # noqa: SIM117
        with rasterio.open(url) as raster:
            if raster.crs is None:
                raise ValueError(
                    "O arquivo nao informa seu sistema de coordenadas"
                )

            return {
                "formato": raster.driver,
                "largura_pixels": raster.width,
                "altura_pixels": raster.height,
                "quantidade_bandas": raster.count,
                "tipos_dados": raster.dtypes,
                "sistema_coordenadas": raster.crs.to_string(),
                "resolucao": raster.res,
                "limites": tuple(raster.bounds),
                "valor_nodata": raster.nodata,
            }

if __name__ == "__main__":
    raiz_projeto = Path(__file__).resolve().parent.parent

    parser = argparse.ArgumentParser(
        description="Inspeciona os metadados de uma imagem geografica"
    )

    parser.add_argument(
        "--pagina",
        type=Path,
        required=True,
        help="Arquivo JSON que contem a cena",
    )

    parser.add_argument(
        "--id-cena",
        required=True,
        help="Identificador da cena desejada",
    )

    parser.add_argument(
        "--asset",
        choices=["visual", "scl", "red", "nir"],
        default="visual",
        help="Arquivo a inspecionar: visual, scl, red ou nir",
    )

    argumentos = parser.parse_args()

    arquivo_pagina = (raiz_projeto / argumentos.pagina).resolve()

    dados = json.loads(
        arquivo_pagina.read_text(encoding="utf-8")
    )

    url = obter_url_asset(
        dados,
        argumentos.id_cena,
        argumentos.asset,
    )
    metadados = inspecionar_raster(url)

    print(f"Cena: {argumentos.id_cena}")

    for campo, valor in metadados.items():
        print(f"{campo}: {valor}")