import requests


def inspecionar_arquivo(url):
    resposta = requests.head(
        url,
        timeout=30,
        allow_redirects=True,
    )
    resposta.raise_for_status()

    return {
        "status": resposta.status_code,
        "tipo": resposta.headers.get("Content-Type"),
        "tamanho_bytes": resposta.headers.get("Content-Length"),
        "ultima_modificacao": resposta.headers.get("Last-Modified"),
    }


def verificar_acesso_parcial(url):
    with requests.get(
        url,
        headers={"Range": "bytes=0-0"},
        stream=True,
        timeout=30,
        allow_redirects=True,
    ) as resposta:
        resposta.raise_for_status()

        return {
            "status": resposta.status_code,
            "content_range": resposta.headers.get("Content-Range"),
        }

if __name__ == "__main__":
    base_url = (
        "https://geoftp.ibge.gov.br/informacoes_ambientais/"
        "pedologia/vetores/escala_250_mil/versao_2026"
    )

    arquivos = [
        "atributos_pedo.pdf",
        "pedo_area.zip",
        "pedo_tabelas.zip",
    ]

    for nome in arquivos:
        url = f"{base_url}/{nome}"
        informacoes = inspecionar_arquivo(url)

        print(f"Arquivo: {nome}")

        for campo, valor in informacoes.items():
            print(f"  {campo}: {valor}")

        print()

        url_areas = f"{base_url}/pedo_area.zip"

    acesso_parcial = verificar_acesso_parcial(url_areas)

    print("Teste de acesso parcial ao arquivo de areas:")

    for campo, valor in acesso_parcial.items():
        print(f"  {campo}: {valor}")