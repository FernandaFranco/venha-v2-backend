# Venha - Backend (Flask)

API REST para o sistema de convites online Venha, permitindo criação e gerenciamento de eventos com funcionalidade de RSVP.

## 📋 Sobre o Projeto

O sistema Venha permite que anfitriões criem eventos e gerem um link de convite para compartilhar, e assim gerenciar confirmações de presença. Os convidados podem confirmar presença, modificar ou cancelar suas respostas através desse link.

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

- Visualização de detalhes do evento via link
- Confirmação de presença (RSVP)
- Informação de número de adultos e crianças
- Comentários sobre necessidades especiais ou alergias
- Modificação de confirmação de presença
- Cancelamento de presença com motivo opcional

## 🏗️ Arquitetura da Aplicação

![Diagrama de Arquitetura](docs/architecture-diagram.png)

<details>
<summary>💡 Ver código Mermaid (clique para expandir)</summary>

```mermaid
graph LR
    A["🐳<br/>Frontend<br/>Next.js"] <-->|REST/JSON| B["🐳<br/>Backend<br/>Flask API"]
    B <-->|SQL| C[("Database<br/>SQLite<br/>(local)")]

    A <-.->|REST| D[ViaCEP]
    A <-.->|REST| E[Google Maps API]
    A <-.->|REST| F[WeatherAPI]

    B <-.->|REST| G[Google Geocoding API]
    B <-.->|REST<br/>fallback| H[Nominatim OSM]

    style A fill:#b3e0ff,stroke:#333,stroke-width:2px,color:#000
    style B fill:#b3e0ff,stroke:#333,stroke-width:2px,color:#000
    style C fill:#b3e0ff,stroke:#333,stroke-width:2px,color:#000
    style D fill:#ffe6b3,stroke:#333,stroke-width:2px,color:#000
    style E fill:#ffe6b3,stroke:#333,stroke-width:2px,color:#000
    style F fill:#ffe6b3,stroke:#333,stroke-width:2px,color:#000
    style G fill:#ffe6b3,stroke:#333,stroke-width:2px,color:#000
    style H fill:#ffe6b3,stroke:#333,stroke-width:2px,color:#000
```

</details>

**Legenda:**

- **Linha contínua (←→):** Comunicação obrigatória
- **Linha tracejada (←-→):** Comunicação opcional ou fallback
- **🐳 (Docker):** Container Docker separado
- **Azul:** Módulos implementados no projeto
- **Amarelo:** APIs externas

**Componentes:**

- **Frontend (Next.js) 🐳:** Interface web responsiva, páginas públicas e privadas, autenticação via session cookies
- **Backend (Flask) 🐳:** API REST com lógica de negócio, validações, documentação Swagger automática
- **Database (SQLite):** Arquivo local montado via volume Docker para persistência de dados (hosts, eventos e RSVPs)
- **APIs Externas Frontend:** ViaCEP (endereços), Google Maps (mapas), WeatherAPI (clima)
- **APIs Externas Backend:** Google Geocoding (coordenadas) com fallback Nominatim
- **Notificações:** Emails simulados no console (sem envio real)

## 🌐 APIs Externas

O backend integra-se com **1 API externa** principal (Google Geocoding) com fallback para Nominatim (OpenStreetMap).

### Google Geocoding API

**URL:** https://developers.google.com/maps/documentation/geocoding

**Propósito:** Conversão de endereços completos em coordenadas geográficas (latitude/longitude) para exibição de mapas no frontend.

**Licença/Custo:**

- Plano gratuito com crédito mensal de $200 USD
- Primeiras 40.000 requisições/mês são gratuitas
- Licença: Proprietária (Google Cloud Platform)

**Uso no Backend:**

- Arquivo: `services/geocoding_service.py`
- Endpoints que utilizam:

  - `POST /api/events/geocode` - Endpoint dedicado para geocodificar o endereço antes da criação do evento (mapa para conferência do anfitrião)
  - `POST /api/events/create` - Geocodifica automaticamente o endereço ao criar um evento e persiste as coordenadas

- Funcionalidade: Converter endereço textual em coordenadas lat/lng. Coordenadas são necessárias para exibir o endereço do evento no mapa (Google Maps) na página de convite.

**Endpoints utilizados:**

- `GET https://maps.googleapis.com/maps/api/geocode/json`
  - Parâmetros: `address` (endereço completo), `key` (API key)
  - Retorna: `results[0].geometry.location` (lat, lng)

**Fallback - Nominatim (OpenStreetMap):**

Se a chave do Google não estiver configurada ou falhar, o sistema usa Nominatim como alternativa:

