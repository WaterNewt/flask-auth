import os
import json
import utils
from typing import Final
from dotenv import load_dotenv
from flask import Flask, render_template, request, session, redirect, url_for

load_dotenv('.env')
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
DB_USER_FILE: Final[str] = 'databases/users.json'
DB_TASKS_FILE: Final[str] = 'databases/tasks.json'

def write_db(db, db_file=DB_USER_FILE, **kwargs) -> None:json.dump(db, open(db_file, 'w'), indent=4, **kwargs)
def generate_session(username:str):return utils.md5_hash(utils.generate_key(username))
def has_session():return 'session' in session
def get_logged_user() -> bool|dict:
    logged_user = None
    with open(DB_USER_FILE, 'r') as f:
        users = json.load(f)
    if has_session():
        for i in users:
            if i['log']['session']==session['session']:
                logged_user = i
                return logged_user
    return False
def verify_user(form) -> bool:
    with open(DB_USER_FILE, 'r') as f:
        users = json.load(f)
    for i in users:
        if i['username']==form['username'] and i['password']==utils.md5_hash(form['password']):
            return True
    return False
def regenerate_session(username:str) -> bool|str:
    try:
        with open(DB_USER_FILE, 'r') as f:
            users = json.load(f)
        for index,user in enumerate(users):
            if user['username']==username:
                new_session = generate_session(username)
                users[index]['log']['session'] = new_session
                write_db(users)
                return new_session
        return False
    except:
        return False
def log_status(status:False, ip:str, username:str) -> bool:
    with open(DB_USER_FILE, 'r') as f:
        users = json.load(f)
    for index,user in enumerate(users):
        if user['username']==username:
            users[index]['log']['logged'] = status
            if status is False:
                users[index]['log']['session'] = None
                users[index]['log']['ip'] = None
            else:
                users[index]['log']['ip'] = ip
            write_db(users)
            return True
    return False
def new_user(form) -> bool:
    with open(DB_USER_FILE, 'r') as f:
        users:list = json.load(f)
    usernames = [i['username'] for i in users]
    if form.get('username') in usernames:
        return False
    else:
        new_id = users[-1]['id']+1
        user = {'username': form.get('username'), 'password': utils.md5_hash(form.get('password')), 'email': form.get('email'), 'api_key': None, 'log': {'logged': False, 'ip': None, 'session': None}, "id": int(new_id)}
        users.append(user)
        write_db(users)
        return True
def restore_password(password, username) -> bool:
    with open(DB_USER_FILE, 'r') as f:
        users:list = json.load(f)
    for index,user in enumerate(users):
        if user['username']==username:
            users[index]['password'] = utils.md5_hash(password)
            write_db(users)
            return True
    return False
def new_task(form, logged_user) -> bool:
    if logged_user:
        with open(DB_TASKS_FILE, 'r') as f:
            tasks:list = json.load(f)
        my_tasks = []
        for i in tasks:
            if i['owner_id']==logged_user['id']:
                my_tasks.append(i)
        my_labels = [i['label'] for i in my_tasks]
        if form.get('label') in my_labels:
            return False
        new_id = tasks[-1]['id']+1
        task = {'label': form.get('label'), 'description': form.get('description'), 'due_date': form.get('due_date'), 'owner_id': logged_user['id'], 'id': new_id}
        tasks.append(task)
        write_db(tasks, DB_TASKS_FILE)
        return True
    else:
        return False
def get_tasks(logged_user) -> list:
    with open(DB_TASKS_FILE, 'r') as f:
        tasks:list = json.load(f)
    my_tasks = []
    for i in tasks:
        if i['owner_id'] == logged_user['id']:
            my_tasks.append(i)
    return my_tasks
def find_task(id:int, logged_user) -> dict|None:
    with open(DB_TASKS_FILE, 'r') as f:
        tasks:list = json.load(f)
    for i in tasks:
        if i['id'] == id and i['owner_id'] == logged_user['id']:
            return i
    return None
