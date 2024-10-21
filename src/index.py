from flask import * 
import re
from config import config  
from tokensmethods import *
from database.OperacionesBD import *
from jwt_auth import jwt, init_jwt  
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity,
    set_access_cookies, unset_jwt_cookies
)
from validardpi import validar_dpi
from twilio.rest import Client


app = Flask(__name__)

app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_ACCESS_COOKIE_PATH'] = '/'
app.config['JWT_COOKIE_SECURE'] = False  # Cambia a True en producción si usas HTTPS
app.config['JWT_COOKIE_CSRF_PROTECT'] = False  # Maneja los tokens CSRF si lo necesitas  
app.config.from_object(config['development'])
init_jwt(app)

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        DPI = request.form['dpi']
        contra = request.form['password']

        if validar_login(DPI, contra): 
            session['dpi'] = DPI  # Guardamos el DPI en la sesión temporalmente

            # Obtenemos los datos del usuario (id, teléfono y correo)
            user_data = obtener_datos_usuario(DPI)
            if user_data:
                session['employee_id'] = user_data['employee_id']
                session['telefono'] = user_data['telefono']
                session['email'] = user_data['email']

                return render_template('token.html', telefono=user_data['telefono'], email=user_data['email'])
            else:
                flash("Error al obtener los datos del usuario", "danger")
                return redirect(url_for('login'))
        else:
            flash("Usuario o contraseña incorrectos", "danger") 
            return redirect(url_for('login'))  
    else:
        return render_template('index.html')

@app.route('/generate_token', methods=['POST'])
def generate_token_route():
    if 'dpi' not in session:
        return redirect(url_for('login'))

    employee_id = session.get('employee_id')
    token_type = request.form.get('token_type')  # Puede ser 'SMS' o 'EMAIL'
    
    # Generar el token
    token_value = generar_token(employee_id, token_type)

    if token_value:
        # Print the token for debugging purposes
        print(f"Generated token: {token_value} via {token_type}")

        if token_type == 'SMS':
            telefono = session.get('telefono')
            #enviar_sms(telefono, token_value)
        elif token_type == 'EMAIL':
            email = session.get('email')
            enviar_email(email, token_value)

        # Redirige al usuario a validartoken.html para ingresar el token
        return redirect(url_for('validate_token'))  # Redirige a la página de validación de token
    else:
        flash("Error al generar el token.", "danger")
        return redirect(url_for('login'))

@app.route('/validate_token', methods=['POST', 'GET'])
def validate_token():
    if 'dpi' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        token_value = request.form.get('token')  # Obtener el token ingresado
        dpi = session.get('dpi')  # Obtener el DPI del usuario de la sesión

        # Validar el token utilizando la función `validar_token`
        if validar_token(dpi, token_value):
            # Generar JWT
            access_token = create_access_token(identity=dpi)
            resp = make_response(redirect(url_for('home')))
            set_access_cookies(resp, access_token)
            session.clear()  # Limpiar la sesión
            return resp  # Retornar la respuesta con el JWT en las cookies
        else:
            flash("Token inválido o expirado.", "danger")
            return render_template('validartoken.html')  # Mantén el formulario visible para reingresar el token
    else:
        return render_template('validartoken.html')

@app.route('/home', methods=['GET', 'POST'])
@jwt_required()
def home():
    dpi = get_jwt_identity()
    # Retrieve user data from the database
    user_data = obtener_datos_home(dpi)
    
    if user_data:
        nombre = user_data.get('FirstName')
        creditolim = user_data.get('CreditLimit')
        credito = user_data.get('AvailableBalance')
        rol = user_data.get('UserType')
    else:
        # Handle the case where no data is found
        nombre = None
        creditolim = None
        credito = None
        rol = None
        flash("No se encontraron datos para el usuario.", "danger")
        # Optionally, you can redirect the user to another page
        return redirect(url_for('login'))
    
    # Redirigir a la plantilla correcta según el rol del usuario
    if rol == 'ADMIN':
        return render_template('homeAdmin.html')
    elif rol == 'STAFF':
        return render_template('homeEmp.html', nombre=nombre, creditolim=creditolim, credito=credito)
    else:
        # Si el rol no coincide con ninguno, se puede manejar un rol por defecto o mostrar un mensaje
        flash("Rol no autorizado.", "danger")
        return redirect(url_for('login'))



@app.route('/logout')
def logout():
    resp = make_response(redirect(url_for('login')))
    unset_jwt_cookies(resp)
    flash("Has cerrado sesión.", "success")
    return resp

