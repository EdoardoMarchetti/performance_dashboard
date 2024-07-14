import os
import pandas as pd

import numpy as np
from sqlalchemy import text, MetaData, Table, inspect, create_engine
from sqlalchemy import update, and_
from sqlalchemy.dialects.sqlite import insert
from tqdm import tqdm


def create_database(db_path):
    try:
        print(f'Creazione db at {os.path.abspath(db_path)}')
        engine = create_engine(f'sqlite:///{db_path}', echo=True)
        # Test the engine by connecting to it
        with engine.connect() as connection:
            print("Successfully connected to the database.")
        print('DB creato')
        return engine
    except Exception as e:
        print(f'Error creating database: {e}')
        return None

def table_exists(engine, table_name):
    """
    Check if a table exists in the database.
    
    Args:
    - engine: SQLAlchemy engine object connected to the database.
    - table_name (str): Name of the table to check.
    
    Returns:
    - bool: True if the table exists, False otherwise.
    """
    exists = False
    try:
        with engine.connect() as con:
            query = text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            result = con.execute(query)
            exists = bool(result.fetchone())
    finally:
        engine.dispose()
    return exists



def create_table(engine, table_name, column_types, primary_keys=None):
    """
    Create a table in the database using the provided column types.

    Args:
    - engine: SQLAlchemy Engine object for database connection.
    - table_name (str): Name of the table to create.
    - column_types (dict): Dictionary with column names as keys and column types as values.
    - primary_keys (list, optional): List of columns to use as primary keys.

    Returns:
    - None
    """
    try:
        # Construct the schema part with columns and data types
        schema = ', '.join([f'`{col}` {col_type}' for col, col_type in column_types.items()])

        # Add primary keys if specified
        if primary_keys:
            primary_keys_str = ', '.join([f'`{key}`' for key in primary_keys])
            schema += f', PRIMARY KEY ({primary_keys_str})'

        # Create the query to create the table
        create_query = text(f'CREATE TABLE IF NOT EXISTS `{table_name}` ({schema})')

        # Execute the query to create the table
        with engine.connect() as con:
            con.execute(create_query)
    finally:
        engine.dispose()


        

def chunks(iterable, chunk_size):
    """Yield successive chunks of size chunk_size from iterable."""
    for i in range(0, len(iterable), chunk_size):
        yield iterable[i:i + chunk_size]


