import sqlite3

# Create a new SQLite database named "vacation_packages"
db_name = "vacation_packages.db"
conn = sqlite3.connect(db_name)
cursor = conn.cursor()

# Create the "packages" table with the specified columns
create_packages_table_query = """
CREATE TABLE packages (
    destination TEXT,
    Relaxing BOOLEAN,
    Adventurous BOOLEAN,
    Exploratory BOOLEAN,
    Dining BOOLEAN,
    Beach BOOLEAN,
    Urban BOOLEAN,
    Wilderness BOOLEAN,
    Alone BOOLEAN,
    "With Significant Other" BOOLEAN,
    "With Family" BOOLEAN,
    "With Friends" BOOLEAN
);
"""

cursor.execute(create_packages_table_query)

# Create the "tones" table with the "style" and "tone" columns
create_tones_table_query = """
CREATE TABLE tones (
    style TEXT,
    tone TEXT
);
"""

cursor.execute(create_tones_table_query)

# Commit the changes and close the connection
conn.commit()
conn.close()

print(f"Database '{db_name}' created with the 'packages' and 'tones' tables.")
