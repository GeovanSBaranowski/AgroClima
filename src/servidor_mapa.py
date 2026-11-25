import argparse
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from math import isfinite
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import geopandas as gpd
import rasterio

from consultar_raster_ponto import consultar_raster_ponto
from consultar_solo import consultar_solo_ponto, formatar_valor

PASTA_MAPAS = Path(__file__).resolve().parent.parent / "data" / "maps"


class ServidorMapa(SimpleHTTPRequestHandler):
    arquivo_ndvi = None
    arquivo_elevacao = None
    arquivo_inclinacao = None
    dados_solo = None
    data_ndvi = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PASTA_MAPAS), **kwargs)

    def do_GET(self):
        requisicao = urlparse(self.path)

        if requisicao.path != "/api/ponto":
            return super().do_GET()

        parametros = parse_qs(requisicao.query)

        try:
            latitude = float(parametros["latitude"][0])
            longitude = float(parametros["longitude"][0])

            if not (
                isfinite(latitude)
                and isfinite(longitude)
                and -90 <= latitude <= 90
                and -180 <= longitude <= 180
            ):
                raise ValueError("Coordenadas fora do intervalo válido")

        except (KeyError, ValueError, IndexError):
            return self.enviar_json(
                {"erro": "Informe latitude e longitude válidas."},
                status=400,
            )

        valor_ndvi = consultar_raster_ponto(
            self.arquivo_ndvi,
            latitude=latitude,
            longitude=longitude,
        )

        valor_elevacao = None
        valor_inclinacao = None

        if self.arquivo_elevacao is not None:
            valor_elevacao = consultar_raster_ponto(
                self.arquivo_elevacao,
                latitude=latitude,
                longitude=longitude,
            )

        if self.arquivo_inclinacao is not None:
            valor_inclinacao = consultar_raster_ponto(
                self.arquivo_inclinacao,
                latitude=latitude,
                longitude=longitude,
            )

        unidades_solo = None

        if self.dados_solo is not None:
            encontrados = consultar_solo_ponto(
                self.dados_solo,
                latitude=latitude,
                longitude=longitude,
            )

            unidades_solo = []

            for _, unidade in encontrados.iterrows():
                unidades_solo.append({
                    "categoria": formatar_valor(unidade.get("leg_ordem")),
                    "legenda": formatar_valor(unidade.get("legenda")),
                })

        self.enviar_json({
            "latitude": latitude,
            "longitude": longitude,
            "ndvi": valor_ndvi,
            "data_ndvi": self.data_ndvi,
            "elevacao": valor_elevacao,
            "inclinacao": valor_inclinacao,
            "solo": unidades_solo,
        })

    def enviar_json(self, dados, status=200):
        conteudo = json.dumps(dados, ensure_ascii=False).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(conteudo)))
        self.end_headers()
        self.wfile.write(conteudo)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Disponibiliza o mapa e consulta pontos"
    )

    parser.add_argument(
        "--ndvi",
        type=Path,
        required=True,
        help="Arquivo raster de NDVI usado nas consultas",
    )

    parser.add_argument(
        "--elevacao",
        type=Path,
        help="Arquivo raster de elevação",
    )

    parser.add_argument(
        "--inclinacao",
        type=Path,
        help="Arquivo raster de inclinação em graus",
    )

    parser.add_argument(
        "--solo",
        type=Path,
        help="Arquivo vetorial das unidades de solo",
    )

    argumentos = parser.parse_args()

    if not argumentos.ndvi.is_file():
        parser.error(f"Arquivo de NDVI não encontrado: {argumentos.ndvi}")

    ServidorMapa.arquivo_ndvi = argumentos.ndvi.resolve()

    with rasterio.open(ServidorMapa.arquivo_ndvi) as raster:
        ServidorMapa.data_ndvi = raster.tags().get("data_observacao_utc")

    for nome in ("elevacao", "inclinacao"):
        arquivo = getattr(argumentos, nome)

        if arquivo is not None:
            if not arquivo.is_file():
                parser.error(f"Arquivo de {nome} não encontrado: {arquivo}")

            setattr(ServidorMapa, f"arquivo_{nome}", arquivo.resolve())

    if argumentos.solo is not None:
        if not argumentos.solo.is_file():
            parser.error(f"Arquivo de solo não encontrado: {argumentos.solo}")

        ServidorMapa.dados_solo = gpd.read_file(argumentos.solo)

    endereco = ("127.0.0.1", 8001)

    print("Servidor disponível em http://127.0.0.1:8001/chapeco.html")
    ThreadingHTTPServer(endereco, ServidorMapa).serve_forever()