import pytest

from normalizar_clima import normalizar_temperaturas


def criar_dados_teste(temperatura):
    return {
        "parameters": {
            "T2M": {"units": "C"}
        },
        "header": {
            "fill_value": -999.0,
            "time_standard": "UTC"
        },
        "geometry": {
            "coordinates": [-52.62, -27.1, 589.74]
        },
        "properties": {
            "parameter": {
                "T2M": {"20240101": temperatura}
            }
        }
    }

@pytest.mark.parametrize(
    "entrada,esperado",
    [
        (-999.0, None),
        (None, None),
        (0, 0),
        (23.54, 23.54)
    ],
)

def teste_normalizar_temperatura(entrada, esperado):
    dados = criar_dados_teste(entrada)
    registros = normalizar_temperaturas(dados)

    assert len(registros) == 1
    assert registros[0]["temperatura_c"] == esperado