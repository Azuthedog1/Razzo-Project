#note: implement standardized quotes and better concatenation for strings, postContent and commentContent modifications when creating new document 
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
    return render_template('login.html', message='&nbsp;&nbsp;You were logged out')

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
                message='&nbsp;&nbsp;You were successfully logged in as ' + session['user_data']['login'] + '. Don\'t forget to log out before exiting this wbesite.'
            else:
                session.clear()
                message='&nbsp;&nbsp;Please sign in with a valid admin account. You attempted to log in as ' + session['user_data']['login'] + '. This is not an admin account. To log in as an admin you may need to log out of Github before attempting to log in again.'
        except Exception as inst:
            session.clear()
            print(inst)
            message='&nbsp;&nbsp;Unable to login, please try again.'
    session['username'] = 'admin'
    return render_template('login.html', message = message)

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
    if 'github_token' in session:
        for post in collection.find():
            bigString1 += '<tr><td class="col1"><img src="/static/images/person.png" alt="icon" width="30" height="30"></td>'
            bigString1 += '<td class="col2"><form action="/viewELLU"><select class="selection" name="thread"><option value="' + str(post.get('_id')) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form></td>'
            if post.get('parentEmail') == "":
                bigString1 += '<td class="col3"><i>' + post.get('parentName') + ' / ' + post.get('studentNameGrade') + ' / Email not provided</i></td>'
            else:
                bigString1 += '<td class="col3"><i>' + post.get('parentName') + ' / ' + post.get('studentNameGrade') + ' / ' + post.get('parentEmail') + '</i></td>'
            bigString1 += '<td class="col4"><form action="/deleteELL" method="post"><button type="submit" class="btn btn-danger btn-sm" name="delete" value="' + str(post.get('_id')) + '"><span class="glyphicon glyphicon-trash"></span>Confirm Delete</button></form>'
            if(post.get('approved') == "false"):
                bigString1 += '<form action="/vetELL" method="post"><button type="submit" class="btn btn-warning btn-sm" name="vet" value="' + str(post.get('_id'))+ '">' + '<span class="glyphicon glyphicon-plus"></span>Vet'
            else:
                bigString1 += '<form action="/unvetELL" method="post"><button type="submit" class="btn btn-warning btn-sm" name="vet" value="' + str(post.get('_id'))+ '">' + '<span class="glyphicon glyphicon-minus"></span>Unvet'
            utc_dt = datetime(int(post.get('dateTime').strftime("%Y")), int(post.get('dateTime').strftime("%m")), int(post.get('dateTime').strftime("%d")), int(post.get('dateTime').strftime("%H")), int(post.get('dateTime').strftime("%M")), 0, tzinfo=pytz.utc)
            loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
            if int(loc_dt.strftime("%H")) > 12:
                hour = str(int(loc_dt.strftime("%H")) - 12)
                loc_dt = loc_dt.strftime("%m/%d/%Y, " + hour + ":%M PM PT")
            else:
                loc_dt = loc_dt.strftime("%m/%d/%Y, %H:%M AM PT")
            bigString1 += '</button></form><i>' + loc_dt + '</i></td></tr>'
            postList.insert(0, bigString1)
            bigString1 = ""
    else:
        for post in collection.find():
            if(post.get('approved') == "true"):
                bigString1 += '<tr><td class="col1"><img src="/static/images/person.png" alt="icon" width="30" height="30"></td>'
                bigString1 += '<td class="col2"><form action="/viewELLU"><select class="selection" name="thread"><option value="' + str(post.get('_id')) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form></td>'
                if(post.get('anonymous') == "true"):
                    bigString1 += '<td class="col3"><i>Anonymous Post</i></td>'
                else:
                    bigString1 += '<td class="col3"><i>' + post.get('parentName') + '</i></td>'
                utc_dt = datetime(int(post.get('dateTime').strftime("%Y")), int(post.get('dateTime').strftime("%m")), int(post.get('dateTime').strftime("%d")), int(post.get('dateTime').strftime("%H")), int(post.get('dateTime').strftime("%M")), 0, tzinfo=pytz.utc)
                loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
                if int(loc_dt.strftime("%H")) > 12:
                    hour = str(int(loc_dt.strftime("%H")) - 12)
                    loc_dt = loc_dt.strftime("%m/%d/%Y, " + hour + ":%M PM PT")
                else:
                    loc_dt = loc_dt.strftime("%m/%d/%Y, %H:%M AM PT")
                bigString1 += '<td class="col4"><i>' + loc_dt + '</i></td></tr>'
                postList.insert(0, bigString1)
                bigString1 = ""
    for item in postList:
        bigString1 += item
    postList.clear()
    collection = db['ELLA']
    if 'github_token' in session: 
        for post in collection.find():
            utc_dt = datetime(int(post.get('dateTime').strftime("%Y")), int(post.get('dateTime').strftime("%m")), int(post.get('dateTime').strftime("%d")), int(post.get('dateTime').strftime("%H")), int(post.get('dateTime').strftime("%M")), 0, tzinfo=pytz.utc)
            loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
            if int(loc_dt.strftime("%H")) > 12:
                hour = str(int(loc_dt.strftime("%H")) - 12)
                loc_dt = loc_dt.strftime("%m/%d/%Y, " + hour + ":%M PM PT")
            else:
                loc_dt = loc_dt.strftime("%m/%d/%Y, %H:%M AM PT")
            bigString2 += ('<tr><td class="col1"><img src="/static/images/person.png" alt="icon" width="30" height="30"></td>' +
                           '<td class="col2"><form action="/viewELLA"><select class="selection" name="thread"><option value="' + str(post.get('_id')) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form></td>' +
                           '<td class="col3"><i>' + post.get('adminName') + '</i></td>' +
                           '<td class="col4"><form action="/deleteELL" method="post"><button type="submit" class="btn btn-danger btn-sm lineUp" name="delete" value="' + str(post.get('_id')) + '"><span class="glyphicon glyphicon-trash"></span>Confirm Delete</button></form><i>' + loc_dt + '</i></td></tr>')
            postList.insert(0, bigString2)
            bigString2 = ""
    else:
        for post in collection.find():
            utc_dt = datetime(int(post.get('dateTime').strftime("%Y")), int(post.get('dateTime').strftime("%m")), int(post.get('dateTime').strftime("%d")), int(post.get('dateTime').strftime("%H")), int(post.get('dateTime').strftime("%M")), 0, tzinfo=pytz.utc)
            loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
            if int(loc_dt.strftime("%H")) > 12:
                hour = str(int(loc_dt.strftime("%H")) - 12)
                loc_dt = loc_dt.strftime("%m/%d/%Y, " + hour + ":%M PM PT")
            else:
                loc_dt = loc_dt.strftime("%m/%d/%Y, %H:%M AM PT")
            bigString2 += ('<tr><td class="col1"><img src="/static/images/person.png" alt="icon" width="30" height="30"></td>' +
                           '<td class="col2"><form action="/viewELLA"><select class="selection" name="thread"><option value="' + str(post.get('_id')) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form></td>' +
                           '<td class="col3"><i>' + post.get('adminName') + '</i></td>' +
                           '<td class="col4"><i>' + loc_dt + '</i></td></tr>')
            postList.insert(0, bigString2)
            bigString2 = ""
    for item in postList:
        bigString2 += item
    return render_template('englishlearnerforum.html', ELLUPosts = Markup(bigString1), ELLAPosts = Markup(bigString2))

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
    if 'github_token' in session:
        for post in collection.find():
            bigString1 += '<tr><td class="col1"><img src="/static/images/person.png" alt="icon" width="30" height="30"></td>'
            bigString1 += '<td class="col2"><form action="/viewELLU"><select class="selection" name="thread"><option value="' + str(post.get('_id')) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form></td>'
            if post.get('parentEmail') == "":
                bigString1 += '<td class="col3"><i>' + post.get('parentName') + ' / ' + post.get('studentNameGrade') + ' / Email not provided</i></td>'
            else:
                bigString1 += '<td class="col3"><i>' + post.get('parentName') + ' / ' + post.get('studentNameGrade') + ' / ' + post.get('parentEmail') + '</i></td>'
            bigString1 += '<td class="col4"><form action="/deleteELL" method="post"><button type="submit" class="btn btn-danger btn-sm" name="delete" value="' + str(post.get('_id')) + '"><span class="glyphicon glyphicon-trash"></span>Confirm Delete</button></form>'
            if(post.get('approved') == "false"):
                bigString1 += '<form action="/vetELL" method="post"><button type="submit" class="btn btn-warning btn-sm" name="vet" value="' + str(post.get('_id'))+ '">' + '<span class="glyphicon glyphicon-plus"></span>Vet'
            else:
                bigString1 += '<form action="/unvetELL" method="post"><button type="submit" class="btn btn-warning btn-sm" name="vet" value="' + str(post.get('_id'))+ '">' + '<span class="glyphicon glyphicon-minus"></span>Unvet'
            utc_dt = datetime(int(post.get('dateTime').strftime("%Y")), int(post.get('dateTime').strftime("%m")), int(post.get('dateTime').strftime("%d")), int(post.get('dateTime').strftime("%H")), int(post.get('dateTime').strftime("%M")), 0, tzinfo=pytz.utc)
            loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
            if int(loc_dt.strftime("%H")) > 12:
                hour = str(int(loc_dt.strftime("%H")) - 12)
                loc_dt = loc_dt.strftime("%m/%d/%Y, " + hour + ":%M PM PT")
            else:
                loc_dt = loc_dt.strftime("%m/%d/%Y, %H:%M AM PT")
            bigString1 += '</button></form><i>' + loc_dt + '</i></td></tr>'
            postList.insert(0, bigString1)
            bigString1 = ""
    else:
        for post in collection.find():
            if(post.get('approved') == "true"):
                bigString1 += '<tr><td class="col1"><img src="/static/images/person.png" alt="icon" width="30" height="30"></td>'
                bigString1 += '<td class="col2"><form action="/viewELLU"><select class="selection" name="thread"><option value="' + str(post.get('_id')) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form></td>'
                if(post.get('anonymous') == "true"):
                    bigString1 += '<td class="col3"><i>Anonymous Post</i></td>'
                else:
                    bigString1 += '<td class="col3"><i>' + post.get('parentName') + '</i></td>'
                utc_dt = datetime(int(post.get('dateTime').strftime("%Y")), int(post.get('dateTime').strftime("%m")), int(post.get('dateTime').strftime("%d")), int(post.get('dateTime').strftime("%H")), int(post.get('dateTime').strftime("%M")), 0, tzinfo=pytz.utc)
                loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
                if int(loc_dt.strftime("%H")) > 12:
                    hour = str(int(loc_dt.strftime("%H")) - 12)
                    loc_dt = loc_dt.strftime("%m/%d/%Y, " + hour + ":%M PM PT")
                else:
                    loc_dt = loc_dt.strftime("%m/%d/%Y, %H:%M AM PT")
                bigString1 += '<td class="col4"><i>' + loc_dt + '</i></td></tr>'
                postList.insert(0, bigString1)
                bigString1 = ""
    for item in postList:
        bigString1 += item
    postList.clear()
    collection = db['SEA']
    if 'github_token' in session: 
        for post in collection.find():
            utc_dt = datetime(int(post.get('dateTime').strftime("%Y")), int(post.get('dateTime').strftime("%m")), int(post.get('dateTime').strftime("%d")), int(post.get('dateTime').strftime("%H")), int(post.get('dateTime').strftime("%M")), 0, tzinfo=pytz.utc)
            loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
            if int(loc_dt.strftime("%H")) > 12:
                hour = str(int(loc_dt.strftime("%H")) - 12)
                loc_dt = loc_dt.strftime("%m/%d/%Y, " + hour + ":%M PM PT")
            else:
                loc_dt = loc_dt.strftime("%m/%d/%Y, %H:%M AM PT")
            bigString2 += ('<tr><td class="col1"><img src="/static/images/person.png" alt="icon" width="30" height="30"></td>' +
                           '<td class="col2"><form action="/viewELLA"><select class="selection" name="thread"><option value="' + str(post.get('_id')) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form></td>' +
                           '<td class="col3"><i>' + post.get('adminName') + '</i></td>' +
                           '<td class="col4"><form action="/deleteELL" method="post"><button type="submit" class="btn btn-danger btn-sm lineUp" name="delete" value="' + str(post.get('_id')) + '"><span class="glyphicon glyphicon-trash"></span>Confirm Delete</button></form><i>' + loc_dt + '</i></td></tr>')
            postList.insert(0, bigString2)
            bigString2 = ""
    else:
        for post in collection.find():
            utc_dt = datetime(int(post.get('dateTime').strftime("%Y")), int(post.get('dateTime').strftime("%m")), int(post.get('dateTime').strftime("%d")), int(post.get('dateTime').strftime("%H")), int(post.get('dateTime').strftime("%M")), 0, tzinfo=pytz.utc)
            loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
            if int(loc_dt.strftime("%H")) > 12:
                hour = str(int(loc_dt.strftime("%H")) - 12)
                loc_dt = loc_dt.strftime("%m/%d/%Y, " + hour + ":%M PM PT")
            else:
                loc_dt = loc_dt.strftime("%m/%d/%Y, %H:%M AM PT")
            bigString2 += ('<tr><td class="col1"><img src="/static/images/person.png" alt="icon" width="30" height="30"></td>' +
                           '<td class="col2"><form action="/viewELLA"><select class="selection" name="thread"><option value="' + str(post.get('_id')) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form></td>' +
                           '<td class="col3"><i>' + post.get('adminName') + '</i></td>' +
                           '<td class="col4"><i>' + loc_dt + '</i></td></tr>')
            postList.insert(0, bigString2)
            bigString2 = ""
    for item in postList:
        bigString2 += item
    return render_template('specialeducationforum.html', SEUPosts = Markup(bigString1), SEAPosts = Markup(bigString2))

