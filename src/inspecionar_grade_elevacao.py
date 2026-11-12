import argparse
from pathlib import Path

import rasterio
from rasterio.warp import calculate_default_transform


def inspecionar_grade(arquivo_raster):
    with rasterio.open(arquivo_raster) as origem:
        if origem.crs is None:
            raise ValueError("O raster precisa informar suas coordenadas")

        crs_destino = "EPSG:32722"

        transformacao, largura, altura = calculate_default_transform(
            origem.crs,
            crs_destino,
            origem.width,
            origem.height,
            *origem.bounds,
        )

        print(f"Sistema de origem: {origem.crs}")
        print(f"Resolucao de origem: {origem.res}")
        print(f"Sistema de destino: {crs_destino}")
        print(f"Largura proposta: {largura}")
        print(f"Altura proposta: {altura}")
        print(
            "Resolucao proposta: "
            f"({abs(transformacao.a):.2f}, "
            f"{abs(transformacao.e):.2f}) metros"
        )
        print(f"Transformacao proposta: {transformacao}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Inspeciona uma grade projetada para a elevacao"
    )

    parser.add_argument("--raster", type=Path, required=True)

    argumentos = parser.parse_args()

    inspecionar_grade(argumentos.raster)