#!/bin/sh
# Entrypoint script para garantir que PORT seja lido corretamente
PORT="${PORT:-5000}"
echo "Starting gunicorn on port $PORT"
exec gunicorn app:app --bind "0.0.0.0:$PORT"
