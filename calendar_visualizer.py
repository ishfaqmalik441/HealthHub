import pandas as pd
import matplotlib.pyplot as plt
import calendar
from matplotlib.widgets import Button

import pandas as pd
import calendar
import matplotlib.pyplot as plt


class CalendarVisualizer:
    def __init__(self, data_path, username):
        self.data_path = data_path
        self.username = username
        self.sheet_name = f"workout_data_{username}"

        # Load user data
        try:
            self.df = pd.read_excel(data_path, sheet_name=self.sheet_name)
            self.df["Date"] = pd.to_datetime(
                self.df["Date"], errors="coerce"
            )  # Handle invalid dates
            self.df["Workout(Y/N)"] = self.df["Workout(Y/N)"].map(
                {"Y": True, "N": False}
            )
            self.df.dropna(
                subset=["Date"], inplace=True
            )  # Drop rows with invalid or missing dates
        except Exception as e:
            # If the sheet doesn't exist or there is an error, initialize an empty DataFrame
            print(f"Error loading data for {username}: {e}")
            self.df = pd.DataFrame(columns=["Date", "Workout(Y/N)"])

        # Set the current date to the earliest date in the dataset, or today if no data exists
        self.current_date = (
            self.df["Date"].min() if not self.df.empty else pd.Timestamp.today()
        )

        # Initialize the figure and plot the current calendar
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.update_calendar(self.current_date.year, self.current_date.month)

    def plot_calendar(self, year, month):
        self.ax.clear()  # Clear the previous plot
        self.ax.set_xlim(-0.5, 6.5)  # Set x-axis limits for the days of the week
        self.ax.set_ylim(0, 5)  # Set y-axis limits for the weeks
        self.ax.invert_yaxis()  # Invert y-axis to display weeks from top to bottom
        self.ax.axis("off")  # Hide axes

        # Get the number of days in the month and the starting day of the week
        days_in_month = calendar.monthrange(year, month)[1]
        day_of_week, _ = calendar.monthrange(year, month)

        # Loop through all days in the month
        for day in range(1, days_in_month + 1):
            x = (day_of_week + day - 1) % 7  # Calculate x-coordinate (day of the week)
            y = (
                day_of_week + day - 1
            ) // 7  # Calculate y-coordinate (week of the month)
            date = pd.Timestamp(year, month, day)

            # Check if the day is a workout day
            workout_day = not self.df[
                (self.df["Date"] == date) & (self.df["Workout(Y/N)"])
            ].empty

            if workout_day:
                # Plot workout days in green
                self.ax.plot(x, y, "go", markersize=12, zorder=5)
                self.ax.annotate(
                    day,
                    (x, y),
                    textcoords="offset points",
                    xytext=(0, 10),
                    ha="center",
                    color="green",
                    fontsize=10,
                    zorder=10,
                )
            else:
                # Plot non-workout days in grey
                self.ax.plot(x, y, "o", markersize=12, color="lightgrey", zorder=5)
                self.ax.annotate(
                    day,
                    (x, y),
                    textcoords="offset points",
                    xytext=(0, 10),
                    ha="center",
                    color="black",
                    fontsize=10,
                    zorder=10,
                )

        # Set the title of the calendar
        self.ax.set_title(f"{calendar.month_name[month]} {year}", fontsize=16, pad=20)

    def save_fig(self):
        # Save the current figure as an image
        image_path = f"static/img/calendar_{self.username}.png"
        self.fig.savefig(image_path)
        plt.close(self.fig)  # Close the figure after saving to free up memory
        return image_path

    def update_calendar(self, year, month):
        # Update the calendar for the given year and month
        self.plot_calendar(year, month)
        return self.save_fig()

    def next_month(self):
        # Move to the next month
        self.current_date += pd.DateOffset(months=1)
        return self.update_calendar(self.current_date.year, self.current_date.month)

    def prev_month(self):
        # Move to the previous month
        self.current_date -= pd.DateOffset(months=1)
        return self.update_calendar(self.current_date.year, self.current_date.month)
