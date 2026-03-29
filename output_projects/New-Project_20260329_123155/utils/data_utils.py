import sqlite3
from typing import Tuple

def connect_to_db() -> sqlite3.Connection:
    """
    Connect to the SQLite database.

    Returns:
        A connection object to the SQLite database.
    """
    conn = sqlite3.connect('case_intelli.db')
    return conn

def execute_query(query: str, params: Tuple = ()) -> list:
    """
    Execute a SQL query on the database.

    Args:
        query (str): The SQL query to execute.
        params (Tuple): The parameters to pass to the query.

    Returns:
        A list of rows returned by the query.
    """
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows