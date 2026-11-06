import pytest

from normalizar_satelite import normalizar_cenas


def criar_cena(id_cena="cena-teste", nuvens=24.5):
    return {
        "id": id_cena,
        "collection": "sentinel-2-c1-l2a",
        "properties": {
            "datetime": "2024-02-06T13:40:05Z",
            "platform": "sentinel-2b",
            "eo:cloud_cover": nuvens,
        },
        "assets": {
            "visual": {
                "href": "https://example.com/visual.tif",
            },
            "scl": {
                "href": "https://example.com/scl.tif",
            },
        },
    }


def test_normaliza_todas_as_cenas():
    dados = {
        "type": "FeatureCollection",
        "features": [
            criar_cena(id_cena="cena-1", nuvens=24.5),
            criar_cena(id_cena="cena-2", nuvens=0),
        ],
    }

    registros = normalizar_cenas(dados)

    assert len(registros) == 2

    assert registros[0] == {
        "id_cena": "cena-1",
        "colecao": "sentinel-2-c1-l2a",
        "data_hora_observacao": "2024-02-06T13:40:05Z",
        "plataforma": "sentinel-2b",
        "nuvens_cena_percentual": 24.5,
        "url_visual": "https://example.com/visual.tif",
        "url_classificacao": "https://example.com/scl.tif",
    }

    assert registros[1]["id_cena"] == "cena-2"
    assert registros[1]["nuvens_cena_percentual"] == 0


def test_pagina_vazia_retorna_lista_vazia():
    dados = {
        "type": "FeatureCollection",
        "features": [],
    }

    assert normalizar_cenas(dados) == []


@pytest.mark.parametrize("nuvens", [-1, 101])
def test_rejeita_porcentagem_de_nuvens_invalida(nuvens):
    dados = {
        "type": "FeatureCollection",
        "features": [criar_cena(nuvens=nuvens)],
    }

    with pytest.raises(
        ValueError,
        match="Porcentagem de nuvens invalida",
    ):
        normalizar_cenas(dados)