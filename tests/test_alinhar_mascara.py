import numpy as np
import rasterio
from rasterio.transform import from_origin

from alinhar_mascara import alinhar_mascara


def test_alinhamento_preserva_posicao_decisoes_e_disponibilidade(tmp_path):
    arquivo_mascara = tmp_path / "mascara_20m.tif"
    arquivo_referencia = tmp_path / "referencia_10m.tif"
    arquivo_saida = tmp_path / "mascara_alinhada.tif"

    dados_mascara = np.array(
        [
            [1, 0],
            [1, 1],
        ],
        dtype="uint8",
    )

    disponibilidade_mascara = np.array(
        [
            [255, 255],
            [0, 255],
        ],
        dtype="uint8",
    )

    disponibilidade_referencia = np.full(
        (4, 5),
        255,
        dtype="uint8",
    )
    disponibilidade_referencia[0, 1] = 0

    transformacao_referencia = from_origin(
        299990, 7000000, 10, 10
    )

    perfil = {
        "driver": "GTiff",
        "dtype": "uint8",
        "crs": "EPSG:32722",
    }

    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):
        with rasterio.open(
            arquivo_mascara,
            "w",
            height=2,
            width=2,
            count=1,
            transform=from_origin(300000, 7000000, 20, 20),
            **perfil,
        ) as destino:
            destino.write(dados_mascara, 1)
            destino.write_mask(disponibilidade_mascara)

        with rasterio.open(
            arquivo_referencia,
            "w",
            height=4,
            width=5,
            count=3,
            transform=transformacao_referencia,
            **perfil,
        ) as destino:
            destino.write(
                np.zeros((3, 4, 5), dtype="uint8")
            )
            destino.write_mask(disponibilidade_referencia)

    alinhar_mascara(
        arquivo_mascara,
        arquivo_referencia,
        arquivo_saida,
    )

    with rasterio.open(arquivo_saida) as resultado:
        decisoes = resultado.read(1)
        disponibilidade = resultado.dataset_mask()

        assert resultado.shape == (4, 5)
        assert resultado.count == 1
        assert resultado.dtypes == ("uint8",)
        assert resultado.crs.to_epsg() == 32722
        assert resultado.transform == transformacao_referencia
        assert resultado.nodata is None

    np.testing.assert_array_equal(
        decisoes,
        [
            [0, 0, 1, 0, 0],
            [0, 1, 1, 0, 0],
            [0, 0, 0, 1, 1],
            [0, 0, 0, 1, 1],
        ],
    )

    np.testing.assert_array_equal(
        disponibilidade,
        [
            [0, 0, 255, 255, 255],
            [0, 255, 255, 255, 255],
            [0, 0, 0, 255, 255],
            [0, 0, 0, 255, 255],
        ],
    )