@app.route('/userSubmitPostELL', methods=['GET','POST'])
def renderUserPostSubmissionELL():
    if request.method == 'POST':
        connection_string = os.environ["MONGO_CONNECTION_STRING"]
        db_name = os.environ["MONGO_DBNAME"]
        client = pymongo.MongoClient(connection_string)
        db = client[db_name]
        collection = db['ELLU']
        content = request.form['userMessage']
        content = content.replace('\\"', '')
        content = Markup(content[1:len(content)-1])
        post = {"postTitle": request.form['userTitle'], "parentName": request.form['userName'], "studentNameGrade": request.form['userStudent'], "parentEmail": request.form['userEmail'], "anonymous": request.form['anon'], "dateTime": datetime.now(), "postContent": content, "approved": "false"}
        collection.insert_one(post)
    return render_english_learner_forum()

@app.route('/adminSubmitPostELL', methods=['GET', 'POST']) #Same as above, except no name, student name and grade, no anonymous, etc.
def renderAdminPostSubmissionELL():
    if request.method == 'POST':
        connection_string = os.environ["MONGO_CONNECTION_STRING"]
        db_name = os.environ["MONGO_DBNAME"]
        client = pymongo.MongoClient(connection_string)
        db = client[db_name]
        collection = db['ELLA']
        content = request.form['adminMessage']
        content = content.replace('\\"', '')
        content = Markup(content[1:len(content)-1])
        post = {"postTitle": request.form['adminTitle'], "adminName": request.form['adminName'], "dateTime": datetime.now(), "postContent": content}#put all info here using variables
        collection.insert_one(post)
    return render_english_learner_forum() #this will also copy the code from def render_english_learner_forum from above.
    
