import pandas as pd
import calendar
import matplotlib.pyplot as plt
from pathlib import Path


class CalendarVisualizer:
    def __init__(self, data_path, username, user_calendars):
        """
        Initialize the CalendarVisualizer.

        Parameters:
        - data_path: Path to the Excel file.
        - username: Username to identify the data.
        - user_calendars: Global dictionary storing user CalendarVisualizer instances.

        """

        self.data_path = data_path
        self.username = username
        self.sheet_name = f"workout_data_{username}"
        self.user_calendars = user_calendars

        # Check if the user's data is already in user_calendars
        if username in self.user_calendars:
            # Reuse the existing CalendarVisualizer instance
            self.df = self.user_calendars[username].df
        else:
            # Otherwise, try to load the data from the Excel file
            try:
                df = pd.read_excel(data_path, sheet_name=self.sheet_name)
                df["Date"] = pd.to_datetime(
                    df["Date"], errors="coerce"
                )  # Handle invalid dates
                df["Workout(Y/N)"] = df["Workout(Y/N)"].map({"Y": True, "N": False})
                df.dropna(subset=["Date"], inplace=True)  # Drop rows with invalid dates

                self.df = df
                self.user_calendars[username] = self  # Cache this instance for reuse
            except Exception as e:
                print(f"Error loading data for {username}: {e}")
                self.df = pd.DataFrame(columns=["Date", "Workout(Y/N)"])

        # Set the initial date
        self.current_date = (
            self.df["Date"].min() if not self.df.empty else pd.Timestamp.today()
        )

        # Initialize the plot
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.update_calendar(self.current_date.year, self.current_date.month)

    def plot_calendar(self, year, month):
        self.ax.clear()  # Clear the previous month's calendar
        self.ax.set_xlim(-0.5, 6.5)  # Set x-axis for 7 days (Monday to Sunday)
        self.ax.set_ylim(0, 5)  # Set y-axis for up to 5 weeks
        self.ax.invert_yaxis()  # Invert y-axis so the calendar starts at the top
        self.ax.axis("off")  # Hide the axes for a cleaner calendar look

        days_in_month = calendar.monthrange(year, month)[1]
        day_of_week, _ = calendar.monthrange(year, month)

        for day in range(1, days_in_month + 1):
            x = (day_of_week + day - 1) % 7  # Calculate the x-coordinate
            y = (day_of_week + day - 1) // 7  # Calculate the y-coordinate
            date = pd.Timestamp(year, month, day)

            # Check if this is a workout day
            workout_day = not self.df[
                (self.df["Date"] == date) & (self.df["Workout(Y/N)"])
            ].empty

            if workout_day:
                self.ax.plot(
                    x, y, "go", markersize=12, zorder=5
                )  # Mark workout days in green
                self.ax.annotate(
                    day,
                    (x, y),
                    textcoords="offset points",
                    xytext=(0, 10),  # Offset text for readability
                    ha="center",
                    color="green",
                    fontsize=10,
                    zorder=10,
                )
            else:
                self.ax.plot(
                    x, y, "o", markersize=12, color="lightgrey", zorder=5
                )  # Non-workout days
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

        self.ax.set_title(f"{calendar.month_name[month]} {year}", fontsize=16, pad=20)

    def save_fig(self):
        # Save the calendar as an image
        image_path = f"static/img/calendar_{self.username}.png"
        Path("static/img").mkdir(
            parents=True, exist_ok=True
        )  # Ensure the directory exists
        self.fig.savefig(image_path)
        plt.close(self.fig)  # Close the figure to free up memory
        return image_path

    def update_calendar(self, year, month):
        # Update and save the calendar for the given month and year
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
