import argparse
from pathlib import Path

import geopandas as gpd


def preparar_solo(solos):
    if solos.empty:
        raise ValueError("O arquivo nao possui poligonos")

    if solos.crs is None:
        raise ValueError("Os dados precisam informar suas coordenadas")

    if "leg_ordem" not in solos.columns:
        raise ValueError("O campo leg_ordem nao foi encontrado")

    if solos.geometry.isna().any() or solos.geometry.is_empty.any():
        raise ValueError("Existem geometrias ausentes ou vazias")

    if not solos.geometry.is_valid.all():
        raise ValueError("Existem geometrias invalidas para investigar")

    tipos_aceitos = ["Polygon", "MultiPolygon"]

    if not solos.geom_type.isin(tipos_aceitos).all():
        raise ValueError("Os dados precisam conter poligonos")

    preparados = solos.to_crs("EPSG:4326")

    return preparados


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Prepara os poligonos de solo para o mapa"
    )

    parser.add_argument("--arquivo", type=Path, required=True)

    argumentos = parser.parse_args()

    solos = gpd.read_file(argumentos.arquivo)

    preparados = preparar_solo(solos)

    print(f"Poligonos preparados: {len(preparados)}")
    print(f"Sistema de origem: {solos.crs}")
    print(f"Sistema de destino: {preparados.crs}")
    print(f"Limites: {preparados.total_bounds}")