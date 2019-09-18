from datetime import datetime
from app import db

###############################################################
# Create the database models here
###############################################################

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(64), index = True, unique = True)
    email = db.Column(db.String(120), index = True, unique = True)
    password_hash = db.Column(db.String(128))
    reviews = db.relationship('Review', backref = 'author', lazy = 'dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index = True, default = datetime.utcnow)
    film_id = db.Column(db.Integer)

    def __repr__(self):
        return '<Review {}>'.format(self.body)


