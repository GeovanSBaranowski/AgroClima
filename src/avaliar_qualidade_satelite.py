import argparse
import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import geometry_mask, geometry_window
from rasterio.warp import transform_geom

CLASSES_SCL = {
    1: "Saturado ou defeituoso",
    2: "Sombras projetadas",
    3: "Sombras de nuvens",
    4: "Vegetacao",
    5: "Superficie sem vegetacao",
    6: "Agua",
    7: "Nao classificado",
    8: "Nuvem com probabilidade media",
    9: "Nuvem com probabilidade alta",
    10: "Cirrus",
    11: "Neve ou gelo",
}


def resumir_classificacao(arquivo_raster):
    with rasterio.open(arquivo_raster) as origem:
        if origem.count != 1:
            raise ValueError("A classificacao precisa ter uma unica banda")

        if origem.dtypes != ("uint8",):
            raise ValueError("A classificacao precisa conter valores uint8")

        classificacao = origem.read(1, masked=True)

    pixels = classificacao.compressed()
    pixels = pixels[pixels != 0]

    if pixels.size == 0:
        raise ValueError("O recorte nao possui pixels com classificacao")

    codigos, quantidades = np.unique(
        pixels,
        return_counts=True,
    )

    registros = []

    for codigo, quantidade in zip(codigos, quantidades):
        codigo = int(codigo)
        quantidade = int(quantidade)

        if codigo not in CLASSES_SCL:
            raise ValueError(f"Codigo SCL inesperado: {codigo}")

        registros.append({
            "codigo": codigo,
            "classe": CLASSES_SCL[codigo],
            "quantidade_pixels": quantidade,
            "percentual": quantidade / pixels.size * 100,
        })

    return {
        "total_pixels_avaliados": int(pixels.size),
        "classes": registros,
    }

def avaliar_cobertura(arquivo_raster, geometria_lonlat):
    with rasterio.open(arquivo_raster) as origem:
        if origem.crs is None:
            raise ValueError("O arquivo precisa informar suas coordenadas")

        if origem.count != 1 or origem.dtypes != ("uint8",):
            raise ValueError("A avaliacao espera uma banda SCL uint8")

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

    com_dados = (
        ~np.ma.getmaskarray(dados)
        & (dados.filled(0) != 0)
    )

    pixels_esperados = int(np.count_nonzero(dentro_poligono))
    pixels_com_dados = int(
        np.count_nonzero(dentro_poligono & com_dados)
    )

    if pixels_esperados == 0:
        raise ValueError("O poligono nao selecionou pixels nesta resolucao")

    return {
        "pixels_esperados": pixels_esperados,
        "pixels_com_dados": pixels_com_dados,
        "pixels_sem_dados": pixels_esperados - pixels_com_dados,
        "cobertura_percentual": (
            pixels_com_dados / pixels_esperados * 100
        ),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Resume as categorias de um recorte SCL"
    )

    parser.add_argument(
        "--raster",
        type=Path,
        required=True,
        help="Arquivo GeoTIFF de classificacao SCL",
    )

    parser.add_argument(
        "--consulta",
        type=Path,
        help="Arquivo consulta.json que contem o poligono utilizado",
    )

    argumentos = parser.parse_args()

    raiz_projeto = Path(__file__).resolve().parent.parent
    arquivo_raster = (raiz_projeto / argumentos.raster).resolve()

    resumo = resumir_classificacao(arquivo_raster)

    print(f"Arquivo: {arquivo_raster}")
    print(f"Pixels avaliados: {resumo['total_pixels_avaliados']}")
    print("Percentuais entre pixels nao mascarados e diferentes de zero:")

    for registro in resumo["classes"]:
        print(
            f"{registro['codigo']:02d} | "
            f"{registro['classe']} | "
            f"{registro['quantidade_pixels']} pixels | "
            f"{registro['percentual']:.2f}%"
        )

    if argumentos.consulta:
        arquivo_consulta = (
            raiz_projeto / argumentos.consulta
        ).resolve()

        consulta = json.loads(
            arquivo_consulta.read_text(encoding="utf-8")
        )

        geometria = consulta["criterios"]["intersects"]

        cobertura = avaliar_cobertura(
            arquivo_raster,
            geometria,
        )

        print()
        print("Cobertura do poligono:")
        print(f"Pixels esperados: {cobertura['pixels_esperados']}")
        print(f"Pixels com dados: {cobertura['pixels_com_dados']}")
        print(f"Pixels sem dados: {cobertura['pixels_sem_dados']}")
        print(f"Cobertura: {cobertura['cobertura_percentual']:.4f}%")