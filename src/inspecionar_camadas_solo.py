import pyogrio


def listar_camadas():
    url = (
        "https://geoftp.ibge.gov.br/informacoes_ambientais/"
        "pedologia/vetores/escala_250_mil/versao_2026/pedo_area.zip"
    )

    caminho = f"/vsizip//vsicurl/{url}"

    camadas = pyogrio.list_layers(caminho)

    print(f"Quantidade de camadas: {len(camadas)}")

    for nome, tipo_geometria in camadas:
        print(f"Camada: {nome} | Geometria: {tipo_geometria}")


if __name__ == "__main__":
    listar_camadas()