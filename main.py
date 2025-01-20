from flask import Flask, redirect, url_for, render_template, request, session
import os
import datetime
import json
import fcntl
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'U1sNMeUkZSuuX2Zn'

BASE_DIR = os.path.dirname(__file__)
SAVE_FILE = os.path.join(BASE_DIR, 'data/log.json')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

USERLIST = {
    'taro': 'aaa',
    'jiro': 'bbb',
    'sabu': 'ccc',
}

def load_data():
    if not os.path.exists(SAVE_FILE):
        return []
    with open(SAVE_FILE, 'r', encoding='utf-8') as f:
        fcntl.flock(f, fcntl.LOCK_SH)
        data = json.load(f)
        fcntl.flock(f, fcntl.LOCK_UN)
        return data

def save_data(data_list):
    with open(SAVE_FILE, 'w', encoding='utf-8') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        json.dump(data_list, f, ensure_ascii=False)
        fcntl.flock(f, fcntl.LOCK_UN)

def save_data_append(user, text, anonymous=False, image_filename=None):
    tm = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
    user = "匿名" if anonymous else user
    data_list = load_data()
    data = {'name': user, 'text': text, 'date': tm}
    if image_filename:
        data['image'] = f'/static/uploads/{image_filename}'
    data_list.insert(0, data)
    save_data(data_list)

def is_login():
    return 'login' in session

def get_user():
    return session.get('login', 'not login')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/try_login', methods=['POST'])
def try_login():
    user = request.form.get('user', '')
    pw = request.form.get('pw', '')
    if user in USERLIST and USERLIST[user] == pw:
        session['login'] = user
        return redirect('/')
    return show_msg('ログインに失敗しました')

@app.route('/logout')
def logout():
    session.pop('login', None)
    return show_msg('ログアウトしました')

@app.route('/')
def index():
    if not is_login():
        return redirect('/login')
    return render_template('index.html', user=get_user(), data=load_data())

@app.route('/write', methods=['POST'])
def write():
    if not is_login():
        return redirect('/login')

    ta = request.form.get('ta', '').strip()
    anonymous = 'anonymous' in request.form
    image = request.files.get('image')

    image_filename = None
    if image and allowed_file(image.filename):
        image_filename = secure_filename(image.filename)
        image.save(os.path.join(UPLOAD_FOLDER, image_filename))

    if not ta:
        return show_msg('書込が空でした。')

    save_data_append(user=get_user(), text=ta, anonymous=anonymous, image_filename=image_filename)
    return redirect('/')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/try_register', methods=['POST'])
def try_register():
    user = request.form.get('user', '')
    pw = request.form.get('pw', '')
    if user in USERLIST:
        return show_msg('ユーザー名はすでに使用されています')

    USERLIST[user] = pw
    return show_msg('登録が完了しました。ログインしてください')

def show_msg(msg):
    return render_template('msg.html', msg=msg)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')