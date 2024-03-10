from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

from dotenv import load_dotenv
import os

# Getting secrets
load_dotenv()
secret_key = os.getenv('secret_key')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://root:root@localhost/db'
app.config['SECRET_KEY'] = secret_key
db = SQLAlchemy(app)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/forms')
def forms():
    return render_template('forms.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

