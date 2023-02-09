from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import string
import random

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.Text(), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime, onupdate=datetime.now())
    activity = db.relationship('Activity', backref="user", uselist=False)

    def __repr__(self) -> str:
        return f'User>>> {self.username}'


class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    used_quota = db.Column(db.Integer, default=0)
    summary_ids = db.Column(db.Text(), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime, onupdate=datetime.now())

    def __repr__(self) -> str:
        return f'Quota>>> {self.url}'


class Summary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Text, nullable=False)
    summary_1 = db.Column(db.Text, nullable=True)
    summary_2 = db.Column(db.Text, nullable=True)
    transcript = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime, onupdate=datetime.now())

    def __repr__(self) -> str:
        return f'Summary>>> {self.video_id}\n{self.summary_2}'
