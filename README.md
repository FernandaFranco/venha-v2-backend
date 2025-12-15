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
- Recebimento de emails quando alguém confirma presença
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

## 🛠️ Tecnologias Utilizadas

- **Python 3.x**
- **Flask** - Framework web
- **SQLAlchemy** - ORM para banco de dados
- **SQLite** - Banco de dados (desenvolvimento)
- **SendGrid** - Serviço de envio de emails
- **Flask-RESTX** - Documentação Swagger/OpenAPI
- **Bcrypt** - Hash de senhas
- **ViaCEP API** - Consulta de endereços via CEP

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
│   ├── email_service.py       # Integração SendGrid
│   └── cep_service.py         # Integração ViaCEP
├── requirements.txt            # Dependências Python
├── .env.example               # Template de variáveis de ambiente
└── .gitignore                 # Arquivos ignorados pelo Git
```

## 🚀 Configuração e Instalação

### Opção 1: Usando Docker (Recomendado)

A forma mais fácil de rodar o projeto completo (frontend + backend) é usando Docker.

#### Pré-requisitos
- Docker Desktop instalado e rodando
- Arquivo `.env` configurado (veja instruções abaixo)

#### Configurar Variáveis de Ambiente

1. Copie o arquivo de exemplo:

```bash
cp .env.example .env
```

2. Edite o arquivo `.env` com suas configurações:

```bash
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=sua-chave-secreta-aqui
DATABASE_URL=sqlite:///invitations.db
SENDGRID_API_KEY=sua-chave-sendgrid-aqui
SENDER_EMAIL=seu-email@gmail.com
GOOGLE_GEOCODING_API_KEY=sua-chave-google-aqui
FRONTEND_URL=http://localhost:3000
```

**Como gerar SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

**Como obter SENDGRID_API_KEY:** Veja seção "Como obter SENDGRID_API_KEY" abaixo.

**Como obter GOOGLE_GEOCODING_API_KEY:**
1. Acesse [Google Cloud Console](https://console.cloud.google.com)
2. Crie um projeto ou selecione um existente
3. Ative a API "Geocoding API"
4. Vá em "Credenciais" → "Criar credenciais" → "Chave de API"
5. Copie a chave gerada

#### Rodar com Docker

**IMPORTANTE:** O docker-compose.yml está localizado na pasta `frontend/`. Para rodar o projeto completo:

1. Certifique-se de que os repositórios estão no mesmo diretório pai:
   ```
   projeto/
   ├── backend/    (este repositório)
   └── frontend/   (repositório do frontend)
   ```

2. Configure o `.env.local` do frontend (veja README do frontend)

3. Navegue até a pasta do frontend e rode:
   ```bash
   cd ../frontend
   docker-compose up --build
   ```

4. Acesse:
   - **Frontend:** http://localhost:3000
   - **Backend API:** http://localhost:5000
   - **Documentação Swagger:** http://localhost:5000/api/docs

**Comandos úteis:**
```bash
# Ver logs em tempo real
docker-compose logs -f

# Ver logs apenas do backend
docker-compose logs -f backend

# Parar containers
docker-compose down

# Reiniciar backend
docker restart venha_backend

# Acessar terminal do container
docker exec -it venha_backend bash
```

### Opção 2: Desenvolvimento Local (sem Docker)

#### Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- Conta SendGrid (gratuita) para envio de emails

#### Passo 1: Clonar o Repositório

```bash
git clone https://github.com/FernandaFranco/rsvp_app_api.git
cd backend
```

#### Passo 2: Criar Ambiente Virtual

**No Mac/Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

**No Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

Você verá `(venv)` no início da linha de comando quando o ambiente estiver ativado.

### Passo 3: Instalar Dependências

```bash
pip install -r requirements.txt
```

### Passo 4: Configurar Variáveis de Ambiente

1. Copie o arquivo de exemplo:

```bash
cp .env.example .env
```

2. Edite o arquivo `.env` e configure as seguintes variáveis:

```bash
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=sua-chave-secreta-aqui
DATABASE_URL=sqlite:///invitations.db
SENDGRID_API_KEY=sua-chave-sendgrid-aqui
```

#### Como gerar SECRET_KEY:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Cole o resultado no campo `SECRET_KEY` do arquivo `.env`.

#### Como obter SENDGRID_API_KEY:

1. Crie uma conta gratuita em [SendGrid](https://sendgrid.com) (100 emails/dia grátis)
2. Vá em **Settings → API Keys**
3. Clique em **Create API Key**
4. Dê um nome (ex: "invitations-app")
5. Selecione **Full Access**
6. Copie a chave (começa com `SG.`)
7. Cole no campo `SENDGRID_API_KEY`

**IMPORTANTE:** Verifique um remetente:

1. Vá em **Settings → Sender Authentication**
2. Clique em **Verify a Single Sender**
3. Preencha com seu email pessoal
4. Verifique seu email e clique no link de confirmação
5. Edite `services/email_service.py` linha 8 e substitua `'noreply@yourdomain.com'` pelo seu email verificado

### Passo 5: Executar a Aplicação

```bash
python app.py
```

A API estará rodando em: `http://localhost:5000`

