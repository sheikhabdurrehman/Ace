import sqlite3
import pandas as pd
from datetime import datetime, timedelta

def create_and_append_to_warehouse_rack(df, db_name='warehouse.db'):
    """
    Dynamically creates the warehouse_rack table based on the DataFrame headers
    and appends the data to the SQLite database.

    Parameters:
        df (pd.DataFrame): The DataFrame containing the data to be appended.
        db_name (str): The name of the SQLite database file. Defaults to 'warehouse.db'.
    """
    if 'Frame_Timestamp' in df.columns:
        df['Frame_Timestamp'] = df['Frame_Timestamp'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'))

    # Connect to the SQLite database
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

    # Extract columns and types from the DataFrame
    columns = df.columns
    column_types = []
    for col in columns:
        if col == 'Frame_Timestamp':
            column_types.append(f"{col} DATETIME")
        else:
            column_types.append(f"{col} INTEGER")

    # Create the table with dynamic columns
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS warehouse_rack (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        {', '.join(column_types)}
    )
    """
    cur.execute(create_table_query)
    conn.commit()

    # Insert the DataFrame data into the database
    insert_query = f"""
    INSERT INTO warehouse_rack ({', '.join(columns)})
    VALUES ({', '.join(['?' for _ in columns])})
    """
    for _, row in df.iterrows():
        cur.execute(insert_query, tuple(row))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

    print("Data appended to 'warehouse_rack' table successfully.")

def data_updates(db_name='warehouse.db', custom_row=None):
    """
    Retrieves the last 30 rows from the warehouse_rack table and returns the stock count
    from the latest row.
    
    Parameters:
        db_name (str): The name of the SQLite database file. Defaults to 'warehouse.db'.
    
    Returns:
        dict: A dictionary containing the stock counts of each item from the latest row.
    """
    # Connect to the SQLite database
    conn = sqlite3.connect(db_name)
    
    # Retrieve the last 30 rows from the warehouse_rack table
    query = """
    SELECT *
    FROM warehouse_rack
    ORDER BY id DESC
    LIMIT 30
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    conn = sqlite3.connect('warehouse.db')
    cursor = conn.cursor()

    # Execute a query to fetch all rows from the table
    cursor.execute("SELECT * FROM items_min_count")

    # Fetch all rows and convert them into a dictionary
    rows = cursor.fetchall()
    min_result = {row[0]: row[1] for row in rows}

    
    # Reverse the DataFrame to be in chronological order
    df = df.iloc[::-1].reset_index(drop=True)
    
    # Retrieve the latest stock count from the last row
    latest_stock = df.iloc[-1][['coke', 'lays', 'milkpack', 'pepsi', 'water']]
    
    # Convert the latest stock count to a dictionary
    stock_dict = latest_stock.to_dict()

    # Creating dataframes from dictionaries
    stock_df = pd.DataFrame(list(stock_dict.items()), columns=['Name', 'Counts'])
    min_df = pd.DataFrame(list(min_result.items()), columns=['Name', 'Threshold'])
    if custom_row != None:
        stock_df = pd.DataFrame(list(custom_row.items()), columns=['Name', 'Counts'])
    # Merging dataframes on the 'Name' column
    combined_df = pd.merge(stock_df, min_df, on='Name')
    return combined_df