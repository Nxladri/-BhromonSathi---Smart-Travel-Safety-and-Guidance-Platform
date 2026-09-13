import pyodbc
from config import get_db_connection_string

def get_db_connection():
    conn_str = get_db_connection_string()
    return pyodbc.connect(conn_str)