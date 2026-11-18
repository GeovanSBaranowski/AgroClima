import argparse
import json
from contextlib import ExitStack
from datetime import date
from pathlib import Path

import numpy as np
import rasterio
from rasterio.merge import merge


def montar_mosaico_ndvi(arquivos, arquivo_saida):
    if not arquivos:
        raise ValueError("Informe pelo menos um arquivo de NDVI")

    arquivos = [Path(arquivo).resolve() for arquivo in arquivos]
    arquivo_saida = Path(arquivo_saida).resolve()

    if arquivo_saida in arquivos:
        raise ValueError("A saida precisa ser diferente das entradas")

    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True), ExitStack() as recursos:
        fontes = [
            recursos.enter_context(rasterio.open(arquivo))
            for arquivo in arquivos
        ]

        referencia = fontes[0]
        cenas = []
        datas = []

        for fonte in fontes:
            if fonte.count != 1 or fonte.dtypes != ("float32",):
                raise ValueError("Cada entrada precisa ter uma banda float32")

            if fonte.crs is None or fonte.crs != referencia.crs:
                raise ValueError(
                    "As entradas precisam ter o mesmo sistema de coordenadas"
                )

            if fonte.res != referencia.res:
                raise ValueError("As entradas precisam ter a mesma resolucao")

            tags = fonte.tags()

            if tags.get("produto") != "NDVI":
                raise ValueError("A entrada precisa ser um produto NDVI")

            if tags.get("qualidade") != "SCL aplicada":
                raise ValueError("A entrada precisa ter qualidade SCL aplicada")

            id_cena = tags.get("id_cena")

            if not id_cena:
                raise ValueError("A entrada precisa identificar sua cena")

            cenas.append(id_cena)

            data_texto = tags.get("data_observacao_utc")

            if not data_texto:
                raise ValueError(
                    "A cena precisa informar a data de observacao UTC"
                )

            try:
                data_cena = date.fromisoformat(data_texto)
            except ValueError as erro:
                raise ValueError(
                    f"Data de observacao invalida: {data_texto}"
                ) from erro

            if data_cena.isoformat() != data_texto:
                raise ValueError(
                    "A data de observacao precisa estar em AAAA-MM-DD"
                )

            datas.append(data_cena)

        if len(set(datas)) != 1:
            raise ValueError(
                "As cenas do mosaico precisam ter a mesma data UTC"
            )
        
        mosaico, transformacao = merge(
            fontes,
            method="first",
            dtype="float32",
            nodata=np.nan,
            masked=True,
        )

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
                produto="NDVI",
                qualidade="SCL aplicada por cena",
                cenas_origem=json.dumps(cenas, ensure_ascii=False),
                arquivos_origem=json.dumps(
                    [str(arquivo) for arquivo in arquivos],
                    ensure_ascii=False,
                ),
                criterio_sobreposicao="primeiro_pixel_valido",
                data_observacao_utc=datas[0].isoformat(),
            )

    print(f"Mosaico NDVI salvo em: {arquivo_saida}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Monta um mosaico de cenas NDVI"
    )

    parser.add_argument(
        "--arquivos",
        type=Path,
        nargs="+",
        required=True,
        help="Arquivos NDVI em ordem de prioridade",
    )

    parser.add_argument("--saida", type=Path, required=True)

    argumentos = parser.parse_args()

    montar_mosaico_ndvi(argumentos.arquivos, argumentos.saida)