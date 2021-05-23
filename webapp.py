from flask import Flask, redirect, Markup, url_for, session, request, jsonify
from flask_oauthlib.client import OAuth
from flask import render_template
from bson.objectid import ObjectId

import pprint
import os
import sys
import pymongo
from datetime import datetime, timedelta
from pytz import timezone
import pytz

utc = pytz.utc
pacific = timezone('America/Los_Angeles')
fmtAM = '%m/%d/%Y, %H:%M:%S AM PT'
fmtPM = '%m/%d/%Y, %H:%M:%S PM PT'

app = Flask(__name__)

app.secret_key = os.environ['SECRET_KEY'] #used to sign session cookies
oauth = OAuth(app)
oauth.init_app(app) #initialize the app to be able to make requests for user information

admin1="Azuthedog1"
admin2="DanaLearnsToCode"
admin3="MyDSWAccount"
admin4="Korkz"
admin5="Ponmo"
admin6="piemusician"
admin7="Ramon-W"

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
            if session['user_data']['login'] == admin1 or session['user_data']['login'] == admin2 or session['user_data']['login'] == admin3 or session['user_data']['login'] == admin4 or session['user_data']['login'] == admin5 or session['user_data']['login'] == admin6 or session['user_data']['login'] == admin7:
                message='You were successfully logged in as ' + session['user_data']['login'] + '. Don\'t forget to log out before exiting this wbesite.'
            else:
                session.clear()
                message='Please sign in with a valid admin account. You attempted to log in as ' + session['user_data']['login'] + '. This is not an admin account. To log in as an admin you may need to log out of Github before attempting to log in again.'
        except Exception as inst:
            session.clear()
            print(inst)
            message='Unable to login, please try again.  '
    session['username'] = 'admin'
    return render_template('login.html', message=message)

