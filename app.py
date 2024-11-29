from flask import Flask, url_for, render_template, request, redirect, session, flash
import pandas as pd
import numpy as np
import json, flask_login, datetime, requests, base64
from datetime import timedelta
from datetime import datetime
from hashlib import sha256
from models import *
from io import BytesIO
import calendar
import os
from matplotlib.figure import Figure
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.backends.backend_agg import FigureCanvasAgg
import matplotlib.pyplot as plt
import openpyxl
from calendar_visualizer import CalendarVisualizer
import matplotlib
matplotlib.use("Agg")
from flask import Flask, render_template, request, redirect, url_for, send_file
import os

user_calendars = {}
app = Flask(__name__)
app.secret_key = "9773e89f69e69285cf11c10cbc44a37945f6abbc5d78d5e20c2b1b0f12d75ab7"  # we need to change it

# Make the uploads folder
upload_folder = "uploads"
os.makedirs(upload_folder, exist_ok=True)
app.config["upload_folder"] = upload_folder


@app.route("/download/<template_name>", methods=["GET"])
def download_file(template_name):
    file_path = os.path.join("./static/file_template", template_name)
    return send_file(file_path, as_attachment=True, download_name=template_name)


# Login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

# data files
global USER_CREDENTIALS, USER_PREDICTIONS
USER_CREDENTIALS = "static/users/credentials.json"

# # API URL
# TODAY = datetime.date.today()
# ONEYEARAGO = TODAY - datetime.timedelta(days=365)
# URL_BASE = "https://api.polygon.io/v2/aggs/ticker/MYTICKER/range/1/day/%s/%s"%(ONEYEARAGO, TODAY)


# it must be here for maintain user session after logged in
@login_manager.user_loader
def load_user(userid):
    user_json = pd.read_json(USER_CREDENTIALS).get(userid)
    return User(user_json["username"], user_json["password"], user_json["email"])


@app.get("/")
def index():
    msg = request.args.get("msg")
    return render_template("index.html", msg=msg)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")
        password_hash = sha256(password.encode("utf-8")).hexdigest()

        # check if the user already exists
        # for simplicity, we use a JSON to keep track of all registered users for now
        # user_existing = pd.read_json(USER_CREDENTIALS).T
        user_existing = pd.read_json(USER_CREDENTIALS).T
        # xxx.t --> is to exchange col and row

        existing_usernames = user_existing["username"].values
        # if exists, refresh this page with an error message
        # if username in user_existing['username']:
        if username in existing_usernames:
            # x in existing_usernames(['x', 'y', 'z']) --> true, x is inside
            return render_template("signup.html", msg="username")
        # if not, go ahead and put it to the JSON (append)
        user_series = pd.Series(
            dict(username=username, password=password_hash, email=email)
        )
        user_existing.loc[sha256(username.encode("utf-8")).hexdigest()] = user_series
        user_existing.to_json(USER_CREDENTIALS, orient="index")
        return redirect(url_for("login", msg="signup"))
    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST" and "login" in request.form:
        # Get form data
        username = request.form.get("username")  # Use .get() to avoid KeyErrors
        password = request.form.get("password")

        # Hash username and password
        userid = sha256(username.encode("utf-8")).hexdigest()
        password_hash = sha256(password.encode("utf-8")).hexdigest()

        # Load users.json
        with open(USER_CREDENTIALS, "r") as file:
            users = json.load(file)  # Load JSON data as a dictionary

        # Check if user exists
        user_json = users.get(userid)
        if user_json is None:  # If user does not exist
            return render_template("login.html", msg="notexist")

        # Check if password matches
        if user_json["password"] != password_hash:
            return render_template("login.html", msg="mismatch")

        # Login the user
        user = User(user_json["username"], user_json["password"], user_json["email"])
        flask_login.login_user(user)
        return redirect(
            url_for(
                "dashboard", msg="logged in", name=flask_login.current_user.username
            )
        )

    elif request.method == "POST" and "signup" in request.form:
        return redirect(url_for("signup"))

    return render_template("login.html", msg=request.args.get("msg"))


