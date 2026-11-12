import json

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from montar_mosaico_elevacao import montar_mosaico_elevacao


def criar_recorte(caminho, dados, mascara, origem_x, id_item):
    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):  # noqa: SIM117
        with rasterio.open(
            caminho,
            "w",
            driver="GTiff",
            width=2,
            height=2,
            count=1,
            dtype="float32",
            crs="EPSG:4326",
            transform=from_origin(origem_x, -27, 0.001, 0.001),
        ) as destino:
            destino.write(np.array(dados, dtype="float32"), 1)
            destino.write_mask(np.array(mascara, dtype="uint8"))
            destino.update_tags(id_item=id_item)


def test_preserva_valores_mascara_e_prioridade(tmp_path):
    primeiro = tmp_path / "primeiro.tif"
    segundo = tmp_path / "segundo.tif"
    saida = tmp_path / "mosaico.tif"

    criar_recorte(
        primeiro,
        dados=[[0.0, 100.5], [200.25, 300.75]],
        mascara=[[255, 0], [255, 255]],
        origem_x=-53.0,
        id_item="item_1",
    )

    criar_recorte(
        segundo,
        dados=[[400.5, 500.25], [600.5, 700.25]],
        mascara=[[255, 255], [255, 0]],
        origem_x=-52.999,
        id_item="item_2",
    )

    montar_mosaico_elevacao([primeiro, segundo], saida)

    with rasterio.open(saida) as arquivo:
        resultado = arquivo.read(1, masked=True)

        assert resultado.shape == (2, 3)
        assert arquivo.dtypes == ("float32",)

        np.testing.assert_array_equal(
            np.ma.getmaskarray(resultado),
            [[False, False, False], [False, False, True]],
        )

        # Zero continua valido.
        assert resultado[0, 0] == pytest.approx(0.0)

        # O primeiro esta mascarado: usa o segundo.
        assert resultado[0, 1] == pytest.approx(400.5)

        # Os dois sao validos: usa o primeiro.
        assert resultado[1, 1] == pytest.approx(300.75)

        assert resultado[0, 2] == pytest.approx(500.25)
        assert resultado[1, 0] == pytest.approx(200.25)

        assert json.loads(arquivo.tags()["itens_origem"]) == [
            "item_1",
            "item_2",
        ]


def test_rejeita_recorte_deslocado_meio_pixel(tmp_path):
    primeiro = tmp_path / "primeiro.tif"
    segundo = tmp_path / "segundo.tif"
    saida = tmp_path / "mosaico.tif"

    criar_recorte(
        primeiro,
        dados=[[100, 100], [100, 100]],
        mascara=[[255, 255], [255, 255]],
        origem_x=-53.0,
        id_item="item_1",
    )

    criar_recorte(
        segundo,
        dados=[[200, 200], [200, 200]],
        mascara=[[255, 255], [255, 255]],
        origem_x=-52.9995,
        id_item="item_2",
    )

    with pytest.raises(ValueError, match="mesma grade"):
        montar_mosaico_elevacao([primeiro, segundo], saida)

    assert not saida.exists()


def test_nao_sobrescreve_arquivo_de_entrada(tmp_path):
    entrada = tmp_path / "recorte.tif"

    criar_recorte(
        entrada,
        dados=[[100, 100], [100, 100]],
        mascara=[[255, 255], [255, 255]],
        origem_x=-53.0,
        id_item="item_1",
    )

    with pytest.raises(ValueError, match="diferente das entradas"):
        montar_mosaico_elevacao([entrada], entrada)

    with rasterio.open(entrada) as arquivo:
        assert arquivo.tags()["id_item"] == "item_1"