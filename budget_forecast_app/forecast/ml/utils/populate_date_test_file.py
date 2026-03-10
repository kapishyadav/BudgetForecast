import pandas as pd
import numpy as np
import os


def add_testing_dates(input_filename, output_filename):
    # Read the original CSV file
    try:
        df = pd.read_csv(input_filename)
        print(f"Successfully loaded {input_filename}")
    except FileNotFoundError:
        print(f"Error: The file {input_filename} was not found.")
        return

    # Identify the actual month column name from the possibilities
    possible_month_cols = ["month", "year_month", "Month(Year)"]
    actual_month_col = next((col for col in possible_month_cols if col in df.columns), None)

    if not actual_month_col:
        print(f"Error: Could not find any of the expected month columns {possible_month_cols} in the dataset.")
        print(f"Columns found: {df.columns.tolist()}")
        return

    print(f"Found month data in column: '{actual_month_col}'")

    # Function to generate a random date for a parsed month
    def generate_random_date(month_str):
        try:
            # pd.to_datetime handles formats like '2023-07', 'July 2023', or just 'July' (defaults to current year)
            base_date = pd.to_datetime(month_str)

            # Find the total number of days in that specific month/year
            days_in_month = base_date.days_in_month

            # Pick a random day between 1 and the last day of the month
            random_day = np.random.randint(1, days_in_month + 1)

            # Replace the day and format it back to a string (YYYY-MM-DD)
            test_date = base_date.replace(day=random_day)
            return test_date.strftime('%m/%d/%Y')
        except Exception:
            # If the month is missing or unparseable, return a default or leave blank
            return None

    # Apply the function to create the new 'date' column
    df['date'] = df[actual_month_col].apply(generate_random_date)

    # Optional: Reorder columns so 'date' appears right after 'month'
    cols = df.columns.tolist()
    if 'date' in cols and actual_month_col in cols:
        cols.insert(cols.index(actual_month_col) + 1, cols.pop(cols.index('date')))
        df = df[cols]

    # Save to the new CSV
    df.to_csv(output_filename, index=False)
    print(f"Success! Data with the new 'date' column has been saved to '{output_filename}'.")


if __name__ == "__main__":
    # Define the absolute directory path
    DIRECTORY_PATH = "/Users/kapishyadavbanda/Desktop/BudgetForecast-TestFiles"
    # Define file names
    INPUT_FILE = os.path.join(DIRECTORY_PATH, "Forecast Data July TEST.csv")
    OUTPUT_FILE = os.path.join(DIRECTORY_PATH, "ForecastDataTEST_with_dates.csv")

    add_testing_dates(INPUT_FILE, OUTPUT_FILE)