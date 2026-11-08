import argparse
import json
from pathlib import Path

import requests


def obter_miniatura(dados, id_cena):
    for cena in dados["features"]:
        if cena["id"] == id_cena:
            return cena["assets"]["thumbnail"]

    raise ValueError(f"Cena nao encontrada nesta pagina: {id_cena}")

if __name__ == "__main__":
    raiz_projeto = Path(__file__).resolve().parent.parent

    parser = argparse.ArgumentParser(
        description="Baixa a miniatura de uma cena de satelite"
    )

    parser.add_argument(
        "--pagina",
        type=Path,
        required=True,
        help="Arquivo JSON que contem a cena",
    )

    parser.add_argument(
        "--id-cena",
        required=True,
        help="Identificador da cena desejada",
    )

    argumentos = parser.parse_args()

    arquivo_pagina = (raiz_projeto / argumentos.pagina).resolve()

    dados = json.loads(
        arquivo_pagina.read_text(encoding="utf-8")
    )

    miniatura = obter_miniatura(dados, argumentos.id_cena)

    if miniatura["type"] != "image/jpeg":
        raise ValueError("A miniatura precisa estar no formato JPEG")

    resposta = requests.get(
        miniatura["href"],
        timeout=60,
    )
    resposta.raise_for_status()

    pasta_previa = raiz_projeto / "data" / "previews"
    pasta_previa.mkdir(parents=True, exist_ok=True)

    arquivo_previa = pasta_previa / f"{argumentos.id_cena}.jpg"
    arquivo_previa.write_bytes(resposta.content)

    print(f"Previa salva em: {arquivo_previa}")
    print(f"Tamanho recebido: {len(resposta.content)} bytes")