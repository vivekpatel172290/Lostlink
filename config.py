import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
IS_VERCEL = os.environ.get('VERCEL') == '1'

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'campus-lost-and-found-super-secret-key-2026'
    
    # On Vercel serverless, filesystem is read-only except /tmp
    if IS_VERCEL:
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or "sqlite:////tmp/campus_lost_found.db"
        UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or "/tmp/uploads"
    else:
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f"sqlite:///{os.path.join(BASE_DIR, 'campus_lost_found.db')}"
        UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
    
    # ML Matching settings per PDF specification
    CLIP_MODEL_NAME = "sentence-transformers/clip-ViT-B-32"
    SIMILARITY_THRESHOLD = 0.25
    MAX_MATCH_RESULTS = 5
