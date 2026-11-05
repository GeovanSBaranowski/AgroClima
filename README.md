# AgroClima SC

Projeto de engenharia de dados para relacionar informações meteorológicas, imagens de satélite e características do terreno em Santa Catarina.

O desenvolvimento começa com um ponto de estudo em Chapecó. O processamento atual é local. O uso de serviços da AWS faz parte das próximas etapas.

## Estado atual

O projeto realiza:

- Coleta de dados meteorológicos diários pela API NASA POWER, com período informado na execução.
- Armazenamento das respostas originais em JSON.
- Normalização de datas, coordenadas, variáveis, valores e unidades.
- Carga no PostgreSQL, na tabela `silver.observacao_meteorologica_diaria`.
- Reprocessamento sem duplicar observações.
- Coleta e validação do limite municipal de Chapecó pela API do IBGE.
- Consulta das observações armazenadas no PostgreSQL por data e ponto de referência.
- Geração de um mapa com o limite municipal e as medições meteorológicas no marcador.
- Testes automatizados dos argumentos da coleta, da normalização, da validação do limite municipal e do conteúdo do popup.
- Execução dos testes no GitHub Actions a cada push ou atualização de pull request.

As variáveis coletadas são:

| Código | Variável | Unidade |
|---|---|---|
| T2M | Temperatura do ar a 2 metros | C |
| RH2M | Umidade relativa do ar a 2 metros | % |
| PRECTOTCORR | Precipitação corrigida | mm/day |

As consultas utilizam UTC e as coordenadas aproximadas de Chapecó: latitude -27.10 e longitude -52.62.

As coordenadas usadas no coletor meteorológico, na consulta ao banco e no mapa são definidas em `src/configuracao.py`.

## Tecnologias

- Python 3.12
- PostgreSQL 16 em Docker
- Requests
- Psycopg
- python-dotenv
- Folium
- pytest
- Git
- GitHub Actions

## Preparação

Com o PostgreSQL disponível, execute na raiz do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Preencha o `.env` com os dados de conexão. Na configuração local, o PostgreSQL é acessado por `127.0.0.1:5432`.

O `.env` contém a configuração privada e fica fora do versionamento. O `.env.example` documenta as variáveis necessárias, sem a senha.

Para uma instalação nova, prepare o banco pelo pgAdmin:

1. Execute `sql/001_criar_banco.sql` conectado ao banco `postgres`.
2. Abra uma conexão com o banco `agroclima_sc`.
3. Execute `CREATE SCHEMA IF NOT EXISTS silver;`.
4. Execute `sql/003_criar_observacoes_meteorologicas.sql`.

## Execução

Execute os comandos na raiz do projeto.

Verifique a conexão:

```powershell
.\.venv\Scripts\python.exe .\src\verificar_conexao.py
```

Colete os dados para o período desejado:

```powershell
.\.venv\Scripts\python.exe .\src\coletar_clima.py --inicio 2024-02-01 --fim 2024-02-07
```

Os argumentos `--inicio` e `--fim` são obrigatórios, no formato `AAAA-MM-DD`. A data inicial deve ser anterior ou igual à final.

Para inspecionar os registros normalizados sem gravar no banco:

```powershell
.\.venv\Scripts\python.exe .\src\normalizar_clima.py
```

Para normalizar e carregar todos os arquivos JSON disponíveis:

```powershell
.\.venv\Scripts\python.exe .\src\carregar_clima.py
```

Os arquivos originais ficam em `data/raw/nasa_power`, fora do versionamento. Os registros são armazenados em `silver.observacao_meteorologica_diaria`.

Para consultar as observações de uma data no terminal:

```powershell
.\.venv\Scripts\python.exe .\src\consultar_clima.py --data 2024-02-01
```

A consulta utiliza o ponto de referência de Chapecó, a fonte NASA POWER e a referência temporal UTC. O PostgreSQL deve estar disponível e as observações precisam ter sido carregadas previamente.

## Limite municipal e mapa

Colete o limite de Chapecó, identificado pelo código IBGE `4204202`:

```powershell
.\.venv\Scripts\python.exe .\src\coletar_limite.py
```

