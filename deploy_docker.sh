#!/bin/bash

# Script para fazer deploy do projeto scraper-tracks na VPS usando Docker

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuração da VPS
VPS_HOST="212.85.23.16"
VPS_USER="root"
VPS_PASS=".40.yABB9x2VY,hay/He"
PROJECT_DIR="/root/scraper-tracks"

echo -e "${YELLOW}Iniciando deploy do projeto scraper-tracks para a VPS com Docker...${NC}"

# Executar o script de atualização local
chmod +x docker_update.sh
./docker_update.sh

# Criar um arquivo temporário para o script de inicialização
cat > setup.sh << 'EOL'
#!/bin/bash

# Verificar se o Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "Docker não encontrado, instalando..."
    apt-get update
    apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io
fi

# Verificar se o Docker Compose está instalado
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose não encontrado, instalando..."
    curl -L "https://github.com/docker/compose/releases/download/v2.15.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Criar diretórios para volumes
mkdir -p "$PROJECT_DIR/data"
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$PROJECT_DIR/debug"

# Iniciar os containers
cd "$PROJECT_DIR"
docker-compose down || true
docker-compose up -d --build

# Configurar firewall
if command -v ufw &> /dev/null; then
    ufw allow 5002/tcp
    echo "Firewall configurado para permitir conexões na porta 5002"
fi

echo "Deploy concluído! O dashboard está disponível em http://$HOSTNAME:5002"
EOL

# Criar diretório remoto via SSH
echo -e "${YELLOW}Criando diretório do projeto...${NC}"
sshpass -p "$VPS_PASS" ssh -o StrictHostKeyChecking=no $VPS_USER@$VPS_HOST "mkdir -p $PROJECT_DIR"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Diretório criado com sucesso!${NC}"
else
    echo -e "${RED}Erro ao criar diretório!${NC}"
    exit 1
fi

# Compactar os arquivos do projeto
echo -e "${YELLOW}Compactando arquivos do projeto...${NC}"
tar -czf scraper-tracks.tar.gz --exclude="__pycache__" --exclude="*.pyc" --exclude=".DS_Store" --exclude="scraper-tracks.tar.gz" .

# Enviar o arquivo compactado para a VPS
echo -e "${YELLOW}Enviando arquivos para a VPS...${NC}"
sshpass -p "$VPS_PASS" scp -o StrictHostKeyChecking=no scraper-tracks.tar.gz setup.sh $VPS_USER@$VPS_HOST:$PROJECT_DIR/

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Arquivos enviados com sucesso!${NC}"
else
    echo -e "${RED}Erro ao enviar arquivos!${NC}"
    exit 1
fi

# Descompactar os arquivos no servidor e executar o setup
echo -e "${YELLOW}Configurando o servidor...${NC}"
sshpass -p "$VPS_PASS" ssh -o StrictHostKeyChecking=no $VPS_USER@$VPS_HOST "cd $PROJECT_DIR && tar -xzf scraper-tracks.tar.gz && rm scraper-tracks.tar.gz && chmod +x setup.sh && ./setup.sh"

echo -e "${GREEN}Deploy concluído! O dashboard está disponível em http://$VPS_HOST:5002${NC}"

# Limpar arquivos temporários
rm -f setup.sh 