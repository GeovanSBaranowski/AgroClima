import folium
import geopandas as gpd
from shapely.geometry import Polygon

from camada_solo import (
    COR_NAO_IDENTIFICADA,
    CORES_SOLO,
    adicionar_camada_solo,
    estilizar_solo,
    quantidade_para_popup,
    texto_para_popup,
)


def test_escolhe_cor_da_categoria_conhecida():
    feicao = {
        "properties": {
            "leg_ordem": "CAMBISSOLO",
        }
    }

    estilo = estilizar_solo(feicao)

    assert estilo["fillColor"] == CORES_SOLO["CAMBISSOLO"]


def test_usa_cor_padrao_para_categoria_desconhecida():
    feicao = {
        "properties": {
            "leg_ordem": "CATEGORIA NOVA",
        }
    }

    estilo = estilizar_solo(feicao)

    assert estilo["fillColor"] == COR_NAO_IDENTIFICADA


def test_usa_cor_padrao_quando_categoria_esta_ausente():
    feicao = {
        "properties": {
            "leg_ordem": None,
        }
    }

    estilo = estilizar_solo(feicao)

    assert estilo["fillColor"] == COR_NAO_IDENTIFICADA


def test_adiciona_camada_preservando_atributos():
    poligono = Polygon([
        (-52.70, -27.10),
        (-52.69, -27.10),
        (-52.69, -27.09),
        (-52.70, -27.09),
        (-52.70, -27.10),
    ])

    solos = gpd.GeoDataFrame(
        {
            "leg_ordem": ["CAMBISSOLO"],
            "componente": ["Descricao de exemplo"],
        },
        geometry=[poligono],
        crs="EPSG:4674",
    )

    mapa = folium.Map(location=[-27.10, -52.70])

    camada = adicionar_camada_solo(mapa, solos)

    assert camada.layer_name == "Unidades de solo - IBGE"
    assert camada.show is False

    propriedades = camada.data["features"][0]["properties"]

    assert propriedades["leg_ordem"] == "CAMBISSOLO"
    assert propriedades["componente"] == "Descricao de exemplo"

    # A tabela recebida nao teve seu sistema de origem alterado.
    assert solos.crs.to_epsg() == 4674

def test_texto_para_popup_trata_valores_ausentes():
    assert texto_para_popup(None) == "Nao informado"
    assert texto_para_popup("") == "Nao informado"
    assert texto_para_popup("   ") == "Nao informado"


def test_texto_para_popup_trata_caracteres_especiais():
    assert texto_para_popup("<solo> & agua") == (
        "&lt;solo&gt; &amp; agua"
    )


def test_prepara_popup_para_todos_os_poligonos():
    primeiro = Polygon([
        (-52.70, -27.10),
        (-52.69, -27.10),
        (-52.69, -27.09),
        (-52.70, -27.09),
        (-52.70, -27.10),
    ])

    segundo = Polygon([
        (-52.68, -27.10),
        (-52.67, -27.10),
        (-52.67, -27.09),
        (-52.68, -27.09),
        (-52.68, -27.10),
    ])

    solos = gpd.GeoDataFrame(
        {
            "leg_ordem": ["CAMBISSOLO", "OUTROS"],
            "legenda": ["Solo de exemplo", "Área Urbana"],
            "val_ncompo": [2, None],
            "textura": ["Argilosa", None],
        },
        geometry=[primeiro, segundo],
        crs="EPSG:4674",
    )

    mapa = folium.Map(location=[-27.10, -52.70])

    camada = adicionar_camada_solo(mapa, solos)

    feicoes = camada.data["features"]

    assert len(feicoes) == 2

    primeira = feicoes[0]["properties"]
    segunda = feicoes[1]["properties"]

    assert primeira["exibicao_categoria"] == "CAMBISSOLO"
    assert primeira["exibicao_legenda"] == "Solo de exemplo"
    assert primeira["exibicao_textura"] == "Argilosa"

    assert segunda["exibicao_categoria"] == "OUTROS"
    assert segunda["exibicao_legenda"] == "Área Urbana"
    assert segunda["exibicao_textura"] == "Nao informado"

    # O atributo original tambem continua disponivel.
    assert segunda["leg_ordem"] == "OUTROS"


def test_formata_quantidade_inteira_para_popup():
    assert quantidade_para_popup(4.0) == "4"
    assert quantidade_para_popup(2) == "2"


def test_formata_quantidade_ausente_para_popup():
    assert quantidade_para_popup(None) == "Nao informado"