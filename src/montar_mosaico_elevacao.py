import argparse
import json
from contextlib import ExitStack
from pathlib import Path

import numpy as np
import rasterio
from rasterio.merge import merge


def montar_mosaico_elevacao(arquivos, arquivo_saida):
    if not arquivos:
        raise ValueError("Informe ao menos um arquivo de elevacao")

    arquivos = [Path(arquivo).resolve() for arquivo in arquivos]
    arquivo_saida = Path(arquivo_saida).resolve()

    if arquivo_saida in arquivos:
        raise ValueError("A saida precisa ser diferente das entradas")

    if arquivo_saida.exists():
        raise FileExistsError(f"O arquivo de saida ja existe: {arquivo_saida}")

    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True), ExitStack() as recursos:
        fontes = [
            recursos.enter_context(rasterio.open(arquivo))
            for arquivo in arquivos
        ]

        referencia = fontes[0]
        itens_origem = []

        for fonte in fontes:
            if fonte.count != 1 or fonte.dtypes != ("float32",):
                raise ValueError("Cada arquivo precisa ter uma banda float32")

            if fonte.crs is None or fonte.crs != referencia.crs:
                raise ValueError(
                    "Os arquivos precisam ter o mesmo sistema de coordenadas"
                )

            if fonte.res != referencia.res:
                raise ValueError("Os arquivos precisam ter a mesma resolucao")

            # Comparamos as origens na unidade de pixels da grade.
            deslocamento_x = (
                fonte.transform.c - referencia.transform.c
            ) / referencia.res[0]

            deslocamento_y = (
                fonte.transform.f - referencia.transform.f
            ) / referencia.res[1]

            if not (
                np.isclose(
                    deslocamento_x,
                    round(deslocamento_x),
                    rtol=0,
                    atol=0.000001,
                )
                and np.isclose(
                    deslocamento_y,
                    round(deslocamento_y),
                    rtol=0,
                    atol=0.000001,
                )
            ):
                raise ValueError("Os arquivos nao estao na mesma grade")

            id_item = fonte.tags().get("id_item")

            if not id_item:
                raise ValueError("O arquivo precisa identificar o item de origem")

            itens_origem.append(id_item)

        mosaico, transformacao = merge(
            fontes,
            method="first",
            dtype="float32",
            nodata=np.nan,
            masked=True,
        )

        # Garante que NaN e infinitos estejam mascarados.
        mosaico = np.ma.masked_invalid(mosaico)

        pixels_validos = ~np.ma.getmaskarray(mosaico[0])

        if not pixels_validos.any():
            raise ValueError("O mosaico nao possui pixels validos")

        perfil = referencia.profile.copy()
        perfil.update(
            driver="GTiff",
            width=mosaico.shape[2],
            height=mosaico.shape[1],
            transform=transformacao,
            count=1,
            dtype="float32",
            nodata=None,
            compress="deflate",
        )

        arquivo_saida.parent.mkdir(parents=True, exist_ok=True)

        with rasterio.open(arquivo_saida, "w", **perfil) as destino:
            destino.write(mosaico.filled(0).astype("float32"))
            destino.write_mask(pixels_validos)

            destino.update_tags(
                fonte="Copernicus DEM GLO-30",
                unidade="meter",
                itens_origem=json.dumps(itens_origem, ensure_ascii=False),
                arquivos_origem=json.dumps(
                    [str(arquivo) for arquivo in arquivos],
                    ensure_ascii=False,
                ),
                criterio_sobreposicao="primeiro_pixel_valido",
            )

    print(f"Mosaico salvo em: {arquivo_saida}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Monta um mosaico dos recortes de elevacao"
    )

    parser.add_argument(
        "--arquivos",
        type=Path,
        nargs="+",
        required=True,
        help="Recortes na ordem de prioridade",
    )

    parser.add_argument("--saida", type=Path, required=True)

    argumentos = parser.parse_args()

    montar_mosaico_elevacao(
        argumentos.arquivos,
        argumentos.saida,
    )