def toggle_completion(id:int, logged_user) -> bool:
    with open(DB_TASKS_FILE, 'r') as f:
        tasks:list = json.load(f)
    for index,task in enumerate(tasks):
        if task['owner_id'] == logged_user['id'] and task['id'] == id:
            if task['completed'] is True:
                tasks[index]['completed'] = False
            else:
                tasks[index]['completed'] = True
            write_db(tasks, DB_TASKS_FILE)
            return True
    return False

@app.route('/')
def index():
    logged_user = get_logged_user()
    if logged_user:
        return render_template('index.html', user=logged_user)
    else:
        return redirect(url_for('login'))
    
@app.route("/login", methods=['POST', 'GET'])
def login():
    logged_user = get_logged_user()
    if logged_user:
        return redirect(url_for('index'))
    else:
        if request.method == 'GET':
            return render_template('login.html')
        elif request.method == 'POST':
            if verify_user(request.form):
                log_status(True, request.remote_addr, request.form.get('username'))
                new_session = regenerate_session(request.form.get('username'))
                if isinstance(new_session, str):
                    session['session'] = new_session
                else:
                    print(new_session)
                    return "Error while generating session"
                return redirect(url_for('index'))
            else:
                return render_template('login.html', error="Incorrect credentials.")
            
@app.route("/register", methods=['POST', 'GET'])
def register():
    logged_user = get_logged_user()
    if logged_user:
        return redirect(url_for('index'))
    else:
        if request.method == 'GET':
            return render_template('register.html')
        elif request.method == 'POST':
            created_user = new_user(request.form)
            if created_user is False:
                return render_template('register.html', error='Username is already in use.')
            elif created_user is True:
                log_status(True, request.remote_addr, request.form.get('username'))
                new_session = regenerate_session(request.form.get('username'))
                session['session'] = new_session
                return redirect(url_for('index'))
            
@app.route("/newtask", methods=['POST', 'GET'])
def newtask():
    if request.method == 'GET':
        return redirect(url_for('index'))
    elif request.method == 'POST':
        logged_user = get_logged_user()
        if logged_user:
            if new_task(request.form, logged_user) is False:
                return render_template('index.html', user=logged_user, error="A task with that label already exists")
        else:
            return redirect(url_for('login'))
        return render_template('index.html', user=logged_user, success="Successfully created a new task.")

@app.route("/mytasks", methods=['GET'])
def mytasks():
    if request.method == 'GET':
        logged_user = get_logged_user()
        if logged_user:
            my_tasks = get_tasks(logged_user)
            if 'id' in request.args:
                task = find_task(int(request.args.get('id')), logged_user)
                if task is not None:
                    return render_template('tasks.html', task=task)
                else:
                    return render_template('tasks.html', error=f'Could not find task with id {request.args.get("id")}', tasks=my_tasks, empty=len(my_tasks)==0)
            else:
                return render_template('tasks.html', tasks=my_tasks, empty=len(my_tasks)==0)
        else:
            return redirect(url_for('login'))
        
@app.route('/togglecompletion', methods=['GET'])
def completetask():
    if request.method == 'GET':
        logged_user = get_logged_user()
        if logged_user:
            if 'id' in request.args:
                toggle_completion(int(request.args.get('id')), logged_user)
                return redirect(f'/mytasks?id={request.args.get("id")}')
            else:
                return redirect(url_for('index'))
        else:
            return redirect(url_for('login'))

@app.route("/resetpass", methods=['POST', 'GET'])
def resetpass():
    if request.method == 'GET':
        return redirect(url_for('index'))
    elif request.method == 'POST':
        logged_user = get_logged_user()
        if logged_user:
            old_pass = request.form.get('old')
            new_pass = request.form.get('new')
            form = {'username': logged_user['username'], 'password': old_pass}
            if verify_user(form):
                restore_password(new_pass, logged_user['username'])
                return redirect(url_for('index'))
            else:
                return render_template('index.html', user=logged_user)
        else:
            return redirect(url_for('login'))

@app.route("/logout", methods=['GET'])
def logout() -> bool:
    logged_user = get_logged_user()
    if logged_user:
        log_status(False, None, logged_user['username'])
        session.pop('session')
        return redirect(url_for('login'))
    return redirect(url_for('login'))
    
    
if __name__ == '__main__':
    app.run(port=8080, debug=True)