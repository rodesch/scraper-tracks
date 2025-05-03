# Scrapers de CDs 

Este repositório contém scripts para extrair informações de CDs de diversos sites de venda.

## Scrapers Disponíveis

- **Sebo do Messias**: Extração de CDs do site Sebo do Messias
- **Sebo do Messias (Selenium)**: Versão alternativa usando Selenium
- **Locomotiva Discos (CDs Usados)**: Extração de CDs usados do site Locomotiva Discos
- **Locomotiva Discos (CDs Novos)**: Extração de CDs novos do site Locomotiva Discos
- **Supernova**: Extração de CDs do site Supernova
- **Supernova (Selenium)**: Versão alternativa usando Selenium
- **Tracks Rio**: Extração de CDs do site Tracks Rio
- **Shopee (LinhuaCong)**: Extração de CDs da loja LinhuaCong na Shopee
- **Pops Discos**: Extração de CDs do site Pops Discos

## Dashboard

O dashboard permite controlar todos os scrapers a partir de uma interface web, visualizar os produtos extraídos, consultar logs de execução e baixar os dados em formato CSV.

### Como executar o dashboard

```
python dashboard.py
```

O dashboard estará disponível em http://localhost:5002/

## Estrutura do Projeto

- `extrair_cds_*.py`: Scripts de scraping para cada site
- `dashboard.py`: Interface web para controle dos scrapers
- `templates/`: Templates HTML para o dashboard
- `static/`: Arquivos estáticos para o dashboard (CSS, JavaScript)
- `exemplos_csv/`: Exemplos de arquivos CSV com estrutura de dados de cada scraper

## Formatos de Dados

Todos os scrapers salvam os dados em arquivos CSV com a seguinte estrutura básica:

```
titulo,preco,categoria,url,data_extracao
```

Alguns scrapers incluem campos adicionais como `artista`, `codigo_produto`, etc.

## Requisitos

- Python 3.6+
- Bibliotecas: requests, beautifulsoup4, selenium (para alguns scrapers), flask (para o dashboard)

## Instalação

1. Clone o repositório
2. Instale as dependências:

```
pip install -r requirements.txt
```

3. Execute o dashboard ou os scrapers individualmente

## Funcionalidades

- Dashboard para monitoramento de scrapers
- Extração de dados de produtos (CDs) de diversas lojas
- Armazenamento em CSV para análise posterior
- Logs detalhados de execução
- Interface web para visualização e busca de produtos

## Lojas Suportadas

- Tracks Rio
- Locomotiva Discos
- Supernova Discos
- Sebo do Messias

## Pré-requisitos

- Python 3.7+
- Bibliotecas Python (veja requirements.txt)
- Navegador web para acessar a interface

## Instalação

1. Clone este repositório:

```bash
git clone https://github.com/rodesch/scraper-tracks.git
cd scraper-tracks
```

2. Instale as dependências necessárias:

```bash
pip3 install -r requirements.txt
```

## Uso

Para iniciar o dashboard:

```bash
python3 dashboard.py
```

Acesse a interface web através do navegador no endereço: http://127.0.0.1:5001/

A partir da interface web você pode:

1. Iniciar e monitorar scrapers
2. Visualizar os produtos extraídos
3. Acessar logs de execução
4. Exportar dados em CSV

## Estrutura do Projeto

- `dashboard.py` - Aplicação principal Flask para interface web
- `scraper-tracks/` - Pasta com scripts individuais de scrapers
  - `extrair_cds_tracks_rio.py` - Scraper para Tracks Rio
  - `extrair_cds_locomotiva.py` - Scraper para Locomotiva Discos
  - `extrair_cds_supernova.py` - Scraper para Supernova Discos
  - `extrair_cds_sebo_messias.py` - Scraper para Sebo do Messias
- `templates/` - Templates HTML para a interface web
- `static/` - Arquivos estáticos (CSS, JavaScript)
- `logs/` - Logs de execução dos scrapers
- `debug/` - Arquivos para debugging

## Documentação dos Scrapers

Cada scraper é projetado para extrair informações de uma loja específica, incluindo:
- Título do produto
- Preço
- URL
- Categoria (quando disponível)

Os dados são salvos em arquivos CSV individuais para cada loja.

## Licença

Este projeto é distribuído sob a licença MIT.

## Contribuições

Contribuições são bem-vindas! Para contribuir, faça um fork do repositório, crie uma branch para sua feature e envie um pull request. 