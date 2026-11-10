import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from aplicar_mascara import aplicar_mascara


@pytest.fixture
def entradas(tmp_path):
    arquivo_imagem = tmp_path / "imagem.tif"
    arquivo_mascara = tmp_path / "qualidade.tif"

    cores = np.full((3, 2, 3), 100, dtype="uint8")
    cores[:, 0, 0] = 0

    disponibilidade_imagem = np.array(
        [
            [255, 255, 255],
            [255, 0, 255],
        ],
        dtype="uint8",
    )

    decisoes = np.array(
        [
            [1, 0, 1],
            [1, 1, 0],
        ],
        dtype="uint8",
    )

    disponibilidade_qualidade = np.array(
        [
            [255, 255, 0],
            [255, 255, 255],
        ],
        dtype="uint8",
    )

    perfil = {
        "driver": "GTiff",
        "height": 2,
        "width": 3,
        "dtype": "uint8",
        "crs": "EPSG:32722",
        "transform": from_origin(300000, 7000000, 20, 20),
    }

    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):
        with rasterio.open(
            arquivo_imagem,
            "w",
            count=3,
            **perfil,
        ) as destino:
            destino.write(cores)
            destino.write_mask(disponibilidade_imagem)

        with rasterio.open(
            arquivo_mascara,
            "w",
            count=1,
            **perfil,
        ) as destino:
            destino.write(decisoes, 1)
            destino.write_mask(disponibilidade_qualidade)

    return {
        "imagem": arquivo_imagem,
        "mascara": arquivo_mascara,
        "saida": tmp_path / "resultado.tif",
        "cores": cores,
    }


def test_aplicacao_preserva_cores_e_combina_mascaras(entradas):
    resumo = aplicar_mascara(
        entradas["imagem"],
        entradas["mascara"],
        entradas["saida"],
    )

    with rasterio.open(entradas["saida"]) as resultado:
        assert resultado.count == 3
        assert resultado.shape == (2, 3)
        assert resultado.dtypes == ("uint8", "uint8", "uint8")
        assert resultado.crs.to_epsg() == 32722
        assert resultado.nodata is None

        assert resultado.transform == from_origin(
            300000, 7000000, 20, 20
        )

        np.testing.assert_array_equal(
            resultado.read(),
            entradas["cores"],
        )

        np.testing.assert_array_equal(
            resultado.dataset_mask(),
            [
                [255, 0, 0],
                [255, 0, 0],
            ],
        )

    assert resumo["pixels_com_imagem"] == 5
    assert resumo["pixels_mantidos"] == 2
    assert resumo["pixels_excluidos_pela_regra"] == 2
    assert resumo["pixels_sem_qualidade"] == 1
    assert resumo["percentual_mantido"] == pytest.approx(40)


def test_rejeita_mascara_com_grade_deslocada(entradas):
    with rasterio.open(entradas["mascara"], "r+") as mascara:
        mascara.transform = from_origin(
            300010, 7000000, 20, 20
        )

    with pytest.raises(ValueError, match="alinhada"):
        aplicar_mascara(
            entradas["imagem"],
            entradas["mascara"],
            entradas["saida"],
        )

    assert not entradas["saida"].exists()


def test_aceita_todos_os_pixels_excluidos(entradas):
    with rasterio.open(entradas["mascara"], "r+") as mascara:
        mascara.write(
            np.zeros((2, 3), dtype="uint8"),
            1,
        )

    resumo = aplicar_mascara(
        entradas["imagem"],
        entradas["mascara"],
        entradas["saida"],
    )

    with rasterio.open(entradas["saida"]) as resultado:
        assert np.count_nonzero(resultado.dataset_mask()) == 0

    assert resumo["pixels_com_imagem"] == 5
    assert resumo["pixels_mantidos"] == 0
    assert resumo["pixels_excluidos_pela_regra"] == 4
    assert resumo["pixels_sem_qualidade"] == 1
    assert resumo["percentual_mantido"] == pytest.approx(0)
    