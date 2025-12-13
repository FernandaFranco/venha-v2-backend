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
from services.geocoding_service import geocode_address
from datetime import datetime
from dotenv import load_dotenv
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
CORS(app, supports_credentials=True, origins=["http://localhost:3000"])

# Swagger API
api = Api(
    app,
    version="1.0",
    title="Venha API",
    description="API para criação e gerenciamento de convites de eventos",
    doc="/api/docs",
    catch_all_404s=False,
)

# Namespaces
auth_ns = api.namespace(
    "auth", description="Authentication operations", path="/api/auth"
)
events_ns = api.namespace(
    "events", description="Event management operations", path="/api/events"
)
attendees_ns = api.namespace(
    "attendees", description="Attendee/RSVP operations", path="/api/attendees"
)

# ============= MODELS =============
signup_model = api.model(
    "Signup",
    {
        "email": fields.String(
            required=True, description="Host email", example="host@example.com"
        ),
        "password": fields.String(
            required=True, description="Password", example="securepass123"
        ),
        "name": fields.String(
            required=True, description="Host name", example="John Doe"
        ),
        "whatsapp_number": fields.String(
            required=True, description="WhatsApp number", example="5521999999999"
        ),
    },
)

login_model = api.model(
    "Login",
    {
        "email": fields.String(
            required=True, description="Host email", example="host@example.com"
        ),
        "password": fields.String(
            required=True, description="Password", example="securepass123"
        ),
    },
)

event_create_model = api.model(
    "EventCreate",
    {
        "title": fields.String(
            required=True, description="Event title", example="Birthday Party"
        ),
        "description": fields.String(
            description="Event description", example="Join us for a celebration!"
        ),
        "event_date": fields.String(
            required=True, description="Event date (YYYY-MM-DD)", example="2025-12-25"
        ),
        "start_time": fields.String(
            required=True, description="Start time (HH:MM)", example="18:00"
        ),
        "end_time": fields.String(description="End time (HH:MM)", example="22:00"),
        "address_cep": fields.String(
            description="Brazilian CEP (optional)", example="22040-020"
        ),
        "address_full": fields.String(
            required=True,
            description="Full address (coordinates will be automatically geocoded)",
            example="Av. Atlântica, 1702, Copacabana, Rio de Janeiro - RJ, Brasil",
        ),
        "allow_modifications": fields.Boolean(
            description="Allow guests to modify RSVP", default=True, example=True
        ),
        "allow_cancellations": fields.Boolean(
            description="Allow guests to cancel RSVP", default=True, example=True
        ),
    },
)

event_update_model = api.model(
    "EventUpdate",
    {
        "title": fields.String(
            description="Event title", example="Festa de Aniversário (Atualizado)"
        ),
        "description": fields.String(description="Event description"),
        "event_date": fields.String(
            description="Event date (YYYY-MM-DD)", example="2024-12-25"
        ),
        "start_time": fields.String(description="Start time (HH:MM)", example="18:00"),
        "end_time": fields.String(description="End time (HH:MM)", example="23:00"),
        "address_cep": fields.String(description="ZIP code"),
        "address_full": fields.String(description="Full address"),
        "allow_modifications": fields.Boolean(
            description="Allow guests to modify RSVP"
        ),
        "allow_cancellations": fields.Boolean(
            description="Allow guests to cancel RSVP"
        ),
    },
)

rsvp_model = api.model(
    "RSVP",
    {
        "event_slug": fields.String(
            required=True, description="Event slug", example="abc123"
        ),
        "whatsapp_number": fields.String(
            required=True, description="Attendee WhatsApp", example="5521988888888"
        ),
        "name": fields.String(
            required=True, description="Attendee name", example="Maria Silva"
        ),
        "family_member_names": fields.List(
            fields.String, description="Family member names", example=["Pedro", "Ana"]
        ),
        "num_adults": fields.Integer(
            required=True, description="Number of adults", example=2
        ),
        "num_children": fields.Integer(description="Number of children", example=1),
        "comments": fields.String(
            description="Special accommodations or allergies",
            example="Vegetarian meal needed",
        ),
    },
)

rsvp_update_model = api.model(
    "RSVPUpdate",
    {
        "whatsapp_number": fields.String(
            required=True,
            description="Attendee WhatsApp for identification",
            example="5521988888888",
        ),
        "name": fields.String(description="Updated name", example="Maria Silva"),
        "family_member_names": fields.List(
            fields.String,
            description="Updated family members",
            example=["Pedro", "Ana"],
        ),
        "num_adults": fields.Integer(description="Updated number of adults", example=3),
        "num_children": fields.Integer(
            description="Updated number of children", example=2
        ),
        "comments": fields.String(
            description="Updated comments", example="Now need vegan meal"
        ),
    },
)

