from extensions import db
from datetime import datetime
import uuid


class Host(db.Model):
    __tablename__ = "hosts"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    whatsapp_number = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    events = db.relationship(
        "Event", backref="host", lazy=True, cascade="all, delete-orphan"
    )


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    host_id = db.Column(db.Integer, db.ForeignKey("hosts.id"), nullable=False)
    slug = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4())[:8],
    )

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    banner_image = db.Column(db.String(255))

    event_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time)

    address_cep = db.Column(db.String(10))
    address_full = db.Column(db.Text)

    allow_modifications = db.Column(db.Boolean, default=True)
    allow_cancellations = db.Column(db.Boolean, default=True)
    custom_fields = db.Column(db.JSON)  # Store as JSON array

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    attendees = db.relationship(
        "Attendee", backref="event", lazy=True, cascade="all, delete-orphan"
    )


class Attendee(db.Model):
    __tablename__ = "attendees"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)

    whatsapp_number = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    family_member_names = db.Column(db.JSON)  # Array of names
    num_adults = db.Column(db.Integer, default=1)
    num_children = db.Column(db.Integer, default=0)
    comments = db.Column(db.Text)

    status = db.Column(db.String(20), default="confirmed")  # confirmed, cancelled
    rsvp_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Composite unique constraint: one RSVP per whatsapp number per event
    __table_args__ = (
        db.UniqueConstraint(
            "event_id", "whatsapp_number", name="unique_attendee_per_event"
        ),
    )
