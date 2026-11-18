import argparse
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from configuracao import LATITUDE_REFERENCIA, LONGITUDE_REFERENCIA
from preparar_solo import preparar_solo


def consultar_solo_ponto(solos, latitude, longitude):
    preparados = preparar_solo(solos)

    ponto = Point(longitude, latitude)

    encontrados = preparados[
        preparados.geometry.covers(ponto)
    ]

    return encontrados


def formatar_valor(valor):
    if pd.isna(valor):
        return "Nao informado"

    texto = str(valor).strip()

    if not texto:
        return "Nao informado"

    return texto

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Consulta unidades de solo no ponto de referencia"
    )

    parser.add_argument(
        "--arquivo",
        type=Path,
        required=True,
        help="Arquivo vetorial das unidades de solo",
    )

    argumentos = parser.parse_args()

    solos = gpd.read_file(argumentos.arquivo)

    encontrados = consultar_solo_ponto(
        solos,
        latitude=LATITUDE_REFERENCIA,
        longitude=LONGITUDE_REFERENCIA,
    )

    print(
        f"Ponto consultado: latitude {LATITUDE_REFERENCIA}, "
        f"longitude {LONGITUDE_REFERENCIA}"
    )
    print(f"Unidades encontradas: {len(encontrados)}")

    for _, unidade in encontrados.iterrows():
        print()

        print(f"Categoria: {formatar_valor(unidade.get('leg_ordem'))}")
        print(f"Legenda: {formatar_valor(unidade.get('legenda'))}")
        print(f"Textura: {formatar_valor(unidade.get('textura'))}")
        print(f"Componentes: {formatar_valor(unidade.get('val_ncompo'))}")
