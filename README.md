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
- Consulta paginada de cenas Sentinel-2 pelo catálogo Earth Search, usando o limite municipal.
- Armazenamento dos critérios da consulta e das páginas originais em JSON.
- Normalização e carga dos metadados das cenas em `silver.cena_satelite`, sem duplicar cenas já carregadas.
- Download de miniaturas e inspeção de metadados dos GeoTIFFs remotos.
- Recorte das imagens pelo polígono da consulta e montagem de mosaicos com máscara de validade.
- Exibição do mosaico no mapa, com transparência fora do recorte e controle de camadas.
- Cálculo de NDVI por cena, mosaico com máscara de qualidade e visualização com legenda.
- Inspeção, recorte e mosaico da classificação SCL do Sentinel-2.
- Contagem das categorias SCL e cálculo de seus percentuais entre os pixels disponíveis.
- Avaliação da cobertura de dados SCL em relação ao polígono da consulta.
- Geração de uma máscara de qualidade a partir das categorias SCL.
- Alinhamento da máscara à grade da imagem colorida por vizinho mais próximo.
- Aplicação da máscara ao mosaico, preservando as cores e registrando os pixels excluídos na máscara interna.
- Testes automatizados da coleta, da normalização, da validação do limite, do popup, dos mosaicos, da avaliação SCL e da aplicação da máscara de qualidade.
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
- NumPy
- Rasterio
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
5. Execute `sql/004_criar_cenas_satelite.sql`.

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

O mapa mostra o limite do IBGE, um fundo do OpenStreetMap e o ponto utilizado nas consultas à NASA POWER. Também pode exibir o mosaico de satélite e os contornos das cenas. As coordenadas do marcador estão na ordem latitude, longitude. Os arquivos GeoJSON e HTML gerados ficam fora do versionamento.

## Catálogo de satélite

A consulta utiliza o Earth Search v1 e a coleção `sentinel-2-c1-l2a`. O polígono utilizado é o limite de Chapecó mais recente disponível em `data/raw/ibge_malhas`.

Execute a consulta:

```powershell
.\.venv\Scripts\python.exe .\src\consultar_satelite.py
```

O período está definido no código: de 1 a 7 de fevereiro de 2024, em UTC. Cada página solicita até cinco registros. A coleta segue os links de continuação por POST e interrompe com erro se ainda houver continuação após cem páginas.

Cada execução cria uma pasta em `data/raw/earth_search`, identificada pelo instante da coleta em UTC. O arquivo `consulta.json` registra os critérios utilizados. Os arquivos `pagina_001.json`, `pagina_002.json` e seguintes preservam as respostas recebidas, inclusive páginas vazias.

Para inspecionar os registros normalizados de uma execução:

```powershell
.\.venv\Scripts\python.exe .\src\normalizar_satelite.py --pasta .\data\raw\earth_search\20261106T001415084591Z
```

Para normalizar e carregar as cenas dessa execução no PostgreSQL:

```powershell
.\.venv\Scripts\python.exe .\src\carregar_satelite.py --pasta .\data\raw\earth_search\20261106T001415084591Z
```

Substitua o identificador da pasta pelo da consulta que deseja processar. Execute os comandos na raiz do projeto; a pasta usada na carga precisa estar dentro do projeto.

A tabela `silver.cena_satelite` armazena a coleção, o identificador da cena, o horário de observação, a plataforma, a porcentagem de nuvens da cena e os endereços da imagem em cores naturais e do arquivo de classificação SCL. Também registra o caminho relativo da página de origem e o instante da carga.

Cada cena é identificada pela combinação de coleção e identificador. A carga utiliza `ON CONFLICT DO NOTHING`, mantendo os dados e a origem da primeira inserção. Todas as páginas da execução são carregadas na mesma transação.

A porcentagem de nuvens pode ser nula; quando informada, deve estar entre zero e cem. O valor zero é preservado.

A consulta e a carga do catálogo armazenam os metadados e os endereços dos arquivos. O processamento das imagens é feito pelos scripts descritos a seguir.

## Prévia, recorte e mosaico

O exemplo utiliza as duas cenas de 1 de fevereiro de 2024 encontradas para Chapecó. Ajuste a pasta para uma execução existente da consulta ao catálogo:

