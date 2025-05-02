# Scraper de CDs da Shopee

Este scraper foi desenvolvido para extrair informações de CDs da loja [LinhuaCong na Shopee](https://shopee.com.br/linhuacong.br?categoryId=100639&sortBy=ctime&page=0), mas enfrenta algumas limitações devido às políticas de segurança da Shopee.

## Limitações Atuais

O principal desafio enfrentado pelo scraper é que a Shopee requer autenticação para acessar a página de produtos. Quando executado sem autenticação, o scraper detecta a página de login e cria um produto dummy para evitar erros no dashboard.

### Comportamento Atual
- Detecta quando está na página de login
- Salva screenshots e HTML para depuração
- Cria um produto dummy para exibição no dashboard
- Lida com múltiplos formatos de HTML da Shopee

## Possíveis Soluções

Para acessar os produtos reais da Shopee, algumas soluções possíveis são:

### 1. Autenticação com Selenium
É possível modificar o scraper para fazer login automaticamente com credenciais válidas:

```python
def fazer_login(self, usuario, senha):
    try:
        # Encontrar e preencher campos de login
        campo_usuario = self.driver.find_element(By.CSS_SELECTOR, "input[name='loginKey']")
        campo_senha = self.driver.find_element(By.CSS_SELECTOR, "input[name='password']")
        
        campo_usuario.send_keys(usuario)
        campo_senha.send_keys(senha)
        
        # Clicar no botão de login
        botao_login = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        botao_login.click()
        
        # Aguardar redirecionamento
        time.sleep(5)
        return True
    except Exception as e:
        logger.error(f"Erro ao fazer login: {e}")
        return False
```

### 2. Salvar e reutilizar cookies
Outra abordagem é salvar os cookies após um login manual e reutilizá-los:

```python
def salvar_cookies(self):
    cookies = self.driver.get_cookies()
    with open("shopee_cookies.pkl", "wb") as f:
        pickle.dump(cookies, f)

def carregar_cookies(self):
    try:
        with open("shopee_cookies.pkl", "rb") as f:
            cookies = pickle.load(f)
            for cookie in cookies:
                self.driver.add_cookie(cookie)
        return True
    except:
        return False
```

### 3. Utilizar a API da Shopee
A Shopee possui uma API interna que pode ser usada para acessar dados de produtos sem a necessidade de login. Isso requer engenharia reversa da API, mas pode ser mais confiável:

```python
def obter_produtos_api(self, vendor_id, limit=20, offset=0):
    url = f"https://shopee.com.br/api/v4/search/search_items"
    params = {
        "by": "relevancy",
        "match_id": vendor_id,
        "limit": limit,
        "newest": offset,
        "order": "desc",
        "page_type": "shop",
        "scenario": "PAGE_OTHERS"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"https://shopee.com.br/{vendor_id}"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        data = response.json()
        return data.get("items", [])
    except Exception as e:
        logger.error(f"Erro ao acessar API: {e}")
        return []
```

## Como Implementar a Autenticação

Para implementar a autenticação, recomendamos:

1. Criar um arquivo `.env` com as credenciais (não incluir no controle de versão)
2. Ler as credenciais no início do script
3. Implementar a função de login antes de tentar acessar a página de produtos

Exemplo de uso:
```python
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    usuario = os.getenv("SHOPEE_USERNAME")
    senha = os.getenv("SHOPEE_PASSWORD")
    
    scraper = ShopeeScraperSelenium()
    if usuario and senha:
        scraper.fazer_login(usuario, senha)
    scraper.executar()
```

## Testes e Monitoramento

É fundamental monitorar o funcionamento do scraper, já que a Shopee pode mudar a estrutura da página ou intensificar as medidas anti-bot. Os logs e screenshots salvos em `debug/` ajudam nesse monitoramento.

---

**Nota**: Use este scraper respeitando os Termos de Serviço da Shopee. Este código é fornecido apenas para fins educacionais e de pesquisa. 