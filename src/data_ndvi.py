from datetime import date

import rasterio


def comparar_data_ndvi(data_texto, data_clima):
    if data_texto is None or data_texto == "":
        return {
            "situacao": "ausente",
            "data_ndvi": None,
        }

    if not isinstance(data_texto, str):
        return {
            "situacao": "invalida",
            "data_ndvi": None,
        }

    try:
        data_ndvi = date.fromisoformat(data_texto)
    except ValueError:
        return {
            "situacao": "invalida",
            "data_ndvi": None,
        }

    if data_ndvi.isoformat() != data_texto:
        return {
            "situacao": "invalida",
            "data_ndvi": None,
        }

    if data_ndvi == data_clima:
        situacao = "coincide"
    else:
        situacao = "diferente"

    return {
        "situacao": situacao,
        "data_ndvi": data_ndvi,
    }

def avaliar_data_raster_ndvi(arquivo_raster, data_clima):
    with rasterio.open(arquivo_raster) as origem:
        data_texto = origem.tags().get("data_observacao_utc")

    return comparar_data_ndvi(data_texto, data_clima)