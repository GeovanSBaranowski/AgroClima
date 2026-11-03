# AgroClima SC

Projeto de engenharia de dados para relacionar informações meteorológicas, imagens de satélite e características do terreno em Santa Catarina.

O desenvolvimento começa com um ponto de estudo em Chapecó. A proposta é construir o processamento localmente e, depois, utilizar serviços da AWS.

## Estado atual

O projeto realiza:

- Coleta de temperatura diária pela API NASA POWER.
- Armazenamento da resposta original em JSON.
- Normalização de datas, coordenadas e temperaturas.
- Carga dos registros no PostgreSQL.
- Reprocessamento sem duplicar observações.
- Testes automatizados do tratamento de temperaturas.

O primeiro exercício utiliza dados de 1 a 7 de janeiro de 2024, em UTC, para as coordenadas aproximadas de Chapecó: latitude -27.10 e longitude -52.62.

## Tecnologias

- Python 3.12
- PostgreSQL 16 em Docker
- Requests
- Psycopg
- python-dotenv
- pytest
- Git

## Preparação

Com o PostgreSQL disponível, execute na raiz do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Preencha o `.env` com os dados de conexão. Na configuração local, o PostgreSQL é acessado por `127.0.0.1:5432`.

O `.env` contém a configuração privada. O `.env.example` documenta as variáveis necessárias, sem a senha.

Para preparar o banco pelo pgAdmin:

1. Execute `sql/001_criar_banco.sql` conectado ao banco `postgres`.
2. Abra uma conexão com o banco `agroclima_sc`.
3. Execute `sql/002_criar_tabela_temperatura.sql`.

## Execução

Verifique a conexão:

```powershell
.\.venv\Scripts\python.exe .\src\verificar_conexao.py
```

Colete os dados:

```powershell
.\.venv\Scripts\python.exe .\src\coletar_clima.py --inicio 2024-01-01 --fim 2024-01-07
*--inicio e --fim sao obrigatorios
```

Normalize e carregue os arquivos disponíveis:

```powershell
.\.venv\Scripts\python.exe .\src\carregar_clima.py
```

Os arquivos originais ficam em `data/raw/nasa_power`. Os registros normalizados são armazenados em `silver.temperatura_diaria`.

## Tratamento dos dados

As temperaturas são armazenadas em graus Celsius. Valores ausentes são convertidos para `NULL`, enquanto uma temperatura de zero é preservada.

Cada observação é identificada pela combinação de data, latitude, longitude, fonte e referência temporal.

A carga utiliza `ON CONFLICT DO NOTHING`. Observações já existentes são mantidas, mesmo que um arquivo posterior apresente outro valor para a mesma observação.

O nome do arquivo de origem e o instante da carga são registrados no banco.

## Testes

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Os testes verificam o tratamento do marcador de ausência, de valores nulos, de temperatura zero e de uma temperatura válida.

## Organização

- `src`: coleta, normalização e carga.
- `sql`: criação do banco e da tabela.
- `tests`: testes automatizados.
- `docs`: documentação complementar.
- `data`: arquivos locais, fora do versionamento.

## Limitações e próximos passos

Os dados meteorológicos têm resolução regional e não representam uma medição realizada diretamente em uma propriedade rural.

As próximas etapas incluem parametrizar as coletas, adicionar outras variáveis meteorológicas, incorporar imagens de satélite, construir o mapa e preparar a execução na AWS.

## Fonte dos dados

[NASA POWER — documentação da API diária](https://power.larc.nasa.gov/docs/services/api/temporal/daily/)