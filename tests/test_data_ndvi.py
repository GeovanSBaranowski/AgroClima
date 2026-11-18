from datetime import date

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from data_ndvi import avaliar_data_raster_ndvi, comparar_data_ndvi


def test_identifica_datas_iguais():
    resultado = comparar_data_ndvi(
        "2024-02-01",
        date(2024, 2, 1),
    )

    assert resultado["situacao"] == "coincide"
    assert resultado["data_ndvi"] == date(2024, 2, 1)


def test_identifica_datas_diferentes():
    resultado = comparar_data_ndvi(
        "2024-02-02",
        date(2024, 2, 1),
    )

    assert resultado["situacao"] == "diferente"
    assert resultado["data_ndvi"] == date(2024, 2, 2)


def test_identifica_data_ausente():
    resultado = comparar_data_ndvi(
        None,
        date(2024, 2, 1),
    )

    assert resultado["situacao"] == "ausente"
    assert resultado["data_ndvi"] is None


@pytest.mark.parametrize(
    "data_invalida",
    ["2024-02-30", "20240201"],
)
def test_identifica_data_invalida(data_invalida):
    resultado = comparar_data_ndvi(
        data_invalida,
        date(2024, 2, 1),
    )

    assert resultado["situacao"] == "invalida"
    assert resultado["data_ndvi"] is None

def criar_raster_ndvi(caminho, data_tag):
    with rasterio.open(
        caminho,
        "w",
        driver="GTiff",
        width=1,
        height=1,
        count=1,
        dtype="float32",
        crs="EPSG:32722",
        transform=from_origin(300000, 7000000, 10, 10),
    ) as destino:
        destino.write(
            np.array([[0.5]], dtype="float32"),
            1,
        )

        if data_tag is not None:
            destino.update_tags(
                data_observacao_utc=data_tag,
            )


@pytest.mark.parametrize(
    ("data_tag", "situacao_esperada"),
    [
        ("2024-02-01", "coincide"),
        ("2024-02-02", "diferente"),
        (None, "ausente"),
        ("data-invalida", "invalida"),
    ],
)
def test_avalia_data_registrada_no_raster(
    tmp_path,
    data_tag,
    situacao_esperada,
):
    arquivo = tmp_path / "ndvi.tif"

    criar_raster_ndvi(arquivo, data_tag)

    resultado = avaliar_data_raster_ndvi(
        arquivo,
        date(2024, 2, 1),
    )

    assert resultado["situacao"] == situacao_esperada