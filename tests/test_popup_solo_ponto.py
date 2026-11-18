from datetime import date

import pandas as pd

from gerar_mapa import montar_popup_integrado, montar_popup_solo


def test_mostra_unidade_encontrada():
    unidades = pd.DataFrame([
        {
            "leg_ordem": "CAMBISSOLO",
            "legenda": "Cambissolo de exemplo",
        }
    ])

    popup = montar_popup_solo(unidades)

    assert "Fonte: IBGE | BDiA" in popup
    assert "Categoria: CAMBISSOLO" in popup
    assert "Unidade: Cambissolo de exemplo" in popup


def test_informa_quando_nao_ha_unidade():
    unidades = pd.DataFrame()

    popup = montar_popup_solo(unidades)

    assert "Nenhuma unidade de solo encontrada" in popup


def test_mostra_todas_as_unidades_e_trata_texto():
    unidades = pd.DataFrame([
        {
            "leg_ordem": "CAMBISSOLO",
            "legenda": "<solo>",
        },
        {
            "leg_ordem": "LATOSSOLO",
            "legenda": None,
        },
    ])

    popup = montar_popup_solo(unidades)

    assert "CAMBISSOLO" in popup
    assert "LATOSSOLO" in popup
    assert "&lt;solo&gt;" in popup
    assert "Unidade: Nao informado" in popup

def test_mostra_solo_mesmo_sem_observacoes_climaticas():
    unidades = pd.DataFrame([
        {
            "leg_ordem": "OUTROS",
            "legenda": "Área Urbana",
        }
    ])

    popup = montar_popup_integrado(
        registros=[],
        data_observacao=date(2024, 2, 1),
        unidades_solo=unidades,
    )

    assert "Sem observações disponíveis" in popup
    assert "Categoria: OUTROS" in popup
    assert "Unidade: Área Urbana" in popup


def test_sem_consulta_de_solo_mostra_apenas_clima():
    popup = montar_popup_integrado(
        registros=[],
        data_observacao=date(2024, 2, 1),
    )

    assert "Sem observações disponíveis" in popup
    assert "Fonte: NASA POWER" in popup
    assert "Unidades de mapeamento no ponto" not in popup