```powershell
$pastaConsulta = ".\data\raw\earth_search\20261106T001415084591Z"
$paginaSatelite = Join-Path $pastaConsulta "pagina_001.json"
$idCenaSul = "S2A_T22JCQ_20240201T133141_L2A"
$idCenaNorte = "S2A_T22JCR_20240201T133141_L2A"
```

Os identificadores precisam estar presentes na página informada. Para baixar uma miniatura JPEG e inspecionar os metadados do GeoTIFF remoto:

```powershell
.\.venv\Scripts\python.exe .\src\baixar_previa_satelite.py --pagina $paginaSatelite --id-cena $idCenaSul
.\.venv\Scripts\python.exe .\src\inspecionar_raster.py --pagina $paginaSatelite --id-cena $idCenaSul
```

A miniatura fica em `data/previews`. A inspeção mostra dimensões, bandas, tipos de dados, sistema de coordenadas, resolução e limites do arquivo remoto.

Recorte as duas cenas:

```powershell
.\.venv\Scripts\python.exe .\src\recortar_cena.py --pagina $paginaSatelite --id-cena $idCenaSul
.\.venv\Scripts\python.exe .\src\recortar_cena.py --pagina $paginaSatelite --id-cena $idCenaNorte
```

O recorte utiliza o polígono de `consulta.json`, na mesma pasta da página, convertendo suas coordenadas para o sistema da imagem. Cada saída preserva a resolução e o sistema de coordenadas da origem e grava uma máscara interna de validade.

Os recortes ficam em `data/processed/sentinel2`, em uma subpasta com o identificador da consulta. Cada cena pode cobrir apenas parte do município.

Monte o mosaico:

```powershell
$pastaRecortes = Join-Path ".\data\processed\sentinel2" (Split-Path $pastaConsulta -Leaf)
$cenaSul = Join-Path $pastaRecortes "$($idCenaSul)_chapeco.tif"
$cenaNorte = Join-Path $pastaRecortes "$($idCenaNorte)_chapeco.tif"
$arquivoMosaico = Join-Path $pastaRecortes "chapeco_20240201_mosaico.tif"

.\.venv\Scripts\python.exe .\src\montar_mosaico.py --arquivos $cenaSul $cenaNorte --saida $arquivoMosaico
```

A ordem dos arquivos define a prioridade: na sobreposição, o primeiro pixel válido é mantido. A junção aceita uma ou três bandas `uint8` e exige o mesmo sistema de coordenadas, a mesma resolução e a mesma quantidade de bandas em todos os arquivos de entrada. O resultado mantém pixels pretos válidos e registra a ordem das fontes e o critério de sobreposição nas tags do GeoTIFF.

Para exibir o mosaico junto às observações meteorológicas:

```powershell
.\.venv\Scripts\python.exe .\src\gerar_mapa.py --data 2024-02-01 --raster $arquivoMosaico
```

O argumento `--raster` é opcional. A camada prepara uma prévia em Web Mercator, com canal de transparência e maior lado limitado a 1400 pixels. A imagem é incorporada ao HTML. O GeoTIFF original permanece preservado em sua resolução.

Para comparar os contornos das cenas com o limite municipal:

```powershell
.\.venv\Scripts\python.exe .\src\gerar_mapa.py --data 2024-02-01 --pasta-cenas $pastaConsulta
```

O argumento `--pasta-cenas` percorre todas as páginas e adiciona somente os contornos das cenas observadas na data escolhida, em UTC. Pode ser combinado com `--raster`.

Cada geração substitui `data/maps/chapeco.html`. Utilize o servidor HTTP descrito anteriormente para abrir o mapa. O controle de camadas permite mostrar ou esconder a imagem, o limite municipal e os contornos adicionados.

## Classificação SCL e cobertura

A SCL atribui uma categoria a cada pixel, como vegetação, água, nuvens ou sombras. No exemplo, a imagem colorida tem três bandas e resolução de 10 metros; a SCL tem uma banda e resolução de 20 metros.

Prepare os caminhos para as duas cenas da mesma data:

```powershell
$pastaConsulta = ".\data\raw\earth_search\20261106T001415084591Z"
$paginaSatelite = Join-Path $pastaConsulta "pagina_001.json"
$idCenaSul = "S2A_T22JCQ_20240201T133141_L2A"
$idCenaNorte = "S2A_T22JCR_20240201T133141_L2A"
```

Inspecione a classificação e recorte as duas cenas:

