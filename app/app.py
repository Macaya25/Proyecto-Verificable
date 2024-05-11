import os
import logging
import json
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_wtf.csrf import CSRFProtect
from forms import FormularioForm, JSONForm
from models import db, Formulario, Persona, Enajenante, Adquirente, Multipropietario, CNE, Comuna
from tools import process_and_save_json_into_db, CONSTANTS
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
    form.comuna.choices = [(comuna.id, comuna.descripcion)
                           for comuna in Comuna.query.order_by('descripcion')]
    if request.method == 'POST' and form.validate_on_submit():
        new_formulario = Formulario(
            cne=form.cne.data,
            comuna=form.comuna.data,
            manzana=form.manzana.data,
            predio=form.predio.data,
            fojas=form.fojas.data,
            fecha_inscripcion=form.fecha_inscripcion.data,
            num_inscripcion=form.num_inscripcion.data
        )
        db.session.add(new_formulario)

        if form.cne.data == CONSTANTS.CNE_COMPRAVENTA.value:
            for enajenante_data in form.enajenantes.data:
                enajenante_persona = db.session.get(
                    Persona, enajenante_data['run_rut'])
                if not enajenante_persona:
                    enajenante_persona = Persona(
                        run_rut=enajenante_data['run_rut'])
                    db.session.add(enajenante_persona)
                new_enajenante = Enajenante(
                    porc_derecho=enajenante_data['porc_derecho'],
                    persona=enajenante_persona,
                    formulario=new_formulario
                )
                db.session.add(new_enajenante)

        for adquirente_data in form.adquirentes.data:
            adquirente_persona = db.session.get(
                Persona, adquirente_data['run_rut'])
            if not adquirente_persona:
                adquirente_persona = Persona(
                    run_rut=adquirente_data['run_rut'])
                db.session.add(adquirente_persona)
            new_adquirente = Adquirente(
                porc_derecho=adquirente_data['porc_derecho'],
                persona=adquirente_persona,
                formulario=new_formulario
            )
            db.session.add(new_adquirente)

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
                    multiprop_handler.process_new_form(form)
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
    form = FormularioForm()
    search_results = []

    if request.method == 'POST' and form.validate_on_submit():
        # Imprimir el contenido del formulario
        app.logger.info('Formulario recibido: %s', form.data)

        comuna = form.comuna.data
        manzana = form.manzana.data
        predio = form.predio.data
        año = form.fecha_inscripcion.data.year

        search_results = Multipropietario.query.filter_by(
            comuna=comuna, manzana=manzana, predio=predio).filter(Multipropietario.ano_inscripcion >= año).all()

        return render_template('multipropietario.html', form=form, search_results=search_results)
    else:
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
