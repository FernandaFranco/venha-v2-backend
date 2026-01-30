#!/bin/sh
# Entrypoint script para producao
echo "Starting gunicorn on port 5000"
exec gunicorn app:app --bind "0.0.0.0:5000"
