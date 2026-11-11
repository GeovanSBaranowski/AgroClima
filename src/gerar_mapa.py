import argparse
import json
import os
from datetime import date, datetime, timezone
from html import escape
from pathlib import Path

import folium
import psycopg
from dotenv import load_dotenv

from camada_ndvi import adicionar_camada_ndvi
from camada_satelite import adicionar_camada_satelite
from coletar_limite import validar_limite
from configuracao import LATITUDE_REFERENCIA, LONGITUDE_REFERENCIA
from consultar_clima import consultar_observacoes


def montar_popup(registros, data_observacao):
    nomes_variaveis = {
        "T2M": "Temperatura do ar",
        "RH2M": "Umidade relativa do ar",
        "PRECTOTCORR": "Precipitação",
    }

    linhas = [
        f"<b>Observações de {data_observacao:%d/%m/%Y}</b>",
        "Fonte: NASA POWER | UTC",
    ]

    if not registros:
        linhas.append("Sem observações disponíveis para esta data.")
        return "<br>".join(linhas)

    for registro in registros:
        codigo = registro["variavel"]
        nome = nomes_variaveis.get(codigo, codigo)
        valor = registro["valor"]

        if valor is None:
            texto_valor = "Sem medição"
        else:
            texto_valor = f"{valor:.2f} {registro['unidade']}"

        linhas.append(
            f"{escape(nome)}: {escape(texto_valor)}"
        )

    return "<br>".join(linhas)

def estilizar_contorno_cena(feicao):
    return {
        "color": "#e67e22",
        "weight": 2,
        "fill": False,
    }

def adicionar_contornos_cenas(mapa, dados_catalogo, data_observacao):
    if dados_catalogo.get("type") != "FeatureCollection":
        raise ValueError("O catalogo precisa ser uma FeatureCollection")

    total = 0

    for cena in dados_catalogo["features"]:
        instante = datetime.fromisoformat(
            cena["properties"]["datetime"]
        )

        data_cena = instante.astimezone(timezone.utc).date()  # noqa: UP017

        if data_cena != data_observacao:
            continue

        identificador = escape(cena["id"])

        folium.GeoJson(
            data=cena["geometry"],
            name=f"Cena {identificador}",
            tooltip=identificador,
            style_function=estilizar_contorno_cena,
        ).add_to(mapa)

        total += 1

    return total

def estilizar_limite_municipal(feicao):
    return {
        "color": "#3388ff",
        "weight": 2,
        "fill": False,
    }
        
if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Gera o mapa com observacoes meteorologicas"
    )

    parser.add_argument(
        "--data",
        type=date.fromisoformat,
        required=True,
        help="Data das observacoes, por exemplo: 2024-02-01",
    )

    parser.add_argument(
        "--pasta-cenas",
        type=Path,
        help="Pasta da consulta ao catalogo de satelite",
    )

    parser.add_argument(
        "--raster",
        type=Path,
        help="GeoTIFF que sera exibido no mapa",
    )

    parser.add_argument(
        "--ndvi",
        type=Path,
        help="GeoTIFF de NDVI que sera exibido no mapa",
    )

    argumentos = parser.parse_args()

    raiz_projeto = Path(__file__).resolve().parent.parent

    pasta_raw = raiz_projeto / "data" / "raw" / "ibge_malhas"

    arquivos = sorted(
        pasta_raw.glob("chapeco_4204202_minima_*.geojson")
    )

    if not arquivos:
        raise FileNotFoundError(
            f"Nenhum limite de Chapeco encontrado em {pasta_raw}"
        )    

    arquivo_raw = arquivos[-1]

    dados = json.loads(
        arquivo_raw.read_text(encoding="utf-8")
    )

    validar_limite(dados, "4204202")

    ponto_referencia = [LATITUDE_REFERENCIA, LONGITUDE_REFERENCIA]

    load_dotenv(raiz_projeto / ".env")

    with psycopg.connect(
        host=os.environ["PGHOST"],
        port=int(os.environ["PGPORT"]),
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        connect_timeout=10,
    ) as conexao:
        registros = consultar_observacoes(
            conexao,
            data_observacao=argumentos.data,
            latitude=ponto_referencia[0],
            longitude=ponto_referencia[1],
        )

    conteudo_popup = montar_popup(
        registros,
        argumentos.data,
    )

    mapa = folium.Map(
        location=ponto_referencia,
        tiles="OpenStreetMap",
        control_scale=True,
    )

    if argumentos.raster is not None:
        arquivo_raster = (
            raiz_projeto / argumentos.raster
        ).resolve()

        adicionar_camada_satelite(
            mapa,
            arquivo_raster,
        )

        print(f"Imagem utilizada: {arquivo_raster}")

    if argumentos.ndvi is not None:
        arquivo_ndvi = (
            raiz_projeto / argumentos.ndvi
        ).resolve()

        adicionar_camada_ndvi(
            mapa,
            arquivo_ndvi,
        )

        print(f"NDVI utilizado: {arquivo_ndvi}")

        legenda_ndvi = """
        <div style="
            position: fixed;
            bottom: 35px;
            left: 20px;
            z-index: 9999;
            background: white;
            padding: 10px 12px;
            border: 1px solid #777;
            border-radius: 4px;
            font-size: 13px;
        ">
            <strong>NDVI Sentinel-2</strong><br>
            <span style="color: #2d6eb4;">&#9632;</span>
            -1 a menos de 0<br>
            <span style="color: #dcc8a0;">&#9632;</span>
            0 a menos de 0,2<br>
            <span style="color: #96c850;">&#9632;</span>
            0,2 a menos de 0,5<br>
            <span style="color: #1e7837;">&#9632;</span>
            0,5 a 1<br>
            <span style="color: #963caa;">&#9632;</span>
            Fora de [-1, 1]
        </div>
        """

        mapa.get_root().html.add_child(
            folium.Element(legenda_ndvi)
        )
        
    limite = folium.GeoJson(
        data=dados,
        name="Limite municipal de Chapeco",
        tooltip="Chapeco - IBGE",
        style_function=estilizar_limite_municipal,
    ).add_to(mapa)

    if argumentos.pasta_cenas is not None:
        pasta_cenas = (
            raiz_projeto / argumentos.pasta_cenas
        ).resolve()

        paginas = sorted(pasta_cenas.glob("pagina_*.json"))

        if not paginas:
            raise FileNotFoundError(
                f"Nenhuma pagina encontrada em {pasta_cenas}"
            )

        total_contornos = 0

        for pagina in paginas:
            dados_catalogo = json.loads(
                pagina.read_text(encoding="utf-8")
            )

            total_contornos += adicionar_contornos_cenas(
                mapa,
                dados_catalogo,
                argumentos.data,
            )

        print(f"Contornos de cenas adicionados: {total_contornos}")

    folium.Marker(
        location=ponto_referencia,
        tooltip="Consultar observações meteorológicas",
        popup=folium.Popup(
            conteudo_popup,
            max_width=350,
        ),
    ).add_to(mapa)

    folium.LayerControl(collapsed=False).add_to(mapa)
    mapa.fit_bounds(limite.get_bounds())

    pasta_mapas = raiz_projeto / "data" / "maps"
    pasta_mapas.mkdir(parents=True, exist_ok=True)

    arquivo_mapa = pasta_mapas / "chapeco.html"
    mapa.save(str(arquivo_mapa))

    print(f"Limite utilizado: {arquivo_raw}")
    print(f"Mapa salvo em: {arquivo_mapa}")