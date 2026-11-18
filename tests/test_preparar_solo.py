import geopandas as gpd
import pytest
from shapely.geometry import Point, Polygon

from preparar_solo import preparar_solo


def criar_solos():
    poligono = Polygon([
        (-52.70, -27.10),
        (-52.69, -27.10),
        (-52.69, -27.09),
        (-52.70, -27.09),
        (-52.70, -27.10),
    ])

    return gpd.GeoDataFrame(
        {
            "leg_ordem": ["CAMBISSOLO"],
            "componente": ["Descricao de exemplo"],
        },
        geometry=[poligono],
        crs="EPSG:4674",
    )


def test_reprojeta_e_preserva_atributos():
    solos = criar_solos()

    preparados = preparar_solo(solos)

    assert preparados.crs.to_epsg() == 4326
    assert preparados.loc[0, "leg_ordem"] == "CAMBISSOLO"
    assert preparados.loc[0, "componente"] == "Descricao de exemplo"

    # A tabela recebida continua com seu sistema original.
    assert solos.crs.to_epsg() == 4674


def test_rejeita_dados_sem_sistema_de_coordenadas():
    solos = criar_solos()
    solos = solos.set_crs(None, allow_override=True)

    with pytest.raises(ValueError, match="informar suas coordenadas"):
        preparar_solo(solos)


def test_rejeita_ausencia_do_campo_de_legenda():
    solos = criar_solos().drop(columns=["leg_ordem"])

    with pytest.raises(ValueError, match="leg_ordem"):
        preparar_solo(solos)


def test_rejeita_geometria_invalida():
    # Os segmentos se cruzam no centro.
    poligono_invalido = Polygon([
        (-52.70, -27.10),
        (-52.69, -27.09),
        (-52.70, -27.09),
        (-52.69, -27.10),
        (-52.70, -27.10),
    ])

    solos = gpd.GeoDataFrame(
        {"leg_ordem": ["CAMBISSOLO"]},
        geometry=[poligono_invalido],
        crs="EPSG:4674",
    )

    with pytest.raises(ValueError, match="geometrias invalidas"):
        preparar_solo(solos)


def test_rejeita_geometria_que_nao_e_poligono():
    solos = gpd.GeoDataFrame(
        {"leg_ordem": ["CAMBISSOLO"]},
        geometry=[Point(-52.70, -27.10)],
        crs="EPSG:4674",
    )

    with pytest.raises(ValueError, match="precisam conter poligonos"):
        preparar_solo(solos)