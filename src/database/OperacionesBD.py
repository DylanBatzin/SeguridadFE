import mariadb
from werkzeug.security import check_password_hash
from database.ConexionDB import conectar_a_bd  
from werkzeug.security import generate_password_hash

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

def obtener_medicamentos(ProductID=None):
    try:
        conn = conectar_a_bd()
        cur = conn.cursor()

        if ProductID:
            query = "SELECT ProductID, ProductName, Description, Price, Stock, Category, IsActive FROM Products WHERE ProductID = ?"
            cur.execute(query, (ProductID,))
        else:      
            query = "SELECT ProductID, ProductName, Description, Price, Stock, Category, IsActive FROM Products"
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
                'Category': row[5],
                'IsActive':row[6]
            })
        
        return productos

    except mariadb.Error as e:
        print(f"Error al realizar la consulta: {e}")
        return []
    finally:
        conn.close()

def obtener_empleados(employee_id=None):
    try:
        conn = conectar_a_bd()
        cur = conn.cursor()

        # Consulta base
        if employee_id:
            # Consulta para obtener un empleado específico
            query = "SELECT EmployeeID, DPI, FirstName, LastName, CreditLimit, AvailableBalance, PhoneNumber, Email, UserType FROM Employees WHERE EmployeeID = ?"
            cur.execute(query, (employee_id,))
        else:
            # Consulta para obtener todos los empleados
            query = "SELECT EmployeeID, DPI, FirstName, LastName, CreditLimit, AvailableBalance, PhoneNumber, Email,UserType FROM Employees"
            cur.execute(query)

        empleados = []
        rows = cur.fetchall()
        for row in rows:
            empleados.append({
                'EmployeeID': row[0],
                'DPI': row[1],
                'FirstName': row[2],
                'LastName': row[3],
                'CreditLimit': row[4],
                'AvailableBalance': row[5],
                'PhoneNumber': row[6],
                'Email': row[7],
                'UserType': row[8]
            })

        return empleados if empleados else None

    except mariadb.Error as e:
        print(f"Error al realizar la consulta: {e}")
        return None
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

