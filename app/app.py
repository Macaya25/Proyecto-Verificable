import os
import logging
import json
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_wtf.csrf import CSRFProtect
from forms import FormularioForm, JSONForm
from models import db, Formulario, Persona, Enajenante, Adquirente, Multipropietario, Comuna
from tools import analyze_json
from dotenv import load_dotenv
from flask import jsonify


load_dotenv()
secret_key = os.getenv('SECRET_KEY')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
app.config['SECRET_KEY'] = secret_key
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
csrf = CSRFProtect(app)
db.init_app(app)

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')


@app.route('/')
def index_route() -> str:
    return render_template('index.html')


@app.route('/form', methods=['GET', 'POST'])
def form_route():
    form = FormularioForm()
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

        for enajenante_data in form.enajenantes.data:
            enajenante_persona = Persona.query.get(enajenante_data['run_rut'])
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
            adquirente_persona = Persona.query.get(adquirente_data['run_rut'])
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

        db.session.commit()
        flash('Formulario registrado con éxito!')
        return redirect(url_for('index_route'))
    else:
        if form.region.data:
            form.comuna.choices = [('', 'Seleccione Comuna')] + [(comuna.id, comuna.descripcion) for comuna in Comuna.query.filter_by(id_region=form.region.data).order_by('descripcion')]

    return render_template('form.html', form=form)


@app.route('/forms')
def forms_route():
    forms = Formulario.query.all()
    return render_template('forms.html', forms=forms)


@app.route('/form/json', methods=['GET', 'POST'])
def form_json_route():
    form = JSONForm()

    if form.validate_on_submit():
        file = form.file.data

        if file.filename.endswith('.json'):
            file = json.loads(file.read().decode('utf-8'))

            analyze_json(db, file)

        else:
            print('Archivo no es json.')

    return render_template('formJSON.html', form=form)


@app.route('/forms/<int:n_atencion>')
def form_details_route(n_atencion):
    formulario = Formulario.query.get_or_404(n_atencion)
    return render_template('form_details.html', formulario=formulario)


@app.route('/multipropietario', methods=['GET', 'POST'])
def multipropietario_route():
    if request.method == 'POST':
        comuna = request.form.get('comuna')
        manzana = request.form.get('manzana')
        predio = request.form.get('predio')
        año = request.form.get('año')

        results = Multipropietario.query.filter_by(
            comuna=comuna, manzana=manzana, predio=predio, año=año).all()
        return render_template('multipropietario.html', search_results=results)

    return render_template('multipropietario.html', search_results=None)

@app.route('/comunas/<int:region_id>')
def get_comunas(region_id):
    comunas = Comuna.query.filter_by(id_region=region_id).order_by('descripcion').all()
    return jsonify([{'id': comuna.id, 'descripcion': comuna.descripcion} for comuna in comunas])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0')
