import json

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from montar_mosaico_ndvi import montar_mosaico_ndvi


def criar_ndvi(caminho, dados, mascara, origem_x, id_cena):
    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):  # noqa: SIM117
        with rasterio.open(
            caminho,
            "w",
            driver="GTiff",
            width=2,
            height=2,
            count=1,
            dtype="float32",
            crs="EPSG:32722",
            transform=from_origin(origem_x, 7000000, 10, 10),
        ) as destino:
            destino.write(np.array(dados, dtype="float32"), 1)
            destino.write_mask(np.array(mascara, dtype="uint8"))

            destino.update_tags(
                id_cena=id_cena,
                produto="NDVI",
                qualidade="SCL aplicada",
            )


def test_mosaico_preserva_valores_mascaras_e_prioridade(tmp_path):
    primeira = tmp_path / "primeira.tif"
    segunda = tmp_path / "segunda.tif"
    saida = tmp_path / "mosaico.tif"

    criar_ndvi(
        primeira,
        dados=[[0.0, 0.2], [0.3, 0.4]],
        mascara=[[255, 0], [255, 255]],
        origem_x=300000,
        id_cena="cena_1",
    )

    criar_ndvi(
        segunda,
        dados=[[0.6, 0.7], [0.8, 0.9]],
        mascara=[[255, 255], [255, 0]],
        origem_x=300010,
        id_cena="cena_2",
    )

    montar_mosaico_ndvi([primeira, segunda], saida)

    with rasterio.open(saida) as arquivo:
        resultado = arquivo.read(1, masked=True)

        assert arquivo.dtypes == ("float32",)
        assert resultado.shape == (2, 3)

        np.testing.assert_array_equal(
            np.ma.getmaskarray(resultado),
            [[False, False, False], [False, False, True]],
        )

        # O zero da primeira cena continua valido.
        assert resultado[0, 0] == pytest.approx(0.0)

        # A primeira cena estava mascarada: usa a segunda.
        assert resultado[0, 1] == pytest.approx(0.6)

        # As duas tinham valores validos: prioriza a primeira.
        assert resultado[1, 1] == pytest.approx(0.4)

        assert resultado[0, 2] == pytest.approx(0.7)
        assert resultado[1, 0] == pytest.approx(0.3)

        assert json.loads(arquivo.tags()["cenas_origem"]) == [
            "cena_1",
            "cena_2",
        ]


def test_nao_sobrescreve_arquivo_de_entrada(tmp_path):
    entrada = tmp_path / "cena.tif"

    criar_ndvi(
        entrada,
        dados=[[0.1, 0.2], [0.3, 0.4]],
        mascara=[[255, 255], [255, 255]],
        origem_x=300000,
        id_cena="cena_1",
    )

    with pytest.raises(ValueError, match="diferente das entradas"):
        montar_mosaico_ndvi([entrada], entrada)

    with rasterio.open(entrada) as arquivo:
        assert arquivo.tags()["id_cena"] == "cena_1"


def test_rejeita_arquivo_sem_identificacao_de_ndvi(tmp_path):
    entrada = tmp_path / "sem_tags.tif"
    saida = tmp_path / "mosaico.tif"

    with rasterio.open(
        entrada,
        "w",
        driver="GTiff",
        width=2,
        height=2,
        count=1,
        dtype="float32",
        crs="EPSG:32722",
        transform=from_origin(300000, 7000000, 10, 10),
    ) as destino:
        destino.write(np.ones((2, 2), dtype="float32"), 1)

    with pytest.raises(ValueError, match="produto NDVI"):
        montar_mosaico_ndvi([entrada], saida)

    assert not saida.exists()