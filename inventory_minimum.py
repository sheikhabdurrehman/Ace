import sqlite3

# List of items
items = ['coke', 'lays', 'milkpack', 'pepsi', 'water']

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('warehouse.db')
cursor = conn.cursor()

# Delete the table if it already exists
cursor.execute("DROP TABLE IF EXISTS items_min_count")

# Create the table
cursor.execute("""
CREATE TABLE items_min_count (
    items TEXT,
    minimum INTEGER
)
""")

# Insert items with user-provided minimum counts
for item in items:
    minimum = int(input(f"Enter the minimum count for {item}: "))
    cursor.execute("INSERT INTO items_min_count (items, minimum) VALUES (?, ?)", (item, minimum))

# Commit the transaction and close the connection
conn.commit()
conn.close()
