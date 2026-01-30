# backend/app.py
from flask import Flask, request, session, Response, redirect
from flask_cors import CORS
from flask_restx import Api, Resource, fields
from extensions import db, bcrypt, limiter
from models import Host, Event, Attendee
from email_validator import validate_email, EmailNotValidError
from services.email_service import (
    send_rsvp_notification,
    send_modification_notification,
    send_cancellation_notification,
)
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError
import os
import csv
import io

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
bcrypt.init_app(app)
limiter.init_app(app)
CORS(app, supports_credentials=True, origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")])

# API Swagger
api = Api(
    app,
    version="1.0",
    title="Venha API",
    description="API para criação e gerenciamento de convites de eventos",
    doc="/api/docs",
    catch_all_404s=False,
)

# Namespaces (grupos de endpoints)
auth_ns = api.namespace(
    "auth", description="Operações de autenticação", path="/api/auth"
)
events_ns = api.namespace(
    "events", description="Operações de gerenciamento de eventos", path="/api/events"
)
attendees_ns = api.namespace(
    "attendees", description="Operações de convidados/RSVP", path="/api/attendees"
)

# ============= MODELS =============
signup_model = api.model(
    "Signup",
    {
        "email": fields.String(
            required=True, description="Email do anfitrião", example="anfitriao@exemplo.com"
        ),
        "password": fields.String(
            required=True, description="Senha", example="senhaSegura123"
        ),
        "name": fields.String(
            required=True, description="Nome do anfitrião", example="João Silva"
        ),
        "whatsapp_number": fields.String(
            required=True, description="Número do WhatsApp", example="5521999999999"
        ),
    },
)

login_model = api.model(
    "Login",
    {
        "email": fields.String(
            required=True, description="Email do anfitrião", example="anfitriao@exemplo.com"
        ),
        "password": fields.String(
            required=True, description="Senha", example="senhaSegura123"
        ),
    },
)

event_create_model = api.model(
    "EventCreate",
    {
        "title": fields.String(
            required=True, description="Título do evento", example="Festa de Aniversário"
        ),
        "description": fields.String(
            description="Descrição do evento", example="Venha celebrar conosco!"
        ),
        "event_date": fields.String(
            required=True, description="Data do evento (AAAA-MM-DD)", example="2025-12-25"
        ),
        "start_time": fields.String(
            required=True, description="Horário de início (HH:MM)", example="18:00"
        ),
        "end_time": fields.String(description="Horário de término (HH:MM)", example="22:00"),
        "address_cep": fields.String(
            description="CEP brasileiro (opcional)", example="22040-020"
        ),
        "address_full": fields.String(
            required=True,
            description="Endereço completo",
            example="Av. Atlântica, 1702, Copacabana, Rio de Janeiro - RJ, Brasil",
        ),
        "allow_modifications": fields.Boolean(
            description="Permitir convidados modificarem RSVP", default=True, example=True
        ),
        "allow_cancellations": fields.Boolean(
            description="Permitir convidados cancelarem RSVP", default=True, example=True
        ),
    },
)

event_update_model = api.model(
    "EventUpdate",
    {
        "title": fields.String(
            description="Título do evento", example="Festa de Aniversário (Atualizado)"
        ),
        "description": fields.String(description="Descrição do evento"),
        "event_date": fields.String(
            description="Data do evento (AAAA-MM-DD)", example="2024-12-25"
        ),
        "start_time": fields.String(description="Horário de início (HH:MM)", example="18:00"),
        "end_time": fields.String(description="Horário de término (HH:MM)", example="23:00"),
        "address_cep": fields.String(description="CEP"),
        "address_full": fields.String(description="Endereço completo"),
        "allow_modifications": fields.Boolean(
            description="Permitir convidados modificarem RSVP"
        ),
        "allow_cancellations": fields.Boolean(
            description="Permitir convidados cancelarem RSVP"
        ),
    },
)

rsvp_model = api.model(
    "RSVP",
    {
        "event_slug": fields.String(
            required=True, description="Slug do evento", example="abc123"
        ),
        "whatsapp_number": fields.String(
            required=True, description="WhatsApp do convidado", example="5521988888888"
        ),
        "name": fields.String(
            required=True, description="Nome do convidado", example="Maria Silva"
        ),
        "num_adults": fields.Integer(
            required=True, description="Número de adultos", example=2
        ),
        "num_children": fields.Integer(description="Número de crianças", example=1),
        "comments": fields.String(
            description="Acomodações especiais ou alergias",
            example="Refeição vegetariana necessária",
        ),
    },
)

rsvp_update_model = api.model(
    "RSVPUpdate",
    {
        "whatsapp_number": fields.String(
            required=True,
            description="WhatsApp do convidado para identificação",
            example="5521988888888",
        ),
        "name": fields.String(description="Nome atualizado", example="Maria Silva"),
        "num_adults": fields.Integer(description="Número atualizado de adultos", example=3),
        "num_children": fields.Integer(
            description="Número atualizado de crianças", example=2
        ),
        "comments": fields.String(
            description="Comentários atualizados", example="Agora preciso de refeição vegana"
        ),
    },
)

rsvp_cancel_model = api.model(
    "RSVPCancel",
    {
        "event_slug": fields.String(
            required=True, description="Slug do evento", example="festa-aniversario-abc123"
        ),
        "whatsapp_number": fields.String(
            required=True, description="WhatsApp do convidado", example="5521988888888"
        ),
        "reason": fields.String(
            description="Motivo do cancelamento", example="Não poderei comparecer devido a um conflito"
        ),
    },
)

attendee_update_model = api.model(
    "AttendeeUpdate",
    {
        "name": fields.String(description="Nome do convidado", example="Maria Silva"),
        "num_adults": fields.Integer(description="Número de adultos", example=2),
        "num_children": fields.Integer(description="Número de crianças", example=1),
        "comments": fields.String(description="Comentários", example="Vegetariano"),
    },
)

attendee_find_model = api.model(
    "AttendeeFind",
    {
        "event_slug": fields.String(
            required=True, description="Slug do evento", example="festa-aniversario-abc123"
        ),
        "whatsapp_number": fields.String(
            required=True, description="Número do WhatsApp", example="5521999999999"
        ),
    },
)

attendee_modify_model = api.model(
    "AttendeeModify",
    {
        "event_slug": fields.String(required=True, description="Slug do evento"),
        "whatsapp_number": fields.String(required=True, description="Número do WhatsApp"),
        "name": fields.String(description="Novo nome"),
        "num_adults": fields.Integer(description="Novo número de adultos"),
        "num_children": fields.Integer(description="Novo número de crianças"),
        "comments": fields.String(description="Novos comentários"),
    },
)


# ============= AUTH ROUTES =============
@auth_ns.route("/signup")
class Signup(Resource):
    @auth_ns.expect(signup_model)
    @auth_ns.response(201, "Anfitrião criado com sucesso")
    @auth_ns.response(400, "Entrada inválida")
    @auth_ns.response(409, "Email já cadastrado")
    def post(self):
        """Criar nova conta de anfitrião"""
        data = request.get_json()
        required = ["email", "password", "name", "whatsapp_number"]
        if not all(field in data for field in required):
            api.abort(400, "Preencha todos os campos obrigatórios: email, senha, nome e WhatsApp")

        try:
            email_info = validate_email(data["email"], check_deliverability=False)
            email = email_info.normalized
        except EmailNotValidError:
            api.abort(400, "Email inválido. Verifique o formato (exemplo@dominio.com)")

        if Host.query.filter_by(email=email).first():
            api.abort(409, "Este email já está cadastrado. Faça login ou use outro email")

        password_hash = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
        host = Host(
            email=email,
            password_hash=password_hash,
            name=data["name"],
            whatsapp_number=data["whatsapp_number"],
        )
        db.session.add(host)
        db.session.commit()
        session["host_id"] = host.id

        return {
            "message": "Account created successfully",
            "host": {
                "id": host.id,
                "email": host.email,
                "name": host.name,
                "whatsapp_number": host.whatsapp_number,
            },
        }, 201


@auth_ns.route("/login")
class Login(Resource):
    @auth_ns.expect(login_model)
    @auth_ns.response(200, "Login realizado com sucesso")
    @auth_ns.response(400, "Credenciais ausentes")
    @auth_ns.response(401, "Credenciais inválidas")
    def post(self):
        """Fazer login como anfitrião"""
        data = request.get_json()
        if not data.get("email") or not data.get("password"):
            api.abort(400, "Email e senha são obrigatórios")

        host = Host.query.filter_by(email=data["email"]).first()
        if not host or not bcrypt.check_password_hash(
            host.password_hash, data["password"]
        ):
            api.abort(401, "Email ou senha incorretos")

        session["host_id"] = host.id
        return {
            "message": "Login successful",
            "host": {
                "id": host.id,
                "email": host.email,
                "name": host.name,
                "whatsapp_number": host.whatsapp_number,
            },
        }, 200


@auth_ns.route("/logout")
class Logout(Resource):
    @auth_ns.response(200, "Logout realizado com sucesso")
    def post(self):
        """Fazer logout do anfitrião atual"""
        session.pop("host_id", None)
        return {"message": "Logged out successfully"}, 200


@auth_ns.route("/me")
class CurrentHost(Resource):
    @auth_ns.response(200, "Sucesso")
    @auth_ns.response(401, "Não autenticado")
    def get(self):
        """Obter anfitrião autenticado atual"""
        if "host_id" not in session:
            api.abort(401, "Você precisa fazer login para acessar esta página")

        host = Host.query.get(session["host_id"])
        if not host:
            api.abort(404, "Usuário não encontrado. Faça login novamente")

        return {
            "host": {
                "id": host.id,
                "email": host.email,
                "name": host.name,
                "whatsapp_number": host.whatsapp_number,
            }
        }, 200


# ============= EVENT ROUTES =============
@events_ns.route("/create")
class CreateEvent(Resource):
    @events_ns.expect(event_create_model)
    @events_ns.response(201, "Evento criado com sucesso")
    @events_ns.response(400, "Entrada inválida")
    @events_ns.response(401, "Não autenticado")
    def post(self):
        """Criar novo evento (requer autenticação)"""
        if "host_id" not in session:
            api.abort(
                401, "Faça login para criar eventos"
            )

        data = request.get_json()

        # Campos obrigatórios
        required = ["title", "event_date", "start_time", "address_full"]
        if not all(field in data for field in required):
            api.abort(
                400,
                "Preencha todos os campos obrigatórios: título, data, horário e endereço",
            )

        # Parse dates/times
        try:
            event_date = datetime.strptime(data["event_date"], "%Y-%m-%d").date()
            start_time = datetime.strptime(data["start_time"], "%H:%M").time()
            end_time = (
                datetime.strptime(data["end_time"], "%H:%M").time()
                if data.get("end_time")
                else None
            )
        except ValueError:
            api.abort(400, "Formato de data/hora inválido. Use AAAA-MM-DD para data e HH:MM para horário")

        event = Event(
            host_id=session["host_id"],
            title=data["title"],
            description=data.get("description", ""),
            event_date=event_date,
            start_time=start_time,
            end_time=end_time,
            address_cep=data.get("address_cep", ""),
            address_full=data["address_full"],
            allow_modifications=data.get("allow_modifications", True),
            allow_cancellations=data.get("allow_cancellations", True),
        )

        db.session.add(event)
        db.session.commit()

        return {
            "message": "Event created successfully",
            "event": {
                "id": event.id,
                "slug": event.slug,
                "title": event.title,
                "invite_url": f"/invite/{event.slug}",
            },
        }, 201


@events_ns.route("/my-events")
class MyEvents(Resource):
    @events_ns.response(200, "Sucesso")
    @events_ns.response(401, "Não autenticado")
    def get(self):
        """Obter todos os eventos do anfitrião logado"""
        if "host_id" not in session:
            api.abort(401, "Faça login para ver seus eventos")

        events = (
            Event.query.filter_by(host_id=session["host_id"])
            .order_by(Event.event_date.desc())
            .all()
        )

        return {
            "events": [
                {
                    "id": event.id,
                    "slug": event.slug,
                    "title": event.title,
                    "description": event.description,
                    "event_date": event.event_date.isoformat(),
                    "start_time": event.start_time.strftime("%H:%M"),
                    "end_time": (
                        event.end_time.strftime("%H:%M") if event.end_time else None
                    ),
                    "address_cep": event.address_cep,
                    "address_full": event.address_full,
                    "allow_modifications": bool(event.allow_modifications),
                    "allow_cancellations": bool(event.allow_cancellations),
                    "attendee_count": len(
                        [a for a in event.attendees if a.status == "confirmed"]
                    ),
                    "total_adults": sum(
                        a.num_adults for a in event.attendees if a.status == "confirmed"
                    ),
                    "total_children": sum(
                        a.num_children
                        for a in event.attendees
                        if a.status == "confirmed"
                    ),
                }
                for event in events
            ]
        }, 200


@events_ns.route("/<string:slug>")
class EventBySlug(Resource):
    @events_ns.response(200, "Sucesso")
    @events_ns.response(404, "Evento não encontrado")
    def get(self, slug):
        """Obter detalhes do evento por slug (para convidados visualizando o convite)"""
        event = Event.query.filter_by(slug=slug).first()
        if not event:
            api.abort(404, "Convite não encontrado. Verifique o link")

        return {
            "event": {
                "id": event.id,
                "slug": event.slug,
                "title": event.title,
                "description": event.description,
                "event_date": event.event_date.isoformat(),
                "start_time": event.start_time.strftime("%H:%M"),
                "end_time": (
                    event.end_time.strftime("%H:%M") if event.end_time else None
                ),
                "address_full": event.address_full,
                "allow_modifications": bool(event.allow_modifications),
                "allow_cancellations": bool(event.allow_cancellations),
                "host_name": event.host.name,
                "host_whatsapp": event.host.whatsapp_number,
            }
        }, 200


@events_ns.route("/<int:event_id>/attendees")
class EventAttendees(Resource):
    @events_ns.response(200, "Sucesso")
    @events_ns.response(401, "Não autenticado")
    @events_ns.response(403, "Não autorizado")
    @events_ns.response(404, "Evento não encontrado")
    def get(self, event_id):
        """Obter todos os convidados de um evento (apenas anfitrião)"""
        if "host_id" not in session:
            api.abort(401, "Faça login para ver os convidados")

        event = Event.query.get(event_id)
        if not event:
            api.abort(404, "Evento não encontrado")

        if event.host_id != session["host_id"]:
            api.abort(403, "Você não tem permissão para acessar este evento")

        attendees = Attendee.query.filter_by(event_id=event_id).all()

        return {
            "attendees": [
                {
                    "id": attendee.id,
                    "name": attendee.name,
                    "whatsapp_number": attendee.whatsapp_number,
                    "num_adults": attendee.num_adults,
                    "num_children": attendee.num_children,
                    "comments": attendee.comments,
                    "status": attendee.status,
                    "rsvp_date": attendee.rsvp_date.isoformat(),
                }
                for attendee in attendees
            ]
        }, 200


@events_ns.route("/<int:event_id>/attendees/<int:attendee_id>")
class ManageAttendee(Resource):
    @events_ns.expect(attendee_update_model)
    @events_ns.response(200, "Convidado atualizado")
    @events_ns.response(401, "Não autenticado")
    @events_ns.response(403, "Não autorizado")
    @events_ns.response(404, "Não encontrado")
    def put(self, event_id, attendee_id):
        """Atualizar convidado (apenas anfitrião)"""
        if "host_id" not in session:
            api.abort(401, "Faça login para editar convidados")

        event = Event.query.get(event_id)
        if not event or event.host_id != session["host_id"]:
            api.abort(403, "Você não tem permissão para editar este convidado")

        attendee = Attendee.query.get(attendee_id)
        if not attendee or attendee.event_id != event_id:
            api.abort(404, "Convidado não encontrado")

        data = request.get_json()
        if "name" in data:
            attendee.name = data["name"]
        if "num_adults" in data:
            attendee.num_adults = data["num_adults"]
        if "num_children" in data:
            attendee.num_children = data["num_children"]
        if "comments" in data:
            attendee.comments = data["comments"]

        db.session.commit()
        return {"message": "Attendee updated successfully"}, 200

    @events_ns.response(200, "Convidado deletado")
    @events_ns.response(401, "Não autenticado")
    @events_ns.response(403, "Não autorizado")
    @events_ns.response(404, "Não encontrado")
    def delete(self, event_id, attendee_id):
        """Deletar convidado (apenas anfitrião)"""
        if "host_id" not in session:
            api.abort(401, "Faça login para deletar convidados")

        event = Event.query.get(event_id)
        if not event or event.host_id != session["host_id"]:
            api.abort(403, "Você não tem permissão para deletar este convidado")

        attendee = Attendee.query.get(attendee_id)
        if not attendee or attendee.event_id != event_id:
            api.abort(404, "Convidado não encontrado")

        db.session.delete(attendee)
        db.session.commit()
        return {"message": "Attendee deleted successfully"}, 200


@events_ns.route("/<int:event_id>/export-csv")
class ExportAttendees(Resource):
    @events_ns.response(200, "Arquivo CSV")
    @events_ns.response(401, "Não autenticado")
    @events_ns.response(403, "Não autorizado")
    def get(self, event_id):
        """Exportar convidados como CSV (apenas anfitrião)"""
        if "host_id" not in session:
            api.abort(401, "Faça login para exportar a lista de convidados")

        event = Event.query.get(event_id)
        if not event or event.host_id != session["host_id"]:
            api.abort(403, "Você não tem permissão para exportar convidados deste evento")

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "Name",
                "WhatsApp",
                "Adults",
                "Children",
                "Comments",
                "Status",
                "RSVP Date",
            ]
        )

        for attendee in event.attendees:
            writer.writerow(
                [
                    attendee.name,
                    attendee.whatsapp_number,
                    attendee.num_adults,
                    attendee.num_children,
                    attendee.comments,
                    attendee.status,
                    attendee.rsvp_date.strftime("%Y-%m-%d %H:%M"),
                ]
            )

        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=event_{event_id}_attendees.csv"
            },
        )


