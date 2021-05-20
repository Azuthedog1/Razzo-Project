from flask import Flask, redirect, Markup, url_for, session, request, jsonify
from flask_oauthlib.client import OAuth
from flask import render_template
from bson.objectid import ObjectId

import pprint
import os
import sys
import pymongo
from datetime import datetime

app = Flask(__name__)

app.secret_key = os.environ['SECRET_KEY'] #used to sign session cookies
oauth = OAuth(app)
oauth.init_app(app) #initialize the app to be able to make requests for user information

admin1="Azuthedog1"
admin2="DanaLearnsToCode"
admin3="MyDSWAccount"
admin4="Korkz"
admin5="Ponmo"

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
            if session['user_data']['login'] == admin1 or session['user_data']['login'] == admin2 or session['user_data']['login'] == admin3 or session['user_data']['login'] == admin4 or session['user_data']['login'] == admin5:
                message='You were successfully logged in as ' + session['user_data']['login'] + '. Don\'t forget to log out before exiting this wbesite.'
            else:
                session.clear()
                message='Please sign in with a valid admin account. You attempted to log in as ' + session['user_data']['login'] + '. This is not an admin account. To log in as an admin you may need to log out of Github before attempting to log in again.'
        except Exception as inst:
            session.clear()
            print(inst)
            message='Unable to login, please try again.  '
    return render_template('login.html', message=message)

@app.route('/englishlearnerforum')
def render_english_learner_forum():
    connection_string = os.environ["MONGO_CONNECTION_STRING"]
    db_name = os.environ["MONGO_DBNAME"]
    client = pymongo.MongoClient(connection_string)
    db = client[db_name]
    collection = db['ELLU']
    bigString1 = ""
    for post in collection.find():
        if(post.get('approved') == "false"):
            bigString1 = bigString1 + Markup('{% if logged_in %}')
        bigString1 = bigString1 + Markup ('<tr><td class="col1">NoIcons</td>')  
        bigString1 = bigString1 + Markup('<td class="col2"><form action="/comments"><select class="selection" name="thread"><option value="' + post.get(str('ObjectId')) + '"></option></select><button type="submit" class="customButton commentButton">' + post.get('postTitle') + '</button></form></td>')
        if(post.get('anonymous') == "true"):
            bigString1 = bigString1 + Markup('<td class="col3"> {% if logged_in %}' + post.get('parentName') + ', ' + post.get('studentName+grade') + '{% endif %} (Anonymous)</td>')
        else:
            bigString1 = bigString1 + Markup('<td class="col3">' + post.get('parentName') + '{% if logged_in %}, ' + post.get('studentName+grade') + '{% endif %}</td>')
        bigString1 = bigString1 + Markup('<td class="col4">{% if logged_in %}<span><form action="/delete" method="post"><button type="submit" class="btn btn-danger btn-sm" name="delete" value="' + post.get(str('ObjectId')) + '">Confirm Delete</button></form><form action="/vet" method="post"><button type="submit" class="btn btn-warning btn-sm" name="vet" value="' + post.get(str('ObjectId')) + '">')
        if(post.get('approved') == "false"):
            bigString1 = bigString1 + Markup('Vet')
        else:
            bigString1 = bigString1 + Markup('Unvet')
        bigString1 = bigString1 + Markup('</button></form>' + post.get('date+time') + '</span>{% endif %}</td></tr>')
        if(post.get('approved') == "false"):
            bigString1 = bigString1 + Markup('{% endif %}')
    return render_template('englishlearnerforum.html', ELLUPosts = bigString1)

@app.route('/pendingQuestions')
def render_pending_Questions():
    return render_template('pendingQuestions.html')

@app.route('/specialeducationforum')
def render_special_education_forum():
    connection_string = os.environ["MONGO_CONNECTION_STRING"]
    db_name = os.environ["MONGO_DBNAME"]
    client = pymongo.MongoClient(connection_string)
    db = client[db_name]
    collection = db['SEU']
    #for post in collection.find():
    #    if(&&IfVettedOptionForPostIsFalse&&):
    #        bigString1 = bigString1 + Markup('{% if logged_in %}')
    #    bigString1 = bigString1 + Markup ('<tr><td class="col1">NoIcons</td>')  
    #    bigString1 = bigString1 + Markup('<td class="col2"><form action="/comments"><select class="selection" name="thread"><option value="' + &&JuliaInsertPostObectIDHere&& + '"></option></select><button type="submit" class="customButton commentButton">' + &&InsertPostTitleNameHere&& + '</button></form></td>')
    #    if(&&IfAnonymousOptionIsTrue&&):
    #        bigString1 = bigString1 + Markup('<td class="col3"> {% if logged_in %}' + &&InsertUserName&& + '{% endif %}</td>')
    #    else:
    #        bigString1 = bigString1 + Markup(
    #      <tr>
    #      <td class="col1">Image and tags(maybe)</td> 
    #      <td class="col2"><form action="/comments"><select class="selection" name="thread"><option value="u28d892qh1dj98d"></option></select><button type="submit" class="customButton commentButton">Hello Everyone</button></form></td>
    #      <td class="col3">by Ramon</td>
    #      <td class="col4">{% if logged_in %}<span><button type="button" class="btn btn-danger btn-sm" data-toggle="modal" data-target="#deleteModal">Delete</button><form action="/vet" method="post"><button type="submit" class="btn btn-warning btn-sm" name="vet" value="docid">Vet/Unvet</button></form>Time</span>{% endif %}</td>
    #    </tr>
    return render_template('specialeducationforum.html')

