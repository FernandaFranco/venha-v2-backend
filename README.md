# Venha - Sistema de Convites Online

API REST para criação e gerenciamento de convites de eventos com funcionalidade de RSVP.

## 📋 Sobre o Projeto

Este sistema permite que anfitriões criem eventos, gerem links de convite únicos e gerenciem confirmações de presença. Os convidados podem confirmar presença, modificar ou cancelar suas respostas através de um link personalizado.

### Funcionalidades Principais

**Para Anfitriões:**
- Cadastro e autenticação de usuário
- Criação de eventos com data, hora e endereço (via CEP)
- Visualização de lista de eventos criados
- Gerenciamento de convidados confirmados
- Recebimento de emails simulados quando alguém confirma presença
- Exportação de lista de convidados em CSV
- Configuração de permissões (permitir/bloquear modificações e cancelamentos)

**Para Convidados:**
- Visualização de detalhes do evento via link único
- Confirmação de presença (RSVP)
- Informação de número de adultos e crianças
- Adição de membros da família
- Comentários sobre necessidades especiais ou alergias
- Modificação de confirmação de presença
- Cancelamento de presença com motivo opcional

## 🏗️ Arquitetura da Aplicação

O sistema Venha utiliza uma arquitetura de três camadas (Frontend, Backend API, Banco de Dados) com integração a múltiplas APIs externas.

**Diagrama de Arquitetura Completo:** Consulte o arquivo [`ARCHITECTURE.md`](ARCHITECTURE.md) para visualizar o diagrama detalhado da arquitetura, fluxo de dados, decisões de design e integrações com serviços externos.

**Visão Resumida:**
- **Frontend (Next.js):** Interface web responsiva com SSR, páginas públicas (convites) e privadas (dashboard)
- **Backend (Flask REST API):** Lógica de negócio, autenticação, validações e integrações com serviços externos
- **Banco de Dados (SQLite):** Armazenamento persistente de hosts, eventos e confirmações
- **Serviços Externos (Backend):** Google Geocoding com fallback Nominatim (coordenadas)
- **Serviços Externos (Frontend):** ViaCEP (endereços brasileiros), Google Maps (visualização), WeatherAPI (previsão do tempo)
- **Notificações:** Modo simulação - emails impressos no console

**Comunicação:** API REST com JSON, autenticação via session cookies, documentação Swagger/OpenAPI automática.

## 🛠️ Tecnologias Utilizadas

- **Python 3.x**
- **Flask** - Framework web
- **SQLAlchemy** - ORM para banco de dados
- **SQLite** - Banco de dados (desenvolvimento)
- **Flask-RESTX** - Documentação Swagger/OpenAPI
- **Bcrypt** - Hash de senhas

## 📁 Estrutura do Projeto

```
backend/
├── app.py                      # Aplicação principal e rotas Swagger
├── extensions.py               # Inicialização de extensões (db, bcrypt, limiter)
├── models.py                   # Modelos do banco de dados
├── routes/                     # Rotas da API (blueprints)
│   ├── __init__.py
│   ├── auth.py                # Autenticação
│   ├── events.py              # Gerenciamento de eventos
│   └── attendees.py           # RSVPs e convidados
├── services/                   # Serviços externos
│   ├── __init__.py
│   ├── email_service.py       # Simulação de emails
│   ├── geocoding_service.py   # Integração Google Geocoding/Nominatim
│   └── cep_service.py         # Integração ViaCEP
├── requirements.txt            # Dependências Python
├── .env.example               # Template de variáveis de ambiente
└── .gitignore                 # Arquivos ignorados pelo Git
```

## 🚀 Configuração e Instalação (Docker)

A forma recomendada de rodar o projeto completo é usando Docker. Este método garante que todas as dependências sejam instaladas corretamente e que ambos os serviços (frontend + backend) se comuniquem adequadamente.

### Pré-requisitos
- Docker Desktop instalado e rodando
- Git instalado
- Conexão com internet para download de dependências

### Passo 1: Clonar os Repositórios

Crie um diretório pai e clone ambos os projetos:

```bash
mkdir venha_project
cd venha_project
git clone https://github.com/FernandaFranco/rsvp_app_api.git backend
git clone https://github.com/FernandaFranco/rsvp_app_front_end.git frontend
```

