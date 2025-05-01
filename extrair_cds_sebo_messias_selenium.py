#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Scraper para o site Sebo do Messias usando Selenium
Este script extrai informações de CDs do site https://sebodomessias.com.br/cds
"""

import os
import csv
import time
import random
import logging
import datetime
import requests
import platform
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import
from typing import List, Dict, Optional, Any, Union TimeoutException, NoSuchElementException, StaleElementReferenceException

# Cria as pastas para logs e debug se não existirem
os.makedirs('logs', exist_ok=True)
os.makedirs('debug', exist_ok=True)

# Configuração do logger
data_hora = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILENAME = f"logs/scraper_sebo_messias_selenium_{data_hora}.log"
logging.basicConfig(
    filename=LOG_FILENAME,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Configurações
URL_BASE = "https://sebodomessias.com.br/cds"
ARQUIVO_CSV = "produtos_cd_sebo_messias.csv"

# Verifica se a variável de ambiente DEBUG_DIR está definida
DEBUG_DIR = os.environ.get('DEBUG_DIR', 'debug')

def setup():
    """Configuração inicial e verificação do arquivo CSV"""
    logging.info("Iniciando scraper para o site Sebo do Messias com Selenium")
    
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

def inicializar_driver():
    """Inicializa e configura o driver Selenium com compatibilidade para diferentes sistemas"""
    try:
        logging.info("Inicializando o driver Selenium")
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Execução sem interface gráfica
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        sistema = platform.system()
        logging.info(f"Sistema operacional: {sistema}")
        
        if sistema == "Darwin":  # macOS
            # Para macOS, tentamos usar o Safari Driver ou Chrome com configuração específica
            try:
                logging.info("Tentando usar o Safari Driver no macOS")
                return webdriver.Safari()
            except Exception as e:
                logging.warning(f"Erro ao inicializar Safari Driver: {str(e)}")
                
                # Alternativa: tentar usar Chrome com configuração específica para macOS
                try:
                    logging.info("Tentando usar Chrome no macOS")
                    return webdriver.Chrome(options=chrome_options)
                except Exception as e:
                    logging.error(f"Erro ao inicializar Chrome no macOS: {str(e)}")
                    raise
        else:
            # Para Windows/Linux, usamos o Chrome com webdriver-manager
            from webdriver_manager.chrome import ChromeDriverManager
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            driver.set_page_load_timeout(30)
            return driver
    
    except Exception as e:
        logging.error(f"Erro ao inicializar o driver Selenium: {str(e)}")
        raise

def acessar_pagina(driver, url):
    """Acessa uma página usando o driver Selenium"""
    try:
        logging.info(f"Acessando URL: {url}")
        driver.get(url)
        
        # Aguarda o carregamento da página
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Pausa para garantir o carregamento completo
        time.sleep(random.uniform(2, 4))
        
        # Captura o HTML da página
        html = driver.page_source
        
        # Salva o HTML para debug
        url_filename = url.replace('https://', '').replace('/', '_')
        debug_filename = f"{DEBUG_DIR}/debug_page_sebo_selenium_{data_hora}_{url_filename}.html"
        with open(debug_filename, "w", encoding="utf-8") as f:
            f.write(html)
        logging.info(f"Página salva para debug em: {debug_filename}")
        
        return html
    
    except TimeoutException:
        logging.error(f"Timeout ao acessar a página {url}")
        return None
    except Exception as e:
        logging.error(f"Erro ao acessar a página {url}: {str(e)}")
        return None

def extrair_produtos(html):
    """Extrai informações dos produtos da página"""
    produtos = []
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Encontrar os produtos usando o seletor específico do Sebo do Messias
        # Estamos procurando por elementos com ID que contém 'rptVitrineColuna'
        itens_produtos = soup.find_all(lambda tag: tag.name == 'div' and 
                                              tag.get('id') and 
                                              'rptVitrineColuna' in tag.get('id'))
        
        if not itens_produtos:
            logging.warning("Container de produtos não encontrado na página")
            # Tenta uma abordagem alternativa
            itens_produtos = soup.select('[id*="rptVitrineColuna"]')
            
            if not itens_produtos:
                # Última tentativa - procura por qualquer elemento que pareça um produto
                itens_produtos = soup.select('.card-text, .product-details')
        
        logging.info(f"Encontrados {len(itens_produtos)} produtos potenciais na página")
        
        # Extrai informações de cada produto
        for idx, item in enumerate(itens_produtos):
            try:
                # Busca pelo título e URL do produto
                titulo_elem = item.select_one('a[href*="cd"]') or item.select_one('h3 a')
                if not titulo_elem:
                    # Tenta procurar no contexto maior
                    parent = item.parent
                    titulo_elem = parent.select_one('a[href*="cd"]') or parent.select_one('h3 a')
                
                if not titulo_elem:
                    continue
                
                titulo = titulo_elem.get_text().strip() if titulo_elem.get_text() else "Sem título"
                if not titulo or titulo == "Sem título":
                    # Tenta extrair o título da URL
                    url = urljoin(URL_BASE, titulo_elem['href']) if 'href' in titulo_elem.attrs else ""
                    if url:
                        parts = url.split('/')
                        if len(parts) > 0:
                            titulo = parts[-1].replace('-', ' ').title()
                
                url = urljoin(URL_BASE, titulo_elem['href']) if 'href' in titulo_elem.attrs else ""
                
                # Busca por detalhes do produto
                artista = "Não disponível"
                ano = "Não disponível"
                conservacao = "Não disponível"
                categoria = "CD"
                
                # Tenta extrair o artista
                artista_elem = item.select_one('[id*="lblResponsavel"]')
                if artista_elem and artista_elem.next_sibling and artista_elem.next_sibling.next_sibling:
                    artista = artista_elem.next_sibling.next_sibling.get_text().strip()
                
                # Tenta extrair categoria
                categoria_elem = item.select_one('.category') or item.select_one('ul.category li')
                if categoria_elem:
                    categoria = categoria_elem.get_text().strip()
                
                # Tenta extrair informações de outros detalhes
                detalhes_lista = item.select('.product-details li') or item.select('li')
                for detalhe in detalhes_lista:
                    texto = detalhe.get_text().strip()
                    if "Artista:" in texto or "Responsável:" in texto:
                        artista = texto.split(':', 1)[1].strip() if ':' in texto else texto
                    elif "Ano:" in texto:
                        ano = texto.split(':', 1)[1].strip() if ':' in texto else texto
                    elif "Conservação:" in texto or "Estado:" in texto:
                        conservacao = texto.split(':', 1)[1].strip() if ':' in texto else texto
                
                # Busca por preços
                preco_original = "Não disponível"
                preco_com_desconto = "Não disponível"
                
                # Preço original (pode estar em span.price-old)
                preco_original_elem = item.select_one('.price-old') or item.select_one('del') or item.select_one('.old-price .price')
                if preco_original_elem:
                    preco_original = preco_original_elem.get_text().strip()
                    # Limpa o texto para extrair apenas o valor
                    preco_original = re.sub(r'[^0-9,.]', '', preco_original)
                
                # Preço com desconto (pode estar em span.price-new)
                preco_desconto_elem = item.select_one('.price-new') or item.select_one('ins') or item.select_one('.special-price .price') or item.select_one('.price')
                if preco_desconto_elem:
                    preco_com_desconto = preco_desconto_elem.get_text().strip()
                    # Limpa o texto para extrair apenas o valor
                    preco_com_desconto = re.sub(r'[^0-9,.]', '', preco_com_desconto)
                
                # Adiciona o produto à lista
                produto = {
                    'titulo': titulo,
                    'artista': artista,
                    'ano': ano,
                    'conservacao': conservacao,
                    'preco_original': preco_original,
                    'preco_com_desconto': preco_com_desconto,
                    'categoria': categoria,
                    'url': url,
                    'data_extracao': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                produtos.append(produto)
                logging.info(f"Produto extraído: {titulo}")
            
            except Exception as e:
                logging.error(f"Erro ao extrair produto {idx}: {str(e)}")
                continue
        
        return produtos
    
    except Exception as e:
        logging.error(f"Erro ao extrair produtos da página: {str(e)}")
        return []

def verificar_proxima_pagina(driver, pagina_atual):
    """Verifica se existe próxima página e retorna True se conseguir acessá-la"""
    try:
        # Tenta encontrar o elemento de paginação
        paginacao = None
        try:
            paginacao = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.pagination, .pager, [id*="paginacao"]'))
            )
        except TimeoutException:
            # Tenta encontrar os elementos <a> de paginação numerada
            try:
                # Busca por links de paginação específicos do site
                proxima_pagina = pagina_atual + 1
                xpath_pagina = f"//a[contains(@href, '?p={proxima_pagina}') or contains(@href, 'page={proxima_pagina}') or contains(text(), '{proxima_pagina}')]"
                links_paginacao = driver.find_elements(By.XPATH, xpath_pagina)
                
                if links_paginacao:
                    logging.info(f"Link direto para página {proxima_pagina} encontrado")
                    links_paginacao[0].click()
                    time.sleep(random.uniform(3, 5))
                    return True
            except Exception as e:
                logging.error(f"Erro ao buscar links de paginação numerada: {str(e)}")
        
        # Se encontrou o elemento de paginação principal
        if paginacao:
            # Busca pelo link "Próximo"/"Next" ou similar
            next_links = paginacao.find_elements(By.XPATH, ".//a[contains(text(), 'Next') or contains(text(), 'Próximo') or contains(text(), 'Próxima') or contains(text(), '>')]")
            
            if next_links:
                logging.info(f"Link para próxima página encontrado após a página {pagina_atual}")
                next_links[0].click()
                time.sleep(random.uniform(3, 5))
                return True
            
            # Alternativa: busca pelo número da próxima página
            proxima_pagina = pagina_atual + 1
            page_links = paginacao.find_elements(By.TAG_NAME, "a")
            
            for link in page_links:
                try:
                    if link.text.strip() == str(proxima_pagina):
                        logging.info(f"Link para página {proxima_pagina} encontrado")
                        link.click()
                        time.sleep(random.uniform(3, 5))
                        return True
                except (ValueError, StaleElementReferenceException):
                    continue
        
        # Se não encontrou links de paginação, tenta uma abordagem direta
        try:
            # Tenta acessar a próxima página diretamente pela URL
            next_url = f"{URL_BASE}?p={proxima_pagina}"
            logging.info(f"Tentando acessar diretamente a URL: {next_url}")
            driver.get(next_url)
            
            # Verifica se a página carregou corretamente
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Verifica se tem produtos na página
            produtos_container = driver.find_elements(By.CSS_SELECTOR, '[id*="rptVitrineColuna"], .product-details')
            if produtos_container:
                logging.info(f"Próxima página {proxima_pagina} acessada diretamente via URL")
                return True
            else:
                logging.info(f"Próxima página {proxima_pagina} acessada, mas não contém produtos")
                return False
        
        except (TimeoutException, NoSuchElementException) as e:
            logging.info(f"Não foi possível acessar a próxima página {proxima_pagina} diretamente: {str(e)}")
            return False
        
        return False
    
    except Exception as e:
        logging.error(f"Erro ao verificar próxima página: {str(e)}")
        return False

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
        driver = inicializar_driver()
        
        pagina_atual = 1
        total_produtos = 0
        max_paginas = 50  # Limite de segurança
        
        try:
            # Acessa a página inicial
            html = acessar_pagina(driver, URL_BASE)
            
            if not html:
                logging.error("Não foi possível acessar a página inicial")
                return False
            
            # Loop pelas páginas
            while pagina_atual <= max_paginas:
                logging.info(f"Processando página {pagina_atual}")
                
                # Extrai produtos da página atual
                produtos = extrair_produtos(driver.page_source)
                
                if produtos:
                    # Salva os produtos encontrados
                    salvar_produtos(writer, produtos)
                    total_produtos += len(produtos)
                    logging.info(f"Total acumulado de produtos: {total_produtos}")
                else:
                    logging.warning(f"Nenhum produto encontrado na página {pagina_atual}")
                
                # Verifica se existe próxima página
                if verificar_proxima_pagina(driver, pagina_atual):
                    pagina_atual += 1
                else:
                    logging.info("Não há mais páginas disponíveis")
                    break
            
            logging.info(f"Extração finalizada. Total de produtos: {total_produtos}")
            return True
        
        finally:
            # Fecha o driver e o arquivo CSV
            if driver:
                driver.quit()
            
            csv_file.close()
    
    except Exception as e:
        logging.error(f"Erro na extração de produtos: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        logging.info("Iniciando extração de produtos do Sebo do Messias com Selenium")
        sucesso = extrair_todos_produtos()
        
        if sucesso:
            logging.info("Scraper concluído com sucesso")
        else:
            logging.error("Scraper finalizado com erros")
    
    except Exception as e:
        logging.error(f"Erro fatal no scraper: {str(e)}") 