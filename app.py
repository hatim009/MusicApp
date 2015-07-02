import re
import os
import sqlite3
from flask import Flask, send_from_directory, flash, request, abort
from flask import render_template, redirect, session, url_for, json, g
from werkzeug import secure_filename, generate_password_hash, check_password_hash
from operator import itemgetter
from contextlib import closing

# configuration

app = Flask(__name__)
app.config.from_object(__name__)

app.config['DATABASE'] = os.path.join(app.root_path, 'app.db')
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = "I don't know what to keep my secret key"
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads/')
app.config['ALLOWED_EXTENSIONS'] = ['mp3', 'ogg', 'wav', 'aac']


def connect_db():
    return sqlite3.connect(app.config['DATABASE'])


def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

# @app.cli.command('initdb')
# def initdb_command():
#     init_db()
#     print('Initialised the database.')


@app.before_request
def before_request():
    g.db = connect_db()


def get_db():
    if not hasattr(g, 'db'):
        g.db = connect_db()
    return g.db


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'db'):
        g.db.close()


@app.route('/')
@app.route('/login')
def login():
    if 'user' in session:
        return redirect(url_for('home'))
    return render_template('login.html')


@app.route('/logout', methods=['POST', 'GET'])
def logout():
    session.pop('userId', None)
    session.pop('user', None)
    if request.method == 'POST':
        return '{"status":"success", "message":"/login"}'
    else:
        return redirect(url_for('login'))


status = ''


@app.route('/home')
def home():
    global status
    if 'user' in session:
        temp = status
        status = ''
        return render_template('home.html', name=session['user'], status=temp)
    else:
        return redirect(url_for('login'))


@app.route("/AuthenticateLogIn", methods=['POST'])
def AuthenticateLogIn():
    try:
        email = request.form['email']
        password = request.form['password']
        if email == '':
            return json.dumps({'status': 'failure', 'message': 'Email field is empty'})
        if password == '':
            return json.dumps({'status': 'failure', 'message': 'Password field is empty'})

        db = get_db()
        cursor = db.execute(
            "SELECT * FROM Users WHERE userEmail = '%s'" % (email))
        data = cursor.fetchone()

        if data is not None:
            if check_password_hash(data[3], password):
                session['userId'] = data[0]
                session['user'] = data[1]
                # return redirect('/home')
                return '{"status":"success", "message":"/home"}'
            else:
                return '{"status": "failure", "message": "Incorrect Password"}'
        else:
            return '{"status": "failure", "message": "User doesnot exists"}'
    except Exception as e:
        flash(str(e))
        return json.dumps({'status': 'failure', 'message': str(e)})


class validateUser:

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = password
        self.response = {'status': 'success', 'message': ''}
        self.validate()

    def valid_name(self):
        if (not re.match("^[a-zA-Z][a-zA-Z\\s]+$", self.name)) or len(self.name) > 50:
            self.response['status'] = 'failure'
            self.response['message'] = 'Please enter a valid name.'
            return False
        return True

    def valid_email(self):

        if not re.match("^([a-z0-9_\.-]+)@([\da-z\.-]+)\.([a-z\.]{2,6})$", self.email):
            self.response['status'] = 'failure'
            self.response['message'] = 'Please enter a valid email'
            return False

        db = get_db()
        cursor = db.execute(
            "SELECT * FROM Users WHERE userEmail = '%s'" % (self.email))
        data = cursor.fetchone()

        if data is not None:
            self.response['status'] = 'failure'
            self.response['message'] = 'User already exists with this email'
            return False
        return True

    def valid_password(self):

        if len(self.password) < 8 or len(self.password) > 16:
            self.response['status'] = 'failure'
            self.response[
                'message'] = 'Password length must be between 8 to 16'
            return False
        return True

    def validate(self):
        if self.name == '':
            self.response['status'] = 'failure'
            self.response['message'] = 'Name field is empty'
            return
        if self.email == '':
            self.response['status'] = 'failure'
            self.response['message'] = 'Email field is empty'
            return
        if self.password == '':
            self.response['status'] = 'failure'
            self.response['message'] = 'Password field is empty'
            return

        if not self.valid_name():
            return
        if not self.valid_email():
            return
        if not self.valid_password():
            return
        return

    def get_response(self):
        return self.response


