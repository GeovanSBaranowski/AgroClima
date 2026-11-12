import numpy as np
import pytest

from inclinacao import calcular_inclinacao


def test_superficie_plana_tem_inclinacao_zero():
    elevacao = np.ma.array(
        np.full((3, 3), 500.0),
    )

    resultado = calcular_inclinacao(
        elevacao,
        resolucao_x=10,
        resolucao_y=10,
    )

    assert resultado[1, 1] == pytest.approx(0.0)
    assert resultado.count() == 1

    # As bordas nao possuem todos os vizinhos necessarios.
    assert np.ma.getmaskarray(resultado)[0, :].all()
    assert np.ma.getmaskarray(resultado)[-1, :].all()


def test_rampa_de_45_graus_na_direcao_horizontal():
    elevacao = np.ma.array(
        [
            [0.0, 10.0, 20.0],
            [0.0, 10.0, 20.0],
            [0.0, 10.0, 20.0],
        ]
    )

    resultado = calcular_inclinacao(
        elevacao,
        resolucao_x=10,
        resolucao_y=10,
    )

    assert resultado[1, 1] == pytest.approx(45.0)


def test_considera_resolucao_vertical_diferente():
    elevacao = np.ma.array(
        [
            [0.0, 0.0, 0.0],
            [10.0, 10.0, 10.0],
            [20.0, 20.0, 20.0],
        ]
    )

    resultado = calcular_inclinacao(
        elevacao,
        resolucao_x=10,
        resolucao_y=20,
    )

    angulo_esperado = np.degrees(np.arctan(0.5))

    assert resultado[1, 1] == pytest.approx(angulo_esperado)


def test_mascara_pixel_quando_falta_um_vizinho():
    elevacao = np.ma.array(
        np.full((5, 5), 500.0),
        mask=np.zeros((5, 5), dtype=bool),
    )

    elevacao.mask[2, 2] = True

    resultado = calcular_inclinacao(
        elevacao,
        resolucao_x=10,
        resolucao_y=10,
    )

    mascara = np.ma.getmaskarray(resultado)

    # O proprio pixel e os calculos que dependem dele sao invalidados.
    assert mascara[2, 2]
    assert mascara[2, 1]
    assert mascara[2, 3]
    assert mascara[1, 2]
    assert mascara[3, 2]

    # Este pixel nao depende da posicao mascarada.
    assert not mascara[1, 1]
    assert resultado[1, 1] == pytest.approx(0.0)


def test_rejeita_resolucao_zero():
    elevacao = np.ma.array(np.zeros((3, 3)))

    with pytest.raises(ValueError, match="positivas e finitas"):
        calcular_inclinacao(
            elevacao,
            resolucao_x=0,
            resolucao_y=10,
        )