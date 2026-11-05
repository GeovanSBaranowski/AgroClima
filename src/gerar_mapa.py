import argparse
import json
import os
from datetime import date
from html import escape
from pathlib import Path

import folium
import psycopg
from dotenv import load_dotenv

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

    limite = folium.GeoJson(
        data=dados,
        name="Limite municipal de Chapeco",
        tooltip="Chapeco - IBGE",
    ).add_to(mapa)

    folium.Marker(
        location=ponto_referencia,
        tooltip="Consultar observações meteorológicas",
        popup=folium.Popup(
            conteudo_popup,
            max_width=350,
        ),
    ).add_to(mapa)

    mapa.fit_bounds(limite.get_bounds())

    pasta_mapas = raiz_projeto / "data" / "maps"
    pasta_mapas.mkdir(parents=True, exist_ok=True)

    arquivo_mapa = pasta_mapas / "chapeco.html"
    mapa.save(str(arquivo_mapa))

    print(f"Limite utilizado: {arquivo_raw}")
    print(f"Mapa salvo em: {arquivo_mapa}")