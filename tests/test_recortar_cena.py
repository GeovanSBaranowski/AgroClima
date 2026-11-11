import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from recortar_cena import recortar_cena

POLIGONO_ESPECTRAL = {
    "type": "Polygon",
    "coordinates": [[
        [1, 1],
        [3, 1],
        [3, 3],
        [1, 3],
        [1, 1],
    ]],
}


@pytest.fixture
def entrada_espectral(tmp_path):
    arquivo = tmp_path / "banda_original.tif"

    dados = np.array(
        [
            [900, 900, 900, 900],
            [900, 1000, 2500, 900],
            [900, 0, 3000, 900],
            [900, 900, 900, 900],
        ],
        dtype="uint16",
    )

    with rasterio.open(
        arquivo,
        "w",
        driver="GTiff",
        height=4,
        width=4,
        count=1,
        dtype="uint16",
        crs="EPSG:4326",
        transform=from_origin(0, 4, 1, 1),
        nodata=0,
    ) as destino:
        destino.write(dados, 1)

    return arquivo


@pytest.fixture
def metadados_espectrais():
    return {
        "id_cena": "cena_teste",
        "asset": "red",
        "escala": 0.0001,
        "deslocamento": -0.1,
        "nodata": 0,
        "tipo_dados": "uint16",
        "pagina_origem": "pagina_teste.json",
        "url": "https://exemplo.test/red.tif",
    }


def test_recorte_preserva_valores_mascara_e_metadados(
    tmp_path,
    entrada_espectral,
    metadados_espectrais,
):
    saida = tmp_path / "recorte.tif"

    recortar_cena(
        entrada_espectral,
        POLIGONO_ESPECTRAL,
        saida,
        metadados_espectrais=metadados_espectrais,
    )

    with rasterio.open(saida) as resultado:
        assert resultado.shape == (2, 2)
        assert resultado.count == 1
        assert resultado.dtypes == ("uint16",)
        assert resultado.nodata is None
        assert resultado.crs.to_epsg() == 4326
        assert resultado.transform == from_origin(1, 3, 1, 1)

        np.testing.assert_array_equal(
            resultado.read(1),
            [
                [1000, 2500],
                [0, 3000],
            ],
        )

        np.testing.assert_array_equal(
            resultado.dataset_mask(),
            [
                [255, 255],
                [0, 255],
            ],
        )

        tags = resultado.tags()

    assert tags["stac_id_cena"] == "cena_teste"
    assert tags["stac_asset"] == "red"
    assert float(tags["stac_scale"]) == pytest.approx(0.0001)
    assert float(tags["stac_offset"]) == pytest.approx(-0.1)
    assert tags["stac_nodata"] == "0"
    assert tags["stac_data_type"] == "uint16"
    assert tags["stac_pagina"] == "pagina_teste.json"
    assert tags["stac_url"] == "https://exemplo.test/red.tif"


@pytest.mark.parametrize(
    "campo,valor_incorreto,mensagem",
    [
        ("nodata", 99, "nodata"),
        ("tipo_dados", "uint8", "tipo informado"),
    ],
)
def test_rejeita_banda_diferente_do_catalogo(
    tmp_path,
    entrada_espectral,
    metadados_espectrais,
    campo,
    valor_incorreto,
    mensagem,
):
    metadados_espectrais[campo] = valor_incorreto
    saida = tmp_path / "recorte_invalido.tif"

    with pytest.raises(ValueError, match=mensagem):
        recortar_cena(
            entrada_espectral,
            POLIGONO_ESPECTRAL,
            saida,
            metadados_espectrais=metadados_espectrais,
        )

    assert not saida.exists()


def test_recorte_colorido_preserva_preto_valido(tmp_path):
    origem = tmp_path / "imagem_colorida.tif"
    saida = tmp_path / "recorte_colorido.tif"

    cores = np.full((3, 2, 2), 120, dtype="uint8")
    cores[:, 0, 0] = 0

    disponibilidade = np.array(
        [
            [255, 255],
            [255, 0],
        ],
        dtype="uint8",
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

    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):  # noqa: SIM117
        with rasterio.open(
            origem,
            "w",
            driver="GTiff",
            height=2,
            width=2,
            count=3,
            dtype="uint8",
            crs="EPSG:4326",
            transform=from_origin(0, 2, 1, 1),
        ) as destino:
            destino.write(cores)
            destino.write_mask(disponibilidade)

    recortar_cena(origem, poligono, saida)

    with rasterio.open(saida) as resultado:
        assert resultado.dtypes == ("uint8", "uint8", "uint8")
        assert resultado.nodata is None

        np.testing.assert_array_equal(
            resultado.dataset_mask(),
            disponibilidade,
        )

        assert np.all(resultado.read()[:, 0, 0] == 0)