@app.route('/productos', methods=['GET', 'POST'])
@jwt_required()
def productos():
    # Traer productos de la base de datos
    productos = obtener_medicamentos()

    if request.method == 'GET':
        # Generar tabla HTML con los productos
        if productos:
            html_table = "<table class='table table-dark'>"
            html_table += "<tr><th>ID</th><th>Nombre</th><th>Descripción</th><th>Precio</th><th>Stock</th><th>Categoría</th><th>Acciones</th></tr>"
            for producto in productos:
                html_table += f"<tr><td>{producto['ProductID']}</td><td>{producto['ProductName']}</td><td>{producto['Description']}</td><td>{producto['Price']}</td><td>{producto['Stock']}</td><td>{producto['Category']}</td><td>"
                html_table += f"<form action='/productos' method='POST' style='display:inline;'>"
                html_table += f"<button class='btn btn-outline-secondary' type='submit' name='editar' value='{producto['ProductID']}'>Editar</button>"
                html_table += f"</form>"
                html_table += f"<form action='/productos' method='POST' style='display:inline;'>"
                html_table += f"<button class='btn btn-outline-danger' type='submit' name='eliminar' value='{producto['ProductID']}'>Eliminar</button>"
                html_table += f"</form></td></tr>"
            html_table += "</table>"
        else:
            html_table = "<p>No se encontraron productos.</p>"

        return render_template('tablas.html', html_table=html_table)

    elif request.method == 'POST':
        if 'editar' in request.form:
            product_id = request.form['editar']
            return redirect(url_for('editarproduct', product_id=product_id))

        # Manejo de eliminación
        elif 'eliminar' in request.form:
            product_id = request.form['eliminar']
            eliminar_producto(product_id)
            return redirect(url_for('productos')) 

@app.route('/viewemp', methods=['GET', 'POST'])
@jwt_required()
def verempleado():
    empleados = obtener_empleados()

    if request.method == 'GET':
        if empleados:
            html_table = "<table class='table table-dark'>"
            html_table += "<tr><th>ID</th><th>DPI</th><th>Nombre</th><th>Apellido</th><th>Límite de Crédito</th><th>Balance Disponible</th><th>Acciones</th></tr>"
            for empleado in empleados:
                html_table += f"<tr><td>{empleado['EmployeeID']}</td><td>{empleado['DPI']}</td><td>{empleado['FirstName']}</td><td>{empleado['LastName']}</td><td>{empleado['CreditLimit']}</td><td>{empleado['AvailableBalance']}</td><td>"
                html_table += f"<form action='/viewemp' method='POST' style='display:inline;'>"
                html_table += f"<button class='btn btn-outline-secondary' type='submit' name='editar' value='{empleado['EmployeeID']}'>Editar</button>"
                html_table += f"</form>"
                html_table += f"<form action='/viewemp' method='POST' style='display:inline;'>"
                html_table += f"<button class='btn btn-outline-danger' type='submit' name='eliminar' value='{empleado['EmployeeID']}'>Eliminar</button>"
                html_table += f"</form></td></tr>"
            html_table += "</table>"
        else:
            html_table = "<p>No se encontraron empleados.</p>"

        return render_template('tablas.html', html_table=html_table)

    elif request.method == 'POST':
        if 'editar' in request.form:
            employee_id = request.form['editar']
            return redirect(url_for('editarempleado', employee_id=employee_id))

        elif 'eliminar' in request.form:
            employee_id = request.form['eliminar']
            eliminar_emp(employee_id)
            return redirect(url_for('verempleado'))


