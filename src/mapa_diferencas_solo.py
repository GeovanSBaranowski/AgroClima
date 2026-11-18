import argparse
from pathlib import Path

import folium
import geopandas as gpd


def adicionar_area(mapa, geometria, nome, cor):
    if geometria.is_empty:
        return

    dados = gpd.GeoSeries(
        [geometria],
        crs="EPSG:32722",
    ).to_crs("EPSG:4326")

    folium.GeoJson(
        data=dados.__geo_interface__,
        name=nome,
        style_function=lambda feicao: {
            "color": cor,
            "weight": 1,
            "fillColor": cor,
            "fillOpacity": 0.7,
        },
    ).add_to(mapa)


def gerar_mapa_diferencas(arquivo_solo, arquivo_limite, arquivo_saida):
    solos = gpd.read_file(arquivo_solo)
    limite = gpd.read_file(arquivo_limite)

    if solos.crs is None or limite.crs is None:
        raise ValueError("Os arquivos precisam informar suas coordenadas")

    solos_utm = solos.to_crs("EPSG:32722")
    limite_utm = limite.to_crs("EPSG:32722")

    area_solo = solos_utm.geometry.union_all()
    area_limite = limite_utm.geometry.union_all()

    solo_fora = area_solo.difference(area_limite)
    limite_sem_solo = area_limite.difference(area_solo)

    mapa = folium.Map(
        location=[-27.10, -52.62],
        tiles="OpenStreetMap",
        control_scale=True,
    )

    camada_limite = folium.GeoJson(
        data=limite.to_crs("EPSG:4326").__geo_interface__,
        name="Limite municipal detalhado",
        style_function=lambda feicao: {
            "color": "#3388ff",
            "weight": 2,
            "fill": False,
        },
    ).add_to(mapa)

    adicionar_area(
        mapa,
        solo_fora,
        "Solo fora do limite",
        "#d73027",
    )

    adicionar_area(
        mapa,
        limite_sem_solo,
        "Limite sem poligono de solo",
        "#ffb000",
    )

    folium.LayerControl(collapsed=False).add_to(mapa)
    mapa.fit_bounds(camada_limite.get_bounds())

    arquivo_saida = Path(arquivo_saida)

    if arquivo_saida.exists():
        raise FileExistsError(f"O arquivo ja existe: {arquivo_saida}")

    arquivo_saida.parent.mkdir(parents=True, exist_ok=True)
    mapa.save(str(arquivo_saida))

    print(f"Mapa salvo em: {arquivo_saida.resolve()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Mostra as diferencas entre solo e limite municipal"
    )

    parser.add_argument("--solo", type=Path, required=True)
    parser.add_argument("--limite", type=Path, required=True)
    parser.add_argument("--saida", type=Path, required=True)

    argumentos = parser.parse_args()

    gerar_mapa_diferencas(
        argumentos.solo,
        argumentos.limite,
        argumentos.saida,
    )