import pytest

from coletar_limite import validar_limite


def criar_limite_exemplo():
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "codarea": "4204202",
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [-52.70, -27.20],
                            [-52.60, -27.20],
                            [-52.60, -27.10],
                            [-52.70, -27.10],
                            [-52.70, -27.20],
                        ],
                    ],
                },
            },
        ],
    }


@pytest.mark.parametrize(
    "tipo_geometria",
    ["Polygon", "MultiPolygon"],
)
def test_aceita_limite_esperado(tipo_geometria):
    dados = criar_limite_exemplo()
    geometria = dados["features"][0]["geometry"]

    if tipo_geometria == "MultiPolygon":
        geometria["type"] = "MultiPolygon"
        geometria["coordinates"] = [geometria["coordinates"]]

    validar_limite(dados, "4204202")


def test_rejeita_tipo_de_documento_inesperado():
    dados = criar_limite_exemplo()
    dados["type"] = "Feature"

    with pytest.raises(ValueError, match="FeatureCollection"):
        validar_limite(dados, "4204202")


def test_rejeita_colecao_vazia():
    dados = criar_limite_exemplo()
    dados["features"] = []

    with pytest.raises(ValueError, match="exatamente um municipio"):
        validar_limite(dados, "4204202")


def test_rejeita_municipio_diferente():
    dados = criar_limite_exemplo()
    dados["features"][0]["properties"]["codarea"] = "9999999"

    with pytest.raises(ValueError, match="municipio recebido"):
        validar_limite(dados, "4204202")


def test_rejeita_geometria_de_ponto():
    dados = criar_limite_exemplo()
    dados["features"][0]["geometry"] = {
        "type": "Point",
        "coordinates": [-52.62, -27.10],
    }

    with pytest.raises(ValueError, match="representar uma area"):
        validar_limite(dados, "4204202")


def test_rejeita_coordenadas_vazias():
    dados = criar_limite_exemplo()
    dados["features"][0]["geometry"]["coordinates"] = []

    with pytest.raises(ValueError, match="sem coordenadas"):
        validar_limite(dados, "4204202")