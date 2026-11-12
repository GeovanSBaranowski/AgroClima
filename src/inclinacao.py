import math

import numpy as np


def calcular_inclinacao(elevacao, resolucao_x, resolucao_y):
    elevacao = np.ma.asarray(elevacao)

    if elevacao.ndim != 2:
        raise ValueError("A elevacao precisa ser uma matriz bidimensional")

    if elevacao.shape[0] < 3 or elevacao.shape[1] < 3:
        raise ValueError("A matriz precisa ter pelo menos 3 linhas e 3 colunas")

    for resolucao in (resolucao_x, resolucao_y):
        if (
            isinstance(resolucao, bool)
            or not isinstance(resolucao, (int, float))
            or not math.isfinite(resolucao)
            or resolucao <= 0
        ):
            raise ValueError("As resolucoes precisam ser positivas e finitas")

    valores = np.ma.getdata(elevacao).astype("float64")

    validos = (
        ~np.ma.getmaskarray(elevacao)
        & np.isfinite(valores)
    )

    # O calculo so e feito na parte interna da matriz.
    centro_valido = (
        validos[1:-1, 1:-1]
        & validos[1:-1, :-2]
        & validos[1:-1, 2:]
        & validos[:-2, 1:-1]
        & validos[2:, 1:-1]
    )

    # A distancia entre os dois vizinhos e de dois pixels.
    diferenca_x = (
        valores[1:-1, 2:] - valores[1:-1, :-2]
    ) / (2 * resolucao_x)

    diferenca_y = (
        valores[2:, 1:-1] - valores[:-2, 1:-1]
    ) / (2 * resolucao_y)

    intensidade = np.hypot(diferenca_x, diferenca_y)

    # arctan transforma a razao de alturas e distancias em angulo.
    angulos = np.degrees(np.arctan(intensidade))

    resultado = np.zeros(elevacao.shape, dtype="float32")
    mascara = np.ones(elevacao.shape, dtype=bool)

    resultado[1:-1, 1:-1] = angulos.astype("float32")
    mascara[1:-1, 1:-1] = ~centro_valido

    return np.ma.array(resultado, mask=mascara)