@app.route('/addempleado', methods=['GET', 'POST'])
@jwt_required()
def addempleado():
    if request.method == 'GET':
        # Generate the HTML form dynamically
        html_form = """
        <form action="/addempleado" method="POST">
            <div class="form-group">
                <label for="dpi">DPI</label>
                <input type="text" id="dpi" name="DPI" class="form-control" required>
            </div>
            <div class="form-group">
                <label for="firstname">First Name</label>
                <input type="text" id="firstname" name="FirstName" class="form-control" required>
            </div>
            <div class="form-group">
                <label for="lastname">Last Name</label>
                <input type="text" id="lastname" name="LastName" class="form-control" required>
            </div>
            <div class="form-group">
                <label for="email">Email</label>
                <input type="email" id="email" name="Email" class="form-control" required>
            </div>
            <div class="form-group">
                <label for="phonenumber">Phone Number</label>
                <input type="text" id="phonenumber" name="PhoneNumber" class="form-control">
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" class="form-control" required>
            </div>
            <div class="form-group">
                <label for="confirm_password">Confirm Password</label>
                <input type="password" id="confirm_password" name="ConfirmPassword" class="form-control" required>
            </div>
            <div class="form-group">
                <label for="creditlimit">Credit Limit</label>
                <input type="number" step="0.01" id="creditlimit" name="CreditLimit" class="form-control" required>
            </div>
            <div class="form-group">
                <label for="availablebalance">Available Balance</label>
                <input type="number" step="0.01" id="availablebalance" name="AvailableBalance" class="form-control" required>
            </div>
            <div class="form-group">
                <label for="usertype">User Type</label>
                <select id="usertype" name="UserType" class="form-control" required>
                    <option value="STAFF">Staff</option>
                    <option value="ADMIN">Admin</option>
                </select>
            </div>
            <button type="submit" class="btn btn-success">Submit</button>
        </form>
        """
        return render_template('forms.html', html_form=html_form)

    elif request.method == 'POST':
        # Get form data
        try:
            dpi = request.form['DPI']
            first_name = request.form['FirstName']
            last_name = request.form['LastName']
            email = request.form['Email']
            phone_number = request.form['PhoneNumber']
            password = request.form['password']  # Ensure 'password' is in the form data
            confirm_password = request.form['ConfirmPassword']
            credit_limit = float(request.form['CreditLimit'])
            available_balance = float(request.form['AvailableBalance'])
            user_type = request.form['UserType']
        except KeyError as e:
            flash(f'Missing field: {str(e)}', 'danger')
            return redirect(url_for('addempleado'))

        # Validate DPI
        if validar_dpi(dpi):
            flash('DPI inválido. Por favor, verifica el DPI e inténtalo de nuevo.', 'danger')
            return redirect(url_for('addempleado'))

        # Check if passwords match
        if password != confirm_password:
            flash('Las contraseñas no coinciden. Por favor, verifica e inténtalo de nuevo.', 'danger')
            return redirect(url_for('addempleado'))

        # Check password length and complexity
        if len(password) < 8:
            flash('La contraseña debe tener al menos 8 caracteres.', 'danger')
            return redirect(url_for('addempleado'))

        if not re.search(r'[A-Z]', password) or not re.search(r'[a-z]', password) or not re.search(r'[0-9]', password):
            flash('La contraseña debe contener al menos una letra mayúscula, una letra minúscula y un número.', 'danger')
            return redirect(url_for('addempleado'))

        # Insert employee
        resultado = insertar_empleado(dpi, first_name, last_name, email, phone_number, password, credit_limit, available_balance, user_type)

        if resultado:
            flash('Empleado añadido exitosamente.', 'success')
        else:
            flash('Error al añadir el empleado.', 'danger')

        return redirect(url_for('addempleado'))

@app.route('/addproducto', methods=['GET', 'POST'])
@jwt_required()
def addproducto():
    if request.method == 'GET':
        # Generar formulario HTML dinámicamente
        html_form = """
        <form action="/addproducto" method="POST">
            <div class="form-group">
                <label for="productname">Product Name</label>
                <input type="text" id="productname" name="ProductName" class="form-control" required>
            </div>
            <div class="form-group">
                <label for="description">Description</label>
                <textarea id="description" name="Description" class="form-control" required></textarea>
            </div>
            <div class="form-group">
                <label for="price">Price</label>
                <input type="number" step="0.01" id="price" name="Price" class="form-control" required>
            </div>
            <div class="form-group">
                <label for="stock">Stock</label>
                <input type="number" id="stock" name="Stock" class="form-control" required>
            </div>
            <div class="form-group">
                <label for="category">Category</label>
                <input type="text" id="category" name="Category" class="form-control" required>
            </div>
            <div class="form-group">
                <label for="isactive">Is Active</label>
                <select id="isactive" name="IsActive" class="form-control" required>
                    <option value="1">Yes</option>
                    <option value="0">No</option>
                </select>
            </div>
            <button type="submit" class="btn btn-success">Submit</button>
        </form>
        """
        return render_template('forms.html', html_form=html_form)

    elif request.method == 'POST':
        # Obtener los datos del formulario
        try:
            product_name = request.form['ProductName']
            description = request.form['Description']
            price = float(request.form['Price'])
            stock = int(request.form['Stock'])
            category = request.form['Category']
            is_active = int(request.form['IsActive'])  # 1 para activo, 0 para inactivo
        except KeyError as e:
            flash(f'Falta el campo: {str(e)}', 'danger')
            return redirect(url_for('addproducto'))

        # Validar que el precio y el stock sean mayores que cero
        if price <= 0:
            flash('El precio debe ser mayor que 0.', 'danger')
            return redirect(url_for('addproducto'))

        if stock < 0:
            flash('El stock no puede ser negativo.', 'danger')
            return redirect(url_for('addproducto'))

        # Insertar el producto en la base de datos
        resultado = insertar_products(product_name, description, price, stock, category, is_active)

        if resultado:
            flash('Producto añadido exitosamente.', 'success')
        else:
            flash('Error al añadir el producto.', 'danger')

        return redirect(url_for('addproducto'))

