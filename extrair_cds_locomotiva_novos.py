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
LOG_FILENAME = f"logs/scraper_locomotiva_novos_{data_hora}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILENAME),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LocomotivaNovosDiscosScraper:
    """Classe para extrair informações de CDs novos do site Locomotiva Discos"""
    
    BASE_URL = "https://www.locomotivadiscos.com.br"
    DEFAULT_OUTPUT = "produtos_cd_locomotiva_novos.csv"
    
    def __init__(self, url_inicial: str = None, 
                 max_paginas: int = 100, 
                 delay_min: float = 1.0, 
                 delay_max: float = 3.0,
                 arquivo_saida: str = None,
                 ignorar_produtos_existentes: bool = False) -> None:
        """
        Inicializa o scraper com parâmetros configuráveis
        
        Args:
            url_inicial: URL para começar a extração (se None, usa a padrão)
            max_paginas: Número máximo de páginas a serem processadas
            delay_min: Atraso mínimo entre requisições (segundos)
            delay_max: Atraso máximo entre requisições (segundos)
            arquivo_saida: Nome do arquivo CSV de saída
            ignorar_produtos_existentes: Se True, recoleta todos os produtos mesmo que já existam
        """
        self.url_inicial = url_inicial or "https://www.locomotivadiscos.com.br/cds-novos-ct-3afa5"
        self.max_paginas = max_paginas
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.arquivo_saida = arquivo_saida or self.DEFAULT_OUTPUT
        self.ignorar_produtos_existentes = ignorar_produtos_existentes
        self.todos_produtos = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Referer': 'https://www.locomotivadiscos.com.br/',
            'Cache-Control': 'no-cache, no-store, must-revalidate'
        }
        
        # Verificar se já existe arquivo de produtos para continuar a partir dele
        if not self.ignorar_produtos_existentes:
            self._carregar_produtos_existentes()
        else:
            logger.info("Ignorando produtos existentes. Todos os produtos serão recoletados.")
    
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
            # Adiciona uma string aleatória à URL para evitar cache
            if '?' in url:
                url = f"{url}&_t={int(time.time())}"
            else:
                url = f"{url}?_t={int(time.time())}"
                
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
            # Procura por produtos na página
            elementos_produto = soup.find_all('div', class_=lambda c: c and ('product-box' in c or 'product-item' in c))
            
            for elemento in elementos_produto:
                try:
                    # Extrai o título do produto (geralmente é o texto 'CD' seguido do nome)
                    titulo_element = elemento.find('div', class_=lambda c: c and ('product-name' in c or 'title' in c)) or elemento.find('h3')
                    
                    if not titulo_element:
                        continue
                    
                    titulo = titulo_element.text.strip()
                    
                    # Verifica se o título começa com 'CD' (produtos são CDs)
                    if not titulo.upper().startswith('CD'):
                        continue
                    
                    # Extrai o preço
                    preco_element = elemento.find('div', class_=lambda c: c and ('product-price' in c or 'price' in c)) or elemento.find(string=re.compile(r'R\$'))
                    
                    if not preco_element:
                        continue
                    
                    # Se o elemento de preço for uma string, use-o diretamente
                    if isinstance(preco_element, str):
                        preco_texto = preco_element.strip()
                    else:
                        preco_texto = preco_element.text.strip()
                    
                    # Limpar o preço usando regex para garantir que temos apenas o valor formatado
                    preco_match = re.search(r'R\$\s*(\d+[,.]\d+)', preco_texto)
                    if preco_match:
                        preco_texto = preco_match.group(0)
                    else:
                        preco_texto = preco_texto.replace('\n', ' ').strip()
                    
                    # Extrai a URL do produto
                    url_produto = None
                    link_element = elemento.find('a', href=True)
                    if link_element and link_element.get('href'):
                        url_produto = link_element['href']
                        if not url_produto.startswith('http'):
                            # Garante que a URL comece com o BASE_URL e tenha uma barra após o domínio
                            if url_produto.startswith('/'):
                                url_produto = f"{self.BASE_URL}{url_produto}"
                            else:
                                url_produto = f"{self.BASE_URL}/{url_produto}"
                    
                    if not url_produto:
                        continue
                    
                    # Verifica se o produto já existe na lista (pula se estiver ignorando produtos existentes)
                    if not self.ignorar_produtos_existentes:
                        produto_existente = False
                        for produto in self.todos_produtos:
                            if produto.get('titulo') == titulo and produto.get('url') == url_produto:
                                produto_existente = True
                                break
                        
                        # Adiciona o produto se não for duplicado
                        if not produto_existente and not any(p['titulo'] == titulo and p['url'] == url_produto for p in produtos):
                            produtos.append({
                                'titulo': titulo,
                                'preco': preco_texto,
                                'categoria': self.extrair_categoria(titulo),
                                'url': url_produto,
                                'data_extracao': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                    else:
                        # Adiciona todos os produtos quando ignorar_produtos_existentes é True
                        if not any(p['titulo'] == titulo and p['url'] == url_produto for p in produtos):
                            produtos.append({
                                'titulo': titulo,
                                'preco': preco_texto,
                                'categoria': self.extrair_categoria(titulo),
                                'url': url_produto,
                                'data_extracao': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                except Exception as e:
                    logger.warning(f"Erro ao processar um elemento de produto: {e}")
                    continue
            
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
        
        # Categorias do site da Locomotiva Discos para CDs novos
        categorias = [
            (["rock", "pop", "guitar"], "Rock / Pop"),
            (["brasil", "mpb", "samba", "bossa", "choro", "nacional"], "Música Brasileira / Rock Nacional"),
            (["jazz"], "Jazz / Erudito"),
            (["blues"], "Jazz / Erudito"),
            (["soul", "funk", "r&b", "hip hop", "rap", "world", "reggae"], "Soul / Funk / Hip-Hop / World / Reggae"),
            (["punk", "hardcore"], "Punk / Hardcore"),
            (["metal", "heavy", "thrash", "death"], "Metal"),
            (["world", "música do mundo", "latin"], "Soul / Funk / Hip-Hop / World / Reggae"),
            (["reggae", "ska", "dub"], "Soul / Funk / Hip-Hop / World / Reggae"),
            (["eletrônic", "techno", "house", "trance", "dance", "experimental"], "Eletrônico / Experimental"),
            (["indie", "shoegaze"], "Indiepop / Shoegaze"),
            (["clássic", "erudito", "orquestra", "symphony"], "Jazz / Erudito")
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
            # Procura por links de paginação
            # Primeiro, procura por um link "Próxima"
            proxima_links = soup.find_all('a', string=lambda s: s and 'Próxima' in s)
            
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
            
            # Se ainda não encontrou, tenta através da URL parametrizada
            # Na Locomotiva Discos, parece que a URL segue um padrão como:
            # cds-novos-ct-3afa5?pageNum=X&sortBy=Y
            return f"cds-novos-ct-3afa5?pageNum={pagina_atual + 1}&sortBy=1"
            
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
        logger.info(f"Iniciando extração de produtos com 'CD' do site Locomotiva Discos (CDs NOVOS)...")
        
        produtos_novos = []
        url_atual = self.url_inicial
        pagina_atual = 1
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
                    
                    # Aguarda um pouco mais antes de tentar novamente
                    time.sleep(random.uniform(self.delay_max, self.delay_max * 2))
                    continue
                
                # Extrai os produtos da página atual
                produtos_pagina = self.extrair_produtos_pagina(url_atual)
                
                # Adiciona os produtos à lista de novos produtos
                produtos_novos.extend(produtos_pagina)
                
                # Salva incrementalmente a cada página para evitar perda de dados
                if produtos_pagina:
                    self.salvar_para_csv(produtos_pagina, modo='a' if pagina_atual > 1 or self.todos_produtos else 'w')
                    self.todos_produtos.extend(produtos_pagina)
                
                # Se não encontrou produtos por duas páginas seguidas, pode indicar o fim
                if not produtos_pagina and pagina_atual > 1:
                    logger.info("Página sem produtos. Verificando mais uma página antes de finalizar.")
                    
                    # Se for a segunda página consecutiva sem produtos, finaliza
                    if falhas_consecutivas > 0:
                        logger.info("Duas páginas consecutivas sem produtos. Finalizando.")
                        break
                    
                    falhas_consecutivas += 1
                else:
                    falhas_consecutivas = 0
                
                # Verifica se existem mais páginas
                proxima_pagina = self.encontrar_proxima_pagina(soup, pagina_atual)
                
                # Se não encontrou link para próxima página, termina
                if not proxima_pagina:
                    logger.info("Link para próxima página não encontrado. Finalizando.")
                    break
                
                # Atualiza a URL para a próxima página
                if not proxima_pagina.startswith('http'):
                    # Garante que a URL comece com o BASE_URL e tenha uma barra após o domínio
                    if proxima_pagina.startswith('/'):
                        url_atual = f"{self.BASE_URL}{proxima_pagina}"
                    else:
                        url_atual = f"{self.BASE_URL}/{proxima_pagina}"
                else:
                    # Verifica se a URL já tem http:// mas precisa de uma barra após o domínio
                    if 'locomotivadiscos.com.br' in proxima_pagina and not 'locomotivadiscos.com.br/' in proxima_pagina:
                        url_atual = proxima_pagina.replace('locomotivadiscos.com.br', 'locomotivadiscos.com.br/')
                    else:
                        url_atual = proxima_pagina
                
                # Avança o contador de páginas
                pagina_atual += 1
                
                # Pausa para não sobrecarregar o servidor (delay aleatório)
                delay = random.uniform(self.delay_min, self.delay_max)
                logger.debug(f"Aguardando {delay:.2f} segundos antes da próxima requisição...")
                time.sleep(delay)
                
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
        scraper = LocomotivaNovosDiscosScraper(
            max_paginas=340,  # O site indica ter muitas páginas
            delay_min=2.0,    # Atraso mínimo entre requisições
            delay_max=4.0,    # Atraso máximo entre requisições
            ignorar_produtos_existentes=True  # Força a recoleta de todos os produtos
        )
        
        # Executa o scraper
        scraper.executar()
        
    except KeyboardInterrupt:
        logger.info("Processo interrompido pelo usuário.")
    except Exception as e:
        logger.critical(f"Erro crítico: {e}")

if __name__ == "__main__":
    main() 