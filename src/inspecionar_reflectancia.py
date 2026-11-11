import argparse
import json
from pathlib import Path

import rasterio

from metadados_espectrais import obter_metadados_banda
from reflectancia import converter_reflectancia


def inspecionar_reflectancia(arquivo_raster, metadados):
    with rasterio.open(arquivo_raster) as origem:
        if origem.count != 1:
            raise ValueError("O recorte precisa ter uma banda")

        tags = origem.tags()

        if tags.get("stac_id_cena") != metadados["id_cena"]:
            raise ValueError("A cena do recorte difere da cena solicitada")

        if tags.get("stac_asset") != metadados["asset"]:
            raise ValueError("A banda do recorte difere da banda solicitada")

        valores = origem.read(1, masked=True)

    reflectancia = converter_reflectancia(valores, metadados)

    quantidade_valida = reflectancia.count()

    if quantidade_valida == 0:
        raise ValueError("O recorte nao possui pixels validos")

    print(f"Cena: {metadados['id_cena']}")
    print(f"Banda: {metadados['asset']}")
    print(f"Pixels validos: {quantidade_valida}")
    print(f"Reflectancia minima: {reflectancia.min():.4f}")
    print(f"Reflectancia maxima: {reflectancia.max():.4f}")
    print(f"Reflectancia media: {reflectancia.mean():.4f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Inspeciona a reflectancia de um recorte espectral"
    )

    parser.add_argument("--pagina", type=Path, required=True)
    parser.add_argument("--id-cena", required=True)
    parser.add_argument("--asset", choices=["red", "nir"], required=True)
    parser.add_argument("--raster", type=Path, required=True)

    argumentos = parser.parse_args()

    dados = json.loads(
        argumentos.pagina.read_text(encoding="utf-8")
    )

    metadados = obter_metadados_banda(
        dados,
        argumentos.id_cena,
        argumentos.asset,
    )

    inspecionar_reflectancia(argumentos.raster, metadados)