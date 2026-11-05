from datetime import date

import pytest

from gerar_mapa import montar_popup


def criar_registro(variavel, valor, unidade):
    return {
        "variavel": variavel,
        "valor": valor,
        "unidade": unidade,
    }


def test_popup_exibe_observacoes():
    registros = [
        criar_registro("T2M", 24.39, "C"),
        criar_registro("RH2M", 77.12, "%"),
        criar_registro("PRECTOTCORR", 3.41, "mm/day"),
    ]

    conteudo = montar_popup(registros, date(2024, 2, 1))

    assert "Observações de 01/02/2024" in conteudo
    assert "Fonte: NASA POWER | UTC" in conteudo
    assert "Temperatura do ar: 24.39 C" in conteudo
    assert "Umidade relativa do ar: 77.12 %" in conteudo
    assert "Precipitação: 3.41 mm/day" in conteudo


def test_popup_informa_ausencia_de_observacoes():
    conteudo = montar_popup([], date(2024, 2, 8))

    assert "Observações de 08/02/2024" in conteudo
    assert "Sem observações disponíveis para esta data." in conteudo


@pytest.mark.parametrize(
    "valor, texto_esperado",
    [
        (0, "0.00 mm/day"),
        (None, "Sem medição"),
    ],
)
def test_popup_diferencia_zero_de_valor_ausente(
    valor,
    texto_esperado,
):
    registros = [
        criar_registro("PRECTOTCORR", valor, "mm/day"),
    ]

    conteudo = montar_popup(registros, date(2024, 2, 1))

    assert f"Precipitação: {texto_esperado}" in conteudo


def test_popup_preserva_caracteres_especiais_como_texto():
    registros = [
        criar_registro("TESTE<1>", 1, "u&v"),
    ]

    conteudo = montar_popup(registros, date(2024, 2, 1))

    assert "TESTE&lt;1&gt;: 1.00 u&amp;v" in conteudo
    assert "TESTE<1>" not in conteudo