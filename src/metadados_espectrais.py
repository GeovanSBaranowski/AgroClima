import argparse
import json
import math
from pathlib import Path

from inspecionar_raster import obter_asset


def obter_metadados_banda(dados, id_cena, nome_asset):
    if nome_asset not in ("red", "nir"):
        raise ValueError("A banda precisa ser red ou nir")

    asset = obter_asset(dados, id_cena, nome_asset)
    bandas = asset.get("raster:bands")

    if (
        not isinstance(bandas, list)
        or len(bandas) != 1
        or not isinstance(bandas[0], dict)
    ):
        raise ValueError("O asset precisa informar os metadados de uma banda")

    banda = bandas[0]

    for campo in ("scale", "offset", "nodata"):
        valor = banda.get(campo)

        if (
            isinstance(valor, bool)
            or not isinstance(valor, (int, float))
            or not math.isfinite(valor)
        ):
            raise ValueError(
                f"Metadado ausente ou invalido para {nome_asset}: {campo}"
            )

    if banda["scale"] <= 0:
        raise ValueError("A escala precisa ser positiva")

    if banda.get("data_type") != "uint16":
        raise ValueError("Esta etapa espera uma banda uint16")

    return {
        "id_cena": id_cena,
        "asset": nome_asset,
        "escala": banda["scale"],
        "deslocamento": banda["offset"],
        "nodata": banda["nodata"],
        "tipo_dados": banda["data_type"],
        "url": asset["href"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Inspeciona metadados das bandas espectrais"
    )

    parser.add_argument("--pagina", type=Path, required=True)
    parser.add_argument("--id-cena", required=True)
    parser.add_argument(
        "--asset",
        choices=["red", "nir"],
        required=True,
    )

    argumentos = parser.parse_args()

    raiz_projeto = Path(__file__).resolve().parent.parent
    arquivo_pagina = (raiz_projeto / argumentos.pagina).resolve()

    dados = json.loads(
        arquivo_pagina.read_text(encoding="utf-8")
    )

    metadados = obter_metadados_banda(
        dados,
        argumentos.id_cena,
        argumentos.asset,
    )

    for campo, valor in metadados.items():
        print(f"{campo}: {valor}")