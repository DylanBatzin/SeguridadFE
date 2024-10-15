import mariadb
import sys

def conectar_a_bd():
    try:
        conn = mariadb.connect(
            user="CRUDS",
            password="Dyton1209",
            host="127.0.0.1",
            port=3306,
            database="EmployeeCreditDB"
        )
        return conn
    except mariadb.Error as e:
        print(f"Error al conectar a MariaDB: {e}")
        sys.exit(1)
