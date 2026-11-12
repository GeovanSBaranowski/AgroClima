import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from camada_inclinacao import colorir_inclinacao, preparar_imagem_inclinacao


def test_atribui_cor_para_cada_faixa():
    inclinacao = np.ma.array(
        [[2.0, 7.0, 15.0, 25.0, 45.0]],
        dtype="float32",
    )

    imagem = colorir_inclinacao(inclinacao)

    np.testing.assert_array_equal(
        imagem[0],
        [
            [40, 120, 75, 255],
            [150, 190, 95, 255],
            [235, 215, 125, 255],
            [215, 145, 75, 255],
            [185, 60, 50, 255],
        ],
    )


def test_limites_das_faixas_e_zero_valido():
    inclinacao = np.ma.array(
        [[0.0, 5.0, 10.0, 20.0, 30.0]],
        dtype="float32",
    )

    imagem = colorir_inclinacao(inclinacao)

    np.testing.assert_array_equal(
        imagem[0],
        [
            [40, 120, 75, 255],
            [150, 190, 95, 255],
            [235, 215, 125, 255],
            [215, 145, 75, 255],
            [185, 60, 50, 255],
        ],
    )


def test_destaca_valores_fora_do_intervalo():
    inclinacao = np.ma.array(
        [[-1.0, 90.0]],
        dtype="float32",
    )

    imagem = colorir_inclinacao(inclinacao)

    np.testing.assert_array_equal(
        imagem[0],
        [
            [150, 60, 170, 255],
            [150, 60, 170, 255],
        ],
    )


def test_mascarados_e_nao_finitos_ficam_transparentes():
    inclinacao = np.ma.array(
        [[5.0, 10.0, np.nan]],
        mask=[[False, True, False]],
        dtype="float32",
    )

    imagem = colorir_inclinacao(inclinacao)

    assert imagem[0, 0, 3] == 255
    assert imagem[0, 1, 3] == 0
    assert imagem[0, 2, 3] == 0


def test_rejeita_matriz_com_uma_dimensao():
    inclinacao = np.ma.array([5.0, 10.0], dtype="float32")

    with pytest.raises(ValueError, match="bidimensional"):
        colorir_inclinacao(inclinacao)


def test_prepara_imagem_com_reprojecao_e_transparencia(tmp_path):
    arquivo = tmp_path / "inclinacao.tif"

    dados = np.zeros((8, 8), dtype="float32")
    dados[4:, :] = 25.0

    mascara = np.full((8, 8), 255, dtype="uint8")
    mascara[4:, 4:] = 0

    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):  # noqa: SIM117
        with rasterio.open(
            arquivo,
            "w",
            driver="GTiff",
            width=8,
            height=8,
            count=1,
            dtype="float32",
            crs="EPSG:32722",
            transform=from_origin(317000, 7000000, 30, 30),
        ) as destino:
            destino.write(dados, 1)
            destino.write_mask(mascara)

    imagem, limites = preparar_imagem_inclinacao(arquivo)

    assert imagem.ndim == 3
    assert imagem.shape[2] == 4

    # Uma parte da imagem deve permanecer transparente.
    assert np.any(imagem[:, :, 3] == 0)

    # Zero grau valido deve aparecer em verde-escuro.
    assert np.any(
        np.all(imagem == [40, 120, 75, 255], axis=2)
    )

    # Vinte e cinco graus devem aparecer em laranja.
    assert np.any(
        np.all(imagem == [215, 145, 75, 255], axis=2)
    )

    assert limites[0][0] < limites[1][0]  # sul < norte
    assert limites[0][1] < limites[1][1]  # oeste < leste


def test_rejeita_tamanho_maximo_invalido():
    with pytest.raises(ValueError, match="tamanho maximo"):
        preparar_imagem_inclinacao(
            "arquivo_inexistente.tif",
            tamanho_maximo=0,
        )