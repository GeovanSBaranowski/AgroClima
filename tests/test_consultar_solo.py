import geopandas as gpd
import numpy as np
from shapely.geometry import Polygon

from consultar_solo import consultar_solo_ponto, formatar_valor


def criar_unidades():
    primeiro = Polygon([
        (0, 0),
        (1, 0),
        (1, 1),
        (0, 1),
        (0, 0),
    ])

    segundo = Polygon([
        (1, 0),
        (2, 0),
        (2, 1),
        (1, 1),
        (1, 0),
    ])

    return gpd.GeoDataFrame(
        {
            "leg_ordem": ["CAMBISSOLO", "LATOSSOLO"],
        },
        geometry=[primeiro, segundo],
        crs="EPSG:4326",
    )


def test_encontra_unidade_que_cobre_o_ponto():
    solos = criar_unidades()

    resultado = consultar_solo_ponto(
        solos,
        latitude=0.5,
        longitude=0.5,
    )

    assert len(resultado) == 1
    assert resultado.iloc[0]["leg_ordem"] == "CAMBISSOLO"


def test_retorna_vazio_quando_ponto_esta_fora():
    solos = criar_unidades()

    resultado = consultar_solo_ponto(
        solos,
        latitude=0.5,
        longitude=3.0,
    )

    assert resultado.empty


def test_retorna_as_duas_unidades_na_borda_compartilhada():
    solos = criar_unidades()

    resultado = consultar_solo_ponto(
        solos,
        latitude=0.5,
        longitude=1.0,
    )

    assert len(resultado) == 2
    assert set(resultado["leg_ordem"]) == {
        "CAMBISSOLO",
        "LATOSSOLO",
    }

def test_formata_valores_ausentes():
    assert formatar_valor(None) == "Nao informado"
    assert formatar_valor(np.nan) == "Nao informado"
    assert formatar_valor("   ") == "Nao informado"


def test_preserva_valores_informados():
    assert formatar_valor(0) == "0"
    assert formatar_valor("Área Urbana") == "Área Urbana"