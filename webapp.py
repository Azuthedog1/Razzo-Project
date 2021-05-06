import os
from flask import Flask, url_for, render_template, request

app = Flask(__name__)

@app.route('/')
def renderMain():
    return render_template('home.html')
