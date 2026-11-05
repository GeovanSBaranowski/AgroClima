import json
from pathlib import Path

import folium

from coletar_limite import validar_limite


if __name__ == "__main__":

    raiz_projeto = Path(__file__).resolve().parent.parent

    pasta_raw = raiz_projeto / "data" / "raw" / "ibge_malhas"

    arquivos = sorted(
        pasta_raw.glob("chapeco_4204202_minima_*.geojson")
    )

    if not arquivos:
        raise FileNotFoundError(
            f"Nenhum limite de Chapeco encontrado em {pasta_raw}"
        )    

    arquivo_raw = arquivos[-1]

    dados = json.loads(
        arquivo_raw.read_text(encoding="utf-8")
    )

    validar_limite(dados, "4204202")

    ponto_referencia = [-27.10, -52.62]

    mapa = folium.Map(
        location=ponto_referencia,
        tiles="OpenStreetMap",
        control_scale=True,
    )

    limite = folium.GeoJson(
        data=dados,
        name="Limite municipal de Chapeco",
        tooltip="Chapeco - IBGE",
    ).add_to(mapa)

    folium.Marker(
        location=ponto_referencia,
        tooltip="Ponto da consulta meteorologica",
        popup="Coordenadas utilizadas nas consultas a NASA POWER.",
    ).add_to(mapa)

    mapa.fit_bounds(limite.get_bounds())

    pasta_mapas = raiz_projeto / "data" / "maps"
    pasta_mapas.mkdir(parents=True, exist_ok=True)

    arquivo_mapa = pasta_mapas / "chapeco.html"
    mapa.save(str(arquivo_mapa))

    print(f"Limite utilizado: {arquivo_raw}")
    print(f"Mapa salvo em: {arquivo_mapa}")