@app.get("/user/<name>")
@flask_login.login_required
def user(name):
    return render_template(
        "user_profile.html", edit="No", name=flask_login.current_user.username
    )


@app.post("/user/<name>")
@flask_login.login_required
def user_edit(name):
    user = flask_login.current_user
    msg = None  # Default message

    if "edit" in request.form:
        return render_template(
            "user_profile.html", edit="Yes", name=user.username, msg=msg
        )
    elif "delAC" in request.form:
        user_json = pd.read_json(USER_CREDENTIALS)
        file_path = "static/user_workout_DB/Users.xlsx"
        file = openpyxl.load_workbook(file_path)
        all_sheet = file.sheetnames
        user_sheet_name = f"workout_data_{user.username}"
        if user_sheet_name in all_sheet:
            sheet_to_remove = file[user_sheet_name]
            file.remove(sheet_to_remove)
            file.save("static/user_workout_DB/Users.xlsx")

        user_json.drop(user.id, axis=1, inplace=True)
        user_json.to_json(USER_CREDENTIALS)
        flask_login.logout_user()  # Log the user out
        msg = "deleted"
        return redirect(url_for("index", msg=msg))
    else:
        user_json = pd.read_json(USER_CREDENTIALS)
        try:
            new_password = request.form.get("password", "").strip()
            new_email = request.form.get("email", "").strip()

            # Update password only if it's not empty
            if new_password:
                hashed_password = sha256(new_password.encode("utf-8")).hexdigest()
                user_json.loc["password", user.id] = hashed_password

            # Update email only if it's not empty
            if new_email:
                user_json.loc["email", user.id] = new_email

            if new_password or new_email:
                msg = "success"
            else:
                msg = "nothing done"
        except:
            pass

    user_json.to_json(USER_CREDENTIALS)
    return render_template("user_profile.html", edit="No", name=user.username, msg=msg)


@app.route("/logout")
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return redirect(url_for("index"))


@app.route("/about")
def about():
    return render_template("about.html")


@app.get("/dashboard/<name>")
@flask_login.login_required
def dashboard(name):
    message = request.args.get(
        "msg", default="Welcome!"
    )  # Default message if not provided
    return render_template("dashboard.html", msg=message, name=name)


@app.get("/test")
def test():
    return render_template("test.html")


# Function to save the uploaded file and possibly for data processing
@app.post("/upload/<name>")
def upload_file(name):
    global user_calendars  # Reference the global dictionary

    file = request.files["file"]

    if file.filename == "":
        return redirect(url_for("dashboard", msg="No File Uploaded", name=name))
    if file:
        # Determine file type and read data
        if file.filename.endswith(".csv"):
            data = pd.read_csv(file)
        elif file.filename.endswith(".xls") or file.filename.endswith(".xlsx"):
            data = pd.read_excel(file)
        else:
            return redirect(
                url_for("dashboard", msg="File Type not supported", name=name)
            )

        file_path = "static/user_workout_DB/Users.xlsx"
        with pd.ExcelWriter(file_path, mode="a", if_sheet_exists="replace") as writer:
            data.to_excel(writer, sheet_name=f"workout_data_{name}", index=False)

        user_calendars[name] = CalendarVisualizer(file_path, name)

        return redirect(url_for("dashboard", msg="File Uploaded", name=name))

# Function for calculating the user BMI
def calculate_bmi(weight, height_cm):
    height_m = height_cm / 100  # Convert height to meters
    return round(
        weight / (height_m**2), 1
    )  # Calculate BMI and round to 2 decimal places


def calculate_weight(bmi, height):
    height_m = height / 100  # Convert height to meters
    weight = bmi * (height_m**2)

    return weight


def create_custom_cmap():
    return LinearSegmentedColormap.from_list("", ["#3498db", "#f1c40f", "#e74c3c"])