@events_ns.route("/<int:event_id>")
class EventManagement(Resource):
    @events_ns.expect(event_update_model)
    @events_ns.response(200, "Evento atualizado")
    @events_ns.response(401, "Não autenticado")
    @events_ns.response(403, "Não autorizado")
    @events_ns.response(404, "Evento não encontrado")
    def put(self, event_id):
        """Atualizar evento (apenas anfitrião)"""
        if "host_id" not in session:
            api.abort(401, "Faça login para editar eventos")

        event = Event.query.get(event_id)

        if not event:
            api.abort(404, "Evento não encontrado")

        if event.host_id != session["host_id"]:
            api.abort(403, "Você não tem permissão para editar este evento")

        data = request.get_json()

        try:
            # Atualizar campos básicos
            if "title" in data:
                event.title = data["title"]

            if "description" in data:
                event.description = data["description"]

            if "event_date" in data:
                event.event_date = datetime.strptime(
                    data["event_date"], "%Y-%m-%d"
                ).date()

            if "start_time" in data:
                event.start_time = datetime.strptime(data["start_time"], "%H:%M").time()

            if "end_time" in data:
                if data["end_time"]:
                    event.end_time = datetime.strptime(data["end_time"], "%H:%M").time()
                else:
                    event.end_time = None

            if "address_cep" in data:
                event.address_cep = data["address_cep"]

            if "address_full" in data:
                event.address_full = data["address_full"]

            if "allow_modifications" in data:
                event.allow_modifications = data["allow_modifications"]

            if "allow_cancellations" in data:
                event.allow_cancellations = data["allow_cancellations"]

            db.session.commit()

            return {
                "message": "Event updated successfully",
                "event": {"id": event.id, "slug": event.slug, "title": event.title},
            }, 200

        except (ValueError, SQLAlchemyError):
            db.session.rollback()
            api.abort(500, "Erro ao atualizar evento. Verifique os dados e tente novamente")

    @events_ns.response(200, "Evento deletado")
    @events_ns.response(401, "Não autenticado")
    @events_ns.response(403, "Não autorizado")
    @events_ns.response(404, "Evento não encontrado")
    def delete(self, event_id):
        """Deletar evento (apenas anfitrião)"""
        if "host_id" not in session:
            api.abort(401, "Faça login para deletar eventos")

        event = Event.query.get(event_id)

        if not event:
            api.abort(404, "Evento não encontrado")

        if event.host_id != session["host_id"]:
            api.abort(403, "Você não tem permissão para deletar este evento")

        try:
            # Deletar todos os convidados primeiro (cascade deve lidar com isso, mas sendo explícito)
            Attendee.query.filter_by(event_id=event_id).delete()

            # Deletar evento
            db.session.delete(event)
            db.session.commit()

            return {"message": "Event deleted successfully"}, 200

        except SQLAlchemyError:
            db.session.rollback()
            api.abort(500, "Erro ao deletar evento. Tente novamente")


