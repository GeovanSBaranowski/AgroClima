import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from verificar_par_espectral import verificar_par_espectral


def criar_banda(caminho, asset, cena, transform):
    dados = np.ones((2, 2), dtype="uint16")

    with rasterio.open(
        caminho,
        "w",
        driver="GTiff",
        width=2,
        height=2,
        count=1,
        dtype="uint16",
        crs="EPSG:32722",
        transform=transform,
    ) as destino:
        destino.write(dados, 1)
        destino.update_tags(
            stac_asset=asset,
            stac_id_cena=cena,
        )


def test_aceita_bandas_da_mesma_cena_e_grade(tmp_path, capsys):
    arquivo_red = tmp_path / "red.tif"
    arquivo_nir = tmp_path / "nir.tif"
    grade = from_origin(300000, 7000000, 10, 10)

    criar_banda(arquivo_red, "red", "cena_1", grade)
    criar_banda(arquivo_nir, "nir", "cena_1", grade)

    verificar_par_espectral(arquivo_red, arquivo_nir)

    saida = capsys.readouterr().out
    assert "As bandas possuem a mesma grade." in saida


def test_rejeita_bandas_de_cenas_diferentes(tmp_path):
    arquivo_red = tmp_path / "red.tif"
    arquivo_nir = tmp_path / "nir.tif"
    grade = from_origin(300000, 7000000, 10, 10)

    criar_banda(arquivo_red, "red", "cena_1", grade)
    criar_banda(arquivo_nir, "nir", "cena_2", grade)

    with pytest.raises(ValueError, match="mesma cena"):
        verificar_par_espectral(arquivo_red, arquivo_nir)


def test_rejeita_bandas_com_posicionamento_diferente(tmp_path):
    arquivo_red = tmp_path / "red.tif"
    arquivo_nir = tmp_path / "nir.tif"

    grade_red = from_origin(300000, 7000000, 10, 10)
    grade_nir = from_origin(300010, 7000000, 10, 10)

    criar_banda(arquivo_red, "red", "cena_1", grade_red)
    criar_banda(arquivo_nir, "nir", "cena_1", grade_nir)

    with pytest.raises(ValueError, match="mesmo posicionamento"):
        verificar_par_espectral(arquivo_red, arquivo_nir)