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

# Expor porta do Flask
EXPOSE 5000

# Comando para rodar a aplicação em modo desenvolvimento
CMD ["python", "app.py"]