@app.route('/userSubmitPostSE', methods=['GET', 'POST'])
def renderUserPostSubmissionSE():
    if request.method == 'POST':
        connection_string = os.environ["MONGO_CONNECTION_STRING"]
        db_name = os.environ["MONGO_DBNAME"]
        client = pymongo.MongoClient(connection_string)
        db = client[db_name]
        collection = db['SEU']
        content = request.form['userMessage']
        content = content.replace('\\"', '')
        content = Markup(content[1:len(content)-1])
        post = {"postTitle": request.form['userTitle'], "parentName": request.form['userName'], "studentNameGrade": request.form['userStudent'], "parentEmail": request.form['userEmail'], "anonymous": request.form['anon'], "dateTime": datetime.now(), "postContent": content, "approved": "false"}
        collection.insert_one(post)
    return render_special_education_forum()

@app.route('/adminSubmitPostSE', methods=['GET', 'POST'])
def renderAdminPostSubmissionSE():
    if request.method == 'POST':
        connection_string = os.environ["MONGO_CONNECTION_STRING"]
        db_name = os.environ["MONGO_DBNAME"]
        client = pymongo.MongoClient(connection_string)
        db = client[db_name]
        collection = db['SEA']
        content = request.form['adminMessage']
        content = content.replace('\\"', '')
        content = Markup(content[1:len(content)-1])
        post = {"postTitle": request.form['adminTitle'], "adminName": request.form['adminName'], "dateTime": datetime.now(), "postContent": content}#put all info here using variables
        collection.insert_one(post)
    return render_special_education_forum()

