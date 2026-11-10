import argparse
from pathlib import Path

import numpy as np
import rasterio

CLASSES_MANTIDAS = (4, 5, 6)


def criar_mascara_qualidade(classificacao):
    dados = np.ma.getdata(classificacao)

    if dados.ndim != 2:
        raise ValueError("A classificacao precisa ter linhas e colunas")

    categorias_aceitas = np.isin(dados, CLASSES_MANTIDAS)
    pixels_disponiveis = ~np.ma.getmaskarray(classificacao)

    return categorias_aceitas & pixels_disponiveis

def salvar_mascara_qualidade(arquivo_scl, arquivo_saida):
    arquivo_scl = Path(arquivo_scl).resolve()
    arquivo_saida = Path(arquivo_saida).resolve()

    if arquivo_scl == arquivo_saida:
        raise ValueError("A saida precisa ser diferente da origem")

    with rasterio.open(arquivo_scl) as origem:
        if origem.crs is None:
            raise ValueError("A classificacao precisa informar suas coordenadas")

        if origem.count != 1 or origem.dtypes != ("uint8",):
            raise ValueError("Esta etapa espera uma banda SCL uint8")

        classificacao = origem.read(1, masked=True)

        selecionados = criar_mascara_qualidade(classificacao)

        com_dados = (
            ~np.ma.getmaskarray(classificacao)
            & (classificacao.filled(0) != 0)
        )

        perfil = origem.profile.copy()

    total = int(np.count_nonzero(com_dados))
    mantidos = int(np.count_nonzero(selecionados))

    if total == 0:
        raise ValueError("A classificacao nao possui dados para avaliar")

    perfil.update(
        driver="GTiff",
        count=1,
        dtype="uint8",
        nodata=None,
        compress="deflate",
    )

    arquivo_saida.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):  # noqa: SIM117
        with rasterio.open(arquivo_saida, "w", **perfil) as destino:
            destino.write(selecionados.astype("uint8"), 1)
            destino.write_mask(com_dados)

            destino.update_tags(
                arquivo_scl_origem=str(arquivo_scl),
                classes_mantidas=",".join(
                    str(codigo) for codigo in CLASSES_MANTIDAS
                ),
                significado_valores="1=manter; 0=excluir",
            )

    return {
        "pixels_com_dados": total,
        "pixels_mantidos": mantidos,
        "pixels_excluidos": total - mantidos,
        "percentual_mantido": mantidos / total * 100,
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Gera uma mascara de qualidade a partir da SCL"
    )

    parser.add_argument(
        "--scl",
        type=Path,
        required=True,
        help="GeoTIFF da classificacao SCL",
    )

    parser.add_argument(
        "--saida",
        type=Path,
        required=True,
        help="GeoTIFF da mascara de qualidade",
    )

    argumentos = parser.parse_args()

    raiz_projeto = Path(__file__).resolve().parent.parent
    arquivo_scl = raiz_projeto / argumentos.scl
    arquivo_saida = raiz_projeto / argumentos.saida

    resumo = salvar_mascara_qualidade(
        arquivo_scl,
        arquivo_saida,
    )

    print(f"Mascara salva em: {arquivo_saida.resolve()}")
    print(f"Pixels com dados: {resumo['pixels_com_dados']}")
    print(f"Pixels mantidos: {resumo['pixels_mantidos']}")
    print(f"Pixels excluidos: {resumo['pixels_excluidos']}")
    print(f"Percentual mantido: {resumo['percentual_mantido']:.4f}%")