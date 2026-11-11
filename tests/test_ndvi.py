import numpy as np
import pytest

from ndvi import calcular_ndvi


def test_calcula_ndvi_de_um_pixel():
    vermelho = np.ma.array([[0.2]], dtype="float32")
    nir = np.ma.array([[0.4]], dtype="float32")

    resultado = calcular_ndvi(vermelho, nir)

    assert resultado[0, 0] == pytest.approx(1 / 3)
    assert not np.ma.getmaskarray(resultado)[0, 0]


def test_mascara_pixel_se_uma_das_bandas_for_invalida():
    vermelho = np.ma.array(
        [[0.2, 0.3]],
        mask=[[False, True]],
        dtype="float32",
    )
    nir = np.ma.array(
        [[0.4, 0.5]],
        mask=[[False, False]],
        dtype="float32",
    )

    resultado = calcular_ndvi(vermelho, nir)

    np.testing.assert_array_equal(
        np.ma.getmaskarray(resultado),
        [[False, True]],
    )


def test_mascara_divisao_por_zero():
    vermelho = np.ma.array([[0.0]], dtype="float32")
    nir = np.ma.array([[0.0]], dtype="float32")

    resultado = calcular_ndvi(vermelho, nir)

    assert np.ma.getmaskarray(resultado)[0, 0]


def test_aceita_zero_valido_quando_a_soma_nao_e_zero():
    vermelho = np.ma.array([[0.0]], dtype="float32")
    nir = np.ma.array([[0.4]], dtype="float32")

    resultado = calcular_ndvi(vermelho, nir)

    assert resultado[0, 0] == pytest.approx(1.0)
    assert not np.ma.getmaskarray(resultado)[0, 0]


def test_mascara_valor_nao_finito():
    vermelho = np.ma.array([[np.nan]], dtype="float32")
    nir = np.ma.array([[0.4]], dtype="float32")

    resultado = calcular_ndvi(vermelho, nir)

    assert np.ma.getmaskarray(resultado)[0, 0]


def test_rejeita_dimensoes_diferentes():
    vermelho = np.ma.array([[0.2, 0.3]], dtype="float32")
    nir = np.ma.array([[0.4]], dtype="float32")

    with pytest.raises(ValueError, match="mesmas dimensoes"):
        calcular_ndvi(vermelho, nir)