@app.route('/submitComment', methods=['GET', 'POST'])
def submitComment():
    if request.method == 'POST':
        objectIDPost = request.form['ID']
        connection_string = os.environ["MONGO_CONNECTION_STRING"]
        db_name = os.environ["MONGO_DBNAME"]
        client = pymongo.MongoClient(connection_string)
        db = client[db_name]
        collection = db['SEA']
        post = collection.find_one({'_id': ObjectId(objectIDPost)})
        if post == None:
            collection = db['SEU']
            post = collection.find_one({'_id': ObjectId(objectIDPost)})
        if post == None:
            collection = db['ELLA']
            post = collection.find_one({'_id': ObjectId(objectIDPost)})
        if post == None:
            collection = db['ELLU']
            post = collection.find_one({'_id': ObjectId(objectIDPost)})
        keyList = list(post.keys())
        if "comment" in keyList[-1]:
            lastNumber = keyList[-1]
            lastNumber = lastNumber.replace('comment', '')
            lastNumber = str(int(lastNumber) + 1)
        else:
            lastNumber = "0"
        if 'github_token' in session:
            content = request.form['adminMessage']
            content = content.replace('\\"', '')
            content = Markup(content[1:len(content)-1])
            post["comment" + lastNumber] = {"adminName": request.form['adminName'], "dateTime": datetime.now(), "postContent": content}
            collection.delete_one({'_id': ObjectId(objectIDPost)})
            collection.insert_one(post)
        else:
            content = request.form['userMessage']
            content = content.replace('\\"', '')
            content = Markup(content[1:len(content)-1])
            post["comment" + lastNumber] = {"parentName": request.form['userName'], "studentNameGrade": request.form['userStudent'], "anonymous": request.form['anon'], "dateTime": datetime.now(), "postContent": content, "approved": "false"}
            collection.delete_one({'_id': ObjectId(objectIDPost)})
            collection.insert_one(post)
    return render_template('information.html')