@app.route('/userSubmitPostELL', methods=['GET','POST'])
def renderUserPostSubmissionELL():
    connection_string = os.environ["MONGO_CONNECTION_STRING"]
    db_name = os.environ["MONGO_DBNAME"]
    client = pymongo.MongoClient(connection_string)
    db = client[db_name]
    today = datetime.today()
    #session['userTitle']=request.form['userTitle']
    #session['userComment']=request.form['userComment']
    #session['userName']=request.form['userName']
    #session['userStudent']=request.form['userStudent']
    #session['userEmail']=request.form['userEmail']
    anonymous = True
    if request.form.getlist('anonymous'):
        anonymous = True
    else:
        anonymous = False
    title = request.form['userTitle']
    message = request.form['userComment']
    name = session['userName']
    student = request.form['userStudent']
    email = request.form['userEmail']
    collection = db['ELLU']
    posts = {"comments": {"comment4":"comment 4", "comment5": "comment 5"},"postTitle":title,"postContent":message, "parentName": name, "studentName+grade": student, "parentEmail": email, "anonymous": anonymous,"dateTime": today, "approved":"false"}
    collection.insert_one(posts)
    return render_template('englishlearnerforum.html') #this will also copy the code from def render_english_learner_forum from above.

@app.route('/adminSubmitPostELL', methods=['GET', 'POST']) #Same as above, except no name, student name and grade, no anonymous, etc.
def renderAdminPostSubmissionELL():
    connection_string = os.environ["MONGO_CONNECTION_STRING"]
    db_name = os.environ["MONGO_DBNAME"]
    client = pymongo.MongoClient(connection_string)
    db = client[db_name]
    today = datetime.today()
    #session['adminTitle']=request.form['adminTitle']
    #session['adminComment']=request.form['adminComment']
    #session['adminName']=request.form['adminName']
    title = request.form['adminTitle']
    message = request.form['adminComment']
    name = request.form['adminName']
    collection = db['ELLA']
    posts = {"comments": {"comment4":"comment 4", "comment5": "comment 5"},"postTitle":title,"postContent":message,"displayName": name, "date+time": today}#put all info here using variables
    collection.insert_one(posts)
    return render_template('englishlearnerforum.html') #this will also copy the code from def render_english_learner_forum from above.

@app.route('/userSubmitPostSE', methods=['GET', 'POST']) #for the other forum
def renderUserPostSubmissionSE():
    connection_string = os.environ["MONGO_CONNECTION_STRING"]
    db_name = os.environ["MONGO_DBNAME"]
    client = pymongo.MongoClient(connection_string)
    db = client[db_name]
    today = datetime.today()
    #session['userTitle']=request.form['userTitle']
    #session['userComment']=request.form['userComment']
    #session['userName']=request.form['userName']
    #session['userStudent']=request.form['userStudent']
    #session['userEmail']=request.form['userEmail']
    anonymous = True
    if request.form.getlist('anonymous'):
        anonymous = True
    else:
        anonymous = False
    title = request.form['userTitle']
    message = request.form['userComment']
    name = session['userName']
    student = request.form['userStudent']
    email = request.form['userEmail']
    collection = db['SEU']
    posts = {"comments": {"comment4":"comment 4", "comment5": "comment 5"},"postTitle":title,"postContent":message, "parentName": name, "studentName+grade": student, "parentEmail": email, "anonymous": anonymous,"dateTime": today, "approved":"false"}
    collection.insert_one(posts)
    return render_template('specialeducationforum.html') #this will also copy the code from def special_education_forum from above.

@app.route('/adminSubmitPostSE', methods=['GET', 'POST'])
def renderAdminPostSubmissionSE():
    connection_string = os.environ["MONGO_CONNECTION_STRING"]
    db_name = os.environ["MONGO_DBNAME"]
    client = pymongo.MongoClient(connection_string)
    db = client[db_name]
    today = datetime.today()
    #session['adminTitle']=request.form['adminTitle']
    #session['adminComment']=request.form['adminComment']
    #session['adminName']=request.form['adminName']
    title = request.form['adminTitle']
    message = request.form['adminComment']
    name = request.form['adminName']
    collection = db['SEA']
    posts = {"comments": {"comment4":"comment 4", "comment5": "comment 5"},"postTitle":title,"postContent":message,"displayName": name, "date+time": today}#put all info here using variables
    collection.insert_one(posts)
    return render_template('specialeducationforum.html') #this will also copy the code from def special_education_forum from above.

@app.route('/comments')
def loadTheComments():
    objectIDPost = request.args['thread']
    return render_template('comments.html') #This gets the object ID of the post the user clicked on. Use this function to return the post and its comments using that object ID.

@app.route('/delete', methods=['GET', 'POST'])
def delete():
    objectIDPost = request.form['delete'] #delete post

@app.route('/vet', methods=['GET', 'POST'])
def vet():
    objectIDPost = request.form['vet'] #vet and unvet posts

#make sure the jinja variables use Markup 
@github.tokengetter
def get_github_oauth_token():
    return session['github_token']

if __name__ == '__main__':
    app.run()
