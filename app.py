import os
from flask import Flask, render_template, request, redirect, url_for, abort, send_from_directory, session, flash
from datetime import timedelta, datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import bcrypt
import shutil

app = Flask(__name__)
# app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = ['.*']
app.config['UPLOAD_PATH'] = 'uploads/nullUser'

app.secret_key = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.permanent_session_lifetime = timedelta(minutes=30)

db = SQLAlchemy(app)

class users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    pwd = db.Column(db.String(100))

    def __init__(self, name, pwd):
        self.name = name
        self.pwd = pwd

@app.route("/", methods=["POST","GET"])
@app.route("/login", methods=["POST","GET"])
def login():
    if request.method == "POST":
        user = request.form["nm"]
        pwd = request.form["pwd"]

        found_user = users.query.filter_by(name=user).first()
        if found_user:
            if bcrypt.checkpw(pwd.encode('utf-8'),found_user.pwd) == True:
                session.permanent = True
                session["user"] = user
                session["pwd"] = found_user.pwd
                flash("Login Successful!",category='success')
                return redirect(url_for("upload_files"))
            else:
                flash("Password is wrong!",category='danger')
                return redirect(url_for("login"))
        else:
            flash("User Not Found!",category='danger')
            return redirect(url_for("login"))
    else:
        if "user" in session:
            flash("Already Logged in!",category='info')
            return redirect(url_for("upload_files"))
        return render_template("login.html") 

@app.route("/register", methods=["POST","GET"])
def register():
    if request.method == "POST":
        user = request.form["nm"]
        pwd = request.form["pwd"]
        pwd = bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt())

        found_user = users.query.filter_by(name=user).first()
        if found_user:
            flash("User already exists",category='info')
            return redirect(url_for("register"))
        else:
            session.permanent = True
            session["user"] = user
            usr = users(user, pwd)
            db.session.add(usr)
            db.session.commit()
            createFolder(f'./uploads/{user}')
            flash("User Registered Successfully!",category='success')
            return redirect(url_for("upload_files"))
    else:
        if "user" in session:
            flash("Already Logged in!",category='info')
            return redirect(url_for("upload_files"))
        return render_template("register.html") 

@app.route("/view")     # username: admin, password: admin
def view():
    if  "user" in session and session["user"] == "admin":
        return render_template("view.html", values = users.query.all())
    else:
        flash("You need administrator privileges to view this page",category='danger')
        return redirect(url_for("upload_files"))

@app.route('/view/delete/<int:id>')
def deleteusers(id):
    if "user" in session and session["user"] == "admin":
        currentuser = users.query.get_or_404(id)
        if currentuser.name == "admin":
            flash("Admin can't be deleted",'danger')
        else:
            deleteFolder(currentuser.name)
            db.session.delete(currentuser)
            db.session.commit()
            flash(f"User deleted from the database and contents (if any) are deleted too",category='success')
        return redirect(url_for("view"))
    else:
        flash("You need administrator privileges to view this page",category='danger')
        return redirect(url_for("login"))

@app.route("/logout")
def logout():
    app.config['UPLOAD_PATH'] = 'uploads/nullUser'
    session.pop("user", None)
    session.pop("pwd", None)
    flash("You have been logged out!",category="info")
    return redirect(url_for("login"))


# @app.errorhandler(413)
# def too_large(e):
#     return "File is too large", 413


def createFolder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print ('Error: Creating directory ' +  directory)

def deleteFolder(directory):
    mydir = f"./uploads/{directory}"
    try:
        shutil.rmtree(mydir)
    except OSError as e:
        print ("Error: Deleting directory " + directory)

def deleteFile(directory):
    if os.path.exists(directory):
        os.remove(directory)
    else:
        print("The file does not exist")

@app.route('/upload')
def index():
    if "user" in session:
        user = session["user"]
        app.config['UPLOAD_PATH'] = f'uploads/{user}'
        files = os.listdir(app.config['UPLOAD_PATH'])
        return render_template('index.html', files=files)
    else:
        flash("You are not logged in!",category='danger')
        return redirect(url_for("login"))

@app.route('/upload', methods=['POST'])
def upload_files():
    user = session["user"]
    app.config['UPLOAD_PATH'] = f'uploads/{user}'
    uploaded_file = request.files['file']
    filename = secure_filename(uploaded_file.filename)
    uploaded_file.save(os.path.join(app.config['UPLOAD_PATH'], filename))
    return '', 204

@app.route('/uploads/<filename>')
def upload(filename):
    if "user" in session:
        user = session["user"]
        app.config['UPLOAD_PATH'] = f'uploads/{user}'
        return send_from_directory(app.config['UPLOAD_PATH'], filename)
    else:
        flash("You are not logged in!",category='danger')
        return redirect(url_for("login"))

@app.route('/uploads/delete/<filename>')
def deletefile(filename):
    if "user" in session:
        user = session["user"]
        found_user = users.query.filter_by(name=user).first()
        if found_user:
            myfile = f"./uploads/{user}/{filename}"
            deleteFile(myfile)
            return redirect('/viewuploads')
        else:
            flash("Only the author can delete the post",category='danger')
            return redirect('/viewuploads')
    else:
        flash("You are not logged in!",category='danger')
        return redirect(url_for("login"))


@app.route('/viewuploads', methods=['GET'])
def dirtree():
    if "user" in session:
        path = f"uploads/{session['user']}"
        return render_template('dirtree.html', tree=make_tree(path))
    else:
        flash("You are not logged in!",category='danger')
        return redirect(url_for("login"))


def make_tree(path):
    tree = dict(name=os.path.basename(path), children=[])
    try: lst = os.listdir(path)
    except OSError:
        pass
    else:
        for name in lst:
            tree['children'].append(dict(name=name))
    return tree   

if __name__ == '__main__':
    db.create_all()
    app.run(host='0.0.0.0', debug=True, port=8000)