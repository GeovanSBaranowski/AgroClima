import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from avaliar_qualidade_satelite import (
    avaliar_cobertura,
    resumir_classificacao,
)

POLIGONO_TESTE = {
    "type": "Polygon",
    "coordinates": [[
        [0, 0],
        [2, 0],
        [2, 2],
        [0, 2],
        [0, 0],
    ]],
}


def criar_raster_teste(caminho, dados, mascara=None):
    imagem = np.array(dados, dtype="uint8")

    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):  # noqa: SIM117
        with rasterio.open(
            caminho,
            "w",
            driver="GTiff",
            height=imagem.shape[0],
            width=imagem.shape[1],
            count=1,
            dtype="uint8",
            crs="EPSG:4326",
            transform=from_origin(0, imagem.shape[0], 1, 1),
        ) as destino:
            destino.write(imagem, 1)

            if mascara is not None:
                destino.write_mask(
                    np.array(mascara, dtype="uint8")
                )

    return caminho


def test_resumo_ignora_mascara_e_zero(tmp_path):
    arquivo = criar_raster_teste(
        tmp_path / "classificacao.tif",
        dados=[
            [4, 4, 6],
            [9, 0, 10],
        ],
        mascara=[
            [255, 255, 255],
            [255, 255, 0],
        ],
    )

    resumo = resumir_classificacao(arquivo)

    assert resumo["total_pixels_avaliados"] == 4

    classes = {
        registro["codigo"]: registro
        for registro in resumo["classes"]
    }

    assert set(classes) == {4, 6, 9}

    assert classes[4]["quantidade_pixels"] == 2
    assert classes[6]["quantidade_pixels"] == 1
    assert classes[9]["quantidade_pixels"] == 1

    assert classes[4]["percentual"] == pytest.approx(50)
    assert classes[6]["percentual"] == pytest.approx(25)
    assert classes[9]["percentual"] == pytest.approx(25)


@pytest.mark.parametrize(
    "dados,mascara,pixels_com_dados",
    [
        ([[4, 4], [4, 4]], None, 4),
        ([[4], [4]], None, 2),
        ([[4, 0], [4, 4]], None, 3),
        (
            [[4, 4], [4, 4]],
            [[255, 0], [255, 255]],
            3,
        ),
        ([[9, 9], [9, 9]], None, 4),
    ],
    ids=[
        "cobertura_completa",
        "arquivo_cobre_metade",
        "pixel_sem_dados",
        "pixel_mascarado",
        "nuvem_conta_como_dado",
    ],
)
def test_cobertura_considera_poligono_inteiro(
    tmp_path,
    dados,
    mascara,
    pixels_com_dados,
):
    arquivo = criar_raster_teste(
        tmp_path / "cobertura.tif",
        dados,
        mascara,
    )

    resultado = avaliar_cobertura(
        arquivo,
        POLIGONO_TESTE,
    )

    assert resultado["pixels_esperados"] == 4
    assert resultado["pixels_com_dados"] == pixels_com_dados
    assert resultado["pixels_sem_dados"] == 4 - pixels_com_dados

    assert resultado["cobertura_percentual"] == pytest.approx(
        pixels_com_dados / 4 * 100
    )


def test_cobertura_respeita_buraco_no_poligono(tmp_path):
    arquivo = criar_raster_teste(
        tmp_path / "poligono_com_buraco.tif",
        dados=[
            [4, 4, 4],
            [4, 0, 4],
            [4, 4, 4],
        ],
    )

    poligono = {
        "type": "Polygon",
        "coordinates": [
            [
                [0, 0],
                [3, 0],
                [3, 3],
                [0, 3],
                [0, 0],
            ],
            [
                [1, 1],
                [1, 2],
                [2, 2],
                [2, 1],
                [1, 1],
            ],
        ],
    }

    resultado = avaliar_cobertura(arquivo, poligono)

    assert resultado["pixels_esperados"] == 8
    assert resultado["pixels_com_dados"] == 8
    assert resultado["pixels_sem_dados"] == 0
    assert resultado["cobertura_percentual"] == pytest.approx(100)


def test_resumo_rejeita_ausencia_de_classificacao(tmp_path):
    arquivo = criar_raster_teste(
        tmp_path / "sem_dados.tif",
        dados=[[0, 0]],
    )

    with pytest.raises(ValueError, match="nao possui pixels"):
        resumir_classificacao(arquivo)


def test_resumo_rejeita_codigo_desconhecido(tmp_path):
    arquivo = criar_raster_teste(
        tmp_path / "codigo_invalido.tif",
        dados=[[12]],
    )

    with pytest.raises(ValueError, match="Codigo SCL inesperado"):
        resumir_classificacao(arquivo)