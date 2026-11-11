import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from avaliar_mosaico_ndvi import avaliar_mosaico_ndvi


def criar_mosaico(caminho, dados, mascara):
    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):  # noqa: SIM117
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


def test_avalia_mascara_zero_valido_e_area_fora_do_raster(tmp_path):
    arquivo = tmp_path / "ndvi.tif"

    criar_mosaico(
        arquivo,
        dados=[[0.0, 1.2], [-0.2, 0.6]],
        mascara=[[255, 255], [255, 0]],
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

    resumo = avaliar_mosaico_ndvi(arquivo, poligono)

    assert resumo["pixels_esperados"] == 6
    assert resumo["pixels_com_ndvi"] == 3
    assert resumo["pixels_sem_ndvi"] == 3
    assert resumo["cobertura_percentual"] == pytest.approx(50.0)
    assert resumo["fora_intervalo"] == 1


def test_rejeita_poligono_sem_ndvi_valido(tmp_path):
    arquivo = tmp_path / "ndvi.tif"

    criar_mosaico(
        arquivo,
        dados=[[0.1, 0.2], [0.3, 0.4]],
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

    with pytest.raises(ValueError, match="Nao ha pixels validos"):
        avaliar_mosaico_ndvi(arquivo, poligono)