from flask import redirect, url_for, flash
from flask_jwt_extended import JWTManager

jwt = JWTManager()

def init_jwt(app):
    jwt.init_app(app)

    @jwt.unauthorized_loader
    def unauthorized_response(callback):
        flash('Necesitas autenticarte', 'danger')
        return redirect(url_for('login'))

    @jwt.invalid_token_loader
    def invalid_token_response(callback):
        flash('Token inválido. Necesitas autenticarte', 'danger')
        return redirect(url_for('login'))

    # Agrega más callbacks si es necesario
