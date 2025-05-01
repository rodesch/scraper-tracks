#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Scraper para o site Supernova Discos usando Selenium
Este script extrai informações de CDs do site https://www.supernovadiscos.com.br/
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
from typing import List, Dict, Optional, Any, Union TimeoutException, NoSuchElementException, WebDriverException

# Cria as pastas para logs e debug se não existirem
os.makedirs('logs', exist_ok=True)
os.makedirs('debug', exist_ok=True)

# Verificar se existe uma variável de ambiente para o diretório de debug
DEBUG_DIR = os.environ.get('DEBUG_DIR', 'debug')

# Configuração do logger
data_hora = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILENAME = f"logs/scraper_supernova_selenium_{data_hora}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILENAME),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('scraper_supernova_selenium')

class SupernovaDiscosSeleniumScraper:
    """Classe para extrair informações de CDs do site Supernova Discos utilizando Selenium para simular scroll infinito"""
    
    BASE_URL = "https://www.supernovadiscos.com.br"
    DEFAULT_OUTPUT = "produtos_cd_supernova_selenium.csv"
    
    def __init__(self, url_inicial: str = None, 
                 max_scrolls: int = 50, 
                 scroll_wait: float = 2.0,
                 arquivo_saida: str = None,
                 headless: bool = True) -> None:
        """
        Inicializa o scraper com parâmetros configuráveis
        
        Args:
            url_inicial: URL para começar a extração (se None, usa a padrão)
            max_scrolls: Número máximo de scrolls a serem executados
            scroll_wait: Tempo de espera após cada scroll (segundos)
            arquivo_saida: Nome do arquivo CSV de saída
            headless: Se True, executa o navegador em modo headless (invisível)
        """
        self.url_inicial = url_inicial or "https://www.supernovadiscos.com.br/discos/cds/?sort_by=created-descending"
        self.max_scrolls = max_scrolls
        self.scroll_wait = scroll_wait
        self.arquivo_saida = arquivo_saida or self.DEFAULT_OUTPUT
        self.headless = headless
        self.todos_produtos = []
        self.driver = None
        
        # Verificar se já existe arquivo de produtos para continuar a partir dele
        self._carregar_produtos_existentes()
    
    def _carregar_produtos_existentes(self) -> None:
        """Carrega produtos de um arquivo CSV existente, se disponível"""
        if os.path.exists(self.arquivo_saida):
            try:
                with open(self.arquivo_saida, 'r', encoding='utf-8') as arquivo:
                    leitor = csv.DictReader(arquivo)
                    self.todos_produtos = list(leitor)
                    logger.info(f"Carregados {len(self.todos_produtos)} produtos do arquivo existente.")
            except Exception as e:
                logger.error(f"Erro ao carregar arquivo existente: {e}")
    
    def inicializar_driver(self) -> None:
        """Inicializa o driver do Selenium Chrome"""
        try:
            # Configura as opções do Chrome
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36")
            
            # Inicializa o driver
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(30)
            logger.info("Driver do Selenium inicializado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao inicializar o driver: {e}")
            raise e
    
    def fechar_driver(self) -> None:
        """Fecha o driver do Selenium"""
        if self.driver:
            self.driver.quit()
            logger.info("Driver do Selenium fechado.")
    
    def scroll_para_baixo(self) -> bool:
        """
        Executa um scroll para baixo na página
        
        Returns:
            bool: True se a altura da página mudou após o scroll, False caso contrário
        """
        try:
            # Obtém a altura atual da página
            altura_anterior = self.driver.execute_script("return document.body.scrollHeight")
            
            # Executa o scroll
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Aguarda um pouco para carregar novos elementos
            time.sleep(self.scroll_wait)
            
            # Obtém a nova altura
            nova_altura = self.driver.execute_script("return document.body.scrollHeight")
            
            # Retorna se houve mudança na altura
            return nova_altura > altura_anterior
        except Exception as e:
            logger.error(f"Erro ao executar scroll: {e}")
            return False
    
    def extrair_produtos_pagina(self) -> List[Dict[str, str]]:
        """
        Extrai todos os produtos da página atual
        
        Returns:
            Lista de dicionários contendo informações dos produtos
        """
        produtos = []
        
        try:
            # Localiza todos os elementos de produto
            # Espera até que pelo menos alguns produtos estejam visíveis
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".js-item-product, .item.product, .product-item, .item-product, div[data-product]"))
                )
            except TimeoutException:
                logger.warning("Timeout ao aguardar elementos de produto")
            
            # Tenta identificar os produtos usando diferentes seletores
            elementos_produto = []
            
            # Tenta com seletores comuns
            seletores = [
                ".js-item-product", 
                ".item.product", 
                ".product-item", 
                ".product-box", 
                "div[data-product]",
                ".producto", 
                ".list-item", 
                ".item-product",
                ".grid-item"
            ]
            
            for seletor in seletores:
                elementos = self.driver.find_elements(By.CSS_SELECTOR, seletor)
                if elementos:
                    logger.info(f"Encontrados {len(elementos)} elementos com o seletor: {seletor}")
                    elementos_produto.extend(elementos)
            
            # Se ainda não encontrou, tenta encontrar todos os links nas seções de produtos
            if not elementos_produto:
                container = self.driver.find_element(By.CSS_SELECTOR, ".js-product-table, .product-grid, .products-list, main, .category-products")
                if container:
                    elementos_produto = container.find_elements(By.TAG_NAME, "a")
            
            logger.info(f"Encontrados {len(elementos_produto)} possíveis elementos de produto na página.")
            
            # Debug - imprime o HTML para análise
            with open(f"debug_page_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            
            for elemento in elementos_produto:
                try:
                    # Verifica se o elemento ainda está válido no DOM
                    try:
                        elemento.is_displayed()  # Testa se o elemento está válido
                    except StaleElementReferenceException:
                        continue
                    
                    # Extrai o título do produto
                    titulo = ""
                    try:
                        # Tenta várias abordagens para extrair o título
                        titulo_element = elemento.find_element(By.CSS_SELECTOR, "h3, h2, .title, .name, .product-title")
                        titulo = titulo_element.text.strip()
                    except NoSuchElementException:
                        try:
                            # Tenta extrair de atributos
                            titulo = elemento.get_attribute("title") or elemento.get_attribute("data-name") or ""
                            if not titulo:
                                # Tenta extrair de links
                                link = elemento.find_element(By.TAG_NAME, "a")
                                titulo = link.get_attribute("title") or link.text.strip()
                        except:
                            try:
                                # Tenta extrair de imagens
                                img = elemento.find_element(By.TAG_NAME, "img")
                                titulo = img.get_attribute("alt") or ""
                            except:
                                # Última tentativa: usa o texto completo do elemento
                                titulo = elemento.text.strip()
                                
                                # Se o texto for muito longo, tenta extrair a primeira linha
                                if len(titulo) > 100:
                                    linhas = titulo.split('\n')
                                    titulo = linhas[0].strip()
                    
                    # Depuração
                    logger.info(f"Título encontrado: {titulo[:50]}...")
                    
                    # Verifica se o título não está vazio
                    if not titulo:
                        continue
                    
                    # Extrai o preço
                    preco_texto = ""
                    try:
                        preco_element = elemento.find_element(By.CSS_SELECTOR, ".price, .product-price, .js-price-display, .item-price")
                        preco_texto = preco_element.text.strip()
                    except NoSuchElementException:
                        try:
                            # Busca no conteúdo de texto do elemento
                            texto_elemento = elemento.text
                            preco_match = re.search(r'R\$\s*(\d+[,.]\d+)', texto_elemento)
                            if preco_match:
                                preco_texto = preco_match.group(0)
                            else:
                                # Se não encontrar o padrão R$, tenta outros formatos de preço
                                preco_match = re.search(r'(\d+[,.]\d+)', texto_elemento)
                                if preco_match:
                                    preco_texto = f"R$ {preco_match.group(0)}"
                        except:
                            pass
                    
                    # Se não conseguiu extrair preço, tenta mais uma vez com regex em todo o texto
                    if not preco_texto:
                        try:
                            html = elemento.get_attribute('innerHTML')
                            preco_match = re.search(r'R\$\s*(\d+[,.]\d+)', html)
                            if preco_match:
                                preco_texto = preco_match.group(0)
                        except:
                            pass
                    
                    # Se ainda não encontrou preço, continua com o próximo elemento
                    if not preco_texto:
                        logger.warning(f"Não foi possível extrair o preço para o produto: {titulo[:50]}")
                        continue
                    
                    # Extrai a URL do produto
                    url_produto = ""
                    try:
                        if elemento.tag_name == "a":
                            url_produto = elemento.get_attribute("href")
                        else:
                            # Procura por um link dentro do elemento
                            link = elemento.find_element(By.TAG_NAME, "a")
                            url_produto = link.get_attribute("href")
                    except NoSuchElementException:
                        try:
                            # Tenta encontrar o link usando JavaScript
                            url_produto = self.driver.execute_script(
                                "return arguments[0].querySelector('a').getAttribute('href');", 
                                elemento
                            )
                        except:
                            continue
                    
                    # Verifica se a URL é válida
                    if not url_produto:
                        continue
                    
                    # Extrai informações sobre banda/artista e álbum do título
                    artista = ""
                    album = ""
                    if " - " in titulo:
                        partes = titulo.split(" - ", 1)
                        artista = partes[0].strip()
                        album = partes[1].strip()
                    else:
                        album = titulo
                    
                    # Extrai a categoria com base no título e URL
                    categoria = self.extrair_categoria(titulo, url_produto)
                    
                    # Adiciona o produto à lista
                    produtos.append({
                        'titulo': titulo,
                        'artista': artista,
                        'album': album,
                        'preco': preco_texto,
                        'categoria': categoria,
                        'url': url_produto,
                        'data_extracao': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                    
                    logger.info(f"Produto extraído com sucesso: {titulo[:50]}...")
                
                except Exception as e:
                    logger.warning(f"Erro ao processar um elemento de produto: {e}")
                    continue
            
            logger.info(f"Extraídos {len(produtos)} produtos nesta página.")
            return produtos
            
        except Exception as e:
            logger.error(f"Erro ao extrair produtos da página: {e}")
            return []
    
    @staticmethod
    def extrair_categoria(titulo: str, url_produto: str) -> str:
        """
        Extrai a categoria do CD com base no título e URL
        
        Args:
            titulo: Título do produto
            url_produto: URL do produto
            
        Returns:
            Nome da categoria
        """
        titulo_lower = titulo.lower()
        url_lower = url_produto.lower()
        
        # Tenta extrair a categoria da URL primeiro
        if 'rock' in url_lower:
            # Tenta ser mais específico
            if 'classic' in url_lower or '70' in url_lower:
                return "Rock Clássico / Prog / 70's"
            elif 'metal' in url_lower or 'punk' in url_lower or 'grunge' in url_lower:
                return "Metal / Punk / Grunge"
            elif 'alt' in url_lower or 'indie' in url_lower or 'pop' in url_lower:
                return "Alternativo / Indie / Pop Rock"
            else:
                return "Rock"
        elif 'jazz' in url_lower or 'blues' in url_lower:
            return "Jazz / Blues"
        elif 'brasil' in url_lower:
            return "Brasil"
        elif 'trilha' in url_lower:
            return "Trilha Sonora"
        elif 'rap' in url_lower or 'hip' in url_lower:
            return "Rap / Hip Hop"
        elif 'pop' in url_lower:
            return "Pop / Cantoras"
        
        # Se não conseguir extrair da URL, tenta pelo título
        categorias = [
            (["rock", "prog", "psych", "70", "60"], "Rock Clássico / Prog / 70's"),
            (["metal", "punk", "grunge", "thrash", "death", "black"], "Metal / Punk / Grunge"),
            (["alt", "indie", "pop rock", "new wave", "post"], "Alternativo / Indie / Pop Rock"),
            (["jazz", "blues"], "Jazz / Blues"),
            (["brasil", "mpb", "samba", "bossa", "choro", "nacional"], "Brasil"),
            (["trilha", "soundtrack", "ost"], "Trilha Sonora"),
            (["rap", "hip hop", "hip-hop"], "Rap / Hip Hop"),
            (["pop", "cantora", "diva"], "Pop / Cantoras")
        ]
        
        for termos, categoria in categorias:
            if any(termo in titulo_lower for termo in termos):
                return categoria
        
        return "Outros"
    
    def salvar_para_csv(self, produtos: List[Dict[str, str]], modo: str = 'w') -> bool:
        """
        Salva os produtos em um arquivo CSV
        
        Args:
            produtos: Lista de dicionários com informações dos produtos
            modo: Modo de escrita do arquivo ('w' para sobrescrever, 'a' para anexar)
            
        Returns:
            True se salvou com sucesso, False caso contrário
        """
        try:
            # Verifica se há produtos para salvar
            if not produtos:
                logger.warning("Nenhum produto para salvar.")
                return False
            
            # Campos a serem salvos
            campos = ['titulo', 'artista', 'album', 'preco', 'categoria', 'url', 'data_extracao']
            
            # Verifica se o arquivo já existe e se o modo é 'w'
            arquivo_existe = os.path.exists(self.arquivo_saida)
            
            # Escreve no arquivo CSV
            with open(self.arquivo_saida, modo, newline='', encoding='utf-8') as arquivo:
                escritor = csv.writer(arquivo, quoting=csv.QUOTE_ALL)
                
                # Escreve o cabeçalho apenas se estiver criando um novo arquivo
                if modo == 'w' or not arquivo_existe:
                    escritor.writerow(campos)
                
                # Escreve os dados de cada produto
                for produto in produtos:
                    escritor.writerow([
                        produto.get('titulo', ''),
                        produto.get('artista', ''),
                        produto.get('album', ''),
                        produto.get('preco', ''),
                        produto.get('categoria', ''),
                        produto.get('url', ''),
                        produto.get('data_extracao', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    ])
            
            logger.info(f"Dados salvos com sucesso no arquivo {self.arquivo_saida}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar arquivo CSV: {e}")
            return False
    
    def simular_scroll_infinito(self) -> List[Dict[str, str]]:
        """
        Simula o scroll infinito para carregar e extrair todos os produtos
        
        Returns:
            Lista com todos os produtos extraídos
        """
        produtos_total = []
        scrolls_sem_produtos_novos = 0
        ultima_contagem = 0
        total_scrolls = 0
        
        try:
            # Navega para a página inicial
            self.driver.get(self.url_inicial)
            logger.info(f"Navegando para a URL inicial: {self.url_inicial}")
            
            # Aguarda o carregamento inicial da página
            time.sleep(3)
            
            # Aceita cookies se necessário
            try:
                botao_cookies = self.driver.find_element(By.CSS_SELECTOR, ".js-notification-cookie-accept, #accept-cookies, .accept-cookies")
                botao_cookies.click()
                logger.info("Botão de cookies clicado.")
                time.sleep(1)
            except NoSuchElementException:
                logger.info("Botão de cookies não encontrado.")
            
            # Extrai produtos iniciais
            produtos_pagina = self.extrair_produtos_pagina()
            produtos_total.extend(produtos_pagina)
            
            # Salva os produtos iniciais
            if produtos_pagina:
                self.salvar_para_csv(produtos_pagina, modo='w')
                self.todos_produtos.extend(produtos_pagina)
                ultima_contagem = len(produtos_total)
            
            # Continua rolando e extraindo enquanto houver novos produtos
            while total_scrolls < self.max_scrolls:
                # Faz o scroll para baixo
                mudou_altura = self.scroll_para_baixo()
                total_scrolls += 1
                
                logger.info(f"Scroll {total_scrolls}/{self.max_scrolls} executado")
                
                # Extrai produtos após o scroll
                produtos_pagina = self.extrair_produtos_pagina()
                
                if produtos_pagina:
                    # Adiciona apenas produtos novos (não duplicados)
                    produtos_novos = []
                    for produto in produtos_pagina:
                        # Verifica se o produto já existe na lista total
                        if not any(p['titulo'] == produto['titulo'] and p['url'] == produto['url'] for p in produtos_total):
                            produtos_novos.append(produto)
                    
                    # Se encontrou produtos novos, salva e adiciona à lista total
                    if produtos_novos:
                        produtos_total.extend(produtos_novos)
                        self.todos_produtos.extend(produtos_novos)
                        self.salvar_para_csv(produtos_novos, modo='a')
                        scrolls_sem_produtos_novos = 0
                        logger.info(f"Adicionados {len(produtos_novos)} novos produtos após scroll.")
                    else:
                        scrolls_sem_produtos_novos += 1
                        logger.info(f"Nenhum produto novo encontrado após scroll. Tentativa {scrolls_sem_produtos_novos}/3")
                else:
                    scrolls_sem_produtos_novos += 1
                    logger.info(f"Nenhum produto encontrado após scroll. Tentativa {scrolls_sem_produtos_novos}/3")
                
                # Se não encontrou novos produtos em 3 scrolls consecutivos e a altura não mudou
                # provavelmente não há mais produtos para carregar
                if scrolls_sem_produtos_novos >= 3 and not mudou_altura:
                    logger.info("Três scrolls consecutivos sem novos produtos e sem mudança na altura. Finalizando...")
                    break
                
                # Se não encontrou novos produtos em 5 scrolls consecutivos, mesmo que a altura continue mudando
                # isso pode indicar que estamos carregando outros elementos, mas não produtos
                if scrolls_sem_produtos_novos >= 5:
                    logger.info("Cinco scrolls consecutivos sem novos produtos. Finalizando...")
                    break
                
                # Aguarda um pouco para não sobrecarregar o servidor
                time.sleep(random.uniform(1.0, 2.0))
            
            logger.info(f"Processo de scroll finalizado. Total de {len(produtos_total)} produtos extraídos.")
            return produtos_total
            
        except Exception as e:
            logger.error(f"Erro durante a simulação de scroll infinito: {e}")
            return produtos_total
    
    def executar(self) -> None:
        """Executa o processo de extração completo"""
        logger.info(f"Iniciando extração de CDs do site Supernova Discos com Selenium...")
        
        try:
            # Inicia a contagem de tempo
            tempo_inicio = time.time()
            
            # Inicializa o driver
            self.inicializar_driver()
            
            # Extrai os produtos simulando scroll infinito
            produtos_novos = self.simular_scroll_infinito()
            
            # Exibe estatísticas finais
            tempo_total = time.time() - tempo_inicio
            logger.info(f"Extração concluída em {tempo_total:.2f} segundos.")
            logger.info(f"Total de {len(self.todos_produtos)} produtos na base.")
            logger.info(f"Foram adicionados {len(produtos_novos)} novos produtos nesta execução.")
            
        except Exception as e:
            logger.critical(f"Erro crítico durante a execução: {e}")
        finally:
            # Garante que o driver seja fechado mesmo em caso de erros
            self.fechar_driver()

def verificar_dependencias():
    """Verifica se todas as dependências estão instaladas"""
    dependencias = ['selenium', 'requests', 'bs4']
    faltando = []
    
    for dep in dependencias:
        try:
            __import__(dep)
        except ImportError:
            faltando.append(dep)
    
    if faltando:
        logger.critical(f"Dependências ausentes: {', '.join(faltando)}")
        logger.critical("Instale as dependências com: pip install " + " ".join(faltando))
        print(f"\nDependências ausentes: {', '.join(faltando)}")
        print("Instale as dependências com:")
        print(f"pip install {' '.join(faltando)}\n")
        return False
    
    return True

def main():
    """Função principal para executar o scraper"""
    # Verifica dependências antes de executar
    if not verificar_dependencias():
        return
    
    try:
        # Permite configurar via linha de comando ou usar valores padrão
        scraper = SupernovaDiscosSeleniumScraper(
            max_scrolls=30,     # Número máximo de scrolls
            scroll_wait=2.0,    # Tempo de espera após cada scroll
            headless=True       # Executa em modo invisível (sem navegador visível)
        )
        
        # Executa o scraper
        scraper.executar()
        
    except KeyboardInterrupt:
        logger.info("Processo interrompido pelo usuário.")
    except Exception as e:
        logger.critical(f"Erro crítico: {e}")

if __name__ == "__main__":
    main() 