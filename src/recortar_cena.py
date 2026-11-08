import argparse
import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.mask import mask
from rasterio.warp import transform_geom

from inspecionar_raster import inspecionar_raster, obter_url_asset


def recortar_cena(url, geometria_lonlat, arquivo_saida):
    with rasterio.Env(
        GDAL_HTTP_TIMEOUT="60",
        GDAL_TIFF_INTERNAL_MASK=True,
    ):
        with rasterio.open(url) as origem:
            if origem.crs is None:
                raise ValueError(
                    "A imagem nao informa seu sistema de coordenadas"
                )

            geometria_projetada = transform_geom(
                "EPSG:4326",
                origem.crs,
                geometria_lonlat,
            )

            imagem, transformacao = mask(
                origem,
                [geometria_projetada],
                crop=True,
                filled=False,
            )

            perfil = origem.profile.copy()

            perfil.update(
                driver="GTiff",
                height=imagem.shape[1],
                width=imagem.shape[2],
                transform=transformacao,
                nodata=None,
                compress="deflate",
            )

        mascaras_bandas = np.ma.getmaskarray(imagem)
        pixels_invalidos = mascaras_bandas.any(axis=0)
        pixels_validos = ~pixels_invalidos

        if not pixels_validos.any():
            raise ValueError("O recorte nao possui pixels validos")

        arquivo_saida.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with rasterio.open(
            arquivo_saida,
            "w",
            **perfil,
        ) as destino:
            destino.write(imagem.filled(0))
            destino.write_mask(pixels_validos)


if __name__ == "__main__":
    raiz_projeto = Path(__file__).resolve().parent.parent

    parser = argparse.ArgumentParser(
        description="Recorta uma cena pelo poligono da consulta"
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
        choices=["visual", "scl"],
        default="visual",
        help="Arquivo da cena a recortar: visual ou scl",
    )

    argumentos = parser.parse_args()

    arquivo_pagina = (
        raiz_projeto / argumentos.pagina
    ).resolve()

    arquivo_consulta = arquivo_pagina.parent / "consulta.json"

    dados_pagina = json.loads(
        arquivo_pagina.read_text(encoding="utf-8")
    )

    dados_consulta = json.loads(
        arquivo_consulta.read_text(encoding="utf-8")
    )

    url = obter_url_asset(
        dados_pagina,
        argumentos.id_cena,
        argumentos.asset,
    )

    geometria = dados_consulta["criterios"]["intersects"]

    pasta_saida = (
        raiz_projeto
        / "data"
        / "processed"
        / "sentinel2"
        / arquivo_pagina.parent.name
    )

    if argumentos.asset == "visual":
        nome_arquivo = f"{argumentos.id_cena}_chapeco.tif"
    else:
        nome_arquivo = f"{argumentos.id_cena}_scl_chapeco.tif"

    arquivo_saida = pasta_saida / nome_arquivo

    recortar_cena(
        url,
        geometria,
        arquivo_saida,
    )

    print(f"Recorte salvo em: {arquivo_saida}")

    metadados = inspecionar_raster(arquivo_saida)

    for campo, valor in metadados.items():
        print(f"{campo}: {valor}")