# -*- coding: utf-8 -*-
"""
Created on Thu Mar 19 08:24:42 2020

@author: KUSH
"""
from flask import Flask , render_template , request , session ,redirect
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from werkzeug import secure_filename
import json
import os
import math
from datetime import datetime

#reading json file
with open('config.json' , 'r') as c:  
    params = json.load(c)["params"]
    
app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.config.update(
        MAIL_SERVER = 'smtp.gmail.com',
        MAIL_PORT = '465' , 
        MAIL_USE_SSL = 'True' , 
        MAIL_USERNAME = params['gmail-user'] , 
        MAIL_PASSWORD = params['gmail-password']
        )

mail = Mail(app)
local_server = True

if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']    
    
db = SQLAlchemy(app)

class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=False, nullable=False)
    email = db.Column(db.String(20), unique=True, nullable=False)
    phone_num = db.Column(db.String(12), unique=True, nullable=False)
    msg = db.Column(db.String(120), unique=True, nullable=False)
    date = db.Column(db.String(12), unique=True, nullable=True)

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=False, nullable=False)
    slug = db.Column(db.String(25), unique=True, nullable=False)
    content = db.Column(db.String(120), unique=True, nullable=False)
    tagline = db.Column(db.String(120), unique=True, nullable=False)
    date = db.Column(db.String(12), unique=True, nullable=True)
    img_file = db.Column(db.String(12), unique=True, nullable=False)
    
@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    #[0:params['no_of_posts']]
    last = math.ceil(len(posts)/int(params['no_of_posts']))
    #pagination logic
    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page=1
    page=int(page)
    posts = posts[(page-1)*int(params['no_of_posts']) : (page-1)*int(params['no_of_posts']) + int(params['no_of_posts'])]
    
    #first page
    if(page==1):
        prev= "#"
        Next = "/?page=" + str(page+1)
    #last page
    elif(page==last):
        prev = "/?page=" + str(page-1)
        Next = "#"
    #Any in between page    
    else:
        prev = "/?page=" + str(page-1)
        Next = "/?page=" + str(page+1)
        
    return render_template("index.html" , params=params , posts=posts ,prev=prev , Next=Next)

@app.route("/about")
def about():
    return render_template("about.html" , params=params)

@app.route("/dashboard" , methods=['GET', 'POST'])
def dashboard():
    if ('user' in session and session['user'] == params['admin_user']):
        posts = Posts.query.all()
        return render_template("dashboard.html",params=params,posts=posts)

    if request.method == 'POST':
        username=request.form.get('uname')
        userpass=request.form.get('pass')
        if(username==params['admin_user'] and userpass==params['admin_password']):
            #set session variable
            session['user'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html' , params=params , posts=posts)
    return render_template("login.html" , params=params)

@app.route("/contact" , methods = ["GET" , "POST"])
def contact():
    if(request.method == 'POST'):
        #add entry to database
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone-num')
        message = request.form.get('msg')
        
        entry = Contacts(name=name , email= email , phone_num=phone , msg=message , date = datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from ' + name , 
                          sender = email , 
                          recipients= [params['gmail-user']] ,
                          body = message + "\n" + phone
                          )
    return render_template("contact.html" , params=params)



@app.route("/post/<string:post_slug>" , methods=["GET"])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template("post.html" , params=params, post=post)

@app.route("/edit/<string:sno>" , methods=["GET" , "POST"])
def edit(sno):
    if ('user' in session and session['user']==params['admin_user']):
        if request.method == 'POST':
            title = request.form.get('title')
            tline = request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()
            if sno=='0':
                post = Posts(title=title , tagline=tline , slug = slug , content = content , img_file= img_file , date= date)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title=title
                post.content=content
                post.slug=slug
                post.tagline=tline
                post.img_file=img_file
                post.date= date
                db.session.commit()
                redirect("/edit/" + sno)
        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html' , params=params , post=post)

@app.route("/uploader" , methods=["GET","POST"])
def uploader():
    if ('user' in session and session['user']==params['admin_user']):
        if request.method == 'POST':
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
            return "uploaded successfully"

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect("/dashboard")
        
@app.route("/delete/<string:sno>" , methods=["GET" , "POST"])
def delete_post(sno):
        if ('user' in session and session['user']==params['admin_user']):
            post = Posts.query.filter_by(sno=sno).first()
            db.session.delete(post)
            db.session.commit()
        return redirect('/dashboard')
    
app.run(debug=False)
