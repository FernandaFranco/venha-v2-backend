import os
from werkzeug.utils import secure_filename
from PIL import Image
import uuid

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_banner_image(file, upload_folder):
    """Save and optimize banner image"""
    if file and allowed_file(file.filename):
        # Generate unique filename
        ext = file.filename.rsplit(".", 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(upload_folder, filename)

        # Open and optimize image
        img = Image.open(file)

        # Resize if too large (max width 1200px)
        max_width = 1200
        if img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

        # Save optimized image
        img.save(filepath, optimize=True, quality=85)

        return filename
    return None