@events_ns.route("/<int:event_id>/duplicate")
class DuplicateEvent(Resource):
    @events_ns.response(201, "Evento duplicado")
    @events_ns.response(401, "Não autenticado")
    @events_ns.response(403, "Não autorizado")
    @events_ns.response(404, "Evento não encontrado")
    def post(self, event_id):
        """Duplicar um evento existente"""
        if "host_id" not in session:
            api.abort(401, "Faça login para duplicar eventos")

        original_event = Event.query.get(event_id)

        if not original_event:
            api.abort(404, "Evento não encontrado")

        if original_event.host_id != session["host_id"]:
            api.abort(403, "Você não tem permissão para duplicar este evento")

        try:
            # Criar novo evento com os mesmos dados
            new_event = Event(
                host_id=session["host_id"],
                title=f"{original_event.title} (Cópia)",
                description=original_event.description,
                event_date=original_event.event_date,
                start_time=original_event.start_time,
                end_time=original_event.end_time,
                address_cep=original_event.address_cep,
                address_full=original_event.address_full,
                allow_modifications=original_event.allow_modifications,
                allow_cancellations=original_event.allow_cancellations,
            )

            db.session.add(new_event)
            db.session.commit()

            return {
                "message": "Event duplicated successfully",
                "event": {
                    "id": new_event.id,
                    "slug": new_event.slug,
                    "title": new_event.title,
                },
            }, 201

        except SQLAlchemyError:
            db.session.rollback()
            api.abort(500, "Erro ao duplicar evento. Tente novamente")


