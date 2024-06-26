import os
import logging

from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_wtf.csrf import CSRFProtect
from forms import FormularioForm, JSONForm, SearchForm
from models import db, Formulario, Multipropietario, CNE, Comuna
from tools import (CONSTANTS, add_adquirientes_to_database_from_form,
                   add_formulario_to_database_from_form, add_enajenantes_to_database_from_form)
from json_processing import (analyse_json_save_into_db_and_process_it)
from dotenv import load_dotenv
from multipropietario.multipropietario_handler import MultipropietarioHandler


load_dotenv()
secret_key = os.getenv('SECRET_KEY')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
csrf = CSRFProtect(app)
db.init_app(app)

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')
multiprop_handler = MultipropietarioHandler()


@app.route('/')
def render_home_page() -> str:
    return render_template('home.html')


@app.route('/form', methods=['GET'])
def get_create_form_view():
    form = FormularioForm()

    # Add the comunas from database to the Formulario object to show on the Web UI as options
    form.comuna.choices = [(comuna.id, comuna.descripcion)
                           for comuna in Comuna.query.order_by('descripcion')]

    return render_template('create_form.html', form=form)


@app.route('/form', methods=['POST'])
def create_form_route():

    form = FormularioForm()
    # Add the comunas from database to allow them as valid choices
    form.comuna.choices = [(comuna.id, comuna.descripcion)
                           for comuna in Comuna.query.order_by('descripcion')]

    if form.validate_on_submit():
        new_formulario = add_formulario_to_database_from_form(db, form)
        add_adquirientes_to_database_from_form(db, form, new_formulario)

        if form.cne.data == CONSTANTS.CNE_COMPRAVENTA:
            add_enajenantes_to_database_from_form(db, form, new_formulario)

        converted_form = multiprop_handler.convert_form_into_object(form)
        multiprop_handler.process_new_formulario_object(db, converted_form)
        db.session.commit()
        flash('Formulario registrado con éxito!')
        return redirect(url_for('show_all_forms_route'))

    else:
        # Print form errors and data for debugging
        print("Form validation failed")
        print("Form errors: ", form.errors)
        print("Form data: ", form.data)
        flash('Formulario no fue registrado. Por favor, corrige los errores e intenta de nuevo.')
        return render_template('show_all_forms_route.html', form=form)


@app.route('/forms')
def show_all_forms_route():
    forms = Formulario.query.all()
    cnes = {cne.id: cne for cne in CNE.query.all()}
    comunas = {comuna.id: comuna for comuna in Comuna.query.all()}
    return render_template('show_all_forms.html', forms=forms, cnes=cnes, comunas=comunas)


@app.route('/form/json', methods=['GET'])
def get_create_json_form_view():
    form = JSONForm()

    return render_template('create_form_JSON.html', form=form)


@app.route('/form/json', methods=['POST'])
def create_json_form_route():
    form = JSONForm()

    if form.validate_on_submit():
        submitted_file = form.file.data
        is_valid_json = analyse_json_save_into_db_and_process_it(db, multiprop_handler, submitted_file)

        if is_valid_json:
            return redirect(url_for('show_all_forms_route'))


@app.route('/forms/<int:n_atencion>')
def form_details_route(n_atencion):
    formulario = Formulario.query.get_or_404(n_atencion)
    comuna_obj = Comuna.query.filter_by(id=formulario.comuna).first()
    descripcion_cne = obtener_descripcion_cne(formulario.cne)
    return render_template('form_details.html', formulario=formulario, descripcion_cne=descripcion_cne, comuna=comuna_obj)


def obtener_descripcion_cne(cne_id):
    cne = CNE.query.filter_by(id=cne_id).first()
    return cne.descripcion if cne else "Descripción no encontrada"


@app.route('/multipropietario', methods=['GET'])
def get_multipropietarios_route():
    form = SearchForm()
    search_results = []

    search_results = Multipropietario.query.all()
    return render_template('multipropietario.html', form=form, search_results=search_results)


@app.route('/multipropietario', methods=['POST'])
def search_multipropietarios():
    form = SearchForm()

    search_results = multiprop_handler.search_multipropietario(db, request)

    return render_template('multipropietario.html', form=form, search_results=search_results)


@app.route('/comunas/<int:region_id>')
def get_comunas(region_id):
    comunas = Comuna.query.filter_by(
        id_region=region_id).order_by('descripcion').all()
    return jsonify([{'id': comuna.id, 'descripcion': comuna.descripcion} for comuna in comunas])


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', debug=True)
