
from . import db
from sqlalchemy import func


class Url(db.Model):
    code = db.Column(
        db.String(20),
        unique=True,
        primary_key=True,
        nullable=False
    )

    url = db.Column(
        db.String(2000),
        nullable=False
    )

    used = db.Column(
        db.Integer,
        nullable=False
    )

    magic = db.Column(
        db.String(256),
        nullable=False
    )

    date = db.Column(
        db.DateTime,
        nullable=False,
        default=func.now()
    )


class Used(db.Model):
    idx = db.Column(
        db.Integer,
        unique=True,
        primary_key=True,
        nullable=False
    )

    code = db.Column(
        db.String(20),
        nullable=False
    )

    date = db.Column(
        db.DateTime,
        nullable=False,
        default=func.now()
    )

    used = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