- **URL:** https://nominatim.openstreetmap.org/
- **Licença:** Open Data Commons Open Database License (ODbL)
- **Sem custo:** Completamente gratuito
- **Limitações:**
  - Taxa de 1 requisição por segundo
  - **Precisão limitada com endereços brasileiros** (menor cobertura e acurácia)

**Endpoints utilizados:**

- `GET https://nominatim.openstreetmap.org/search`
  - Parâmetros: `q` (endereço), `format=json`, `limit=1`
  - Retorna: `[0].lat`, `[0].lon`

**Tratamento de Erro:**

- Se ambas as APIs falharem, salva evento sem coordenadas
- Frontend exibe evento normalmente, mas sem mapa
- Comportamento gracioso: sistema continua funcional

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
├── app.py                      # Aplicação principal com todas as rotas e documentação Swagger
├── extensions.py               # Inicialização de extensões (db, bcrypt, limiter)
├── models.py                   # Modelos do banco de dados (Host, Event, Attendee)
├── services/                   # Serviços externos
│   ├── __init__.py
│   ├── email_service.py       # Simulação de emails
│   ├── geocoding_service.py   # Integração Google Geocoding/Nominatim
│   └── cep_service.py         # Integração ViaCEP
├── utils/                      # Utilitários
├── requirements.txt            # Dependências Python
├── .env.example               # Template de variáveis de ambiente
├── Dockerfile                 # Dockerfile do backend
└── .gitignore                 # Arquivos ignorados pelo Git
```

## 🚀 Como Rodar o Projeto (Docker)

Esta é a forma recomendada de rodar o projeto completo (frontend + backend). Este método garante que todas as dependências sejam instaladas corretamente e que ambos os serviços se comuniquem adequadamente.

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

### Passo 2: Configurar Backend (.env)

Primeiro, configure o backend:

1. Navegue até a pasta do backend e copie o arquivo de exemplo:

```bash
cd backend
cp .env.example .env
```

2. Edite o arquivo `backend/.env`:

```bash
# Obrigatórias
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=sua-chave-secreta-aqui    # Gere com: python3 -c "import secrets; print(secrets.token_hex(32))"
DATABASE_URL=sqlite:///invitations.db

# Necessária para endereços brasileiros (usa Nominatim como fallback, mas com limitações)
GOOGLE_GEOCODING_API_KEY=sua-chave-google-aqui

# Frontend URL
FRONTEND_URL=http://localhost:3000
```

**Como obter GOOGLE_GEOCODING_API_KEY:**

1. Acesse [Google Cloud Console](https://console.cloud.google.com)
2. Crie um projeto ou selecione um existente
3. Ative a API "Geocoding API"
4. Vá em "Credenciais" → "Criar credenciais" → "Chave de API"
5. Copie a chave gerada

> **Nota para Avaliadores:** A chave de API do Google Geocoding é a mesma do Maps e será disponibilizada de modo privado ao enviar as URLs para avaliação.

### Passo 3: Configurar Frontend (.env.local)

Agora configure o frontend:

```bash
cd ../frontend
cp .env.local.example .env.local
```

Edite o arquivo `frontend/.env.local` e configure as chaves de API necessárias (Google Maps e WeatherAPI).

Veja o README do frontend para instruções completas sobre como obter as chaves de API.

> **Nota para Avaliadores:** As chaves de API seram disponibilizadas de modo privado ao enviar as URLs para avaliação.

### Passo 4: Rodar com Docker Compose

**IMPORTANTE:** O `docker-compose.yml` está localizado na pasta `frontend/`. Certifique-se de estar na pasta `frontend/`:

```bash
cd ../frontend  # Se ainda não estiver na pasta frontend
docker-compose up --build
```

**O que acontece:**

- O Docker baixa as imagens base necessárias
- Instala todas as dependências do backend (Python/Flask)
- Instala todas as dependências do frontend (Next.js)
- Inicia ambos os serviços
- Backend fica disponível na porta 5000
- Frontend fica disponível na porta 3000

**Primeira execução:** Pode levar alguns minutos para baixar as imagens e instalar tudo.

### Passo 5: Acessar a Aplicação

Aguarde até ver as mensagens indicando que os serviços estão prontos. Então acesse:

- **Frontend (Interface):** http://localhost:3000
- **Backend API:** http://localhost:5000 (redireciona automaticamente para a documentação Swagger)
- **Documentação Swagger:** http://localhost:5000/api/docs

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

## 📄 Licença

Este projeto foi desenvolvido para fins educacionais.

## 👤 Autora

Fernanda Franco

PUC-Rio - Pós-Graduação em Engenharia de Software

Sprint de Arquitetura de Software - 2025
