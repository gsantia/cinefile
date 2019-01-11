from flask import Flask

##############################################################################
# Driver script for the app, using Flask. Right now, I'm not totally sure what
# features to include, and what the point really is. No matter!
##############################################################################


application = Flask(__name__)

@application.route('/')
def hello_world():
    return "hello world!"