A documentação Swagger estará disponível em: `http://localhost:5000/api/docs`

## 📖 Documentação da API

### Swagger UI

Acesse a documentação interativa em:

```
http://localhost:5000/api/docs
```

Aqui você pode:

- Ver todos os endpoints disponíveis
- Testar requisições diretamente no navegador
- Ver exemplos de requisições e respostas
- Verificar códigos de status HTTP

### Principais Endpoints

#### Autenticação

- `POST /api/auth/signup` - Criar conta de anfitrião
- `POST /api/auth/login` - Fazer login
- `POST /api/auth/logout` - Fazer logout
- `GET /api/auth/me` - Obter usuário atual

#### Eventos

- `POST /api/events/create` - Criar novo evento (requer autenticação)
- `GET /api/events/my-events` - Listar meus eventos (requer autenticação)
- `GET /api/events/{slug}` - Obter detalhes de evento por slug (público)
- `GET /api/events/{event_id}/attendees` - Listar convidados (requer autenticação)
- `PUT /api/events/{event_id}/attendees/{attendee_id}` - Atualizar convidado
- `DELETE /api/events/{event_id}/attendees/{attendee_id}` - Remover convidado
- `GET /api/events/{event_id}/export-csv` - Exportar convidados como CSV

#### Convidados (RSVP)

- `POST /api/attendees/rsvp` - Confirmar presença em evento
- `POST /api/attendees/find` - Buscar confirmação por WhatsApp
- `PUT /api/attendees/modify` - Modificar confirmação
- `POST /api/attendees/cancel` - Cancelar confirmação

## 🧪 Testando a API

### Exemplo 1: Criar uma conta

```bash
curl -X POST http://localhost:5000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "anfitriao@exemplo.com",
    "password": "senha123",
    "name": "João Silva",
    "whatsapp_number": "5521999999999"
  }'
```

### Exemplo 2: Fazer login

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "anfitriao@exemplo.com",
    "password": "senha123"
  }' \
  --cookie-jar cookies.txt
```

### Exemplo 3: Criar um evento

```bash
curl -X POST http://localhost:5000/api/events/create \
  -H "Content-Type: application/json" \
  --cookie cookies.txt \
  -d '{
    "title": "Festa de Aniversário",
    "description": "Venha comemorar comigo!",
    "event_date": "2025-12-25",
    "start_time": "18:00",
    "end_time": "22:00",
    "address_cep": "22040-020",
    "allow_modifications": true,
    "allow_cancellations": true
  }'
```

### Exemplo 4: Confirmar presença (RSVP)

```bash
curl -X POST http://localhost:5000/api/attendees/rsvp \
  -H "Content-Type: application/json" \
  -d '{
    "event_slug": "abc123",
    "whatsapp_number": "5521988888888",
    "name": "Maria Santos",
    "num_adults": 2,
    "num_children": 1,
    "comments": "Preciso de refeição vegetariana"
  }'
