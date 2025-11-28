# backend/app.py
from flask import Flask
from flask_cors import CORS
from extensions import db, bcrypt, limiter  # Import from extensions, don't create them
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.getenv("UPLOAD_FOLDER")
app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_CONTENT_LENGTH"))

# Create upload folder if it doesn't exist
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Initialize extensions with app (don't create them here)
db.init_app(app)
bcrypt.init_app(app)
limiter.init_app(app)
CORS(app)

# Import routes AFTER app is configured
from routes import auth, events, attendees

app.register_blueprint(auth.bp)
app.register_blueprint(events.bp)
app.register_blueprint(attendees.bp)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Create tables
    app.run(debug=True, port=5000)