# ============= ATTENDEE ROUTES =============
@attendees_ns.route("/rsvp")
class RSVPResource(Resource):
    @attendees_ns.expect(rsvp_model)
    @attendees_ns.response(201, "Confirmação realizada com sucesso")
    @attendees_ns.response(400, "Entrada inválida ou já confirmado")
    @attendees_ns.response(404, "Evento não encontrado")
    @limiter.limit("30 per minute")
    def post(self):
        """Criar confirmação de presença para um evento"""
        data = request.get_json()
        required = ["event_slug", "whatsapp_number", "name", "num_adults"]
        if not all(field in data for field in required):
            api.abort(400, "Preencha todos os campos obrigatórios: nome, WhatsApp e número de adultos")

        event = Event.query.filter_by(slug=data["event_slug"]).first()
        if not event:
            api.abort(404, "Evento não encontrado. Verifique o link do convite")

        existing = Attendee.query.filter_by(
            event_id=event.id, whatsapp_number=data["whatsapp_number"]
        ).first()
        if existing:
            api.abort(400, "Você já confirmou presença neste evento")

        attendee = Attendee(
            event_id=event.id,
            whatsapp_number=data["whatsapp_number"],
            name=data["name"],
            num_adults=data["num_adults"],
            num_children=data.get("num_children", 0),
            comments=data.get("comments", ""),
        )
        db.session.add(attendee)
        db.session.commit()

        send_rsvp_notification(event, attendee)

        return {"message": "RSVP successful", "attendee_id": attendee.id}, 201


