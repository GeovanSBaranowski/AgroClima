import folium
import rasterio
from rasterio.enums import Resampling
from rasterio.vrt import WarpedVRT
from rasterio.warp import transform_bounds


def preparar_imagem_satelite(arquivo_raster, tamanho_maximo=1400):
    if tamanho_maximo < 1:
        raise ValueError("O tamanho maximo precisa ser positivo")

    with rasterio.open(arquivo_raster) as origem:
        if origem.crs is None:
            raise ValueError("A imagem precisa informar seu sistema de coordenadas")

        if origem.dtypes != ("uint8", "uint8", "uint8"):
            raise ValueError("Esta visualizacao espera tres bandas uint8")

        with WarpedVRT(
            origem,
            crs="EPSG:3857",
            add_alpha=True,
            resampling=Resampling.nearest,
        ) as projetado:
            fator = min(
                1.0,
                tamanho_maximo / max(projetado.width, projetado.height),
            )

            largura = max(1, round(projetado.width * fator))
            altura = max(1, round(projetado.height * fator))

            dados = projetado.read(
                out_shape=(4, altura, largura),
                resampling=Resampling.nearest,
            )

            oeste, sul, leste, norte = transform_bounds(
                projetado.crs,
                "EPSG:4326",
                *projetado.bounds,
            )

    imagem_rgba = dados.transpose(1, 2, 0)

    limites = [
        [sul, oeste],
        [norte, leste],
    ]

    return imagem_rgba, limites


def adicionar_camada_satelite(mapa, arquivo_raster):
    imagem, limites = preparar_imagem_satelite(arquivo_raster)

    folium.map.CustomPane(
        name="satelite",
        z_index=350,
        pointer_events=False,
    ).add_to(mapa)

    return folium.raster_layers.ImageOverlay(
        image=imagem,
        bounds=limites,
        name="Imagem Sentinel-2",
        origin="upper",
        opacity=1,
        mercator_project=False,
        pane="satelite",
        attribution="Copernicus Sentinel-2 | Earth Search",
    ).add_to(mapa)