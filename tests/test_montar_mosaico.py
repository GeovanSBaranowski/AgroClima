import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from montar_mosaico import montar_mosaico


@pytest.mark.parametrize("quantidade_bandas", [1, 3])
def test_mosaico_preserva_prioridade_mascara_e_zero(
    tmp_path,
    quantidade_bandas,
):
    primeira = tmp_path / "primeira.tif"
    segunda = tmp_path / "segunda.tif"
    saida = tmp_path / "mosaico.tif"

    perfil = {
        "driver": "GTiff",
        "height": 3,
        "width": 3,
        "count": quantidade_bandas,
        "dtype": "uint8",
        "crs": "EPSG:32722",
    }

    dados_primeira = np.full(
        (quantidade_bandas, 3, 3),
        10,
        dtype="uint8",
    )
    dados_primeira[:, 0, 0] = 0

    mascara_primeira = np.full((3, 3), 255, dtype="uint8")
    mascara_primeira[1, 0] = 0

    dados_segunda = np.full(
        (quantidade_bandas, 3, 3),
        100,
        dtype="uint8",
    )

    mascara_segunda = np.full((3, 3), 255, dtype="uint8")
    mascara_segunda[0, 0] = 0

    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):
        with rasterio.open(
            primeira,
            "w",
            transform=from_origin(300010, 6999990, 10, 10),
            **perfil,
        ) as arquivo:
            arquivo.write(dados_primeira)
            arquivo.write_mask(mascara_primeira)

        with rasterio.open(
            segunda,
            "w",
            transform=from_origin(300000, 7000000, 10, 10),
            **perfil,
        ) as arquivo:
            arquivo.write(dados_segunda)
            arquivo.write_mask(mascara_segunda)

    montar_mosaico([primeira, segunda], saida)

    with rasterio.open(saida) as resultado:
        assert resultado.width == 4
        assert resultado.height == 4
        assert resultado.count == quantidade_bandas
        assert resultado.dtypes == ("uint8",) * quantidade_bandas
        assert resultado.crs.to_epsg() == 32722
        assert resultado.nodata is None

        assert resultado.transform == from_origin(
            300000, 7000000, 10, 10
        )

        imagem = resultado.read()
        mascara = resultado.dataset_mask()

    # O zero valido da primeira imagem deve ser preservado.
    assert np.all(imagem[:, 1, 1] == 0)

    # Onde a primeira imagem e invalida, usamos a segunda.
    assert np.all(imagem[:, 2, 1] == 100)

    # Na sobreposicao valida, a primeira imagem tem prioridade.
    assert np.all(imagem[:, 1, 2] == 10)

    mascara_esperada = np.array(
        [
            [0, 255, 255, 0],
            [255, 255, 255, 255],
            [255, 255, 255, 255],
            [0, 255, 255, 255],
        ],
        dtype="uint8",
    )

    np.testing.assert_array_equal(
        mascara,
        mascara_esperada,
    )