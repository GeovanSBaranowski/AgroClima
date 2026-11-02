from datetime import datetime, timezone
from pathlib import Path

import requests

url = "https://power.larc.nasa.gov/api/temporal/daily/point"

parametros = {
    "parameters": "T2M",
    "community": "AG",
    "latitude": "-27.10",
    "longitude": "-52.62",
    "start": "20240101",
    "end": "20240107",
    "format": "JSON",
    "time-standard": "UTC"
}

resposta = requests.get(url, params=parametros, timeout=30)
resposta.raise_for_status()

dados = resposta.json()

if dados["header"]["time_standard"] != parametros["time-standard"]:
    raise ValueError("A referencia temporal difere da solicitada")

temperaturas = dados["properties"]["parameter"]["T2M"]

print(resposta.status_code)

for data, temperatura in temperaturas.items():
    print(data, temperatura)

##-------------------------------------------------
##Armazenamento do arquivo JSON

raiz_projeto = Path(__file__).resolve().parent.parent

pasta_raw = raiz_projeto / "data" / "raw" / "nasa_power"
pasta_raw.mkdir(parents=True, exist_ok=True)

instante_coleta = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")  # noqa: UP017

nome_arquivo = (
    f"chapeco_{parametros['start']}_{parametros['end']}_"
    f"{parametros['time-standard']}_{instante_coleta}.json"
)

arquivo = pasta_raw / nome_arquivo
arquivo.write_bytes(resposta.content)

print(f"Resposta salva em: {arquivo}")