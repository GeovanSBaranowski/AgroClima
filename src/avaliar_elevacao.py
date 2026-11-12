import argparse
import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import geometry_mask, geometry_window
from rasterio.warp import transform_geom


def avaliar_elevacao(arquivo_raster):
    with rasterio.open(arquivo_raster) as origem:
        if origem.count != 1 or origem.dtypes != ("float32",):
            raise ValueError("A elevacao precisa ter uma banda float32")

        dados = origem.read(1, masked=True)
        tags = origem.tags()

    valores = np.ma.getdata(dados)

    validos = (
        ~np.ma.getmaskarray(dados)
        & np.isfinite(valores)
    )

    elevacoes = valores[validos]

    if elevacoes.size == 0:
        raise ValueError("O recorte nao possui valores validos")

    print(f"Arquivo: {arquivo_raster}")
    print(f"Item de origem: {tags.get('id_item')}")
    print(f"Pixels validos: {elevacoes.size}")
    print(f"Elevacao minima: {elevacoes.min():.2f} m")
    print(f"Elevacao maxima: {elevacoes.max():.2f} m")
    print(f"Elevacao media: {elevacoes.mean():.2f} m")


def avaliar_cobertura(arquivo_raster, geometria_lonlat):
    with rasterio.open(arquivo_raster) as origem:
        if origem.crs is None:
            raise ValueError("O raster precisa informar suas coordenadas")

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

    pixels_esperados = int(np.count_nonzero(dentro_poligono))
    pixels_validos = int(np.count_nonzero(validos))

    if pixels_esperados == 0:
        raise ValueError("O poligono nao selecionou pixels")

    return {
        "pixels_esperados": pixels_esperados,
        "pixels_validos": pixels_validos,
        "pixels_sem_dados": pixels_esperados - pixels_validos,
        "cobertura_percentual": pixels_validos / pixels_esperados * 100,
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Resume os valores de um raster de elevacao"
    )

    parser.add_argument("--raster", type=Path, required=True)

    parser.add_argument(
        "--consulta",
        type=Path,
        help="Arquivo consulta.json que contem o poligono",
    )

    argumentos = parser.parse_args()

    avaliar_elevacao(argumentos.raster)

    if argumentos.consulta is not None:
        consulta = json.loads(
            argumentos.consulta.read_text(encoding="utf-8")
        )

        geometria = consulta["criterios"]["intersects"]

        cobertura = avaliar_cobertura(
            argumentos.raster,
            geometria,
        )

        print()
        print("Cobertura do poligono:")
        print(f"Pixels esperados: {cobertura['pixels_esperados']}")
        print(f"Pixels validos: {cobertura['pixels_validos']}")
        print(f"Pixels sem dados: {cobertura['pixels_sem_dados']}")
        print(f"Cobertura: {cobertura['cobertura_percentual']:.4f}%")