@app.route('/viewSEA')
def viewSEA():
    objectIDPost = request.args['thread']
    connection_string = os.environ["MONGO_CONNECTION_STRING"]
    db_name = os.environ["MONGO_DBNAME"]
    client = pymongo.MongoClient(connection_string)
    db = client[db_name]
    collection = db['SEA']
    post = collection.find_one({'_id': ObjectId(objectIDPost)})
    postTitle = post.get('postTitle')
    postContent = post.get('postContent')
    utc_dt = datetime(int(post.get('dateTime').strftime("%Y")), int(post.get('dateTime').strftime("%m")), int(post.get('dateTime').strftime("%d")), int(post.get('dateTime').strftime("%H")), int(post.get('dateTime').strftime("%M")), 0, tzinfo=pytz.utc)
    loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
    if int(loc_dt.strftime("%H")) > 12:
        hour = str(int(loc_dt.strftime("%H")) - 12)
        loc_dt = loc_dt.strftime("%m/%d/%Y, " + hour + ":%M PM PT")
    else:
        loc_dt = loc_dt.strftime("%m/%d/%Y, %H:%M AM PT")
    displayName = post.get('adminName')
    bigString = ''
    keyList = list(post.keys())
    commentAmount = 0
    for item in keyList:
        if "comment" in item:
            commentAmount += 1
    bigString = ''
    counter = 0
    i = 0
    if 'github_token' in session: #if admin is logged in
        while counter < commentAmount:
            if("comment" + str(i) in post):
                utc_dt = datetime(int(post.get("comment" + str(i), {}).get("dateTime").strftime("%Y")), int(post.get("comment" + str(i), {}).get("dateTime").strftime("%m")), int(post.get("comment" + str(i), {}).get("dateTime").strftime("%d")), int(post.get("comment" + str(i), {}).get("dateTime").strftime("%H")), int(post.get("comment" + str(i), {}).get("dateTime").strftime("%M")), 0, tzinfo=pytz.utc)
                loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
                if int(loc_dt.strftime("%H")) > 12:
                    hour = str(int(loc_dt.strftime("%H")) - 12)
                    loc_dt = loc_dt.strftime("%m/%d/%Y, " + hour + ":%M PM PT")
                else:
                    loc_dt = loc_dt.strftime("%m/%d/%Y, %H:%M AM PT")
                if post.get("comment" + str(i), {}).get("adminName") != None: #checks if it is admin post
                    bigString += '<tr><td class="comments"><b>' + post.get("comment" + str(i), {}).get("adminName") + ' (Staff)</b><br><i>' + loc_dt + '</i><br><br>' + post.get("comment" + str(i), {}).get("postContent") + '</td></tr>'
                else:
                    bigString += '<tr><td class="comments"><b>' + post.get("comment" + str(i), {}).get("parentName") + '</b> / ' + post.get("comment" + str(i), {}).get("studentNameGrade") + '<br><i>' + loc_dt + '</i><br><br>' + post.get("comment" + str(i), {}).get("postContent") + '</td></tr>'
                counter += 1
            i += 1
    else:
        while counter < commentAmount:
            if("comment" + str(i) in post):
                utc_dt = datetime(int(post.get("comment" + str(i), {}).get("dateTime").strftime("%Y")), int(post.get("comment" + str(i), {}).get("dateTime").strftime("%m")), int(post.get("comment" + str(i), {}).get("dateTime").strftime("%d")), int(post.get("comment" + str(i), {}).get("dateTime").strftime("%H")), int(post.get("comment" + str(i), {}).get("dateTime").strftime("%M")), 0, tzinfo=pytz.utc)
                loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
                if int(loc_dt.strftime("%H")) > 12:
                    hour = str(int(loc_dt.strftime("%H")) - 12)
                    loc_dt = loc_dt.strftime("%m/%d/%Y, " + hour + ":%M PM PT")
                else:
                    loc_dt = loc_dt.strftime("%m/%d/%Y, %H:%M AM PT")
                if post.get("comment" + str(i), {}).get("adminName") != None:
                    bigString += '<tr><td class="comments"><b>' + post.get("comment" + str(i), {}).get("adminName") + ' (Staff)</b><br><i>' + loc_dt + '</i><br><br>' + post.get("comment" + str(i), {}).get("postContent") + '</td></tr>'
                else:
                    if post.get("comment" + str(i), {}).get("approved") == "true":
                        if post.get("comment" + str(i), {}).get("anonymous") == "true":
                            bigString += '<tr><td class="comments"><b> Anonymous Comment</b><br><i>' + loc_dt + '</i><br><br>' + post.get("comment" + str(i), {}).get("postContent") + '</td></tr>'
                        else:
                            bigString += '<tr><td class="comments"><b>' + post.get("comment" + str(i), {}).get("parentName") + '</b><br><i>' + loc_dt + '</i><br><br>' + post.get("comment" + str(i), {}).get("postContent") + '</td></tr>'
                counter += 1
            i += 1
    return render_template('comments.html', title = postTitle, name = parentName, information = info, time = loc_dt, content = postContent, ID = objectIDPost, comments = Markup(bigString))

