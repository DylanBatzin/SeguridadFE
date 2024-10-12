import mariadb 
import sys
def conectar_a_bd():
    try:
        # Establecer la conexión con MariaDB
        conn = mariadb.connect(
            user="CRUDS",
            password="Dyton1209",
            host="127.0.0.1",
            port=3306,  # Puerto predeterminado de MariaDB
            database="EmployeeCreditDB"  # Reemplaza con el nombre de tu base de datos
        )
        return conn
    except mariadb.Error as e:
        print(f"Error al conectar a MariaDB: {e}")
        sys.exit(1)

if __name__ == "__main__":
    conectar_a_bd()