def insertar_empleado(dpi, first_name, last_name, email, phone_number, password, credit_limit, available_balance, user_type='STAFF'):
    try:
        conn = conectar_a_bd()
        cur = conn.cursor()

        # Generar el hash de la contraseña
        hashed_password = generate_password_hash(password)

        # Consulta de inserción
        query = """
            INSERT INTO Employees (DPI, FirstName, LastName, Email, PhoneNumber, PasswordHash, CreditLimit, AvailableBalance, UserType)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        # Ejecutar la consulta con los valores proporcionados
        cur.execute(query, (dpi, first_name, last_name, email, phone_number, hashed_password, credit_limit, available_balance, user_type))

        # Guardar los cambios en la base de datos
        conn.commit()

        print("Empleado insertado correctamente.")
        return True  # Retornar True si la inserción fue exitosa

    except mariadb.Error as e:
        print(f"Error al insertar el empleado: {e}")
        return False  # Retornar False si ocurrió algún error

    finally:
        conn.close()

def insertar_products( ProductName, Description, Price, Stock, Category, IsActive):
    try:
        conn = conectar_a_bd()
        cur = conn.cursor()


        # Consulta de inserción
        query = """
            INSERT INTO `products` ( `ProductName`, `Description`, `Price`, `Stock`, `Category`, `IsActive`) VALUES(?, ?, ?, ?, ?, ?)
        """

        # Ejecutar la consulta con los valores proporcionados
        cur.execute(query, (ProductName, Description, Price, Stock, Category, IsActive))

        # Guardar los cambios en la base de datos
        conn.commit()

        print("Empleado insertado correctamente.")
        return True  # Retornar True si la inserción fue exitosa

    except mariadb.Error as e:
        print(f"Error al insertar el empleado: {e}")
        return False  # Retornar False si ocurrió algún error

    finally:
        conn.close()


def editar_empleado(employee_id, first_name=None, last_name=None, email=None, phone_number=None, password=None, credit_limit=None, available_balance=None, user_type=None):
    try:
        conn = conectar_a_bd()
        cur = conn.cursor()

        # Lista para almacenar los campos que se deben actualizar
        fields_to_update = []
        values_to_update = []

        # Verificar qué valores han sido proporcionados y agregarlos a la consulta
        if first_name:
            fields_to_update.append("FirstName = ?")
            values_to_update.append(first_name)
        if last_name:
            fields_to_update.append("LastName = ?")
            values_to_update.append(last_name)
        if email:
            fields_to_update.append("Email = ?")
            values_to_update.append(email)
        if phone_number:
            fields_to_update.append("PhoneNumber = ?")
            values_to_update.append(phone_number)
        if password:
            hashed_password = generate_password_hash(password)
            fields_to_update.append("PasswordHash = ?")
            values_to_update.append(hashed_password)
        if credit_limit is not None:
            fields_to_update.append("CreditLimit = ?")
            values_to_update.append(credit_limit)
        if available_balance is not None:
            fields_to_update.append("AvailableBalance = ?")
            values_to_update.append(available_balance)
        if user_type:
            fields_to_update.append("UserType = ?")
            values_to_update.append(user_type)

        # Si no hay campos a actualizar, no hacemos nada
        if not fields_to_update:
            print("No se proporcionaron campos para actualizar.")
            return False

        # Construir la consulta SQL dinámica
        query = f"""
            UPDATE Employees
            SET {", ".join(fields_to_update)}
            WHERE EmployeeID = ?
        """
        values_to_update.append(employee_id)

        # Ejecutar la consulta de actualización
        cur.execute(query, values_to_update)

        # Guardar los cambios en la base de datos
        conn.commit()

        print("Empleado actualizado correctamente.")
        return True  # Retornar True si la actualización fue exitosa

    except mariadb.Error as e:
        print(f"Error al actualizar el empleado: {e}")
        return False  # Retornar False si ocurrió algún error

    finally:
        conn.close()

def editar_producto(product_id, ProductName=None, Description=None, Price=None, Stock=None, Category=None, IsActive=None):
    try:
        # Conectar a la base de datos
        conn = conectar_a_bd()
        cur = conn.cursor()

        # Lista para almacenar los campos que se deben actualizar
        fields_to_update = []
        values_to_update = []

        # Verificar qué valores han sido proporcionados y agregarlos a la consulta
        if ProductName:
            fields_to_update.append("ProductName = ?")
            values_to_update.append(ProductName)
        if Description:
            fields_to_update.append("Description = ?")
            values_to_update.append(Description)
        if Price is not None:
            fields_to_update.append("Price = ?")
            values_to_update.append(Price)
        if Stock is not None:
            fields_to_update.append("Stock = ?")
            values_to_update.append(Stock)
        if Category:
            fields_to_update.append("Category = ?")
            values_to_update.append(Category)
        if IsActive is not None:
            fields_to_update.append("IsActive = ?")
            values_to_update.append(IsActive)

        # Si no hay campos a actualizar, no hacemos nada
        if not fields_to_update:
            print("No se proporcionaron campos para actualizar.")
            return False

        # Construir la consulta SQL dinámica
        query = f"""
            UPDATE products
            SET {", ".join(fields_to_update)}
            WHERE ProductID = ?
        """
        values_to_update.append(product_id)

        # Ejecutar la consulta de actualización
        cur.execute(query, values_to_update)

        # Guardar los cambios en la base de datos
        conn.commit()

        print("Producto actualizado correctamente.")
        return True  # Retornar True si la actualización fue exitosa

    except mariadb.Error as e:
        print(f"Error al actualizar el producto: {e}")
        return False  # Retornar False si ocurrió algún error

    finally:
        # Cerrar la conexión a la base de datos
        conn.close()

def eliminar_producto(ProductID):
    try:
        # Conectar a la base de datos
        conn = conectar_a_bd()
        cur = conn.cursor()

        # Consulta para eliminar el producto basado en el ProductID
        query = "DELETE FROM Products WHERE ProductID = ?"
        
        # Ejecutar la consulta
        cur.execute(query, (ProductID,))
        
        # Confirmar los cambios en la base de datos
        conn.commit()

        # Verificar si algún registro fue afectado (si se eliminó el producto)
        if cur.rowcount > 0:
            return True  # Retornar True si la eliminación fue exitosa
        else:
            return False  # Retornar False si no se encontró el producto

    except mariadb.Error as e:
        print(f"Error al eliminar el producto: {e}")
        return False  # Retornar False si ocurrió algún error

    finally:
        # Cerrar la conexión a la base de datos
        conn.close()

def eliminar_emp(employee_id):
    try:
        # Conectar a la base de datos
        conn = conectar_a_bd()
        cur = conn.cursor()

        # Consulta para eliminar el producto basado en el ProductID
        query = "DELETE FROM Employees WHERE EmployeeID = ?"
        
        # Ejecutar la consulta
        cur.execute(query, (employee_id,))
        
        # Confirmar los cambios en la base de datos
        conn.commit()

        # Verificar si algún registro fue afectado (si se eliminó el producto)
        if cur.rowcount > 0:
            return True  # Retornar True si la eliminación fue exitosa
        else:
            return False  # Retornar False si no se encontró el producto

    except mariadb.Error as e:
        print(f"Error al eliminar el producto: {e}")
        return False  # Retornar False si ocurrió algún error

    finally:
        # Cerrar la conexión a la base de datos
        conn.close()

def insertar_log_auditoria(employee_id, accion, detalles_accion):
    try:
        # Conectar a la base de datos
        conn = conectar_a_bd()
        cur = conn.cursor()

        # Mapeo de acciones basado en el número proporcionado
        acciones = {
            1: 'Insert',
            2: 'Update',
            3: 'Delete',
            4: 'View',
            6: 'Purchase'
        }

        # Obtener la acción correspondiente según el número proporcionado
        accion_str = acciones.get(accion, 'Unknown')  # Si no se encuentra, marcar como 'Unknown'

        # Consulta de inserción
        query = """
            INSERT INTO auditlogs (EmployeeID, Action, ActionDetails) 
            VALUES (?, ?, ?)
        """

        # Ejecutar la consulta con los valores proporcionados
        cur.execute(query, (employee_id, accion_str, detalles_accion))

        # Guardar los cambios en la base de datos
        conn.commit()

        print("Log de auditoría insertado correctamente.")
        return True  # Retornar True si la inserción fue exitosa

    except mariadb.Error as e:
        print(f"Error al insertar en el log de auditoría: {e}")
        return False  # Retornar False si ocurrió algún error

    finally:
        conn.close()
