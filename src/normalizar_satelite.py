import argparse
import json
from pathlib import Path


def normalizar_cenas(dados):
    if dados.get("type") != "FeatureCollection":
        raise ValueError("O documento precisa ser uma FeatureCollection")

    registros = []

    for cena in dados["features"]:
        propriedades = cena["properties"]
        assets = cena["assets"]

        nuvens = propriedades.get("eo:cloud_cover")

        if nuvens is not None and not 0 <= nuvens <= 100:
            raise ValueError(
                f"Porcentagem de nuvens invalida na cena {cena['id']}"
            )

        registro = {
            "id_cena": cena["id"],
            "colecao": cena["collection"],
            "data_hora_observacao": propriedades["datetime"],
            "plataforma": propriedades.get("platform"),
            "nuvens_cena_percentual": nuvens,
            "url_visual": assets["visual"]["href"],
            "url_classificacao": assets["scl"]["href"],
        }

        registros.append(registro)

    return registros

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Normaliza os metadados das cenas de satelite"
    )

    parser.add_argument(
        "--pasta",
        type=Path,
        required=True,
        help="Pasta de uma execucao da consulta ao catalogo",
    )

    argumentos = parser.parse_args()

    if not argumentos.pasta.is_dir():
        raise FileNotFoundError(
            f"Pasta nao encontrada: {argumentos.pasta}"
        )

    arquivos = sorted(argumentos.pasta.glob("pagina_*.json"))

    if not arquivos:
        raise FileNotFoundError(
            f"Nenhuma pagina encontrada em {argumentos.pasta}"
        )

    total_registros = 0

    for arquivo in arquivos:
        dados = json.loads(
            arquivo.read_text(encoding="utf-8")
        )

        registros = normalizar_cenas(dados)
        total_registros += len(registros)

        print(f"{arquivo.name}: {len(registros)} cenas")

        for registro in registros:
            print(
                registro["id_cena"],
                registro["data_hora_observacao"],
                registro["nuvens_cena_percentual"],
            )

    print(f"Total normalizado: {total_registros} cenas.")