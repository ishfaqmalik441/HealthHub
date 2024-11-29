import pandas as pd
import matplotlib.pyplot as plt
import calendar
from pathlib import Path

class CalendarVisualizer:
    def __init__(self, file_path, username, user_calendars):
        self.data_path = file_path
        self.username = username
        self.sheet_name = f"workout_data_{username}"
        self.user_calendars = user_calendars

        if username in self.user_calendars:
            self.df = self.user_calendars[username].df
        else:
            try:
                # Load user data from the Excel file
                user_data = pd.read_excel(self.data_path, sheet_name=self.sheet_name)
                user_data["Date"] = pd.to_datetime(user_data["Date"], errors="coerce")
                user_data["Workout(Y/N)"] = user_data["Workout(Y/N)"].map({"Y": True, "N": False})
                user_data.dropna(subset=["Date"], inplace=True)
                self.df = user_data
                self.user_calendars[username] = self
            except Exception as e:
                print(f"Error loading data for {username}: {e}")
                self.df = pd.DataFrame(columns=["Date", "Workout(Y/N)"])

        self.current_date = self.df["Date"].min() if not self.df.empty else pd.Timestamp.today()
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.update_calendar(self.current_date.year, self.current_date.month)

    def plot_calendar(self, year, month):
        self.ax.clear()
        self.ax.set_xlim(-0.5, 6.5)
        self.ax.set_ylim(0, 5)
        self.ax.invert_yaxis()
        self.ax.axis("off")

        days_in_month = calendar.monthrange(year, month)[1]
        day_of_week, _ = calendar.monthrange(year, month)

        for day in range(1, days_in_month + 1):
            x = (day_of_week + day - 1) % 7
            y = (day_of_week + day - 1) // 7
            date = pd.Timestamp(year, month, day)

            workout_day = not self.df[(self.df["Date"] == date) & (self.df["Workout(Y/N)"])].empty

            if workout_day:
                self.ax.plot(x, y, "go", markersize=12, zorder=5)
                self.ax.annotate(day, (x, y), textcoords="offset points", xytext=(0, 10), ha="center", color="green", fontsize=10, zorder=10)
            else:
                self.ax.plot(x, y, "o", markersize=12, color="lightgrey", zorder=5)
                self.ax.annotate(day, (x, y), textcoords="offset points", xytext=(0, 10), ha="center", color="black", fontsize=10, zorder=10)

        self.ax.set_title(f"{calendar.month_name[month]} {year}", fontsize=16, pad=20)

    def save_fig(self):
        image_path = f"static/img/calendar_{self.username}.png"
        Path("static/img").mkdir(parents=True, exist_ok=True)
        self.fig.savefig(image_path)
        plt.close(self.fig)
        return image_path

    def update_calendar(self, year, month):
        self.plot_calendar(year, month)
        return self.save_fig()

    def next_month(self):
        self.current_date += pd.DateOffset(months=1)
        return self.update_calendar(self.current_date.year, self.current_date.month)

    def prev_month(self):
        self.current_date -= pd.DateOffset(months=1)
        return self.update_calendar(self.current_date.year, self.current_date.month)