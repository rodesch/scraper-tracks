# Configuração de Credenciais para o Scraper da Shopee

Este documento explica como configurar e usar credenciais de usuário para fazer o scraper da Shopee funcionar corretamente.

## Por que são necessárias credenciais?

A Shopee utiliza mecanismos de proteção contra bots e scraping, exigindo autenticação para acessar determinadas páginas e conteúdos. Sem credenciais válidas, o scraper encontrará páginas de login, o que impede a coleta adequada de dados.

## Configurando suas credenciais

Existem duas maneiras de configurar suas credenciais:

### 1. Usando um arquivo .env (Recomendado)

1. Crie um arquivo chamado `.env` na raiz do projeto (mesmo diretório onde está o arquivo `extrair_cds_shopee.py`).
2. Adicione suas credenciais da Shopee no seguinte formato:

```
SHOPEE_USERNAME="seu_email@exemplo.com"
SHOPEE_PASSWORD="sua_senha"
```

3. Salve o arquivo. As credenciais serão carregadas automaticamente quando você executar o scraper.

⚠️ **IMPORTANTE**: Nunca compartilhe seu arquivo `.env` ou commit ele em repositórios git. O arquivo já está incluído no `.gitignore`.

### 2. Usando parâmetros de linha de comando

Você pode passar suas credenciais diretamente quando executar o script, usando os parâmetros `--username` e `--password`:

```bash
python executar_shopee.py --username "seu_email@exemplo.com" --password "sua_senha"
```

⚠️ **ATENÇÃO**: Este método pode expor suas credenciais no histórico do terminal e não é recomendado para uso regular.

## Executando o scraper com credenciais

Quando as credenciais estiverem configuradas, você pode executar o scraper normalmente:

```bash
python executar_shopee.py
```

O script carregará automaticamente as credenciais do arquivo `.env` (ou usará as que foram passadas por parâmetro) e tentará fazer login na Shopee antes de iniciar o processo de scraping.

## Verificação de login

O scraper vai tentar verificar se o login foi bem-sucedido e salvará capturas de tela do processo nos seguintes arquivos (na pasta `debug/`):

- `shopee_pre_login_[timestamp].png`: Página antes da tentativa de login
- `shopee_post_login_[timestamp].png`: Página após login bem-sucedido
- `shopee_login_error_[timestamp].png`: Página em caso de falha no login

## Solução de problemas

Se o scraper não conseguir fazer login corretamente, verifique:

1. **Credenciais corretas**: Certifique-se de que o email/usuário e senha estão corretos
2. **Captchas**: A Shopee pode exigir captchas ou verificações adicionais
3. **Bloqueio de IP**: Se tentar muitas vezes, seu IP pode ser temporariamente bloqueado
4. **Alterações no site**: O Shopee pode mudar a estrutura da página de login periodicamente

## Cookies e sessões

O scraper não implementa ainda a funcionalidade de salvar e reutilizar cookies, mas isso pode ser adicionado no futuro para reduzir a necessidade de login frequente.

---

**Nota**: Este scraper é fornecido apenas para fins educacionais e de pesquisa. Respeite os Termos de Serviço da Shopee ao usar esta ferramenta. 