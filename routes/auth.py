from flask import Blueprint, request, jsonify, session
from extensions import db, bcrypt
from models import Host
from email_validator import validate_email, EmailNotValidError

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()

    # Validate required fields
    required = ["email", "password", "name", "whatsapp_number"]
    if not all(field in data for field in required):
        return jsonify({"error": "Missing required fields"}), 400

    # Validate email format
    try:
        validate_email(data["email"])
    except EmailNotValidError:
        return jsonify({"error": "Invalid email format"}), 400

    # Check if email already exists
    if Host.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already registered"}), 409

    # Hash password
    password_hash = bcrypt.generate_password_hash(data["password"]).decode("utf-8")

    # Create host
    host = Host(
        email=data["email"],
        password_hash=password_hash,
        name=data["name"],
        whatsapp_number=data["whatsapp_number"],
    )

    db.session.add(host)
    db.session.commit()

    # Create session (log them in)
    session["host_id"] = host.id

    return (
        jsonify(
            {
                "message": "Account created successfully",
                "host": {
                    "id": host.id,
                    "email": host.email,
                    "name": host.name,
                    "whatsapp_number": host.whatsapp_number,
                },
            }
        ),
        201,
    )


@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email and password required"}), 400

    host = Host.query.filter_by(email=data["email"]).first()

    if not host or not bcrypt.check_password_hash(host.password_hash, data["password"]):
        return jsonify({"error": "Invalid email or password"}), 401

    # Create session
    session["host_id"] = host.id

    return (
        jsonify(
            {
                "message": "Login successful",
                "host": {
                    "id": host.id,
                    "email": host.email,
                    "name": host.name,
                    "whatsapp_number": host.whatsapp_number,
                },
            }
        ),
        200,
    )


@bp.route("/logout", methods=["POST"])
def logout():
    session.pop("host_id", None)
    return jsonify({"message": "Logged out successfully"}), 200


@bp.route("/me", methods=["GET"])
def get_current_host():
    """Get currently logged in host"""
    if "host_id" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    host = Host.query.get(session["host_id"])
    if not host:
        return jsonify({"error": "Host not found"}), 404

    return (
        jsonify(
            {
                "host": {
                    "id": host.id,
                    "email": host.email,
                    "name": host.name,
                    "whatsapp_number": host.whatsapp_number,
                }
            }
        ),
        200,
    )