```powershell
.\.venv\Scripts\python.exe .\src\inspecionar_raster.py --pagina $paginaSatelite --id-cena $idCenaSul --asset scl
.\.venv\Scripts\python.exe .\src\recortar_cena.py --pagina $paginaSatelite --id-cena $idCenaSul --asset scl
.\.venv\Scripts\python.exe .\src\recortar_cena.py --pagina $paginaSatelite --id-cena $idCenaNorte --asset scl
```

O argumento `--asset` aceita `visual`, `scl`, `red` ou `nir`. Quando omitido, utiliza `visual`. Os recortes SCL recebem o final `_scl_chapeco.tif`, preservando os arquivos coloridos.

Monte um mosaico da classificação na mesma ordem utilizada para as imagens coloridas:

```powershell
$pastaRecortes = Join-Path ".\data\processed\sentinel2" (Split-Path $pastaConsulta -Leaf)
$sclSul = Join-Path $pastaRecortes "$($idCenaSul)_scl_chapeco.tif"
$sclNorte = Join-Path $pastaRecortes "$($idCenaNorte)_scl_chapeco.tif"
$mosaicoScl = Join-Path $pastaRecortes "chapeco_20240201_scl_mosaico.tif"

.\.venv\Scripts\python.exe .\src\montar_mosaico.py --arquivos $sclSul $sclNorte --saida $mosaicoScl
```

A sobreposição mantém o primeiro pixel válido, sem calcular médias entre códigos de classificação. Esse critério não escolhe automaticamente o pixel com menos nuvens.

Avalie as categorias e a cobertura do polígono:

```powershell
$arquivoConsulta = Join-Path $pastaConsulta "consulta.json"

.\.venv\Scripts\python.exe .\src\avaliar_qualidade_satelite.py --raster $mosaicoScl --consulta $arquivoConsulta
```

O resumo ignora posições mascaradas e o código zero, que representa ausência de dados. Exibe apenas as categorias presentes, com suas quantidades e percentuais. Os códigos 8, 9 e 10 representam categorias de nuvens; 2 e 3 representam categorias de sombras. A descrição de vegetação não identifica, por si só, uma lavoura.

Os percentuais são calculados entre os pixels disponíveis do arquivo informado. Ao avaliar um recorte de uma única cena, o resultado se refere somente à parte coberta por ela. Valores muito pequenos podem aparecer como `0.00%` devido ao arredondamento; a quantidade de pixels continua sendo exibida.

O argumento opcional `--consulta` permite comparar os pixels com dados SCL aos pixels esperados para todo o polígono salvo em `consulta.json`, na grade do raster. A leitura considera também as partes do polígono que estejam fora da extensão do arquivo. A seleção de pixels utiliza a mesma regra do recorte, com `all_touched=False`.

Cobertura de 100% significa presença de dados SCL em todos os pixels esperados para esse polígono e essa grade. Pixels classificados como nuvens ou sombras também contam como dados existentes. A cobertura não mede a porcentagem de pixels adequados a uma análise agrícola.

O mosaico SCL é utilizado na avaliação numérica. O mapa também pode exibir o mosaico de NDVI descrito a seguir.

## Máscara de qualidade

A regra inicial mantém os códigos SCL 4 (vegetação), 5 (superfície sem vegetação) e 6 (água). As demais categorias são excluídas. A seleção não identifica áreas agrícolas nem garante a ausência de erros na classificação.

Prepare os caminhos dos mosaicos da mesma data, gerados nas etapas anteriores:

```powershell
$pastaRecortes = ".\data\processed\sentinel2\20261106T001415084591Z"
$mosaicoScl = Join-Path $pastaRecortes "chapeco_20240201_scl_mosaico.tif"
$imagemColorida = Join-Path $pastaRecortes "chapeco_20240201_mosaico.tif"
$mascaraQualidade = Join-Path $pastaRecortes "chapeco_20240201_mascara_qualidade.tif"
$mascaraAlinhada = Join-Path $pastaRecortes "chapeco_20240201_mascara_qualidade_10m.tif"
$imagemFiltrada = Join-Path $pastaRecortes "chapeco_20240201_mosaico_filtrado.tif"
```

Gere a máscara na grade original da SCL:

```powershell
.\.venv\Scripts\python.exe .\src\mascara_qualidade.py --scl $mosaicoScl --saida $mascaraQualidade
```