@attendees_ns.route("/find")
class FindAttendee(Resource):
    @attendees_ns.expect(attendee_find_model)
    @attendees_ns.response(200, "Convidado encontrado")
    @attendees_ns.response(404, "Convidado não encontrado")
    def post(self):
        """Buscar convidado por WhatsApp e slug do evento"""
        data = request.get_json()

        event_slug = data.get("event_slug")
        whatsapp_number = data.get("whatsapp_number")

        if not event_slug or not whatsapp_number:
            api.abort(400, "Link do evento e número de WhatsApp são obrigatórios")

        # Buscar evento
        event = Event.query.filter_by(slug=event_slug).first()
        if not event:
            api.abort(404, "Evento não encontrado. Verifique o link")

        # Buscar convidado
        attendee = Attendee.query.filter_by(
            event_id=event.id, whatsapp_number=whatsapp_number
        ).first()

        if not attendee:
            api.abort(404, "Nenhuma confirmação encontrada para este WhatsApp. Verifique o número digitado")

        return {
            "attendee": {
                "id": attendee.id,
                "name": attendee.name,
                "whatsapp_number": attendee.whatsapp_number,
                "num_adults": attendee.num_adults,
                "num_children": attendee.num_children,
                "comments": attendee.comments,
                "status": attendee.status,
            },
            "event": {
                "title": event.title,
                "event_date": event.event_date.isoformat(),
                "allow_modifications": bool(event.allow_modifications),
                "allow_cancellations": bool(event.allow_cancellations),
            },
        }, 200


