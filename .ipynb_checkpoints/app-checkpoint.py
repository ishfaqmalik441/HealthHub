from flask import Flask, url_for, render_template, request, redirect, session, flash
import pandas as pd
import numpy as np
import json, flask_login, datetime, requests, base64
from hashlib import sha256
from models import *
from io import BytesIO
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg

app = Flask(__name__)
app.secret_key = "9773e89f69e69285cf11c10cbc44a37945f6abbc5d78d5e20c2b1b0f12d75ab7" # we need to change it

# Login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

# data files
global USER_CREDENTIALS, USER_PREDICTIONS
USER_CREDENTIALS = './static/users/users.json'
USER_PREDICTIONS = './static/users/user_predict.json'

# API URL
TODAY = datetime.date.today()
ONEYEARAGO = TODAY - datetime.timedelta(days=365)
URL_BASE = "https://api.polygon.io/v2/aggs/ticker/MYTICKER/range/1/day/%s/%s"%(ONEYEARAGO, TODAY)

#it must be here for maintain user session after logged in
@login_manager.user_loader
def load_user(userid):
    user_json = pd.read_json(USER_CREDENTIALS).get(userid)
    return User(user_json['username'],
                user_json['email'],
                user_json['password'])

@app.get('/')
def index():
    return render_template('index.html')