O arquivo grava `1` para manter e `0` para excluir. Uma máscara interna separada informa onde havia dados SCL para tomar a decisão. Assim, zero disponível representa uma exclusão conhecida, enquanto uma posição indisponível representa ausência de classificação. O arquivo utiliza `nodata=None`.

A saída informa quantos pixels com dados foram mantidos ou excluídos e o percentual mantido entre eles. Esse percentual corresponde à regra de seleção, incluindo água.

Alinhe a máscara à imagem colorida:

```powershell
.\.venv\Scripts\python.exe .\src\alinhar_mascara.py --mascara $mascaraQualidade --referencia $imagemColorida --saida $mascaraAlinhada
```

O alinhamento utiliza o sistema de coordenadas, a transformação geográfica, a largura e a altura da referência. O método vizinho mais próximo preserva as decisões zero e um. A disponibilidade também considera a máscara interna da imagem de referência.

No exemplo, a grade passa de 20 para 10 metros. Isso permite combinar as posições dos arquivos, mas a informação da classificação continua tendo o detalhe original de 20 metros. O valor 255 é usado apenas durante o cálculo para representar ausência de dados; o arquivo final mantém decisões zero e um e uma máscara interna de disponibilidade.

Aplique a máscara ao mosaico colorido:

```powershell
.\.venv\Scripts\python.exe .\src\aplicar_mascara.py --imagem $imagemColorida --mascara $mascaraAlinhada --saida $imagemFiltrada
```

A aplicação exige uma imagem de três bandas `uint8`, uma máscara de uma banda `uint8` com decisões zero ou um e grades iguais em sistema de coordenadas, transformação e dimensões. O resultado mantém apenas posições com imagem disponível, decisão disponível e valor um.

Os valores RGB originais são copiados. A exclusão fica registrada na máscara interna, que precisa ser respeitada pelo leitor. No mapa, os pixels excluídos são apresentados com transparência. Os GeoTIFFs de entrada permanecem preservados.

O resumo distingue pixels mantidos, excluídos pela regra e sem dados de qualidade, considerando somente as posições com imagem disponível. O percentual mantido é calculado nessa base. As contagens da grade de 10 metros podem diferir das contagens anteriores da SCL de 20 metros. Um resultado com todos os pixels excluídos também pode ser gravado.

Os arquivos de saída precisam ser diferentes das entradas. As etapas registram os caminhos de origem, a regra de seleção e as referências de alinhamento nas tags dos GeoTIFFs correspondentes.

Gere o mapa com o resultado filtrado:

```powershell
.\.venv\Scripts\python.exe .\src\gerar_mapa.py --data 2024-02-01 --raster $imagemFiltrada
```

Atualize o mapa pelo servidor HTTP descrito anteriormente. A seleção pela SCL torna pixels indisponíveis; ela não reconstrói o terreno encoberto por nuvens.

## NDVI

O NDVI é calculado a partir das bandas vermelha (`red`, B04) e infravermelha próxima (`nir`, B08) do Sentinel-2: `(nir - red) / (nir + red)`. Os valores de cada banda são convertidos para reflectância com a escala e o deslocamento dos seus metadados STAC. Valores ausentes e pixels mascarados são excluídos; um zero válido é preservado. Uma soma igual a zero não produz NDVI válido.

O exemplo usa as duas cenas de 1 de fevereiro de 2024 e pressupõe uma consulta existente, com `consulta.json`, e os recortes SCL criados na seção anterior. Substitua a pasta pela da sua consulta:

```powershell
$pastaConsulta = ".\data\raw\earth_search\20261106T001415084591Z"
$paginaSatelite = Join-Path $pastaConsulta "pagina_001.json"
$pastaRecortes = Join-Path ".\data\processed\sentinel2" (Split-Path $pastaConsulta -Leaf)
$idCenaSul = "S2A_T22JCQ_20240201T133141_L2A"
$idCenaNorte = "S2A_T22JCR_20240201T133141_L2A"
```

Inspecione os metadados e recorte as duas bandas de cada cena:

```powershell
.\.venv\Scripts\python.exe .\src\metadados_espectrais.py --pagina $paginaSatelite --id-cena $idCenaSul --asset red
.\.venv\Scripts\python.exe .\src\metadados_espectrais.py --pagina $paginaSatelite --id-cena $idCenaSul --asset nir
foreach ($cena in @($idCenaSul, $idCenaNorte)) {
    foreach ($banda in @('red', 'nir')) {
        .\.venv\Scripts\python.exe .\src\recortar_cena.py --pagina $paginaSatelite --id-cena $cena --asset $banda
    }
}
```

