from flask import Flask, url_for, render_template, request, redirect, session, flash
import pandas as pd
import numpy as np
import json, flask_login, datetime, requests, base64
from datetime import timedelta
from hashlib import sha256
from models import *
from io import BytesIO
import os
from matplotlib.figure import Figure
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.backends.backend_agg import FigureCanvasAgg
import matplotlib.pyplot as plt

app = Flask(__name__)
app.secret_key = "9773e89f69e69285cf11c10cbc44a37945f6abbc5d78d5e20c2b1b0f12d75ab7" # we need to change it

# Make the uploads folder
upload_folder = 'uploads'
os.makedirs(upload_folder, exist_ok=True)
app.config['upload_folder'] = upload_folder

# Login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

# data files
global USER_CREDENTIALS, USER_PREDICTIONS
USER_CREDENTIALS = 'static/users/credentials.json'
USER_PREDICTIONS = 'static/users/user_predict.json'

# API URL
TODAY = datetime.date.today()
ONEYEARAGO = TODAY - datetime.timedelta(days=365)
URL_BASE = "https://api.polygon.io/v2/aggs/ticker/MYTICKER/range/1/day/%s/%s"%(ONEYEARAGO, TODAY)

#it must be here for maintain user session after logged in
@login_manager.user_loader
def load_user(userid):
    user_json = pd.read_json(USER_CREDENTIALS).get(userid)
    return User(user_json['username'],
                user_json['password'])

