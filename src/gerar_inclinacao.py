import argparse
from pathlib import Path

import numpy as np
import rasterio

from inclinacao import calcular_inclinacao


def gerar_inclinacao(arquivo_elevacao, arquivo_saida):
    arquivo_elevacao = Path(arquivo_elevacao).resolve()
    arquivo_saida = Path(arquivo_saida).resolve()

    if arquivo_saida == arquivo_elevacao:
        raise ValueError("A saida precisa ser diferente da entrada")

    if arquivo_saida.exists():
        raise FileExistsError(f"O arquivo de saida ja existe: {arquivo_saida}")

    with rasterio.open(arquivo_elevacao) as origem:
        if origem.crs is None or origem.crs.to_epsg() != 32722:
            raise ValueError("A elevacao precisa estar em EPSG:32722")

        if origem.count != 1 or origem.dtypes != ("float32",):
            raise ValueError("A elevacao precisa ter uma banda float32")

        transformacao = origem.transform

        if (
            transformacao.b != 0
            or transformacao.d != 0
            or transformacao.a <= 0
            or transformacao.e >= 0
        ):
            raise ValueError("A grade precisa estar orientada ao norte")

        elevacao = origem.read(1, masked=True)

        inclinacao = calcular_inclinacao(
            elevacao,
            resolucao_x=transformacao.a,
            resolucao_y=abs(transformacao.e),
        )

        if inclinacao.count() == 0:
            raise ValueError("Nao ha pixels validos para calcular inclinacao")

        perfil = origem.profile.copy()

    perfil.update(
        driver="GTiff",
        count=1,
        dtype="float32",
        nodata=None,
        compress="deflate",
    )

    pixels_validos = ~np.ma.getmaskarray(inclinacao)

    arquivo_saida.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):  # noqa: SIM117
        with rasterio.open(arquivo_saida, "w", **perfil) as destino:
            destino.write(inclinacao.filled(0), 1)
            destino.write_mask(pixels_validos)

            destino.update_tags(
                produto="inclinacao",
                unidade="graus",
                arquivo_elevacao=str(arquivo_elevacao),
                metodo="diferencas_centrais_vizinhos_cardinais",
            )

    valores_validos = inclinacao.compressed()

    print(f"Inclinacao salva em: {arquivo_saida}")
    print(f"Pixels validos: {valores_validos.size}")
    print(f"Inclinacao minima: {valores_validos.min():.2f} graus")
    print(f"Inclinacao maxima: {valores_validos.max():.2f} graus")
    print(f"Inclinacao media: {valores_validos.mean():.2f} graus")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Calcula a inclinacao a partir da elevacao"
    )

    parser.add_argument("--elevacao", type=Path, required=True)
    parser.add_argument("--saida", type=Path, required=True)

    argumentos = parser.parse_args()

    gerar_inclinacao(
        argumentos.elevacao,
        argumentos.saida,
    )