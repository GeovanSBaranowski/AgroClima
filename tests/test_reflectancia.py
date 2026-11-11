import numpy as np
import pytest

from reflectancia import converter_reflectancia


@pytest.fixture
def metadados():
    return {
        "escala": 0.0001,
        "deslocamento": -0.1,
        "nodata": 0,
        "tipo_dados": "uint16",
    }


def test_converte_valores_e_preserva_posicoes_invalidas(metadados):
    valores = np.ma.array(
        [
            [0, 1000, 3000],
            [5000, 1000, 9000],
        ],
        mask=[
            [False, False, False],
            [True, False, False],
        ],
        dtype="uint16",
    )

    resultado = converter_reflectancia(valores, metadados)

    assert resultado.dtype == np.dtype("float32")

    np.testing.assert_array_equal(
        np.ma.getmaskarray(resultado),
        [
            [True, False, False],
            [True, False, False],
        ],
    )

    np.testing.assert_allclose(
        resultado.compressed(),
        [0.0, 0.2, 0.0, 0.8],
        atol=0.000001,
    )

    # A entrada continua com seus valores e sua mascara originais.
    assert valores.dtype == np.dtype("uint16")
    assert not np.ma.getmaskarray(valores)[0, 0]
    assert np.ma.getmaskarray(valores)[1, 0]


def test_utiliza_os_ajustes_informados(metadados):
    metadados["escala"] = 0.0002
    metadados["deslocamento"] = -0.05

    valores = np.ma.array([[1000]], dtype="uint16")

    resultado = converter_reflectancia(valores, metadados)

    assert resultado[0, 0] == pytest.approx(0.15, abs=0.000001)


def test_rejeita_valores_ja_convertidos(metadados):
    valores = np.ma.array([[0.2]], dtype="float32")

    with pytest.raises(ValueError, match="matriz uint16"):
        converter_reflectancia(valores, metadados)


@pytest.mark.parametrize("escala_invalida", [0, float("nan")])
def test_rejeita_escala_invalida(metadados, escala_invalida):
    metadados["escala"] = escala_invalida
    valores = np.ma.array([[1000]], dtype="uint16")

    with pytest.raises(ValueError):
        converter_reflectancia(valores, metadados)


def test_rejeita_metadado_ausente(metadados):
    del metadados["deslocamento"]
    valores = np.ma.array([[1000]], dtype="uint16")

    with pytest.raises(ValueError, match="deslocamento"):
        converter_reflectancia(valores, metadados)