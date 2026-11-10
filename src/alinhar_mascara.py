import argparse
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject

from inspecionar_raster import inspecionar_raster


def alinhar_mascara(arquivo_mascara, arquivo_referencia, arquivo_saida):
    arquivo_mascara = Path(arquivo_mascara).resolve()
    arquivo_referencia = Path(arquivo_referencia).resolve()
    arquivo_saida = Path(arquivo_saida).resolve()

    if arquivo_saida in (arquivo_mascara, arquivo_referencia):
        raise ValueError("A saida precisa ser diferente das entradas")

    with (
        rasterio.open(arquivo_mascara) as origem,
        rasterio.open(arquivo_referencia) as referencia,
    ):
        if origem.crs is None or referencia.crs is None:
            raise ValueError("Os arquivos precisam informar suas coordenadas")

        if origem.count != 1 or origem.dtypes != ("uint8",):
            raise ValueError("A mascara precisa ter uma banda uint8")

        mascara = origem.read(1, masked=True)

        if not np.isin(mascara.compressed(), (0, 1)).all():
            raise ValueError("A mascara precisa conter apenas zero e um")

        alinhada = np.full(
            referencia.shape,
            255,
            dtype="uint8",
        )

        reproject(
            source=mascara.filled(255),
            destination=alinhada,
            src_transform=origem.transform,
            src_crs=origem.crs,
            src_nodata=255,
            dst_transform=referencia.transform,
            dst_crs=referencia.crs,
            dst_nodata=255,
            resampling=Resampling.nearest,
        )

        disponiveis = (
            (alinhada != 255)
            & (referencia.dataset_mask() > 0)
        )

        perfil = origem.profile.copy()
        perfil.update(
            driver="GTiff",
            height=referencia.height,
            width=referencia.width,
            transform=referencia.transform,
            crs=referencia.crs,
            count=1,
            dtype="uint8",
            nodata=None,
            compress="deflate",
        )

        metadados = origem.tags()
        metadados.update(
            mascara_origem=str(arquivo_mascara),
            raster_referencia=str(arquivo_referencia),
            reamostragem="nearest",
        )

    if not disponiveis.any():
        raise ValueError("Nao ha dados comuns entre mascara e referencia")

    decisoes = np.where(disponiveis, alinhada, 0).astype("uint8")

    arquivo_saida.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):  # noqa: SIM117
        with rasterio.open(arquivo_saida, "w", **perfil) as destino:
            destino.write(decisoes, 1)
            destino.write_mask(disponiveis)
            destino.update_tags(**metadados)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Alinha a mascara de qualidade a um raster de referencia"
    )

    parser.add_argument("--mascara", type=Path, required=True)
    parser.add_argument("--referencia", type=Path, required=True)
    parser.add_argument("--saida", type=Path, required=True)

    argumentos = parser.parse_args()

    raiz_projeto = Path(__file__).resolve().parent.parent
    arquivo_saida = raiz_projeto / argumentos.saida

    alinhar_mascara(
        raiz_projeto / argumentos.mascara,
        raiz_projeto / argumentos.referencia,
        arquivo_saida,
    )

    print(f"Mascara alinhada salva em: {arquivo_saida.resolve()}")

    for campo, valor in inspecionar_raster(arquivo_saida).items():
        print(f"{campo}: {valor}")