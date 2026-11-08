import argparse
import json
from contextlib import ExitStack
from pathlib import Path

import numpy as np
import rasterio
from rasterio.merge import merge

from inspecionar_raster import inspecionar_raster


def montar_mosaico(arquivos, arquivo_saida):
    if not arquivos:
        raise ValueError("Informe pelo menos um arquivo")

    arquivos = [
        Path(arquivo).resolve()
        for arquivo in arquivos
    ]
    arquivo_saida = Path(arquivo_saida).resolve()

    if arquivo_saida in arquivos:
        raise ValueError(
            "A saida precisa ser diferente dos arquivos de entrada"
        )

    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True), ExitStack() as recursos:
        fontes = []

        for arquivo in arquivos:
            fonte = recursos.enter_context(
                rasterio.open(arquivo)
            )
            fontes.append(fonte)

        referencia = fontes[0]

        for fonte in fontes:
            if fonte.crs is None or fonte.crs != referencia.crs:
                raise ValueError(
                    "As imagens precisam ter o mesmo sistema de coordenadas"
                )

            if fonte.res != referencia.res:
                raise ValueError(
                    "As imagens precisam ter a mesma resolucao"
                )

            if fonte.count not in (1, 3):
                raise ValueError(
                    "Esta etapa espera uma ou tres bandas"
                )

            if fonte.count != referencia.count:
                raise ValueError(
                    "As imagens precisam ter a mesma quantidade de bandas"
                )

            if any(tipo != "uint8" for tipo in fonte.dtypes):
                raise ValueError(
                    "Todas as bandas precisam ser do tipo uint8"
                )

        mosaico, transformacao = merge(
            fontes,
            method="first",
            dtype="uint16",
            nodata=65535,
            masked=True,
        )

        mascaras_bandas = np.ma.getmaskarray(mosaico)
        pixels_invalidos = mascaras_bandas.any(axis=0)
        pixels_validos = ~pixels_invalidos

        if not pixels_validos.any():
            raise ValueError("O mosaico nao possui pixels validos")

        perfil = referencia.profile.copy()

        perfil.update(
            driver="GTiff",
            height=mosaico.shape[1],
            width=mosaico.shape[2],
            transform=transformacao,
            dtype="uint8",
            nodata=None,
            compress="deflate",
        )

        arquivo_saida.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with rasterio.open(
            arquivo_saida,
            "w",
            **perfil,
        ) as destino:
            destino.write(
                mosaico.filled(0).astype("uint8")
            )
            destino.write_mask(pixels_validos)

            destino.update_tags(
                arquivos_origem=json.dumps(
                    [str(arquivo) for arquivo in arquivos],
                    ensure_ascii=False,
                ),
                criterio_sobreposicao="primeiro_pixel_valido",
            )


if __name__ == "__main__":
    raiz_projeto = Path(__file__).resolve().parent.parent

    parser = argparse.ArgumentParser(
        description="Monta um mosaico dos recortes de satelite"
    )

    parser.add_argument(
        "--arquivos",
        type=Path,
        nargs="+",
        required=True,
        help="Recortes na ordem de prioridade",
    )

    parser.add_argument(
        "--saida",
        type=Path,
        required=True,
        help="Caminho do GeoTIFF que sera gerado",
    )

    argumentos = parser.parse_args()

    arquivos = [
        raiz_projeto / caminho
        for caminho in argumentos.arquivos
    ]

    arquivo_saida = raiz_projeto / argumentos.saida

    montar_mosaico(
        arquivos,
        arquivo_saida,
    )

    print(f"Mosaico salvo em: {arquivo_saida}")

    metadados = inspecionar_raster(arquivo_saida)

    for campo, valor in metadados.items():
        print(f"{campo}: {valor}")