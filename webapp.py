from flask import Flask, redirect, Markup, url_for, session, request, jsonify
from flask_oauthlib.client import OAuth
from flask import render_template
from bson.objectid import ObjectId
from mongosanitizer.sanitizer import sanitize #documentation says used to sanitize user input quieries, but no quieries here are performed with user input.

import pprint
import os
import sys
import pymongo
from datetime import datetime, timedelta
from pytz import timezone
import pytz
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

app.secret_key = os.environ['SECRET_KEY'] #used to sign session cookies
oauth = OAuth(app)
oauth.init_app(app) #initialize the app to be able to make requests for user information

connection_string = os.environ['MONGO_CONNECTION_STRING']
db_name = os.environ['MONGO_DBNAME']
client = pymongo.MongoClient(connection_string)
db = client[db_name]

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
    return {'logged_in':('github_token' in session)}

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
            collection = db['ADMIN'] #database storing admin information
            adminDocuments = collection.find({}) #find all documents in admin database
            adminList = [] 
            for admin in adminDocuments: #for all admin documents
                adminList.append(admin.get('username')) #put name of admin into list
            if session['user_data']['login'] in adminList: #if the admin name list has name of user trying to log in
                message='You were successfully logged in as ' + session['user_data']['login'] + '. Don\'t forget to log out before exiting this website.' 
            else:
                session.clear()
                message='Please sign in with a valid admin account. You attempted to log in as ' + session['user_data']['login'] + '. This is not an admin account. To log in as an admin you may need to log out of Github before attempting to log in again.'
        except Exception as inst:
            session.clear()
            print(inst)
            message='Unable to login, please try again.'
    session['username'] = 'admin'
    return render_template('login.html', message = message)

def send_email(receiver_email, title, name, link, logged, comment):
    collection = db['EMAIL'] #database contains a single document storing the email and password of the email bot
    try:
        information = collection.find_one({'_id': ObjectId('60b2d66ba55f630f74e0a554')}) #gets the document storing the email and password of the bot
        smtp_server = 'smtp.gmail.com'
        sender_email = information.get('sender_email') #gets bot email
        password = information.get('password') #gets bot password
        message = MIMEMultipart('alternative')
        message['Subject'] = 'SBHS Parent Board Notification' #subject of automatic email
        message['From'] = sender_email #email of bot
        message['To'] = receiver_email #sends to this email
        text = """\
        """ #basic text
        html = """\
        """ #text version with html
        if logged == False: #email to user when an admin comments on their post
            text = """\
            Hello name,
            Your post title has recieved a response from a staff member.
            <link>
            
            Hola name,
            Tu publicación title ha recibido una respuesta de un miembro del personal.
            <link>"""
            html = """\
            <html>
                <body>
                    <p><b>Hi, """ + name + """.</b><br>
                    Your post <a href='""" + link + """'>""" + title + """</a> has recieved a response from a staff member.<br>
                    --------------------------------------------------------------------------------------------------------<br>
                    <b>Hola, """ + name + """.</b><br>
                    Tu publicación <a href='""" + link + """'>""" + title + """</a> ha recibido una respuesta de un miembro del personal.<br>
                    --------------------------------------------------------------------------------------------------------<br>
                    <small>*Please do not response to this email / Por favor, no responda a este correo electrónico.</small>
                    </p>
                </body>
            </html>
            """
        elif comment == False: #email to admin when a user posts
            text = """\
            Hello.
            A user has posted on the parent board forum.
            <link>
            
            Hola.
            Un usuario ha publicado en el foro del tablero principal.
            <link>"""
            html = """\
            <html>
                <body>
                    <p><b>Hi.</b><br>
                    """ + name + """ has posted <a href='""" + link + """'>""" + title + """</a> on the parent board forum<br>
                    --------------------------------------------------------------------------------------------------------<br>
                    <b>Hola.</b><br>
                    """ + name + """ ha publicado <a href='""" + link + """'>""" + title + """</a> en el foro del tablero principal.<br>
                    --------------------------------------------------------------------------------------------------------<br>
                    <small>*Please do not response to this email / Por favor, no responda a este correo electrónico.</small>
                    </p>
                </body>
            </html>
            """
        else: #email to admin when a user comments
            text = """\
            Hello.
            A user has commented on the parent board forum.
            <link>
            
            Hola.
            Un usuario ha comentado en el foro del tablero principal.
            <link>"""
            html = """\
            <html>
                <body>
                    <p><b>Hi.</b><br>
                    """ + name + """ has commented on <a href='""" + link + """'>""" + title + """</a> on the parent board forum<br>
                    --------------------------------------------------------------------------------------------------------<br>
                    <b>Hola.</b><br>
                    """ + name + """ ha comentado en <a href='""" + link + """'>""" + title + """</a> en el foro del tablero principal.<br>
                    --------------------------------------------------------------------------------------------------------<br>
                    <small>*Please do not response to this email / Por favor, no responda a este correo electrónico.</small>
                    </p>
                </body>
            </html>
            """
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')
        message.attach(part1)
        message.attach(part2)
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, password) #logs into the bot email
            server.sendmail(sender_email, receiver_email, message.as_string()) #sends email
    except:
        return
    return

@app.route('/addAdmin', methods=['GET', 'POST']) #adds admin
def add_admin():
    if request.method == 'POST':
        collection = db['ADMIN']
        collection.insert_one({'username': request.form['username'], 'opt': False, 'optComment': False})
    return render_admin_log()
        
@app.route('/removeAdmin', methods=['GET', 'POST']) #removes admin
def remove_admin():
    if request.method == 'POST':
        collection = db['ADMIN']
        collection.delete_one({'_id': ObjectId(request.form['delete'])}) 
    return render_admin_log()
        
@app.route('/optOut', methods=['GET', 'POST']) #admin opts out of getting emails from user posts
def opt_out():
    if request.method == 'POST':
        collection = db['ADMIN']
        collection.find_one_and_update({'_id': ObjectId(request.form['optOut'])},
                                       {'$set': {'opt': False}})
    return render_admin_log()

@app.route('/optIn', methods=['GET', 'POST']) #admin opts in of getting emails from user posts
def opt_in():
    if request.method == 'POST':
        collection = db['ADMIN']
        collection.find_one_and_update({'_id': ObjectId(request.form['optIn'])},
                                       {'$set': {'opt': True}})
    return render_admin_log()

@app.route('/optInComment', methods=['GET', 'POST']) #admin opts in of getting emails from user comments
def opt_in_comment():
    if request.method == 'POST':
        collection = db['ADMIN']
        collection.find_one_and_update({'_id': ObjectId(request.form['optInComment'])},
                                       {'$set': {'optComment': True}})
    return render_admin_log()

@app.route('/optOutComment', methods=['GET', 'POST']) #admin opts out of getting emails from user comments
def opt_out_comment():
    if request.method == 'POST':
        collection = db['ADMIN']
        collection.find_one_and_update({'_id': ObjectId(request.form['optOutComment'])},
                                       {'$set': {'optComment': False}})
    return render_admin_log()

@app.route('/addEmail', methods=['GET', 'POST']) #attaches or changes an email for an admin
def add_email():
    if request.method == 'POST':
        collection = db['ADMIN']
        collection.find_one_and_update({'_id': ObjectId(request.form['id'])},
                                       {'$set': {'email': request.form['email']}}) 
    return render_admin_log()
        
