import argparse
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import calculate_default_transform, reproject


def reprojetar_elevacao(arquivo_origem, arquivo_saida):
    arquivo_origem = Path(arquivo_origem).resolve()
    arquivo_saida = Path(arquivo_saida).resolve()

    if arquivo_saida == arquivo_origem:
        raise ValueError("A saida precisa ser diferente da origem")

    if arquivo_saida.exists():
        raise FileExistsError(f"O arquivo de saida ja existe: {arquivo_saida}")

    crs_destino = "EPSG:32722"

    with rasterio.open(arquivo_origem) as origem:
        if origem.crs is None:
            raise ValueError("O raster precisa informar suas coordenadas")

        if origem.count != 1 or origem.dtypes != ("float32",):
            raise ValueError("A elevacao precisa ter uma banda float32")

        transformacao, largura, altura = calculate_default_transform(
            origem.crs,
            crs_destino,
            origem.width,
            origem.height,
            *origem.bounds,
        )

        dados_origem = origem.read(1, masked=True)
        dados_origem = np.ma.masked_invalid(dados_origem)

        if dados_origem.count() == 0:
            raise ValueError("O raster de origem nao possui dados validos")

        # NaN representa ausência durante a reprojecao.
        valores_origem = dados_origem.filled(np.nan)

        valores_destino = np.full(
            (altura, largura),
            np.nan,
            dtype="float32",
        )

        reproject(
            source=valores_origem,
            destination=valores_destino,
            src_transform=origem.transform,
            src_crs=origem.crs,
            src_nodata=np.nan,
            dst_transform=transformacao,
            dst_crs=crs_destino,
            dst_nodata=np.nan,
            resampling=Resampling.bilinear,
        )

        perfil = origem.profile.copy()

    pixels_validos = np.isfinite(valores_destino)

    if not pixels_validos.any():
        raise ValueError("A reprojecao nao produziu pixels validos")

    perfil.update(
        driver="GTiff",
        width=largura,
        height=altura,
        count=1,
        dtype="float32",
        crs=crs_destino,
        transform=transformacao,
        nodata=None,
        compress="deflate",
    )

    # No arquivo final, a disponibilidade fica na mascara interna.
    valores_para_gravar = np.where(
        pixels_validos,
        valores_destino,
        0,
    ).astype("float32")

    arquivo_saida.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):  # noqa: SIM117
        with rasterio.open(arquivo_saida, "w", **perfil) as destino:
            destino.write(valores_para_gravar, 1)
            destino.write_mask(pixels_validos)

            destino.update_tags(
                arquivo_origem=str(arquivo_origem),
                sistema_destino=crs_destino,
                reamostragem="bilinear",
                unidade="meter",
            )

    print(f"Elevacao reprojetada salva em: {arquivo_saida}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Reprojeta o raster de elevacao para UTM"
    )

    parser.add_argument("--origem", type=Path, required=True)
    parser.add_argument("--saida", type=Path, required=True)

    argumentos = parser.parse_args()

    reprojetar_elevacao(
        argumentos.origem,
        argumentos.saida,
    )