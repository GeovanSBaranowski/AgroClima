import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from mascara_qualidade import (
    criar_mascara_qualidade,
    salvar_mascara_qualidade,
)


def test_seleciona_categorias_de_superficie():
    classificacao = np.array(
        [
            [0, 1, 2, 3],
            [4, 5, 6, 7],
            [8, 9, 10, 11],
        ],
        dtype="uint8",
    )

    resultado = criar_mascara_qualidade(classificacao)

    esperado = np.array([
        [False, False, False, False],
        [True, True, True, False],
        [False, False, False, False],
    ])

    np.testing.assert_array_equal(resultado, esperado)


def test_exclui_pixel_mascarado_mesmo_com_categoria_aceita():
    classificacao = np.ma.array(
        [[4, 5, 6]],
        mask=[[False, True, False]],
        dtype="uint8",
    )

    resultado = criar_mascara_qualidade(classificacao)

    np.testing.assert_array_equal(
        resultado,
        [[True, False, True]],
    )


def test_rejeita_classificacao_sem_linhas_e_colunas():
    classificacao = np.array([4, 5, 6], dtype="uint8")

    with pytest.raises(ValueError, match="linhas e colunas"):
        criar_mascara_qualidade(classificacao)

def gravar_scl_teste(caminho, dados, mascara=None):
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
            crs="EPSG:32722",
            transform=from_origin(300000, 7000000, 20, 20),
        ) as destino:
            destino.write(imagem, 1)

            if mascara is not None:
                destino.write_mask(
                    np.array(mascara, dtype="uint8")
                )

    return caminho


def test_gravacao_distingue_excluido_de_sem_dados(tmp_path):
    origem = gravar_scl_teste(
        tmp_path / "scl.tif",
        dados=[
            [4, 9, 6],
            [5, 0, 4],
        ],
        mascara=[
            [255, 255, 255],
            [255, 255, 0],
        ],
    )

    saida = tmp_path / "qualidade.tif"

    resumo = salvar_mascara_qualidade(origem, saida)

    with rasterio.open(saida) as resultado:
        decisoes = resultado.read(1)
        disponibilidade = resultado.dataset_mask()

        assert resultado.count == 1
        assert resultado.dtypes == ("uint8",)
        assert resultado.width == 3
        assert resultado.height == 2
        assert resultado.crs.to_epsg() == 32722
        assert resultado.nodata is None

        assert resultado.transform == from_origin(
            300000, 7000000, 20, 20
        )

        assert resultado.tags()["classes_mantidas"] == "4,5,6"

    np.testing.assert_array_equal(
        decisoes,
        [
            [1, 0, 1],
            [1, 0, 0],
        ],
    )

    np.testing.assert_array_equal(
        disponibilidade,
        [
            [255, 255, 255],
            [255, 0, 0],
        ],
    )

    assert resumo["pixels_com_dados"] == 4
    assert resumo["pixels_mantidos"] == 3
    assert resumo["pixels_excluidos"] == 1
    assert resumo["percentual_mantido"] == pytest.approx(75)


def test_gravacao_aceita_todos_os_pixels_excluidos(tmp_path):
    origem = gravar_scl_teste(
        tmp_path / "somente_nuvens.tif",
        dados=[
            [9, 9],
            [9, 9],
        ],
    )

    saida = tmp_path / "qualidade.tif"

    resumo = salvar_mascara_qualidade(origem, saida)

    with rasterio.open(saida) as resultado:
        np.testing.assert_array_equal(
            resultado.read(1),
            np.zeros((2, 2), dtype="uint8"),
        )

        np.testing.assert_array_equal(
            resultado.dataset_mask(),
            np.full((2, 2), 255, dtype="uint8"),
        )

    assert resumo["pixels_com_dados"] == 4
    assert resumo["pixels_mantidos"] == 0
    assert resumo["pixels_excluidos"] == 4
    assert resumo["percentual_mantido"] == pytest.approx(0)