@app.post('/')
def search():
    if 'clear' in request.form:
        return redirect(url_for('index')) 
        #for user to clean the search result, will only shown after a successful search, and it will redirect us to the page again
    elif 'search' in request.form: 
        #start to seach the data the user wants
        ticker = request.form.get('ticker')
        apikey = request.form.get('apikey')
        url = URL_BASE.replace('MYTICKER', ticker)
        r = requests.get(url, params={'apiKey': apikey})
        print(r.url)
        r_status = r.status_code
        print(r_status)
        # if search failed:
        if r_status != 200:
            return render_template('index.html', msg='failed') 
            #will return failed msg to browser, {% if mag == 'failed' %}
            
        #if status == 200, extract the data
        results = r.json()
        results_price = results['results']
        results_df = pd.DataFrame(results_price)
        col_map = {'c': 'Closing Price', 'h': 'Highest Price', 'l': 'Lowest Price',
                   'n': 'Num Trans', 'o': 'Openning Price', 'otc': 'OTC Stock', 't': 'Unix Time',
                   'v': 'Volume', 'vw': 'Volume Weighted Price'
                  }
        results_df.rename(columns=col_map, inplace=True)
        # add datetime based on unix time
        print(results_df.head())
        results_df['Date'] = pd.to_datetime(results_df['Unix Time'], unit='ms').dt.date
        # save for now
        results_df.to_csv('./static/uploads/%s.csv'%ticker, index=False)
        # visualization

        fig = Figure(figsize=[12, 5.5])
        ax_arr = fig.subplots(ncols=2)
        for i, col in enumerate(['Closing Price', 'Num Trans']):
            ax = ax_arr[i]
            ax.scatter(x=results_df['Date'], y=results_df[col])
            ax.set_xlabel('Date')
            ax.set_ylabel(col)
        fig.tight_layout()

        # Convert plot to PNG image
        buf = BytesIO()
        FigureCanvasAgg(fig).print_png(buf)
         # Encode PNG image to base64 string
        buf_str = "data:image/png;base64,"
        buf_str += base64.b64encode(buf.getvalue()).decode('utf8')

        return render_template('index.html', msg='success', imgsrc=buf_str)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password_hash = sha256(password.encode('utf-8')).hexdigest()

        # check if the user already exists
        # for simplicity, we use a JSON to keep track of all registered users for now
        #user_existing = pd.read_json(USER_CREDENTIALS).T
        user_existing = pd.read_json(USER_CREDENTIALS).T 
        #xxx.t --> is to exchange col and row
        
        existing_usernames = user_existing['username'].values
        # if exists, refresh this page with an error message
        #if username in user_existing['username']:
        if username in existing_usernames:
            # x in existing_usernames(['x', 'y', 'z']) --> true, x is inside
            return render_template('signup.html', msg='username')
        # if not, go ahead and put it to the JSON (append)
        user_series = pd.Series(dict(username=username, password=password_hash, email=email))
        user_existing.loc[sha256(username.encode('utf-8')).hexdigest()] = user_series
        user_existing.to_json(USER_CREDENTIALS, orient='index')
        return redirect(url_for('login', msg='signup'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # when clikcing the login button:
    if request.method == 'POST' and 'login' in request.form:
        username = request.form['username']
        password = request.form['password']
        # obtain the hash
        userid = sha256(username.encode('utf-8')).hexdigest()
        password_hash = sha256(password.encode('utf-8')).hexdigest()

        # load the user as an User object
        user_json = pd.read_json(USER_CREDENTIALS).get(userid)
        user = User(user_json['username'], user_json['email'], user_json['password'])

        # if user does not exist or if password does not match
        if user is None or password_hash != user.password:
            return render_template('login.html', msg="mismatch")
        # else, login success; redirect to user page
        else:
            flask_login.login_user(user)
            flash("You're logged in!")
            #return redirect(url_for('user', name=user.username))
            return redirect(url_for('index'))
    # when clikcing the signup button
    elif request.method == 'POST' and 'signup' in request.form:
        return redirect(url_for('signup'))
    return render_template('login.html', msg=request.args.get('msg'))

@app.get('/user/<name>')
@flask_login.login_required
def user(name):
    return render_template('user_profile.html', edit='No', editPWD='No',
                           name=flask_login.current_user.username)

@app.post('/user/<name>')
@flask_login.login_required
def user_edit(name):
    user = flask_login.current_user
    if 'editEmail' in request.form:
        return render_template('user_profile.html', edit="Yes", editPWD='No',
                               name=user.username)
    elif 'editPWD' in request.form:
        return render_template('user_profile.html', editPWD="Yes", edit='No',
                               name=user.username)
    else:
        user_json = pd.read_json(USER_CREDENTIALS)
        # email
        try:
            new_email = request.form['email']
            user_json.loc['email', user.id] = new_email
        except:
            pass
            
        # pwd
        try:
            new_password = request.form['password']
            new_password = sha256(new_password.encode('utf-8')).hexdigest()
            user_json.loc['password', user.id] = new_password
            # .loc[x, y] --> specifies the rows and the columns to access
        except:
            pass
        
        user_json.to_json(USER_CREDENTIALS) #.to_json --> convert a pandas DataFrame or Series into JSON format
        user = User(*user_json[user.id].values)
        #user_json[user.id].values --> get the value stored in dictionary  
        return redirect(url_for('user', name=user.username)) #linked to @app.get('/user/<name>')

'''
@app.post('/user/<name>')
@flask_login.login_required
def user_edit_pwd(name):
    if 'editPWD' in request.form:
        return render_template('user_profile.html', edit="No", editPWD="Yes",
                               name=user.username)
    else:
        new_password = request.form['password']
        new_password = sha256(new_password.encode('utf-8')).hexdigest()
        user_json = pd.read_json(USER_CREDENTIALS)
        user_json.loc['password', user.id] = new_password
        user_json.to_json(USER_CREDENTIALS)
        user = User(*user_json[user.id].values)
        return redirect(url_for('user', name=user.username))
'''

@app.get('/predictions/<name>')
@flask_login.login_required
def user_predictions(name):
    user = flask_login.current_user
    try:
        d_usr = json.load(open(USER_PREDICTIONS, 'r')).get(user.username)
        # add integer index
        for i in range(len(d_usr)):
            d_usr[i]['index'] = i + 1
        return render_template('user_page.html', name=user.username, items=d_usr)
    except:
        return render_template('user_page.html', name=user.username)

@app.post('/predictions/<name>') #it repecent where the user located in the webpage --> /'location/<user name>'
@flask_login.login_required
def modify_predictions(name):
    user = flask_login.current_user
    print(request.form.keys())
    d_all = json.load(open(USER_PREDICTIONS, 'r'))
    if 'add' in request.form:
        ticker = request.form['ticker']
        prediction = request.form['prediction']
        if len(ticker) < 1 or len(prediction) < 2 :
            
            # to ensure the inputs are valid, two input are strings, if meet will add, otherwise will redirect to page, and do nothing
            
            return redirect(url_for('user_predictions', name=user.username))
        d_all[user.username].append(dict(ticker=ticker, prediction=prediction))
    else:
        # which row to delete
        del_row = int(list(request.form.keys())[0].replace('Del', ''))
        # minus 1 because python starts counting by 1
        d_all[user.username].pop(del_row-1)
    with open(USER_PREDICTIONS, 'w') as f:
        json.dump(fp=f, obj=d_all)
    return redirect(url_for('user_predictions', name=user.username))

@app.route("/logout")
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return redirect(url_for('index'))

@app.route('/about')
def about():
    return render_template('about.html')
