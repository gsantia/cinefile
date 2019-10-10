#!/usr/bin/python3
from app import create_app, db
from app.models import User, Review, Notification, Message, Task

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Review': Review,
            'Message': Message, 'Notification': Notification,
            'Task': Task}
