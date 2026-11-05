import argparse
from datetime import date, datetime, timezone
from pathlib import Path

import requests

from configuracao import LATITUDE_REFERENCIA, LONGITUDE_REFERENCIA


def ler_argumentos(lista_argumentos=None):
    parser = argparse.ArgumentParser(
        description="Coleta temperatura diaria da NASA POWER"
    )

    parser.add_argument(
        "--inicio",
        type=date.fromisoformat,
        required=True,
        help="Data incial, por exemplo: 2024-02-01",
    )

    parser.add_argument(
        "--fim",
        type=date.fromisoformat,
        required=True,
        help="Data final, por exemplo 2024-02-07"
    )

    argumentos = parser.parse_args(lista_argumentos)

    if argumentos.inicio > argumentos.fim:
        parser.error("A data inicial deve ser anterior ou igual a final")

    return argumentos

##----------------------------------------------------------------------------------------------------------------
## Bloco de execucao

if __name__ == "__main__":
    argumentos = ler_argumentos()

    url = "https://power.larc.nasa.gov/api/temporal/daily/point"

    parametros = {
        "parameters": "T2M,RH2M,PRECTOTCORR",
        "community": "AG",
        "latitude": LATITUDE_REFERENCIA,
        "longitude": LONGITUDE_REFERENCIA,
        "start": argumentos.inicio.strftime("%Y%m%d"),
        "end": argumentos.fim.strftime("%Y%m%d"),
        "format": "JSON",
        "time-standard": "UTC"
    }

    resposta = requests.get(url, params=parametros, timeout=30)
    resposta.raise_for_status()

    dados = resposta.json()

    if dados["header"]["time_standard"] != parametros["time-standard"]:
        raise ValueError("A referencia temporal difere da solicitada")

    series = dados["properties"]["parameter"]

    for codigo, valores_por_data in series.items():
        metadados = dados["parameters"][codigo]
        unidade = metadados["units"]

        print(
            f"{codigo} | "
            f"unidade: {unidade} | "
            f"dias: {len(valores_por_data)}"
        )

    ##-----------------------------------------------------------------------------------------------------------
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