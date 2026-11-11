import math

import numpy as np


def converter_reflectancia(valores, metadados):
    valores = np.ma.asarray(valores)

    if valores.ndim != 2 or valores.dtype != np.dtype("uint16"):
        raise ValueError("A banda precisa ser uma matriz uint16")

    if metadados.get("tipo_dados") != "uint16":
        raise ValueError("Os metadados precisam informar uint16")

    for campo in ("escala", "deslocamento", "nodata"):
        valor = metadados.get(campo)

        if (
            isinstance(valor, bool)
            or not isinstance(valor, (int, float))
            or not math.isfinite(valor)
        ):
            raise ValueError(f"Metadado invalido: {campo}")

    escala = metadados["escala"]
    deslocamento = metadados["deslocamento"]
    nodata = metadados["nodata"]

    if escala <= 0:
        raise ValueError("A escala precisa ser positiva")

    if nodata != int(nodata) or not 0 <= nodata <= 65535:
        raise ValueError("O nodata precisa ser um valor uint16")

    dados_brutos = np.ma.getdata(valores)

    invalidos = (
        np.ma.getmaskarray(valores)
        | (dados_brutos == nodata)
    )

    dados_float = np.ma.array(
        dados_brutos,
        mask=invalidos,
    ).astype("float32")

    reflectancia = dados_float * escala + deslocamento

    return reflectancia.astype("float32")