Os recortes espectrais preservam a máscara interna e registram a cena, a banda e os metadados de escala, deslocamento e ausência de dados nas tags. O cálculo lê os ajustes de cada banda na página STAC indicada.

Gere uma máscara de qualidade para cada cena, alinhe-a à respectiva banda vermelha e salve o NDVI:

```powershell
foreach ($cena in @($idCenaSul, $idCenaNorte)) {
    $scl = Join-Path $pastaRecortes "${cena}_scl_chapeco.tif"
    $red = Join-Path $pastaRecortes "${cena}_red_chapeco.tif"
    $nir = Join-Path $pastaRecortes "${cena}_nir_chapeco.tif"
    $mascara = Join-Path $pastaRecortes "${cena}_mascara_qualidade.tif"
    $mascara10m = Join-Path $pastaRecortes "${cena}_mascara_qualidade_10m.tif"
    $ndvi = Join-Path $pastaRecortes "${cena}_ndvi.tif"

    .\.venv\Scripts\python.exe .\src\mascara_qualidade.py --scl $scl --saida $mascara
    .\.venv\Scripts\python.exe .\src\alinhar_mascara.py --mascara $mascara --referencia $red --saida $mascara10m
    .\.venv\Scripts\python.exe .\src\inspecionar_ndvi.py --pagina $paginaSatelite --id-cena $cena --red $red --nir $nir --mascara $mascara10m --saida $ndvi
}
```

O cálculo verifica se as bandas pertencem à mesma cena e têm a mesma grade. A máscara mantém as classes SCL 4, 5 e 6. Seu alinhamento não aumenta o detalhe original da SCL, de 20 metros. O usuário deve assegurar que a máscara corresponda à cena: a grade é verificada, mas sua origem ainda não é validada automaticamente. A saída é um GeoTIFF `float32` com máscara interna e identificação da cena.

Monte o mosaico e avalie sua cobertura dentro do polígono:

```powershell
$ndviSul = Join-Path $pastaRecortes "${idCenaSul}_ndvi.tif"
$ndviNorte = Join-Path $pastaRecortes "${idCenaNorte}_ndvi.tif"
$mosaicoNdvi = Join-Path $pastaRecortes "chapeco_20240201_ndvi_mosaico.tif"
$consultaSatelite = Join-Path $pastaConsulta "consulta.json"

.\.venv\Scripts\python.exe .\src\montar_mosaico_ndvi.py --arquivos $ndviSul $ndviNorte --saida $mosaicoNdvi
.\.venv\Scripts\python.exe .\src\avaliar_mosaico_ndvi.py --raster $mosaicoNdvi --consulta $consultaSatelite
```

Na sobreposição, o mosaico utiliza o primeiro pixel válido conforme a ordem informada; não escolhe automaticamente a cena de melhor qualidade. Os arquivos de origem e sua ordem são registrados nas tags. A cobertura considera os pixels válidos após o filtro e o polígono da consulta, inclusive áreas fora da extensão do raster.

Para exibir o NDVI junto à imagem colorida e aos dados meteorológicos:

```powershell
$imagemColorida = Join-Path $pastaRecortes "chapeco_20240201_mosaico.tif"
.\.venv\Scripts\python.exe .\src\gerar_mapa.py --data 2024-02-01 --raster $imagemColorida --ndvi $mosaicoNdvi
```

Abra o mapa pelo servidor HTTP descrito acima. A legenda mostra faixas escolhidas para visualização; valores fora de `[-1, 1]` aparecem em roxo. A legenda permanece visível quando a camada é desligada. A imagem exibida é uma prévia reduzida; o GeoTIFF conserva seus valores e sua grade.

O NDVI indica uma relação entre as reflectâncias, não identifica por si só lavouras nem diagnostica sua saúde. Reflectâncias negativas podem gerar valores de NDVI fora de `[-1, 1]`; esses valores são mantidos e informados para investigação. A SCL pode apresentar erros. A verificação das datas das cenas, do mosaico e das observações exibidas ainda é manual.

## Tratamento dos dados meteorológicos

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

Os testes de satélite simulam a paginação HTTP, verificam o envio do corpo de continuação e a gravação das duas respostas, incluindo uma página vazia. Também verificam a normalização de várias cenas, a preservação de zero, o tratamento de páginas vazias e a rejeição de porcentagens fora do intervalo permitido.

