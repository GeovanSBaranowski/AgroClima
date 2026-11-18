import argparse
import math
from pathlib import Path

import numpy as np
import rasterio
from rasterio.warp import transform
from rasterio.windows import Window

from configuracao import LATITUDE_REFERENCIA, LONGITUDE_REFERENCIA


def consultar_raster_ponto(arquivo_raster, latitude, longitude):
    with rasterio.open(arquivo_raster) as origem:
        if origem.crs is None:
            raise ValueError("O raster precisa informar suas coordenadas")

        if origem.count != 1:
            raise ValueError("A consulta espera um raster de uma banda")

        # As coordenadas recebidas estao em longitude e latitude.
        coordenadas_x, coordenadas_y = transform(
            "EPSG:4326",
            origem.crs,
            [longitude],
            [latitude],
        )

        linha, coluna = origem.index(
            coordenadas_x[0],
            coordenadas_y[0],
        )

        if not (
            0 <= linha < origem.height
            and 0 <= coluna < origem.width
        ):
            return None

        janela = Window(coluna, linha, 1, 1)

        pixel = origem.read(
            1,
            window=janela,
            masked=True,
        )[0, 0]

        if np.ma.is_masked(pixel):
            return None

        valor = float(pixel)

        if not math.isfinite(valor):
            return None

        return valor


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Consulta um raster no ponto de referencia"
    )

    parser.add_argument(
        "--raster",
        type=Path,
        required=True,
        help="Arquivo raster com uma banda",
    )

    argumentos = parser.parse_args()

    valor = consultar_raster_ponto(
        argumentos.raster,
        latitude=LATITUDE_REFERENCIA,
        longitude=LONGITUDE_REFERENCIA,
    )

    print(
        f"Ponto consultado: latitude {LATITUDE_REFERENCIA}, "
        f"longitude {LONGITUDE_REFERENCIA}"
    )

    if valor is None:
        print("Valor indisponivel no ponto.")
    else:
        print(f"Valor encontrado: {valor:.4f}")