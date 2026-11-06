import json
from datetime import datetime, timezone
from pathlib import Path

import requests

from coletar_limite import validar_limite


def obter_proximo_link(dados):
    for link in dados.get("links", []):
        if link.get("rel") == "next":
            return link

    return None

def coletar_paginas(url, criterios, pasta_execucao):
    corpo = criterios
    total_cenas = 0

    for numero_pagina in range(1, 101):
        resposta = requests.post(
            url,
            json=corpo,
            timeout=60,
        )
        resposta.raise_for_status()

        dados = resposta.json()

        if dados.get("type") != "FeatureCollection":
            raise ValueError(
                "O catalogo retornou um formato inesperado"
            )

        cenas = dados["features"]

        arquivo_resposta = (
            pasta_execucao / f"pagina_{numero_pagina:03d}.json"
        )
        arquivo_resposta.write_bytes(resposta.content)

        total_cenas += len(cenas)

        print(
            f"Pagina {numero_pagina:03d}: "
            f"{len(cenas)} cenas."
        )

        proximo_link = obter_proximo_link(dados)

        if proximo_link is None:
            return total_cenas

        if proximo_link.get("method", "GET") != "POST":
            raise ValueError(
                "Esta coleta espera paginacao por POST"
            )

        url = proximo_link["href"]
        corpo = proximo_link["body"]

        if proximo_link.get("merge", False):
            corpo = {**criterios, **corpo}

    raise RuntimeError(
        "Limite de 100 paginas atingido. "
        "A coleta ainda possui continuacao."
    )

if __name__ == "__main__":
    raiz_projeto = Path(__file__).resolve().parent.parent

    pasta_limites = raiz_projeto / "data" / "raw" / "ibge_malhas"

    arquivos = sorted(
        pasta_limites.glob("chapeco_4204202_minima_*.geojson")
    )

    if not arquivos:
        raise FileNotFoundError(
            f"Nenhum limite de Chapeco encontrado em {pasta_limites}"
        )

    arquivo_limite = arquivos[-1]

    dados_limite = json.loads(
        arquivo_limite.read_text(encoding="utf-8")
    )

    validar_limite(dados_limite, "4204202")

    geometria = dados_limite["features"][0]["geometry"]

    url = "https://earth-search.aws.element84.com/v1/search"

    criterios = {
        "collections": ["sentinel-2-c1-l2a"],
        "intersects": geometria,
        "datetime": (
            "2024-02-01T00:00:00Z/"
            "2024-02-07T23:59:59Z"
        ),
        "limit": 5,
    }

    instante_coleta = datetime.now(timezone.utc)  # noqa: UP017

    identificador_execucao = instante_coleta.strftime(
        "%Y%m%dT%H%M%S%fZ"
    )

    pasta_raw = raiz_projeto / "data" / "raw" / "earth_search"
    pasta_execucao = pasta_raw / identificador_execucao
    pasta_execucao.mkdir(parents=True, exist_ok=True)

    registro_consulta = {
        "coletado_em": instante_coleta.isoformat(),
        "endpoint": url,
        "metodo": "POST",
        "arquivo_limite": arquivo_limite.name,
        "criterios": criterios,
    }

    arquivo_consulta = pasta_execucao / "consulta.json"
    arquivo_consulta.write_text(
        json.dumps(
            registro_consulta,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Consulta salva em: {arquivo_consulta}")

    total_cenas = coletar_paginas(
        url,
        criterios,
        pasta_execucao,
    )

    print(f"Coleta concluida: {total_cenas} registros de cenas.")
    print(f"Paginas salvas em: {pasta_execucao}")