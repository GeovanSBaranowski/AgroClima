import argparse
from pathlib import Path

import geopandas as gpd


def comparar_limites(arquivo_solo, arquivo_limite):
    solos = gpd.read_file(arquivo_solo)
    limite = gpd.read_file(arquivo_limite)

    if solos.crs is None or limite.crs is None:
        raise ValueError("Os dois arquivos precisam informar suas coordenadas")

    # Usamos um sistema em metros para comparar as áreas.
    solos_utm = solos.to_crs("EPSG:32722")
    limite_utm = limite.to_crs("EPSG:32722")

    # Reunimos os polígonos de cada arquivo em uma geometria.
    area_solo = solos_utm.geometry.union_all()
    area_municipio = limite_utm.geometry.union_all()

    fora_do_limite = area_solo.difference(area_municipio)
    sem_poligono_solo = area_municipio.difference(area_solo)

    print(f"Arquivo de solo: {arquivo_solo}")
    print(f"Limite utilizado: {arquivo_limite}")
    print(f"Area do limite: {area_municipio.area / 1_000_000:.3f} km²")
    print(
        "Area de solo fora do limite: "
        f"{fora_do_limite.area / 1_000_000:.3f} km²"
    )
    print(
        "Area do limite sem poligono de solo: "
        f"{sem_poligono_solo.area / 1_000_000:.3f} km²"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compara o recorte de solo com o limite municipal"
    )

    parser.add_argument("--solo", type=Path, required=True)
    parser.add_argument("--limite", type=Path, required=True)

    argumentos = parser.parse_args()

    comparar_limites(argumentos.solo, argumentos.limite)