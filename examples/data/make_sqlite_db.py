import csv
import sqlite3

# Path to the CSV file
csv_file_path = "./synthetic_people_data.csv"

# Connect to a SQLite database (will be created if it doesn't exist)
conn = sqlite3.connect("people.sqlite")
cur = conn.cursor()

# Create a table
cur.execute(
    """
CREATE TABLE IF NOT EXISTS people (
    id INTEGER PRIMARY KEY,
    Name TEXT,
    Age INTEGER,
    Location TEXT,
    Occupation TEXT,
    Email TEXT
)
"""
)

# Read data from the CSV file
with open(csv_file_path, "r") as csvfile:
    csvreader = csv.reader(csvfile)
    next(csvreader)  # Skip the header row
    for row in csvreader:
        # Insert each row into the database
        cur.execute(
            """
        INSERT INTO people (Name, Age, Location, Occupation, Email)
        VALUES (?, ?, ?, ?, ?)
        """,
            row,
        )

# Commit changes and close the connection
conn.commit()
conn.close()

print("Data imported into SQLite database successfully.")
