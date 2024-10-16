import mariadb
from werkzeug.security import check_password_hash
from database.ConexionDB import conectar_a_bd  

def validar_login(dpi, password):
    try:
        conn = conectar_a_bd()  
        cur = conn.cursor()

        
        query = "SELECT PasswordHash FROM Employees WHERE dpi = ?"
        cur.execute(query, (dpi,))

        
        row = cur.fetchone()

        if row:
            stored_hashed_password = row[0] 
            
            if check_password_hash(stored_hashed_password, password):
                return True  
            else:
                return False 
        else:
            return False 

    except mariadb.Error as e:
        print(f"Error al realizar la consulta: {e}")
        return False
    finally:
        conn.close()  

def obtener_datos_home(dpi):
    try:
        conn = conectar_a_bd()
        cur = conn.cursor()

        # Consulta para obtener los datos del empleado según el DPI
        query = "SELECT FirstName, CreditLimit, AvailableBalance, UserType FROM Employees WHERE dpi = ?"
        cur.execute(query, (dpi,))
        
        row = cur.fetchone()

        if row:
            # Devolver un diccionario con los datos del empleado
            return {
                'FirstName': row[0],  
                'CreditLimit': row[1],     
                'AvailableBalance': row[2] ,
                'UserType' :  row[3].strip().upper()          
            }
        else:
            return None  # Si no se encuentra el empleado

    except mariadb.Error as e:
        print(f"Error al realizar la consulta: {e}")
        return None
    finally:
        conn.close()

def obtener_medicamentos():
    try:
        conn = conectar_a_bd()
        cur = conn.cursor()

        # Consulta para obtener todos los productos
        query = "SELECT ProductID, ProductName, Description, Price, Stock, Category FROM Products"
        cur.execute(query)
        
        rows = cur.fetchall()

        productos = []
        for row in rows:
            productos.append({
                'ProductID': row[0],
                'ProductName': row[1],
                'Description': row[2],
                'Price': row[3],
                'Stock': row[4],
                'Category': row[5]
            })
        
        return productos

    except mariadb.Error as e:
        print(f"Error al realizar la consulta: {e}")
        return []
    finally:
        conn.close()


def obtener_datos_usuario(dpi):
    try:
        conn = conectar_a_bd()
        cur = conn.cursor()

        # Consulta para obtener los datos del empleado según el DPI
        query = "SELECT EmployeeID, PhoneNumber, Email FROM Employees WHERE dpi = ?"
        cur.execute(query, (dpi,))
        
        row = cur.fetchone()

        if row:
            # Devolver un diccionario con los datos del empleado
            return {
                'employee_id': row[0],  
                'telefono': row[1],     
                'email': row[2]         
            }
        else:
            return None  # Si no se encuentra el empleado

    except mariadb.Error as e:
        print(f"Error al realizar la consulta: {e}")
        return None
    finally:
        conn.close()

import uuid
from datetime import datetime, timedelta

def generar_token(employee_id, token_type):
    try:
        conn = conectar_a_bd()
        cur = conn.cursor()

        # Generar un valor de token único (puedes ajustar esto según tus necesidades)
        token_value = str(uuid.uuid4())[:8]  # Token de 8 caracteres

        # Definir fecha de expiración (por ejemplo, 10 minutos después de la creación)
        expires_at = datetime.now() + timedelta(minutes=10)

        # Insertar el nuevo token en la base de datos
        query = """
        INSERT INTO Tokens (EmployeeID, TokenValue, TokenType, ExpiresAt) 
        VALUES (?, ?, ?, ?)
        """
        cur.execute(query, (employee_id, token_value, token_type, expires_at))
        conn.commit()

        return token_value  # Devolver el valor del token generado

    except mariadb.Error as e:
        print(f"Error al generar el token: {e}")
        return None
    finally:
        conn.close()
def validar_token(dpi, token_value):
    try:
        conn = conectar_a_bd()
        cur = conn.cursor()

        # Consulta para obtener el EmployeeID a partir del DPI
        query = "SELECT EmployeeID FROM Employees WHERE dpi = ?"
        cur.execute(query, (dpi,))
        row = cur.fetchone()

        if not row:
            return False  # Si no existe el empleado, retornar False

        employee_id = row[0]

        # Consulta para validar el token (que no haya expirado y no esté usado)
        query = """
        SELECT TokenID, ExpiresAt FROM Tokens 
        WHERE EmployeeID = ? AND TokenValue = ? AND IsUsed = FALSE
        """
        cur.execute(query, (employee_id, token_value))
        token_row = cur.fetchone()

        if not token_row:
            return False  # Token inválido o ya usado

        token_id = token_row[0]
        expires_at = token_row[1]

        # Verificar si el token ha expirado
        if datetime.now() > expires_at:
            return False  # Token expirado

        # Si el token es válido, marcarlo como usado
        query = "UPDATE Tokens SET IsUsed = TRUE WHERE TokenID = ?"
        cur.execute(query, (token_id,))
        conn.commit()

        return True  # Token válido y marcado como usado

    except mariadb.Error as e:
        print(f"Error al validar el token: {e}")
        return False
    finally:
        conn.close()
