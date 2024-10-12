from flask import * 
from config import *

app= Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.config.from_object(config['development'])
    app.run(port=5000)