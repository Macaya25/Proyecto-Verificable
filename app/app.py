import os
import logging
import json

from sqlalchemy import and_, or_
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_wtf.csrf import CSRFProtect
from forms import FormularioForm, JSONForm, SearchForm
from models import db, Formulario, Multipropietario, CNE, Comuna
from tools import (CONSTANTS, process_and_save_json_into_db, add_adquirientes_to_database_from_form,
                   add_formulario_to_database_from_form, add_enajenantes_to_database_from_form)
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
def index_route() -> str:
    return render_template('index.html')


@app.route('/form', methods=['GET', 'POST'])
def form_route():
    form = FormularioForm()

    # Add the comunas from database to the Formulario object to show on the Web UI as options
    form.comuna.choices = [(comuna.id, comuna.descripcion)
                           for comuna in Comuna.query.order_by('descripcion')]

    if request.method == 'POST' and form.validate_on_submit():

        new_formulario = add_formulario_to_database_from_form(db, form)
        add_adquirientes_to_database_from_form(db, form, new_formulario)

        if form.cne.data == CONSTANTS.CNE_COMPRAVENTA.value:
            add_enajenantes_to_database_from_form(db, form, new_formulario)

        converted_form = multiprop_handler.convert_form_into_object(form)
        multiprop_handler.process_new_formulario(converted_form)
        db.session.commit()
        flash('Formulario registrado con éxito!')
        return redirect(url_for('forms_route'))
    else:
        print(form.errors)

    return render_template('form.html', form=form)


@app.route('/forms')
def forms_route():
    forms = Formulario.query.all()
    cnes = {cne.id: cne for cne in CNE.query.all()}
    comunas = {comuna.id: comuna for comuna in Comuna.query.all()}
    return render_template('forms.html', forms=forms, cnes=cnes, comunas=comunas)


@app.route('/form/json', methods=['GET', 'POST'])
def form_json_route():
    form = JSONForm()

    if form.validate_on_submit():
        file = form.file.data

        if file.filename.endswith('.json'):
            file = json.loads(file.read().decode('utf-8'))

            if process_and_save_json_into_db(db, file):
                converted_forms_list = multiprop_handler.convert_json_into_object_list(
                    file)
                for form in converted_forms_list:
                    multiprop_handler.process_new_formulario(form)
                db.session.commit()

            return redirect(url_for('forms_route'))

        else:
            print('Archivo no es json.')

    return render_template('formJSON.html', form=form)


@app.route('/forms/<int:n_atencion>')
def form_details_route(n_atencion):
    formulario = Formulario.query.get_or_404(n_atencion)
    comuna_obj = Comuna.query.filter_by(id=formulario.comuna).first()
    descripcion_cne = obtener_descripcion_cne(formulario.cne)
    return render_template('form_details.html', formulario=formulario, descripcion_cne=descripcion_cne, comuna=comuna_obj)


def obtener_descripcion_cne(cne_id):
    cne = CNE.query.filter_by(id=cne_id).first()
    return cne.descripcion if cne else "Descripción no encontrada"


@app.route('/multipropietario', methods=['GET', 'POST'])
def multipropietario_route():
    form = SearchForm()
    search_results = []
    if request.method == 'POST':
        comuna = request.form.get('comuna')
        manzana = request.form.get('manzana')
        predio = request.form.get('predio')
        ano_vigencia = request.form.get('ano_vigencia')
        search_results = Multipropietario.query.filter(
            and_(
                Multipropietario.comuna == comuna,
                Multipropietario.manzana == manzana,
                Multipropietario.predio == predio,
                Multipropietario.ano_vigencia_inicial <= ano_vigencia,
                or_(
                    Multipropietario.ano_vigencia_final >= ano_vigencia,
                    Multipropietario.ano_vigencia_final.is_(None)
                )
            )
        ).all()

        return render_template('multipropietario.html', form=form, search_results=search_results)
    search_results = Multipropietario.query.all()
    return render_template('multipropietario.html', form=form, search_results=search_results)


@app.route('/comunas/<int:region_id>')
def get_comunas(region_id):
    comunas = Comuna.query.filter_by(
        id_region=region_id).order_by('descripcion').all()
    return jsonify([{'id': comuna.id, 'descripcion': comuna.descripcion} for comuna in comunas])


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0')
