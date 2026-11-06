import json
from unittest.mock import Mock, patch

from consultar_satelite import coletar_paginas


def criar_resposta(dados):
    resposta = Mock()
    resposta.json.return_value = dados
    resposta.content = json.dumps(dados).encode("utf-8")
    resposta.raise_for_status.return_value = None

    return resposta


def test_coleta_salva_paginas_e_segue_continuacao(tmp_path):
    url = "https://earth-search.aws.element84.com/v1/search"

    criterios = {
        "collections": ["sentinel-2-c1-l2a"],
        "limit": 1,
    }

    corpo_proxima_pagina = {
        **criterios,
        "next": "marcador-de-teste",
    }

    primeira_pagina = {
        "type": "FeatureCollection",
        "features": [{"id": "cena-de-teste"}],
        "links": [
            {
                "rel": "next",
                "href": url,
                "method": "POST",
                "merge": False,
                "body": corpo_proxima_pagina,
            }
        ],
    }

    segunda_pagina = {
        "type": "FeatureCollection",
        "features": [],
        "links": [],
    }

    primeira_resposta = criar_resposta(primeira_pagina)
    segunda_resposta = criar_resposta(segunda_pagina)

    with patch(
        "consultar_satelite.requests.post",
        side_effect=[primeira_resposta, segunda_resposta],
    ) as requisicao:
        total = coletar_paginas(url, criterios, tmp_path)

    assert total == 1
    assert requisicao.call_count == 2

    assert requisicao.call_args_list[0].kwargs["json"] == criterios
    assert (
        requisicao.call_args_list[1].kwargs["json"]
        == corpo_proxima_pagina
    )

    assert (
        (tmp_path / "pagina_001.json").read_bytes()
        == primeira_resposta.content
    )
    assert (
        (tmp_path / "pagina_002.json").read_bytes()
        == segunda_resposta.content
    )