@app.route('/englishlearnerforum')
def render_english_learner_forum():
    collection = db['ELLU'] #first generate posts code for the english language learner user forum
    cursor = collection.find({}).sort('_id', -1).limit(500) #get the newest 500 posts from the user forum
    bigString1 = '' #generated html containing all posts in english language learner user forum
    bigString2 = '' #generated html containing all posts in english language learner admin forum
    if 'github_token' in session: #if the viewer is an admin
        for post in cursor: #for every post, generate html.
            bigString1 += ('<tr><td class="col1"><form action="/viewELLU" class="inLine"><select class="selection" name="thread"><option value="' + str(post.get('_id')) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form><br><i>' + post.get('parentName') + ' / ' + post.get('studentNameGrade') + ' / ' + post.get('parentEmail') + '</i></td>' +
                           '<td class="col2"><span class="glyphicon glyphicon-comment"></span> ' + str(post.get('amount')) + '</td>')
            if(post.get('approved') == 'false'): #if the post is not approved, add a vet button. Else, add an unvet button
                bigString1 += '<td class="col3"><form action="/vetELL" method="post" class="inLine"><button type="submit" class="btn btn-warning btn-sm" name="vet" value="' + str(post.get('_id'))+ '">' + '<span class="glyphicon glyphicon-plus"></span> Vet</button></form> '
            else:
                bigString1 += '<td class="col3"><form action="/unvetELL" method="post" class="inLine"><button type="submit" class="btn btn-warning btn-sm" name="vet" value="' + str(post.get('_id'))+ '">' + '<span class="glyphicon glyphicon-minus"></span> Unvet</button></form> '
            bigString1 += '<form action="/bumpPost" method="post" class="inLine"><button type="submit" class="btn btn-info btn-sm" name="bump" value="' + str(post.get('_id'))+ '">' + '<span class="glyphicon glyphicon-arrow-up"></span> Bump</button></form> <button type="button" class="btn btn-danger btn-sm delete"><span class="glyphicon glyphicon-trash"></span> Delete</button><button type="button" class="btn btn-danger btn-sm cancel inLine">Cancel</button> <form action="/deleteELL" method="post" class="inLine confirm"><button type="submit" class="btn btn-danger btn-sm" name="delete" value="' + str(post.get('_id')) + '"><span class="glyphicon glyphicon-trash"></span> Confirm Delete</button></form>'
            utc_dt = datetime(int(post.get('dateTime').strftime('%Y')), int(post.get('dateTime').strftime('%m')), int(post.get('dateTime').strftime('%d')), int(post.get('dateTime').strftime('%H')), int(post.get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
            loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
            if int(loc_dt.strftime('%H')) > 12:
                hour = str(int(loc_dt.strftime('%H')) - 12)
                loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT') # this chunk of code converts the stored time into neat pacific time. This is repeated for any time a time is displayed on page on comments, posts, admin log, etc.
            else:
                hour = str(int(loc_dt.strftime('%H')))
                if hour == '0':
                    hour = '12'
                loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
            bigString1 += '<br><i>' + loc_dt + '</i></td></tr>'
    else: #if the viewer of the page is an user (not logged in)
        for post in cursor: #for every post, generate html
            if(post.get('approved') == 'true'): #don't show the post if it is not vetted
                bigString1 += '<tr><td class="col1"><form action="/viewELLU" class="inLine"><select class="selection" name="thread"><option value="' + str(post.get('_id')) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form><br>'
                if(post.get('anonymous') == 'true'): #don't show the poster's name if they want to be anonymous
                    bigString1 += '<i>Anonymous Post</i></td>'
                else:
                    bigString1 += '<i>' + post.get('parentName') + '</i></td>'
                bigString1 += '<td class="col2"><span class="glyphicon glyphicon-comment"></span> ' + str(post.get('amount')) + '</td>'
                utc_dt = datetime(int(post.get('dateTime').strftime('%Y')), int(post.get('dateTime').strftime('%m')), int(post.get('dateTime').strftime('%d')), int(post.get('dateTime').strftime('%H')), int(post.get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
                loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
                if int(loc_dt.strftime('%H')) > 12:
                    hour = str(int(loc_dt.strftime('%H')) - 12)
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
                else:
                    hour = str(int(loc_dt.strftime('%H')))
                    if hour == '0':
                        hour = '12'
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
                bigString1 += '<td class="col3"><i>' + loc_dt + '</i></td></tr>'
    collection = db['ELLA'] #now generate all posts code for the english language learners admin forum
    cursor = collection.find({}).sort('_id', -1).limit(500) #get newest 500 posts
    if 'github_token' in session: #if the viewer is logged in
        for post in cursor: #for every post, generate html
            utc_dt = datetime(int(post.get('dateTime').strftime('%Y')), int(post.get('dateTime').strftime('%m')), int(post.get('dateTime').strftime('%d')), int(post.get('dateTime').strftime('%H')), int(post.get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
            loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
            if int(loc_dt.strftime('%H')) > 12:
                hour = str(int(loc_dt.strftime('%H')) - 12)
                loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
            else:
                hour = str(int(loc_dt.strftime('%H')))
                if hour == '0':
                    hour = '12'
                loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
            bigString2 += ('<tr><td class="col1">  <form action="/viewELLA" class="inLine"><select class="selection" name="thread"><option value="' + str(post.get('_id')) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form><br><i>' + post.get('adminName') + '</i></td>' +
                           '<td class="col2"><span class="glyphicon glyphicon-comment"></span> ' + str(post.get('amount')) + '</td>' +
                           '<td class="col3"><form action="/bumpPost" method="post" class="inLine"><button type="submit" class="btn btn-info btn-sm" name="bump" value="' + str(post.get('_id'))+ '">' + '<span class="glyphicon glyphicon-arrow-up"></span> Bump</button></form> <button type="button" class="btn btn-danger btn-sm delete"><span class="glyphicon glyphicon-trash"></span> Delete</button><button type="button" class="btn btn-danger btn-sm cancel inLine">Cancel</button> <form action="/deleteELL" method="post" class="inLine confirm"><button type="submit" class="btn btn-danger btn-sm" name="delete" value="' + str(post.get('_id')) + '"><span class="glyphicon glyphicon-trash"></span>Confirm Delete</button></form><br><i>' + loc_dt + '</i></td></tr>')
    else: #if the viewer of the page is not an admin
        for post in cursor: #for every post, generate html
            utc_dt = datetime(int(post.get('dateTime').strftime('%Y')), int(post.get('dateTime').strftime('%m')), int(post.get('dateTime').strftime('%d')), int(post.get('dateTime').strftime('%H')), int(post.get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
            loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
            if int(loc_dt.strftime('%H')) > 12:
                hour = str(int(loc_dt.strftime('%H')) - 12)
                loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
            else:
                hour = str(int(loc_dt.strftime('%H')))
                if hour == '0':
                    hour = '12'
                loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
            bigString2 += ('<tr><td class="col1">  <form action="/viewELLA" class="inLine"><select class="selection" name="thread"><option value="' + str(post.get('_id')) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form><br><i>' + post.get('adminName') + '</i></td>' +
                           '<td class="col2"><span class="glyphicon glyphicon-comment"></span> ' + str(post.get('amount')) + '</td>' +
                           '<td class="col3"><i>' + loc_dt + '</i></td></tr>')
    return render_template('englishlearnerforum.html', ELLUPosts = Markup(bigString1), ELLAPosts = Markup(bigString2))

@app.route('/specialeducationforum')
def render_special_education_forum():
    collection = db['SEU'] #first generate posts code for the special education user forum
    cursor = collection.find({}).sort('_id', -1).limit(500) #get newest 500 posts
    bigString1 = '' #generated html code for all posts in the special education user forum
    bigString2 = '' #generated html code for all posts in the special educatio admin forum
    if 'github_token' in session: #if the viewer is an admin
        for post in cursor: #generate html for each post
            bigString1 += ('<tr><td class="col1"><form action="/viewSEU" class="inLine"><select class="selection" name="thread"><option value="' + str(post.get('_id')) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form><br><i>' + post.get('parentName') + ' / ' + post.get('studentNameGrade') + ' / ' + post.get('parentEmail') + '</i></td>' +
                           '<td class="col2"><span class="glyphicon glyphicon-comment"></span> ' + str(post.get('amount')) + '</td>')
            if(post.get('approved') == 'false'):
                bigString1 += '<td class="col3"><form action="/vetSE" method="post" class="inLine"><button type="submit" class="btn btn-warning btn-sm" name="vet" value="' + str(post.get('_id'))+ '">' + '<span class="glyphicon glyphicon-plus"></span> Vet</button></form> '
            else:
                bigString1 += '<td class="col3"><form action="/unvetSE" method="post" class="inLine"><button type="submit" class="btn btn-warning btn-sm" name="vet" value="' + str(post.get('_id'))+ '">' + '<span class="glyphicon glyphicon-minus"></span> Unvet</button></form> '
            bigString1 += '<form action="/bumpPost" method="post" class="inLine"><button type="submit" class="btn btn-info btn-sm" name="bump" value="' + str(post.get('_id'))+ '">' + '<span class="glyphicon glyphicon-arrow-up"></span> Bump</button></form> <button type="button" class="btn btn-danger btn-sm delete"><span class="glyphicon glyphicon-trash"></span> Delete</button><button type="button" class="btn btn-danger btn-sm cancel inLine">Cancel</button> <form action="/deleteSE" method="post" class="inLine confirm"><button type="submit" class="btn btn-danger btn-sm" name="delete" value="' + str(post.get('_id')) + '"><span class="glyphicon glyphicon-trash"></span> Confirm Delete</button></form>'
            utc_dt = datetime(int(post.get('dateTime').strftime('%Y')), int(post.get('dateTime').strftime('%m')), int(post.get('dateTime').strftime('%d')), int(post.get('dateTime').strftime('%H')), int(post.get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
            loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
            if int(loc_dt.strftime('%H')) > 12:
                hour = str(int(loc_dt.strftime('%H')) - 12)
                loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
            else:
                hour = str(int(loc_dt.strftime('%H')))
                if hour == '0':
                    hour = '12'
                loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
            bigString1 += '</button></form><br><i>' + loc_dt + '</i></td></tr>'
    else: #if the viewer is not an admin
        for post in cursor: #generate html for each posts
            if(post.get('approved') == 'true'):
                bigString1 += '<tr><td class="col1"><form action="/viewSEU" class="inLine"><select class="selection" name="thread"><option value="' + str(post.get('_id')) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form><br>'
                if(post.get('anonymous') == 'true'):
                    bigString1 += '<i>Anonymous Post</i></td>'
                else:
                    bigString1 += '<i>' + post.get('parentName') + '</i></td>'
                bigString1 += '<td class="col2"><span class="glyphicon glyphicon-comment"></span> ' + str(post.get('amount')) + '</td>'
                utc_dt = datetime(int(post.get('dateTime').strftime('%Y')), int(post.get('dateTime').strftime('%m')), int(post.get('dateTime').strftime('%d')), int(post.get('dateTime').strftime('%H')), int(post.get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
                loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
                if int(loc_dt.strftime('%H')) > 12:
                    hour = str(int(loc_dt.strftime('%H')) - 12)
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
                else:
                    hour = str(int(loc_dt.strftime('%H')))
                    if hour == '0':
                        hour = '12'
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
                bigString1 += '<td class="col3"><i>' + loc_dt + '</i></td></tr>'
    collection = db['SEA'] #now generate posts code for the special education admin forum
    cursor = collection.find({}).sort('_id', -1).limit(500) #get latest 500 posts
    if 'github_token' in session: #if the viewer is an admin
        for post in cursor: #generate html for every post
            utc_dt = datetime(int(post.get('dateTime').strftime('%Y')), int(post.get('dateTime').strftime('%m')), int(post.get('dateTime').strftime('%d')), int(post.get('dateTime').strftime('%H')), int(post.get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
            loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
            if int(loc_dt.strftime('%H')) > 12:
                hour = str(int(loc_dt.strftime('%H')) - 12)
                loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
            else:
                hour = str(int(loc_dt.strftime('%H')))
                if hour == '0':
                    hour = '12'
                loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
            bigString2 += ('<tr><td class="col1">  <form action="/viewSEA" class="inLine"><select class="selection" name="thread"><option value="' + str(post.get('_id')) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form><br><i>' + post.get('adminName') + '</i></td>' +
                           '<td class="col2"><span class="glyphicon glyphicon-comment"></span> ' + str(post.get('amount')) + '</td>' +
                           '<td class="col3"><form action="/bumpPost" method="post" class="inLine"><button type="submit" class="btn btn-info btn-sm" name="bump" value="' + str(post.get('_id'))+ '">' + '<span class="glyphicon glyphicon-arrow-up"></span> Bump</button></form> <button type="button" class="btn btn-danger btn-sm delete"><span class="glyphicon glyphicon-trash"></span> Delete</button><button type="button" class="btn btn-danger btn-sm cancel inLine">Cancel</button> <form action="/deleteSE" method="post" class="inLine confirm"><button type="submit" class="btn btn-danger btn-sm" name="delete" value="' + str(post.get('_id')) + '"><span class="glyphicon glyphicon-trash"></span> Confirm Delete</button></form><br><i>' + loc_dt + '</i></td></tr>')
    else: #if the viewer is not an admin
        for post in cursor: #generate html for every post
            utc_dt = datetime(int(post.get('dateTime').strftime('%Y')), int(post.get('dateTime').strftime('%m')), int(post.get('dateTime').strftime('%d')), int(post.get('dateTime').strftime('%H')), int(post.get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
            loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
            if int(loc_dt.strftime('%H')) > 12:
                hour = str(int(loc_dt.strftime('%H')) - 12)
                loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
            else:
                hour = str(int(loc_dt.strftime('%H')))
                if hour == '0':
                    hour = '12'
                loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
            bigString2 += ('<tr><td class="col1">  <form action="/viewSEA" class="inLine"><select class="selection" name="thread"><option value="' + str(post.get('_id')) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form><br><i>' + post.get('adminName') + '</i></td>' +
                           '<td class="col2"><span class="glyphicon glyphicon-comment"></span> ' + str(post.get('amount')) + '</td>' +
                           '<td class="col3"><i>' + loc_dt + '</i></td></tr>')
    return render_template('specialeducationforum.html', SEUPosts = Markup(bigString1), SEAPosts = Markup(bigString2))

@app.route('/adminLog')
def render_admin_log():
    collection = db['LOG'] #log database contains strings that represent every action: posting, commenting, deleting, vetting, editing, and bumping.
    cursor = collection.find({}).sort('_id', -1).limit(1000) #get latest 1000 actions
    bigString = '' #contains html code for all actions
    counter = 0
    for item in cursor: #for all actions, generate html
        utc_dt = datetime(int(item.get('dateTime').strftime('%Y')), int(item.get('dateTime').strftime('%m')), int(item.get('dateTime').strftime('%d')), int(item.get('dateTime').strftime('%H')), int(item.get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
        loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
        if int(loc_dt.strftime('%H')) > 12:
            hour = str(int(loc_dt.strftime('%H')) - 12)
            loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
        else:
            hour = str(int(loc_dt.strftime("%H")))
            if hour == '0':
                hour = '12'
            loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
        bigString += '<tr><td class="logContent"><span class="timeColor">' + loc_dt + '</span>: ' + item.get('action')
        if item.get('content') != 'none': #if the action was deleting a comment or post, generate a collapsible allowing admins to view the content that was deleted.
            counter += 1
            bigString += ' <button class="btn btn-default btn-sm" type="button" data-toggle="collapse" data-target="#collapse' + str(counter) + '" aria-expanded="false" aria-controls="collapseExample">View <span class="glyphicon glyphicon-triangle-bottom"></span></button><div class="collapse" id="collapse' + str(counter) + '">' + item.get('content') + '</div>'
        bigString += '<br></td></tr>'
    collection = db['ADMIN'] #now, we generate code for admin information: view account, edit account, view other admins, and add/delete admins
    item = collection.find_one({'username': session['user_data']['login']}) #the viewer's information
    receive = ''
    change = '<form action="/addEmail" method="POST"><input type="email" class="form-control" name="email" maxlength="254"><button type="submit" class="btn btn-primary" name="id" value="' + str(item.get('_id')) + '">Submit</button></form>'
    username = item.get('username')
    email = 'Not provided'
    opt = 'No'
    optComment = 'No'
    if item.get('opt') == True: #if the admin has opted in to getting emails for user posts, opt out button. Else, opt in button.
        opt = 'Yes'
        receive = '<form action="/optOut" method="POST"><button type="submit" class="btn btn-warning btn-sm" name="optOut" value="' + str(item.get('_id'))+ '">Opt Out</button></form>'
    else:
        receive = '<form action="/optIn" method="POST"><button type="submit" class="btn btn-warning btn-sm" name="optIn" value="' + str(item.get('_id'))+ '">Opt In</button></form>'
    if item.get('optComment') == True: #if the admin has opted in to getting emails for user comments, opt out button. Else, opt in button.
        optComment = 'Yes'
        receiveComment = '<form action="/optOutComment" method="POST"><button type="submit" class="btn btn-warning btn-sm" name="optOutComment" value="' + str(item.get('_id'))+ '">Opt Out</button></form>'
    else:
        receiveComment = '<form action="/optInComment" method="POST"><button type="submit" class="btn btn-warning btn-sm" name="optInComment" value="' + str(item.get('_id'))+ '">Opt In</button></form>'
    if 'email' in item: #if the admin has an email
        email = item.get('email')
    add = '<form action="/addAdmin" method="POST"><input type="text" class="form-control" name="username"><button type="submit" class="btn btn-primary">Add</button></form>'
    admins = ''
    cursor = collection.find({})
    for admin in cursor: #generates a list of all admins as well as remove buttons attached to their id.
        admins += admin.get('username') + '<form action="/removeAdmin" method="POST"><button type="submit" class="btn btn-danger btn-sm" name="delete" value="' + str(admin.get('_id'))+ '">Remove</button></form><br>'
    return render_template('adminlog.html', log = Markup(bigString), email = email, opt = opt, username = username, change = Markup(change), receive = Markup(receive), admins = Markup(admins), add = Markup(add), optComment = optComment, receiveComment = Markup(receiveComment))

def add_admin_log(dateTime, action, content): #adds an action to the admin log database
    collection = db['LOG']
    collection.insert_one({'dateTime': dateTime, 'action': action, 'content': content})

@app.route('/userSubmitPostELL', methods=['GET','POST']) #post submitted in english language learners user forum
def user_submit_post_ELL():
    if request.method == 'POST':
        collection = db['ELLU']
        content = request.form['userMessage']
        content = content.replace('\\"', '')
        content = content.replace('\\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
        content = content.replace(' ', '&nbsp;')
        content = Markup(content[1:len(content)-1]) #these turn content from quill text into content that is readable and usable.
        if request.form['userEmail'] == '': #if the poster did not put down an email.
            email = 'Email not provided'
        else: #if the poster put down an email.
            email = request.form['userEmail']
        generate = ObjectId() #generate object id for the post
        post = {'_id': generate, 'postTitle': request.form['userTitle'], 'parentName': request.form['userName'], 'studentNameGrade': request.form['userStudent'], 'parentEmail': email, 'anonymous': request.form['anon'], 'dateTime': datetime.now(), 'postContent': content, 'approved': 'false', 'amount': 0}
        collection.insert_one(post) #inserts post into the collection
        action = request.form['userName'] + '<span class="createColor"> posted </span><form action="/viewELLU" class="inLine"><select class="selection" name="thread"><option value="' + str(generate) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + request.form['userTitle'] + '</b></button></form> in english language learner forum'
        add_admin_log(datetime.now(), action, 'none') #adds this posting action to the log.
        collection = db['ADMIN'] #any admin who opted into getting emails for posts will get an email
        adminDocuments = collection.find({})
        notificationList = []
        for admin in adminDocuments:
            if admin.get('email') != None and admin.get('opt') == True:
                notificationList.append(admin.get('email'))
        link = 'https://razzoforumproject.herokuapp.com/viewELLU?thread=' + str(generate) #generated link to the post. NOTE: will not work if the link changes so need to be updated
        for email in notificationList: #for every admin who has opted in to getting post email, send an email to them
            send_email(email, request.form['userTitle'], request.form['userName'], link, True, False)
    return render_english_learner_forum()

@app.route('/adminSubmitPostELL', methods=['GET', 'POST'])
def admin_submit_post_ELL():
    if request.method == 'POST':
        collection = db['ELLA'] 
        content = request.form['adminMessage']
        content = content.replace('\\"', '')
        content = content.replace('\\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
        content = content.replace(' ', '&nbsp;')
        content = Markup(content[1:len(content)-1]) #these turn content from quill text into content that is readable and usable.
        generate = ObjectId()
        post = {'_id': generate, 'postTitle': request.form['adminTitle'], 'adminName': request.form['adminName'], 'dateTime': datetime.now(), 'postContent': content, 'amount': 0}
        collection.insert_one(post) #insert admin post into the collection
        action = request.form['adminName'] + '<span class="createColor"> posted </span><form action="/viewELLA" class="inLine"><select class="selection" name="thread"><option value="' + str(generate) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + request.form['adminTitle'] + '</b></button></form> in english language learner forum'
        add_admin_log(datetime.now(), action, 'none') #adds this posting action to the log
    return render_english_learner_forum()
    
@app.route('/userSubmitPostSE', methods=['GET', 'POST']) #see user_submit_post_ell for commented code
def user_submit_post_SE():
    if request.method == 'POST':
        collection = db['SEU']
        content = request.form['userMessage']
        content = content.replace('\\"', '')
        content = content.replace('\\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
        content = content.replace(' ', '&nbsp;')
        content = Markup(content[1:len(content)-1])
        if request.form['userEmail'] == '':
            email = 'Email not provided'
        else:
            email = request.form['userEmail']
        generate = ObjectId()
        post = {'_id': generate, 'postTitle': request.form['userTitle'], 'parentName': request.form['userName'], 'studentNameGrade': request.form['userStudent'], 'parentEmail': email, 'anonymous': request.form['anon'], 'dateTime': datetime.now(), 'postContent': content, 'approved': 'false', 'amount': 0}
        post = collection.insert_one(post)
        action = request.form['userName'] + '<span class="createColor"> posted </span><form action="/viewSEU" class="inLine"><select class="selection" name="thread"><option value="' + str(generate) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + request.form['userTitle'] + '</b></button></form> in special education forum'
        add_admin_log(datetime.now(), action, 'none')
        collection = db['ADMIN']
        adminDocuments = collection.find({})
        notificationList = []
        for admin in adminDocuments:
            if admin.get('email') != None and admin.get('opt') == True:
                notificationList.append(admin.get('email'))
        link = 'https://razzoforumproject.herokuapp.com/viewSEU?thread=' + str(generate)
        for email in notificationList:
            send_email(email, request.form['userTitle'], request.form['userName'], link, True, False)
    return render_special_education_forum()

@app.route('/adminSubmitPostSE', methods=['GET', 'POST']) #see admin_submit_post_ell for commented code
def admin_submit_post_SE():
    if request.method == 'POST':
        collection = db['SEA']
        content = request.form['adminMessage']
        content = content.replace('\\"', '')
        content = content.replace('\\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
        content = content.replace(' ', '&nbsp;')
        content = Markup(content[1:len(content)-1])
        generate = ObjectId()
        post = {'_id': generate, 'postTitle': request.form['adminTitle'], 'adminName': request.form['adminName'], 'dateTime': datetime.now(), 'postContent': content, 'amount': 0}
        post = collection.insert_one(post)
        action = request.form['adminName'] + '<span class="createColor"> posted </span><form action="/viewSEA" class="inLine"><select class="selection" name="thread"><option value="' + str(generate) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + request.form['adminTitle'] + '</b></button></form> in special education forum'
        add_admin_log(datetime.now(), action, 'none')
    return render_special_education_forum()

@app.route('/submitComment', methods=['GET', 'POST']) 
def submit_comment():
    if request.method == 'POST':
        objectIDPost = request.form['ID']
        collection = db['SEA']
        post = collection.find_one({'_id': ObjectId(objectIDPost)})
        link = 'https://razzoforumproject.herokuapp.com/viewSEA?thread=' + objectIDPost
        if post == None:
            collection = db['SEU']
            post = collection.find_one({'_id': ObjectId(objectIDPost)})
            link = 'https://razzoforumproject.herokuapp.com/viewSEU?thread=' + objectIDPost
        if post == None:
            collection = db['ELLA']
            post = collection.find_one({'_id': ObjectId(objectIDPost)})
            link = 'https://razzoforumproject.herokuapp.com/viewELLA?thread=' + objectIDPost
        if post == None:
            collection = db['ELLU']
            post = collection.find_one({'_id': ObjectId(objectIDPost)}) #if statements find out what collection the commented post belongs to,
            link = 'https://razzoforumproject.herokuapp.com/viewELLU?thread=' + objectIDPost #as well as get the post itself
        keyList = list(post.keys())
        if 'comment' in keyList[-1]: #since all comments are stored as, for example, 'comment0', 'comment1', and 'comment4,' this code generates the number at the end of 'comment'
            lastNumber = keyList[-1]
            lastNumber = lastNumber.replace('comment', '')
            lastNumber = str(int(lastNumber) + 1)
        else:
            lastNumber = '0'
        if 'github_token' in session: #if the commenter is an admin
            content = request.form['adminMessage']
            content = content.replace('\\"', '')
            content = content.replace('\\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
            content = content.replace(' ', '&nbsp;')
            content = Markup(content[1:len(content)-1]) #quill text changed to readable and usable content
            post['comment' + lastNumber] = {'adminName': request.form['adminName'], 'dateTime': datetime.now(), 'postContent': content}
            post['amount'] = post.get('amount') + 1
            collection.replace_one({'_id': ObjectId(objectIDPost)}, post) #replaces the post with the same post but with the comment added.
        else: #if the commenter is not an admin
            content = request.form['userMessage']
            content = content.replace('\\"', '')
            content = content.replace('\\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
            content = content.replace(' ', '&nbsp;')
            content = Markup(content[1:len(content)-1]) #quill text changed to readable and usable content
            post['comment' + lastNumber] = {'parentName': request.form['userName'], 'studentNameGrade': request.form['userStudent'], 'anonymous': request.form['anon'], 'dateTime': datetime.now(), 'postContent': content, 'approved': 'false'}
            collection.replace_one({'_id': ObjectId(objectIDPost)}, post) #replaces the post with the same post but with the comment added.
            name = post.get('parentName') #chunk of code below sends emails to any admin who has opted into getting emails for user comments
            if name == None:
                name = post.get('adminName')
            collectionTwo = db['ADMIN']
            adminDocuments = collectionTwo.find({}) 
            notificationList = []
            for admin in adminDocuments:
                if admin.get('email') != None and admin.get('optComment') == True:
                    notificationList.append(admin.get('email'))
            for email in notificationList:
                send_email(email, post.get('postTitle'), name, link, True, True)
    if collection == db['SEA']: #the rest of the code below adds the correct text to the admin logs and returns the post that the commenter was on
        if 'github_token' in session:
            action = request.form['adminName'] + '<span class="createColor"> commented </span>on <form action="/viewSEA" class="inLine"><select class="selection" name="thread"><option value="' + objectIDPost + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form> in special education forum'
            add_admin_log(datetime.now(), action, 'none')
        else:
            action = request.form['userName'] + '<span class="createColor"> commented </span>on <form action="/viewSEA" class="inLine"><select class="selection" name="thread"><option value="' + objectIDPost + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form> in special education forum'
            add_admin_log(datetime.now(), action, 'none')
        return view_SEA(objectIDPost)
    elif collection == db['SEU']:
        if 'github_token' in session:
            action = request.form['adminName'] + '<span class="createColor"> commented </span>on <form action="/viewSEU" class="inLine"><select class="selection" name="thread"><option value="' + objectIDPost + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form> in special education forum'
            add_admin_log(datetime.now(), action, 'none')
            if post.get('parentEmail') != 'Email not provided' and post.get('approved') == 'true':
                link = 'https://razzoforumproject.herokuapp.com/viewSEU?thread=' + objectIDPost 
                send_email(post.get('parentEmail'), post.get('postTitle'), post.get('parentName'), link, False, False)
        else:
            action = request.form['userName'] + '<span class="createColor"> commented </span>on <form action="/viewSEU" class="inLine"><select class="selection" name="thread"><option value="' + objectIDPost + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form> in special education forum'
            add_admin_log(datetime.now(), action, 'none')
        return view_SEU(objectIDPost)
    elif collection == db['ELLA']:
        if 'github_token' in session:
            action = request.form['adminName'] + '<span class="createColor"> commented </span>on <form action="/viewELLA" class="inLine"><select class="selection" name="thread"><option value="' + objectIDPost + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form> in english language learner forum'
            add_admin_log(datetime.now(), action, 'none')
        else:
            action = request.form['userName'] + '<span class="createColor"> commented </span>on <form action="/viewELLA" class="inLine"><select class="selection" name="thread"><option value="' + objectIDPost + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form> in english language learner forum'
            add_admin_log(datetime.now(), action, 'none')
        return view_ELLA(objectIDPost)
    elif collection == db['ELLU']:
        if 'github_token' in session:
            action = request.form['adminName'] + '<span class="createColor"> commented </span>on <form action="/viewELLU" class="inLine"><select class="selection" name="thread"><option value="' + objectIDPost + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form> in english language learner forum'
            add_admin_log(datetime.now(), action, 'none')
            if post.get('parentEmail') != 'Email not provided' and post.get('approved') == 'true':
                link = 'https://razzoforumproject.herokuapp.com/viewSEU?thread=' + objectIDPost 
                send_email(post.get('parentEmail'), post.get('postTitle'), post.get('parentName'), link, False, False)
        else:
            action = request.form['userName'] + '<span class="createColor"> commented </span>on <form action="/viewELLU" class="inLine"><select class="selection" name="thread"><option value="' + objectIDPost + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form> in english language learner forum'
            add_admin_log(datetime.now(), action, 'none')
        return view_ELLU(objectIDPost)
    return render_template('information.html')

@app.route('/deleteComment', methods=['GET', 'POST'])
def delete_comment():
    if request.method == 'POST':
        objectIDPost = request.form['delete']
        comment = request.form['comment']    
        collection = db['SEU']
        post = collection.find_one({'_id': ObjectId(objectIDPost)})
        if post == None:
            collection = db['SEA']
            post = collection.find_one({'_id': ObjectId(objectIDPost)})
        if post == None:
            collection = db['ELLA']
            post = collection.find_one({'_id': ObjectId(objectIDPost)}) #if statements find out what collection the commented post belongs to, as well as the post itself
        if post == None:
            collection = db['ELLU'] 
            post = collection.find_one({'_id': ObjectId(objectIDPost)})  
        if collection == db['SEA']:
            if post.get(comment, {}).get('adminName') != None:
                action = session['user_data']['login'] + '<span class="deleteColor"> deleted </span>a comment by ' + post.get(comment, {}).get('adminName') + ' in the post <form action="/viewSEA" class="inLine"><select class="selection" name="thread"><option value="' + objectIDPost + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form> in special education forum'
                add_admin_log(datetime.now(), action, post.get(comment, {}).get('postContent'))
                post.pop(comment, None)
                post['amount'] = post.get('amount') - 1
                collection.replace_one({'_id': ObjectId(objectIDPost)}, post) #almost the same as adding posts, but removing the specific comment from the post. Adds action to admin log as well.
            else:
                action = session['user_data']['login'] + '<span class="deleteColor"> deleted </span>a comment by ' + post.get(comment, {}).get('parentName') + ' / ' + post.get(comment, {}).get('studentNameGrade') + ' in the post <form action="/viewSEA" class="inLine"><select class="selection" name="thread"><option value="' + objectIDPost + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form> in special education forum'
                add_admin_log(datetime.now(), action, post.get(comment, {}).get('postContent'))
                post.pop(comment, None)
                post['amount'] = post.get('amount') - 1
                collection.replace_one({'_id': ObjectId(objectIDPost)}, post) 
            return view_SEA(objectIDPost)
        elif collection == db['SEU']:
            if post.get(comment, {}).get('adminName') != None:
                action = session['user_data']['login'] + '<span class="deleteColor"> deleted </span>a comment by ' + post.get(comment, {}).get('adminName') + ' in the post <form action="/viewSEU" class="inLine"><select class="selection" name="thread"><option value="' + objectIDPost + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form> in special education forum'
                add_admin_log(datetime.now(), action, post.get(comment, {}).get('postContent'))
                post.pop(comment, None)
                post['amount'] = post.get('amount') - 1
                collection.replace_one({'_id': ObjectId(objectIDPost)}, post)
            else:
                action = session['user_data']['login'] + '<span class="deleteColor"> deleted </span>a comment by ' + post.get(comment, {}).get('parentName') + ' / ' + post.get(comment, {}).get('studentNameGrade') + ' in the post <form action="/viewSEU" class="inLine"><select class="selection" name="thread"><option value="' + objectIDPost + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form> in special education forum'
                add_admin_log(datetime.now(), action, post.get(comment, {}).get('postContent'))
                post.pop(comment, None)
                post['amount'] = post.get('amount') - 1
                collection.replace_one({'_id': ObjectId(objectIDPost)}, post)
            return view_SEU(objectIDPost)
        elif collection == db['ELLA']:
            if post.get(comment, {}).get('adminName') != None:
                action = session['user_data']['login'] + '<span class="deleteColor"> deleted </span>a comment by ' + post.get(comment, {}).get('adminName') + ' in the post <form action="/viewELLA" class="inLine"><select class="selection" name="thread"><option value="' + objectIDPost + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form> in english language learner forum'
                add_admin_log(datetime.now(), action, post.get(comment, {}).get('postContent'))
                post.pop(comment, None)
                post['amount'] = post.get('amount') - 1
                collection.replace_one({'_id': ObjectId(objectIDPost)}, post)
            else:
                action = session['user_data']['login'] + '<span class="deleteColor"> deleted </span>a comment by ' + post.get(comment, {}).get('parentName') + ' / ' + post.get(comment, {}).get('studentNameGrade') + ' in the post <form action="/viewELLA" class="inLine"><select class="selection" name="thread"><option value="' + objectIDPost + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form> in english language learner forum'
                add_admin_log(datetime.now(), action, post.get(comment, {}).get('postContent'))
                post.pop(comment, None)
                post['amount'] = post.get('amount') - 1
                collection.replace_one({'_id': ObjectId(objectIDPost)}, post)
            return view_ELLA(objectIDPost)
        elif collection == db['ELLU']:
            if post.get(comment, {}).get('adminName') != None:
                action = session['user_data']['login'] + '<span class="deleteColor"> deleted </span>a comment by ' + post.get(comment, {}).get('adminName') + ' in the post <form action="/viewELLU" class="inLine"><select class="selection" name="thread"><option value="' + objectIDPost + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form> in english language learner forum'
                add_admin_log(datetime.now(), action, post.get(comment, {}).get('postContent'))
                post.pop(comment, None)
                post['amount'] = post.get('amount') - 1
                collection.replace_one({'_id': ObjectId(objectIDPost)}, post)
            else:
                action = session['user_data']['login'] + '<span class="deleteColor"> deleted </span>a comment by ' + post.get(comment, {}).get('parentName') + ' / ' + post.get(comment, {}).get('studentNameGrade') + ' in the post <form action="/viewELLU" class="inLine"><select class="selection" name="thread"><option value="' + objectIDPost + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form> in english language learner forum'
                add_admin_log(datetime.now(), action, post.get(comment, {}).get('postContent'))
                post.pop(comment, None)
                post['amount'] = post.get('amount') - 1
                collection.replace_one({'_id': ObjectId(objectIDPost)}, post)
            return view_ELLU(objectIDPost)
    return render_template('information.html')

@app.route('/vetComment', methods=['GET', 'POST'])
def vet_comment():
    if request.method == 'POST':
        objectIDPost = request.form['vet']
        collection = db['SEU']
        post = collection.find_one({'_id': ObjectId(objectIDPost)})
        if post == None:
            collection = db['SEA']
            post = collection.find_one({'_id': ObjectId(objectIDPost)})
        if post == None:
            collection = db['ELLA']
            post = collection.find_one({'_id': ObjectId(objectIDPost)})
        if post == None:
            collection = db['ELLU'] #if statements find out what collection the commented post belongs to, as well as the post itself
            post = collection.find_one({'_id': ObjectId(objectIDPost)})
        post[request.form['comment']]['approved'] = 'true'
        post['amount'] = post.get('amount') + 1
        collection.replace_one({'_id': ObjectId(objectIDPost)}, post) #changes the approved field to true for the comment in the post
        if collection == db['SEA']:
            action = session['user_data']['login'] + '<span class="vettingColor"> vetted </span>a comment by ' + post.get(request.form['comment'], {}).get('parentName') + ' in the post <form action="/viewSEA" class="inLine"><select class="selection" name="thread"><option value="' + objectIDPost + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form> in special education forum'
            add_admin_log(datetime.now(), action, 'none') #these return the page that comment was on and adds the action to the log
            return view_SEA(objectIDPost)
        elif collection == db['SEU']:
            action = session['user_data']['login'] + '<span class="vettingColor"> vetted </span>a comment by ' + post.get(request.form['comment'], {}).get('parentName') + ' in the post <form action="/viewSEU" class="inLine"><select class="selection" name="thread"><option value="' + objectIDPost + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form> in special education forum'
            add_admin_log(datetime.now(), action, 'none')
            return view_SEU(objectIDPost)
        elif collection == db['ELLA']:
            action = session['user_data']['login'] + '<span class="vettingColor"> vetted </span>a comment by ' + post.get(request.form['comment'], {}).get('parentName') + ' in the post <form action="/viewELLA" class="inLine"><select class="selection" name="thread"><option value="' + objectIDPost + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form> in english language learner forum'
            add_admin_log(datetime.now(), action, 'none')
            return view_ELLA(objectIDPost)
        elif collection == db['ELLU']:
            action = session['user_data']['login'] + '<span class="vettingColor"> vetted </span>a comment by ' + post.get(request.form['comment'], {}).get('parentName') + ' in the post <form action="/viewELLU" class="inLine"><select class="selection" name="thread"><option value="' + objectIDPost + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form> in english language learner forum'
            add_admin_log(datetime.now(), action, 'none')
            return view_ELLU(objectIDPost)
    return render_template('information.html')
        
@app.route('/unvetComment', methods=['GET', 'POST']) #pretty much the same code as vetting comments, except it unvets them.
def unvet_comment():
    if request.method == 'POST':
        objectIDPost = request.form['vet']
        collection = db['SEU']
        post = collection.find_one({'_id': ObjectId(objectIDPost)})
        if post == None:
            collection = db['SEA']
            post = collection.find_one({'_id': ObjectId(objectIDPost)})
        if post == None:
            collection = db['ELLA']
            post = collection.find_one({'_id': ObjectId(objectIDPost)})
        if post == None:
            collection = db['ELLU']
            post = collection.find_one({'_id': ObjectId(objectIDPost)})
        post[request.form['comment']]['approved'] = 'false'
        post['amount'] = post.get('amount') - 1
        collection.replace_one({'_id': ObjectId(objectIDPost)}, post)
        if collection == db['SEA']:
            action = session['user_data']['login'] + '<span class="vettingColor"> unvetted </span>a comment by ' + post.get(request.form['comment'], {}).get('parentName') + ' in the post <form action="/viewSEU" class="inLine"><select class="selection" name="thread"><option value="' + objectIDPost + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form> in special education forum'
            add_admin_log(datetime.now(), action, 'none')
            return view_SEA(objectIDPost)
        elif collection == db['SEU']:
            action = session['user_data']['login'] + '<span class="vettingColor"> unvetted </span>a comment by ' + post.get(request.form['comment'], {}).get('parentName') + ' in the post <form action="/viewSEA" class="inLine"><select class="selection" name="thread"><option value="' + objectIDPost + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form> in special education forum'
            add_admin_log(datetime.now(), action, 'none')
            return view_SEU(objectIDPost)
        elif collection == db['ELLA']:
            action = session['user_data']['login'] + '<span class="vettingColor"> unvetted </span>a comment by ' + post.get(request.form['comment'], {}).get('parentName') + ' in the post <form action="/viewELLA" class="inLine"><select class="selection" name="thread"><option value="' + objectIDPost + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form> in english language learner forum'
            add_admin_log(datetime.now(), action, 'none')
            return view_ELLA(objectIDPost)
        elif collection == db['ELLU']:
            action = session['user_data']['login'] + '<span class="vettingColor"> unvetted </span>a comment by ' + post.get(request.form['comment'], {}).get('parentName') + ' in the post <form action="/viewELLU" class="inLine"><select class="selection" name="thread"><option value="' + objectIDPost + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form> in english language learner forum'
            add_admin_log(datetime.now(), action, 'none')
            return view_ELLU(objectIDPost)
    return render_template('information.html')

@app.route('/viewSEA') #when viewer clicks on a post in the special education admin forum
def reroute_view_SEA():
    objectIDPost = request.args['thread']
    return view_SEA(objectIDPost)

@app.route('/viewSEU') #when viewer clicks on a post in the special education user forum
def reroute_view_SEU():
    objectIDPost = request.args['thread']
    return view_SEU(objectIDPost)

@app.route('/viewELLA') #when viewer clicks on a post in the english language learner admin forum
def reroute_view_ELLA():
    objectIDPost = request.args['thread']
    return view_ELLA(objectIDPost)

@app.route('/viewELLU') #when viewer clicks on a post in the english language learner admin forum
def reroute_view_ELLU():
    objectIDPost = request.args['thread']
    return view_ELLU(objectIDPost)

def view_SEA(objectIDPost): #render the contents and comments of the special education admin post.
    collection = db['SEA']
    post = collection.find_one({'_id': ObjectId(objectIDPost)})
    postTitle = post.get('postTitle')
    postContent = post.get('postContent')
    utc_dt = datetime(int(post.get('dateTime').strftime('%Y')), int(post.get('dateTime').strftime('%m')), int(post.get('dateTime').strftime('%d')), int(post.get('dateTime').strftime('%H')), int(post.get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
    loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
    if int(loc_dt.strftime('%H')) > 12:
        hour = str(int(loc_dt.strftime('%H')) - 12)
        loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
    else:
        hour = str(int(loc_dt.strftime('%H')))
        if hour == '0':
            hour = '12'
        loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
    displayName = post.get('adminName') #chunk above gets the post title, content, datetime, etc. of the post. Below is where comments html are generated
    keyList = list(post.keys())
    commentAmount = 0
    for item in keyList: #number of comments on the post, so it knows how many comments it should be going through.
        if 'comment' in item:
            commentAmount += 1
    bigString = ''
    counter = 0
    i = 0 #the number in 'comment3' or 'comment23'. 
    if 'github_token' in session: #if the viewer is an admin
        while counter < commentAmount: #goes through all the comments
            if('comment' + str(i) in post): #checks if the comment with the end number exists. If it does, generate html code for it.
                utc_dt = datetime(int(post.get('comment' + str(i), {}).get('dateTime').strftime('%Y')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%m')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%d')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%H')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
                loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
                if int(loc_dt.strftime('%H')) > 12:
                    hour = str(int(loc_dt.strftime('%H')) - 12)
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
                else:
                    hour = str(int(loc_dt.strftime('%H')))
                    if hour == '0':
                        hour = '12'
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
                if post.get('comment' + str(i), {}).get('adminName') != None: #if it is an admin post
                    bigString += '<tr><td class="comments"><b>' + post.get('comment' + str(i), {}).get('adminName') + '<span class="staff"> (Staff)</span></b><br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent')
                else:
                    bigString += '<tr><td class="comments"><b>' + post.get('comment' + str(i), {}).get('parentName') + '</b> / ' + post.get('comment' + str(i), {}).get('studentNameGrade') + '<br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent')
                bigString += '<div class="rightAlign">'
                if post.get('comment' + str(i), {}).get('adminName') == None: #if it is an admin post, add admin buttons.
                    if(post.get('comment' + str(i), {}).get('approved') == 'false'):
                        bigString += '<form action="/vetComment" method="post" class="inLine"><input name="comment" type="hidden" value="' + 'comment' + str(i) + '"><button type="submit" class="btn btn-warning btn-sm" name="vet" value="' + str(post.get('_id'))+ '">' + '<span class="glyphicon glyphicon-plus"></span> Vet</button></form> '
                    else:
                        bigString += '<form action="/unvetComment" method="post" class="inLine"><input name="comment" type="hidden" value="' + 'comment' + str(i) + '"><button type="submit" class="btn btn-warning btn-sm" name="vet" value="' + str(post.get('_id'))+ '">' + '<span class="glyphicon glyphicon-minus"></span> Unvet</button></form> '
                bigString += '<button type="button" class="btn btn-danger btn-sm delete"><span class="glyphicon glyphicon-trash"></span> Delete</button><button type="button" class="btn btn-danger btn-sm cancel inLine">Cancel</button> <form action="/deleteComment" method="post" class="inLine confirm"><input name="comment" type="hidden" value="' + 'comment' + str(i) + '"><button type="submit" class="btn btn-danger btn-sm" name="delete" value="' + str(post.get('_id')) + '"><span class="glyphicon glyphicon-trash"></span> Confirm Delete</button></form>'
                bigString += '</div></td></tr>'
                counter += 1
            i += 1
    else: #if the viewer is not an admin
        while counter < commentAmount: #goes through all the comments
            if('comment' + str(i) in post): #checks if the comment with the end number exists. If it does, generate html code for it.
                utc_dt = datetime(int(post.get('comment' + str(i), {}).get('dateTime').strftime('%Y')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%m')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%d')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%H')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
                loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
                if int(loc_dt.strftime('%H')) > 12:
                    hour = str(int(loc_dt.strftime('%H')) - 12)
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
                else:
                    hour = str(int(loc_dt.strftime('%H')))
                    if hour == '0':
                        hour = '12'
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
                if post.get('comment' + str(i), {}).get('adminName') != None: #if the comment is by an admin
                    bigString += '<tr><td class="comments"><b>' + post.get('comment' + str(i), {}).get('adminName') + '<span class="staff"> (Staff)</span></b><br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent') + '</td></tr>'
                else: #if the comment is by a user
                    if post.get('comment' + str(i), {}).get('approved') == 'true': #if the comment is vetted
                        if post.get('comment' + str(i), {}).get('anonymous') == 'true': #if the comment is anonymous, don't display the name,
                            bigString += '<tr><td class="comments"><b> Anonymous Comment</b><br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent') + '</td></tr>'
                        else:
                            bigString += '<tr><td class="comments"><b>' + post.get('comment' + str(i), {}).get('parentName') + '</b><br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent') + '</td></tr>'
                counter += 1
            i += 1
    return render_template('comments.html', title = postTitle, name = displayName, information = '', time = loc_dt, content = Markup(postContent), _id = objectIDPost, comments = Markup(bigString), oldContent = Markup(postContent), oldTitle = postTitle, page = 'specialeducationforum')

def view_SEU(objectIDPost): #go to view_SEA for comments since these functions work the same way.
    collection = db['SEU']
    post = collection.find_one({'_id': ObjectId(objectIDPost)})
    postTitle = post.get('postTitle')
    postContent = post.get('postContent')
    utc_dt = datetime(int(post.get('dateTime').strftime('%Y')), int(post.get('dateTime').strftime('%m')), int(post.get('dateTime').strftime('%d')), int(post.get('dateTime').strftime('%H')), int(post.get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
    loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
    if int(loc_dt.strftime('%H')) > 12:
        hour = str(int(loc_dt.strftime('%H')) - 12)
        loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
    else:
        hour = str(int(loc_dt.strftime('%H')))
        if hour == '0':
            hour = '12'
        loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
    if 'github_token' in session:
        parentName = post.get('parentName')
        studentNameGrade = post.get('studentNameGrade')
        parentEmail = post.get('parentEmail')
        if parentEmail == '':
            parentEmail = 'Email not provided'
    else:
        if post.get('anonymous') == 'false':
            parentName = post.get('parentName')
        else:
            parentName = 'Anonymous Post'
        studentNameGrade = ''
        parentEmail = ''
    info = ' / ' + studentNameGrade + ' / ' + parentEmail
    bigString = ''
    keyList = list(post.keys())
    commentAmount = 0
    for item in keyList:
        if 'comment' in item:
            commentAmount += 1
    bigString = ''
    counter = 0
    i = 0
    if 'github_token' in session: #if admin is logged in
        while counter < commentAmount:
            if('comment' + str(i) in post):
                utc_dt = datetime(int(post.get('comment' + str(i), {}).get('dateTime').strftime('%Y')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%m')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%d')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%H')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
                loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
                if int(loc_dt.strftime('%H')) > 12:
                    hour = str(int(loc_dt.strftime('%H')) - 12)
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
                else:
                    hour = str(int(loc_dt.strftime('%H')))
                    if hour == '0':
                        hour = '12'
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
                if post.get('comment' + str(i), {}).get('adminName') != None: #checks if it is admin post
                    bigString += '<tr><td class="comments"><b>' + post.get('comment' + str(i), {}).get('adminName') + '<span class="staff"> (Staff)</span></b><br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent')
                else:
                    bigString += '<tr><td class="comments"><b>' + post.get('comment' + str(i), {}).get('parentName') + '</b> / ' + post.get('comment' + str(i), {}).get('studentNameGrade') + '<br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent')
                bigString += '<div class="rightAlign">'
                if post.get('comment' + str(i), {}).get('adminName') == None:
                    if(post.get('comment' + str(i), {}).get('approved') == 'false'):
                        bigString += '<form action="/vetComment" method="post" class="inLine"><input name="comment" type="hidden" value="' + 'comment' + str(i) + '"><button type="submit" class="btn btn-warning btn-sm" name="vet" value="' + str(post.get('_id'))+ '">' + '<span class="glyphicon glyphicon-plus"></span> Vet</button></form> '
                    else:
                        bigString += '<form action="/unvetComment" method="post" class="inLine"><input name="comment" type="hidden" value="' + 'comment' + str(i) + '"><button type="submit" class="btn btn-warning btn-sm" name="vet" value="' + str(post.get('_id'))+ '">' + '<span class="glyphicon glyphicon-minus"></span> Unvet</button></form> '
                bigString += '<button type="button" class="btn btn-danger btn-sm delete"><span class="glyphicon glyphicon-trash"></span> Delete</button><button type="button" class="btn btn-danger btn-sm cancel inLine">Cancel</button> <form action="/deleteComment" method="post" class="inLine confirm"><input name="comment" type="hidden" value="' + 'comment' + str(i) + '"><button type="submit" class="btn btn-danger btn-sm" name="delete" value="' + str(post.get('_id')) + '"><span class="glyphicon glyphicon-trash"></span> Confirm Delete</button></form>'
                bigString += '</div></td></tr>'
                counter += 1
            i += 1
    else:
        while counter < commentAmount:
            if('comment' + str(i) in post):
                utc_dt = datetime(int(post.get('comment' + str(i), {}).get('dateTime').strftime('%Y')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%m')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%d')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%H')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
                loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
                if int(loc_dt.strftime('%H')) > 12:
                    hour = str(int(loc_dt.strftime('%H')) - 12)
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
                else:
                    hour = str(int(loc_dt.strftime('%H')))
                    if hour == '0':
                        hour = '12'
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
                if post.get('comment' + str(i), {}).get('adminName') != None:
                    bigString += '<tr><td class="comments"><b>' + post.get('comment' + str(i), {}).get('adminName') + '<span class="staff"> (Staff)</span></b><br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent') + '</td></tr>'
                else:
                    if post.get('comment' + str(i), {}).get('approved') == 'true':
                        if post.get('comment' + str(i), {}).get('anonymous') == 'true':
                            bigString += '<tr><td class="comments"><b> Anonymous Comment</b><br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent') + '</td></tr>'
                        else:
                            bigString += '<tr><td class="comments"><b>' + post.get('comment' + str(i), {}).get('parentName') + '</b><br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent') + '</td></tr>'
                counter += 1
            i += 1
    return render_template('comments.html', title = postTitle, name = parentName, information = info, time = loc_dt, content = Markup(postContent), _id = objectIDPost, comments = Markup(bigString), oldContent = Markup(postContent), oldTitle = postTitle, page = 'specialeducationforum')

def view_ELLA(objectIDPost): #go to view_SEA for comments since these functions work the same way.
    collection = db['ELLA']
    post = collection.find_one({'_id': ObjectId(objectIDPost)})
    postTitle = post.get('postTitle')
    postContent = post.get('postContent')
    utc_dt = datetime(int(post.get('dateTime').strftime('%Y')), int(post.get('dateTime').strftime('%m')), int(post.get('dateTime').strftime('%d')), int(post.get('dateTime').strftime('%H')), int(post.get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
    loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
    if int(loc_dt.strftime('%H')) > 12:
        hour = str(int(loc_dt.strftime('%H')) - 12)
        loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
    else:
        hour = str(int(loc_dt.strftime('%H')))
        if hour == '0':
            hour = '12'
        loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
    displayName = post.get('adminName')
    bigString = ''
    keyList = list(post.keys())
    commentAmount = 0
    for item in keyList:
        if 'comment' in item:
            commentAmount += 1
    bigString = ''
    keyList = list(post.keys())
    commentAmount = 0
    for item in keyList:
        if 'comment' in item:
            commentAmount += 1
    bigString = ''
    counter = 0
    i = 0
    if 'github_token' in session: #if admin is logged in
        while counter < commentAmount:
            if('comment' + str(i) in post):
                utc_dt = datetime(int(post.get('comment' + str(i), {}).get('dateTime').strftime('%Y')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%m')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%d')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%H')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
                loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
                if int(loc_dt.strftime('%H')) > 12:
                    hour = str(int(loc_dt.strftime('%H')) - 12)
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
                else:
                    hour = str(int(loc_dt.strftime('%H')))
                    if hour == '0':
                        hour = '12'
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
                if post.get('comment' + str(i), {}).get('adminName') != None: #checks if it is admin post
                    bigString += '<tr><td class="comments"><b>' + post.get('comment' + str(i), {}).get('adminName') + '<span class="staff"> (Staff)</span></b><br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent')
                else:
                    bigString += '<tr><td class="comments"><b>' + post.get('comment' + str(i), {}).get('parentName') + '</b> / ' + post.get('comment' + str(i), {}).get('studentNameGrade') + '<br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent')
                bigString += '<div class="rightAlign">'
                if post.get('comment' + str(i), {}).get('adminName') == None:
                    if(post.get('comment' + str(i), {}).get('approved') == 'false'):
                        bigString += '<form action="/vetComment" method="post" class="inLine"><input name="comment" type="hidden" value="' + 'comment' + str(i) + '"><button type="submit" class="btn btn-warning btn-sm" name="vet" value="' + str(post.get('_id'))+ '">' + '<span class="glyphicon glyphicon-plus"></span> Vet</button></form> '
                    else:
                        bigString += '<form action="/unvetComment" method="post" class="inLine"><input name="comment" type="hidden" value="' + 'comment' + str(i) + '"><button type="submit" class="btn btn-warning btn-sm" name="vet" value="' + str(post.get('_id'))+ '">' + '<span class="glyphicon glyphicon-minus"></span> Unvet</button></form> '
                bigString += '<button type="button" class="btn btn-danger btn-sm delete"><span class="glyphicon glyphicon-trash"></span> Delete</button><button type="button" class="btn btn-danger btn-sm cancel inLine">Cancel</button> <form action="/deleteComment" method="post" class="inLine confirm"><input name="comment" type="hidden" value="' + 'comment' + str(i) + '"><button type="submit" class="btn btn-danger btn-sm" name="delete" value="' + str(post.get('_id')) + '"><span class="glyphicon glyphicon-trash"></span> Confirm Delete</button></form>'
                bigString += '</div></td></tr>'
                counter += 1
            i += 1
    else:
        while counter < commentAmount:
            if('comment' + str(i) in post):
                utc_dt = datetime(int(post.get('comment' + str(i), {}).get('dateTime').strftime('%Y')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%m')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%d')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%H')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
                loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
                if int(loc_dt.strftime('%H')) > 12:
                    hour = str(int(loc_dt.strftime('%H')) - 12)
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
                else:
                    hour = str(int(loc_dt.strftime('%H')))
                    if hour == '0':
                        hour = '12'
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
                if post.get('comment' + str(i), {}).get('adminName') != None:
                    bigString += '<tr><td class="comments"><b>' + post.get('comment' + str(i), {}).get('adminName') + '<span class="staff"> (Staff)</span></b><br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent') + '</td></tr>'
                else:
                    if post.get('comment' + str(i), {}).get('approved') == 'true':
                        if post.get('comment' + str(i), {}).get('anonymous') == 'true':
                            bigString += '<tr><td class="comments"><b> Anonymous Comment</b><br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent') + '</td></tr>'
                        else:
                            bigString += '<tr><td class="comments"><b>' + post.get('comment' + str(i), {}).get('parentName') + '</b><br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent') + '</td></tr>'
                counter += 1
            i += 1
    return render_template('comments.html', title = postTitle, name = displayName, information = '', time = loc_dt, content = Markup(postContent), _id = objectIDPost, comments = Markup(bigString), oldContent = Markup(postContent), oldTitle = postTitle, page = 'englishlearnerforum')

def view_ELLU(objectIDPost): #go to view_SEA for comments since these functions work the same way.
    collection = db['ELLU']
    post = collection.find_one({'_id': ObjectId(objectIDPost)})
    postTitle = post.get('postTitle')
    postContent = post.get('postContent')
    utc_dt = datetime(int(post.get('dateTime').strftime('%Y')), int(post.get('dateTime').strftime('%m')), int(post.get('dateTime').strftime('%d')), int(post.get('dateTime').strftime('%H')), int(post.get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
    loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
    if int(loc_dt.strftime('%H')) > 12:
        hour = str(int(loc_dt.strftime('%H')) - 12)
        loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
    else:
        hour = str(int(loc_dt.strftime('%H')))
        if hour == '0':
            hour = '12'
        loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
    if 'github_token' in session:
        parentName = post.get('parentName')
        studentNameGrade = post.get('studentNameGrade')
        parentEmail = post.get('parentEmail')
        if parentEmail == '':
            parentEmail = 'Email not provided'
    else:
        if post.get('anonymous') == 'false':
            parentName = post.get('parentName')
        else:
            parentName = 'Anonymous Post'
        studentNameGrade = ''
        parentEmail = ''
    info = ' / ' + studentNameGrade + ' / ' + parentEmail
    bigString = ''
    keyList = list(post.keys())
    commentAmount = 0
    for item in keyList:
        if 'comment' in item:
            commentAmount += 1
    bigString = ''
    counter = 0
    i = 0
    if 'github_token' in session: #if admin is logged in
        while counter < commentAmount:
            if('comment' + str(i) in post):
                utc_dt = datetime(int(post.get('comment' + str(i), {}).get('dateTime').strftime('%Y')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%m')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%d')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%H')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
                loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
                if int(loc_dt.strftime('%H')) > 12:
                    hour = str(int(loc_dt.strftime('%H')) - 12)
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
                else:
                    hour = str(int(loc_dt.strftime('%H')))
                    if hour == '0':
                        hour = '12'
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
                if post.get('comment' + str(i), {}).get('adminName') != None: #checks if it is admin post
                    bigString += '<tr><td class="comments"><b>' + post.get('comment' + str(i), {}).get('adminName') + '<span class="staff"> (Staff)</span></b><br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent')
                else:
                    bigString += '<tr><td class="comments"><b>' + post.get('comment' + str(i), {}).get('parentName') + '</b> / ' + post.get('comment' + str(i), {}).get('studentNameGrade') + '<br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent')
                bigString += '<div class="rightAlign">'
                if post.get('comment' + str(i), {}).get('adminName') == None:
                    if(post.get('comment' + str(i), {}).get('approved') == 'false'):
                        bigString += '<form action="/vetComment" method="post" class="inLine"><input name="comment" type="hidden" value="' + 'comment' + str(i) + '"><button type="submit" class="btn btn-warning btn-sm" name="vet" value="' + str(post.get('_id'))+ '">' + '<span class="glyphicon glyphicon-plus"></span> Vet</button></form> '
                    else:
                        bigString += '<form action="/unvetComment" method="post" class="inLine"><input name="comment" type="hidden" value="' + 'comment' + str(i) + '"><button type="submit" class="btn btn-warning btn-sm" name="vet" value="' + str(post.get('_id'))+ '">' + '<span class="glyphicon glyphicon-minus"></span> Unvet</button></form> '
                bigString += '<button type="button" class="btn btn-danger btn-sm delete"><span class="glyphicon glyphicon-trash"></span> Delete</button><button type="button" class="btn btn-danger btn-sm cancel inLine">Cancel</button> <form action="/deleteComment" method="post" class="inLine confirm"><input name="comment" type="hidden" value="' + 'comment' + str(i) + '"><button type="submit" class="btn btn-danger btn-sm" name="delete" value="' + str(post.get('_id')) + '"><span class="glyphicon glyphicon-trash"></span> Confirm Delete</button></form>'
                bigString += '</div></td></tr>'
                counter += 1
            i += 1
    else:
        while counter < commentAmount:
            if('comment' + str(i) in post):
                utc_dt = datetime(int(post.get('comment' + str(i), {}).get('dateTime').strftime('%Y')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%m')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%d')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%H')), int(post.get('comment' + str(i), {}).get('dateTime').strftime('%M')), 0, tzinfo=pytz.utc)
                loc_dt = utc_dt.astimezone(timezone('America/Los_Angeles'))
                if int(loc_dt.strftime('%H')) > 12:
                    hour = str(int(loc_dt.strftime('%H')) - 12)
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M PM PT')
                else:
                    hour = str(int(loc_dt.strftime('%H')))
                    if hour == '0':
                        hour = '12'
                    loc_dt = loc_dt.strftime('%m/%d/%Y, ' + hour + ':%M AM PT')
                if post.get('comment' + str(i), {}).get('adminName') != None:
                    bigString += '<tr><td class="comments"><b>' + post.get('comment' + str(i), {}).get('adminName') + '<span class="staff"> (Staff)</span></b><br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent') + '</td></tr>'
                else:
                    if post.get('comment' + str(i), {}).get('approved') == 'true':
                        if post.get('comment' + str(i), {}).get('anonymous') == 'true':
                            bigString += '<tr><td class="comments"><b> Anonymous Comment</b><br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent') + '</td></tr>'
                        else:
                            bigString += '<tr><td class="comments"><b>' + post.get('comment' + str(i), {}).get('parentName') + '</b><br><i>' + loc_dt + '</i><br><br>' + post.get('comment' + str(i), {}).get('postContent') + '</td></tr>'
                counter += 1
            i += 1
    return render_template('comments.html', title = postTitle, name = parentName, information = info, time = loc_dt, content = Markup(postContent), _id = objectIDPost, comments = Markup(bigString), oldContent = Markup(postContent), oldTitle = postTitle, page = 'englishlearnerforum')

@app.route('/deleteSE', methods=['GET', 'POST']) #deletes a user or admin post in the special education forum
def delete_SE():
    if request.method == 'POST':
        objectIDPost = request.form['delete']
        collection = db['SEA']
        post = collection.find_one({'_id': ObjectId(objectIDPost)}) #finds the post
        if post == None:
            collection = db['SEU']
            post = collection.find_one({'_id': ObjectId(objectIDPost)}) #finds the post
            name = post.get('parentName') + ' / ' + post.get('studentNameGrade') + ' / ' + post.get('parentEmail') #gets for log
        else:
            name = post.get('adminName') #gets for log
        collection.delete_one({'_id': ObjectId(objectIDPost)}) #deletes the post
        action = session['user_data']['login'] + '<span class="deleteColor"> deleted </span><b>' + post.get('postTitle') + '</b> by ' + name + ' in english language learner forum'
        add_admin_log(datetime.now(), action, post.get('postContent')) #adds action to log
    return render_special_education_forum()

@app.route('/deleteELL', methods=['GET', 'POST']) #works the same way as delete_se
def delete_ELL():
    if request.method == 'POST':
        objectIDPost = request.form['delete']
        collection = db['ELLA']
        post = collection.find_one({'_id': ObjectId(objectIDPost)})
        if post == None:
            collection = db['ELLU']
            post = collection.find_one({'_id': ObjectId(objectIDPost)})
            name = post.get('parentName') + ' / ' + post.get('studentNameGrade') + ' / ' + post.get('parentEmail')
        else:
            name = post.get('adminName')
        collection.delete_one({'_id': ObjectId(objectIDPost)})
        action = session['user_data']['login'] + '<span class="deleteColor"> deleted </span><b>' + post.get('postTitle') + '</b> by ' + name + ' in english language learner forum'
        add_admin_log(datetime.now(), action, post.get('postContent'))
    return render_english_learner_forum()

@app.route('/vetELL', methods=['GET', 'POST']) #vets a user post in english language learner forum
def vet_ELL():
    if request.method == 'POST':
        objectIDPost = request.form['vet']
        collection = db['ELLU']
        collection.find_one_and_update({'_id': ObjectId(objectIDPost)}, #finds and updates the post's approved field to true
                                       {'$set': {'approved': 'true'}})
        post = collection.find_one({'_id': ObjectId(objectIDPost)})
        action = session['user_data']['login'] + '<span class="vettingColor"> vetted </span><form action="/viewELLU" class="inLine"><select class="selection" name="thread"><option value="' + objectIDPost + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form> in english language learner forum'
        add_admin_log(datetime.now(), action, 'none') #adds action to log
    return render_english_learner_forum()
                                             
@app.route('/unvetELL', methods=['GET', 'POST']) #unvets a user post in english language learner forum
def unvet_ELL():
    if request.method == 'POST':
        objectIDPost = request.form['vet']
        collection = db['ELLU']
        collection.find_one_and_update({'_id': ObjectId(objectIDPost)}, #finds and updates the post's approved field to false
                                       {'$set': {'approved': 'false'}}) 
        post = collection.find_one({'_id': ObjectId(objectIDPost)})
        action = session['user_data']['login'] + '<span class="vettingColor"> unvetted </span><form action="/viewELLU" class="inLine"><select class="selection" name="thread"><option value="' + objectIDPost + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form> in english language learner forum'
        add_admin_log(datetime.now(), action, 'none') #adds action to log
    return render_english_learner_forum()
                                             
@app.route('/vetSE', methods=['GET', 'POST']) #works the same as vet_ell
def vet_SE():
    if request.method == 'POST':
        objectIDPost = request.form['vet'] 
        connection_string = os.environ['MONGO_CONNECTION_STRING']
        db_name = os.environ['MONGO_DBNAME']
        client = pymongo.MongoClient(connection_string)
        db = client[db_name]       
        collection = db['SEU']
        collection.find_one_and_update({'_id': ObjectId(objectIDPost)},
                                       {'$set': {'approved': 'true'}})
        post = collection.find_one({'_id': ObjectId(objectIDPost)})
        action = session['user_data']['login'] + '<span class="vettingColor"> vetted </span><form action="/viewSEU" class="inLine"><select class="selection" name="thread"><option value="' + objectIDPost + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form> in special education forum'
        add_admin_log(datetime.now(), action, 'none')
    return render_special_education_forum()
                                             
@app.route('/unvetSE', methods=['GET', 'POST']) #works the same as unvet_ell
def unvet_SE():
    if request.method == 'POST':
        objectIDPost = request.form['vet'] #vet and unvet posts
        collection = db['SEU']
        collection.find_one_and_update({'_id': ObjectId(objectIDPost)},
                                       {'$set': {'approved': 'false'}})
        post = collection.find_one({'_id': ObjectId(objectIDPost)})
        action = session['user_data']['login'] + '<span class="vettingColor"> unvetted </span><form action="/viewSEU" class="inLine"><select class="selection" name="thread"><option value="' + objectIDPost + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form> in special education forum'
        add_admin_log(datetime.now(), action, 'none')
    return render_special_education_forum()

@app.route('/bumpPost', methods=['GET', 'POST']) #sends a post to the top by giving the post a new document id
def bump_post():
    if request.method == 'POST':
        objectIDPost = request.form['bump']
        collection = db['SEU']
        post = collection.find_one({'_id': ObjectId(objectIDPost)})
        if post == None:
            collection = db['SEA']
            post = collection.find_one({'_id': ObjectId(objectIDPost)})
        if post == None:
            collection = db['ELLA']
            post = collection.find_one({'_id': ObjectId(objectIDPost)})
        if post == None:
            collection = db['ELLU']
            post = collection.find_one({'_id': ObjectId(objectIDPost)}) #if statements finds the collection the post is in, as well as the post itself.
        collection.delete_one({'_id': ObjectId(objectIDPost)}) #delete the document in the database
        generate = ObjectId() #generate a new object id for the post.
        post['_id'] = generate #gives the post the new id
        collection.insert_one(post) #inserts the post back into the database with a new id.
        if collection == db['SEU']: #returns to the page they were on, and adds the action to the log.
            action = session['user_data']['login'] + '<span class="bumpColor"> bumped </span><form action="/viewSEU" class="inLine"><select class="selection" name="thread"><option value="' + str(generate) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form> in special education forum'
            add_admin_log(datetime.now(), action, 'none')
            return render_special_education_forum()
        if collection == db['SEA']:
            action = session['user_data']['login'] + '<span class="bumpColor"> bumped </span><form action="/viewSEA" class="inLine"><select class="selection" name="thread"><option value="' + str(generate) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form> in special education forum'
            add_admin_log(datetime.now(), action, 'none')
            return render_special_education_forum()
        if collection == db['ELLA']:
            action = session['user_data']['login'] + '<span class="bumpColor"> bumped </span><form action="/viewELLA" class="inLine"><select class="selection" name="thread"><option value="' + str(generate) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form> in english language learner forum'
            add_admin_log(datetime.now(), action, 'none')
            return render_english_learner_forum()
        if collection == db['ELLU']:
            action = session['user_data']['login'] + '<span class="bumpColor"> bumped </span><form action="/viewELLU" class="inLine"><select class="selection" name="thread"><option value="' + str(generate) + '"></option></select><button type="submit" class="customButton commentButton"><b>' + post.get('postTitle') + '</b></button></form> in english language learner forum'
            add_admin_log(datetime.now(), action, 'none')
            return render_english_learner_forum()
    return render_template('information.html')

@app.route('/editPost', methods=['GET', 'POST']) #admins editing user or admin posts.
def edit_post():
    if request.method == 'POST':
        objectIDPost = request.form['ID'] 
        collection = db['SEU']
        post = collection.find_one({'_id': ObjectId(objectIDPost)})
        if post == None:
            collection = db['SEA']
            post = collection.find_one({'_id': ObjectId(objectIDPost)})
        if post == None:
            collection = db['ELLA']
            post = collection.find_one({'_id': ObjectId(objectIDPost)}) #if statements find what collection the post belongs to
        if post == None:
            collection = db['ELLU']
        content = request.form['newMessage']
        content = content.replace('\\"', '')
        content = content.replace('\\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
        content = content.replace(' ', '&nbsp;')
        content = Markup(content[1:len(content)-1]) #takes the new quill text and converts to content that is usable and readable.
        collection.find_one_and_update({'_id': ObjectId(objectIDPost)},
                                       {'$set': {'postTitle': request.form['newTitle'], 'postContent': content}}) #updates the post with the new title and content
        if collection == db['SEU']: #returns the editor to the post they were viewing and adds the action to the log
            action = session['user_data']['login'] + '<span class="vettingColor"> edited </span><form action="/viewSEU" class="inLine"><select class="selection" name="thread"><option value="' + objectIDPost + '"></option></select><button type="submit" class="customButton commentButton"><b>' + request.form['newTitle'] + '</b></button></form> in special education forum'
            add_admin_log(datetime.now(), action, 'none')
            return view_SEU(objectIDPost)
        if collection == db['SEA']:
            action = session['user_data']['login'] + '<span class="vettingColor"> edited </span><form action="/viewSEA" class="inLine"><select class="selection" name="thread"><option value="' + objectIDPost + '"></option></select><button type="submit" class="customButton commentButton"><b>' + request.form['newTitle'] + '</b></button></form> in special education forum'
            add_admin_log(datetime.now(), action, 'none')
            return view_SEA(objectIDPost)
        if collection == db['ELLA']:
            action = session['user_data']['login'] + '<span class="vettingColor"> edited </span><form action="/viewELLA" class="inLine"><select class="selection" name="thread"><option value="' + objectIDPost + '"></option></select><button type="submit" class="customButton commentButton"><b>' + request.form['newTitle'] + '</b></button></form> in english language learner forum'
            add_admin_log(datetime.now(), action, 'none')
            return view_ELLA(objectIDPost)
        if collection == db['ELLU']:
            action = session['user_data']['login'] + '<span class="vettingColor"> edited </span><form action="/viewELLU" class="inLine"><select class="selection" name="thread"><option value="' + objectIDPost + '"></option></select><button type="submit" class="customButton commentButton"><b>' + request.form['newTitle'] + '</b></button></form> in english language learner forum'
            add_admin_log(datetime.now(), action, 'none')
            return view_ELLU(objectIDPost)
    return render_template('information.html')
        

#make sure the jinja variables use Markup 
@github.tokengetter
def get_github_oauth_token():
    return session['github_token']

if __name__ == '__main__':
    app.run()
