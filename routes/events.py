# backend/routes/events.py
from flask import Blueprint, request, jsonify, session, Response
from extensions import db
from models import Host, Event, Attendee
from services.geocoding_service import geocode_address
from datetime import datetime
import csv
import io

bp = Blueprint("events", __name__, url_prefix="/api/events")


def require_auth(f):
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "host_id" not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)

    return decorated_function


@bp.route("/create", methods=["POST"])
@require_auth
def create_event():
    data = request.get_json()

    # Campos obrigatórios atualizados
    required = ["title", "event_date", "start_time", "address_full"]
    if not all(field in data for field in required):
        return jsonify({"error": "Missing required fields"}), 400

    # Tentar geocodificar o endereço automaticamente
    latitude, longitude = geocode_address(data["address_full"])

    # Criar evento (se não encontrou coordenadas, salva None)
    event = Event(
        host_id=session["host_id"],
        title=data["title"],
        description=data.get("description", ""),
        event_date=datetime.strptime(data["event_date"], "%Y-%m-%d").date(),
        start_time=datetime.strptime(data["start_time"], "%H:%M").time(),
        end_time=(
            datetime.strptime(data["end_time"], "%H:%M").time()
            if data.get("end_time")
            else None
        ),
        address_cep=data.get("address_cep", ""),
        address_full=data["address_full"],
        latitude=latitude,
        longitude=longitude,
        allow_modifications=data.get("allow_modifications", True),
        allow_cancellations=data.get("allow_cancellations", True),
    )

    db.session.add(event)
    db.session.commit()

    return (
        jsonify(
            {
                "message": "Event created successfully",
                "event": {
                    "id": event.id,
                    "slug": event.slug,
                    "invite_url": f"/invite/{event.slug}",
                },
            }
        ),
        201,
    )


@bp.route("/my-events", methods=["GET"])
@require_auth
def get_my_events():
    events = (
        Event.query.filter_by(host_id=session["host_id"])
        .order_by(Event.event_date.desc())
        .all()
    )

    return (
        jsonify(
            {
                "events": [
                    {
                        "id": event.id,
                        "slug": event.slug,
                        "title": event.title,
                        "event_date": event.event_date.isoformat(),
                        "start_time": event.start_time.strftime("%H:%M"),
                        "attendee_count": len(event.attendees),
                        "total_adults": sum(
                            a.num_adults
                            for a in event.attendees
                            if a.status == "confirmed"
                        ),
                        "total_children": sum(
                            a.num_children
                            for a in event.attendees
                            if a.status == "confirmed"
                        ),
                    }
                    for event in events
                ]
            }
        ),
        200,
    )


@bp.route("/<slug>", methods=["GET"])
def get_event_by_slug(slug):
    event = Event.query.filter_by(slug=slug).first()

    if not event:
        return jsonify({"error": "Event not found"}), 404

    return (
        jsonify(
            {
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
            }
        ),
        200,
    )


@bp.route("/<int:event_id>/attendees", methods=["GET"])
@require_auth
def get_event_attendees(event_id):
    event = Event.query.get(event_id)

    if not event:
        return jsonify({"error": "Event not found"}), 404

    if event.host_id != session["host_id"]:
        return jsonify({"error": "Unauthorized"}), 403

    attendees = Attendee.query.filter_by(event_id=event_id).all()

    return (
        jsonify(
            {
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
            }
        ),
        200,
    )


@bp.route("/<int:event_id>/export-csv", methods=["GET"])
@require_auth
def export_attendees_csv(event_id):
    event = Event.query.get(event_id)

    if not event or event.host_id != session["host_id"]:
        return jsonify({"error": "Unauthorized"}), 403

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


@bp.route("/<int:event_id>/attendees/<int:attendee_id>", methods=["PUT"])
@require_auth
def update_attendee(event_id, attendee_id):
    """Update attendee (host only)"""
    event = Event.query.get(event_id)

    if not event:
        return jsonify({"error": "Event not found"}), 404

    if event.host_id != session["host_id"]:
        return jsonify({"error": "Unauthorized"}), 403

    attendee = Attendee.query.get(attendee_id)
    if not attendee or attendee.event_id != event_id:
        return jsonify({"error": "Attendee not found"}), 404

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

    return jsonify({"message": "Attendee updated successfully"}), 200


@bp.route("/<int:event_id>/attendees/<int:attendee_id>", methods=["DELETE"])
@require_auth
def delete_attendee(event_id, attendee_id):
    """Delete attendee (host only)"""
    event = Event.query.get(event_id)

    if not event:
        return jsonify({"error": "Event not found"}), 404

    if event.host_id != session["host_id"]:
        return jsonify({"error": "Unauthorized"}), 403

    attendee = Attendee.query.get(attendee_id)
    if not attendee or attendee.event_id != event_id:
        return jsonify({"error": "Attendee not found"}), 404

    db.session.delete(attendee)
    db.session.commit()

    return jsonify({"message": "Attendee deleted successfully"}), 200


@bp.route("/<int:event_id>", methods=["PUT"])
@require_auth
def update_event(event_id):
    """Update event (host only)"""
    event = Event.query.get(event_id)

    if not event:
        return jsonify({"error": "Event not found"}), 404

    if event.host_id != session["host_id"]:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()

    try:
        # Update basic fields
        if "title" in data:
            event.title = data["title"]

        if "description" in data:
            event.description = data["description"]

        if "event_date" in data:
            event.event_date = datetime.strptime(data["event_date"], "%Y-%m-%d").date()

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

            # Re-geocode if address changed
            from .events import geocode_address

            lat, lon = geocode_address(data["address_full"], data.get("address_cep"))
            event.latitude = lat
            event.longitude = lon

        if "allow_modifications" in data:
            event.allow_modifications = data["allow_modifications"]

        if "allow_cancellations" in data:
            event.allow_cancellations = data["allow_cancellations"]

        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Event updated successfully",
                    "event": {"id": event.id, "slug": event.slug, "title": event.title},
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@bp.route("/<int:event_id>", methods=["DELETE"])
@require_auth
def delete_event(event_id):
    """Delete event (host only)"""
    event = Event.query.get(event_id)

    if not event:
        return jsonify({"error": "Event not found"}), 404

    if event.host_id != session["host_id"]:
        return jsonify({"error": "Unauthorized"}), 403

    try:
        # Delete all attendees first (cascade should handle this, but being explicit)
        Attendee.query.filter_by(event_id=event_id).delete()

        # Delete event
        db.session.delete(event)
        db.session.commit()

        return jsonify({"message": "Event deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@bp.route("/<int:event_id>/duplicate", methods=["POST"])
@require_auth
def duplicate_event(event_id):
    """Duplicate an existing event (host only)"""
    original_event = Event.query.get(event_id)

    if not original_event:
        return jsonify({"error": "Event not found"}), 404

    if original_event.host_id != session["host_id"]:
        return jsonify({"error": "Unauthorized"}), 403

    try:
        # Create new event with same data
        new_event = Event(
            host_id=session["host_id"],
            title=f"{original_event.title} (Cópia)",
            description=original_event.description,
            event_date=original_event.event_date,
            start_time=original_event.start_time,
            end_time=original_event.end_time,
            address_cep=original_event.address_cep,
            address_full=original_event.address_full,
            latitude=original_event.latitude,
            longitude=original_event.longitude,
            allow_modifications=original_event.allow_modifications,
            allow_cancellations=original_event.allow_cancellations,
        )

        db.session.add(new_event)
        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Event duplicated successfully",
                    "event": {
                        "id": new_event.id,
                        "slug": new_event.slug,
                        "title": new_event.title,
                    },
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
