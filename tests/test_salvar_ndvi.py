import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from inspecionar_ndvi import salvar_ndvi


def criar_referencia(caminho):
    with rasterio.open(
        caminho,
        "w",
        driver="GTiff",
        width=2,
        height=2,
        count=1,
        dtype="uint16",
        crs="EPSG:32722",
        transform=from_origin(300000, 7000000, 10, 10),
    ) as destino:
        destino.write(
            np.ones((2, 2), dtype="uint16"),
            1,
        )


def test_salva_valores_e_mascara_interna(tmp_path):
    referencia = tmp_path / "red.tif"
    saida = tmp_path / "ndvi.tif"
    criar_referencia(referencia)

    ndvi = np.ma.array(
        [[0.0, 0.7], [-0.2, 0.5]],
        mask=[[False, False], [True, False]],
        dtype="float32",
    )

    salvar_ndvi(ndvi, referencia, saida, "cena_1")

    with rasterio.open(saida) as arquivo:
        resultado = arquivo.read(1, masked=True)

        assert arquivo.dtypes == ("float32",)
        assert arquivo.crs.to_string() == "EPSG:32722"
        assert arquivo.transform == from_origin(
            300000, 7000000, 10, 10
        )
        assert arquivo.tags()["id_cena"] == "cena_1"
        assert arquivo.tags()["produto"] == "NDVI"

        np.testing.assert_array_equal(
            np.ma.getmaskarray(resultado),
            [[False, False], [True, False]],
        )

        assert resultado[0, 0] == pytest.approx(0.0)
        assert resultado[0, 1] == pytest.approx(0.7)
        assert resultado[1, 1] == pytest.approx(0.5)


def test_nao_sobrescreve_a_banda_de_referencia(tmp_path):
    referencia = tmp_path / "red.tif"
    criar_referencia(referencia)

    ndvi = np.ma.array(
        np.full((2, 2), 0.5, dtype="float32")
    )

    with pytest.raises(ValueError, match="diferente da banda"):
        salvar_ndvi(ndvi, referencia, referencia, "cena_1")

    with rasterio.open(referencia) as arquivo:
        assert arquivo.dtypes == ("uint16",)