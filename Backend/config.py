DB_CONFIG = {
    "driver" : "ODBC Driver 17 for SQL Server",
    "server" : "NILADRI\SQLEXPRESS",
    "database" : "SmartTravel",
    "trusted_connection" : "yes",
    # "uid": "your_username",
    # "pwd": "your_password",
}

def get_db_connection_string():
    if DB_CONFIG.get("trusted_connection", "").lower() == "yes":
        return (
            f"DRIVER={{{DB_CONFIG['driver']}}};"
            f"SERVER={DB_CONFIG['server']};"
            f"DATABASE={DB_CONFIG['database']};"
            "Trusted_Connection=yes;"
        )
    else:
        return (
            f"DRIVER={{{DB_CONFIG['driver']}}};"
            f"SERVER={DB_CONFIG['server']};"
            f"DATABASE={DB_CONFIG['database']};"
            f"UID={DB_CONFIG.get('uid', '')};"
            f"PWD={DB_CONFIG.get('pwd', '')};"
        )