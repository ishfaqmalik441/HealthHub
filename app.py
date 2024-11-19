from flask import Flask, url_for, render_template, request, redirect, flash
import pandas as pd
import json
from hashlib import sha256

app = Flask(__name__)
#app.secret_key = "9773e89f69e69285cf11c10cbc44a37945f6abbc5d78d5e20c2b1b0f12d75ab7"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/list')
def list():
    items = [{'title': 'T1', 'author': "John Smith", 'created': '5 hours ago'}, 
             {'title': 'T2', 'author': "Mike Smith", 'created': 'a day ago'},
             {'title': 'T3', 'author': "Ishfaq Malik", 'created': '2 days ago'}]
    # Have to use the items argument as a list of dictionaries
    return render_template('list.html', items=items)

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         # the `name` attribute of your input tags
#         username = request.form['username']
#         password = request.form['password']
       
#         if username == 'is3240' and password == 'is3240':
#             return redirect(url_for('hello', name=username))
#         else:
#             return render_template('login.html')
#             #return redirect(url_for('index'))
    
#     return render_template('login.html')

@app.route('/user/<name>')
def hello(name):
    users_predictions = json.load(open('./static/users/user_predict.json', 'r'))
    user_prediction = users_predictions[name]
    return render_template('hello.html', stocks = user_prediction, name = name)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        print(request.files)
        #df = pd.read_csv(request.files.get('datainput'))
        fname = request.files['datainput']
        data = pd.read_csv(fname)
        data.to_csv('./static/uploads/%s'%fname, index=False)
        summ = data.mean(numeric_only=True).to_frame()
        return render_template('upload.html', table=summ.to_html(classes='data'))
    return render_template('upload.html')


@app.route('/about')
def about():
    return render_template('about.html')

# Uncomment the following for a more sophisicated
# design of the login function

@app.route('/login', methods=['GET', 'POST'])
def login():
    user_cred = json.load(open('./static/users/credentials.json', 'r'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # obtain the hash
        password = sha256(password.encode('utf-8')).hexdigest()
        
        if username not in user_cred:
            return render_template('login.html')
        elif password != user_cred[username]:
            return render_template('login.html')
        else:
            return redirect(url_for('hello', name=username))
    return render_template('login.html')