@app.get("/dashboard/bmi-calculator/<name>")
@flask_login.login_required
def bmiCalc(name):
    return render_template("bmi-calculator.html", name=name)


@app.post("/dashboard/bmi-calculator/<name>")
@flask_login.login_required
def bmiCalculator(name):
    weight = float(request.form["weight"])
    height = float(request.form["height"])
    bmi = calculate_bmi(weight, height)
    min_weight = round(calculate_weight(18.5, height), 2)
    max_weight = round(calculate_weight(24.9, height), 2)
    foodNutrition = []

    if bmi < 18.5:
        category = "Underweight"
        foodNutrition = [
            "Nuts and seeds (e.g. almonds, cashews, pumpkin seeds)",
            "Full-fat dairy products (e.g. whole milk, full-fat yogurt, cheese)",
            "Fatty fish (e.g. salmon, tuna)",
            "Lean meats (e.g. chicken, beef, pork)",
            "Eggs",
            "Fruits (e.g bananas, mangoes)",
            "Vegetables (e.g corn, sweet potatoes)",
        ]
    elif bmi < 25:
        category = "Normal"
        foodNutrition = [
            "Vegetables (e.g spinach, kale, broccoli, cauliflower)",
            "Lean protiens (e.g chicken, fish)",
            "Legumes (e.g lentils, beans)",
            "Whole grains (e.g quinoa, brown rice)",
            "Nuts and seeds",
        ]
    elif bmi < 30:
        category = "Overweight"
        foodNutrition = [
            "Vegetables (leafy greens, broccoli, bell peppers)",
            "Fruits (apples, berries, citrus fruits)",
            "Lean proteins (chicken, turkey, fish)",
            "Whole grains (brown rice, quinoa, whole wheat)",
        ]
    else:
        category = "Obese"
        foodNutrition = [
            "Vegetables (leafy greens, broccoli, bell peppers)",
            "Fruits (apples, berries, citrus fruits)",
            "Lean proteins (chicken, turkey, fish)",
            "Whole grains (brown rice, quinoa, whole wheat)",
        ]
    return render_template(
        "bmi-calculator.html",
        name=name,
        bmi=bmi,
        height=height,
        category=category,
        min_weight=min_weight,
        max_weight=max_weight,
        nutrition=foodNutrition,
    )


