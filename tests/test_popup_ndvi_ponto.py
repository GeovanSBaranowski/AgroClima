from datetime import date

import pytest

from gerar_mapa import montar_popup_ndvi


@pytest.mark.parametrize(
    ("valor", "texto_esperado"),
    [
        (0.2901, "NDVI: 0.2901"),
        (0.0, "NDVI: 0.0000"),
        (None, "NDVI indisponivel neste ponto."),
    ],
)
def test_mostra_valor_ou_indisponibilidade(valor, texto_esperado):
    popup = montar_popup_ndvi(valor)

    assert texto_esperado in popup
    assert "Data da imagem nao verificada" in popup

@pytest.mark.parametrize(
    ("avaliacao", "mensagem"),
    [
        (
            {
                "situacao": "coincide",
                "data_ndvi": date(2024, 2, 1),
            },
            "A data coincide com a data climatica.",
        ),
        (
            {
                "situacao": "diferente",
                "data_ndvi": date(2024, 2, 2),
            },
            "A data difere da data climatica.",
        ),
        (
            {
                "situacao": "ausente",
                "data_ndvi": None,
            },
            "Data da imagem nao verificada: tag ausente.",
        ),
        (
            {
                "situacao": "invalida",
                "data_ndvi": None,
            },
            "Data da imagem nao verificada: tag invalida.",
        ),
    ],
)
def test_mostra_situacao_da_data(avaliacao, mensagem):
    popup = montar_popup_ndvi(0.2901, avaliacao)

    assert mensagem in popup