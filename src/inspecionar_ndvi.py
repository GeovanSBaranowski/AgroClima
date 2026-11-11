import argparse
import json
from pathlib import Path

import numpy as np
import rasterio

from metadados_espectrais import obter_metadados_banda
from ndvi import calcular_ndvi
from reflectancia import converter_reflectancia
from verificar_par_espectral import verificar_par_espectral


def ler_banda_convertida(arquivo, metadados):
    with rasterio.open(arquivo) as origem:
        valores = origem.read(1, masked=True)

    return converter_reflectancia(valores, metadados)


def aplicar_qualidade(resultado, arquivo_red, arquivo_mascara):
    with (
        rasterio.open(arquivo_red) as referencia,
        rasterio.open(arquivo_mascara) as mascara,
    ):
        if mascara.count != 1 or mascara.dtypes != ("uint8",):
            raise ValueError("A mascara precisa ter uma banda uint8")

        if (
            mascara.crs != referencia.crs
            or mascara.width != referencia.width
            or mascara.height != referencia.height
            or mascara.transform != referencia.transform
        ):
            raise ValueError("A mascara nao esta alinhada a banda")

        qualidade = mascara.read(1, masked=True)

    dados_qualidade = np.ma.getdata(qualidade)
    sem_dados = np.ma.getmaskarray(qualidade)

    valores_validos = dados_qualidade[~sem_dados]

    if not np.isin(valores_validos, [0, 1]).all():
        raise ValueError("A mascara precisa conter apenas 0 ou 1")

    invalidos = (
        np.ma.getmaskarray(resultado)
        | sem_dados
        | (dados_qualidade == 0)
    )

    return np.ma.array(
        np.ma.getdata(resultado),
        mask=invalidos,
    )


def salvar_ndvi(resultado, arquivo_red, arquivo_saida, id_cena):
    arquivo_red = Path(arquivo_red).resolve()
    arquivo_saida = Path(arquivo_saida).resolve()

    if arquivo_saida == arquivo_red:
        raise ValueError("O arquivo de saida precisa ser diferente da banda")

    with rasterio.open(arquivo_red) as referencia:
        perfil = referencia.profile.copy()

    perfil.update(
        driver="GTiff",
        count=1,
        dtype="float32",
        nodata=None,
        compress="deflate",
    )

    arquivo_saida.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):  # noqa: SIM117
        with rasterio.open(arquivo_saida, "w", **perfil) as destino:
            destino.write(resultado.filled(0).astype("float32"), 1)

            pixels_validos = ~np.ma.getmaskarray(resultado)
            destino.write_mask(pixels_validos)

            destino.update_tags(
                id_cena=id_cena,
                produto="NDVI",
                qualidade="SCL aplicada",
            )

    print(f"NDVI salvo em: {arquivo_saida}")


def inspecionar_ndvi(
    arquivo_red,
    arquivo_nir,
    dados_pagina,
    id_cena,
    arquivo_mascara=None,
    arquivo_saida=None,
):
    verificar_par_espectral(arquivo_red, arquivo_nir)

    with rasterio.open(arquivo_red) as origem:
        if origem.tags().get("stac_id_cena") != id_cena:
            raise ValueError("O par nao pertence a cena solicitada")

    metadados_red = obter_metadados_banda(dados_pagina, id_cena, "red")
    metadados_nir = obter_metadados_banda(dados_pagina, id_cena, "nir")

    red = ler_banda_convertida(arquivo_red, metadados_red)
    nir = ler_banda_convertida(arquivo_nir, metadados_nir)

    resultado = calcular_ndvi(red, nir)

    pixels_antes_qualidade = resultado.count()

    if arquivo_mascara is not None:
        resultado = aplicar_qualidade(
            resultado,
            arquivo_red,
            arquivo_mascara,
        )

        print(f"Pixels antes da qualidade: {pixels_antes_qualidade}")
        print(f"Pixels apos a qualidade: {resultado.count()}")
        print(
            "Pixels removidos pela qualidade: "
            f"{pixels_antes_qualidade - resultado.count()}"
        )

    pixels_validos = resultado.count()

    if pixels_validos == 0:
        raise ValueError("Nenhum pixel valido para calcular o NDVI")

        # Encontra a linha e a coluna do menor NDVI valido.
    posicao_minimo = np.unravel_index(
        resultado.argmin(),
        resultado.shape,
    )

    red_minimo = red[posicao_minimo]
    nir_minimo = nir[posicao_minimo]

    fora_intervalo = np.ma.sum(
        (resultado < -1) | (resultado > 1)
    )

    posicoes_fora = np.argwhere(
        (~np.ma.getmaskarray(resultado))
        & (
            (np.ma.getdata(resultado) < -1)
            | (np.ma.getdata(resultado) > 1)
        )
    )

    print("Detalhes dos primeiros pixels fora de [-1, 1]:")

    for linha, coluna in posicoes_fora[:10]:
        valor_red = red[linha, coluna]
        valor_nir = nir[linha, coluna]
        valor_ndvi = resultado[linha, coluna]

        print(
            f"  Linha {linha}, coluna {coluna} | "
            f"red={valor_red:.6f} | "
            f"nir={valor_nir:.6f} | "
            f"soma={valor_red + valor_nir:.6f} | "
            f"NDVI={valor_ndvi:.4f}"
        )

    print(f"Posicao do menor NDVI (linha, coluna): {posicao_minimo}")
    print(f"Vermelho nessa posicao: {red_minimo:.6f}")
    print(f"NIR nessa posicao: {nir_minimo:.6f}")
    print(f"Soma das bandas: {red_minimo + nir_minimo:.6f}")
    print(f"Pixels com NDVI fora de [-1, 1]: {fora_intervalo}")

    print(f"Pixels com NDVI: {pixels_validos}")
    print(f"NDVI minimo: {resultado.min():.4f}")
    print(f"NDVI maximo: {resultado.max():.4f}")
    print(f"NDVI medio: {resultado.mean():.4f}")

    if arquivo_mascara is None:
        print("Observacao: mascara SCL de qualidade nao aplicada.")
    else:
        print("Observacao: mascara SCL de qualidade aplicada.")

    if arquivo_saida is not None:
        if arquivo_mascara is None:
            raise ValueError(
                "Informe a mascara de qualidade para salvar o NDVI"
            )

        if Path(arquivo_saida).resolve() in {
            Path(arquivo_nir).resolve(),
            Path(arquivo_mascara).resolve(),
        }:
            raise ValueError(
                "O arquivo de saida precisa ser diferente das entradas"
            )

        salvar_ndvi(resultado, arquivo_red, arquivo_saida, id_cena)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Calcula e inspeciona o NDVI de uma cena"
    )

    parser.add_argument("--pagina", type=Path, required=True)
    parser.add_argument("--id-cena", required=True)
    parser.add_argument("--red", type=Path, required=True)
    parser.add_argument("--nir", type=Path, required=True)
    parser.add_argument("--mascara", type=Path)
    parser.add_argument("--saida", type=Path)

    argumentos = parser.parse_args()

    dados_pagina = json.loads(
        argumentos.pagina.read_text(encoding="utf-8")
    )

    inspecionar_ndvi(
        argumentos.red,
        argumentos.nir,
        dados_pagina,
        argumentos.id_cena,
        argumentos.mascara,
        argumentos.saida,
    )