def insert_table(engine, table_name, df, chunk_size=1000, disable_pb = False):
    """
    Inserts or updates records from the DataFrame into the specified table in the database.

    Args:
    - engine: Database engine.
    - table_name (str): Name of the table in the database.
    - df (DataFrame): DataFrame containing the data to insert or update.
    - chunk_size (int): Size of each chunk for batch insertions. Default is 1000.

    Returns:
    None
    """
    try:
        # Reflect the existing table from the database
        metadata = MetaData()
        table = Table(table_name, metadata, autoload_with=engine)
        primary_keys = [key.name for key in inspect(table).primary_key]

        # Calculate total number of chunks
        total_chunks = -(-len(df) // chunk_size)  # Ceiling division

        # Start a transaction
        with engine.begin() as connection:
            # Iterate over chunks and insert records into the table
            for i, chunk in enumerate(tqdm(chunks(df, chunk_size), total=total_chunks, desc="Inserting records", disable=disable_pb)):
                records = chunk.to_dict(orient='records')
                connection.execute(table.insert().values(records))
        
        

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return False  # Raise the exception to indicate failure
    finally:
        # Close the connection to the database engine
        engine.dispose()

    return True
        

def select_from(engine, from_table, cols_to_select=[], where_condition=None):
    """
    Perform a SELECT query on the specified table in the database.

    Args:
    - engine: SQLAlchemy Engine object for database connection.
    - from_table (str): Name of the table from which to select.
    - cols_to_select (list, optional): List of column names to select. If empty, selects all columns.
    - where_condition (str, optional): WHERE condition for filtering rows in the query.

    Returns:
    - pd.DataFrame: DataFrame containing the results of the SELECT query.
    """
    select = "SELECT "

    if len(cols_to_select) == 0:
        select += '*'
    else:
        for i, col in enumerate(cols_to_select):
            if i == len(cols_to_select) - 1:
                select += f'{col} '
            else:
                select += f'{col}, '

    try:
        query = f"""{select} FROM {from_table} """
        if where_condition:
            query += f"WHERE {where_condition}"

        return pd.read_sql_query(query, con=engine)
    finally:
        engine.dispose()



def upsert_table(engine, table_name, df):
    """
    Update or insert records from the DataFrame into the specified table in the database.

    Args:
    - engine: SQLAlchemy Engine object for database connection.
    - table_name (str): Name of the table in the database.
    - df (DataFrame): DataFrame containing the data to be inserted or updated.

    Returns:
    - None
    """
    try:
        # Reflect the existing table from the database
        metadata = MetaData()
        table = Table(table_name, metadata, autoload_with=engine)
        primary_keys = [key.name for key in inspect(table).primary_key]

        # Iterate over each row in the DataFrame
        for _, record in tqdm(df.iterrows(), total=len(df)):
            # Build the insert statement
            insert_stmt = insert(table).values(record.to_dict())

            # Create a dictionary for columns to update in case of conflict
            update_dict = {
                c.name: c
                for c in insert_stmt.excluded
                if not c.primary_key
            }

            # Build the upsert statement
            do_update_stmt = insert_stmt.on_conflict_do_update(
                index_elements=primary_keys,
                set_=update_dict,
            )

            # Execute the database connection and upsert the record
            with engine.connect() as connection:
                connection.execute(do_update_stmt)
                connection.commit()  # Commit the transaction
    finally:
        # Close the connection to the database engine
        engine.dispose()




def update_table(engine, table_name, df, cols=[]):
    """
    Update records in the specified database table with data provided in the DataFrame.

    Args:
    - engine: SQLAlchemy Engine object for database connection.
    - table_name (str): Name of the table in the database.
    - df (DataFrame): DataFrame containing the data to update.
    - cols (list, optional): List of columns to update. If not specified, updates the entire row.

    Returns:
    - None
    """
    try:
        # Reflect the existing table from the database
        metadata = MetaData()
        table = Table(table_name, metadata, autoload_with=engine)
        primary_keys = [key.name for key in inspect(table).primary_key]

        # Iterate over each row in the DataFrame
        for _, record in tqdm(df.iterrows(), total=len(df)):
            # If cols is not specified, update the entire row; otherwise, update only the specified columns
            if not cols:
                update_values = record.to_dict()  # Update the entire row
            else:
                update_values = {col: record[col] for col in cols}  # Update only specified columns
                
            # Create the WHERE clause to locate the record to update
            where_clause = and_(*[getattr(table.c, key) == record[key] for key in primary_keys])

            # Build the update statement
            update_stmt = update(table).values(update_values).where(where_clause)

            # Execute the database connection and update the record
            with engine.connect() as connection:
                connection.execute(update_stmt)
                connection.commit()  # Commit the transaction
    finally:
        # Close the connection to the database engine
        engine.dispose()


def add_empty_column(engine, table_name, column_name, column_type):
    """
    Adds an empty column to the specified database table if it doesn't already exist.

    Args:
    - engine: SQLAlchemy Engine object for database connection.
    - table_name (str): Name of the table in the database.
    - column_name (str): Name of the column to add.
    - column_type (str): Data type of the new column.

    Returns:
    - bool: True if the column was created, False otherwise.
    """
    col_created = False
    try:
        # Create a connection to the database
        with engine.connect() as connection:
            # Check if the column already exists in the table
            query = text(f"PRAGMA table_info({table_name})")
            result = connection.execute(query)
            existing_columns = [row[1] for row in result.fetchall()]

            # If the column doesn't exist, execute the ALTER TABLE statement to add it
            if column_name not in existing_columns:
                alter_query = text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
                connection.execute(alter_query)
                col_created = True
            else:
                print(f"Column '{column_name}' already exists in table '{table_name}'")
    finally:
        # Dispose of the connection to the database engine
        engine.dispose()

    return col_created



def delete_column(engine, table_name, column_name):
    """
    Deletes a specified column from a table in a database.

    Args:
    - engine: SQLAlchemy Engine object for database connection.
    - table_name (str): Name of the table from which to delete the column.
    - column_name (str): Name of the column to delete from the table.

    Returns:
    None
    """
    try:
        # Create a connection to the database
        with engine.connect() as connection:
            # Check if the column exists in the table
            query = text(f"PRAGMA table_info({table_name})")
            result = connection.execute(query)
            existing_columns = [row[1] for row in result.fetchall()]

            # If the column exists, execute the ALTER TABLE statement to drop it
            if column_name in existing_columns:
                alter_query = text(f"ALTER TABLE {table_name} DROP COLUMN {column_name}")
                connection.execute(alter_query)
            else:
                print(f"Column '{column_name}' does not exist in table '{table_name}'")
    finally:
        # Dispose of the database connection
        engine.dispose()





def make_join(engine, main_table, joins):
    """
    Executes a join operation between the main table and specified tables.

    Args:
    - engine: SQLAlchemy Engine object for database connection.
    - main_table (str): Name of the main table.
    - joins (dict): Dictionary specifying the tables to join. Each key is the table name to join, and the value is a dictionary with:
        - 'type' (str): Type of join to execute ('INNER', 'LEFT', 'RIGHT', 'FULL').
        - 'on' (list): List of tuples specifying the columns to join on. Each tuple contains three elements: (column in the joining table, joining table, column in the main table).

    Returns:
    DataFrame: Resulting DataFrame from the join operation. Columns have a MultiIndex (table_name, column_name).
    """
    select = f"{main_table}.* "
    join = ''
    
    # Build the SELECT and JOIN strings based on the specifications
    for table, v in joins.items():
        select += f", {table}.*"
        join += f"{v['type']} JOIN {table} ON "
        for i, (left_on, right_table, right_on) in enumerate(v['on']):
            join += f"{table}.{left_on} = {right_table}.{right_on} "
            if i + 1 < len(v['on']):
                join += 'AND '

    # Construct the complete SQL query
    query = f"""
    SELECT {select}
    FROM {main_table}
    {join}
    """

    try:
        # Read data from the SQL query
        df = pd.read_sql_query(query, con=engine)
        
        # Find the position of the artificial column separator ':'
        fake_col_index = df.columns.get_loc("':'")

        # Split columns based on the artificial column separator
        table_names = [main_table] + list(joins.keys())  # Table names in the order they appear
        start = 0
        new_columns = []
        columns = list(df.columns)
        for i, idx in enumerate(fake_col_index):
            new_columns.append([(table_names[i], c) for c in columns[start:idx]])
            start = idx + 1
        new_columns.append([(table_names[-1], c) for c in columns[start:]])
        new_columns = sum(new_columns, [])

        # Remove the artificial column separator ':'
        df = df.drop("':'", axis=1)

        # Create a MultiIndex
        df.columns = pd.MultiIndex.from_tuples(new_columns)

    finally:
        # Close the connection to the database engine
        engine.dispose()

    return df