rsvp_cancel_model = api.model(
    "RSVPCancel",
    {
        "whatsapp_number": fields.String(
            required=True, description="Attendee WhatsApp", example="5521988888888"
        ),
        "reason": fields.String(
            description="Cancellation reason", example="Cannot attend due to conflict"
        ),
    },
)

attendee_update_model = api.model(
    "AttendeeUpdate",
    {
        "name": fields.String(description="Attendee name", example="Maria Silva"),
        "num_adults": fields.Integer(description="Number of adults", example=2),
        "num_children": fields.Integer(description="Number of children", example=1),
        "comments": fields.String(description="Comments", example="Vegetarian"),
    },
)

attendee_find_model = api.model(
    "AttendeeFind",
    {
        "event_slug": fields.String(
            required=True, description="Event slug", example="festa-aniversario-abc123"
        ),
        "whatsapp_number": fields.String(
            required=True, description="WhatsApp number", example="5521999999999"
        ),
    },
)

attendee_modify_model = api.model(
    "AttendeeModify",
    {
        "event_slug": fields.String(required=True, description="Event slug"),
        "whatsapp_number": fields.String(required=True, description="WhatsApp number"),
        "name": fields.String(description="New name"),
        "num_adults": fields.Integer(description="New number of adults"),
        "num_children": fields.Integer(description="New number of children"),
        "comments": fields.String(description="New comments"),
    },
)


# ============= AUTH ROUTES =============
@auth_ns.route("/signup")
class Signup(Resource):
    @auth_ns.expect(signup_model)
    @auth_ns.response(201, "Host created successfully")
    @auth_ns.response(400, "Invalid input")
    @auth_ns.response(409, "Email already registered")
    def post(self):
        """Create new host account"""
        data = request.get_json()
        required = ["email", "password", "name", "whatsapp_number"]
        if not all(field in data for field in required):
            api.abort(400, "Missing required fields")

        try:
            email_info = validate_email(data["email"], check_deliverability=False)
            email = email_info.normalized
        except EmailNotValidError as e:
            api.abort(400, f"Invalid email: {str(e)}")

        if Host.query.filter_by(email=email).first():
            api.abort(409, "Email already registered")

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
    @auth_ns.response(200, "Login successful")
    @auth_ns.response(400, "Missing credentials")
    @auth_ns.response(401, "Invalid credentials")
    def post(self):
        """Login as host"""
        data = request.get_json()
        if not data.get("email") or not data.get("password"):
            api.abort(400, "Email and password required")

        host = Host.query.filter_by(email=data["email"]).first()
        if not host or not bcrypt.check_password_hash(
            host.password_hash, data["password"]
        ):
            api.abort(401, "Invalid credentials")

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
    @auth_ns.response(200, "Logout successful")
    def post(self):
        """Logout current host"""
        session.pop("host_id", None)
        return {"message": "Logged out successfully"}, 200


@auth_ns.route("/me")
class CurrentHost(Resource):
    @auth_ns.response(200, "Success")
    @auth_ns.response(401, "Not authenticated")
    def get(self):
        """Get currently authenticated host"""
        if "host_id" not in session:
            api.abort(401, "Not authenticated")

        host = Host.query.get(session["host_id"])
        if not host:
            api.abort(404, "Host not found")

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
    @events_ns.response(201, "Event created successfully")
    @events_ns.response(400, "Invalid input")
    @events_ns.response(401, "Not authenticated")
    def post(self):
        """Create new event (requires authentication)"""
        if "host_id" not in session:
            api.abort(
                401, "Authentication required. Please login first at /api/auth/login"
            )

        data = request.get_json()

        # Campos obrigatórios
        required = ["title", "event_date", "start_time", "address_full"]
        if not all(field in data for field in required):
            api.abort(
                400,
                "Missing required fields: title, event_date, start_time, address_full",
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
        except ValueError as e:
            api.abort(400, f"Invalid date/time format: {str(e)}")

        # Tentar geocodificar o endereço automaticamente
        latitude, longitude = geocode_address(data["address_full"])

        # Criar evento (se não encontrou coordenadas, salva None)
        event = Event(
            host_id=session["host_id"],
            title=data["title"],
            description=data.get("description", ""),
            event_date=event_date,
            start_time=start_time,
            end_time=end_time,
            address_cep=data.get("address_cep", ""),  # Apenas armazenar, não validar
            address_full=data["address_full"],
            latitude=latitude,
            longitude=longitude,
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
    @events_ns.response(200, "Success")
    @events_ns.response(401, "Not authenticated")
    def get(self):
        """Get all events for the logged-in host"""
        if "host_id" not in session:
            api.abort(401, "Authentication required")

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
                    "event_date": event.event_date.isoformat(),
                    "start_time": event.start_time.strftime("%H:%M"),
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
    @events_ns.response(200, "Success")
    @events_ns.response(404, "Event not found")
    def get(self, slug):
        """Get event details by slug (for guests viewing invitation)"""
        event = Event.query.filter_by(slug=slug).first()
        if not event:
            api.abort(404, "Event not found")

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
                "latitude": event.latitude,
                "longitude": event.longitude,
                "allow_modifications": event.allow_modifications,
                "allow_cancellations": event.allow_cancellations,
            }
        }, 200