**Importante:** Os comandos acima clonam os repositórios nas pastas `backend` e `frontend` respectivamente, que são os nomes esperados pelo Docker Compose.

**Estrutura de diretórios esperada:**
```
venha_project/
├── backend/    (este repositório)
│   ├── app.py
│   ├── .env.example
│   ├── Dockerfile
│   └── ...
└── frontend/   (repositório do frontend)
    ├── docker-compose.yml
    ├── .env.local.example
    ├── Dockerfile
    └── ...
```

### Passo 2: Configurar Variáveis de Ambiente

1. Navegue até a pasta do backend e copie o arquivo de exemplo:

```bash
cd backend
cp .env.example .env
```

2. Gere uma chave secreta única para o SECRET_KEY:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

3. Edite o arquivo `.env` e configure as variáveis:

```bash
# Obrigatórias
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=sua-chave-secreta-gerada-aqui
DATABASE_URL=sqlite:///invitations.db

# Opcional - Google Geocoding API (usa Nominatim como fallback se não configurado)
GOOGLE_GEOCODING_API_KEY=sua-chave-google-aqui

# Frontend URL
FRONTEND_URL=http://localhost:3000
```

**Substituições necessárias:**
- `sua-chave-secreta-gerada-aqui`: Cole a chave gerada no passo 2
- `sua-chave-google-aqui`: Sua chave do Google Geocoding API (opcional)

