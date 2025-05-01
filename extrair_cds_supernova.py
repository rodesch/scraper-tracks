#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Scraper para o site Supernova Discos
Este script extrai informações de CDs do site https://www.supernovadiscos.com.br/
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
from urllib.parse import urljoin
import re

# Cria as pastas para logs e debug se não existirem
os.makedirs('logs', exist_ok=True)
os.makedirs('debug', exist_ok=True)

# Verificar se existe uma variável de ambiente para o diretório de debug
DEBUG_DIR = os.environ.get('DEBUG_DIR', 'debug')

# Configuração do logger
data_hora = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILENAME = f"logs/scraper_supernova_{data_hora}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILENAME),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('scraper_supernova')

class SupernovaDiscosScraper:
    """Classe para extrair informações de CDs do site Supernova Discos"""
    
    BASE_URL = "https://www.supernovadiscos.com.br"
    DEFAULT_OUTPUT = "produtos_cd_supernova.csv"
    
    def __init__(self, url_inicial: str = None, 
                 max_paginas: int = 100, 
                 delay_min: float = 1.0, 
                 delay_max: float = 3.0,
                 arquivo_saida: str = None) -> None:
        """
        Inicializa o scraper com parâmetros configuráveis
        
        Args:
            url_inicial: URL para começar a extração (se None, usa a padrão)
            max_paginas: Número máximo de páginas a serem processadas
            delay_min: Atraso mínimo entre requisições (segundos)
            delay_max: Atraso máximo entre requisições (segundos)
            arquivo_saida: Nome do arquivo CSV de saída
        """
        self.url_inicial = url_inicial or "https://www.supernovadiscos.com.br/discos/cds/?sort_by=created-descending"
        self.max_paginas = max_paginas
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.arquivo_saida = arquivo_saida or self.DEFAULT_OUTPUT
        self.todos_produtos = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Referer': 'https://www.supernovadiscos.com.br/'
        }
        
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
    
    def _fazer_requisicao(self, url: str) -> Optional[BeautifulSoup]:
        """
        Faz uma requisição HTTP e retorna o objeto BeautifulSoup
        
        Args:
            url: URL para acessar
            
        Returns:
            BeautifulSoup object ou None em caso de erro
        """
        try:
            resposta = requests.get(url, headers=self.headers, timeout=30)
            resposta.raise_for_status()
            return BeautifulSoup(resposta.text, 'html.parser')
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição para {url}: {e}")
            return None
    
    def extrair_produtos_pagina(self, url: str) -> List[Dict[str, str]]:
        """
        Extrai todos os produtos da seção de CDs da página
        
        Args:
            url: URL da página a ser processada
            
        Returns:
            Lista de dicionários contendo informações dos produtos
        """
        produtos = []
        soup = self._fazer_requisicao(url)
        
        if not soup:
            return produtos
        
        try:
            # Debug - salvar HTML para análise
            # with open(f"debug_page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html", "w", encoding="utf-8") as f:
            #     f.write(str(soup))
            
            # Na Supernova Discos, os produtos estão em elementos com classe "js-item-product" ou "item product"
            elementos_produto = soup.select('.js-item-product, .item.product')
            
            # Se não encontrou com o seletor acima, tenta outras abordagens
            if not elementos_produto:
                # Tenta encontrar qualquer elemento que contenha "product" na classe
                elementos_produto = soup.find_all(class_=lambda c: c and 'product' in c)
            
            # Tenta encontrar todos os itens dentro da seção principal de produtos
            if not elementos_produto:
                main_section = soup.select_one('#main-categories-content, .grid-row, .js-product-table')
                if main_section:
                    elementos_produto = main_section.find_all('div')
            
            logger.info(f"Encontrados {len(elementos_produto)} elementos de produto no HTML.")
            
            for elemento in elementos_produto:
                try:
                    # Extrai o título do produto
                    titulo_element = elemento.select_one('h3, h2, .title, .name')
                    
                    if not titulo_element:
                        # Tenta encontrar o título em links
                        link_com_titulo = elemento.select_one('a[title]')
                        if link_com_titulo:
                            titulo = link_com_titulo.get('title', '').strip()
                        else:
                            # Tenta extrair de atributos alt de imagens
                            img = elemento.select_one('img[alt]')
                            if img:
                                titulo = img.get('alt', '').strip()
                            else:
                                continue
                    else:
                        titulo = titulo_element.text.strip()
                    
                    # Verifica se o título não está vazio
                    if not titulo:
                        continue
                    
                    # Extrai o preço 
                    # No site da Supernova, os preços geralmente aparecem no formato "R$ 88,00"
                    preco_element = elemento.select_one('.price, .product-price, .js-price-display')
                    
                    if not preco_element:
                        # Tenta encontrar qualquer texto que corresponda ao padrão R$ XX,XX
                        preco_text = elemento.find(string=re.compile(r'R\$\s*\d+[,.]\d+'))
                        if preco_text:
                            preco_texto = preco_text.strip()
                        else:
                            continue
                    else:
                        preco_texto = preco_element.text.strip()
                    
                    # Limpa o preço usando regex
                    preco_match = re.search(r'R\$\s*(\d+[,.]\d+)', preco_texto)
                    if preco_match:
                        preco_texto = preco_match.group(0)
                    else:
                        # Se não conseguir extrair com regex, usa o texto inteiro
                        preco_texto = preco_texto.replace('\n', ' ').strip()
                    
                    # Extrai a URL do produto
                    url_produto = None
                    # Verifica se o próprio elemento é um link
                    if elemento.name == 'a' and elemento.has_attr('href'):
                        url_produto = elemento['href']
                    else:
                        # Procura por um link dentro do elemento
                        link_element = elemento.select_one('a[href]')
                        if link_element:
                            url_produto = link_element['href']
                    
                    if not url_produto:
                        continue
                    
                    # Garante que a URL seja absoluta
                    if not url_produto.startswith('http'):
                        url_produto = f"{self.BASE_URL}{url_produto}" if url_produto.startswith('/') else f"{self.BASE_URL}/{url_produto}"
                    
                    # Extrai informações sobre banda/artista e álbum do título
                    # Formato comum: "Banda - Álbum (Importado)"
                    artista = ""
                    album = ""
                    if " - " in titulo:
                        partes = titulo.split(" - ", 1)
                        artista = partes[0].strip()
                        album = partes[1].strip()
                    else:
                        album = titulo
                    
                    # Extrai a categoria (se disponível)
                    categoria = self.extrair_categoria(titulo, url_produto)
                    
                    # Verifica se o produto já existe na lista
                    produto_existente = False
                    for produto in self.todos_produtos:
                        if produto.get('titulo') == titulo and produto.get('url') == url_produto:
                            produto_existente = True
                            break
                    
                    # Adiciona o produto se não for duplicado
                    if not produto_existente and not any(p['titulo'] == titulo and p['url'] == url_produto for p in produtos):
                        produtos.append({
                            'titulo': titulo,
                            'artista': artista,
                            'album': album,
                            'preco': preco_texto,
                            'categoria': categoria,
                            'url': url_produto,
                            'data_extracao': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                except Exception as e:
                    logger.warning(f"Erro ao processar um elemento de produto: {e}")
                    continue
            
            logger.info(f"Extraídos {len(produtos)} produtos nesta página.")
            return produtos
            
        except Exception as e:
            logger.error(f"Erro ao extrair produtos da página {url}: {e}")
            return []
    
    def extrair_categoria(self, titulo: str, url_produto: str) -> str:
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
    
    def encontrar_proxima_pagina(self, soup: BeautifulSoup, pagina_atual: int) -> Optional[str]:
        """
        Identifica o link para a próxima página
        
        Args:
            soup: Objeto BeautifulSoup da página atual
            pagina_atual: Número da página atual
            
        Returns:
            URL da próxima página ou None se não encontrada
        """
        if not soup:
            return None
            
        try:
            # Procura por links de paginação típicos
            proxima_links = soup.find_all('a', string=lambda s: s and ('Próximo' in s or 'Próxima' in s or '»' in s))
            
            for link in proxima_links:
                if link.has_attr('href'):
                    return link['href']
            
            # Se não encontrar, procura por links numéricos de paginação
            pagina_links = soup.find_all('a')
            for link in pagina_links:
                # Tenta encontrar um link com o número da próxima página
                try:
                    if link.text.strip().isdigit() and int(link.text.strip()) == pagina_atual + 1:
                        return link['href']
                except:
                    continue
            
            # No site da Supernova Discos com scroll infinito, a paginação é feita através
            # do parâmetro mpage= na URL. Vamos construir a próxima página assim:
            return f"/discos/cds/?sort_by=created-descending&mpage={pagina_atual + 1}"
            
        except Exception as e:
            logger.error(f"Erro ao buscar próxima página: {e}")
            return None
    
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
                        produto.get('data_extracao', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    ])
            
            logger.info(f"Dados salvos com sucesso no arquivo {self.arquivo_saida}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar arquivo CSV: {e}")
            return False

    def extrair_produtos_com_paginacao(self) -> List[Dict[str, str]]:
        """
        Extrai produtos de múltiplas páginas simulando o comportamento de scroll infinito
        através de requisições paginadas
        
        Returns:
            Lista com todos os produtos extraídos
        """
        produtos_total = []
        pagina_atual = 1
        falhas_consecutivas = 0
        produtos_vazios_consecutivos = 0
        
        while pagina_atual <= self.max_paginas:
            # Constrói a URL da página atual usando o parâmetro mpage
            url = f"{self.BASE_URL}/discos/cds/?sort_by=created-descending&mpage={pagina_atual}"
            
            logger.info(f"Processando página {pagina_atual}: {url}")
            
            try:
                # Faz a requisição e extrai os produtos
                soup = self._fazer_requisicao(url)
                if not soup:
                    falhas_consecutivas += 1
                    if falhas_consecutivas >= 3:
                        logger.error("Três falhas consecutivas. Finalizando.")
                        break
                    
                    # Aguarda um pouco mais antes de tentar novamente
                    time.sleep(random.uniform(self.delay_max, self.delay_max * 2))
                    continue
                
                # Extrai os produtos da página atual
                produtos_pagina = self.extrair_produtos_pagina(url)
                
                # Verifica se encontrou produtos na página
                if not produtos_pagina:
                    produtos_vazios_consecutivos += 1
                    logger.warning(f"Nenhum produto encontrado na página {pagina_atual}. Tentativa {produtos_vazios_consecutivos} de 3.")
                    
                    # Se não encontrou produtos por três páginas seguidas, finaliza
                    if produtos_vazios_consecutivos >= 3:
                        logger.info("Três páginas consecutivas sem produtos. Finalizando.")
                        break
                else:
                    produtos_vazios_consecutivos = 0
                    
                    # Adiciona os produtos à lista
                    produtos_total.extend(produtos_pagina)
                    
                    # Salva incrementalmente
                    self.salvar_para_csv(produtos_pagina, 
                                        modo='a' if pagina_atual > 1 or self.todos_produtos else 'w')
                    
                    # Adiciona à lista de todos os produtos
                    self.todos_produtos.extend(produtos_pagina)
                
                # Avança para a próxima página
                pagina_atual += 1
                
                # Pausa para não sobrecarregar o servidor
                delay = random.uniform(self.delay_min, self.delay_max)
                logger.info(f"Aguardando {delay:.2f} segundos antes da próxima requisição...")
                time.sleep(delay)
                
                # Reseta contador de falhas
                falhas_consecutivas = 0
                
            except Exception as e:
                logger.error(f"Erro ao processar a página {pagina_atual}: {e}")
                falhas_consecutivas += 1
                if falhas_consecutivas >= 3:
                    logger.error("Três falhas consecutivas. Finalizando.")
                    break
                
                # Aguarda um pouco mais antes de tentar novamente
                time.sleep(random.uniform(self.delay_max, self.delay_max * 2))
        
        return produtos_total

    def executar(self) -> None:
        """Executa o processo de extração completo"""
        logger.info(f"Iniciando extração de CDs do site Supernova Discos...")
        
        # Inicia a contagem de tempo
        tempo_inicio = time.time()
        
        # Extrai os produtos com paginação para simular scroll infinito
        produtos_novos = self.extrair_produtos_com_paginacao()
        
        # Exibe estatísticas finais
        tempo_total = time.time() - tempo_inicio
        logger.info(f"Extração concluída em {tempo_total:.2f} segundos.")
        logger.info(f"Total de {len(self.todos_produtos)} produtos na base.")
        logger.info(f"Foram adicionados {len(produtos_novos)} novos produtos nesta execução.")

def main():
    """Função principal para executar o scraper"""
    try:
        # Permite configurar via linha de comando ou usar valores padrão
        scraper = SupernovaDiscosScraper(
            max_paginas=50,    # Limite máximo de páginas a verificar para scroll infinito
            delay_min=2.0,     # Atraso mínimo entre requisições
            delay_max=5.0      # Atraso máximo entre requisições
        )
        
        # Executa o scraper
        scraper.executar()
        
    except KeyboardInterrupt:
        logger.info("Processo interrompido pelo usuário.")
    except Exception as e:
        logger.critical(f"Erro crítico: {e}")

if __name__ == "__main__":
    main() 