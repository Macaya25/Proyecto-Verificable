import os
import logging
import json
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_wtf.csrf import CSRFProtect
from forms import FormularioForm, JSONForm
from models import db, Formulario, Persona, Enajenante, Adquirente, Multipropietario, CNE
from tools import analyze_json
from dotenv import load_dotenv



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
    if form.validate_on_submit():
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
        
        if form.cne.data == '1':
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
        new_multipropietarios(form)
        db.session.commit()
        flash('Formulario registrado con éxito!')
        return redirect(url_for('index_route'))

    return render_template('form.html', form=form)

def new_multipropietarios(form):
    for adquiriente in form.adquirentes.data:
        new_multipropietario(form, adquiriente['run_rut'], adquiriente['porc_derecho'])
    if form.cne.data == '1':
        for enajenante in form.enajenantes.data:
            new_multipropietario(form, enajenante['run_rut'], enajenante['porc_derecho'])

def new_multipropietario(form, rut, derecho):
    año_vigencia_inicial = form.fecha_inscripcion.data.year
    año_vigencia_final = None
    # Lógica para determinar el año de vigencia final
    multipropietario_anterior = Multipropietario.query.filter_by(
        comuna=form.comuna.data,
        manzana=form.manzana.data,
        predio=form.predio.data
    ).filter(Multipropietario.ano_vigencia_inicial >= año_vigencia_inicial).first()

    if multipropietario_anterior:
        año_vigencia_final = multipropietario_anterior.año_vigencia_inicial

    new_multipropietario = Multipropietario(
        comuna=form.comuna.data,
        manzana=form.manzana.data,
        predio=form.predio.data,
        run_rut=rut,
        porc_derechos=derecho,
        fojas=form.fojas.data,
        ano_inscripcion=form.fecha_inscripcion.data.year,
        num_inscripcion=form.num_inscripcion.data,
        fecha_inscripcion=form.fecha_inscripcion.data,
        ano_vigencia_inicial=año_vigencia_inicial,
        ano_vigencia_final=año_vigencia_final
    )
    db.session.add(new_multipropietario)

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
    descripcion_cne =obtener_descripcion_cne(formulario.cne)
    return render_template('form_details.html', formulario=formulario, descripcion_cne = descripcion_cne)

def obtener_descripcion_cne(cne_id):
    print(cne_id)
    cne = CNE.query.filter_by(id=cne_id).first()
    return cne.descripcion if cne else "Descripción no encontrada"


@app.route('/multipropietario', methods=['GET', 'POST'])
def multipropietario_route():
    form = FormularioForm()
    search_results = []

    if request.method == 'POST' and form.validate_on_submit():
        comuna = form.comuna.data
        manzana = form.manzana.data
        predio = form.predio.data
        año = form.fecha_inscripcion

        search_results = Multipropietario.query.filter_by(
            comuna=comuna, manzana=manzana, predio=predio).filter(Multipropietario.ano_inscripcion >= año).all()
        print("hola")
        return render_template('multipropietario.html', form=form, search_results=search_results)
    else:
        search_results = Multipropietario.query.all()
        return render_template('multipropietario.html',form = form, search_results=search_results)



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0')