@app.route('/viewSEU')
def viewSEU():
    objectIDPost = request.args['thread']
    connection_string = os.environ["MONGO_CONNECTION_STRING"]
    db_name = os.environ["MONGO_DBNAME"]
    client = pymongo.MongoClient(connection_string)
    db = client[db_name]
    collection = db['SEU']
    post = collection.find_one({'_id': ObjectId(objectIDPost)})
    postTitle = post.get('postTitle')
    postContent = post.get('postContent')
    utc_dt = datetime(int(post.get('dateTime').strftime("%Y")), int(post.get('dateTime').strftime("%m")), int(post.get('dateTime').strftime("%d")), int(post.get('dateTime').strftime("%H")), int(post.get('dateTime').strftime("%M")), 0, tzinfo=pytz.utc)
    loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
    if int(loc_dt.strftime("%H")) > 12:
        hour = str(int(loc_dt.strftime("%H")) - 12)
        loc_dt = loc_dt.strftime("%m/%d/%Y, " + hour + ":%M PM PT")
    else:
        loc_dt = loc_dt.strftime("%m/%d/%Y, %H:%M AM PT")
    if 'github_token' in session:
        parentName = post.get('parentName')
        studentNameGrade = post.get('studentNameGrade')
        parentEmail = post.get('parentEmail')
        if parentEmail == "":
            parentEmail = "Email not provided"
    else:
        if post.get('anonymous') == "false":
            parentName = post.get('parentName')
        else:
            parentName = "Anonymous Post"
        studentNameGrade = ""
        parentEmail = ""
    info = " / " + studentNameGrade + " / " + parentEmail
    bigString = ''
    keyList = list(post.keys())
    commentAmount = 0
    for item in keyList:
        if "comment" in item:
            commentAmount += 1
    bigString = ''
    counter = 0
    i = 0
    if 'github_token' in session: #if admin is logged in
        while counter < commentAmount:
            if("comment" + str(i) in post):
                utc_dt = datetime(int(post.get("comment" + str(i), {}).get("dateTime").strftime("%Y")), int(post.get("comment" + str(i), {}).get("dateTime").strftime("%m")), int(post.get("comment" + str(i), {}).get("dateTime").strftime("%d")), int(post.get("comment" + str(i), {}).get("dateTime").strftime("%H")), int(post.get("comment" + str(i), {}).get("dateTime").strftime("%M")), 0, tzinfo=pytz.utc)
                loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
                if int(loc_dt.strftime("%H")) > 12:
                    hour = str(int(loc_dt.strftime("%H")) - 12)
                    loc_dt = loc_dt.strftime("%m/%d/%Y, " + hour + ":%M PM PT")
                else:
                    loc_dt = loc_dt.strftime("%m/%d/%Y, %H:%M AM PT")
                if post.get("comment" + str(i), {}).get("adminName") != None: #checks if it is admin post
                    bigString += '<tr><td class="comments"><b>' + post.get("comment" + str(i), {}).get("adminName") + ' (Staff)</b><br><i>' + loc_dt + '</i><br><br>' + post.get("comment" + str(i), {}).get("postContent") + '</td></tr>'
                else:
                    bigString += '<tr><td class="comments"><b>' + post.get("comment" + str(i), {}).get("parentName") + '</b> / ' + post.get("comment" + str(i), {}).get("studentNameGrade") + '<br><i>' + loc_dt + '</i><br><br>' + post.get("comment" + str(i), {}).get("postContent") + '</td></tr>'
                counter += 1
            i += 1
    else:
        while counter < commentAmount:
            if("comment" + str(i) in post):
                utc_dt = datetime(int(post.get("comment" + str(i), {}).get("dateTime").strftime("%Y")), int(post.get("comment" + str(i), {}).get("dateTime").strftime("%m")), int(post.get("comment" + str(i), {}).get("dateTime").strftime("%d")), int(post.get("comment" + str(i), {}).get("dateTime").strftime("%H")), int(post.get("comment" + str(i), {}).get("dateTime").strftime("%M")), 0, tzinfo=pytz.utc)
                loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
                if int(loc_dt.strftime("%H")) > 12:
                    hour = str(int(loc_dt.strftime("%H")) - 12)
                    loc_dt = loc_dt.strftime("%m/%d/%Y, " + hour + ":%M PM PT")
                else:
                    loc_dt = loc_dt.strftime("%m/%d/%Y, %H:%M AM PT")
                if post.get("comment" + str(i), {}).get("adminName") != None:
                    bigString += '<tr><td class="comments"><b>' + post.get("comment" + str(i), {}).get("adminName") + ' (Staff)</b><br><i>' + loc_dt + '</i><br><br>' + post.get("comment" + str(i), {}).get("postContent") + '</td></tr>'
                else:
                    if post.get("comment" + str(i), {}).get("approved") == "true":
                        if post.get("comment" + str(i), {}).get("anonymous") == "true":
                            bigString += '<tr><td class="comments"><b> Anonymous Comment</b><br><i>' + loc_dt + '</i><br><br>' + post.get("comment" + str(i), {}).get("postContent") + '</td></tr>'
                        else:
                            bigString += '<tr><td class="comments"><b>' + post.get("comment" + str(i), {}).get("parentName") + '</b><br><i>' + loc_dt + '</i><br><br>' + post.get("comment" + str(i), {}).get("postContent") + '</td></tr>'
                counter += 1
            i += 1
    return render_template('comments.html', title = postTitle, name = parentName, information = info, time = loc_dt, content = postContent, ID = objectIDPost, comments = Markup(bigString))