@app.route('/englishlearnerforum')
def render_english_learner_forum():
    connection_string = os.environ["MONGO_CONNECTION_STRING"]
    db_name = os.environ["MONGO_DBNAME"]
    client = pymongo.MongoClient(connection_string)
    db = client[db_name]
    collection = db['ELLU']
    postList = []
    bigString1 = ""
    bigString2 = ""
    #try:
    if 'github_token' in session: #session['user_data']['login'] == admin1 or session['user_data']['login'] == admin2 or session['user_data']['login'] == admin3 or session['user_data']['login'] == admin4 or session['user_data']['login'] == admin5 or session['user_data']['login'] == admin6 or session['user_data']['login'] == admin7:
        for post in collection.find():
            bigString1 = bigString1 + Markup ('<tr><td class="col1"><img src="/static/images/person.png" alt="icon" width="30" height="30"></td>')  
            bigString1 = bigString1 + Markup('<td class="col2"><form action="/viewELLU"><select class="selection" name="thread"><option value="' + str(post.get('_id')) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form></td>')
            if post.get('parentEmail') == "":
                bigString1 = bigString1 + Markup('<td class="col3"><i>' + post.get('parentName') + ' / ' + post.get('studentName+grade') + ' / Email not provided</i></td>')
            else:
                bigString1 = bigString1 + Markup('<td class="col3"><i>' + post.get('parentName') + ' / ' + post.get('studentName+grade') + ' / ' + post.get('parentEmail') + '</i></td>')
            bigString1 = bigString1 + Markup('<td class="col4"><form action="/deleteELL" method="post"><button type="submit" class="btn btn-danger btn-sm" name="delete" value="' + str(post.get('_id')) + '"><span class="glyphicon glyphicon-trash"></span>Confirm Delete</button></form>')
            if(post.get('approved') == "false"):
                bigString1 = bigString1 + Markup('<form action="/vetELL" method="post"><button type="submit" class="btn btn-warning btn-sm" name="vet" value="' + str(post.get('_id'))+ '">' + '<span class="glyphicon glyphicon-plus"></span>Vet')
            else:
                bigString1 = bigString1 + Markup('<form action="/unvetELL" method="post"><button type="submit" class="btn btn-warning btn-sm" name="vet" value="' + str(post.get('_id'))+ '">' + '<span class="glyphicon glyphicon-minus">Unvet')
            bigString1 = bigString1 + Markup('</button></form><i>' + str(post.get('dateTime')) + '</i></td></tr>')
            postList.insert(0, bigString1)
            bigString1 = ""
    else:
        for post in collection.find():
            if(post.get('approved') == "true"):
                bigString1 = bigString1 + Markup ('<tr><td class="col1"><img src="/static/images/person.png" alt="icon" width="30" height="30"></span></td>')  
                bigString1 = bigString1 + Markup('<td class="col2"><form action="/viewELLU"><select class="selection" name="thread"><option value="' + str(post.get('_id')) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form></td>')
                if(post.get('anonymous') == "true"):
                    bigString1 = bigString1 + Markup('<td class="col3"><i>Anonymous Post</i></td>')
                else:
                    bigString1 = bigString1 + Markup('<td class="col3"><i>' + post.get('parentName') + '</i></td>')
                bigString1 = bigString1 + Markup('<td class="col4"><i>' + str(post.get('dateTime')) + '</i></td></tr>')
                postList.insert(0, bigString1)
                bigString1 = ""
    for item in postList:
        bigString1 = bigString1 + item
    postList.clear()
    collection = db['ELLA']
    #try:
    if 'github_token' in session: #if session['user_data']['login'] == admin1 or session['user_data']['login'] == admin2 or session['user_data']['login'] == admin3 or session['user_data']['login'] == admin4 or session['user_data']['login'] == admin5 or session['user_data']['login'] == admin6 or session['user_data']['login'] == admin7:
        for post in collection.find():
            bigString2 = bigString2 + Markup('<tr><td class="col1"><img src="/static/images/person.png" alt="icon" width="30" height="30"></td>' +
                                             '<td class="col2"><form action="/viewELLA"><select class="selection" name="thread"><option value="' + str(post.get('_id')) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form></td>' +
                                             '<td class="col3"><i>' + post.get('displayName') + '</i></td>' +
                                             '<td class="col4"><form action="/deleteELL" method="post"><button type="submit" class="btn btn-danger btn-sm lineUp" name="delete" value="' + str(post.get('_id')) + '"><span class="glyphicon glyphicon-trash"></span>Confirm Delete</button></form><i>' + str(post.get('dateTime')) + '</i></td></tr>')
            postList.insert(0, bigString2)
            bigString2 = ""
    else:
        for post in collection.find():
            bigString2 = bigString2 + Markup('<tr><td class="col1"><img src="/static/images/person.png" alt="icon" width="30" height="30"></span></td>' +
                                             '<td class="col2"><form action="/viewELLA"><select class="selection" name="thread"><option value="' + str(post.get('_id')) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form></td>' +
                                             '<td class="col3"><i>' + post.get('displayName') + '</i></td>' +
                                             '<td class="col4"><i>' + str(post.get('dateTime')) + '</i></td></tr>')
            postList.insert(0, bigString2)
            bigString2 = ""
    for item in postList:
        bigString2 = bigString2 + item
    return render_template('englishlearnerforum.html', ELLUPosts = bigString1, ELLAPosts = bigString2)

@app.route('/adminLog')
def render_admin_log():
    return render_template('adminlog.html')

@app.route('/specialeducationforum')
def render_special_education_forum():
    connection_string = os.environ["MONGO_CONNECTION_STRING"]
    db_name = os.environ["MONGO_DBNAME"]
    client = pymongo.MongoClient(connection_string)
    db = client[db_name]
    collection = db['SEU']
    postList = []
    bigString1 = ""
    bigString2 = ""
    #try:
    if 'github_token' in session: #if session['user_data']['login'] == admin1 or session['user_data']['login'] == admin2 or session['user_data']['login'] == admin3 or session['user_data']['login'] == admin4 or session['user_data']['login'] == admin5 or session['user_data']['login'] == admin6 or session['user_data']['login'] == admin7:
        for post in collection.find():
            bigString1 = bigString1 + Markup ('<tr><td class="col1"><img src="/static/images/person.png" alt="icon" width="30" height="30"></span></td>')  
            bigString1 = bigString1 + Markup('<td class="col2"><form action="/viewSEU"><select class="selection" name="thread"><option value="' + str(post.get('_id')) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form></td>')
            if post.get('parentEmail') == "":
                bigString1 = bigString1 + Markup('<td class="col3"><i>' + post.get('parentName') + ' / ' + post.get('studentName+grade') + ' / Email not provided</i></td>')
            else:
                bigString1 = bigString1 + Markup('<td class="col3"><i>' + post.get('parentName') + ' / ' + post.get('studentName+grade') + ' / ' + post.get('parentEmail') + '</i></td>')
            bigString1 = bigString1 + Markup('<td class="col4"><form action="/deleteSE" method="post"><button type="submit" class="btn btn-danger btn-sm lineUp" name="delete" value="' + str(post.get('_id')) + '"><span class="glyphicon glyphicon-trash"></span>Confirm Delete</button></form>')
            if(post.get('approved') == "false"):
                bigString1 = bigString1 + Markup('<form action="/vetSE" method="post"><button type="submit" class="btn btn-warning btn-sm" name="vet" value="' + str(post.get('_id'))+ '">' + '<span class="glyphicon glyphicon-plus"></span>Vet')
            else:
                bigString1 = bigString1 + Markup('<form action="/unvetSE" method="post"><button type="submit" class="btn btn-warning btn-sm" name="vet" value="' + str(post.get('_id'))+ '">' + '<span class="glyphicon glyphicon-minus">Unvet')
            year = int(post.get('dateTime').strftime("%Y"))
            month = int(post.get('dateTime').strftime("%m"))
            day = int(post.get('dateTime').strftime("%d"))
            if int(post.get('dateTime').strftime("%H")) > 12:
                hour = int(post.get('dateTime').strftime("%H")) - 12
            else:
                hour = int(post.get('dateTime').strftime("%H"))
            minute = int(post.get('dateTime').strftime("%M"))
            second = int(post.get('dateTime').strftime("%S"))
            utc_dt = datetime(year, month, day, hour, minute, second, tzinfo=utc)
            loc_dt = utc_dt.astimezone(pacific)
            if int(post.get('dateTime').strftime("%H")) > 12:
                loc_dt.strftime(fmtPM)
            else:
                loc_dt.strftime(fmtAM)
            bigString1 = bigString1 + Markup('</button></form><i>' + str(loc_dt) + 'TEST PLEASE</i></td></tr>')
            postList.insert(0, bigString1)
            bigString1 = ""
    else:
        for post in collection.find():
            if(post.get('approved') == "true"):
                bigString1 = bigString1 + Markup ('<tr><td class="col1"><img src="/static/images/person.png" alt="icon" width="30" height="30"></td>')  
                bigString1 = bigString1 + Markup('<td class="col2"><form action="/viewSEU"><select class="selection" name="thread"><option value="' + str(post.get('_id')) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form></td>')
                if(post.get('anonymous') == "true"):
                    bigString1 = bigString1 + Markup('<td class="col3"><i>Anonymous Post</i></td>')
                else:
                    bigString1 = bigString1 + Markup('<td class="col3"><i>' + post.get('parentName') + '</i></td>')
                bigString1 = bigString1 + Markup('<td class="col4"><i>' + str(post.get('dateTime')) + '</i></td></tr>')
                postList.insert(0, bigString1)
                bigString1 = ""
    for item in postList:
        bigString1 = bigString1 + item
    postList.clear()
    collection = db['SEA']
    #try:
    if 'github_token' in session: #if session['user_data']['login'] == admin1 or session['user_data']['login'] == admin2 or session['user_data']['login'] == admin3 or session['user_data']['login'] == admin4 or session['user_data']['login'] == admin5 or session['user_data']['login'] == admin6 or session['user_data']['login'] == admin7:
        for post in collection.find():
            bigString2 = bigString2 + Markup('<tr><td class="col1"><img src="/static/images/person.png" alt="icon" width="30" height="30"></td>' +
                                             '<td class="col2"><form action="/viewSEA"><select class="selection" name="thread"><option value="' + str(post.get('_id')) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form></td>' +
                                             '<td class="col3"><i>' + post.get('displayName') + '</i></td>' +
                                             '<td class="col4"><form action="/deleteSE" method="post"><button type="submit" class="btn btn-danger btn-sm lineUp" name="delete" value="' + str(post.get('_id')) + '"><span class="glyphicon glyphicon-trash"></span>Confirm Delete</button></form><i>' + str(post.get('dateTime')) + '</i></td></tr>')
            postList.insert(0, bigString2)
            bigString2 = ""
    else:
        for post in collection.find():
            bigString2 = bigString2 + Markup('<tr><td class="col1"><img src="/static/images/person.png" alt="icon" width="30" height="30"></td>' +
                                             '<td class="col2"><form action="/viewSEA"><select class="selection" name="thread"><option value="' + str(post.get('_id')) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form></td>' +
                                             '<td class="col3"><i>' + post.get('displayName') + '</i></td>' +
                                             '<td class="col4"><i>' + str(post.get('dateTime')) + '</i></td></tr>')
            postList.insert(0, bigString2)
            bigString2 = ""
    for item in postList:
        bigString2 = bigString2 + item
    return render_template('specialeducationforum.html', SEUPosts = bigString1, SEAPosts = bigString2)

@app.route('/userSubmitPostELL', methods=['GET','POST'])
def renderUserPostSubmissionELL():
    if request.method == 'POST':
        connection_string = os.environ["MONGO_CONNECTION_STRING"]
        db_name = os.environ["MONGO_DBNAME"]
        client = pymongo.MongoClient(connection_string)
        db = client[db_name]
        today = datetime.now()
        #if(int(today.strftime("%H")) + 5 > 12):
        #    hour = str(int(today.strftime("%H")) + 5 - 12)
        #    today = today.strftime("%m/%d/%Y, " + hour + ":%M AM PT")
        #else:
        #    hour = str(int(today.strftime("%H")) + 5)
        #    today = today.strftime("%m/%d/%Y, " + hour + ":%M PM PT")
        #today = today.strftime("%m/%d/%Y, %H:%M GMT")
        #session['userTitle']=request.form['userTitle']
        #session['userComment']=request.form['userComment']
        #session['userName']=request.form['userName']
        #session['userStudent']=request.form['userStudent']
        #session['userEmail']=request.form['userEmail']
        anonymous = request.form['anon']
        #if request.form('anon'): #getList
        #    anonymous = "true"
        #else:
        #    anonymous = "false"
        title = request.form['userTitle']
        message = Markup(request.form['userComment'])
        name = request.form['userName']
        student = request.form['userStudent']
        email = request.form['userEmail']
        collection = db['ELLU']
        posts = {"comments": {"comment4":"comment 4", "comment5": "comment 5"},"postTitle":title,"postContent":message, "parentName": name, "studentName+grade": student, "parentEmail": email, "anonymous": anonymous,"dateTime": today, "approved":"false"}
        collection.insert_one(posts)
        return render_english_learner_forum() #render_template('englishlearnerforum.html')
    else:
        return render_english_learner_forum()

@app.route('/adminSubmitPostELL', methods=['GET', 'POST']) #Same as above, except no name, student name and grade, no anonymous, etc.
def renderAdminPostSubmissionELL():
    if request.method == 'POST':
        connection_string = os.environ["MONGO_CONNECTION_STRING"]
        db_name = os.environ["MONGO_DBNAME"]
        client = pymongo.MongoClient(connection_string)
        db = client[db_name]
        today = datetime.now()
        #if(int(today.strftime("%H")) + 5 > 12):
        #    hour = str(int(today.strftime("%H")) + 5 - 12)
        #    today = today.strftime("%m/%d/%Y, " + hour + ":%M AM PT")
        #else:
        #    hour = str(int(today.strftime("%H")) + 5)
        #    today = today.strftime("%m/%d/%Y, " + hour + ":%M PM PT")
        #today = today.strftime("%m/%d/%Y, %H:%M GMT")
        #session['adminTitle']=request.form['adminTitle']
        #session['adminComment']=request.form['adminComment']
        #session['adminName']=request.form['adminName']
        title = request.form['adminTitle']
        message = Markup(request.form['adminComment'])
        name = request.form['adminName']
        collection = db['ELLA']
        posts = {"comments": {"comment4":"comment 4", "comment5": "comment 5"},"postTitle":title,"postContent":message,"displayName": name, "dateTime": today}#put all info here using variables
        collection.insert_one(posts)
        return render_english_learner_forum() #render_template('englishlearnerforum.html') #this will also copy the code from def render_english_learner_forum from above.
    else:
        return render_english_learner_forum()
    
@app.route('/userSubmitPostSE', methods=['GET', 'POST']) #for the other forum
def renderUserPostSubmissionSE():
    if request.method == 'POST':
        connection_string = os.environ["MONGO_CONNECTION_STRING"]
        db_name = os.environ["MONGO_DBNAME"]
        client = pymongo.MongoClient(connection_string)
        db = client[db_name]
        today = datetime.now()
        #if(int(today.strftime("%H")) + 5 > 12):
        #    hour = str(int(today.strftime("%H")) + 5 - 12)
        #    today = today.strftime("%m/%d/%Y, " + hour + ":%M AM PT")
        #else:
        #    hour = str(int(today.strftime("%H")) + 5)
        #    today = today.strftime("%m/%d/%Y, " + hour + ":%M PM PT")
        #today = today.strftime("%m/%d/%Y, %H:%M GMT")
        #session['userTitle']=request.form['userTitle']
        #session['userComment']=request.form['userComment']
        #session['userName']=request.form['userName']
        #session['userStudent']=request.form['userStudent']
        #session['userEmail']=request.form['userEmail']
        anonymous = request.form['anon']
        #if request.form('anon'): #getList
        #    anonymous = "true"
        #else:
        #    anonymous = "false"
        title = request.form['userTitle']
        message = Markup(request.form['userComment'])
        name = request.form['userName']
        student = request.form['userStudent']
        email = request.form['userEmail']
        collection = db['SEU']
        posts = {"comments": {"comment4":"comment 4", "comment5": "comment 5"},"postTitle":title,"postContent":message, "parentName": name, "studentName+grade": student, "parentEmail": email, "anonymous": anonymous,"dateTime": today, "approved":"false"}
        collection.insert_one(posts)
        return render_special_education_forum() #render_template('specialeducationforum.html') #this will also copy the code from def special_education_forum from above.
    else:
        return render_special_education_forum()

@app.route('/adminSubmitPostSE', methods=['GET', 'POST'])
def renderAdminPostSubmissionSE():
    if request.method == 'POST':
        connection_string = os.environ["MONGO_CONNECTION_STRING"]
        db_name = os.environ["MONGO_DBNAME"]
        client = pymongo.MongoClient(connection_string)
        db = client[db_name]
        today = datetime.now()
        #if(int(today.strftime("%H")) + 5 > 12):
        #    hour = str(int(today.strftime("%H")) + 5 - 12)
        #    today = today.strftime("%m/%d/%Y, " + hour + ":%M AM PT")
        #else:
        #    hour = str(int(today.strftime("%H")) + 5)
        #    today = today.strftime("%m/%d/%Y, " + hour + ":%M PM PT")
        #today = today.strftime("%m/%d/%Y, %H:%M GMT")
        #session['adminTitle']=request.form['adminTitle']
        #session['adminComment']=request.form['adminComment']
        #session['adminName']=request.form['adminName']
        title = request.form['adminTitle']
        message = Markup(request.form['adminComment'])
        name = request.form['adminName']
        collection = db['SEA']
        posts = {"comments": {"comment4":"comment 4", "comment5": "comment 5"},"postTitle":title,"postContent":message,"displayName": name, "dateTime": today}#put all info here using variables
        collection.insert_one(posts)
        return render_special_education_forum()
    else:
        return render_special_education_forum()

@app.route('/submitCommentA', methods=['GET', 'POST'])
def newCommentA():
    #if request.method == 'POST':
    objectIDPost = request.args['thread']
        #connection_string = os.environ["MONGO_CONNECTION_STRING"]
        #db_name = os.environ["MONGO_DBNAME"]
        #client = pymongo.MongoClient(connection_string)
        #db = client[db_name]
        #collection = db['SEA']
        #x = collection.find_one({'_id': ObjectId(objectIDPost)})
        #if x == None:
        #    collection = db['SEU']
        #    x = collection.find_one({'_id': ObjectId(objectIDPost)})
        #if x == None:
        #    collection = db['ELLA']
        #    x = collection.find_one({'_id': ObjectId(objectIDPost)})
        #if x == None:
        #    collection = db['ELLU']
        #    x = collection.find_one({'_id': ObjectId(objectIDPost)})
        #name = request.form['adminName']
        #comment = request.form['adminComment']
        #myquery = { "address": "Valley 345" }
        #newvalues = { "$set": { "address": "Canyon 123" } }
        #collection.update_one({'_id': ObjectId(objectIDPost)}, newvalues)
        
        #collection.find_one_and_update(
        #    {"_id" : ObjectId("5cfa4c0ad9edff487939dda0")},
        #    {"$currentDate": {"some date": True}},
        #    upsert = True
        #)
        #return render_template('information.html')
    #else:
    return render_template('information.html')

@app.route('/submitCommentU', methods=['GET', 'POST'])
def newCommentU():
    if request.method == 'POST':
        objectIDPost = request.args['thread']
    return render_template('information.html')

@app.route('/viewSEA')
def viewSEA():
    objectIDPost = request.args['thread']
    connection_string = os.environ["MONGO_CONNECTION_STRING"]
    db_name = os.environ["MONGO_DBNAME"]
    client = pymongo.MongoClient(connection_string)
    db = client[db_name]
    collection = db['SEA']
    x = collection.find_one({'_id': ObjectId(objectIDPost)})
    postTitle = x.get('postTitle')
    postContent = x.get('postContent')
    dateTime = x.get('dateTime')
    displayName = x.get('displayName')
    info = ""
    return render_template('comments.html', title = postTitle, name = displayName, information = info, time = dateTime, content = postContent)

@app.route('/viewSEU')
def viewSEU():
    objectIDPost = request.args['thread']
    connection_string = os.environ["MONGO_CONNECTION_STRING"]
    db_name = os.environ["MONGO_DBNAME"]
    client = pymongo.MongoClient(connection_string)
    db = client[db_name]
    collection = db['SEU']
    x = collection.find_one({'_id': ObjectId(objectIDPost)})
    postTitle = x.get('postTitle')
    postContent = x.get('postContent')
    dateTime = x.get('dateTime')
    if 'github_token' in session:
        parentName = x.get('parentName')
        studentNameGrade = x.get('studentName+grade')
        parentEmail = x.get('parentEmail')
        if parentEmail == "":
            parentEmail = "Email not provided"
    else:
        if x.get('anonymous') == "false":
            parentName = x.get('parentName')
        else:
            parentName = "Anonymous Post"
        studentNameGrade = ""
        parentEmail = ""
    info = " / " + studentNameGrade + " / " + parentEmail
    return render_template('comments.html', title = postTitle, name = parentName, information = info, time = dateTime, content = postContent)

@app.route('/viewELLA')
def viewELLA():
    objectIDPost = request.args['thread']
    connection_string = os.environ["MONGO_CONNECTION_STRING"]
    db_name = os.environ["MONGO_DBNAME"]
    client = pymongo.MongoClient(connection_string)
    db = client[db_name]
    collection = db['ELLA']
    x = collection.find_one({'_id': ObjectId(objectIDPost)})
    postTitle = x.get('postTitle')
    postContent = x.get('postContent')
    dateTime = x.get('dateTime')
    displayName = x.get('displayName')
    info = ""
    return render_template('comments.html', title = postTitle, name = displayName, information = info, time = dateTime, content = postContent)

@app.route('/viewELLU')
def viewELLU():
    objectIDPost = request.args['thread']
    connection_string = os.environ["MONGO_CONNECTION_STRING"]
    db_name = os.environ["MONGO_DBNAME"]
    client = pymongo.MongoClient(connection_string)
    db = client[db_name]
    collection = db['ELLU']
    x = collection.find_one({'_id': ObjectId(objectIDPost)})
    postTitle = x.get('postTitle')
    postContent = x.get('postContent')
    dateTime = x.get('dateTime')
    if 'github_token' in session:
        parentName = x.get('parentName')
        studentNameGrade = x.get('studentName+grade')
        parentEmail = x.get('parentEmail')
        if parentEmail == "":
            parentEmail = "Email not provided"
    else:
        if x.get('anonymous') == "false":
            parentName = x.get('parentName')
        else:
            parentName = "Anonymous Post"
        studentNameGrade = ""
        parentEmail = ""
    info = " / " + studentNameGrade + " / " + parentEmail
    return render_template('comments.html', title = postTitle, name = parentName, information = info, time = dateTime, content = postContent)

@app.route('/deleteSE', methods=['GET', 'POST'])
def deleteSE():
    if request.method == 'POST':
        objectIDPost = request.form['delete'] #delete post
        connection_string = os.environ["MONGO_CONNECTION_STRING"]
        db_name = os.environ["MONGO_DBNAME"]
        client = pymongo.MongoClient(connection_string)
        db = client[db_name]
        collection = db['SEA']
        collection.delete_one({'_id': ObjectId(objectIDPost)})
        collection = db['SEU']
        collection.delete_one({'_id': ObjectId(objectIDPost)})
        return render_special_education_forum()
    else:
        return render_special_education_forum()

@app.route('/deleteELL', methods=['GET', 'POST'])
def deleteELL():
    if request.method == 'POST':
        objectIDPost = request.form['delete'] #delete post
        connection_string = os.environ["MONGO_CONNECTION_STRING"]
        db_name = os.environ["MONGO_DBNAME"]
        client = pymongo.MongoClient(connection_string)
        db = client[db_name]
        collection = db['ELLA']
        collection.delete_one({'_id': ObjectId(objectIDPost)})
        collection = db['ELLU']
        collection.delete_one({'_id': ObjectId(objectIDPost)})
        return render_english_learner_forum()
    else:
        return render_english_learner_forum()

@app.route('/vetELL', methods=['GET', 'POST'])
def vetELL():
    if request.method == 'POST':
        objectIDPost = request.form['vet'] #vet and unvet posts
        connection_string = os.environ["MONGO_CONNECTION_STRING"]
        db_name = os.environ["MONGO_DBNAME"]
        client = pymongo.MongoClient(connection_string)
        db = client[db_name]
        collection = db['ELLU']
        collection.find_one_and_update({"_id": ObjectId(objectIDPost)},
                                       {"$set": {"approved": "true"}})
        return render_english_learner_forum()
    else:
        return render_english_learner_forum()
                                             
@app.route('/unvetELL', methods=['GET', 'POST'])
def unvetELL():
    if request.method == 'POST':
        objectIDPost = request.form['vet'] #vet and unvet posts
        connection_string = os.environ["MONGO_CONNECTION_STRING"]
        db_name = os.environ["MONGO_DBNAME"]
        client = pymongo.MongoClient(connection_string)
        db = client[db_name]
        collection = db['ELLU']
        collection.find_one_and_update({"_id": ObjectId(objectIDPost)},
                                       {"$set": {"approved": "false"}})
        return render_english_learner_forum()
    else:
        return render_english_learner_forum()

                                             
@app.route('/vetSE', methods=['GET', 'POST'])
def vetSE():
    if request.method == 'POST':
        objectIDPost = request.form['vet'] #vet and unvet posts
        connection_string = os.environ["MONGO_CONNECTION_STRING"]
        db_name = os.environ["MONGO_DBNAME"]
        client = pymongo.MongoClient(connection_string)
        db = client[db_name]       
        collection = db['SEU']
        collection.find_one_and_update({"_id": ObjectId(objectIDPost)},
                                       {"$set": {"approved": "true"}})
        return render_special_education_forum()
    else:
        return render_special_education_forum()
                                             
@app.route('/unvetSE', methods=['GET', 'POST'])
def unvetSE():
    if request.method == 'POST':
        objectIDPost = request.form['vet'] #vet and unvet posts
        connection_string = os.environ["MONGO_CONNECTION_STRING"]
        db_name = os.environ["MONGO_DBNAME"]
        client = pymongo.MongoClient(connection_string)
        db = client[db_name]
        collection = db['SEU']
        collection.find_one_and_update({"_id": ObjectId(objectIDPost)},
                                       {"$set": {"approved": "false"}})
        return render_special_education_forum()
    else:
        return render_special_education_forum()

#make sure the jinja variables use Markup 
@github.tokengetter
def get_github_oauth_token():
    return session['github_token']

if __name__ == '__main__':
    app.run()
