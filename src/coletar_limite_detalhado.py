from pathlib import Path

import requests

from coletar_limite import validar_limite

if __name__ == "__main__":
    codigo_municipio = "4204202"

    url = (
        "https://servicodados.ibge.gov.br/api/v4/malhas/municipios/"
        f"{codigo_municipio}"
    )

    parametros = {
        "formato": "application/vnd.geo+json",
        "qualidade": "maxima",
    }

    resposta = requests.get(
        url,
        params=parametros,
        timeout=60,
    )
    resposta.raise_for_status()

    dados = resposta.json()
    validar_limite(dados, codigo_municipio)

    raiz_projeto = Path(__file__).resolve().parent.parent

    arquivo_saida = (
        raiz_projeto
        / "data"
        / "raw"
        / "ibge_malhas"
        / "chapeco_4204202_maxima_teste.geojson"
    )

    arquivo_saida.parent.mkdir(parents=True, exist_ok=True)

    if arquivo_saida.exists():
        raise FileExistsError(
            f"O arquivo ja existe: {arquivo_saida}"
        )

    arquivo_saida.write_bytes(resposta.content)

    print(f"Status HTTP: {resposta.status_code}")
    print(f"Tipo de geometria: {dados['features'][0]['geometry']['type']}")
    print(f"Limite salvo em: {arquivo_saida}")