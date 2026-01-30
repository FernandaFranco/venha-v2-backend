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

# Desabilitar buffering do Python (para ver logs em tempo real)
ENV PYTHONUNBUFFERED=1

# Porta padrão (Railway injeta PORT automaticamente)
ENV PORT=5000
EXPOSE 5000

# Comando para producao usando gunicorn
# Para desenvolvimento local, docker-compose.yml sobrescreve com "python app.py"
# Usa exec form com shell explicito para garantir expansao de $PORT
CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:${PORT:-5000}"]
