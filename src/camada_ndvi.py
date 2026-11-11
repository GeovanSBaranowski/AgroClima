import folium
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.vrt import WarpedVRT
from rasterio.warp import transform_bounds


def colorir_ndvi(ndvi):
    ndvi = np.ma.asarray(ndvi)

    if ndvi.ndim != 2:
        raise ValueError("O NDVI precisa ser uma matriz bidimensional")

    valores = np.ma.getdata(ndvi)

    validos = (
        ~np.ma.getmaskarray(ndvi)
        & np.isfinite(valores)
    )

    imagem = np.zeros((*ndvi.shape, 4), dtype="uint8")

    azul = validos & (valores >= -1) & (valores < 0)
    bege = validos & (valores >= 0) & (valores < 0.2)
    verde_claro = validos & (valores >= 0.2) & (valores < 0.5)
    verde_escuro = validos & (valores >= 0.5) & (valores <= 1)
    fora_intervalo = validos & ((valores < -1) | (valores > 1))

    imagem[azul] = [45, 110, 180, 255]
    imagem[bege] = [220, 200, 160, 255]
    imagem[verde_claro] = [150, 200, 80, 255]
    imagem[verde_escuro] = [30, 120, 55, 255]
    imagem[fora_intervalo] = [150, 60, 170, 255]

    return imagem


def preparar_imagem_ndvi(arquivo_raster, tamanho_maximo=1400):
    if tamanho_maximo < 1:
        raise ValueError("O tamanho maximo precisa ser positivo")

    with rasterio.open(arquivo_raster) as origem:
        if origem.crs is None:
            raise ValueError("O NDVI precisa informar suas coordenadas")

        if origem.count != 1 or origem.dtypes != ("float32",):
            raise ValueError("A visualizacao espera uma banda float32")

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
                1,
                out_shape=(altura, largura),
                masked=True,
                resampling=Resampling.nearest,
            )

            alpha = projetado.read(
                2,
                out_shape=(altura, largura),
                resampling=Resampling.nearest,
            )

            dados = np.ma.array(
                np.ma.getdata(dados),
                mask=np.ma.getmaskarray(dados) | (alpha == 0),
            )

            oeste, sul, leste, norte = transform_bounds(
                projetado.crs,
                "EPSG:4326",
                *projetado.bounds,
            )

    imagem = colorir_ndvi(dados)

    limites = [
        [sul, oeste],
        [norte, leste],
    ]

    return imagem, limites


def adicionar_camada_ndvi(mapa, arquivo_raster):
    imagem, limites = preparar_imagem_ndvi(arquivo_raster)

    folium.map.CustomPane(
        name="ndvi",
        z_index=360,
        pointer_events=False,
    ).add_to(mapa)

    return folium.raster_layers.ImageOverlay(
        image=imagem,
        bounds=limites,
        name="NDVI Sentinel-2",
        origin="upper",
        opacity=1,
        mercator_project=False,
        pane="ndvi",
        attribution="Copernicus Sentinel-2 | Earth Search",
    ).add_to(mapa)