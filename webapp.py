from flask import Flask, redirect, url_for, session, request, jsonify
from flask_oauthlib.client import OAuth
from flask import render_template

import pprint
import os
import sys
import pymongo
import time

app = Flask(__name__)

admins = ["MyDSWAccount", "Azuthedog1", "DanaLearnsToCode"]

app.secret_key = os.environ['SECRET_KEY'] #used to sign session cookies
oauth = OAuth(app)
oauth.init_app(app) #initialize the app to be able to make requests for user information

#Set up GitHub as OAuth provider
github = oauth.remote_app(
    'github',
    consumer_key=os.environ['GITHUB_CLIENT_ID'], 
    consumer_secret=os.environ['GITHUB_CLIENT_SECRET'],
    request_token_params={'scope': 'user:email'}, 
    base_url='https://api.github.com/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://github.com/login/oauth/access_token',  
    authorize_url='https://github.com/login/oauth/authorize' 
)

@app.context_processor
def inject_logged_in():
    return {"logged_in":('github_token' in session)}

@app.route('/')
def render_information():
    return render_template('information.html')

@app.route('/login')
def login():   
    return github.authorize(callback=url_for('authorized', _external=True, _scheme='https')) #callback URL must match the pre-configured callback URL

@app.route('/logout')
def logout():
    session.clear()
    return render_template('login.html', message='You were logged out')

@app.route('/login/authorized')
def authorized():
    resp = github.authorized_response()
    if resp is None:
        session.clear()
        message = 'Access denied: reason=' + request.args['error'] + ' error=' + request.args['error_description'] + ' full=' + pprint.pformat(request.args)      
    else:
        try:
            session['github_token'] = (resp['access_token'], '') #save the token to prove that the user logged in
            session['user_data']=github.get('user').data
            #pprint.pprint(vars(github['/email']))
            #pprint.pprint(vars(github['api/2/accounts/profile/']))
            global admins
            for admin in admins:
                if session['user_data']['login'] == admin:
                    message='You were successfully logged in as ' + session['user_data']['login'] + '.'
                else:
                    session.clear()
                    message='Please sign in with a valid admin account.  '
        except Exception as inst:
            session.clear()
            print(inst)
            message='Unable to login, please try again.  '
    return render_template('login.html', message=message)

@app.route('/englishlearnerforum')
def render_english_learner_forum():
    return render_template('englishlearnerforum.html')

@app.route('/specialeducationforum')
def render_special_education_forum():
    return render_template('specialeducationforum.html')

@app.route('/userSumbitPostELL', methods=['GET','POST'])
def renderUserPostSubmissionELL():
    session["name of the ids"]=request.form['name of the ids'] #make sure you get the current time of posting too using import time. Also, if we have time (not mandatory), store their personal information in cookies and auto fill out that part of the form using jinja each time they go to create a post)
    return render_template('englishlearnerforum.html') #set the same jinja variables here as in @app.route('englishlearnerforum') above (there are none right now)

#Once Henry adds a more complex text form, make sure the jinja variables use Markup 
@github.tokengetter
def get_github_oauth_token():
    return session['github_token']

if __name__ == '__main__':
    app.run()
