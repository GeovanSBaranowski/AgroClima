import argparse
import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import geometry_mask, geometry_window
from rasterio.warp import transform_geom


def avaliar_mosaico_ndvi(arquivo_raster, geometria_lonlat):
    with rasterio.open(arquivo_raster) as origem:
        if origem.crs is None:
            raise ValueError("O raster precisa informar suas coordenadas")

        if origem.count != 1 or origem.dtypes != ("float32",):
            raise ValueError("O NDVI precisa ter uma banda float32")

        geometria = transform_geom(
            "EPSG:4326",
            origem.crs,
            geometria_lonlat,
        )

        janela = geometry_window(
            origem,
            [geometria],
            boundless=True,
        )

        dados = origem.read(
            1,
            window=janela,
            boundless=True,
            masked=True,
            fill_value=0,
        )

        dentro_poligono = geometry_mask(
            [geometria],
            out_shape=dados.shape,
            transform=origem.window_transform(janela),
            all_touched=False,
            invert=True,
        )

    valores = np.ma.getdata(dados)
    validos = (
        dentro_poligono
        & ~np.ma.getmaskarray(dados)
        & np.isfinite(valores)
    )

    esperados = int(np.count_nonzero(dentro_poligono))
    com_ndvi = int(np.count_nonzero(validos))

    if esperados == 0:
        raise ValueError("O poligono nao selecionou pixels")

    if com_ndvi == 0:
        raise ValueError("Nao ha pixels validos de NDVI no poligono")

    fora_intervalo = int(
        np.count_nonzero(
            validos & ((valores < -1) | (valores > 1))
        )
    )

    return {
        "pixels_esperados": esperados,
        "pixels_com_ndvi": com_ndvi,
        "pixels_sem_ndvi": esperados - com_ndvi,
        "cobertura_percentual": com_ndvi / esperados * 100,
        "fora_intervalo": fora_intervalo,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Avalia a cobertura de um mosaico NDVI"
    )

    parser.add_argument("--raster", type=Path, required=True)
    parser.add_argument("--consulta", type=Path, required=True)

    argumentos = parser.parse_args()

    consulta = json.loads(
        argumentos.consulta.read_text(encoding="utf-8")
    )

    geometria = consulta["criterios"]["intersects"]

    resumo = avaliar_mosaico_ndvi(
        argumentos.raster,
        geometria,
    )

    print(f"Pixels esperados: {resumo['pixels_esperados']}")
    print(f"Pixels com NDVI: {resumo['pixels_com_ndvi']}")
    print(f"Pixels sem NDVI: {resumo['pixels_sem_ndvi']}")
    print(f"Cobertura: {resumo['cobertura_percentual']:.4f}%")
    print(f"Fora de [-1, 1]: {resumo['fora_intervalo']}")