@app.get('/')
def index():
    msg = request.args.get('msg')
    return render_template('index.html', msg=msg)

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
        user_series = pd.Series(dict(username=username, password=password_hash))
        user_existing.loc[sha256(username.encode('utf-8')).hexdigest()] = user_series
        user_existing.to_json(USER_CREDENTIALS, orient='index')
        return redirect(url_for('login', msg='signup'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and 'login' in request.form:
        # Get form data
        username = request.form.get('username')  # Use .get() to avoid KeyErrors
        password = request.form.get('password')

        # Hash username and password
        userid = sha256(username.encode('utf-8')).hexdigest()
        password_hash = sha256(password.encode('utf-8')).hexdigest()

        # Load users.json
        with open(USER_CREDENTIALS, 'r') as file:
            users = json.load(file)  # Load JSON data as a dictionary

        # Check if user exists
        user_json = users.get(userid)
        if user_json is None:  # If user does not exist
            return render_template('login.html', msg="notexist")

        # Check if password matches
        if user_json['password'] != password_hash:
            return render_template('login.html', msg="mismatch")

        # Login the user
        user = User(user_json['username'], user_json['password'])
        flask_login.login_user(user)
        return redirect(url_for('dashboard', msg="logged in", name = flask_login.current_user.username))

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
    msg = None  # Default message

    if 'editPWD' in request.form:
        return render_template('user_profile.html', editPWD="Yes", name=user.username, msg=msg)
    elif "delAC" in request.form:
        user_json = pd.read_json(USER_CREDENTIALS)
        user_json.drop(user.id, axis=1, inplace=True)
        user_json.to_json(USER_CREDENTIALS)
        flask_login.logout_user()  # Log the user out
        msg="deleted"
        return redirect(url_for('index', msg=msg))
    else:
        user_json = pd.read_json(USER_CREDENTIALS)
        # Password update
        try:
            new_password = request.form['password']
            new_password = sha256(new_password.encode('utf-8')).hexdigest()
            user_json.loc['password', user.id] = new_password
            msg = "Password updated successfully!"
        except:
            pass

        user_json.to_json(USER_CREDENTIALS)
        return render_template('user_profile.html', editPWD="No", name=user.username, msg=msg)

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

@app.get('/dashboard/<name>')
@flask_login.login_required
def dashboard(name):
    message = request.args.get('msg', default="Welcome!")  # Default message if not provided
    return render_template('dashboard.html', msg = message, name = name)

@app.get('/test')
def test():
    return render_template('test.html')


# Function to save the uploaded file and possibly for data processing
@app.post('/upload/<name>')
def upload_file(name):
    file = request.files['file']

    if file.filename == '':
        return redirect(url_for('dashboard', msg = 'No File Uploaded', name = name))
    if file:
        if file.filename.endswith('.csv'):
            data = pd.read_csv(file)
        elif file.filename.endswith('.xls') or file.filename.endswith('.xlsx'):
            data = pd.read_excel(file)
        else:
            return redirect(url_for('dashboard', msg = 'File Type not supported', name = name))
        with pd.ExcelWriter("static/user_workout_DB/Users.xlsx", mode='a', if_sheet_exists='replace') as writer:
            data.to_excel(writer, sheet_name=f"workout_data_{name}", index=False)
        # data.to_excel('static/user_workout_DB/Users.xlsx', sheet_name = "workout_data_%s"%name, index = False)
        return redirect(url_for('dashboard', msg = 'File Uploaded', name = name))

# Function for calculating the user BMI
def calculate_bmi(weight, height_cm):
    height_m = height_cm / 100  # Convert height to meters
    return round(weight / (height_m ** 2), 1)  # Calculate BMI and round to 2 decimal places

def create_custom_cmap():
    return LinearSegmentedColormap.from_list("", ["#3498db", "#f1c40f", "#e74c3c"])

# Function for analysing and processing the user data, and providing a visualization of the User's BMI
@app.get("/dashboard/bmi/<name>")
@flask_login.login_required
def bmi(name):
    bmi_stats_dict = {}
    user = flask_login.current_user
    user_data = pd.read_excel('static/user_workout_DB/Users.xlsx', sheet_name = ['workout_data_%s'%user.username])
    user_data = user_data['workout_data_%s'%user.username]   
    user_data['height'] = user_data['height'][0]

    user_data['Date'] = user_data['Date'].dt.date
    user_data['BMI'] = calculate_bmi(user_data['weight_record'], user_data['height'])
    healthy_bmi_max = 24.9
    healthy_bmi_min = 18.5
    count = user_data['BMI'].count()

    bmi_stats_dict['DayCount'] = count
    highestbmiIndex = user_data['BMI'].idxmax()
    bmi_stats_dict['highestbmi'] = {'date': user_data.loc[highestbmiIndex]['Date'], 'value': user_data['BMI'].max()}
    healthyDays = 0
    for bmi in user_data['BMI']:
        if bmi > 18.5 and bmi < 25:
            healthyDays = healthyDays + 1
    bmi_stats_dict['healthyDays'] = healthyDays
    lowestbmiIndex = user_data['BMI'].idxmin()
    bmi_stats_dict['lowestbmi'] = {'date': user_data.loc[lowestbmiIndex]['Date'], 'value': user_data['BMI'].min()}
    bmi_stats_dict['avgbmi'] = round(user_data['BMI'].mean(), 2)
    bmi_stats_dict['stdbmi'] = round(user_data['BMI'].std(), 2)

    fig = Figure(figsize=[11, 6])
    ax_arr = fig.subplots(ncols=1)
    ax = ax_arr

    # Plot BMI data
    ax.plot(user_data['Date'], user_data['BMI'], label="BMI (Line)", color='#3498db', linestyle='-', linewidth=2, alpha=0.7)
    ax.scatter(user_data['Date'], user_data['BMI'], label="BMI (Scatter)", color='#f1c40f', s=80, edgecolor='white', zorder=100)

    # Add healthy BMI range
    ax.axhspan(healthy_bmi_min, healthy_bmi_max, color='#2ecc71', label='Healthy BMI Range (18.5 - 24.9)', alpha=0.2)

    # Set y-axis limits
    bmi_min = max(0, user_data['BMI'].min() - 1)
    bmi_max = user_data['BMI'].max() + 1
    ax.set_ylim(bmi_min, bmi_max)

    # Customize plot appearance
    ax.set_xlabel("Date", fontsize=14, fontweight='bold')
    ax.set_ylabel("BMI", fontsize=14, fontweight='bold')
    ax.set_title(f'BMI throughout the {count} days', fontsize=18, fontweight='bold')

    # Customize legend
    ax.legend(loc='upper right', fontsize=12, framealpha=0.9)

    # Customize grid
    ax.grid(axis='y', linestyle='--', alpha=0.7, color='#666666')
    ax.grid(axis='x', linestyle='-', alpha=0.3, color='#999999')

    # Customize ticks
    ax.tick_params(axis='both', labelsize=10)

    # # Customize figure background
    # fig.patch.set_facecolor('#212121')
    # ax.set_facecolor('#333333')

    # Remove top and right spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Customize spine colors
    ax.spines['bottom'].set_color('#666666')
    ax.spines['left'].set_color('#666666')

    fig.tight_layout()

    # Convert plot to PNG image
    buf = BytesIO()
    FigureCanvasAgg(fig).print_png(buf)

    # Encode PNG image to base64 string
    buf_str = "data:image/png;base64,"
    buf_str += base64.b64encode(buf.getvalue()).decode('utf8')
            
    if bmi_stats_dict['avgbmi'] < 18.5:
        category = 'Underweight'
    elif bmi_stats_dict['avgbmi'] < 25:
        category = 'Normal'
    elif bmi_stats_dict['avgbmi'] < 30:
        category = 'Overweight'
    else:
        category = 'Obese'
        
    return render_template("bmi.html", imgsrc=buf_str, name=name, stat_dict = bmi_stats_dict, category=category)

@app.get("/dashboard/radar/<name>")
@flask_login.login_required
def radar(name):
    user = flask_login.current_user
    user_data = pd.read_excel('static/user_workout_DB/Users.xlsx', sheet_name = ['workout_data_%s'%user.username])
    user_data = user_data['workout_data_%s'%user.username]

    # shared variables
    workout_cat = ['Chest', 'Back', 'Arms', 'Core', 'Legs']
    theta = np.linspace(0, 2*np.pi, len(workout_cat)+1, endpoint=True)

    def reformatData(data_table):
        new_list = [
            data_table[data_table['Exercise_type'] == 'Chest']['weight_record'].sum(),
            data_table[data_table['Exercise_type'] == 'Back']['weight_record'].sum(),
            data_table[data_table['Exercise_type'] == 'Arms']['weight_record'].sum(),
            data_table[data_table['Exercise_type'] == 'Core']['weight_record'].sum(),
            data_table[data_table['Exercise_type'] == 'Legs']['weight_record'].sum(),
            data_table[data_table['Exercise_type'] == 'Chest']['weight_record'].sum()
        ]
        
        return new_list

    def dataByTime(table, end, start):
        table['Date'] = pd.to_datetime(table['Date'])
        return table[(table['Date'] <= end) & (table['Date'] >= start)]
    
    today = pd.to_datetime(datetime.datetime.today())
    this_week_data = dataByTime(user_data, today, today-timedelta(days=7))
    last_two_weeks_data = dataByTime(user_data, today, today-timedelta(days=14))
    last_four_weeks_data = dataByTime(user_data, today, today-timedelta(days=28))

    thisWeek = reformatData(this_week_data)
    lastTwoWeeks = reformatData(last_two_weeks_data)    
    lastFourWeeks = reformatData(last_four_weeks_data)    
    
    # plot data
    plt.figure(figsize=(6,6), facecolor='white')
    fig, radar = plt.subplots(subplot_kw={'projection': 'polar'})
    radar.set_facecolor('white')
    
    for spine in radar.spines.values():
        spine.set_color('black')
        spine.set_linewidth(1)   
        
    radar.xaxis.grid(color='black', linestyle='-', linewidth=2)
    radar.yaxis.grid(color='black', linestyle='-', linewidth=2)
    
    # plot Last 4 Weeks
    radar.plot(theta, lastFourWeeks, color='#D4EBF8', linewidth=4, label='Last 4 Weeks')
    # plot Last 2 Weeks
    radar.plot(theta, lastTwoWeeks, color='#608BC1', linewidth=4, label='Last 2 Weeks')
    # plot This Week
    radar.plot(theta, thisWeek, color='#0A3981', linewidth=4, label='This Week')

    # adjust ticks
    radar.set_xticks(theta[:-1])
    radar.set_xticklabels(workout_cat, color='black')
    
    # include legend
    plt.legend(loc='upper right', bbox_to_anchor=(1.2, 1.2))

    fig.tight_layout()

    # Convert plot to PNG image
    buf = BytesIO()
    FigureCanvasAgg(fig).print_png(buf)

    # Encode PNG image to base64 string
    buf_str = "data:image/png;base64,"
    buf_str += base64.b64encode(buf.getvalue()).decode('utf8')

    # Return the image and title in the template
    return render_template("radar.html", imgsrc=buf_str, name=name)