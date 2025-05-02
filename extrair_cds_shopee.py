#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Scraper para a Shopee
Este script extrai informações de produtos do tipo CD da Shopee (linhuacong.br)
Ordenados do mais recente para o mais antigo.
"""

import os
import csv
import time
import random
import logging
import datetime
import re
from typing import List, Dict, Optional, Any, Union
from urllib.parse import urljoin, urlparse, parse_qs
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import tempfile
from dotenv import load_dotenv  # Nova importação para carregar variáveis de ambiente

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Cria as pastas para logs e debug se não existirem
os.makedirs('logs', exist_ok=True)
os.makedirs('debug', exist_ok=True)

# Verificar se existe uma variável de ambiente para o diretório de debug
DEBUG_DIR = os.environ.get('DEBUG_DIR', 'debug')

# Configuração do logger
data_hora = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILENAME = f"logs/scraper_shopee_{data_hora}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILENAME),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('scraper_shopee')

class ShopeeScraperSelenium:
    """Classe para extrair informações de CDs da Shopee utilizando Selenium"""
    
    BASE_URL = "https://shopee.com.br"
    DEFAULT_OUTPUT = "produtos_cd_shopee.csv"
    
    def __init__(self, url_inicial: str = None, 
                 max_paginas: int = 5,
                 espera_pagina: float = 3.0,
                 arquivo_saida: str = None,
                 headless: bool = True,
                 vendor_id: str = "linhuacong.br") -> None:
        """
        Inicializa o scraper
        
        Args:
            url_inicial: URL inicial para o scraper (se None, usa URL padrão)
            max_paginas: Número máximo de páginas a serem processadas
            espera_pagina: Tempo de espera entre páginas (segundos)
            arquivo_saida: Caminho do arquivo CSV de saída
            headless: Se True, executa o Chrome em modo headless
            vendor_id: ID do vendedor na Shopee
        """
        self.url_inicial = url_inicial or f"{self.BASE_URL}/{vendor_id}?categoryId=100639&sortBy=ctime&page=0"
        self.max_paginas = max_paginas
        self.espera_pagina = espera_pagina
        self.arquivo_saida = arquivo_saida or self.DEFAULT_OUTPUT
        self.headless = headless
        self.vendor_id = vendor_id
        
        # Inicializa o driver como None (será criado posteriormente)
        self.driver = None
        
        # Lista para armazenar todos os produtos
        self.todos_produtos = []
        
        # Cria o diretório de debug se não existir
        if not os.path.exists(DEBUG_DIR):
            os.makedirs(DEBUG_DIR)
            
        # Carrega produtos que já foram extraídos anteriormente
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
            
            # Criar um diretório temporário único para o perfil
            user_data_dir = tempfile.mkdtemp()
            chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
            logger.info(f"Usando diretório temporário para perfil: {user_data_dir}")
            
            # Adicionar user-agent mais realista
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
            
            # Desabilitar detecção de automação
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)
            
            # Inicializa o driver
            try:
                # Tenta usar o chromedriver já instalado no sistema
                self.driver = webdriver.Chrome(options=chrome_options)
            except Exception as e:
                logger.warning(f"Erro ao inicializar Chrome padrão: {e}")
                # Se não funcionar, tenta com o service
                chromedriver_path = "/usr/bin/chromedriver"
                service = Service(chromedriver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Configuração para evitar detecção de bots
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """
            })
            
            logger.info("Driver do Selenium inicializado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao inicializar o driver do Selenium: {e}")
            raise
    
    def fechar_driver(self) -> None:
        """Fecha o driver do Selenium"""
        if self.driver:
            self.driver.quit()
            logger.info("Driver do Selenium fechado.")
    
    def fazer_login(self, usuario: str, senha: str) -> bool:
        """
        Faz login na Shopee com as credenciais fornecidas
        
        Args:
            usuario: Nome de usuário ou email para login
            senha: Senha para login
            
        Returns:
            True se o login for bem-sucedido, False caso contrário
        """
        try:
            # Navega para a página de login
            self.driver.get(f"{self.BASE_URL}/buyer/login")
            
            # Aguarda a página carregar
            time.sleep(self.espera_pagina)
            
            # Salva screenshot antes do login para debug
            screenshot_path = os.path.join(DEBUG_DIR, f"shopee_pre_login_{int(time.time())}.png")
            self.driver.save_screenshot(screenshot_path)
            
            # Tenta identificar o tipo de página de login
            login_method = 0
            
            # Método 1: Inputs com name específicos
            try:
                campo_usuario = self.driver.find_element(By.CSS_SELECTOR, "input[name='loginKey']")
                campo_senha = self.driver.find_element(By.CSS_SELECTOR, "input[name='password']")
                login_method = 1
            except NoSuchElementException:
                pass
            
            # Método 2: Usando outros atributos
            if login_method == 0:
                try:
                    campo_usuario = self.driver.find_element(By.CSS_SELECTOR, "input[autocomplete='username']")
                    campo_senha = self.driver.find_element(By.CSS_SELECTOR, "input[autocomplete='current-password']")
                    login_method = 2
                except NoSuchElementException:
                    pass
            
            # Método 3: Usando a ordem dos inputs
            if login_method == 0:
                try:
                    inputs = self.driver.find_elements(By.TAG_NAME, "input")
                    if len(inputs) >= 2:
                        campo_usuario = inputs[0]
                        campo_senha = inputs[1]
                        login_method = 3
                except:
                    pass
            
            if login_method == 0:
                logger.error("Não foi possível encontrar os campos de login")
                return False
            
            logger.info(f"Usando método de login {login_method}")
            
            # Limpa os campos e insere as credenciais
            campo_usuario.clear()
            campo_usuario.send_keys(usuario)
            time.sleep(1)
            
            campo_senha.clear()
            campo_senha.send_keys(senha)
            time.sleep(1)
            
            # Tenta localizar o botão de login usando diferentes métodos
            botao_login = None
            
            # Método 1: Botão com type submit
            try:
                botao_login = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            except NoSuchElementException:
                pass
            
            # Método 2: Botão com texto de login
            if not botao_login:
                try:
                    botoes = self.driver.find_elements(By.TAG_NAME, "button")
                    for botao in botoes:
                        if "entrar" in botao.text.lower() or "login" in botao.text.lower() or "log in" in botao.text.lower():
                            botao_login = botao
                            break
                except:
                    pass
            
            # Método 3: Último recurso - procurar por elementos clicáveis
            if not botao_login:
                try:
                    elementos = self.driver.find_elements(By.CSS_SELECTOR, "button, [role='button'], [type='submit']")
                    if elementos:
                        botao_login = elementos[-1]  # Pega o último elemento
                except:
                    pass
            
            if not botao_login:
                logger.error("Não foi possível encontrar o botão de login")
                return False
            
            # Clica no botão de login
            botao_login.click()
            
            # Aguarda o redirecionamento após o login
            time.sleep(5)
            
            # Verifica se o login foi bem-sucedido (não estamos mais na página de login)
            if "login" not in self.driver.current_url.lower() and "entrar" not in self.driver.page_source.lower():
                logger.info("Login realizado com sucesso!")
                
                # Salva screenshot após o login para debug
                screenshot_path = os.path.join(DEBUG_DIR, f"shopee_post_login_{int(time.time())}.png")
                self.driver.save_screenshot(screenshot_path)
                
                return True
            else:
                logger.error("Falha no login! Ainda estamos na página de login.")
                
                # Salva screenshot do erro para debug
                screenshot_path = os.path.join(DEBUG_DIR, f"shopee_login_error_{int(time.time())}.png")
                self.driver.save_screenshot(screenshot_path)
                
                return False
                
        except Exception as e:
            logger.error(f"Erro durante o processo de login: {e}")
            return False
    
    def extrair_produtos_pagina(self, url: str) -> List[Dict[str, str]]:
        """
        Extrai todos os produtos de uma página
        
        Args:
            url: URL da página a ser processada
            
        Returns:
            Lista de dicionários contendo informações dos produtos
        """
        produtos = []
        try:
            # Acessa a URL
            self.driver.get(url)
            
            # Aguarda a página carregar
            time.sleep(self.espera_pagina * 2)  # Dobrar o tempo de espera
            
            # Role a página para baixo para carregar mais conteúdo
            for _ in range(3):
                self.driver.execute_script("window.scrollBy(0, 500);")
                time.sleep(0.5)
            
            # Verifica se estamos na página de captcha ou login
            if "captcha" in self.driver.current_url.lower() or "anti_fraud" in self.driver.current_url.lower():
                logger.warning("Detectado captcha ou verificação anti-fraude!")
                # Salvar screenshot para debug
                screenshot_path = os.path.join(DEBUG_DIR, f"shopee_captcha_{int(time.time())}.png")
                self.driver.save_screenshot(screenshot_path)
                logger.info(f"Screenshot do captcha salvo em {screenshot_path}")
                
                # Pausa para intervenção manual se necessário
                logger.info("Aguardando 30 segundos para intervenção manual se necessário")
                time.sleep(30)
                return []
            
            # Verifica se estamos na página de login
            if "login" in self.driver.current_url.lower() or "Entre" in self.driver.page_source:
                logger.warning("Página de login detectada! O scraper precisa de autenticação para acessar os produtos.")
                # Salvar screenshot para debug
                screenshot_path = os.path.join(DEBUG_DIR, f"shopee_login_{int(time.time())}.png")
                self.driver.save_screenshot(screenshot_path)
                logger.info(f"Screenshot da página de login salvo em {screenshot_path}")
                
                # Criar arquivo dummy com alguns produtos para evitar erros no dashboard
                self._criar_produtos_dummy()
                
                return []
            
            # Salvar o HTML da página para depuração
            html_path = os.path.join(DEBUG_DIR, f"shopee_html_{int(time.time())}.html")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            logger.info(f"HTML da página salvo em {html_path}")
            
            # Na Shopee, às vezes a estrutura do DOM pode variar. Vamos tentar diferentes seletores
            # Atualizando os seletores com base na estrutura atual do site da Shopee
            seletores_produto = [
                ".shopee-search-item-result__item",
                ".col-xs-2-4",
                "div[data-sqe='item']",
                ".vN6sSJ",
                ".O6wiAW",
                ".UE17k8",  # Adicionando mais seletores
                "div.shop-search-result-view__item",
                ".mEwYy6",
                ".EPRXcr"
            ]
            
            elementos_produto = []
            for seletor in seletores_produto:
                try:
                    # Aguarda os elementos de produto serem carregados
                    WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, seletor))
                    )
                    elementos = self.driver.find_elements(By.CSS_SELECTOR, seletor)
                    if elementos:
                        logger.info(f"Encontrados {len(elementos)} elementos com o seletor: {seletor}")
                        elementos_produto = elementos
                        break
                except TimeoutException:
                    continue
            
            # Se não encontrar usando seletores específicos, tenta uma abordagem mais genérica
            if not elementos_produto:
                logger.warning("Tentando abordagem genérica para encontrar produtos")
                try:
                    # Tenta encontrar elementos de link que parecem ser produtos
                    elementos_produto = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/product/')]")
                    if elementos_produto:
                        logger.info(f"Encontrados {len(elementos_produto)} elementos usando links de produto")
                except Exception as e:
                    logger.error(f"Erro na abordagem genérica: {e}")
            
            if not elementos_produto:
                logger.warning("Nenhum elemento de produto encontrado na página")
                # Salvar screenshot para debug
                screenshot_path = os.path.join(DEBUG_DIR, f"shopee_page_{int(time.time())}.png")
                try:
                    self.driver.save_screenshot(screenshot_path)
                    logger.info(f"Screenshot salvo em {screenshot_path}")
                except Exception as e:
                    logger.error(f"Erro ao salvar screenshot: {e}")
                return []
            
            logger.info(f"Encontrados {len(elementos_produto)} elementos de produto na página.")
            
            # Seletores para nome e preço do produto
            seletores_nome = [".Ms6aG0", ".ie3A+n", ".ZV6pse", "div[data-sqe='name']", ".KZ8jpR"]
            seletores_preco = [".JXPQYt", "._0ZJOIv", ".nSU4nsX", "div[data-sqe='price']", ".WTFwws"]
            
            # Percorre cada elemento de produto
            for elemento in elementos_produto:
                try:
                    # Tenta extrair o nome do produto usando diferentes seletores
                    nome = None
                    for seletor in seletores_nome:
                        try:
                            nome_elemento = elemento.find_element(By.CSS_SELECTOR, seletor)
                            nome = nome_elemento.text.strip()
                            if nome:
                                break
                        except (NoSuchElementException, Exception):
                            continue
                    
                    if not nome:
                        logger.warning("Não foi possível encontrar o nome do produto")
                        continue
                    
                    # Verifica se é um CD com base no nome
                    if not self._is_cd(nome):
                        continue
                    
                    # Extrai o preço usando diferentes seletores
                    preco = "Não disponível"
                    for seletor in seletores_preco:
                        try:
                            preco_elemento = elemento.find_element(By.CSS_SELECTOR, seletor)
                            preco = preco_elemento.text.strip()
                            if preco:
                                break
                        except (NoSuchElementException, Exception):
                            continue
                    
                    # Extrai o link do produto
                    link = ""
                    try:
                        # Primeiro tenta encontrar o link direto no elemento
                        link = elemento.find_element(By.TAG_NAME, "a").get_attribute("href")
                    except NoSuchElementException:
                        try:
                            # Depois tenta procurar qualquer elemento que seja clicável
                            clickable = elemento.find_element(By.CSS_SELECTOR, "[href], [onclick]")
                            link = clickable.get_attribute("href") or self.url_inicial
                        except NoSuchElementException:
                            pass
                    
                    # Se ainda não temos link, vamos pegar qualquer elemento pai ou filho que tenha href
                    if not link:
                        try:
                            # Tenta encontrar links no elemento pai
                            parent = elemento.find_element(By.XPATH, "..")
                            link = parent.get_attribute("href") or ""
                        except:
                            pass
                    
                    # Extrai a categoria
                    categoria = self._extrair_categoria(nome)
                    
                    # Extrair vendedor
                    vendedor = self.vendor_id
                    
                    # Criar ID único para o produto
                    produto_id = f"{vendedor}_{self._extract_product_id(link or nome)}"
                    
                    # Cria o dicionário do produto
                    produto = {
                        "id": produto_id,
                        "titulo": nome,
                        "preco": preco,
                        "categoria": categoria,
                        "vendedor": vendedor,
                        "artista": self._extrair_artista(nome),
                        "url": link,
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    # Adiciona o produto à lista apenas se ele ainda não existir
                    if not self._produto_ja_existe(produto):
                        produtos.append(produto)
                        logger.info(f"Produto extraído: {nome}")
                
                except Exception as e:
                    logger.error(f"Erro ao extrair produto: {e}")
                    continue
            
            return produtos
        
        except Exception as e:
            logger.error(f"Erro ao processar a página {url}: {e}")
            # Salvar screenshot para debug em caso de erro
            try:
                screenshot_path = os.path.join(DEBUG_DIR, f"shopee_error_{int(time.time())}.png")
                self.driver.save_screenshot(screenshot_path)
                logger.info(f"Screenshot de erro salvo em {screenshot_path}")
            except:
                pass
            return []
    
    def _extract_product_id(self, url: str) -> str:
        """Extrai o ID do produto a partir da URL"""
        try:
            parsed_url = urlparse(url)
            path = parsed_url.path
            # O padrão da URL da Shopee geralmente termina com um ID numérico
            match = re.search(r'i\.(\d+)\.(\d+)', url)
            if match:
                return f"{match.group(1)}_{match.group(2)}"
            return path.split('-i.')[-1] if '-i.' in path else path.split('.')[-1]
        except:
            return str(hash(url))
    
    def _produto_ja_existe(self, produto: Dict[str, str]) -> bool:
        """Verifica se o produto já existe na lista de produtos extraídos"""
        for prod_existente in self.todos_produtos:
            if prod_existente.get('id') == produto['id'] or prod_existente.get('url') == produto['url']:
                return True
        return False
    
    def _is_cd(self, titulo: str) -> bool:
        """
        Verifica se o produto é um CD com base no título
        
        Args:
            titulo: Título do produto
            
        Returns:
            True se for um CD, False caso contrário
        """
        titulo_lower = titulo.lower()
        
        # Frases específicas que indicam que o produto é um CD
        frases_cd = [
            'cd ', 'cd-', '[cd]', '(cd)', ' cd', 'álbum cd', 'album cd',
            'compact disc', 'box cd', 'cd box', 'cdbox', 'cd single',
            'audio cd', 'áudio cd', 'cd audio', 'cd de música', 'cd de musica',
            'cd musical', 'cd original', 'cd lacrado', 'cd novo',
            'disco compacto', 'coletânea cd', 'coletanea cd'
        ]
        
        for frase in frases_cd:
            if frase in titulo_lower:
                # Verifica exclusões após encontrar correspondência
                # Mas primeiro confirma que é realmente um CD
                exclusoes = [
                    'cabo', 'controle', 'caixa', 'acessório', 'acessorio', 
                    'case', 'estojo', 'suporte', 'dvd', 'notebook', 'player', 
                    'laptop', 'hd', 'ssd', 'pendrive', 'mouse', 'fone', 
                    'headset', 'pc'
                ]
                
                for exclusao in exclusoes:
                    if exclusao in titulo_lower:
                        # Se encontrou um termo de exclusão, verifica se há termos específicos
                        # que confirmam que é um CD apesar do termo de exclusão
                        confirmacoes = ['banda', 'artista', 'cantor', 'álbum', 'album', 'música', 'musica', 'rock']
                        for confirmacao in confirmacoes:
                            if confirmacao in titulo_lower:
                                return True
                        
                        # Se não encontrou confirmação, provavelmente não é um CD
                        return False
                
                # Se não encontrou exclusões, é um CD
                return True
        
        # Verifica se contém o nome de gêneros musicais comuns junto com indicações de ser uma mídia física
        generos = ['rock', 'pop', 'mpb', 'samba', 'jazz', 'blues', 'hip hop', 'rap', 'funk', 'sertanejo', 'gospel']
        termos_midia = ['álbum', 'album', 'disco', 'single', 'faixa', 'banda', 'lançamento']
        
        for genero in generos:
            if genero in titulo_lower:
                for termo in termos_midia:
                    if termo in titulo_lower:
                        return True
        
        # Verificações adicionais para nomes de artistas famosos + indicações de mídia física
        if any(artista in titulo_lower for artista in ['madonna', 'michael jackson', 'queen', 'beatles', 'u2', 'metallica']):
            if any(midia in titulo_lower for midia in ['álbum', 'album', 'single', 'remix', 'versão', 'versao', 'edição', 'edicao']):
                return True
                
        return False  # Se não encontrou nenhuma das frases, não é um CD
    
    def _extrair_artista(self, titulo: str) -> str:
        """
        Tenta extrair o nome do artista do título do produto
        
        Args:
            titulo: Título do produto
            
        Returns:
            Nome do artista, se identificado
        """
        # Lista de padrões comuns para identificar artistas
        # Geralmente no formato: "Artista - Nome do Álbum" ou "CD Nome do Álbum - Artista"
        
        # Normaliza o título para evitar problemas com codificação
        titulo = titulo.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        
        # Padrão: "Artista - Nome do Álbum"
        if " - " in titulo:
            partes = titulo.split(" - ", 1)
            
            # Verifica se a primeira parte contém palavra-chave de CD
            palavras_cd = ["cd", "álbum", "album", "disco"]
            primeira_parte_lower = partes[0].lower()
            
            if any(palavra in primeira_parte_lower for palavra in palavras_cd):
                # Provavelmente é "CD Nome - Artista"
                if len(partes) > 1:
                    return partes[1].strip()
            else:
                # Provavelmente é "Artista - Nome"
                return partes[0].strip()
        
        # Padrão: "CD Artista - Nome do Álbum"
        if titulo.lower().startswith("cd ") and " - " in titulo[3:]:
            titulo_sem_cd = titulo[3:]
            partes = titulo_sem_cd.split(" - ", 1)
            return partes[0].strip()
        
        # Padrão: "CD Nome do Álbum do Artista"
        if titulo.lower().startswith("cd "):
            # Procura por padrões como "do Artista", "by Artista", "de Artista"
            texto = titulo[3:]  # Remove "CD " do início
            for padrao in [" do ", " by ", " de ", " por ", " with "]:
                if padrao in texto.lower():
                    partes = texto.lower().split(padrao, 1)
                    if len(partes) > 1:
                        return texto.split(padrao, 1)[1].strip()
        
        # Tenta encontrar artistas conhecidos no título
        artistas_conhecidos = [
            "Madonna", "Michael Jackson", "Queen", "Beatles", "U2", "Metallica",
            "AC/DC", "Pink Floyd", "Rolling Stones", "Led Zeppelin", "Black Sabbath",
            "Elvis Presley", "Bob Dylan", "David Bowie", "Prince", "Nirvana",
            "Bruce Springsteen", "The Police", "Dire Straits", "Guns N' Roses",
            "Iron Maiden", "Aerosmith", "Deep Purple", "Kiss", "Bon Jovi",
            "Red Hot Chili Peppers", "Pearl Jam", "Radiohead", "Coldplay",
            "Roberto Carlos", "Caetano Veloso", "Gilberto Gil", "Tim Maia",
            "Djavan", "Lulu Santos", "Legião Urbana", "Paralamas do Sucesso",
            "Titãs", "Barão Vermelho", "Capital Inicial", "Skank", "Jota Quest"
        ]
        
        for artista in artistas_conhecidos:
            if artista.lower() in titulo.lower():
                # Verifica se o artista é parte de uma palavra maior
                indice = titulo.lower().find(artista.lower())
                fim_indice = indice + len(artista)
                
                # Verifica se o artista está como palavra isolada ou no início/fim
                if (indice == 0 or not titulo[indice-1].isalpha()) and \
                   (fim_indice == len(titulo) or not titulo[fim_indice].isalpha()):
                    return artista
        
        return "Não identificado"
    
    def _extrair_categoria(self, titulo: str) -> str:
        """
        Tenta extrair a categoria do CD com base no título
        
        Args:
            titulo: Título do produto
            
        Returns:
            Categoria do CD
        """
        titulo_lower = titulo.lower()
        
        # Mapeamento de palavras-chave para categorias
        categorias = {
            'rock': ['rock', 'metal', 'punk', 'grunge'],
            'pop': ['pop', 'pop music'],
            'mpb': ['mpb', 'música popular brasileira', 'musica popular brasileira'],
            'samba': ['samba', 'pagode', 'axé', 'axe'],
            'jazz': ['jazz', 'blues'],
            'clássica': ['clássica', 'classica', 'classical', 'orchestra'],
            'hip hop': ['hip hop', 'rap', 'hip-hop', 'trap'],
            'eletrônica': ['eletrônica', 'eletronica', 'electronic', 'dance', 'techno'],
            'reggae': ['reggae', 'ska'],
            'country': ['country', 'folk', 'sertanejo']
        }
        
        for categoria, keywords in categorias.items():
            for keyword in keywords:
                if keyword in titulo_lower:
                    return categoria
        
        return "Outros"  # Categoria padrão
    
    def navegar_por_paginas(self) -> List[Dict[str, str]]:
        """
        Navega pela lista de páginas de resultados
        
        Returns:
            Lista de todos os produtos extraídos
        """
        pagina_atual = 0
        produtos_extraidos = []
        
        while pagina_atual < self.max_paginas:
            # Constrói a URL para esta página
            url_paginada = self.url_inicial.replace("page=0", f"page={pagina_atual}")
            
            logger.info(f"Processando página {pagina_atual + 1}/{self.max_paginas}: {url_paginada}")
            
            # Extrai produtos desta página
            produtos_pagina = self.extrair_produtos_pagina(url_paginada)
            
            # Adiciona à lista total
            produtos_extraidos.extend(produtos_pagina)
            
            # Se a página não retornou produtos, assume que chegamos ao fim
            if not produtos_pagina:
                logger.info(f"Nenhum produto encontrado na página {pagina_atual + 1}. Encerrando.")
                break
            
            # Aguarda um pouco antes de ir para a próxima página (para evitar bloqueios)
            tempo_espera = self.espera_pagina + random.uniform(1.0, 3.0)
            logger.info(f"Aguardando {tempo_espera:.2f} segundos antes da próxima página...")
            time.sleep(tempo_espera)
            
            pagina_atual += 1
        
        return produtos_extraidos
    
    def salvar_para_csv(self, produtos: List[Dict[str, str]], modo: str = 'a') -> bool:
        """
        Salva os produtos extraídos para um arquivo CSV
        
        Args:
            produtos: Lista de dicionários com informações dos produtos
            modo: Modo de abertura do arquivo ('w' para escrever, 'a' para adicionar)
            
        Returns:
            True se salvou com sucesso, False em caso de erro
        """
        if not produtos:
            logger.info("Nenhum produto para salvar.")
            return True
        
        # Define o cabeçalho do CSV
        fieldnames = ['id', 'titulo', 'artista', 'preco', 'categoria', 'vendedor', 'url', 'timestamp']
        
        try:
            # Verifica se o arquivo já existe para determinar se precisa escrever o cabeçalho
            arquivo_existe = os.path.exists(self.arquivo_saida) and os.path.getsize(self.arquivo_saida) > 0
            
            with open(self.arquivo_saida, modo, newline='', encoding='utf-8') as arquivo:
                writer = csv.DictWriter(arquivo, fieldnames=fieldnames)
                
                # Escreve o cabeçalho apenas se o arquivo for novo ou estiver vazio
                if not arquivo_existe or modo == 'w':
                    writer.writeheader()
                
                # Escreve as linhas com os dados dos produtos
                for produto in produtos:
                    # Garante que todos os campos necessários existam
                    row = {field: produto.get(field, '') for field in fieldnames}
                    writer.writerow(row)
            
            logger.info(f"Dados salvos com sucesso em {self.arquivo_saida}. Total: {len(produtos)} produtos.")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar dados em CSV: {e}")
            return False
    
    def executar(self) -> None:
        """Executa o scraper, extraindo e salvando os produtos"""
        try:
            # Inicializa o driver do Selenium
            self.inicializar_driver()
            
            # Tenta fazer login se existirem credenciais configuradas
            usuario = os.getenv("SHOPEE_USERNAME")
            senha = os.getenv("SHOPEE_PASSWORD")
            
            if usuario and senha:
                logger.info(f"Tentando fazer login com o usuário: {usuario}")
                login_success = self.fazer_login(usuario, senha)
                if login_success:
                    logger.info("Login realizado com sucesso. Prosseguindo com a extração.")
                else:
                    logger.warning("Falha no login. Tentando prosseguir com o scraper mesmo assim.")
            else:
                logger.warning("Credenciais não encontradas no arquivo .env. O scraper pode não funcionar corretamente.")
            
            # Navega pelas páginas e extrai os produtos
            novos_produtos = self.navegar_por_paginas()
            
            if novos_produtos:
                # Salva os produtos no arquivo CSV
                if self.salvar_para_csv(novos_produtos):
                    logger.info(f"Total de {len(novos_produtos)} novos produtos salvos no arquivo {self.arquivo_saida}")
                else:
                    logger.error("Erro ao salvar os produtos no arquivo CSV")
            else:
                logger.warning("Nenhum novo produto encontrado")
                
        except Exception as e:
            logger.error(f"Erro ao executar o scraper: {e}")
        finally:
            # Fecha o driver do Selenium
            self.fechar_driver()

    def _criar_produtos_dummy(self) -> None:
        """
        Cria alguns produtos dummy para evitar erros no dashboard quando não consegue acessar a página real
        """
        logger.info("Criando produtos dummy para a Shopee")
        produtos_dummy = [
            {
                "id": f"shopee_dummy_{1}",
                "titulo": "CD Exemplo da Shopee - Precisa de Autenticação",
                "artista": "Artista Exemplo",
                "preco": "R$ 30,00",
                "categoria": "CD",
                "vendedor": self.vendor_id,
                "url": self.url_inicial,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        ]
        
        # Salva os produtos dummy para CSV
        try:
            with open(self.arquivo_saida, 'w', newline='', encoding='utf-8') as arquivo_csv:
                writer = csv.DictWriter(arquivo_csv, fieldnames=produtos_dummy[0].keys())
                writer.writeheader()
                writer.writerows(produtos_dummy)
            logger.info(f"Salvos {len(produtos_dummy)} produtos dummy no arquivo {self.arquivo_saida}")
        except Exception as e:
            logger.error(f"Erro ao salvar produtos dummy: {e}")
            
        self.todos_produtos.extend(produtos_dummy)

def verificar_dependencias():
    """Verifica se todas as dependências estão instaladas"""
    try:
        import selenium
        logger.info(f"Selenium instalado: {selenium.__version__}")
        return True
    except ImportError:
        logger.error("Selenium não está instalado. Instale com: pip install selenium")
        return False

def main():
    """Função principal"""
    logger.info("Iniciando script de extração de CDs da Shopee...")
    
    # Verifica dependências
    if not verificar_dependencias():
        return
    
    # Cria e executa o scraper
    scraper = ShopeeScraperSelenium()
    scraper.executar()

if __name__ == "__main__":
    main() 