# Function for analysing and processing the user data, and providing a visualization of the User's BMI
@app.get("/dashboard/bmi/<name>")
@flask_login.login_required
def bmi(name):
    bmi_stats_dict = {}
    user = flask_login.current_user
    try:
        user_data = pd.read_excel(
            "static/user_workout_DB/Users.xlsx",
            sheet_name=["workout_data_%s" % user.username],
        )
        user_data = user_data["workout_data_%s" % user.username]
        user_data["height_cm"] = user_data["height_cm"][0]

        user_data["Date"] = user_data["Date"].dt.date
        user_data["BMI"] = calculate_bmi(
            user_data["weight_record_kg"], user_data["height_cm"]
        )
        healthy_bmi_max = 24.9
        healthy_bmi_min = 18.5
        count = user_data["BMI"].count()

        bmi_stats_dict["DayCount"] = count
        highestbmiIndex = user_data["BMI"].idxmax()
        bmi_stats_dict["highestbmi"] = {
            "date": user_data.loc[highestbmiIndex]["Date"],
            "value": user_data["BMI"].max(),
        }
        healthyDays = 0
        for bmi in user_data["BMI"]:
            if bmi > 18.5 and bmi < 25:
                healthyDays = healthyDays + 1
        bmi_stats_dict["healthyDays"] = healthyDays
        lowestbmiIndex = user_data["BMI"].idxmin()
        bmi_stats_dict["lowestbmi"] = {
            "date": user_data.loc[lowestbmiIndex]["Date"],
            "value": user_data["BMI"].min(),
        }
        bmi_stats_dict["avgbmi"] = round(user_data["BMI"].mean(), 2)
        bmi_stats_dict["stdbmi"] = round(user_data["BMI"].std(), 2)

        fig = Figure(figsize=[11, 6])
        ax_arr = fig.subplots(ncols=1)
        ax = ax_arr

        # Plot BMI data
        ax.plot(
            user_data["Date"],
            user_data["BMI"],
            label="BMI (Line)",
            color="#3498db",
            linestyle="-",
            linewidth=2,
            alpha=0.7,
        )
        ax.scatter(
            user_data["Date"],
            user_data["BMI"],
            label="BMI (Scatter)",
            color="#f1c40f",
            s=80,
            edgecolor="white",
            zorder=100,
        )

        # Add healthy BMI range
        ax.axhspan(
            healthy_bmi_min,
            healthy_bmi_max,
            color="#2ecc71",
            label="Healthy BMI Range (18.5 - 24.9)",
            alpha=0.2,
        )

        # Set y-axis limits
        bmi_min = max(0, user_data["BMI"].min() - 1)
        bmi_max = user_data["BMI"].max() + 1
        ax.set_ylim(bmi_min, bmi_max)

        # Customize plot appearance
        ax.set_xlabel("Date", fontsize=14, fontweight="bold")
        ax.set_ylabel("BMI", fontsize=14, fontweight="bold")
        ax.set_title(f"BMI throughout the {count} days", fontsize=18, fontweight="bold")

        # Customize legend
        ax.legend(loc="upper right", fontsize=12, framealpha=0.9)

        # Customize grid
        ax.grid(axis="y", linestyle="--", alpha=0.7, color="#666666")
        ax.grid(axis="x", linestyle="-", alpha=0.3, color="#999999")

        # Customize ticks
        ax.tick_params(axis="both", labelsize=10)

        # Remove top and right spines
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        # Customize spine colors
        ax.spines["bottom"].set_color("#666666")
        ax.spines["left"].set_color("#666666")

        fig.tight_layout()

        # Convert plot to PNG image
        buf = BytesIO()
        FigureCanvasAgg(fig).print_png(buf)

        # Encode PNG image to base64 string
        buf_str = "data:image/png;base64,"
        buf_str += base64.b64encode(buf.getvalue()).decode("utf8")

        if bmi_stats_dict["avgbmi"] < 18.5:
            category = "Underweight"
        elif bmi_stats_dict["avgbmi"] < 25:
            category = "Normal"
        elif bmi_stats_dict["avgbmi"] < 30:
            category = "Overweight"
        else:
            category = "Obese"

        return render_template(
            "bmi.html",
            imgsrc=buf_str,
            name=name,
            stat_dict=bmi_stats_dict,
            category=category,
        )
    except Exception as e:
        return redirect(url_for("dashboard", name=name, msg="Sheet not found"))

    redirect(url_for("dashboard", name=name, msg="Sheet not found"))


