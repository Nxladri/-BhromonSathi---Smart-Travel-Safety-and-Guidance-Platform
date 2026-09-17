import psycopg2
from config import get_db_connection_string

def get_db_connection():
    return psycopg2.connect(get_db_connection_string())