O teste do mosaico cria pequenos GeoTIFFs locais, com uma e três bandas, para verificar a prioridade na sobreposição, o uso da segunda imagem quando a primeira tem um pixel inválido, a preservação do zero válido, a máscara e a posição geográfica do resultado. A aparência e o alinhamento da camada de satélite também foram conferidos manualmente no navegador.

Os testes da avaliação SCL verificam a contagem das categorias, a exclusão de pixels mascarados e do código zero, a rejeição de códigos desconhecidos e a ausência de classificação. Também verificam cobertura completa, arquivo com extensão parcial, pixels sem dados ou mascarados, nuvens contadas como dados existentes e buracos no polígono.

Os testes da máscara de qualidade verificam as categorias mantidas, a disponibilidade dos pixels e a distinção entre exclusão conhecida e ausência de dados na gravação. O alinhamento é verificado com grades deslocadas, resolução diferente e pixels indisponíveis na origem e na referência. A aplicação verifica a preservação das cores, incluindo preto válido, a rejeição de uma máscara deslocada, as contagens e um resultado com todos os pixels excluídos. O alinhamento do resultado real também foi conferido manualmente no mapa.

Os testes usam dados de exemplo e não dependem de consultas às APIs ou de uma conexão com o banco. O GitHub Actions executa a suíte em Linux com Python 3.12.

## Organização

- `src`: coleta, normalização, carga, processamento das imagens, consulta e geração do mapa.
- `sql`: scripts de criação do banco e das tabelas.
- `tests`: testes automatizados.
- `docs`: documentação complementar.
- `data`: arquivos locais, fora do versionamento.

As miniaturas ficam em `data/previews`, os recortes, mosaicos, máscaras de qualidade e imagens filtradas em `data/processed/sentinel2` e o mapa em `data/maps`.

## Limitações e próximos passos

Os dados meteorológicos têm resolução regional e não representam uma medição realizada diretamente em uma propriedade rural. A umidade relativa do ar não representa a umidade do solo.

O limite municipal é simplificado e serve para a visualização inicial. A validação atual não verifica a validade geométrica completa do polígono. As medições exibidas correspondem ao ponto de consulta e não descrevem a variação meteorológica dentro do município.

A porcentagem de nuvens recebida do catálogo se refere à cena, e não ao polígono de Chapecó. A busca seleciona cenas que intersectam o município; ela não recorta imagens nem garante cobertura completa do município por cada cena. O catálogo atual ainda utiliza um período fixo no código.

A máscara dos recortes considera o polígono e a validade indicada pela imagem de origem. O filtro de qualidade SCL é aplicado pelos scripts de geração, alinhamento e aplicação da máscara. A regra atual mantém vegetação, superfície sem vegetação e água, excluindo as demais categorias. A SCL pode apresentar erros; a seleção não representa uma validação agronômica.

A seleção das cenas e a correspondência entre a data do mosaico e `--data` são manuais. A correspondência entre a data da SCL e a imagem também precisa ser garantida pelo usuário; as verificações de grade não validam a data de aquisição. O gerador não valida a data do GeoTIFF informado. Para reproduzir a comparação, utilize o mesmo limite municipal na consulta e no mapa: o recorte usa o polígono salvo na consulta, enquanto o mapa usa o GeoJSON local mais recente.

A prévia do HTML tem resolução reduzida para exibição e perde detalhes ao ampliar. Os GeoTIFFs mantêm a resolução de origem. A imagem em cores naturais serve para visualização; os próximos indicadores devem utilizar as bandas apropriadas.

As próximas etapas incluem melhorar a rastreabilidade e a automação do processamento, adicionar dados do terreno e preparar a execução na AWS.

## Fontes dos dados

- [NASA POWER — documentação da API diária](https://power.larc.nasa.gov/docs/services/api/temporal/daily/)
- [IBGE — documentação da API de malhas](https://servicodados.ibge.gov.br/api/docs/malhas?versao=4)
- [Earth Search — documentação do catálogo](https://github.com/Element84/earth-search)
- [Copernicus — processamento e categorias SCL](https://sentiwiki.copernicus.eu/web/s2-processing)
- [Rasterio — máscaras de disponibilidade](https://rasterio.readthedocs.io/en/stable/topics/masks.html)
- [OpenStreetMap — dados e atribuição](https://www.openstreetmap.org/copyright)
