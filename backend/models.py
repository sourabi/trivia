from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, String, Integer
from dotenv import load_dotenv
import os

load_dotenv()

database_name = "trivia"
database_password = os.environ.get("database_password")
database_path = "postgresql://{}:{}@{}/{}".format('postgres', database_password, 'localhost:5432', database_name)

db = SQLAlchemy()

'''
setup_db(app)
    binds a flask application and a SQLAlchemy service
'''


def setup_db(app, db_path=database_path):
    app.config["SQLALCHEMY_DATABASE_URI"] = db_path
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.app = app
    db.init_app(app)


'''
Question
'''


class Question(db.Model):
    __tablename__ = 'questions'

    id = Column(Integer, primary_key=True)
    question = Column(String, nullable=False)
    answer = Column(String, nullable=False)
    difficulty = Column(Integer, nullable=False)
    category = Column(Integer, db.ForeignKey('categories.id', ondelete='CASCADE'), nullable=False)

    def __init__(self, question, answer, category, difficulty):
        self.question = question
        self.answer = answer
        self.difficulty = difficulty
        self.category = category

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def format(self):
        return {
            'id': self.id,
            'question': self.question,
            'answer': self.answer,
            'difficulty': self.difficulty,
            'category': self.category
        }


'''
Category
'''


class Category(db.Model):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    type = Column(String, nullable=False)
    questions = db.relationship('Question', backref='categories', lazy=True, cascade="all, delete")

    def __init__(self, type):
        self.type = type

    def format(self):
        return {
            'id': self.id,
            'type': self.type
        }
