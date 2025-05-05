# Scrapers de CDs - Sistema Atualizado

Este sistema consiste em um conjunto de scrapers web para coleta de informações sobre CDs à venda em diversas lojas online, junto com um dashboard para controle e visualização.

## Recursos Atualizados

### Novos Scripts de Atualização Automática

- **`atualizar_produtos_locomotiva.py`**: Executa a atualização completa de produtos da Locomotiva Discos
- **`atualizar_todos_scrapers.py`**: Executa a atualização completa de todos os scrapers do sistema

### Scrapers Melhorados

Todos os scrapers foram atualizados para resolver o problema de produtos novos que não estavam sendo capturados:

- Parâmetro `ignorar_produtos_existentes` adicionado para forçar a recoleta de todos os produtos
- Headers anti-cache para garantir respostas atualizadas dos servidores
- Timestamps nas URLs para evitar cache do navegador

### Dashboard Aprimorado

O dashboard web agora inclui:

- Botão para atualização completa da Locomotiva Discos
- Botão para atualização completa de todos os scrapers
- Status em tempo real da execução dos scrapers

## Lojas Suportadas

- Locomotiva Discos (CDs Usados)
- Locomotiva Discos (CDs Novos)
- Tracks Rio
- Supernova Discos
- Sebo do Messias
- Pops Discos
- Shopee (LinhuaCong)

## Requisitos

- Python 3.6+
- Módulos Python listados em requirements.txt
- Chrome e ChromeDriver (para scrapers que usam Selenium)

## Instalação

1. Clone este repositório
2. Instale as dependências:
```bash
pip install -r requirements.txt
```
3. Para scrapers que usam Selenium, certifique-se de que o Chrome e o ChromeDriver estão instalados

## Uso

### Executando o Dashboard

```bash
python3 dashboard.py
```

O dashboard estará disponível em: http://localhost:5002

### Executando Scrapers Individuais

```bash
python3 extrair_cds_<loja>.py
```

### Executando Atualização Completa

Para atualizar apenas a Locomotiva Discos:
```bash
python3 atualizar_produtos_locomotiva.py
```

Para atualizar todos os scrapers:
```bash
python3 atualizar_todos_scrapers.py
```

## Documentação

- `README.md` - Documentação geral
- `README_ATUALIZADO.md` - Este arquivo (documentação atualizada)
- `README_ATUALIZACAO.md` - Detalhes sobre a atualização da Locomotiva Discos
- `README_ATUALIZACAO_GERAL.md` - Detalhes sobre a atualização de todos os scrapers
- `README_SHOPEE.md` - Instruções específicas para o scraper da Shopee
- `README_CREDENCIAIS_SHOPEE.md` - Detalhes sobre as credenciais da Shopee
- `README_DOCKER.md` - Instruções para execução com Docker 