**Como obter GOOGLE_GEOCODING_API_KEY (Opcional):**
1. Acesse [Google Cloud Console](https://console.cloud.google.com)
2. Crie um projeto ou selecione um existente
3. Ative a API "Geocoding API"
4. Vá em "Credenciais" → "Criar credenciais" → "Chave de API"
5. Copie a chave gerada
6. (Recomendado) Configure restrições de IP ou serviço para segurança

**Nota sobre APIs Externas:** As chaves de API serão compartilhadas separadamente para fins de avaliação. Não inclua chaves reais no código versionado.

### Passo 3: Configurar Frontend

Configure também o `.env.local` do frontend seguindo as instruções no README do frontend.

### Passo 4: Rodar com Docker

**IMPORTANTE:** O `docker-compose.yml` está localizado na pasta `frontend/`. Para rodar o projeto completo:

1. Navegue até a pasta do frontend:
   ```bash
   cd ../frontend
   ```

2. Execute o Docker Compose:
   ```bash
   docker-compose up --build
   ```

   **O que acontece:**
   - O Docker baixa as imagens base necessárias
   - Instala todas as dependências do backend (Python/Flask)
   - Instala todas as dependências do frontend (Next.js)
   - Inicia ambos os serviços
   - Backend fica disponível na porta 5000
   - Frontend fica disponível na porta 3000

   **Primeira execução:** Pode levar alguns minutos para baixar e instalar tudo.

3. Aguarde até ver as mensagens indicando que os serviços estão prontos. Então acesse:
   - **Frontend:** http://localhost:3000
   - **Backend API:** http://localhost:5000
   - **Documentação Swagger:** http://localhost:5000/api/docs

### Comandos Úteis do Docker

**Ver logs em tempo real:**
```bash
docker-compose logs -f
```

**Ver logs apenas do backend:**
```bash
docker-compose logs -f backend
```

**Parar containers (mantém os dados):**
```bash
docker-compose down
```

**Parar e remover volumes (limpa o banco de dados):**
```bash
docker-compose down -v
```

**Reiniciar apenas o backend:**
```bash
docker restart venha_backend
```

**Acessar terminal do container:**
```bash
docker exec -it venha_backend bash
```

**Reconstruir do zero (se houver problemas):**
```bash
docker-compose down -v
docker-compose up --build --force-recreate
```

## 📖 Documentação da API

### Swagger UI

Acesse a documentação interativa em: http://localhost:5000/api/docs

Aqui você pode:
- Ver todos os endpoints disponíveis
- Testar requisições diretamente no navegador
- Ver exemplos de requisições e respostas
- Verificar códigos de status HTTP

### Principais Endpoints

**Autenticação:**
- `POST /api/auth/signup` - Criar conta de anfitrião
- `POST /api/auth/login` - Fazer login
- `POST /api/auth/logout` - Fazer logout
- `GET /api/auth/me` - Obter usuário atual

**Eventos:**
- `POST /api/events/create` - Criar novo evento (requer autenticação)
- `GET /api/events/my-events` - Listar meus eventos (requer autenticação)
- `GET /api/events/{slug}` - Obter detalhes de evento por slug (público)
- `GET /api/events/{event_id}/attendees` - Listar convidados (requer autenticação)
- `GET /api/events/{event_id}/export-csv` - Exportar convidados como CSV

**Convidados (RSVP):**
- `POST /api/attendees/rsvp` - Confirmar presença em evento
- `POST /api/attendees/find` - Buscar confirmação por WhatsApp
- `PUT /api/attendees/modify` - Modificar confirmação
- `POST /api/attendees/cancel` - Cancelar confirmação

## 🌐 APIs Externas

O backend integra-se com **1 API externa** principal (Google Geocoding) com fallback para Nominatim (OpenStreetMap).

> **Nota:** A API ViaCEP (busca de endereços por CEP) é chamada **diretamente pelo frontend**, não pelo backend.

### Google Geocoding API

**URL:** https://developers.google.com/maps/documentation/geocoding

**Propósito:** Conversão de endereços completos em coordenadas geográficas (latitude/longitude) para exibição de mapas no frontend.

**Licença/Custo:**
- Plano gratuito com crédito mensal de $200 USD
- Primeiras 40.000 requisições/mês são gratuitas
- Licença: Proprietária (Google Cloud Platform)

**Uso no Backend:**
- Arquivo: `services/geocoding_service.py`
- Endpoints expostos: `POST /api/events/create` (geocoding automático), `POST /api/events/geocode` (validação manual)
- Funcionalidade: Converter endereço textual em coordenadas lat/lng

**Endpoints utilizados:**
- `GET https://maps.googleapis.com/maps/api/geocode/json`
  - Parâmetros: `address` (endereço completo), `key` (API key)
  - Retorna: `results[0].geometry.location` (lat, lng)

**Fallback - Nominatim (OpenStreetMap):**

Se a chave do Google não estiver configurada ou falhar, o sistema usa Nominatim como alternativa:
- **URL:** https://nominatim.openstreetmap.org/
- **Licença:** Open Data Commons Open Database License (ODbL)
- **Sem custo:** Completamente gratuito
- **Limitações:** Taxa de 1 requisição por segundo

**Endpoints utilizados:**
- `GET https://nominatim.openstreetmap.org/search`
  - Parâmetros: `q` (endereço), `format=json`, `limit=1`
  - Retorna: `[0].lat`, `[0].lon`

**Tratamento de Erro:**
- Se ambas as APIs falharem, salva evento sem coordenadas
- Frontend exibe evento normalmente, mas sem mapa
- Comportamento gracioso: sistema continua funcional

## 📧 Notificações por Email - Modo Simulação

**Implementação Atual:** O sistema **não envia emails reais**. Quando um convidado confirma, modifica ou cancela presença, o backend **imprime o conteúdo do email no console**.

**Como funciona:**
- Arquivo: `services/email_service.py`
- Modo: **Sempre simulação** (logs no console)
- Eventos que geram emails simulados:
  - Novo RSVP confirmado
  - Modificação de confirmação
  - Cancelamento de presença

**Para ver os emails simulados:**

Com o Docker rodando, execute em um novo terminal:
```bash
docker-compose logs -f backend
```

Faça um RSVP no frontend e observe o log formatado:
```
================================================================================
📧 EMAIL SIMULADO - Novo RSVP para Festa de Aniversário
================================================================================
De: noreply@venha.app
Para: host@example.com
Assunto: Novo RSVP para Festa de Aniversário

[Conteúdo HTML do email...]
================================================================================
```

## ⚙️ Resumo de Configuração

**Obrigatórias:**
- `SECRET_KEY` - Gerado localmente (Python secrets)
- `FLASK_APP` - app.py
- `DATABASE_URL` - sqlite:///invitations.db

**Opcionais com fallback:**
- `GOOGLE_GEOCODING_API_KEY` - Usa Nominatim (OpenStreetMap) se não configurado

### Comportamento Gracioso

O sistema foi projetado para funcionar mesmo quando APIs externas não estão disponíveis:

| API | Se não configurada | Impacto no usuário |
|-----|-------------------|-------------------|
| Google Geocoding | Usa Nominatim (OSM) | Nenhum (fallback automático) |
| Nominatim | Eventos criados sem coordenadas | Mapas não aparecem no frontend |

**Emails:** Sistema sempre opera em modo simulação (logs no console).

## 🐛 Solução de Problemas

### Erro: Porta já em uso (5000)
```bash
# Mac/Linux
lsof -ti:5000 | xargs kill -9
```

### Containers não iniciam ou erro de dependências
```bash
docker-compose down -v
docker-compose up --build --force-recreate
```

### Frontend não consegue conectar ao backend
- Verifique se `NEXT_PUBLIC_API_URL=http://localhost:5000` em `frontend/.env.local`
- Verifique se `FRONTEND_URL=http://localhost:3000` em `backend/.env`
- Certifique-se de que ambos os containers estão rodando: `docker ps`

### Banco de dados não foi criado
- O SQLite é criado automaticamente na primeira execução
- Se houver problemas, remova os volumes: `docker-compose down -v`

## 📝 Notas para Avaliadores

Este projeto foi desenvolvido como parte da Sprint de Arquitetura de Software da Pós-Graduação em Engenharia de Software da PUC-Rio.

### Guia Rápido de Avaliação

**Siga os passos de instalação acima** na seção "Configuração e Instalação (Docker)".

### Fluxo de Teste Sugerido

1. **Criar Conta:** Acesse http://localhost:3000 e crie uma conta de anfitrião
2. **Criar Evento:** No dashboard, crie um evento de teste (use um CEP válido como 22040-020)
3. **Copiar Link:** Copie o link do convite gerado
4. **Simular Convidado:** Abra o link em uma aba anônima
5. **Confirmar Presença:** Preencha o formulário de RSVP
6. **Ver Notificação:** Execute `docker-compose logs -f backend` para ver o email simulado
7. **Gerenciar RSVPs:** Volte ao dashboard e visualize a lista de confirmações
8. **Exportar CSV:** Exporte a lista de convidados
9. **Modificar/Cancelar:** Use o mesmo WhatsApp para buscar e modificar a confirmação

### 📧 Sistema de Notificações

**O sistema opera em MODO SIMULAÇÃO.**

Os emails **NÃO são enviados** de verdade. O conteúdo aparece nos logs do console.

**Para ver os emails simulados:**
1. Com o Docker rodando, abra um novo terminal
2. Execute: `docker-compose logs -f backend`
3. Faça um RSVP no frontend
4. Observe o log formatado no terminal

### 🗺️ APIs Externas e Fallbacks

Veja a seção **"APIs Externas"** acima para detalhes completos sobre endpoints e parâmetros.

| API | Status | Fallback | Impacto |
|-----|--------|----------|---------|
| **Google Geocoding** | Opcional | Nominatim (OpenStreetMap) | Nenhum (fallback automático) |
| **Nominatim** | Gratuito, sem chave | - | Se falhar, evento criado sem coordenadas |

**Frontend APIs (configuradas no frontend/.env.local):**
- **Google Maps:** Exibição de mapas nos convites
- **WeatherAPI:** Previsão do tempo para data do evento
- **ViaCEP:** Busca automática de endereço (API pública gratuita)

### 🐳 Comandos Úteis para Avaliação

**Ver logs em tempo real:**
```bash
docker-compose logs -f
```

**Ver apenas logs do backend (incluindo emails simulados):**
```bash
docker-compose logs -f backend
```

**Parar os containers:**
```bash
docker-compose down
```

**Reiniciar um serviço específico:**
```bash
docker restart venha_backend
docker restart venha_frontend
```

**Limpar tudo e recomeçar:**
```bash
docker-compose down -v
docker-compose up --build --force-recreate
```

### 📚 Documentação Adicional

- **Arquitetura Completa:** Veja `ARCHITECTURE.md` para diagrama detalhado
- **API REST:** Acesse http://localhost:5000/api/docs para documentação Swagger interativa
- **Código Fonte:** Todos os endpoints estão documentados em `routes/`

## 📄 Licença

Este projeto foi desenvolvido para fins educacionais.

## 👤 Autora

Fernanda Franco

PUC-Rio - Pós-Graduação em Engenharia de Software

Sprint de Arquitetura de Software - 2025