@app.get("/dashboard/radar/<name>")
@flask_login.login_required
def radar(name):
    user = flask_login.current_user
    user_data = pd.read_excel(
        "static/user_workout_DB/Users.xlsx",
        sheet_name=["workout_data_%s" % user.username],
    )
    user_data = user_data["workout_data_%s" % user.username]

    # shared variables
    workout_cat = ["Chest", "Back", "Arms", "Core", "Legs"]
    theta = np.linspace(0, 2 * np.pi, len(workout_cat) + 1, endpoint=True)

    def reformatData(data_table):
        new_list = [
            data_table[data_table["Exercise_type"] == "Chest"]["weight_record_kg"].sum(),
            data_table[data_table["Exercise_type"] == "Back"]["weight_record_kg"].sum(),
            data_table[data_table["Exercise_type"] == "Arms"]["weight_record_kg"].sum(),
            data_table[data_table["Exercise_type"] == "Core"]["weight_record_kg"].sum(),
            data_table[data_table["Exercise_type"] == "Legs"]["weight_record_kg"].sum(),
            data_table[data_table["Exercise_type"] == "Chest"]["weight_record_kg"].sum(),
        ]

        return new_list

    def dataByTime(table, end, start):
        table["Date"] = pd.to_datetime(table["Date"])
        return table[(table["Date"] <= end) & (table["Date"] >= start)]

    today = pd.to_datetime(datetime.today())
    this_week_data = dataByTime(user_data, today, today - timedelta(days=7))
    last_two_weeks_data = dataByTime(user_data, today, today - timedelta(days=14))
    last_four_weeks_data = dataByTime(user_data, today, today - timedelta(days=28))

    thisWeek = reformatData(this_week_data)
    lastTwoWeeks = reformatData(last_two_weeks_data)
    lastFourWeeks = reformatData(last_four_weeks_data)

    # plot data
    fig = Figure(figsize=[11, 6], facecolor="white")
    radar = fig.subplots(subplot_kw={"projection": "polar"})
    radar.set_facecolor("white")

    for spine in radar.spines.values():
        spine.set_color("black")
        spine.set_linewidth(1)

    radar.xaxis.grid(color="black", linestyle="-", linewidth=2)
    radar.yaxis.grid(color="black", linestyle="-", linewidth=2)

    # plot Last 4 Weeks
    radar.plot(theta, lastFourWeeks, color="#D4EBF8", linewidth=4, label="Last 4 Weeks")
    # plot Last 2 Weeks
    radar.plot(theta, lastTwoWeeks, color="#608BC1", linewidth=4, label="Last 2 Weeks")
    # plot This Week
    radar.plot(theta, thisWeek, color="#0A3981", linewidth=4, label="This Week")

    # adjust ticks
    radar.set_xticks(theta[:-1])
    radar.set_xticklabels(workout_cat, color="black")

    # include legend
    radar.legend(loc="upper right", bbox_to_anchor=(1.2, 1.2))

    fig.tight_layout()

    # Convert plot to PNG image
    buf = BytesIO()
    FigureCanvasAgg(fig).print_png(buf)

    # Encode PNG image to base64 string
    buf_str = "data:image/png;base64,"
    buf_str += base64.b64encode(buf.getvalue()).decode("utf8")

    # Return the image and title in the template
    return render_template("radar.html", imgsrc=buf_str, name=name)


def calculate_longest_streak(workout_days):
    if not workout_days:
        return 0

    workout_days = sorted(workout_days)
    longest_streak = 1
    current_streak = 1

    for i in range(1, len(workout_days)):
        if workout_days[i] == workout_days[i - 1] + 1:
            current_streak += 1
            longest_streak = max(longest_streak, current_streak)
        else:
            current_streak = 1

    return longest_streak

USER_WORKOUT_DB_PATH = "static/user_workout_DB/Users.xlsx"


