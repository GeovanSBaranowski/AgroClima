from datetime import date

import pytest

from metadados_cena import obter_data_cena_utc


def pagina_com_cena(data_hora):
    return {
        "features": [
            {
                "id": "cena_1",
                "properties": {
                    "datetime": data_hora,
                },
            }
        ]
    }


def test_le_data_de_observacao_utc():
    dados = pagina_com_cena("2024-02-01T13:40:02Z")

    resultado = obter_data_cena_utc(dados, "cena_1")

    assert resultado == date(2024, 2, 1)


def test_converte_fuso_antes_de_obter_a_data():
    dados = pagina_com_cena("2024-02-01T23:30:00-03:00")

    resultado = obter_data_cena_utc(dados, "cena_1")

    # 23h30 no fuso -03:00 corresponde a 02h30 do dia seguinte em UTC.
    assert resultado == date(2024, 2, 2)


@pytest.mark.parametrize("data_invalida", [None, "data-invalida"])
def test_rejeita_data_ausente_ou_invalida(data_invalida):
    dados = pagina_com_cena(data_invalida)

    with pytest.raises(ValueError):
        obter_data_cena_utc(dados, "cena_1")


def test_rejeita_data_sem_fuso_horario():
    dados = pagina_com_cena("2024-02-01T13:40:02")

    with pytest.raises(ValueError, match="fuso horario"):
        obter_data_cena_utc(dados, "cena_1")


def test_rejeita_cena_nao_encontrada():
    dados = pagina_com_cena("2024-02-01T13:40:02Z")

    with pytest.raises(ValueError, match="Era esperada uma cena"):
        obter_data_cena_utc(dados, "outra_cena")


def test_rejeita_identificador_duplicado():
    cena = {
        "id": "cena_1",
        "properties": {
            "datetime": "2024-02-01T13:40:02Z",
        },
    }

    dados = {
        "features": [cena, cena],
    }

    with pytest.raises(ValueError, match="Era esperada uma cena"):
        obter_data_cena_utc(dados, "cena_1")