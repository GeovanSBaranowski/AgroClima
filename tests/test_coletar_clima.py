import pytest

from coletar_clima import ler_argumentos


@pytest.mark.parametrize(
    "inicio,fim",
    [
        ("2024-02-01", "2024-02-07"),
        ("2024-02-01", "2024-02-01"),
    ],
)
def test_aceita_periodo_valido(inicio, fim):
    argumentos = ler_argumentos(
        ["--inicio", inicio, "--fim", fim]
    )

    assert argumentos.inicio.isoformat() == inicio
    assert argumentos.fim.isoformat() == fim


@pytest.mark.parametrize(
    "argumentos",
    [
        [
            "--inicio", "2024-02-07",
            "--fim", "2024-02-01",
        ],
        [
            "--inicio", "2024-02-30",
            "--fim", "2024-03-01",
        ],
    ],
)
def test_rejeita_periodo_invalido(argumentos):
    with pytest.raises(SystemExit) as erro:
        ler_argumentos(argumentos)

    assert erro.value.code == 2