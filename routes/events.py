from flask import Blueprint, request, jsonify, session, send_from_directory
from extensions import db
from flask import current_app as app
from models import Host, Event, Attendee
from utils.file_handler import save_banner_image
from services.cep_service import get_address_from_cep
from datetime import datetime
import csv
import io

bp = Blueprint("events", __name__, url_prefix="/api/events")


def require_auth(f):
    """Decorator to require authentication"""
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
    data = request.form.to_dict()  # Use form data because of file upload

    # Validate required fields
    required = ["title", "event_date", "start_time", "address_cep"]
    if not all(field in data for field in required):
        return jsonify({"error": "Missing required fields"}), 400

    # Get address from CEP
    address_full = get_address_from_cep(data["address_cep"])
    if not address_full:
        return jsonify({"error": "Invalid CEP"}), 400

    # Handle banner image upload
    banner_filename = None
    if "banner_image" in request.files:
        file = request.files["banner_image"]
        if file.filename:
            banner_filename = save_banner_image(file, app.config["UPLOAD_FOLDER"])

    # Parse custom fields (sent as JSON string)
    import json

    custom_fields = json.loads(data.get("custom_fields", "[]"))

    # Create event
    event = Event(
        host_id=session["host_id"],
        title=data["title"],
        description=data.get("description", ""),
        banner_image=banner_filename,
        event_date=datetime.strptime(data["event_date"], "%Y-%m-%d").date(),
        start_time=datetime.strptime(data["start_time"], "%H:%M").time(),
        end_time=(
            datetime.strptime(data["end_time"], "%H:%M").time()
            if data.get("end_time")
            else None
        ),
        address_cep=data["address_cep"],
        address_full=address_full,
        allow_modifications=data.get("allow_modifications", "true").lower() == "true",
        allow_cancellations=data.get("allow_cancellations", "true").lower() == "true",
        custom_fields=custom_fields,
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
    """Get all events for the logged-in host"""
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
    """Get event details by slug (for guests viewing invitation)"""
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
                    "banner_image": (
                        f"/uploads/banners/{event.banner_image}"
                        if event.banner_image
                        else None
                    ),
                    "event_date": event.event_date.isoformat(),
                    "start_time": event.start_time.strftime("%H:%M"),
                    "end_time": (
                        event.end_time.strftime("%H:%M") if event.end_time else None
                    ),
                    "address_full": event.address_full,
                    "allow_modifications": event.allow_modifications,
                    "allow_cancellations": event.allow_cancellations,
                    "custom_fields": event.custom_fields,
                }
            }
        ),
        200,
    )


@bp.route("/<int:event_id>/attendees", methods=["GET"])
@require_auth
def get_event_attendees(event_id):
    """Get all attendees for an event (host only)"""
    event = Event.query.get(event_id)

    if not event:
        return jsonify({"error": "Event not found"}), 404

    # Check if the logged-in host owns this event
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
    """Export attendees as CSV"""
    event = Event.query.get(event_id)

    if not event or event.host_id != session["host_id"]:
        return jsonify({"error": "Unauthorized"}), 403

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write headers
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

    # Write data
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

    # Prepare response
    output.seek(0)
    from flask import Response

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=event_{event_id}_attendees.csv"
        },
    )


# Serve uploaded images
@bp.route("/uploads/banners/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)
