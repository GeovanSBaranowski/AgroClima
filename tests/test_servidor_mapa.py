import threading
from http.server import ThreadingHTTPServer

import geopandas as gpd
import numpy as np
import pytest
import rasterio
import requests
from rasterio.transform import from_origin
from shapely.geometry import Polygon

from servidor_mapa import ServidorMapa


@pytest.fixture
def endereco_servidor(tmp_path):
    arquivo_ndvi = tmp_path / "ndvi.tif"

    with rasterio.open(
        arquivo_ndvi,
        "w",
        driver="GTiff",
        width=1,
        height=1,
        count=1,
        dtype="float32",
        crs="EPSG:4326",
        transform=from_origin(-53, -27, 1, 1),
    ) as raster:
        raster.write(np.array([[0.75]], dtype="float32"), 1)

    solos = gpd.GeoDataFrame(
        {
            "leg_ordem": ["LATOSSOLO"],
            "legenda": ["Solo de teste"],
        },
        geometry=[
            Polygon([
                (-53, -28),
                (-52, -28),
                (-52, -27),
                (-53, -27),
                (-53, -28),
            ])
        ],
        crs="EPSG:4326",
    )

    class ServidorTeste(ServidorMapa):
        pass

    ServidorTeste.arquivo_ndvi = arquivo_ndvi
    ServidorTeste.arquivo_elevacao = None
    ServidorTeste.arquivo_inclinacao = None
    ServidorTeste.dados_solo = solos
    ServidorTeste.data_ndvi = "2024-02-01"

    servidor = ThreadingHTTPServer(("127.0.0.1", 0), ServidorTeste)
    thread = threading.Thread(target=servidor.serve_forever, daemon=True)
    thread.start()

    try:
        porta = servidor.server_address[1]
        yield f"http://127.0.0.1:{porta}"
    finally:
        servidor.shutdown()
        thread.join()
        servidor.server_close()


def test_consulta_ponto_com_ndvi_e_solo(endereco_servidor):
    resposta = requests.get(
        f"{endereco_servidor}/api/ponto",
        params={"latitude": -27.5, "longitude": -52.5},
        timeout=5,
    )

    assert resposta.status_code == 200
    dados = resposta.json()

    assert dados["latitude"] == -27.5
    assert dados["longitude"] == -52.5
    assert dados["ndvi"] == pytest.approx(0.75)
    assert dados["data_ndvi"] == "2024-02-01"
    assert dados["elevacao"] is None
    assert dados["inclinacao"] is None
    assert dados["solo"] == [
        {"categoria": "LATOSSOLO", "legenda": "Solo de teste"}
    ]


def test_ponto_fora_da_cobertura(endereco_servidor):
    resposta = requests.get(
        f"{endereco_servidor}/api/ponto",
        params={"latitude": -29, "longitude": -52.5},
        timeout=5,
    )

    assert resposta.status_code == 200
    assert resposta.json()["ndvi"] is None
    assert resposta.json()["solo"] == []


@pytest.mark.parametrize(
    "parametros",
    [
        {"latitude": "abc", "longitude": -52.5},
        {"latitude": 91, "longitude": -52.5},
        {"latitude": "nan", "longitude": -52.5},
        {"latitude": -27.5},
    ],
)
def test_rejeita_coordenadas_invalidas(endereco_servidor, parametros):
    resposta = requests.get(
        f"{endereco_servidor}/api/ponto",
        params=parametros,
        timeout=5,
    )

    assert resposta.status_code == 400
    assert "erro" in resposta.json()