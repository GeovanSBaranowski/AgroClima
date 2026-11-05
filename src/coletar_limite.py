from datetime import datetime, timezone
from pathlib import Path

import requests


def validar_limite(dados, codigo_municipio):
    if dados["type"] != "FeatureCollection":
        raise ValueError("A resposta precisa ser uma FeatureCollection")

    feicoes = dados["features"]

    if len(feicoes) != 1:
        raise ValueError("Era esperado exatamente um municipio")

    feicao = feicoes[0]

    if feicao["properties"]["codarea"] != codigo_municipio:
        raise ValueError("O municipio recebido difere do solicitado")

    geometria = feicao["geometry"]

    if geometria["type"] not in ("Polygon", "MultiPolygon"):
        raise ValueError("A geometria precisa representar uma area")

    if not geometria["coordinates"]:
        raise ValueError("A geometria esta sem coordenadas")

if __name__ == "__main__":
    
    codigo_municipio = "4204202"

    url = (
        "https://servicodados.ibge.gov.br/api/v4/malhas/municipios/"
        f"{codigo_municipio}"
    )

    parametros = {
        "formato": "application/vnd.geo+json",
        "qualidade": "minima",
    }

    resposta = requests.get(
        url,
        params=parametros,
        timeout=30
    )

    resposta.raise_for_status()

    dados = resposta.json()

    validar_limite(dados, codigo_municipio)

    print("Status HTTP:", resposta.status_code)
    print("Tipo do documento:", dados["type"])
    print("Chaves principais:", list(dados.keys()))

    feicoes = dados["features"]

    print("Quantidade de feicoes:", len(feicoes))

    for feicao in feicoes:
        propriedades = feicao["properties"]
        geometria = feicao["geometry"]

        print("Tipo do elemento:", feicao["type"])
        print("Propriedades:", propriedades)
        print("Tipo da geometria:", geometria["type"])

    raiz_projeto = Path(__file__).resolve().parent.parent

    pasta_raw = raiz_projeto / "data" / "raw" / "ibge_malhas"
    pasta_raw.mkdir(parents=True, exist_ok=True)

    instante_coleta = datetime.now(timezone.utc).strftime(  # noqa: UP017
        "%Y%m%dT%H%M%S%fZ"
    )

    nome_arquivo = (
        f"chapeco_{codigo_municipio}_"
        f"{parametros['qualidade']}_{instante_coleta}.geojson"
    )

    arquivo = pasta_raw / nome_arquivo
    arquivo.write_bytes(resposta.content)

    print(f"Resposta salva em: {arquivo}")