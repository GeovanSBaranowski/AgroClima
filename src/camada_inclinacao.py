import folium
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.vrt import WarpedVRT
from rasterio.warp import transform_bounds


def colorir_inclinacao(inclinacao):
    inclinacao = np.ma.asarray(inclinacao)

    if inclinacao.ndim != 2:
        raise ValueError(
            "A inclinacao precisa ser uma matriz bidimensional"
        )

    valores = np.ma.getdata(inclinacao)

    validos = (
        ~np.ma.getmaskarray(inclinacao)
        & np.isfinite(valores)
    )

    imagem = np.zeros((*inclinacao.shape, 4), dtype="uint8")

    ate_5 = validos & (valores >= 0) & (valores < 5)
    de_5_a_10 = validos & (valores >= 5) & (valores < 10)
    de_10_a_20 = validos & (valores >= 10) & (valores < 20)
    de_20_a_30 = validos & (valores >= 20) & (valores < 30)
    de_30_a_90 = validos & (valores >= 30) & (valores < 90)
    fora_intervalo = validos & ((valores < 0) | (valores >= 90))

    imagem[ate_5] = [40, 120, 75, 255]
    imagem[de_5_a_10] = [150, 190, 95, 255]
    imagem[de_10_a_20] = [235, 215, 125, 255]
    imagem[de_20_a_30] = [215, 145, 75, 255]
    imagem[de_30_a_90] = [185, 60, 50, 255]
    imagem[fora_intervalo] = [150, 60, 170, 255]

    return imagem


def preparar_imagem_inclinacao(arquivo_raster, tamanho_maximo=1400):
    if tamanho_maximo < 1:
        raise ValueError("O tamanho maximo precisa ser positivo")

    with rasterio.open(arquivo_raster) as origem:
        if origem.crs is None:
            raise ValueError("A inclinacao precisa informar suas coordenadas")

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

    imagem = colorir_inclinacao(dados)

    limites = [
        [sul, oeste],
        [norte, leste],
    ]

    return imagem, limites



def adicionar_camada_inclinacao(mapa, arquivo_raster):
    imagem, limites = preparar_imagem_inclinacao(arquivo_raster)

    folium.map.CustomPane(
        name="inclinacao",
        z_index=380,
        pointer_events=False,
    ).add_to(mapa)

    return folium.raster_layers.ImageOverlay(
        image=imagem,
        bounds=limites,
        name="Inclinacao da superficie",
        origin="upper",
        opacity=1,
        mercator_project=False,
        pane="inclinacao",
        attribution="Copernicus DEM | Earth Search",
    ).add_to(mapa)