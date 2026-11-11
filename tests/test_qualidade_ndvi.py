import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from inspecionar_ndvi import aplicar_qualidade


def criar_raster(caminho, dados, transform, mascara_interna=None):
    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):  # noqa: SIM117
        with rasterio.open(
            caminho,
            "w",
            driver="GTiff",
            width=dados.shape[1],
            height=dados.shape[0],
            count=1,
            dtype=dados.dtype,
            crs="EPSG:32722",
            transform=transform,
        ) as destino:
            destino.write(dados, 1)

            if mascara_interna is not None:
                destino.write_mask(mascara_interna)


def test_aplica_qualidade_preservando_mascara_do_ndvi(tmp_path):
    arquivo_red = tmp_path / "red.tif"
    arquivo_mascara = tmp_path / "qualidade.tif"
    grade = from_origin(300000, 7000000, 10, 10)

    criar_raster(
        arquivo_red,
        np.ones((2, 2), dtype="uint16"),
        grade,
    )

    criar_raster(
        arquivo_mascara,
        np.array([[1, 0], [1, 1]], dtype="uint8"),
        grade,
        mascara_interna=np.array(
            [[255, 255], [0, 255]],
            dtype="uint8",
        ),
    )

    ndvi = np.ma.array(
        [[0.7, 0.6], [0.5, 0.4]],
        mask=[[False, False], [False, True]],
        dtype="float32",
    )

    resultado = aplicar_qualidade(ndvi, arquivo_red, arquivo_mascara)

    np.testing.assert_array_equal(
        np.ma.getmaskarray(resultado),
        [[False, True], [True, True]],
    )
    assert resultado[0, 0] == pytest.approx(0.7)


def test_rejeita_mascara_desalinhada(tmp_path):
    arquivo_red = tmp_path / "red.tif"
    arquivo_mascara = tmp_path / "qualidade.tif"

    criar_raster(
        arquivo_red,
        np.ones((2, 2), dtype="uint16"),
        from_origin(300000, 7000000, 10, 10),
    )

    criar_raster(
        arquivo_mascara,
        np.ones((2, 2), dtype="uint8"),
        from_origin(300010, 7000000, 10, 10),
    )

    ndvi = np.ma.array(np.full((2, 2), 0.5, dtype="float32"))

    with pytest.raises(ValueError, match="nao esta alinhada"):
        aplicar_qualidade(ndvi, arquivo_red, arquivo_mascara)


def test_rejeita_valor_invalido_na_mascara(tmp_path):
    arquivo_red = tmp_path / "red.tif"
    arquivo_mascara = tmp_path / "qualidade.tif"
    grade = from_origin(300000, 7000000, 10, 10)

    criar_raster(
        arquivo_red,
        np.ones((2, 2), dtype="uint16"),
        grade,
    )

    criar_raster(
        arquivo_mascara,
        np.array([[1, 2], [0, 1]], dtype="uint8"),
        grade,
    )

    ndvi = np.ma.array(np.full((2, 2), 0.5, dtype="float32"))

    with pytest.raises(ValueError, match="apenas 0 ou 1"):
        aplicar_qualidade(ndvi, arquivo_red, arquivo_mascara)