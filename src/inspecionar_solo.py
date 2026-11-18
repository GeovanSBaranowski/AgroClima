import argparse
from pathlib import Path

import geopandas as gpd


def inspecionar_solo(arquivo):
    solos = gpd.read_file(arquivo)

    print(f"Arquivo: {arquivo}")
    print(f"Quantidade de unidades: {len(solos)}")
    print(f"Sistema de coordenadas: {solos.crs}")
    print(f"Tipos de geometria: {solos.geom_type.unique().tolist()}")
    print(f"Colunas: {solos.columns.tolist()}")
    print(f"Limites: {solos.total_bounds}")

    resumo = (
        solos.groupby(
            ["ordem", "subordem"],
            dropna=False,
        )
        .size()
        .reset_index(name="quantidade_poligonos")
    )

    print()
    print("Poligonos por ordem e subordem:")
    print(resumo.to_string(index=False))

    sem_ordem = solos[
        solos["ordem"].isna() | solos["subordem"].isna()
    ]

    colunas_inspecao = [
        "id1",
        "nom_unidad",
        "legenda",
        "leg_ordem",
        "componente",
    ]

    print()
    print("Poligonos com ordem ou subordem ausente:")
    print(
        sem_ordem[colunas_inspecao].to_string(
            index=False,
        )
    )   

    contagem_legenda = (
        solos["leg_ordem"]
        .value_counts(dropna=False)
    )

    print()
    print("Poligonos por classe de legenda:")
    print(contagem_legenda.to_string())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Inspeciona os dados vetoriais de solo"
    )

    parser.add_argument("--arquivo", type=Path, required=True)

    argumentos = parser.parse_args()

    inspecionar_solo(argumentos.arquivo)