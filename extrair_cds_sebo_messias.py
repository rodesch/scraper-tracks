#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Scraper para o site Sebo do Messias
Este script extrai informações de CDs do site https://sebodomessias.com.br/cds
"""

import os
import csv
import time
import random
import logging
import datetime
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Any, Union
from urllib.parse import urljoin, urlparse, parse_qs, urlencode

# Cria as pastas para logs e debug se não existirem
os.makedirs('logs', exist_ok=True)
os.makedirs('debug', exist_ok=True)

# Verificar se existe uma variável de ambiente para o diretório de debug
DEBUG_DIR = os.environ.get('DEBUG_DIR', 'debug')

# Configuração do logger
data_hora = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILENAME = f"logs/scraper_sebo_messias_{data_hora}.log"
logging.basicConfig(
    filename=LOG_FILENAME,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Configurações
URL_BASE = "https://sebodomessias.com.br/cds"
ARQUIVO_CSV = "produtos_cd_sebo_messias.csv"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Referer": "https://sebodomessias.com.br/"
}

def setup():
    """Configuração inicial e verificação do arquivo CSV"""
    logging.info("Iniciando scraper para o site Sebo do Messias")
    
    # Verifica se o arquivo CSV já existe
    file_exists = os.path.isfile(ARQUIVO_CSV)
    
    # Abre o arquivo CSV para escrita
    csv_file = open(ARQUIVO_CSV, 'a', newline='', encoding='utf-8')
    writer = csv.writer(csv_file)
    
    # Escreve o cabeçalho se o arquivo não existir
    if not file_exists:
        writer.writerow([
            'titulo', 'artista', 'ano', 'conservacao', 
            'preco_original', 'preco_com_desconto', 'categoria', 'url', 'data_extracao'
        ])
        logging.info("Arquivo CSV criado com cabeçalho")
    
    return csv_file, writer

def obter_pagina(url):
    """Obtém o conteúdo HTML da página"""
    try:
        logging.info(f"Acessando URL: {url}")
        
        # Realiza a requisição HTTP
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        
        # Pausa para evitar sobrecarga no servidor
        time.sleep(random.uniform(1, 3))
        
        return response.text
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro ao acessar a página {url}: {str(e)}")
        return None

def extrair_produtos(html):
    """Extrai informações dos produtos da página"""
    produtos = []
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # No Sebo do Messias, os produtos aparecem como itens em uma lista com detalhes específicos
        # Vamos procurar por todos os itens que têm lista de detalhes de CD
        
        # Procura por todas as entradas de produtos que começam com a estrutura observada no site
        produtos_html = soup.find_all(lambda tag: tag.name == 'li' and tag.find('h2') is not None)
        
        if not produtos_html:
            # Busca alternativa para identificar produtos
            produtos_html = soup.select('li:has(img):has(.product-name)')
        
        logging.info(f"Encontrados {len(produtos_html)} produtos potenciais na página atual")
        
        # Debug - imprimir os primeiros produtos encontrados para ver sua estrutura
        for i, prod in enumerate(produtos_html[:3]):
            logging.info(f"Estrutura do produto {i+1}: {prod.name} com classes {prod.get('class', [])}")
        
        for item in produtos_html:
            try:
                # Extrai o título do produto
                titulo_elem = item.find('h2') or item.select_one('.product-name')
                if titulo_elem:
                    titulo_link = titulo_elem.find('a')
                    if titulo_link:
                        titulo = titulo_link.get_text().strip()
                        url = urljoin(URL_BASE, titulo_link['href']) if 'href' in titulo_link.attrs else ""
                    else:
                        titulo = titulo_elem.get_text().strip()
                        url = ""
                else:
                    titulo = "Não disponível"
                    url = ""
                
                # Extrai detalhes do produto
                detalhes = item.select('li') or item.select('.details')
                
                artista = "Não disponível"
                ano = "Não disponível"
                conservacao = "Não disponível"
                categoria = "CD"
                
                # Procura por elementos que contenham os detalhes do artista, ano e conservação
                for detalhe in detalhes:
                    texto = detalhe.get_text().strip()
                    if "Artista:" in texto:
                        artista = texto.replace("Artista:", "").strip()
                    elif "Ano:" in texto:
                        ano = texto.replace("Ano:", "").strip()
                    elif "Conservação:" in texto:
                        conservacao = texto.replace("Conservação:", "").strip()
                    elif "CD" in texto and len(texto) < 30:  # Possível categoria
                        categoria = texto.strip()
                
                # Identifica os preços - original e com desconto
                preco_original = "Não disponível"
                preco_com_desconto = "Não disponível"
                
                # Busca pelo elemento que contém os preços
                preco_elem = item.select_one('.price-box') or item.select_one('.price')
                
                if preco_elem:
                    # Procura pelo preço original (normalmente riscado)
                    preco_original_elem = preco_elem.select_one('del') or preco_elem.select_one('.old-price')
                    if preco_original_elem:
                        preco_original = preco_original_elem.get_text().strip()
                    
                    # Procura pelo preço com desconto
                    preco_desconto_elem = preco_elem.select_one('ins') or preco_elem.select_one('.special-price') or preco_elem.select_one('.price')
                    if preco_desconto_elem:
                        preco_com_desconto = preco_desconto_elem.get_text().strip()
                
                # Se não encontrou preço com desconto, usa o preço original
                if preco_com_desconto == "Não disponível" and preco_original != "Não disponível":
                    preco_com_desconto = preco_original
                
                # Tenta extrair categoria diretamente
                categoria_elem = item.select_one('.category')
                if categoria_elem:
                    categoria = categoria_elem.get_text().strip()
                
                # Adiciona o produto à lista
                produtos.append({
                    'titulo': titulo,
                    'artista': artista,
                    'ano': ano,
                    'conservacao': conservacao,
                    'preco_original': preco_original,
                    'preco_com_desconto': preco_com_desconto,
                    'categoria': categoria,
                    'url': url,
                    'data_extracao': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
                logging.info(f"Produto extraído: {titulo}")
            
            except Exception as e:
                logging.error(f"Erro ao extrair produto: {str(e)}")
                continue
        
        return produtos
    
    except Exception as e:
        logging.error(f"Erro ao extrair produtos da página: {str(e)}")
        return []

def obter_proxima_pagina(html, url_atual):
    """Verifica se existe próxima página e retorna sua URL"""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Procura por links de navegação para a próxima página
        next_link = None
        
        # Busca direta por elementos de paginação
        paginacao = soup.select_one('.pages') or soup.select_one('.pagination')
        
        if paginacao:
            # Tenta encontrar um link para a próxima página (geralmente "Next" ou "Próximo")
            for link in paginacao.find_all('a'):
                if 'Next' in link.get_text() or 'Próximo' in link.get_text() or 'next' in link.get('class', []):
                    next_link = link
                    break
            
            if next_link and 'href' in next_link.attrs:
                return urljoin(URL_BASE, next_link['href'])
        
        # Se não encontrou com a busca acima, procura por links específicos de paginação
        # Tenta encontrar o link "Next"
        next_links = soup.find_all('a', string='Next') or soup.find_all('a', string='Próximo') or soup.select('a.next')
        if next_links and 'href' in next_links[0].attrs:
            return urljoin(URL_BASE, next_links[0]['href'])
        
        # Busca por link com texto "Next" dentro de um span
        for link in soup.find_all('a'):
            if link.find('span') and ('Next' in link.find('span').get_text() or 'Próximo' in link.find('span').get_text()):
                return urljoin(URL_BASE, link['href'])
        
        # Alternativa: incrementar o parâmetro de página na URL
        parsed_url = urlparse(url_atual)
        query_params = parse_qs(parsed_url.query)
        
        # Verifica se a URL usa parâmetros de paginação
        if 'p' in query_params:
            try:
                current_page = int(query_params['p'][0])
                query_params['p'] = [str(current_page + 1)]
                new_query = urlencode(query_params, doseq=True)
                parsed_url = parsed_url._replace(query=new_query)
                return parsed_url.geturl()
            except (ValueError, IndexError):
                pass
        
        # Última tentativa: Verifica se a URL tem um formato de página numérica embutido
        # Exemplo: /cds/page/2/
        if '/page/' in url_atual:
            try:
                # Extrai o número da página atual
                page_pattern = r'/page/(\d+)/'
                import re
                match = re.search(page_pattern, url_atual)
                if match:
                    current_page = int(match.group(1))
                    next_page = current_page + 1
                    return re.sub(page_pattern, f'/page/{next_page}/', url_atual)
            except Exception as e:
                logging.error(f"Erro ao extrair número da página da URL: {str(e)}")
        
        # Se for a primeira página, tenta adicionar ?p=2 ou /page/2/
        if '?' not in url_atual and '/page/' not in url_atual:
            if url_atual.endswith('/'):
                return url_atual + 'page/2/'
            else:
                return url_atual + '?p=2'
        
        return None
    
    except Exception as e:
        logging.error(f"Erro ao buscar próxima página: {str(e)}")
        return None

def salvar_produtos(writer, produtos):
    """Salva os produtos no arquivo CSV"""
    for produto in produtos:
        writer.writerow([
            produto['titulo'],
            produto['artista'],
            produto['ano'],
            produto['conservacao'],
            produto['preco_original'],
            produto['preco_com_desconto'],
            produto['categoria'],
            produto['url'],
            produto['data_extracao']
        ])
    
    logging.info(f"Salvos {len(produtos)} produtos no CSV")

def extrair_todos_produtos():
    """Função principal que coordena a extração de produtos de todas as páginas"""
    try:
        # Configuração inicial
        csv_file, writer = setup()
        
        url = URL_BASE
        pagina_atual = 1
        total_produtos = 0
        max_paginas = 100  # Limite de segurança para não entrar em loop infinito
        
        # Loop de extração pelas páginas
        while url and pagina_atual <= max_paginas:
            logging.info(f"Processando página {pagina_atual}")
            
            # Obtém o HTML da página
            html = obter_pagina(url)
            if not html:
                logging.error(f"Não foi possível obter a página {pagina_atual}")
                break
            
            # Salva a página HTML para debug
            debug_filename = f"{DEBUG_DIR}/debug_page_sebo_{data_hora}_{pagina_atual}.html"
            with open(debug_filename, "w", encoding="utf-8") as f:
                f.write(html)
            logging.info(f"Página salva para debug em: {debug_filename}")
            
            # Extrai produtos da página
            produtos = extrair_produtos(html)
            
            if produtos:
                # Salva produtos no CSV
                salvar_produtos(writer, produtos)
                total_produtos += len(produtos)
                logging.info(f"Total acumulado de produtos: {total_produtos}")
            else:
                logging.warning(f"Nenhum produto encontrado na página {pagina_atual}")
                
                # Se não encontrou produtos, mas é a primeira página, tenta uma segunda página
                if pagina_atual == 1:
                    teste_segunda_pagina = URL_BASE + "?p=2"
                    logging.info(f"Tentando acessar a segunda página diretamente: {teste_segunda_pagina}")
                    html_p2 = obter_pagina(teste_segunda_pagina)
                    
                    if html_p2:
                        # Salva a segunda página para debug
                        debug_filename_p2 = f"{DEBUG_DIR}/debug_page_sebo_{data_hora}_p2_teste.html"
                        with open(debug_filename_p2, "w", encoding="utf-8") as f:
                            f.write(html_p2)
                        
                        # Verifica se tem produtos na segunda página
                        produtos_p2 = extrair_produtos(html_p2)
                        if produtos_p2:
                            logging.info(f"Encontrados {len(produtos_p2)} produtos na página 2 de teste")
                            # Continua a partir da página 2
                            url = teste_segunda_pagina
                            pagina_atual = 2
                            continue
            
            # Verifica se há próxima página
            next_url = obter_proxima_pagina(html, url)
            
            if next_url:
                url = next_url
                logging.info(f"Próxima página: {url}")
                pagina_atual += 1
                
                # Pausa entre páginas
                time.sleep(random.uniform(3, 5))
            else:
                logging.info("Não foram encontradas mais páginas. Finalizando extração.")
                break
        
        # Finaliza a extração
        csv_file.close()
        logging.info(f"Extração finalizada. Total de produtos: {total_produtos}")
        return True
    
    except Exception as e:
        logging.error(f"Erro na extração de produtos: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        logging.info("Iniciando extração de produtos do Sebo do Messias")
        sucesso = extrair_todos_produtos()
        
        if sucesso:
            logging.info("Scraper concluído com sucesso")
        else:
            logging.error("Scraper finalizado com erros")
    
    except Exception as e:
        logging.error(f"Erro fatal no scraper: {str(e)}") 