@app.route('/AuthenticateSignUp', methods=['POST'])
def AuthenticateSignUp():

    try:
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        password_hash = generate_password_hash(password)

        User = validateUser(name, email, password)
        response = User.get_response()

        if response['status'] == 'failure':
            return json.dumps(response)

        db = get_db()
        db.execute("INSERT INTO Users (userName,userEmail,userPassword) VALUES ('%s', '%s' ,'%s')" % (
                   name, email, password_hash))
        db.commit()

        cursor = db.execute(
            "SELECT * FROM Users WHERE userEmail = '%s'" % (email))
        data = cursor.fetchone()

        db.execute(
            "CREATE TABLE voteTable%s ( voteId integer PRIMARY KEY AUTOINCREMENT, songId int null, vote int null)" % (data[0]))
        db.commit()

        session['userId'] = data[0]
        session['user'] = data[1]

        # return redirect('/home')
        response['message'] = '/home'
        return json.dumps(response)

    except Exception as e:
        return json.dumps({'status': 'failure', 'message': str(e)})


def allowed_file(filename):
    if '.' in filename:
        if filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']:
            return True
    return False


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    global status
    status = ''
    if 'user' not in session:
        return redirect(url_for('login'))

    file = request.files['file']
    print file.filename
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        print filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        db = get_db()
        db.execute(
            "INSERT INTO Songs (songName,userId,dateAdded) VALUES('%s', '%s', datetime())" % (filename, session['userId']))
        db.commit()

        status = 'uploaded'
        return redirect(url_for('home'))


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/songsList', methods=['POST'])
def songsList():

    if 'user' not in session:
        redirect(url_for('login'))

    db = get_db()
    cursor = db.execute(
        "SELECT songId, songName, upvotes, downvotes FROM Songs ORDER BY (upvotes-downvotes) DESC")
    data = cursor.fetchall()

    L = []

    for i in range(len(data)):
        l1 = []
        for j in range(len(data[i])):
            l1.append(data[i][j])
        l1.append(data[i][2] - data[i][3])
        L.append(l1)

    return json.dumps(L)


@app.route('/vote', methods=['POST'])
def vote():
    if 'user' not in session:
        redirect(url_for('login'))

    songId = request.form['songId']
    vote = request.form['vote']
    userId = session['userId']

    # print "******* vote = '%s' , songId = '%s' ***********\n" % (vote,
    # songId)
    user_vote_table = 'voteTable' + str(userId)

    response = {}
    response['status'] = 'success'

    db = get_db()
    cursor = db.execute("SELECT * FROM %s WHERE songId = '%s'" %
                        (user_vote_table, songId))
    data = cursor.fetchone()

    if data is not None:
        response['status'] = 'failure'
        if data[2] == 1:
            response['message'] = 'You have already upvoted this song'
        else:
            response['message'] = 'You have already downvoted this song'
        return json.dumps(response)

    db.execute("INSERT INTO '%s' (songId,vote) VALUES ('%s', '%s')" %
               (user_vote_table, songId, vote))
    db.commit()

    if vote == '1':
        db.execute(
            "UPDATE Songs SET upvotes = upvotes + 1 WHERE songId = '%s'" % (songId))
    else:
        db.execute(
            "UPDATE Songs SET downvotes = downvotes + 1 WHERE songId = '%s'" % (songId))
    db.commit()

    response['message'] = '/home'
    return json.dumps(response)


def getSong(count):
    db = get_db()
    cursor = db.execute(
        "SELECT songName FROM Songs ORDER BY (upvotes - downvotes) DESC LIMIT 1 OFFSET '%s'" % (count))
    data = cursor.fetchone()

    return data


@app.route('/playSongs', methods=['POST'])
def playSongs():
    if 'user' not in session:
        return redirect(url_for('login'))
    src = getSong(0)
    if src is None:
        flash('No song to play')
        return render_template('play.html', name=session['user'], _source='')
    return render_template('play.html', name=session['user'], _source=src[0])


@app.route('/getNextSong', methods=['POST'])
def getNextSong():
    if 'user' not in session:
        return redirect(url_for('/login'))

    count = request.form['count']

    db = get_db()
    cursor = db.execute("SELECT COUNT(*) FROM Songs")
    data = cursor.fetchall()

    # print data[0][0]
    count = str(int(count) % int(data[0][0]))

    src = getSong(count)

    return json.dumps(src)


app.debug = True
if __name__ == "__main__":
    app.run()
