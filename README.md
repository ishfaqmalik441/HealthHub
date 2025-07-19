

---

# HealthHub

This project is a full-stack health and fitness web application to help you stay healthy and on top of your game! It is a smart application that understands user needs and goals, and helps them achieve their fitness goals through personalized recommendations and streamlined management of their progress. It enables users to upload and save their personal health information, workout history, and set their personal fitness goals in a secure account that they can set up and store this information in their secure account. It then automatically analyzes this information and builds personalized recommendations as well as clean visualizations of their fitness journey so far, such as visualizations of their BMI progress over time, the areas of the body they have focused on more in any given period. It also provides them with a personal calendar where they can log their workout days and visualize their current streaks or the days in the past month or year that they worked out on or did any physical activity. This app is the perfect companion to help you set and reach your fitness goals!
---

## Table of Contents

1. [File Structure](#file-structure)
2. [Features](#features)
3. [How to Run the Application](#how-to-run-the-application)
4. [Data Upload Formats](#data-upload-formats)
5. [Templates Overview](#templates-overview)
6. [Future Enhancements](#future-enhancements)

---

## File Structure

Here is the project's file structure, along with a description of each component:

```
.
├── app.py                     # Main Flask application file
├── calendar_visualizer.py     # Handles workout calendar visualization
├── models.py                  # Defines data models for users and workouts
├── static/                    # Contains static assets like CSS, images, and uploaded files
│   ├── file_template/
│   │   ├──General.xlsx        # Excel template for users to upload workout data
│   │   └──Dietplan.xlsx       # Excel template for users to upload diet plans
│   ├── food/
│   │   └── food_data.csv      # Nutritional data for diet plans
│   ├── img/                   # Stores images (e.g., logos, calendar visualizations)
│   ├── user_workout_DB/
│   │   └── Users.xlsx         # Centralized storage for user workout data
│   └── users/                 # Reserved for user-specific files
├── templates/                 # HTML templates rendered by Flask
│   ├── about.html             # About page
│   ├── base.html              # Base layout for all templates
│   ├── bmi.html               # BMI calculator page
│   ├── calendar.html          # Workout calendar visualization
│   ├── dashboard.html         # User dashboard
│   ├── Dietplan.html          # Displays diet plans
│   ├── index.html             # Home page
│   ├── list.html              # Generic list display (e.g., workouts)
│   ├── login.html             # User login page
│   ├── olddashboard.html      # Previous version of the dashboard
│   ├── radar.html             # Radar chart visualization page
│   ├── signup.html            # User registration page
│   ├── test.html              # Test page for development
│   ├── upload.html            # File upload page for workouts and diet plans
│   └── user_profile.html      # User profile page
├── uploads/                   # Stores uploaded files
│   ├── Book1.xlsx             # Example upload file
│   └── Book3.xlsx             # Example upload file
├── README.md                  # Project documentation
├── .gitignore                 # Files and directories to ignore in Git
```

---

## Features

1. **User Authentication**:
   - Secure user registration and login.
   - Access to personalized dashboards after login.

2. **Workout Calendar Visualization**:
   - Upload workout schedules in `.xlsx` or `.csv` format.
   - View a monthly calendar with workout days highlighted.
   - Displays total workouts and the longest workout streak for each month.

3. **Diet Plan Management**:
   - We use the API to collect the food data from internet, store it as the csv file and as a database for us to calculate the calorie
   - Upload and manage diet plans using an Excel template.
   - After the user uplaod the file contain daily food intake for a period of time, we will match the food with our food_database and then return their actual daily calorie intake
   - Input the use body information, and also the target weight, provide user a daily calorie intake refercenes 

4. **Body Mass Index (BMI) Analysis**:
   - Gain a comprehensive analysis of your body mass index (BMI) trends over time. 
   - Visualize how your weight and health status have evolved. 
   - Gain valuable insights into BMI changes, categorizes weight status (underweight, normal, overweight, or obese), and important statistics related to your BMI.
   - Calculate your BMI as well through our interactive BMI calculator!

5. **Interactive User-Friendly Dashboard**:
   - Central hub to monitor fitness progress, access diet plans, and upload new data.

6. **Radar Chart Data Visualization**:
   - Takes the user's workout records and plot the workout volumes based on muscle group to gain understanding of their past workouts' concentration.
   - The chart visualized the data of different time periods i.e., this week, last 2 weeeks, and last 4 weeks to identify in case there is a change in workout plans.
   - Gain an overall insight on their past training concentration and use it for future training plan considerations.
   - To do that, we use the user's workout data that is grouped by 5 muscle groups and aggregate them based on the specified time period to be then plotted onto the radar chart.

7. **Error Handling**:
   - Displays clear error messages for invalid uploads or missing data.

---
## Data Collection

1. **General Data**:
   - The users will uploading their own data regarding workout history in a past period of time, weight changes, 
   and muscle groups of the body worked out
   - A template is provided to the user to download, so they can edit that template, fill in their data in the 
   given format and upload it for analysis
   - The data is cleaned for any missing values and also standardised for the analysis tools in the app
   - The height data is generalized and assumed as the same for all dates the user has entered the data for
   as we are assuming that the user is an adult with no height changes expected
   - In order upload new data the for its analysis the user can edit the same excel file, they uploaded before add
   additional data and upload it, we will take this as the users new data and overwrite their previous data with this
   new own in our excel database.
   - The user's data is stored in our excel database with the user's own personal sheet for their general data. The database is available live on the server.

2. **Dietplan Data**:
   - The users will uploading their own diet data in a past period of time, included what kind of foods, and the weight
   - A template is provided to the user to download, the data already filled in advance as an example, user can follow the format to edit their own actual data
   - The database we use to calculaet the food calorie was through API to collect data from the https://api.nal.usda.gov/fdc/v1/foods/search API KEY: faH6tAzZ8V9ltT9U9ET0s3We9gjpqjNqjtj1A3eW
   - To calcuate the target intake per day, user also need to input their current body data, such as weight, and height
   - Consider the diet plan is changine everyday, user will need to upload a new file everytime
   - Here is the code for running the API:
      
      '''
      import requests
      import pandas as pd
      import random

      api_key = "faH6tAzZ8V9ltT9U9ET0s3We9gjpqjNqjtj1A3eW"
      url = "https://api.nal.usda.gov/fdc/v1/foods/search"
      params = {'query': 'food','api_key': api_key,'pageSize': 10,}
      food_data = [] 
      target_count = 5000
      
      while len(food_data) < target_count:
         params['pageNumber'] = random.randint(1, 1000)  
         response = requests.get(url, params=params)
    

         if response.status_code != 200:
            print(f"Error: Unable to fetch data (status code {response.status_code})")
            continue
    
         data = response.json()
         
         for food in data.get('foods', []):
            food_name = food.get('description', 'N/A')
            nutrients = food.get('foodNutrients', [])
            calories = next((nutrient['value'] for nutrient in nutrients if nutrient.get('nutrientName') == 'Energy'), 'N/A')
        
            food_data.append({'Food Name': food_name,'Calories': calories})
        
            if len(food_data) >= target_count:
               break

            print(f"Fetched {len(food_data)} items so far...")

      df = pd.DataFrame(food_data)
      output_file = 'food_calories.xlsx'
      df.to_excel(output_file, index=False)

      print("\nSample Food Items:")
      print(df.head(20).to_string(index=False))

      print(f"\nSuccessfully saved {len(food_data)} food items to {output_file}")      
      '''      
---


## How to Run the Application

### Step 1: Clone the Repository
```bash
git clone <repository_url>
cd IS-3240-Web-Application
```

### Step 2: Set Up a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run the Application
```bash
python app.py
```

### Step 5: Open the Application
Open your browser and go to `http://127.0.0.1:5000`.

---

## Data Upload Formats

### Workout Data Format
Users should upload workout data in the following format:

| Date       | Workout(Y/N) |
|------------|--------------|
| 2024-01-01 | Y            |
| 2024-01-02 | N            |

- **`Date`**: Must be in `YYYY-MM-DD` format.
- **`Workout(Y/N)`**: Use `Y` (Yes) for workout days and `N` (No) for non-workout days.

### Diet Plan Format
Users can upload diet plans using the provided `Dietplan.xlsx` template:

| Date      | food        | FoodWeight| 
|-----------|-------------|---------- |
| DD/MM/YY  | Apple       | 30        |
| DD/MM/YY  | Beef        | 60        |

---

## Templates Overview

### Key Templates
1. **`base.html`**:
   - Base layout for all pages (header, footer, and navigation bar).
2. **`index.html`**:
   - Home page introducing the app.
3. **`dashboard.html`**:
   - Displays user progress and links to other features (e.g., calendar, diet plans).
4. **`calendar.html`**:
   - Visualizes workout schedules for a specific month.
5. **`Dietplan.html`**:
   - Displays uploaded diet plans with nutritional details, and display the graph for weight control reference
6. **`bmi.html`**:
   - Allows users to see an analysis of their BMI through a scatter and line plot and show them for how long
   their BMI was in the healthy range for the given amount of days and alaso showing some statistics for their BMI
   analysis
7. **`login.html` and `signup.html`**:
   - Login and registration pages for user authentication.
8. **`upload.html`**:
   - Page for uploading files (workouts or diet plans).
9. **`user_profile.html`**:
   - Displays user-specific details like name, email, and fitness stats.
10. **`bmi-calculator.html`**:
   - Allows the user to enter his current weight and height and calculates his BMI as well as providing nutritional
   recommendations for how he can increase, decrease of mantain his weight to reach or stay in the healthy BMI range.

---

## Future Enhancements

1. **Mobile-Friendly Design**:
   - Improve responsiveness for better usability on mobile devices.

2. **Advanced Data Visualization**:
   - Add more visualizations like pie charts for calorie distribution or line graphs for progress tracking.

3. **Third-Party Integration**:
   - Synchronize data with fitness apps like Fitbit or Google Fit.

4. **Notifications**:
   - Add email or SMS reminders for workouts and diet plan adherence.

5. **PDF Reports**:
   - Allow users to download their workout and diet reports as PDFs.

---

## Contribution Guidelines

We welcome contributions to improve this project! Please follow these steps:

1. Fork this repository.
2. Create a new branch for your feature or bug fix.
3. Commit your changes and push to your branch.
4. Open a pull request with a detailed description of your changes.

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

