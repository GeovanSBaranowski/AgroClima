import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from camada_elevacao import colorir_elevacao, preparar_imagem_elevacao


def test_atribui_cor_para_cada_faixa():
    elevacao = np.ma.array(
        [[350.0, 450.0, 550.0, 650.0, 750.0]],
        dtype="float32",
    )

    imagem = colorir_elevacao(elevacao)

    np.testing.assert_array_equal(
        imagem[0],
        [
            [40, 120, 75, 255],
            [150, 190, 95, 255],
            [235, 215, 125, 255],
            [215, 145, 75, 255],
            [135, 80, 55, 255],
        ],
    )


def test_limites_das_faixas_e_zero_valido():
    elevacao = np.ma.array(
        [[0.0, 400.0, 500.0, 600.0, 700.0]],
        dtype="float32",
    )

    imagem = colorir_elevacao(elevacao)

    np.testing.assert_array_equal(
        imagem[0],
        [
            [40, 120, 75, 255],
            [150, 190, 95, 255],
            [235, 215, 125, 255],
            [215, 145, 75, 255],
            [135, 80, 55, 255],
        ],
    )


def test_valores_mascarados_e_nao_finitos_sao_transparentes():
    elevacao = np.ma.array(
        [[450.0, 550.0, np.nan]],
        mask=[[False, True, False]],
        dtype="float32",
    )

    imagem = colorir_elevacao(elevacao)

    assert imagem[0, 0, 3] == 255
    assert imagem[0, 1, 3] == 0
    assert imagem[0, 2, 3] == 0


def test_rejeita_matriz_com_uma_dimensao():
    elevacao = np.ma.array([400.0, 500.0], dtype="float32")

    with pytest.raises(ValueError, match="bidimensional"):
        colorir_elevacao(elevacao)


def test_prepara_imagem_com_reprojecao_e_transparencia(tmp_path):
    arquivo = tmp_path / "elevacao.tif"

    dados = np.array(
        [
            [0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0],
            [550.0, 550.0, 550.0, 550.0],
            [550.0, 550.0, 550.0, 550.0],
        ],
        dtype="float32",
    )

    mascara = np.array(
        [
            [255, 255, 255, 255],
            [255, 255, 255, 255],
            [255, 255, 0, 0],
            [255, 255, 0, 0],
        ],
        dtype="uint8",
    )

    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):  # noqa: SIM117
        with rasterio.open(
            arquivo,
            "w",
            driver="GTiff",
            width=4,
            height=4,
            count=1,
            dtype="float32",
            crs="EPSG:4326",
            transform=from_origin(-52.7, -27.0, 0.001, 0.001),
        ) as destino:
            destino.write(dados, 1)
            destino.write_mask(mascara)

    imagem, limites = preparar_imagem_elevacao(arquivo)

    assert imagem.ndim == 3
    assert imagem.shape[2] == 4

    # Deve haver pelo menos um pixel transparente.
    assert np.any(imagem[:, :, 3] == 0)

    # Zero valido deve aparecer em verde-escuro.
    assert np.any(
        np.all(imagem == [40, 120, 75, 255], axis=2)
    )

    # O valor 550 deve aparecer em amarelo.
    assert np.any(
        np.all(imagem == [235, 215, 125, 255], axis=2)
    )

    assert limites[0][0] < limites[1][0]  # sul < norte
    assert limites[0][1] < limites[1][1]  # oeste < leste


def test_rejeita_tamanho_maximo_invalido():
    with pytest.raises(ValueError, match="tamanho maximo"):
        preparar_imagem_elevacao(
            "arquivo_inexistente.tif",
            tamanho_maximo=0,
        )