@app.route("/dashboard/calendar/<name>", methods=["GET"])
@flask_login.login_required
def display_calendar(name):
    # Try to create a CalendarVisualizer instance for the user
    try:
        calendar_vis = CalendarVisualizer(USER_WORKOUT_DB_PATH, name)
    except FileNotFoundError:
        # Handle case where the file does not exist
        return redirect(
            url_for(
                "dashboard",
                msg="Error: Workout data file not found. Please upload it first.",
                name=name,
            )
        )
    except ValueError as e:
        # Handle case where the sheet does not exist for the user
        return redirect(
            url_for(
                "dashboard",
                msg=f"Error loading your workout data: {e}. Please upload it first.",
                name=name,
            )
        )

    # Get the current year and month from the visualizer
    year = calendar_vis.current_date.year
    month = calendar_vis.current_date.month

    now = datetime.now()
    is_current_month = month == now.month and year == now.year

    # Filter data for the current month
    current_month_data = calendar_vis.df[
        (calendar_vis.df["Date"].dt.year == year)
        & (calendar_vis.df["Date"].dt.month == month)
    ]

    # Ensure the "Workout(Y/N)" column exists and map its values to boolean
    if "Workout(Y/N)" not in current_month_data.columns:
        return "Error: Workout(Y/N) column missing from data."

    current_month_data["Workout(Y/N)"] = current_month_data["Workout(Y/N)"].map(
        {
            True: True,
            1: True,
            "Y": True,
            "Yes": True,
            False: False,
            0: False,
            "N": False,
            "No": False,
        }
    )

    total_workouts = current_month_data["Workout(Y/N)"].sum()

    # Get a list of workout days for the current month
    workout_days = current_month_data[current_month_data["Workout(Y/N)"]][
        "Date"
    ].dt.day.tolist()

    # Calculate the longest streak
    longest_streak = calculate_longest_streak(workout_days)

    # Generate a list of calendar days with workout information
    days_in_month = calendar.monthrange(year, month)[1]
    calendar_days = []
    for day in range(1, days_in_month + 1):
        is_workout = day in workout_days
        calendar_days.append({"day": day, "workout": is_workout})

    # Render the calendar template
    return render_template(
        "calendar.html",
        name=name,
        current_month=calendar.month_name[month],
        current_year=year,
        calendar_days=calendar_days,
        total_workouts=total_workouts,
        longest_streak=longest_streak,
        is_current_month=is_current_month,
    )


@app.route("/dashboard/calendar/<name>/next", methods=["GET"])
@flask_login.login_required
def next_month(name):
    # Instantiate CalendarVisualizer and move to the next month
    try:
        calendar_vis = CalendarVisualizer(USER_WORKOUT_DB_PATH, name)
        calendar_vis.next_month()
        return redirect(url_for("display_calendar", name=name))
    except (FileNotFoundError, ValueError) as e:
        return redirect(
            url_for("dashboard", msg=f"Error: {e}. Please upload your workout data first.", name=name)
        )


@app.route("/dashboard/calendar/<name>/prev", methods=["GET"])
@flask_login.login_required
def prev_month(name):
    # Instantiate CalendarVisualizer and move to the previous month
    try:
        calendar_vis = CalendarVisualizer(USER_WORKOUT_DB_PATH, name)
        calendar_vis.prev_month()
        return redirect(url_for("display_calendar", name=name))
    except (FileNotFoundError, ValueError) as e:
        return redirect(
            url_for("dashboard", msg=f"Error: {e}. Please upload your workout data first.", name=name)
        )

food_data_df = pd.read_csv('./static/food/food_data.csv')

def search_food_calories(food_name):
    food_entry = food_data_df[
        food_data_df["Food Name"].str.lower() == food_name.lower()
    ]
    if not food_entry.empty:
        return food_entry["Calories (kcal)"].values[0]
    else:
        return "unknown"


def calculate_daily_calories(current_weight, target_weight, days, bmr):
    weight_diff = target_weight - current_weight
    total_calorie_deficit = weight_diff * 7700
    daily_calorie_deficit = total_calorie_deficit / days
    return round(bmr + daily_calorie_deficit, 2)


def calculate_bmr(weight, height, age, gender, activity_level):
    if gender == "male":
        return (66 + (13.7 * weight) + (5 * height) - (6.8 * age)) * activity_level
    else:
        return (655 + (9.6 * weight) + (1.8 * height) - (4.7 * age)) * activity_level


def process_file(file):
    try:
        
        if file.filename.endswith(".csv"):
            df = pd.read_csv(file)
        # Attempt to read the file as Excel if not CSV
        elif file.filename.endswith(".xls") or file.filename.endswith(".xlsx"):
            df = pd.read_excel(file)

        if (
            "Date" not in df.columns
            or "Food" not in df.columns
            or "FoodWeight" not in df.columns
        ):
            raise ValueError(
                "File must contain 'Date', 'Food', and 'FoodWeight' columns."
            )

        df["Calories"] = df.apply(
            lambda row: search_food_calories(row["Food"]) * row["FoodWeight"] / 100,
            axis=1,
        )
        df["Calories"] = pd.to_numeric(df["Calories"])
        df["TotalWeight"] = df.groupby("Date")["Calories"].transform("sum")

        result_df = df[["Date", "Food", "Calories", "TotalWeight"]]
        return result_df
    except:
        pass


