

---

# IS-3240 Web Application

This project is a web-based application for managing fitness and diet plans. It enables users to upload and visualize workout data, monitor their fitness progress, and manage diet plans. The application provides a user-friendly interface with features like workout calendar visualization, BMI calculation, and personalized dashboards.

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

5. **Interactive User-Friendly Dashboard**:
   - Central hub to monitor fitness progress, access diet plans, and upload new data.

6. **Data Visualization**:
   - Radar charts and other visualizations to track fitness and diet adherence.

7. **Error Handling**:
   - Displays clear error messages for invalid uploads or missing data.

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
   - Allows users to calculate their BMI.
7. **`login.html` and `signup.html`**:
   - Login and registration pages for user authentication.
8. **`upload.html`**:
   - Page for uploading files (workouts or diet plans).
9. **`user_profile.html`**:
   - Displays user-specific details like name, email, and fitness stats.

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

