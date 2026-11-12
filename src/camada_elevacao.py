import folium
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.vrt import WarpedVRT
from rasterio.warp import transform_bounds


def colorir_elevacao(elevacao):
    elevacao = np.ma.asarray(elevacao)

    if elevacao.ndim != 2:
        raise ValueError(
            "A elevacao precisa ser uma matriz bidimensional"
        )

    valores = np.ma.getdata(elevacao)

    validos = (
        ~np.ma.getmaskarray(elevacao)
        & np.isfinite(valores)
    )

    # Os canais sao vermelho, verde, azul e transparencia.
    imagem = np.zeros((*elevacao.shape, 4), dtype="uint8")

    abaixo_400 = validos & (valores < 400)
    de_400_a_500 = validos & (valores >= 400) & (valores < 500)
    de_500_a_600 = validos & (valores >= 500) & (valores < 600)
    de_600_a_700 = validos & (valores >= 600) & (valores < 700)
    acima_700 = validos & (valores >= 700)

    imagem[abaixo_400] = [40, 120, 75, 255]
    imagem[de_400_a_500] = [150, 190, 95, 255]
    imagem[de_500_a_600] = [235, 215, 125, 255]
    imagem[de_600_a_700] = [215, 145, 75, 255]
    imagem[acima_700] = [135, 80, 55, 255]

    return imagem


def preparar_imagem_elevacao(arquivo_raster, tamanho_maximo=1400):
    if tamanho_maximo < 1:
        raise ValueError("O tamanho maximo precisa ser positivo")

    with rasterio.open(arquivo_raster) as origem:
        if origem.crs is None:
            raise ValueError("A elevacao precisa informar suas coordenadas")

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

    imagem = colorir_elevacao(dados)

    limites = [
        [sul, oeste],
        [norte, leste],
    ]

    return imagem, limites


def adicionar_camada_elevacao(mapa, arquivo_raster):
    imagem, limites = preparar_imagem_elevacao(arquivo_raster)

    folium.map.CustomPane(
        name="elevacao",
        z_index=370,
        pointer_events=False,
    ).add_to(mapa)

    return folium.raster_layers.ImageOverlay(
        image=imagem,
        bounds=limites,
        name="Elevacao Copernicus",
        origin="upper",
        opacity=1,
        mercator_project=False,
        pane="elevacao",
        attribution="Copernicus DEM | Earth Search",
    ).add_to(mapa)