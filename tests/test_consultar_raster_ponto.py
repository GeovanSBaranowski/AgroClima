import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import transform

from consultar_raster_ponto import consultar_raster_ponto

LATITUDE = -27.10
LONGITUDE = -52.62


def criar_raster(caminho, valor_centro, centro_valido=True):
    coordenadas_x, coordenadas_y = transform(
        "EPSG:4326",
        "EPSG:32722",
        [LONGITUDE],
        [LATITUDE],
    )

    x = coordenadas_x[0]
    y = coordenadas_y[0]

    dados = np.full((3, 3), 0.5, dtype="float32")
    dados[1, 1] = valor_centro

    mascara = np.full((3, 3), 255, dtype="uint8")

    if not centro_valido:
        mascara[1, 1] = 0

    # O ponto consultado fica no centro do pixel central.
    grade = from_origin(x - 15, y + 15, 10, 10)

    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):  # noqa: SIM117
        with rasterio.open(
            caminho,
            "w",
            driver="GTiff",
            width=3,
            height=3,
            count=1,
            dtype="float32",
            crs="EPSG:32722",
            transform=grade,
        ) as destino:
            destino.write(dados, 1)
            destino.write_mask(mascara)


def test_preserva_zero_valido(tmp_path):
    arquivo = tmp_path / "raster.tif"
    criar_raster(arquivo, valor_centro=0.0)

    valor = consultar_raster_ponto(
        arquivo,
        latitude=LATITUDE,
        longitude=LONGITUDE,
    )

    assert valor == pytest.approx(0.0)


def test_retorna_none_para_pixel_mascarado(tmp_path):
    arquivo = tmp_path / "raster.tif"
    criar_raster(arquivo, valor_centro=0.5, centro_valido=False)

    valor = consultar_raster_ponto(
        arquivo,
        latitude=LATITUDE,
        longitude=LONGITUDE,
    )

    assert valor is None


def test_retorna_none_para_ponto_fora_do_raster(tmp_path):
    arquivo = tmp_path / "raster.tif"
    criar_raster(arquivo, valor_centro=0.5)

    valor = consultar_raster_ponto(
        arquivo,
        latitude=LATITUDE,
        longitude=LONGITUDE + 1,
    )

    assert valor is None


def test_retorna_none_para_valor_nao_finito(tmp_path):
    arquivo = tmp_path / "raster.tif"
    criar_raster(arquivo, valor_centro=np.nan)

    valor = consultar_raster_ponto(
        arquivo,
        latitude=LATITUDE,
        longitude=LONGITUDE,
    )

    assert valor is None