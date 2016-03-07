from flask import render_template
from . import main
from app import db
from app.model import User

@main.route('/', methods = ['GET', 'POST'])
def index():
    return render_template('index.html')