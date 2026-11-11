import argparse
import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.mask import mask
from rasterio.warp import transform_geom

from inspecionar_raster import inspecionar_raster, obter_url_asset
from metadados_espectrais import obter_metadados_banda


def recortar_cena(
    url,
    geometria_lonlat,
    arquivo_saida,
    *,
    metadados_espectrais=None,
):
    with rasterio.Env(
        GDAL_HTTP_TIMEOUT="60",
        GDAL_TIFF_INTERNAL_MASK=True,
    ):
        with rasterio.open(url) as origem:
            if origem.crs is None:
                raise ValueError(
                    "A imagem nao informa seu sistema de coordenadas"
                )

            if metadados_espectrais is not None:
                if (
                    origem.count != 1
                    or origem.dtypes != (metadados_espectrais["tipo_dados"],)
                ):
                    raise ValueError(
                        "A banda nao corresponde ao tipo informado no catalogo"
                    )

                if origem.nodata != metadados_espectrais["nodata"]:
                    raise ValueError(
                        "O nodata da banda difere do informado no catalogo"
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

            if metadados_espectrais is not None:
                destino.update_tags(
                    stac_id_cena=metadados_espectrais["id_cena"],
                    stac_asset=metadados_espectrais["asset"],
                    stac_scale=str(metadados_espectrais["escala"]),
                    stac_offset=str(
                        metadados_espectrais["deslocamento"]
                    ),
                    stac_nodata=str(metadados_espectrais["nodata"]),
                    stac_data_type=metadados_espectrais["tipo_dados"],
                    stac_pagina=metadados_espectrais["pagina_origem"],
                    stac_url=metadados_espectrais["url"],
                )


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
        choices=["visual", "scl", "red", "nir"],
        default="visual",
        help="Arquivo da cena a recortar: visual, scl, red ou nir",
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

    metadados_espectrais = None

    if argumentos.asset in ("red", "nir"):
        metadados_espectrais = obter_metadados_banda(
            dados_pagina,
            argumentos.id_cena,
            argumentos.asset,
        )

        metadados_espectrais["pagina_origem"] = str(arquivo_pagina)
        url = metadados_espectrais["url"]
    else:
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
        nome_arquivo = (
            f"{argumentos.id_cena}_{argumentos.asset}_chapeco.tif"
        )

    arquivo_saida = pasta_saida / nome_arquivo

    recortar_cena(
        url,
        geometria,
        arquivo_saida,
        metadados_espectrais=metadados_espectrais,
    )

    print(f"Recorte salvo em: {arquivo_saida}")

    metadados = inspecionar_raster(arquivo_saida)

    for campo, valor in metadados.items():
        print(f"{campo}: {valor}")

    if metadados_espectrais is not None:
        with rasterio.open(arquivo_saida) as banda_recortada:
            tags = banda_recortada.tags()

        print("Metadados gravados:")

        for campo in (
            "stac_id_cena",
            "stac_asset",
            "stac_scale",
            "stac_offset",
            "stac_nodata",
            "stac_pagina",
        ):
            print(f"{campo}: {tags[campo]}")