@app.route('/viewELLA')
def viewELLA():
    objectIDPost = request.args['thread']
    connection_string = os.environ["MONGO_CONNECTION_STRING"]
    db_name = os.environ["MONGO_DBNAME"]
    client = pymongo.MongoClient(connection_string)
    db = client[db_name]
    collection = db['ELLA']
    post = collection.find_one({'_id': ObjectId(objectIDPost)})
    postTitle = post.get('postTitle')
    postContent = post.get('postContent')
    utc_dt = datetime(int(post.get('dateTime').strftime("%Y")), int(post.get('dateTime').strftime("%m")), int(post.get('dateTime').strftime("%d")), int(post.get('dateTime').strftime("%H")), int(post.get('dateTime').strftime("%M")), 0, tzinfo=pytz.utc)
    loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
    if int(loc_dt.strftime("%H")) > 12:
        hour = str(int(loc_dt.strftime("%H")) - 12)
        loc_dt = loc_dt.strftime("%m/%d/%Y, " + hour + ":%M PM PT")
    else:
        loc_dt = loc_dt.strftime("%m/%d/%Y, %H:%M AM PT")
    displayName = post.get('adminName')
    bigString = ''
    keyList = list(post.keys())
    commentAmount = 0
    for item in keyList:
        if "comment" in item:
            commentAmount += 1
    bigString = ''
    keyList = list(post.keys())
    commentAmount = 0
    for item in keyList:
        if "comment" in item:
            commentAmount += 1
    bigString = ''
    counter = 0
    i = 0
    if 'github_token' in session: #if admin is logged in
        while counter < commentAmount:
            if("comment" + str(i) in post):
                utc_dt = datetime(int(post.get("comment" + str(i), {}).get("dateTime").strftime("%Y")), int(post.get("comment" + str(i), {}).get("dateTime").strftime("%m")), int(post.get("comment" + str(i), {}).get("dateTime").strftime("%d")), int(post.get("comment" + str(i), {}).get("dateTime").strftime("%H")), int(post.get("comment" + str(i), {}).get("dateTime").strftime("%M")), 0, tzinfo=pytz.utc)
                loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
                if int(loc_dt.strftime("%H")) > 12:
                    hour = str(int(loc_dt.strftime("%H")) - 12)
                    loc_dt = loc_dt.strftime("%m/%d/%Y, " + hour + ":%M PM PT")
                else:
                    loc_dt = loc_dt.strftime("%m/%d/%Y, %H:%M AM PT")
                if post.get("comment" + str(i), {}).get("adminName") != None: #checks if it is admin post
                    bigString += '<tr><td class="comments"><b>' + post.get("comment" + str(i), {}).get("adminName") + ' (Staff)</b><br><i>' + loc_dt + '</i><br><br>' + post.get("comment" + str(i), {}).get("postContent") + '</td></tr>'
                else:
                    bigString += '<tr><td class="comments"><b>' + post.get("comment" + str(i), {}).get("parentName") + '</b> / ' + post.get("comment" + str(i), {}).get("studentNameGrade") + '<br><i>' + loc_dt + '</i><br><br>' + post.get("comment" + str(i), {}).get("postContent") + '</td></tr>'
                counter += 1
            i += 1
    else:
        while counter < commentAmount:
            if("comment" + str(i) in post):
                utc_dt = datetime(int(post.get("comment" + str(i), {}).get("dateTime").strftime("%Y")), int(post.get("comment" + str(i), {}).get("dateTime").strftime("%m")), int(post.get("comment" + str(i), {}).get("dateTime").strftime("%d")), int(post.get("comment" + str(i), {}).get("dateTime").strftime("%H")), int(post.get("comment" + str(i), {}).get("dateTime").strftime("%M")), 0, tzinfo=pytz.utc)
                loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
                if int(loc_dt.strftime("%H")) > 12:
                    hour = str(int(loc_dt.strftime("%H")) - 12)
                    loc_dt = loc_dt.strftime("%m/%d/%Y, " + hour + ":%M PM PT")
                else:
                    loc_dt = loc_dt.strftime("%m/%d/%Y, %H:%M AM PT")
                if post.get("comment" + str(i), {}).get("adminName") != None:
                    bigString += '<tr><td class="comments"><b>' + post.get("comment" + str(i), {}).get("adminName") + ' (Staff)</b><br><i>' + loc_dt + '</i><br><br>' + post.get("comment" + str(i), {}).get("postContent") + '</td></tr>'
                else:
                    if post.get("comment" + str(i), {}).get("approved") == "true":
                        if post.get("comment" + str(i), {}).get("anonymous") == "true":
                            bigString += '<tr><td class="comments"><b> Anonymous Comment</b><br><i>' + loc_dt + '</i><br><br>' + post.get("comment" + str(i), {}).get("postContent") + '</td></tr>'
                        else:
                            bigString += '<tr><td class="comments"><b>' + post.get("comment" + str(i), {}).get("parentName") + '</b><br><i>' + loc_dt + '</i><br><br>' + post.get("comment" + str(i), {}).get("postContent") + '</td></tr>'
                counter += 1
            i += 1
    return render_template('comments.html', title = postTitle, name = parentName, information = info, time = loc_dt, content = postContent, ID = objectIDPost, comments = Markup(bigString))

