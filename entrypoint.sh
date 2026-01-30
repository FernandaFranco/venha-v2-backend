#!/bin/sh
# Entrypoint script para producao
# Railway injeta PORT, usa 5000 como fallback para desenvolvimento
APP_PORT="${PORT:-5000}"

# Inicializar banco de dados (criar tabelas se nao existirem)
echo "Initializing database..."
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database initialized!')"

echo "Starting gunicorn on port $APP_PORT"
exec gunicorn app:app --bind "0.0.0.0:$APP_PORT"
