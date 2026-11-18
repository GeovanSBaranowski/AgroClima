import json
from html import escape

import folium

from preparar_solo import preparar_solo

CORES_SOLO = {
    "CAMBISSOLO": "#d95f02",
    "LATOSSOLO": "#e6ab02",
    "NEOSSOLO": "#a6761d",
    "NITOSSOLO": "#b2182b",
    "OUTROS": "#888888",
    "CORPO D'ÁGUA CONTINENTAL": "#377eb8",
}

COR_NAO_IDENTIFICADA = "#dddddd"


def estilizar_solo(feicao):
    propriedades = feicao.get("properties", {})
    categoria = propriedades.get("leg_ordem")

    cor = CORES_SOLO.get(categoria, COR_NAO_IDENTIFICADA)

    return {
        "fillColor": cor,
        "color": "#555555",
        "weight": 1,
        "fillOpacity": 0.6,
    }


def texto_para_popup(valor):
    if valor is None:
        return "Nao informado"

    texto = str(valor).strip()

    if not texto:
        return "Nao informado"

    return escape(texto)


def quantidade_para_popup(valor):
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)

    return texto_para_popup(valor)

def adicionar_camada_solo(mapa, solos):
    preparados = preparar_solo(solos)

    dados_geojson = json.loads(
        preparados.to_json()
    )

    for feicao in dados_geojson["features"]:
        propriedades = feicao["properties"]

        propriedades["exibicao_categoria"] = texto_para_popup(
            propriedades.get("leg_ordem")
        )
        propriedades["exibicao_legenda"] = texto_para_popup(
            propriedades.get("legenda")
        )
        propriedades["exibicao_componentes"] = quantidade_para_popup(
            propriedades.get("val_ncompo")
        )
        propriedades["exibicao_textura"] = texto_para_popup(
            propriedades.get("textura")
        )

    return folium.GeoJson(
        data=dados_geojson,
        name="Unidades de solo - IBGE",
        style_function=estilizar_solo,
        show=False,
        popup=folium.GeoJsonPopup(
            fields=[
                "exibicao_categoria",
                "exibicao_legenda",
                "exibicao_componentes",
                "exibicao_textura",
            ],
            aliases=[
                "Categoria:",
                "Unidade de mapeamento:",
                "Numero de componentes:",
                "Textura:",
            ],
        ),
    ).add_to(mapa)