@app.route('/viewELLU')
def viewELLU():
    objectIDPost = request.args['thread']
    connection_string = os.environ["MONGO_CONNECTION_STRING"]
    db_name = os.environ["MONGO_DBNAME"]
    client = pymongo.MongoClient(connection_string)
    db = client[db_name]
    collection = db['ELLU']
    post = collection.find_one({'_id': ObjectId(objectIDPost)})
    postTitle = post.get('postTitle')
    postContent = post.get('postContent')
    utc_dt = datetime(int(post.get('dateTime').strftime("%Y")), int(post.get('dateTime').strftime("%m")), int(post.get('dateTime').strftime("%d")), int(post.get('dateTime').strftime("%H")), int(post.get('dateTime').strftime("%M")), 0, tzinfo=pytz.utc)
    loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
    if int(loc_dt.strftime("%H")) > 12:
        hour = str(int(loc_dt.strftime("%H")) - 12)
        loc_dt = loc_dt.strftime("%m/%d/%Y, " + hour + ":%M PM PT")
    else:
        loc_dt = loc_dt.strftime("%m/%d/%Y, %H:%M AM PT")
    if 'github_token' in session:
        parentName = post.get('parentName')
        studentNameGrade = post.get('studentNameGrade')
        parentEmail = post.get('parentEmail')
        if parentEmail == "":
            parentEmail = "Email not provided"
    else:
        if post.get('anonymous') == "false":
            parentName = post.get('parentName')
        else:
            parentName = "Anonymous Post"
        studentNameGrade = ""
        parentEmail = ""
    info = " / " + studentNameGrade + " / " + parentEmail
    bigString = ''
    keyList = list(post.keys())
    commentAmount = 0
    for item in keyList:
        if "comment" in item:
            commentAmount += 1
    bigString = ''
    counter = 0
    i = 0
    if 'github_token' in session: #if admin is logged in
        while counter < commentAmount:
            if("comment" + str(i) in post):
                utc_dt = datetime(int(post.get("comment" + str(i), {}).get("dateTime").strftime("%Y")), int(post.get("comment" + str(i), {}).get("dateTime").strftime("%m")), int(post.get("comment" + str(i), {}).get("dateTime").strftime("%d")), int(post.get("comment" + str(i), {}).get("dateTime").strftime("%H")), int(post.get("comment" + str(i), {}).get("dateTime").strftime("%M")), 0, tzinfo=pytz.utc)
                loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
                if int(loc_dt.strftime("%H")) > 12:
                    hour = str(int(loc_dt.strftime("%H")) - 12)
                    loc_dt = loc_dt.strftime("%m/%d/%Y, " + hour + ":%M PM PT")
                else:
                    loc_dt = loc_dt.strftime("%m/%d/%Y, %H:%M AM PT")
                if post.get("comment" + str(i), {}).get("adminName") != None: #checks if it is admin post
                    bigString += '<tr><td class="comments"><b>' + post.get("comment" + str(i), {}).get("adminName") + ' (Staff)</b><br><i>' + loc_dt + '</i><br><br>' + post.get("comment" + str(i), {}).get("postContent") + '</td></tr>'
                else:
                    bigString += '<tr><td class="comments"><b>' + post.get("comment" + str(i), {}).get("parentName") + '</b> / ' + post.get("comment" + str(i), {}).get("studentNameGrade") + '<br><i>' + loc_dt + '</i><br><br>' + post.get("comment" + str(i), {}).get("postContent") + '</td></tr>'
                counter += 1
            i += 1
    else:
        while counter < commentAmount:
            if("comment" + str(i) in post):
                utc_dt = datetime(int(post.get("comment" + str(i), {}).get("dateTime").strftime("%Y")), int(post.get("comment" + str(i), {}).get("dateTime").strftime("%m")), int(post.get("comment" + str(i), {}).get("dateTime").strftime("%d")), int(post.get("comment" + str(i), {}).get("dateTime").strftime("%H")), int(post.get("comment" + str(i), {}).get("dateTime").strftime("%M")), 0, tzinfo=pytz.utc)
                loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
                if int(loc_dt.strftime("%H")) > 12:
                    hour = str(int(loc_dt.strftime("%H")) - 12)
                    loc_dt = loc_dt.strftime("%m/%d/%Y, " + hour + ":%M PM PT")
                else:
                    loc_dt = loc_dt.strftime("%m/%d/%Y, %H:%M AM PT")
                if post.get("comment" + str(i), {}).get("adminName") != None:
                    bigString += '<tr><td class="comments"><b>' + post.get("comment" + str(i), {}).get("adminName") + ' (Staff)</b><br><i>' + loc_dt + '</i><br><br>' + post.get("comment" + str(i), {}).get("postContent") + '</td></tr>'
                else:
                    if post.get("comment" + str(i), {}).get("approved") == "true":
                        if post.get("comment" + str(i), {}).get("anonymous") == "true":
                            bigString += '<tr><td class="comments"><b> Anonymous Comment</b><br><i>' + loc_dt + '</i><br><br>' + post.get("comment" + str(i), {}).get("postContent") + '</td></tr>'
                        else:
                            bigString += '<tr><td class="comments"><b>' + post.get("comment" + str(i), {}).get("parentName") + '</b><br><i>' + loc_dt + '</i><br><br>' + post.get("comment" + str(i), {}).get("postContent") + '</td></tr>'
                counter += 1
            i += 1
    return render_template('comments.html', title = postTitle, name = parentName, information = info, time = loc_dt, content = postContent, ID = objectIDPost, comments = Markup(bigString))

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

#make sure the jinja variables use Markup 
@github.tokengetter
def get_github_oauth_token():
    return session['github_token']

if __name__ == '__main__':
    app.run()
