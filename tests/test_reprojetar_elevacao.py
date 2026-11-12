import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from reprojetar_elevacao import reprojetar_elevacao


def criar_elevacao(caminho, dtype="float32"):
    dados = np.zeros((8, 8), dtype=dtype)

    mascara = np.full((8, 8), 255, dtype="uint8")
    mascara[4:, 4:] = 0

    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):  # noqa: SIM117
        with rasterio.open(
            caminho,
            "w",
            driver="GTiff",
            width=8,
            height=8,
            count=1,
            dtype=dtype,
            crs="EPSG:4326",
            transform=from_origin(-52.7, -27.0, 0.001, 0.001),
        ) as destino:
            destino.write(dados, 1)
            destino.write_mask(mascara)


def test_reprojeta_preservando_zero_valido_e_mascara(tmp_path):
    origem = tmp_path / "origem.tif"
    saida = tmp_path / "reprojetado.tif"

    criar_elevacao(origem)

    reprojetar_elevacao(origem, saida)

    with rasterio.open(saida) as arquivo:
        dados = arquivo.read(1, masked=True)

        assert arquivo.crs.to_string() == "EPSG:32722"
        assert arquivo.dtypes == ("float32",)

        # Deve haver pixels validos e pixels indisponiveis.
        assert dados.count() > 0
        assert np.ma.getmaskarray(dados).any()

        # Todos os pixels disponiveis da origem tinham valor zero.
        np.testing.assert_allclose(dados.compressed(), 0.0)

        assert arquivo.tags()["reamostragem"] == "bilinear"


def test_rejeita_tipo_de_dado_inesperado(tmp_path):
    origem = tmp_path / "origem.tif"
    saida = tmp_path / "reprojetado.tif"

    criar_elevacao(origem, dtype="uint8")

    with pytest.raises(ValueError, match="float32"):
        reprojetar_elevacao(origem, saida)

    assert not saida.exists()


def test_nao_sobrescreve_a_origem(tmp_path):
    origem = tmp_path / "origem.tif"

    criar_elevacao(origem)

    with pytest.raises(ValueError, match="diferente da origem"):
        reprojetar_elevacao(origem, origem)

    with rasterio.open(origem) as arquivo:
        assert arquivo.crs.to_string() == "EPSG:4326"