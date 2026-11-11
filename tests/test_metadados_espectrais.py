import pytest

from metadados_espectrais import obter_metadados_banda


@pytest.fixture
def pagina():
    return {
        "features": [
            {
                "id": "cena_teste",
                "assets": {
                    "red": {
                        "href": "https://exemplo.test/red.tif",
                        "raster:bands": [
                            {
                                "scale": 0.0002,
                                "offset": -0.05,
                                "nodata": 0,
                                "data_type": "uint16",
                            }
                        ],
                    },
                    "nir": {
                        "href": "https://exemplo.test/nir.tif",
                        "raster:bands": [
                            {
                                "scale": 0.0001,
                                "offset": -0.1,
                                "nodata": 0,
                                "data_type": "uint16",
                            }
                        ],
                    },
                },
            }
        ]
    }


@pytest.mark.parametrize(
    "nome,escala,deslocamento",
    [
        ("red", 0.0002, -0.05),
        ("nir", 0.0001, -0.1),
    ],
)
def test_obtem_metadados_da_banda(
    pagina,
    nome,
    escala,
    deslocamento,
):
    resultado = obter_metadados_banda(
        pagina,
        "cena_teste",
        nome,
    )

    assert resultado["id_cena"] == "cena_teste"
    assert resultado["asset"] == nome
    assert resultado["escala"] == pytest.approx(escala)
    assert resultado["deslocamento"] == pytest.approx(deslocamento)
    assert resultado["nodata"] == 0
    assert resultado["tipo_dados"] == "uint16"
    assert resultado["url"] == f"https://exemplo.test/{nome}.tif"


@pytest.mark.parametrize("campo", ["offset", "nodata"])
def test_rejeita_metadado_ausente(pagina, campo):
    banda = pagina["features"][0]["assets"]["red"]["raster:bands"][0]
    del banda[campo]

    with pytest.raises(ValueError, match=campo):
        obter_metadados_banda(pagina, "cena_teste", "red")


@pytest.mark.parametrize("escala_invalida", [0, float("nan"), True])
def test_rejeita_escala_invalida(pagina, escala_invalida):
    banda = pagina["features"][0]["assets"]["red"]["raster:bands"][0]
    banda["scale"] = escala_invalida

    with pytest.raises(ValueError):
        obter_metadados_banda(pagina, "cena_teste", "red")


@pytest.mark.parametrize("bandas_invalidas", [None, []])
def test_rejeita_lista_de_bandas_invalida(pagina, bandas_invalidas):
    asset = pagina["features"][0]["assets"]["red"]
    asset["raster:bands"] = bandas_invalidas

    with pytest.raises(ValueError, match="metadados de uma banda"):
        obter_metadados_banda(pagina, "cena_teste", "red")


def test_rejeita_cena_ausente(pagina):
    with pytest.raises(ValueError, match="Cena nao encontrada"):
        obter_metadados_banda(pagina, "outra_cena", "red")