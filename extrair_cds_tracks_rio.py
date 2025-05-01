#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Scraper para o site Tracks Rio
Este script extrai informações de CDs do site http://www.tracksrio.com.br/
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
LOG_FILENAME = f"logs/scraper_tracks_rio_{data_hora}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILENAME),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('scraper_tracks_rio')

class TracksRioScraper:
    """Classe para extrair informações de CDs do site Tracks Rio"""
    
    BASE_URL = "https://tracksrio.com.br"
    DEFAULT_OUTPUT = "produtos_cd_tracks_rio.csv"
    
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
        self.url_inicial = url_inicial or "https://tracksrio.com.br/shop?order=create_date+desc&search=cd"
        self.max_paginas = max_paginas
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.arquivo_saida = arquivo_saida or self.DEFAULT_OUTPUT
        self.todos_produtos = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
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
        Extrai todos os produtos com 'CD' no título de uma página
        
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
            # Os produtos estão em células de tabela
            linhas_tabela = soup.find_all('tr')
            
            for linha in linhas_tabela:
                celulas = linha.find_all('td')
                
                for celula in celulas:
                    # Busca links que podem conter títulos de produtos
                    links = celula.find_all('a', href=True)
                    
                    for link in links:
                        titulo = link.text.strip()
                        # Verifica se o texto do link contém 'CD'
                        if 'CD' in titulo or 'cd' in titulo:
                            # Extrai a URL do produto
                            url_produto = f"{self.BASE_URL}{link['href']}" if link['href'].startswith('/') else link['href']
                            
                            # Extrai o preço (procura pelo formato R$ XX,XX)
                            preco_texto = None
                            preco_match = re.search(r'R\$\s*(\d+[,.]\d+)', celula.text)
                            if preco_match:
                                preco_texto = preco_match.group(0)
                            
                            # Adiciona o produto se tiver título e preço e não for duplicado
                            if titulo and preco_texto:
                                # Verifica se já existe na lista
                                produto_existente = False
                                for produto in self.todos_produtos:
                                    if produto.get('titulo') == titulo and produto.get('url') == url_produto:
                                        produto_existente = True
                                        break
                                
                                if not produto_existente and not any(p['titulo'] == titulo and p['url'] == url_produto for p in produtos):
                                    produtos.append({
                                        'titulo': titulo,
                                        'preco': preco_texto,
                                        'categoria': self.extrair_categoria(titulo),
                                        'url': url_produto,
                                        'data_extracao': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                    })
            
            logger.info(f"Encontrados {len(produtos)} produtos com 'CD' nesta página.")
            return produtos
            
        except Exception as e:
            logger.error(f"Erro ao extrair produtos da página {url}: {e}")
            return []
    
    @staticmethod
    def extrair_categoria(titulo: str) -> str:
        """
        Extrai a categoria do CD com base no título
        
        Args:
            titulo: Título do produto
            
        Returns:
            Nome da categoria
        """
        titulo_lower = titulo.lower()
        
        # Categorias com mapeamento mais detalhado
        categorias = [
            (["rock", "pop"], "Rock / Pop"),
            (["jazz"], "Jazz"),
            (["brasil", "mpb", "samba", "bossa", "choro"], "Música do Brasil"),
            (["world", "música do mundo"], "World Music"),
            (["black", "soul", "funk", "r&b", "hip hop", "rap"], "Black Music"),
            (["clássic", "erudito", "orquestra", "symphony"], "Eruditos"),
            (["blues"], "Blues"),
            (["reggae", "ska", "dub"], "Reggae"),
            (["eletrônic", "techno", "house", "trance"], "Eletrônica")
        ]
        
        for termos, categoria in categorias:
            if any(termo in titulo_lower for termo in termos):
                return categoria
        
        return "Outros Sons"
    
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
            # Primeiro, verifica se existe um link específico para "Próximo"
            links_paginacao = soup.find_all('a')
            for link in links_paginacao:
                if link.text.strip() == 'Próximo':
                    return link['href']
            
            # Se não encontrou, procura por links numéricos de paginação
            for link in links_paginacao:
                if link.text.strip().isdigit() and int(link.text.strip()) == pagina_atual + 1:
                    return link['href']
            
            # Procura por uma lista de paginação
            paginacao = soup.find_all('li')
            for item in paginacao:
                # Verifica se o texto deste item é "Próximo"
                if 'Próximo' in item.text:
                    link = item.find('a', href=True)
                    if link:
                        return link['href']
                
                # Ou verifica se é um número correspondente à próxima página
                if item.text.strip().isdigit() and int(item.text.strip()) == pagina_atual + 1:
                    link = item.find('a', href=True)
                    if link:
                        return link['href']
            
            # Construção manual da URL para a próxima página como último recurso
            return f"/shop/page/{pagina_atual + 1}?order=create_date+desc&search=cd"
            
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
            campos = ['titulo', 'preco', 'categoria', 'url', 'data_extracao']
            
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

    def executar(self) -> None:
        """Executa o processo de extração completo"""
        logger.info(f"Iniciando extração de produtos com 'CD' no título...")
        
        produtos_novos = []
        url_atual = self.url_inicial
        pagina_atual = 1
        produtos_pagina_anterior = -1  # Valor inicial diferente de 0 para iniciar o loop
        falhas_consecutivas = 0
        
        while url_atual and pagina_atual <= self.max_paginas:
            logger.info(f"Processando página {pagina_atual}: {url_atual}")
            
            try:
                # Obtém BeautifulSoup para a página atual
                soup = self._fazer_requisicao(url_atual)
                if not soup:
                    falhas_consecutivas += 1
                    if falhas_consecutivas >= 3:
                        logger.error("Três falhas consecutivas. Finalizando.")
                        break
                    continue
                
                # Extrai os produtos da página atual
                produtos_pagina = self.extrair_produtos_pagina(url_atual)
                
                # Adiciona os produtos à lista de novos produtos
                produtos_novos.extend(produtos_pagina)
                
                # Salva incrementalmente a cada página para evitar perda de dados
                if produtos_pagina:
                    self.salvar_para_csv(produtos_pagina, modo='a' if pagina_atual > 1 or self.todos_produtos else 'w')
                    self.todos_produtos.extend(produtos_pagina)
                
                # Verifica se a página atual tem o mesmo número de produtos da anterior
                # Isso pode indicar que estamos em um loop ou que não há mais páginas
                if len(produtos_pagina) == produtos_pagina_anterior and len(produtos_pagina) == 0:
                    logger.info("Duas páginas consecutivas sem produtos. Finalizando.")
                    break
                
                produtos_pagina_anterior = len(produtos_pagina)
                
                # Verifica se existem mais páginas
                proxima_pagina = self.encontrar_proxima_pagina(soup, pagina_atual)
                
                # Se não encontrou link para próxima página, termina
                if not proxima_pagina:
                    logger.info("Link para próxima página não encontrado. Finalizando.")
                    break
                
                # Atualiza a URL para a próxima página
                url_atual = f"{self.BASE_URL}{proxima_pagina}" if proxima_pagina.startswith('/') else proxima_pagina
                
                # Avança o contador de páginas
                pagina_atual += 1
                
                # Pausa para não sobrecarregar o servidor (delay aleatório)
                delay = random.uniform(self.delay_min, self.delay_max)
                logger.debug(f"Aguardando {delay:.2f} segundos antes da próxima requisição...")
                time.sleep(delay)
                
                # Reseta contador de falhas após sucesso
                falhas_consecutivas = 0
                
            except Exception as e:
                logger.error(f"Erro ao processar a página {pagina_atual}: {e}")
                falhas_consecutivas += 1
                if falhas_consecutivas >= 3:
                    logger.error("Três falhas consecutivas. Finalizando.")
                    break
                # Aguarda um pouco mais antes de tentar novamente
                time.sleep(random.uniform(self.delay_max, self.delay_max * 2))
        
        # Exibe estatísticas finais
        logger.info(f"Extração concluída. Total de {len(self.todos_produtos)} produtos na base.")
        logger.info(f"Foram adicionados {len(produtos_novos)} novos produtos nesta execução.")

def main():
    """Função principal para executar o scraper"""
    try:
        # Permite configurar via linha de comando ou usar valores padrão
        scraper = TracksRioScraper(
            max_paginas=100,  # Limite de segurança para evitar loops infinitos
            delay_min=1.5,    # Atraso mínimo entre requisições
            delay_max=3.5     # Atraso máximo entre requisições
        )
        
        # Executa o scraper
        scraper.executar()
        
    except KeyboardInterrupt:
        logger.info("Processo interrompido pelo usuário.")
    except Exception as e:
        logger.critical(f"Erro crítico: {e}")

if __name__ == "__main__":
    main() 