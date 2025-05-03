#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Scraper para o site Pops Discos
Este script extrai informações de CDs do site https://www.popsdiscos.com.br/listagem_cd.asp
"""

import requests
from bs4 import BeautifulSoup
import csv
import time
import re
import os
import random
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any, Union
import json

# Cria as pastas para logs e debug se não existirem
os.makedirs('logs', exist_ok=True)
os.makedirs('debug', exist_ok=True)

# Configuração de logging
data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILENAME = f"logs/scraper_pops_discos_{data_hora}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILENAME),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PopsDiscosScraper:
    """Classe para extrair informações de CDs do site Pops Discos"""
    
    BASE_URL = "https://www.popsdiscos.com.br"
    DEFAULT_OUTPUT = "produtos_cd_pops_discos.csv"
    
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
        self.url_inicial = url_inicial or "https://www.popsdiscos.com.br/listagem_cd.asp"
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
            'Referer': 'https://www.popsdiscos.com.br/'
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
            
            # Salva a página para debug
            # Gera um nome seguro para o arquivo de debug
            url_safe = url.split('?')[0].split('/')[-1]
            if not url_safe:
                url_safe = 'index'
            debug_filename = f"debug/pops_discos_{url_safe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(debug_filename, "w", encoding="utf-8") as f:
                f.write(resposta.text)
            
            return BeautifulSoup(resposta.text, 'html.parser')
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição para {url}: {e}")
            return None
    
    def obter_categorias(self) -> List[Dict[str, str]]:
        """
        Obtém a lista de categorias de CDs do site
        
        Returns:
            Lista de dicionários com nome e URL de cada categoria
        """
        categorias = []
        soup = self._fazer_requisicao(self.url_inicial)
        
        if not soup:
            logger.error("Não foi possível obter a página inicial para extrair categorias")
            return categorias
        
        try:
            # Encontra links de categorias
            links_categorias = soup.find_all('a', href=lambda href: href and 'generomusical.asp?secao=' in href)
            
            for link in links_categorias:
                nome_categoria = link.get_text().strip()
                url_categoria = link['href']
                
                # Verifica se é uma URL relativa e adiciona o domínio base
                if not url_categoria.startswith('http'):
                    url_categoria = f"{self.BASE_URL}/{url_categoria}" if not url_categoria.startswith('/') else f"{self.BASE_URL}{url_categoria}"
                
                # Adiciona à lista de categorias
                if {'nome': nome_categoria, 'url': url_categoria} not in categorias:
                    categorias.append({
                        'nome': nome_categoria,
                        'url': url_categoria
                    })
                    logger.info(f"Categoria encontrada: {nome_categoria}")
            
            logger.info(f"Total de {len(categorias)} categorias encontradas")
            return categorias
        
        except Exception as e:
            logger.error(f"Erro ao extrair categorias: {e}")
            return []
    
    def extrair_produtos_pagina(self, url: str, nome_categoria: str) -> List[Dict[str, str]]:
        """
        Extrai todos os produtos com 'CD' no título de uma página de categoria
        
        Args:
            url: URL da página a ser processada
            nome_categoria: Nome da categoria atual
            
        Returns:
            Lista de dicionários contendo informações dos produtos
        """
        produtos = []
        soup = self._fazer_requisicao(url)
        
        if not soup:
            return produtos
        
        try:
            # Procura por produtos na página
            # O site da Pops Discos tem CDs listados em tabelas
            links_produtos = soup.find_all('a', href=lambda href: href and 'detalhe.asp?shw_ukey=' in href)
            
            for link in links_produtos:
                try:
                    # No site da Pops Discos, cada CD tem um link com um código único
                    url_produto = link['href']
                    if not url_produto.startswith('http'):
                        url_produto = f"{self.BASE_URL}/{url_produto}" if not url_produto.startswith('/') else f"{self.BASE_URL}{url_produto}"
                    
                    # Verifica se tem CD no texto do link
                    texto_link = link.get_text().strip()
                    
                    if 'CD' not in texto_link.upper():
                        continue
                    
                    # Extrai o título e informações do produto
                    # A estrutura pode ser "código (CD)" ou algo similar
                    codigo_cd = texto_link.split(' ')[0].strip() if texto_link else ""
                    
                    # Vamos acessar a página do produto para obter mais detalhes
                    detalhes = self._extrair_detalhes_produto(url_produto, codigo_cd)
                    
                    if not detalhes:
                        continue
                    
                    # Verifica se o produto já existe na lista
                    produto_existente = False
                    for produto in self.todos_produtos:
                        if produto.get('titulo') == detalhes.get('titulo') and produto.get('url') == url_produto:
                            produto_existente = True
                            break
                    
                    # Adiciona o produto se não for duplicado
                    if not produto_existente and not any(p['url'] == url_produto for p in produtos):
                        detalhes['categoria'] = nome_categoria
                        detalhes['url'] = url_produto
                        detalhes['data_extracao'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        produtos.append(detalhes)
                
                except Exception as e:
                    logger.warning(f"Erro ao processar um link de produto: {e}")
                    continue
            
            logger.info(f"Encontrados {len(produtos)} produtos com 'CD' nesta página.")
            return produtos
            
        except Exception as e:
            logger.error(f"Erro ao extrair produtos da página {url}: {e}")
            return []
    
    def _extrair_detalhes_produto(self, url_produto: str, codigo_cd: str) -> Optional[Dict[str, str]]:
        """
        Extrai detalhes de um produto acessando sua página específica
        
        Args:
            url_produto: URL da página do produto
            codigo_cd: Código do CD identificado na listagem
            
        Returns:
            Dicionário com os detalhes do produto ou None em caso de erro
        """
        try:
            soup = self._fazer_requisicao(url_produto)
            
            if not soup:
                return None
            
            # Inicializa variáveis
            titulo = ""
            artista = ""
            album = ""
            preco = ""
            
            # Nova implementação melhorada para extrair informações
            # 1. Extrair título do álbum e artista a partir da classe arial2pretoB e style4
            album_element = soup.find('div', class_='arial2pretoB')
            if album_element and album_element.find('strong'):
                album = album_element.find('strong').get_text().strip()
            
            artista_element = soup.find('div', class_='style4')
            if artista_element and artista_element.find('strong'):
                artista = artista_element.find('strong').get_text().strip()
            
            # 2. Extrair o código do CD
            if not codigo_cd:
                codigo_element = soup.find(text=re.compile(r'C.digo :'))
                if codigo_element and codigo_element.parent:
                    codigo_texto = codigo_element.parent.get_text()
                    codigo_match = re.search(r'C.digo :\s*([A-Z0-9]+-\d+)', codigo_texto)
                    if codigo_match:
                        codigo_cd = codigo_match.group(1).strip()
            
            # 3. Extrair o preço
            preco_element = soup.find(text=re.compile(r'R\$'))
            if preco_element:
                preco_texto = preco_element.strip()
                preco_match = re.search(r'R\$\s*(\d+[,.]\d+)', preco_texto)
                if preco_match:
                    preco = preco_match.group(0).strip()
            else:
                # Buscar por outros formatos de preço (por exemplo, só o valor)
                preco_element = soup.find('font', attrs={'color': '#CC3300'})
                if preco_element:
                    preco_texto = preco_element.get_text().strip()
                    if 'R$' in preco_texto:
                        preco_match = re.search(r'R\$\s*(\d+[,.]\d+)', preco_texto)
                        if preco_match:
                            preco = preco_match.group(0).strip()
            
            # 4. Se não conseguiu extrair o título do álbum, tenta pelo title da página
            if not album:
                titulo_pagina = soup.find('title')
                if titulo_pagina:
                    titulo_texto = titulo_pagina.get_text().strip()
                    # Remove "POPS DISCOS - " do início se existir
                    if "POPS DISCOS - " in titulo_texto:
                        titulo_texto = titulo_texto.replace("POPS DISCOS - ", "")
                    
                    # Separa artista e álbum se possível
                    parts = titulo_texto.split(" - ", 1)
                    if len(parts) > 1:
                        album = parts[0].strip()
                        artista = parts[1].strip()
                    else:
                        album = titulo_texto.strip()
            
            # 5. Se não tiver título completo, combina album e artista
            if artista and album:
                titulo = f"{album} - {artista}"
            elif album:
                titulo = album
            elif artista:
                titulo = artista
            else:
                # Último recurso: usar o código
                titulo = f"CD {codigo_cd}"
            
            # Registro de debug com mais detalhes
            logger.info(f"Produto extraído: {titulo} | Artista: {artista} | Álbum: {album} | Preço: {preco} | Código: {codigo_cd}")
            
            return {
                'titulo': titulo,
                'artista': artista,
                'album': album,
                'preco': preco,
                'codigo': codigo_cd
            }
            
        except Exception as e:
            logger.error(f"Erro ao extrair detalhes do produto {url_produto}: {e}")
            return None
    
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
            # Procura por links específicos de paginação
            links_paginacao = soup.find_all('a', href=lambda href: href and ('pagina=' in href or 'page=' in href or 'offset=' in href))
            
            # Procura por próxima página
            for link in links_paginacao:
                texto = link.get_text().strip()
                if texto.isdigit() and int(texto) == pagina_atual + 1:
                    return link['href']
                elif texto in ['Próximo', 'Próxima', 'Próx.', '>>', 'Next']:
                    return link['href']
            
            return None
        except Exception as e:
            logger.error(f"Erro ao procurar próxima página: {e}")
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
            campos = ['titulo', 'artista', 'album', 'preco', 'codigo', 'categoria', 'url', 'data_extracao']
            
            # Verifica se o arquivo já existe e se o modo é 'w'
            arquivo_existe = os.path.exists(self.arquivo_saida)
            
            # Escreve no arquivo CSV
            with open(self.arquivo_saida, modo, newline='', encoding='utf-8') as arquivo:
                escritor = csv.DictWriter(arquivo, fieldnames=campos, quoting=csv.QUOTE_ALL)
                
                # Escreve o cabeçalho apenas se estiver criando um novo arquivo
                if modo == 'w' or not arquivo_existe:
                    escritor.writeheader()
                
                # Escreve os dados de cada produto
                escritor.writerows(produtos)
            
            logger.info(f"Dados salvos com sucesso no arquivo {self.arquivo_saida}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar arquivo CSV: {e}")
            return False
    
    def executar(self) -> None:
        """Executa o processo de extração completo"""
        logger.info(f"Iniciando extração de CDs do site Pops Discos...")
        
        try:
            # Primeiro, obtém as categorias disponíveis
            categorias = self.obter_categorias()
            
            if not categorias:
                logger.error("Nenhuma categoria encontrada para processar")
                return
            
            total_produtos_novos = 0
            
            # Itera por cada categoria
            for categoria in categorias:
                nome_categoria = categoria['nome']
                url_categoria = categoria['url']
                
                logger.info(f"Processando categoria: {nome_categoria}")
                
                pagina_atual = 1
                url = url_categoria
                
                # Processa todas as páginas desta categoria
                while pagina_atual <= self.max_paginas and url:
                    logger.info(f"Processando página {pagina_atual} da categoria {nome_categoria} - URL: {url}")
                    
                    # Extrai produtos da página atual
                    produtos = self.extrair_produtos_pagina(url, nome_categoria)
                    
                    if produtos:
                        # Salva os produtos extraídos
                        modo = 'w' if pagina_atual == 1 and not self.todos_produtos else 'a'
                        
                        # Salva os produtos no CSV
                        self.salvar_para_csv(produtos, modo=modo)
                        
                        # Atualiza a lista de todos os produtos
                        self.todos_produtos.extend(produtos)
                        total_produtos_novos += len(produtos)
                    
                    # Pausa para não sobrecarregar o servidor
                    time.sleep(random.uniform(self.delay_min, self.delay_max))
                    
                    # Obtém a próxima página
                    soup = self._fazer_requisicao(url)
                    url_proxima = self.encontrar_proxima_pagina(soup, pagina_atual)
                    
                    if url_proxima:
                        if not url_proxima.startswith('http'):
                            url = f"{self.BASE_URL}{url_proxima}" if url_proxima.startswith('/') else f"{self.BASE_URL}/{url_proxima}"
                        else:
                            url = url_proxima
                        
                        pagina_atual += 1
                    else:
                        # Se não encontrou próxima página, encerra o loop
                        break
            
            logger.info(f"Extração concluída. {total_produtos_novos} novos produtos encontrados.")
            logger.info(f"Total de {len(self.todos_produtos)} produtos no arquivo {self.arquivo_saida}")
            
        except Exception as e:
            logger.error(f"Erro durante a execução do scraper: {e}")

def main():
    """Função principal para executar o scraper"""
    try:
        scraper = PopsDiscosScraper(
            max_paginas=50,  # Número máximo de páginas a processar
            delay_min=1.5,   # Atraso mínimo entre requisições
            delay_max=3.0    # Atraso máximo entre requisições
        )
        
        scraper.executar()
        
    except KeyboardInterrupt:
        logger.info("Processo interrompido pelo usuário.")
    except Exception as e:
        logger.error(f"Erro crítico: {e}")

if __name__ == "__main__":
    main() 