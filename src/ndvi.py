import numpy as np


def calcular_ndvi(vermelho, nir):
    vermelho = np.ma.asarray(vermelho)
    nir = np.ma.asarray(nir)

    if vermelho.ndim != 2 or nir.ndim != 2:
        raise ValueError("As bandas precisam ser matrizes bidimensionais")

    if vermelho.shape != nir.shape:
        raise ValueError("As bandas precisam ter as mesmas dimensoes")

    # Reunimos as posicoes invalidas de ambas as bandas.
    invalidos = (
        np.ma.getmaskarray(vermelho)
        | np.ma.getmaskarray(nir)
    )

    dados_vermelho = np.ma.getdata(vermelho).astype("float32")
    dados_nir = np.ma.getdata(nir).astype("float32")

    soma = dados_nir + dados_vermelho

    invalidos = invalidos | (soma == 0)

    invalidos = (
        invalidos
        | ~np.isfinite(dados_vermelho)
        | ~np.isfinite(dados_nir)
        | ~np.isfinite(soma)
    )

    resultado = np.zeros(vermelho.shape, dtype="float32")

    np.divide(
        dados_nir - dados_vermelho,
        soma,
        out=resultado,
        where=~invalidos,
    )

    return np.ma.array(resultado, mask=invalidos)