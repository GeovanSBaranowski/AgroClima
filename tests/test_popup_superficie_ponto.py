from gerar_mapa import montar_popup_superficie


def test_mostra_elevacao_e_inclinacao():
    popup = montar_popup_superficie({
        "elevacao": 641.438,
        "inclinacao": 6.1082,
    })

    assert "Fonte: Copernicus DEM" in popup
    assert "Elevacao: 641.44 m" in popup
    assert "Inclinacao: 6.11 graus" in popup


def test_mostra_valor_indisponivel_e_preserva_zero():
    popup = montar_popup_superficie({
        "elevacao": None,
        "inclinacao": 0.0,
    })

    assert "Elevacao: Indisponivel" in popup
    assert "Inclinacao: 0.00 graus" in popup


def test_nao_mostra_campo_que_nao_foi_informado():
    popup = montar_popup_superficie({
        "elevacao": 641.0,
    })

    assert "Elevacao: 641.00 m" in popup
    assert "Inclinacao:" not in popup