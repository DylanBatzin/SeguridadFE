from flask import * 
from config import *
from werkzeug.security import generate_password_hash

app= Flask(__name__)

@app.route('/')
def index():
     return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        DPI = request.form['dpi']
        contra = request.form['password']
        hashed_password = generate_password_hash(contra, method='pbkdf2:sha256', salt_length=16)
        data = {
            'dpi': DPI,
            'password': hashed_password
        }
        return render_template('index.html')
    else:
        return render_template('index.html')

if __name__ == '__main__':
    app.config.from_object(config['development'])
    app.run(port=5000)