def generate_comparison_chart(
    daily_actual_calories, daily_calories_target, output_path
):
    try:
        daily_actual_calories_unique = daily_actual_calories[
            ["Date", "TotalWeight"]
        ].drop_duplicates()
        daily_actual_calories_unique["Date"] = pd.to_datetime(
            daily_actual_calories_unique["Date"], format="%d/%m/%Y"
        )
        daily_actual_calories_unique.sort_values(by="Date", inplace=True)
        daily_actual_calories_unique["TargetWeight"] = daily_calories_target

        dates = daily_actual_calories_unique["Date"]
        actual_weight = daily_actual_calories_unique["TotalWeight"]
        target_weight = daily_actual_calories_unique["TargetWeight"]

        plt.figure(figsize=(10, 10))
        plt.plot(
            dates,
            actual_weight,
            label="Actual calorie",
            marker="o",
            color="blue",
            linewidth=2,
        )
        plt.plot(
            dates,
            target_weight,
            label="Target calorie",
            linestyle="--",
            color="red",
            linewidth=2,
        )

        plt.xlabel("Date", fontsize=12)
        plt.ylabel("Calories", fontsize=12)
        plt.title("Daily Calorie Comparison", fontsize=16, fontweight="bold")
        plt.xticks(rotation=45, fontsize=10)
        plt.yticks(fontsize=10)
        plt.grid(alpha=0.3)
        plt.legend(fontsize=12, loc="upper right")
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
    except:
        return None


@app.route("/dashboard/Dietplan/<name>", methods=["GET", "POST"])
@flask_login.login_required
def calorie_calculator(name):
    if request.method == "POST":
        try:
            weight = float(request.form.get("weight"))
            height = float(request.form.get("height"))
            age = int(request.form.get("age"))
            gender = request.form.get("gender")
            target_weight = float(request.form.get("target_weight"))
            days = int(request.form.get("days"))
            activity_level = float(request.form.get("activity_level"))

            bmr = calculate_bmr(weight, height, age, gender, activity_level)
            daily_calories_target = calculate_daily_calories(
                weight, target_weight, days, bmr
            )
            if daily_calories_target < 1200:
                daily_calories_target = 1200

            uploaded_file = request.files["file"]
            if uploaded_file:
                daily_actual_calories = process_file(uploaded_file)

                if daily_actual_calories is None or daily_actual_calories.empty:
                    return (
                        "Error processing file. The DataFrame is empty or invalid.",
                        400,
                    )

                daily_actual_calories_unique = daily_actual_calories[
                    ["Date", "TotalWeight"]
                ].drop_duplicates()
                daily_actual_calories_unique["Date"] = pd.to_datetime(
                    daily_actual_calories_unique["Date"], format="%d/%m/%Y"
                ).dt.date
                daily_actual_calories_unique.sort_values(by="Date", inplace=True)
                daily_actual_calories_list = daily_actual_calories_unique[
                    ["Date", "TotalWeight"]
                ].values.tolist()

                chart_path = os.path.join("static", "img", "comparison_chart.png")
                generate_comparison_chart(
                    daily_actual_calories, daily_calories_target, chart_path
                )

                return render_template(
                    "Dietplan.html",
                    daily_calories_target=daily_calories_target,
                    daily_actual_calories=daily_actual_calories_list,
                    name=flask_login.current_user.username,
                    chart_path="/static/img/comparison_chart.png",
                )
        except:
            return None

    return render_template("Dietplan.html", name=name)


if __name__ == "__main__":
    app.run(debug=True)
