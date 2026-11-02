import json
from datetime import datetime
from pathlib import Path


def normalizar_temperaturas(dados):

    if dados["parameters"]["T2M"]["units"] != "C":
        raise ValueError("O valor da unidade precisa ser C")
    
    registros = []

    coordenadas = dados["geometry"]["coordinates"]
    longitude = coordenadas[0]
    latitude = coordenadas[1]

    temperaturas = dados["properties"]["parameter"]["T2M"]

    valor_ausente = dados["header"]["fill_value"]

    for data, temperatura in temperaturas.items():

        temperatura_c = temperatura

        if temperatura is None or temperatura == valor_ausente:
            temperatura_c = None

        registro_formatado = {
            "data_observacao": datetime.strptime(
                data, "%Y%m%d"
            ).strftime("%Y-%m-%d"),
            "latitude": latitude,
            "longitude": longitude,
            "temperatura_c":temperatura_c,
            "fonte": "NASA_POWER",
            "referencia_temporal": dados["header"]["time_standard"]
        }

        registros.append(registro_formatado)

    return registros

if __name__ == "__main__":
    raiz_projeto = Path(__file__).resolve().parent.parent
    pasta_raw = raiz_projeto / "data" / "raw" / "nasa_power"

    arquivos = sorted(pasta_raw.glob("*.json"))

    if not arquivos:
        raise FileNotFoundError(f"Nenhum JSON encontrado na pasta {pasta_raw}")

    for arquivos_raw in arquivos:
        dados = json.loads(arquivos_raw.read_text(encoding="utf-8"))
        registros = normalizar_temperaturas(dados)

        print(f"{arquivos_raw.name}: {len(registros)} registros")

        for registro in registros:
            print(registro)