@events_ns.route("/<int:event_id>/attendees")
class EventAttendees(Resource):
    @events_ns.response(200, "Success")
    @events_ns.response(401, "Not authenticated")
    @events_ns.response(403, "Unauthorized")
    @events_ns.response(404, "Event not found")
    def get(self, event_id):
        """Get all attendees for an event (host only)"""
        if "host_id" not in session:
            api.abort(401, "Authentication required")

        event = Event.query.get(event_id)
        if not event:
            api.abort(404, "Event not found")

        if event.host_id != session["host_id"]:
            api.abort(403, "Unauthorized")

        attendees = Attendee.query.filter_by(event_id=event_id).all()

        return {
            "attendees": [
                {
                    "id": attendee.id,
                    "name": attendee.name,
                    "whatsapp_number": attendee.whatsapp_number,
                    "family_member_names": attendee.family_member_names,
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
    @events_ns.response(200, "Attendee updated")
    @events_ns.response(401, "Not authenticated")
    @events_ns.response(403, "Unauthorized")
    @events_ns.response(404, "Not found")
    def put(self, event_id, attendee_id):
        """Update attendee (host only)"""
        if "host_id" not in session:
            api.abort(401, "Authentication required")

        event = Event.query.get(event_id)
        if not event or event.host_id != session["host_id"]:
            api.abort(403, "Unauthorized")

        attendee = Attendee.query.get(attendee_id)
        if not attendee or attendee.event_id != event_id:
            api.abort(404, "Attendee not found")

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

    @events_ns.response(200, "Attendee deleted")
    @events_ns.response(401, "Not authenticated")
    @events_ns.response(403, "Unauthorized")
    @events_ns.response(404, "Not found")
    def delete(self, event_id, attendee_id):
        """Delete attendee (host only)"""
        if "host_id" not in session:
            api.abort(401, "Authentication required")

        event = Event.query.get(event_id)
        if not event or event.host_id != session["host_id"]:
            api.abort(403, "Unauthorized")

        attendee = Attendee.query.get(attendee_id)
        if not attendee or attendee.event_id != event_id:
            api.abort(404, "Attendee not found")

        db.session.delete(attendee)
        db.session.commit()
        return {"message": "Attendee deleted successfully"}, 200


@events_ns.route("/<int:event_id>/export-csv")
class ExportAttendees(Resource):
    @events_ns.response(200, "CSV file")
    @events_ns.response(401, "Not authenticated")
    @events_ns.response(403, "Unauthorized")
    def get(self, event_id):
        """Export attendees as CSV (host only)"""
        if "host_id" not in session:
            api.abort(401, "Authentication required")

        event = Event.query.get(event_id)
        if not event or event.host_id != session["host_id"]:
            api.abort(403, "Unauthorized")

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "Name",
                "WhatsApp",
                "Adults",
                "Children",
                "Family Members",
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
                    (
                        ", ".join(attendee.family_member_names)
                        if attendee.family_member_names
                        else ""
                    ),
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
    @events_ns.response(200, "Event updated")
    @events_ns.response(401, "Not authenticated")
    @events_ns.response(403, "Unauthorized")
    @events_ns.response(404, "Event not found")
    def put(self, event_id):
        """Update event (host only)"""
        # Implementation in routes/events.py
        pass

    @events_ns.response(200, "Event deleted")
    @events_ns.response(401, "Not authenticated")
    @events_ns.response(403, "Unauthorized")
    @events_ns.response(404, "Event not found")
    def delete(self, event_id):
        """Delete event (host only)"""
        # Implementation in routes/events.py
        pass


@events_ns.route("/<int:event_id>/duplicate")
class DuplicateEvent(Resource):
    @events_ns.response(201, "Event duplicated")
    @events_ns.response(401, "Not authenticated")
    @events_ns.response(403, "Unauthorized")
    @events_ns.response(404, "Event not found")
    def post(self, event_id):
        """Duplicate an existing event"""
        # Implementation in routes/events.py
        pass


# ============= ATTENDEE ROUTES =============
@attendees_ns.route("/rsvp")
class RSVPResource(Resource):
    @attendees_ns.expect(rsvp_model)
    @attendees_ns.response(201, "RSVP successful")
    @attendees_ns.response(400, "Invalid input or already RSVP'd")
    @attendees_ns.response(404, "Event not found")
    @limiter.limit("5 per minute")
    def post(self):
        """Create RSVP for an event"""
        data = request.get_json()
        required = ["event_slug", "whatsapp_number", "name", "num_adults"]
        if not all(field in data for field in required):
            api.abort(400, "Missing required fields")

        event = Event.query.filter_by(slug=data["event_slug"]).first()
        if not event:
            api.abort(404, "Event not found")

        existing = Attendee.query.filter_by(
            event_id=event.id, whatsapp_number=data["whatsapp_number"]
        ).first()
        if existing:
            api.abort(400, "You have already RSVP'd to this event")

        attendee = Attendee(
            event_id=event.id,
            whatsapp_number=data["whatsapp_number"],
            name=data["name"],
            family_member_names=data.get("family_member_names", []),
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
    @attendees_ns.response(200, "Attendee found")
    @attendees_ns.response(404, "Attendee not found")
    def post(self):
        """Find attendee by WhatsApp and event slug"""
        data = request.get_json()

        event_slug = data.get("event_slug")
        whatsapp_number = data.get("whatsapp_number")

        if not event_slug or not whatsapp_number:
            api.abort(400, "Event slug and WhatsApp number are required")

        # Find event
        event = Event.query.filter_by(slug=event_slug).first()
        if not event:
            api.abort(404, "Event not found")

        # Find attendee
        attendee = Attendee.query.filter_by(
            event_id=event.id, whatsapp_number=whatsapp_number
        ).first()

        if not attendee:
            api.abort(404, "RSVP not found for this WhatsApp number")

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
                "allow_modifications": event.allow_modifications,
                "allow_cancellations": event.allow_cancellations,
            },
        }, 200


@attendees_ns.route("/modify")
class ModifyRSVP(Resource):
    @attendees_ns.expect(attendee_modify_model)
    @attendees_ns.response(200, "RSVP modified")
    @attendees_ns.response(403, "Modifications not allowed")
    @attendees_ns.response(404, "RSVP not found")
    def put(self):
        """Modify existing RSVP"""
        data = request.get_json()

        event_slug = data.get("event_slug")
        whatsapp_number = data.get("whatsapp_number")

        if not event_slug or not whatsapp_number:
            api.abort(400, "Event slug and WhatsApp number are required")

        # Find event
        event = Event.query.filter_by(slug=event_slug).first()
        if not event:
            api.abort(404, "Event not found")

        # Check if modifications are allowed
        if not event.allow_modifications:
            api.abort(403, "Modifications are not allowed for this event")

        # Find attendee
        attendee = Attendee.query.filter_by(
            event_id=event.id, whatsapp_number=whatsapp_number
        ).first()

        if not attendee:
            api.abort(404, "RSVP not found")

        # Update fields
        if "name" in data:
            attendee.name = data["name"]
        if "num_adults" in data:
            attendee.num_adults = data["num_adults"]
        if "num_children" in data:
            attendee.num_children = data["num_children"]
        if "comments" in data:
            attendee.comments = data["comments"]

        # If was cancelled, reactivate
        if attendee.status == "cancelled":
            attendee.status = "confirmed"

        db.session.commit()
        send_modification_notification(event, attendee, data)

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
    @attendees_ns.expect(attendee_find_model)
    @attendees_ns.response(200, "RSVP cancelled")
    @attendees_ns.response(403, "Cancellations not allowed")
    @attendees_ns.response(404, "RSVP not found")
    def post(self):
        """Cancel existing RSVP"""
        data = request.get_json()

        event_slug = data.get("event_slug")
        whatsapp_number = data.get("whatsapp_number")

        if not event_slug or not whatsapp_number:
            api.abort(400, "Event slug and WhatsApp number are required")

        # Find event
        event = Event.query.filter_by(slug=event_slug).first()
        if not event:
            api.abort(404, "Event not found")

        # Check if cancellations are allowed
        if not event.allow_cancellations:
            api.abort(403, "Cancellations are not allowed for this event")

        # Find attendee
        attendee = Attendee.query.filter_by(
            event_id=event.id, whatsapp_number=whatsapp_number
        ).first()

        if not attendee:
            api.abort(404, "RSVP not found")

        # Cancel RSVP
        attendee.status = "cancelled"
        db.session.commit()
        send_cancellation_notification(event, attendee, data.get("reason", ""))

        return {"message": "RSVP cancelled successfully"}, 200


# Keep original blueprints for backward compatibility
from routes import auth, events, attendees

app.register_blueprint(auth.bp)
app.register_blueprint(events.bp)
app.register_blueprint(attendees.bp)


# Root redirect - override Flask-RESTX root route
def redirect_root():
    return redirect("/api/docs")


# Override the Flask-RESTX root endpoint
app.view_functions["root"] = redirect_root


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
