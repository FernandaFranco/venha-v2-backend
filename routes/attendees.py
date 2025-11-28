from flask import Blueprint, request, jsonify
from extensions import db, limiter
from models import Attendee, Event
from services.email_service import send_rsvp_notification

bp = Blueprint("attendees", __name__, url_prefix="/api/attendees")


@bp.route("/rsvp", methods=["POST"])
@limiter.limit("5 per minute")  # Strict rate limit for RSVP
def create_rsvp():
    data = request.get_json()

    # Validate required fields
    required = ["event_slug", "whatsapp_number", "name", "num_adults"]
    if not all(field in data for field in required):
        return jsonify({"error": "Missing required fields"}), 400

    # Find event
    event = Event.query.filter_by(slug=data["event_slug"]).first()
    if not event:
        return jsonify({"error": "Event not found"}), 404

    # Check if already RSVP'd
    existing = Attendee.query.filter_by(
        event_id=event.id, whatsapp_number=data["whatsapp_number"]
    ).first()

    if existing:
        return jsonify({"error": "You have already RSVP'd to this event"}), 400

    # Create attendee
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

    # Send email to host
    send_rsvp_notification(event, attendee)

    return jsonify({"message": "RSVP successful", "attendee_id": attendee.id}), 201