```

## 🗄️ Banco de Dados

O sistema usa SQLite para desenvolvimento. As tabelas são criadas automaticamente na primeira execução.

### Modelo de Dados

**hosts** (Anfitriões)

- id, email, whatsapp_number, name, password_hash, created_at

**events** (Eventos)

- id, host_id, slug, title, description, event_date, start_time, end_time
- address_cep, address_full, allow_modifications, allow_cancellations, created_at

**attendees** (Convidados)

- id, event_id, whatsapp_number, name
- num_adults, num_children, comments, status, rsvp_date, last_modified

## 🔒 Segurança

- Senhas são armazenadas com hash bcrypt
- Autenticação via sessão com cookie seguro
- Rate limiting em endpoints sensíveis (5 RSVPs por minuto)
- Validação de entrada em todos os endpoints
- CORS configurado para permitir frontend

## 📧 Notificações por Email

O anfitrião recebe email quando:

- Alguém confirma presença (RSVP)
- Alguém modifica sua confirmação
- Alguém cancela sua presença

Os emails são enviados via SendGrid e incluem:

- Nome do convidado
- Número de adultos e crianças
- Comentários especiais
- Link para visualizar todos os convidados

## ⚠️ Limitações e Observações

- **CEP:** Funciona apenas com CEPs brasileiros válidos (via ViaCEP)
- **WhatsApp:** Usado apenas como identificador único, sem integração real de API
- **Rate Limiting:** Armazenado em memória (será perdido ao reiniciar o servidor)
- **Banco de Dados:** SQLite não é recomendado para produção (usar PostgreSQL)

## 🐛 Solução de Problemas

### Erro: "ModuleNotFoundError"

```bash
# Certifique-se de que o ambiente virtual está ativado
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Reinstale as dependências
pip install -r requirements.txt
```

### Erro: "Invalid email format"

O validador de email está configurado com `check_deliverability=False`. Se ainda assim houver erro, verifique se o email tem formato válido (exemplo@dominio.com).

### Erro: "Invalid CEP"

Certifique-se de usar um CEP válido brasileiro no formato `12345-678` ou `12345678`.

### Emails não estão sendo enviados

1. Verifique se `SENDGRID_API_KEY` está corretamente configurado no `.env`
2. Confirme que você verificou um remetente no SendGrid
3. Atualize o email em `services/email_service.py` linha 8
4. Verifique os logs do console para erros

### Não consigo criar eventos no Swagger

1. Faça login primeiro em `/api/auth/login`
2. O Swagger mantém a sessão automaticamente no navegador
3. Se não funcionar, use Postman ou curl com cookies

## 📝 Notas para Avaliadores

Este projeto foi desenvolvido como parte da Sprint de Arquitetura de Software da Pós-Graduação em Engenharia de Software da PUC-Rio.

### Para rodar o projeto completo (Recomendado - Docker):

1. Clone ambos os repositórios (backend e frontend) no mesmo diretório pai:
   ```
   projeto/
   ├── backend/
   └── frontend/
   ```

2. Configure os arquivos `.env`:
   - `backend/.env` (copie de `.env.example` e configure as chaves)
   - `frontend/.env.local` (veja README do frontend)

3. A partir da pasta `frontend/`, rode:
   ```bash
   docker-compose up --build
   ```

4. Acesse:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000
   - Documentação Swagger: http://localhost:5000/api/docs

### Para rodar apenas o backend (Local):

1. Clone o repositório
2. Siga os passos de instalação da "Opção 2: Desenvolvimento Local"
3. Configure SendGrid (ou modifique `services/email_service.py` para imprimir no console)
4. Execute `python app.py`
5. Acesse a documentação em `http://localhost:5000/api/docs`

### 📧 Modo de Emails (Importante para Avaliadores):

**O sistema está configurado em MODO SIMULAÇÃO por padrão.**

Os emails NÃO são enviados de verdade. Em vez disso, o conteúdo dos emails aparece nos logs do console quando:
- Alguém confirma presença (RSVP)
- Alguém modifica confirmação
- Alguém cancela presença

**Para ver os emails simulados:**
1. Rode o projeto com Docker: `docker-compose up`
2. Observe os logs do backend: `docker-compose logs -f backend`
3. Ao fazer um RSVP, verá um log formatado como:
   ```
   ================================================================================
   📧 EMAIL SIMULADO - NOVO RSVP
   ================================================================================
   De: noreply@venha.app
   Para: host@example.com
   Assunto: Novo RSVP para Meu Evento
   ...
   ```

**Para habilitar SendGrid real em produção:**

Veja as instruções completas no arquivo `services/email_service.py` (comentários no final do arquivo).

## 📄 Licença

Este projeto foi desenvolvido para fins educacionais.

## 👤 Autora

Fernanda Franco

PUC-Rio - Pós-Graduação em Engenharia de Software

Sprint de Arquitetura de Software - 2025