@app.route('/editarempleado/<int:employee_id>', methods=['GET', 'POST'])
@jwt_required()
def editarempleado(employee_id):
    if request.method == 'GET':
        # Obtener los datos del empleado por su ID
        empleado = obtener_empleados(employee_id)

        if not empleado:
            flash('Empleado no encontrado.', 'danger')
            return redirect(url_for('editarempleado', employee_id=employee_id))

        # Generar el formulario poblado con los datos del empleado
        html_form = f"""
        <form action="/editarempleado/{employee_id}" method="POST">
            <div class="form-group">
                <label for="dpi">DPI</label>
                <input type="text" id="dpi" name="DPI" class="form-control" value="{empleado[0]['DPI']}" required readonly>
            </div>
            <div class="form-group">
                <label for="firstname">First Name</label>
                <input type="text" id="firstname" name="FirstName" class="form-control" value="{empleado[0]['FirstName']}" required>
            </div>
            <div class="form-group">
                <label for="lastname">Last Name</label>
                <input type="text" id="lastname" name="LastName" class="form-control" value="{empleado[0]['LastName']}" required>
            </div>
            <div class="form-group">
                <label for="email">Email</label>
                <input type="email" id="email" name="Email" class="form-control" value="{empleado[0]['Email']}" required>
            </div>
            <div class="form-group">
                <label for="phonenumber">Phone Number</label>
                <input type="text" id="phonenumber" name="PhoneNumber" class="form-control" value="{empleado[0]['PhoneNumber']}">
            </div>
            <div class="form-group">
                <label for="password">Password (Dejar en blanco si no desea cambiar)</label>
                <input type="password" id="password" name="password" class="form-control">
            </div>
            <div class="form-group">
                <label for="confirm_password">Confirm Password</label>
                <input type="password" id="confirm_password" name="ConfirmPassword" class="form-control">
            </div>
            <div class="form-group">
                <label for="creditlimit">Credit Limit</label>
                <input type="number" step="0.01" id="creditlimit" name="CreditLimit" class="form-control" value="{empleado[0]['CreditLimit']}" required>
            </div>
            <div class="form-group">
                <label for="availablebalance">Available Balance</label>
                <input type="number" step="0.01" id="availablebalance" name="AvailableBalance" class="form-control" value="{empleado[0]['AvailableBalance']}" required>
            </div>
            <div class="form-group">
                <label for="usertype">User Type</label>
                <select id="usertype" name="UserType" class="form-control" required>
                    <option value="STAFF" {"selected" if empleado[0]['UserType'] == "STAFF" else ""}>Staff</option>
                    <option value="ADMIN" {"selected" if empleado[0]['UserType'] == "ADMIN" else ""}>Admin</option>
                </select>
            </div>
            <button type="submit" class="btn btn-success">Update</button>
        </form>
        """
        return render_template('forms.html', html_form=html_form)

    elif request.method == 'POST':
        # Obtener datos del formulario
        try:
            first_name = request.form['FirstName']
            last_name = request.form['LastName']
            email = request.form['Email']
            phone_number = request.form['PhoneNumber']
            password = request.form['password']
            confirm_password = request.form['ConfirmPassword']
            credit_limit = float(request.form['CreditLimit'])
            available_balance = float(request.form['AvailableBalance'])
            user_type = request.form['UserType']
        except KeyError as e:
            flash(f'Missing field: {str(e)}', 'danger')
            return redirect(url_for('editarempleado', employee_id=employee_id))

        # Validar si las contraseñas coinciden solo si se está intentando actualizar la contraseña
        if password:
            if password != confirm_password:
                flash('Las contraseñas no coinciden. Por favor, verifica e inténtalo de nuevo.', 'danger')
                return redirect(url_for('editarempleado', employee_id=employee_id))

            # Validar longitud y complejidad de la contraseña
            if len(password) < 8:
                flash('La contraseña debe tener al menos 8 caracteres.', 'danger')
                return redirect(url_for('editarempleado', employee_id=employee_id))

            if not re.search(r'[A-Z]', password) or not re.search(r'[a-z]', password) or not re.search(r'[0-9]', password):
                flash('La contraseña debe contener al menos una letra mayúscula, una letra minúscula y un número.', 'danger')
                return redirect(url_for('editarempleado', employee_id=employee_id))

        # Llamar a la función editar_empleado
        resultado = editar_empleado(employee_id, first_name, last_name, email, phone_number, password, credit_limit, available_balance, user_type)

        if resultado:
            flash('Empleado actualizado exitosamente.', 'success')
        else:
            flash('Error al actualizar el empleado.', 'danger')

        return redirect(url_for('editarempleado', employee_id=employee_id))