A coleta solicita uma malha simplificada e preserva a resposta original em um arquivo GeoJSON em `data/raw/ibge_malhas`. A validação confere o município, o formato básico da resposta, o tipo de geometria e a presença de coordenadas.

Gere o mapa para uma data:

```powershell
.\.venv\Scripts\python.exe .\src\gerar_mapa.py --data 2024-02-01
```

O argumento `--data` é obrigatório e usa o formato `AAAA-MM-DD`. O script utiliza o GeoJSON de Chapecó mais recente, de acordo com o instante registrado no nome do arquivo, e consulta as medições no PostgreSQL. O resultado fica em `data/maps/chapeco.html`.

Ao clicar no marcador, o mapa exibe a data, a fonte, a referência temporal e as medições disponíveis. Uma medição nula aparece como "Sem medição". Se não houver registros para a data, o popup informa a ausência de observações. O valor zero é preservado.

O HTML guarda os dados consultados no momento da geração. Para exibir outra data ou refletir alterações no banco, execute novamente o gerador e atualize a página no navegador.

Para visualizar o mapa, inicie o servidor local na raiz do projeto:

```powershell
.\.venv\Scripts\python.exe -m http.server 8000 --bind 127.0.0.1 --directory .\data\maps
```

Mantenha o terminal aberto e acesse [o mapa local](http://127.0.0.1:8000/chapeco.html) no navegador. Utilize esse endereço HTTP para carregar a página. O mapa de fundo e os recursos de visualização dependem de conexão com a internet.

Para encerrar o servidor, pressione `Ctrl+C` no terminal.

O mapa mostra o limite do IBGE, um fundo do OpenStreetMap e o ponto utilizado nas consultas à NASA POWER. As coordenadas do marcador estão na ordem latitude, longitude. Os arquivos GeoJSON e HTML gerados ficam fora do versionamento.

## Tratamento dos dados

Cada registro representa uma variável meteorológica em uma data e localização. As unidades recebidas são validadas antes da carga.

Valores ausentes são convertidos para `NULL`, enquanto o valor zero é preservado. Arquivos antigos que contêm apenas temperatura também podem ser processados.

Cada observação é identificada pela combinação de data, latitude, longitude, variável, fonte e referência temporal.

A carga utiliza `ON CONFLICT DO NOTHING`. Observações já existentes são mantidas, mesmo que um arquivo posterior apresente outro valor para a mesma observação.

O nome do arquivo de origem e o instante da carga são registrados no banco.

## Testes

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

Os testes verificam os argumentos do período de coleta, a normalização das três variáveis, o tratamento de valores ausentes, a preservação do zero e a rejeição de unidades inesperadas. Também verificam a aceitação de limites em Polygon e MultiPolygon e a rejeição de respostas com município diferente, coleção vazia, tipo de documento inesperado, geometria de ponto ou coordenadas vazias.

Os testes do popup conferem a data, a fonte, as medições e as unidades exibidas, a diferença entre zero e valor ausente, a mensagem para datas sem observações e o tratamento de caracteres especiais como texto.

Os testes usam dados de exemplo e não dependem de consultas às APIs ou de uma conexão com o banco. O GitHub Actions executa a suíte em Linux com Python 3.12.

## Organização

- `src`: coleta, normalização, carga, consulta e geração do mapa.
- `sql`: scripts de criação do banco e das tabelas.
- `tests`: testes automatizados.
- `docs`: documentação complementar.
- `data`: arquivos locais, fora do versionamento.

## Limitações e próximos passos

Os dados meteorológicos têm resolução regional e não representam uma medição realizada diretamente em uma propriedade rural. A umidade relativa do ar não representa a umidade do solo.

O limite municipal é simplificado e serve para a visualização inicial. A validação atual não verifica a validade geométrica completa do polígono. As medições exibidas correspondem ao ponto de consulta e não descrevem a variação meteorológica dentro do município.

As próximas etapas incluem incorporar imagens de satélite e dados do terreno e preparar a execução na AWS.

## Fontes dos dados

- [NASA POWER — documentação da API diária](https://power.larc.nasa.gov/docs/services/api/temporal/daily/)
- [IBGE — documentação da API de malhas](https://servicodados.ibge.gov.br/api/docs/malhas?versao=4)
- [OpenStreetMap — dados e atribuição](https://www.openstreetmap.org/copyright)
