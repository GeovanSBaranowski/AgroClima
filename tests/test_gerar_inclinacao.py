import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from gerar_inclinacao import gerar_inclinacao


def criar_elevacao(
    caminho,
    *,
    crs="EPSG:32722",
    mascara=None,
):
    dados = np.full((3, 3), 500.0, dtype="float32")

    if mascara is None:
        mascara = np.full((3, 3), 255, dtype="uint8")

    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):  # noqa: SIM117
        with rasterio.open(
            caminho,
            "w",
            driver="GTiff",
            width=3,
            height=3,
            count=1,
            dtype="float32",
            crs=crs,
            transform=from_origin(300000, 7000000, 10, 10),
        ) as destino:
            destino.write(dados, 1)
            destino.write_mask(mascara)


def test_salva_inclinacao_plana_com_bordas_mascaradas(tmp_path):
    entrada = tmp_path / "elevacao.tif"
    saida = tmp_path / "inclinacao.tif"

    criar_elevacao(entrada)

    gerar_inclinacao(entrada, saida)

    with rasterio.open(saida) as arquivo:
        resultado = arquivo.read(1, masked=True)

        assert arquivo.crs.to_string() == "EPSG:32722"
        assert arquivo.dtypes == ("float32",)
        assert arquivo.transform == from_origin(
            300000, 7000000, 10, 10
        )

        assert arquivo.tags()["produto"] == "inclinacao"
        assert arquivo.tags()["unidade"] == "graus"

        np.testing.assert_array_equal(
            np.ma.getmaskarray(resultado),
            [
                [True, True, True],
                [True, False, True],
                [True, True, True],
            ],
        )

        # Zero grau e um resultado valido para uma superficie plana.
        assert resultado[1, 1] == pytest.approx(0.0)


def test_rejeita_sistema_de_coordenadas_incorreto(tmp_path):
    entrada = tmp_path / "elevacao.tif"
    saida = tmp_path / "inclinacao.tif"

    criar_elevacao(entrada, crs="EPSG:4326")

    with pytest.raises(ValueError, match="EPSG:32722"):
        gerar_inclinacao(entrada, saida)

    assert not saida.exists()


def test_rejeita_arquivo_sem_pixels_calculaveis(tmp_path):
    entrada = tmp_path / "elevacao.tif"
    saida = tmp_path / "inclinacao.tif"

    criar_elevacao(
        entrada,
        mascara=np.zeros((3, 3), dtype="uint8"),
    )

    with pytest.raises(ValueError, match="Nao ha pixels validos"):
        gerar_inclinacao(entrada, saida)

    assert not saida.exists()