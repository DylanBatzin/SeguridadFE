from flask import * 
from config import config  # Importa el diccionario de configuración
from database.OperacionesBD import validar_login, obtener_datos_usuario, generar_token, validar_token, obtener_datos_home, obtener_medicamentos
from jwt_auth import jwt, init_jwt  # Importa jwt y la función de inicialización
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity,
    set_access_cookies, unset_jwt_cookies
)

app = Flask(__name__)

app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_ACCESS_COOKIE_PATH'] = '/'
app.config['JWT_COOKIE_SECURE'] = False  # Cambia a True en producción si usas HTTPS
app.config['JWT_COOKIE_CSRF_PROTECT'] = False  # Maneja los tokens CSRF si lo necesitas  
app.config.from_object(config['development'])

# Inicializa JWT con la aplicación
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
            enviar_sms(telefono, token_value)
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
            return redirect(url_for('productos', product_id=product_id))

        # Manejo de eliminación
        elif 'eliminar' in request.form:
            product_id = request.form['eliminar']
            return redirect(url_for('productos')) 


def enviar_sms(telefono, token_value):
    # Simulación del envío de SMS   
    print(f"Enviando token por SMS al número {telefono}: {token_value}")

def enviar_email(email, token_value):
    # Simulación del envío de correo
    print(f"Enviando token por correo a {email}: {token_value}")

if __name__ == '__main__':
    app.run(port=5000)
