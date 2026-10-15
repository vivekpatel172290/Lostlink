import os
from datetime import datetime, timezone
import re
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

def get_utc_now():
    return datetime.now(timezone.utc)

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="student", nullable=False)  # "student", "admin"
    avatar = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=get_utc_now, nullable=False)

    items = db.relationship('Item', backref='reporter', lazy=True, cascade='all, delete-orphan')
    claims = db.relationship('Claim', backref='claimant', lazy=True, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='recipient', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

    @property
    def active_reports_count(self):
        return sum(1 for item in self.items if item.status == 'open')

    @property
    def resolved_reports_count(self):
        return sum(1 for item in self.items if item.status == 'resolved')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active_reports': self.active_reports_count,
            'resolved_reports': self.resolved_reports_count
        }

class Item(db.Model):
    __tablename__ = 'items'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    item_type = db.Column(db.String(10), nullable=False)  # "lost" or "found"
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(80), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    contact = db.Column(db.String(150), nullable=False)
    reporter_name = db.Column(db.String(100), default="Campus Member", nullable=False)
    image_path = db.Column(db.String(255), nullable=True)
    image_embedding = db.Column(db.PickleType, nullable=True)  # Normalized 512-dim CLIP vector
    text_embedding = db.Column(db.PickleType, nullable=True)   # Normalized 512-dim CLIP vector
    status = db.Column(db.String(20), default="open", nullable=False)  # "open", "matched", "resolved"
    matched_with_id = db.Column(db.Integer, nullable=True)
    flag_count = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=get_utc_now, nullable=False)

    claims = db.relationship('Claim', backref='item', lazy=True, cascade='all, delete-orphan')
    flags = db.relationship('Flag', backref='item', lazy=True, cascade='all, delete-orphan')

    def is_lost(self):
        return self.item_type.lower() == 'lost'

    def is_found(self):
        return self.item_type.lower() == 'found'

    def is_matched(self):
        return self.status.lower() == 'matched'

    def is_resolved(self):
        return self.status.lower() == 'resolved'

    @property
    def badge_color(self):
        if self.is_lost():
            return 'danger'
        elif self.is_found():
            return 'success'
        return 'primary'

    @property
    def phone_digits(self):
        if not self.contact:
            return ""
        digits = re.sub(r'\D', '', self.contact)
        return digits if len(digits) >= 10 else ""

    @property
    def time_ago(self):
        if not self.created_at:
            return "Recently"
        item_time = self.created_at
        if item_time.tzinfo is None:
            now = datetime.now(timezone.utc).replace(tzinfo=None)
        else:
            now = datetime.now(timezone.utc)
        diff = now - item_time
        seconds = diff.total_seconds()
        if seconds < 0:
            return "Just now"
        elif seconds < 60:
            return "Just now"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            return f"{minutes} min ago" if minutes == 1 else f"{minutes} mins ago"
        elif seconds < 86400:
            hours = int(seconds // 3600)
            return f"{hours} hour ago" if hours == 1 else f"{hours} hours ago"
        else:
            days = int(seconds // 86400)
            return f"{days} day ago" if days == 1 else f"{days} days ago"

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'item_type': self.item_type,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'location': self.location,
            'contact': self.contact,
            'reporter_name': self.reporter_name,
            'phone_digits': self.phone_digits,
            'image_path': self.image_path,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else 'N/A',
            'time_ago': self.time_ago
        }

class Claim(db.Model):
    __tablename__ = 'claims'

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    claimant_name = db.Column(db.String(100), nullable=False)
    claimant_contact = db.Column(db.String(150), nullable=False)
    proof_description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="pending", nullable=False)  # "pending", "approved", "rejected"
    created_at = db.Column(db.DateTime, default=get_utc_now, nullable=False)

    @property
    def time_ago(self):
        if not self.created_at:
            return "Recently"
        item_time = self.created_at
        if item_time.tzinfo is None:
            now = datetime.now(timezone.utc).replace(tzinfo=None)
        else:
            now = datetime.now(timezone.utc)
        diff = now - item_time
        seconds = diff.total_seconds()
        if seconds < 60:
            return "Just now"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            return f"{minutes} min ago" if minutes == 1 else f"{minutes} mins ago"
        elif seconds < 86400:
            hours = int(seconds // 3600)
            return f"{hours} hour ago" if hours == 1 else f"{hours} hours ago"
        else:
            days = int(seconds // 86400)
            return f"{days} day ago" if days == 1 else f"{days} days ago"

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(255), default="/")
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=get_utc_now, nullable=False)

    @property
    def time_ago(self):
        if not self.created_at:
            return "Recently"
        item_time = self.created_at
        if item_time.tzinfo is None:
            now = datetime.now(timezone.utc).replace(tzinfo=None)
        else:
            now = datetime.now(timezone.utc)
        diff = now - item_time
        seconds = diff.total_seconds()
        if seconds < 60:
            return "Just now"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            return f"{minutes} min ago" if minutes == 1 else f"{minutes} mins ago"
        else:
            hours = int(seconds // 3600)
            return f"{hours} hour ago" if hours == 1 else f"{hours} hours ago"

class Flag(db.Model):
    __tablename__ = 'flags'

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    reported_by = db.Column(db.String(100), default="Anonymous Student", nullable=False)
    created_at = db.Column(db.DateTime, default=get_utc_now, nullable=False)