@attendees_ns.route("/modify")
class ModifyRSVP(Resource):
    @attendees_ns.expect(attendee_modify_model)
    @attendees_ns.response(200, "Confirmação modificada")
    @attendees_ns.response(403, "Modificações não permitidas")
    @attendees_ns.response(404, "Confirmação não encontrada")
    def put(self):
        """Modificar confirmação de presença existente"""
        data = request.get_json()

        event_slug = data.get("event_slug")
        whatsapp_number = data.get("whatsapp_number")

        if not event_slug or not whatsapp_number:
            api.abort(400, "Link do evento e número de WhatsApp são obrigatórios")

        # Buscar evento
        event = Event.query.filter_by(slug=event_slug).first()
        if not event:
            api.abort(404, "Evento não encontrado")

        # Verificar se modificações são permitidas
        if not event.allow_modifications:
            api.abort(403, "O anfitrião não permitiu modificações para este evento")

        # Buscar convidado
        attendee = Attendee.query.filter_by(
            event_id=event.id, whatsapp_number=whatsapp_number
        ).first()

        if not attendee:
            api.abort(404, "Confirmação não encontrada. Verifique o número de WhatsApp")

        # Atualizar campos
        if "name" in data:
            attendee.name = data["name"]
        if "num_adults" in data:
            attendee.num_adults = data["num_adults"]
        if "num_children" in data:
            attendee.num_children = data["num_children"]
        if "comments" in data:
            attendee.comments = data["comments"]

        # Se foi cancelado, reativar
        if attendee.status == "cancelled":
            attendee.status = "confirmed"

        db.session.commit()
        send_modification_notification(event, attendee)

        return {
            "message": "RSVP updated successfully",
            "attendee": {
                "id": attendee.id,
                "name": attendee.name,
                "num_adults": attendee.num_adults,
                "num_children": attendee.num_children,
                "comments": attendee.comments,
                "status": attendee.status,
            },
        }, 200


