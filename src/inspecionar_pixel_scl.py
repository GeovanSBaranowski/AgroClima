import argparse
from pathlib import Path

import numpy as np
import rasterio
from rasterio.windows import Window


def inspecionar_pixel(arquivo_banda, arquivo_scl, linha, coluna):
    with (
        rasterio.open(arquivo_banda) as banda,
        rasterio.open(arquivo_scl) as scl,
    ):
        if banda.crs is None or banda.crs != scl.crs:
            raise ValueError(
                "Os arquivos precisam usar o mesmo sistema de coordenadas"
            )

        if not (0 <= linha < banda.height and 0 <= coluna < banda.width):
            raise ValueError("A posicao informada esta fora da banda")

        x, y = banda.xy(linha, coluna)

        linha_scl, coluna_scl = scl.index(x, y)

        if not (
            0 <= linha_scl < scl.height
            and 0 <= coluna_scl < scl.width
        ):
            raise ValueError("A posicao esta fora do arquivo SCL")

        janela = Window(coluna_scl, linha_scl, 1, 1)
        valor = scl.read(1, window=janela, masked=True)[0, 0]

        print(f"Coordenadas do centro: {x:.2f}, {y:.2f}")
        print(f"Posicao na SCL: linha {linha_scl}, coluna {coluna_scl}")

        if np.ma.is_masked(valor):
            print("Classificacao SCL: sem dados nessa posicao")
        else:
            print(f"Codigo SCL: {int(valor)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Consulta a classe SCL na posicao de um pixel"
    )

    parser.add_argument("--banda", type=Path, required=True)
    parser.add_argument("--scl", type=Path, required=True)
    parser.add_argument("--linha", type=int, required=True)
    parser.add_argument("--coluna", type=int, required=True)

    argumentos = parser.parse_args()

    inspecionar_pixel(
        argumentos.banda,
        argumentos.scl,
        argumentos.linha,
        argumentos.coluna,
    )