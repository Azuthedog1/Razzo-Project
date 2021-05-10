import os
from flask import Flask, url_for, render_template, request

app = Flask(__name__)

@app.route('/')
def render_home():
    return render_template('home.html')

@app.route('/englishlearnerforum')
def render_english_learner_forum():
    return render_template('englishlearnerforum.html')

@app.route('/specialeducationforum')
def render_special_education_forum():
    return render_template('specialeducationforum.html')

@app.route('/loginforum')
def render_login_forum():
    return render_template('login.html')
