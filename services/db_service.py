import pyodbc

def get_db_connection():
    conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=223.177.191.70,1433;"
        "DATABASE=posbhaji;"
        "UID=sa;"
        "PWD=485526365;"
        "Encrypt=no;"
        "TrustServerCertificate=yes;"
        "Connection Timeout=30;"
    )

    return pyodbc.connect(conn_str)
