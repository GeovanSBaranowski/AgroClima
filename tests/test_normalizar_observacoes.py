import pytest

from normalizar_clima import normalizar_observacoes


def criar_dados_exemplo():
    return {
        "geometry": {
            "coordinates": [-52.62, -27.10, 589.74],
        },
        "header": {
            "fill_value": -999.0,
            "time_standard": "UTC",
        },
        "parameters": {
            "T2M": {"units": "C"},
            "RH2M": {"units": "%"},
            "PRECTOTCORR": {"units": "mm/day"},
        },
        "properties": {
            "parameter": {
                "T2M": {"20240201": 24.39},
                "RH2M": {"20240201": 77.12},
                "PRECTOTCORR": {"20240201": 3.41},
            },
        },
    }

def test_normaliza_tres_variaveis():
    dados = criar_dados_exemplo()

    registros = normalizar_observacoes(dados)

    assert len(registros) == 3

    observacoes = {}

    for registro in registros:
        codigo = registro["variavel"]
        observacoes[codigo] = (
            registro["valor"],
            registro["unidade"],
        )

        assert registro["data_observacao"] == "2024-02-01"
        assert registro["latitude"] == -27.10
        assert registro["longitude"] == -52.62
        assert registro["fonte"] == "NASA_POWER"
        assert registro["referencia_temporal"] == "UTC"

    assert observacoes == {
        "T2M": (24.39, "C"),
        "RH2M": (77.12, "%"),
        "PRECTOTCORR": (3.41, "mm/day"),
    }

@pytest.mark.parametrize(
    "valor_recebido, valor_esperado",
    [
        (-999.0, None),
        (None, None),
        (0, 0),
        (24.39, 24.39),
    ],
)
def test_trata_valores_ausentes(valor_recebido, valor_esperado):
    dados = criar_dados_exemplo()

    dados["properties"]["parameter"] = {
        "T2M": {"20240201": valor_recebido},
    }

    registros = normalizar_observacoes(dados)

    assert len(registros) == 1
    assert registros[0]["valor"] == valor_esperado

def test_rejeita_unidade_inesperada():
    dados = criar_dados_exemplo()
    dados["parameters"]["RH2M"]["units"] = "C"

    with pytest.raises(ValueError, match="Unidade inesperada"):
        normalizar_observacoes(dados)