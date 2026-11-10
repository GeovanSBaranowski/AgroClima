import argparse
from pathlib import Path

import numpy as np
import rasterio


def aplicar_mascara(arquivo_imagem, arquivo_mascara, arquivo_saida):
    arquivo_imagem = Path(arquivo_imagem).resolve()
    arquivo_mascara = Path(arquivo_mascara).resolve()
    arquivo_saida = Path(arquivo_saida).resolve()

    if arquivo_saida in (arquivo_imagem, arquivo_mascara):
        raise ValueError("A saida precisa ser diferente das entradas")

    with (
        rasterio.open(arquivo_imagem) as origem,
        rasterio.open(arquivo_mascara) as qualidade,
    ):
        if origem.crs is None or qualidade.crs is None:
            raise ValueError("Os arquivos precisam informar suas coordenadas")

        if origem.dtypes != ("uint8", "uint8", "uint8"):
            raise ValueError("A imagem precisa ter tres bandas uint8")

        if qualidade.count != 1 or qualidade.dtypes != ("uint8",):
            raise ValueError("A mascara precisa ter uma banda uint8")

        if (
            origem.crs != qualidade.crs
            or origem.transform != qualidade.transform
            or origem.shape != qualidade.shape
        ):
            raise ValueError("A mascara precisa estar alinhada a imagem")

        imagem = origem.read()
        classificacao = qualidade.read(1, masked=True)

        if not np.isin(classificacao.compressed(), (0, 1)).all():
            raise ValueError("A mascara precisa conter apenas zero e um")

        com_imagem = origem.dataset_mask() > 0
        com_qualidade = ~np.ma.getmaskarray(classificacao)
        decisoes = classificacao.filled(0)

        mantidos = (
            com_imagem
            & com_qualidade
            & (decisoes == 1)
        )

        excluidos = (
            com_imagem
            & com_qualidade
            & (decisoes == 0)
        )

        sem_qualidade = com_imagem & ~com_qualidade

        perfil = origem.profile.copy()
        perfil.update(
            driver="GTiff",
            nodata=None,
            compress="deflate",
        )

        metadados = origem.tags()
        metadados.update(
            imagem_origem=str(arquivo_imagem),
            mascara_qualidade=str(arquivo_mascara),
        )

    total = int(np.count_nonzero(com_imagem))
    total_mantidos = int(np.count_nonzero(mantidos))

    if total == 0:
        raise ValueError("A imagem nao possui pixels disponiveis")

    arquivo_saida.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):  # noqa: SIM117
        with rasterio.open(arquivo_saida, "w", **perfil) as destino:
            destino.write(imagem)
            destino.write_mask(mantidos)
            destino.update_tags(**metadados)

    return {
        "pixels_com_imagem": total,
        "pixels_mantidos": total_mantidos,
        "pixels_excluidos_pela_regra": int(np.count_nonzero(excluidos)),
        "pixels_sem_qualidade": int(np.count_nonzero(sem_qualidade)),
        "percentual_mantido": total_mantidos / total * 100,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Aplica uma mascara de qualidade a imagem colorida"
    )

    parser.add_argument("--imagem", type=Path, required=True)
    parser.add_argument("--mascara", type=Path, required=True)
    parser.add_argument("--saida", type=Path, required=True)

    argumentos = parser.parse_args()

    raiz_projeto = Path(__file__).resolve().parent.parent
    arquivo_saida = raiz_projeto / argumentos.saida

    resumo = aplicar_mascara(
        raiz_projeto / argumentos.imagem,
        raiz_projeto / argumentos.mascara,
        arquivo_saida,
    )

    print(f"Imagem salva em: {arquivo_saida.resolve()}")
    print(f"Pixels com imagem: {resumo['pixels_com_imagem']}")
    print(f"Pixels mantidos: {resumo['pixels_mantidos']}")
    print(f"Excluidos pela regra: {resumo['pixels_excluidos_pela_regra']}")
    print(f"Sem dados de qualidade: {resumo['pixels_sem_qualidade']}")
    print(f"Percentual mantido: {resumo['percentual_mantido']:.4f}%")