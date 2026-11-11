import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from camada_ndvi import colorir_ndvi, preparar_imagem_ndvi


def test_atribui_cor_para_cada_faixa():
    ndvi = np.ma.array(
        [[-0.5, 0.1, 0.3, 0.8, 1.2]],
        dtype="float32",
    )

    imagem = colorir_ndvi(ndvi)

    np.testing.assert_array_equal(
        imagem,
        [[
            [45, 110, 180, 255],
            [220, 200, 160, 255],
            [150, 200, 80, 255],
            [30, 120, 55, 255],
            [150, 60, 170, 255],
        ]],
    )


def test_limites_das_faixas():
    ndvi = np.ma.array(
        [[-1.0, 0.0, 0.2, 0.5, 1.0]],
        dtype="float32",
    )

    imagem = colorir_ndvi(ndvi)

    np.testing.assert_array_equal(
        imagem[0],
        [
            [45, 110, 180, 255],
            [220, 200, 160, 255],
            [150, 200, 80, 255],
            [30, 120, 55, 255],
            [30, 120, 55, 255],
        ],
    )


def test_deixa_mascarados_e_nao_finitos_transparentes():
    ndvi = np.ma.array(
        [[0.7, 0.3, np.nan]],
        mask=[[False, True, False]],
        dtype="float32",
    )

    imagem = colorir_ndvi(ndvi)

    assert imagem[0, 0, 3] == 255
    assert imagem[0, 1, 3] == 0
    assert imagem[0, 2, 3] == 0


def test_rejeita_matriz_com_uma_dimensao():
    ndvi = np.ma.array([0.1, 0.5], dtype="float32")

    with pytest.raises(ValueError, match="bidimensional"):
        colorir_ndvi(ndvi)


def test_prepara_imagem_preservando_zero_e_transparencia(tmp_path):
    arquivo = tmp_path / "ndvi.tif"

    dados = np.array(
        [
            [0.0, 0.7],
            [0.3, 0.5],
        ],
        dtype="float32",
    )

    mascara = np.array(
        [
            [255, 255],
            [0, 255],
        ],
        dtype="uint8",
    )

    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):  # noqa: SIM117
        with rasterio.open(
            arquivo,
            "w",
            driver="GTiff",
            width=2,
            height=2,
            count=1,
            dtype="float32",
            crs="EPSG:3857",
            transform=from_origin(0, 20, 10, 10),
        ) as destino:
            destino.write(dados, 1)
            destino.write_mask(mascara)

    imagem, limites = preparar_imagem_ndvi(arquivo)

    assert imagem.shape == (2, 2, 4)

    # NDVI zero valido: bege e visivel.
    np.testing.assert_array_equal(
        imagem[0, 0],
        [220, 200, 160, 255],
    )

    # Pixel mascarado: transparente.
    assert imagem[1, 0, 3] == 0

    # NDVI 0,7: verde-escuro e visivel.
    np.testing.assert_array_equal(
        imagem[0, 1],
        [30, 120, 55, 255],
    )

    assert limites[0][0] < limites[1][0]  # sul < norte
    assert limites[0][1] < limites[1][1]  # oeste < leste


def test_rejeita_tamanho_maximo_invalido():
    with pytest.raises(ValueError, match="tamanho maximo"):
        preparar_imagem_ndvi("arquivo_inexistente.tif", tamanho_maximo=0)