@attendees_ns.route("/cancel")
class CancelRSVP(Resource):
    @attendees_ns.expect(rsvp_cancel_model)
    @attendees_ns.response(200, "Confirmação cancelada")
    @attendees_ns.response(403, "Cancelamentos não permitidos")
    @attendees_ns.response(404, "Confirmação não encontrada")
    def post(self):
        """Cancelar confirmação de presença existente"""
        data = request.get_json()

        event_slug = data.get("event_slug")
        whatsapp_number = data.get("whatsapp_number")

        if not event_slug or not whatsapp_number:
            api.abort(400, "Link do evento e número de WhatsApp são obrigatórios")

        # Buscar evento
        event = Event.query.filter_by(slug=event_slug).first()
        if not event:
            api.abort(404, "Evento não encontrado")

        # Verificar se cancelamentos são permitidos
        if not event.allow_cancellations:
            api.abort(403, "O anfitrião não permitiu cancelamentos para este evento")

        # Buscar convidado
        attendee = Attendee.query.filter_by(
            event_id=event.id, whatsapp_number=whatsapp_number
        ).first()

        if not attendee:
            api.abort(404, "Confirmação não encontrada. Verifique o número de WhatsApp")

        # Cancelar RSVP
        attendee.status = "cancelled"
        db.session.commit()
        send_cancellation_notification(event, attendee, data.get("reason", ""))

        return {"message": "RSVP cancelled successfully"}, 200


# Manter blueprints originais para compatibilidade retroativa
# Blueprints removidos - todos os endpoints agora usam Flask-RESTX


# Redirecionamento raiz - sobrescrever rota raiz do Flask-RESTX
def redirect_root():
    return redirect("/api/docs")


# Sobrescrever o endpoint raiz do Flask-RESTX
app.view_functions["root"] = redirect_root


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
