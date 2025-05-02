FROM python:3.9-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Instalar Google Chrome para os scrapers que usam Selenium
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Baixar e instalar ChromeDriver
RUN wget -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
    && rm /tmp/chromedriver.zip

# Copiar arquivos do projeto
COPY . /app/

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt || python instalar_dependencias.py

# Criar diretórios necessários
RUN mkdir -p logs static static/css static/js templates debug

# Expor a porta que a aplicação usa
EXPOSE 5002

# Comando para iniciar a aplicação
CMD ["python", "dashboard.py"] 