import argparse
from pathlib import Path

import rasterio


def verificar_par_espectral(arquivo_red, arquivo_nir):
    with (
        rasterio.open(arquivo_red) as red,
        rasterio.open(arquivo_nir) as nir,
    ):
        if red.count != 1 or nir.count != 1:
            raise ValueError("Cada arquivo precisa ter uma banda")

        if red.dtypes != ("uint16",) or nir.dtypes != ("uint16",):
            raise ValueError("As bandas precisam conter valores uint16")

        if red.crs is None or nir.crs is None:
            raise ValueError("As bandas precisam informar suas coordenadas")

        if red.crs != nir.crs:
            raise ValueError("As bandas usam sistemas de coordenadas diferentes")

        if red.width != nir.width or red.height != nir.height:
            raise ValueError("As bandas possuem dimensoes diferentes")

        if red.transform != nir.transform:
            raise ValueError("As bandas nao possuem o mesmo posicionamento")

        tags_red = red.tags()
        tags_nir = nir.tags()

        if tags_red.get("stac_asset") != "red":
            raise ValueError("O primeiro arquivo precisa ser da banda red")

        if tags_nir.get("stac_asset") != "nir":
            raise ValueError("O segundo arquivo precisa ser da banda nir")

        id_cena = tags_red.get("stac_id_cena")

        if not id_cena or id_cena != tags_nir.get("stac_id_cena"):
            raise ValueError("As bandas precisam pertencer a mesma cena")

        print(f"Cena: {id_cena}")
        print(f"Sistema de coordenadas: {red.crs}")
        print(f"Dimensoes: {red.width} x {red.height}")
        print(f"Resolucao: {red.res}")
        print(f"Limites: {red.bounds}")
        print("As bandas possuem a mesma grade.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Verifica se as bandas red e nir formam um par"
    )

    parser.add_argument("--red", type=Path, required=True)
    parser.add_argument("--nir", type=Path, required=True)

    argumentos = parser.parse_args()

    verificar_par_espectral(argumentos.red, argumentos.nir)