@app.route('/editarproduct/<int:product_id>', methods=['GET', 'POST'])
@jwt_required()
def editarproduct(product_id):
    if request.method == 'GET':
        # Obtener los datos del producto usando la función obtener_medicamentos
        productos = obtener_medicamentos(ProductID=product_id)
        
        # Verificar si se obtuvo algún producto
        if not productos:
            flash('Producto no encontrado.', 'danger')
            return redirect(url_for('addproducto'))
        
        producto = productos[0]  # Como solo obtenemos un producto, tomamos el primero de la lista

        # Generar formulario HTML con los datos del producto actual
        html_form = f"""
        <form action="/editarproduct/{product_id}" method="POST">
            <div class="form-group">
                <label for="productname">Product Name</label>
                <input type="text" id="productname" name="ProductName" class="form-control" value="{producto['ProductName']}" required>
            </div>
            <div class="form-group">
                <label for="description">Description</label>
                <textarea id="description" name="Description" class="form-control" required>{producto['Description']}</textarea>
            </div>
            <div class="form-group">
                <label for="price">Price</label>
                <input type="number" step="0.01" id="price" name="Price" class="form-control" value="{producto['Price']}" required>
            </div>
            <div class="form-group">
                <label for="stock">Stock</label>
                <input type="number" id="stock" name="Stock" class="form-control" value="{producto['Stock']}" required>
            </div>
            <div class="form-group">
                <label for="category">Category</label>
                <input type="text" id="category" name="Category" class="form-control" value="{producto['Category']}" required>
            </div>
            <div class="form-group">
                <label for="isactive">Is Active</label>
                <select id="isactive" name="IsActive" class="form-control" required>
                    <option value="1" {"selected" if producto['IsActive'] == 1 else ""}>Yes</option>
                    <option value="0" {"selected" if producto['IsActive'] == 0 else ""}>No</option>
                </select>
            </div>
            <button type="submit" class="btn btn-success">Update</button>
        </form>
        """
        return render_template('forms.html', html_form=html_form)

    elif request.method == 'POST':
        # Obtener los datos actualizados del formulario
        try:
            product_name = request.form['ProductName']
            description = request.form['Description']
            price = float(request.form['Price'])
            stock = int(request.form['Stock'])
            category = request.form['Category']
            is_active = int(request.form['IsActive'])  # 1 para activo, 0 para inactivo
        except KeyError as e:
            flash(f'Falta el campo: {str(e)}', 'danger')
            return redirect(url_for('editarproduct', product_id=product_id))

        # Validar que el precio y el stock sean mayores que cero
        if price <= 0:
            flash('El precio debe ser mayor que 0.', 'danger')
            return redirect(url_for('editarproduct', product_id=product_id))

        if stock < 0:
            flash('El stock no puede ser negativo.', 'danger')
            return redirect(url_for('editarproduct', product_id=product_id))

        # Actualizar el producto en la base de datos
        resultado = editar_producto(
            product_id,
            ProductName=product_name,
            Description=description,
            Price=price,
            Stock=stock,
            Category=category,
            IsActive=is_active
        )

        if resultado:
            flash('Producto actualizado exitosamente.', 'success')
        else:
            flash('Error al actualizar el producto.', 'danger')

        return redirect(url_for('editarproduct', product_id=product_id))





if __name__ == '__main__':
    app.run(port=5000)
