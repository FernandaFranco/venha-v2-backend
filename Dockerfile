# Usar imagem base do Python
FROM python:3.11-slim

# Definir diretório de trabalho
WORKDIR /app

# Copiar requirements primeiro (para cache de dependências)
COPY requirements.txt .

# Instalar dependências (--no-cache-dir para imagem menor)
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Tornar entrypoint executavel
RUN chmod +x entrypoint.sh

# Desabilitar buffering do Python (para ver logs em tempo real)
ENV PYTHONUNBUFFERED=1

# Porta padrão (Railway injeta PORT automaticamente)
ENV PORT=5000
EXPOSE 5000

# Usar entrypoint script para producao
# Para desenvolvimento local, docker-compose.yml sobrescreve com "python app.py"
ENTRYPOINT ["./entrypoint.sh"]
