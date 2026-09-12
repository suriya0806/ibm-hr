from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session, relationship, Query
from flask import abort
from config import Config

Base = declarative_base()

class CustomQuery(Query):
    def get_or_404(self, ident, description=None):
        rv = self.get(ident)
        if rv is None:
            abort(404, description=description or "Resource not found")
        return rv

class DBWrapper:
    def __init__(self):
        self.Model = Base
        self.Column = Column
        self.Integer = Integer
        self.String = String
        self.Text = Text
        self.Float = Float
        self.DateTime = DateTime
        self.JSON = JSON
        self.ForeignKey = ForeignKey
        self.relationship = relationship
        
        self.engine = None
        self.session_factory = None
        self.session = None

    def init_app(self, app):
        db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", Config.SQLALCHEMY_DATABASE_URI)
        self.engine = create_engine(db_uri, echo=False, future=True)
        self.session_factory = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
        self.session = scoped_session(self.session_factory)

        # Attach query property to Base so Model.query works with get_or_404
        Base.query = self.session.query_property(query_cls=CustomQuery)

        @app.teardown_appcontext
        def remove_session(exception=None):
            self.session.remove()

    def create_all(self):
        if self.engine is not None:
            Base.metadata.create_all(bind=self.engine)

db = DBWrapper()

from app.models.job import JobDescription
from app.models.candidate import Candidate, ResumeData
from app.models.match import MatchResult
from app.models.interview import InterviewKit

__all__ = [
    "db",
    "Base",
    "JobDescription",
    "Candidate",
    "ResumeData",
    "MatchResult",
    "InterviewKit",
]
