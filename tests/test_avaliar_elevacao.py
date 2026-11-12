import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from avaliar_elevacao import avaliar_cobertura


def criar_raster_elevacao(caminho, dados, mascara):
    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):
        with rasterio.open(
            caminho,
            "w",
            driver="GTiff",
            width=2,
            height=2,
            count=1,
            dtype="float32",
            crs="EPSG:4326",
            transform=from_origin(0, 2, 1, 1),
        ) as destino:
            destino.write(np.array(dados, dtype="float32"), 1)
            destino.write_mask(np.array(mascara, dtype="uint8"))


def test_cobertura_considera_mascara_nan_zero_e_area_externa(tmp_path):
    arquivo = tmp_path / "elevacao.tif"

    criar_raster_elevacao(
        arquivo,
        dados=[
            [0.0, 100.0],
            [np.nan, 300.0],
        ],
        mascara=[
            [255, 255],
            [255, 0],
        ],
    )

    # O poligono cobre o raster e mais uma coluna a esquerda.
    poligono = {
        "type": "Polygon",
        "coordinates": [[
            [-1, 0],
            [2, 0],
            [2, 2],
            [-1, 2],
            [-1, 0],
        ]],
    }

    cobertura = avaliar_cobertura(arquivo, poligono)

    assert cobertura["pixels_esperados"] == 6
    assert cobertura["pixels_validos"] == 2
    assert cobertura["pixels_sem_dados"] == 4
    assert cobertura["cobertura_percentual"] == pytest.approx(
        2 / 6 * 100
    )


def test_cobertura_sem_pixels_validos(tmp_path):
    arquivo = tmp_path / "elevacao.tif"

    criar_raster_elevacao(
        arquivo,
        dados=[[100.0, 200.0], [300.0, 400.0]],
        mascara=[[0, 0], [0, 0]],
    )

    poligono = {
        "type": "Polygon",
        "coordinates": [[
            [0, 0],
            [2, 0],
            [2, 2],
            [0, 2],
            [0, 0],
        ]],
    }

    cobertura = avaliar_cobertura(arquivo, poligono)

    assert cobertura["pixels_esperados"] == 4
    assert cobertura["pixels_validos"] == 0
    assert cobertura["pixels_sem_dados"] == 4
    assert cobertura["cobertura_percentual"] == 0.0