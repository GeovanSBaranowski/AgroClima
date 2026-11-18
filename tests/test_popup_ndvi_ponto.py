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