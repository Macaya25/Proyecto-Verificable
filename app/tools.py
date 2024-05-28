from typing import List
from enum import Enum
from models import Formulario, Enajenante, Adquirente, Persona, Comuna
from flask_sqlalchemy import SQLAlchemy
from dateutil.parser import parse
from forms import FormularioForm


class CONSTANTS(Enum):
    CNE_REGULARIZACION = 99
    CNE_COMPRAVENTA = 8

    ESCENARIO1_VALUE = 1
    ESCENARIO2_VALUE = 2
    ESCENARIO3_VALUE = 3
    ESCENARIO4_VALUE = 4
    INVALID_ESCENARIO_VALUE = 0


def process_and_save_json_into_db(db: SQLAlchemy, json_form) -> bool:
    def run() -> bool:
        if not json_form['F2890']:
            print('Formato no valido.')
            return False

        for single_form in json_form['F2890']:
            new_form: Formulario = Formulario()

            parse_json_and_set_form(new_form, single_form)
            db.session.add(new_form)

            enajenantes: List[Enajenante] = parse_json_and_get_enajenantes(single_form)
            adquirientes: List[Adquirente] = parse_json_and_get_adquirentes(single_form)

            for single_enajenante in enajenantes:
                single_enajenante.form_id = new_form.n_atencion
                db.session.add(single_enajenante)

            for single_adquiriente in adquirientes:
                single_adquiriente.form_id = new_form.n_atencion
                db.session.add(single_adquiriente)

            db.session.commit()
        return True

    def parse_json_and_set_form(new_form: Formulario, current_form):
        def parse_rol(new_form: Formulario, current_form):
            for k, v in current_form['bienRaiz'].items():
                if k == 'comuna':
                    comuna_exists = db.session.query(
                        db.exists().where(Comuna.id == v)).scalar()
                    if comuna_exists:
                        setattr(new_form, 'comuna', v)
                    else:
                        setattr(new_form, 'comuna', None)
                elif k == 'manzana':
                    setattr(new_form, 'manzana', v)
                elif k == 'predio':
                    setattr(new_form, 'predio', v)

        main_keys = ['cne', 'bienRaiz', 'fojas',
                     'fecha_inscripcion', 'num_inscripcion']

        for key, value in current_form.items():
            if key != 'bienRaiz' and key in main_keys:
                setattr(new_form, key, value)
            elif key == "CNE":
                setattr(new_form, 'cne', value)
            elif key == "fechaInscripcion":
                try:
                    parse(value)
                    setattr(new_form, 'fecha_inscripcion', value)
                except ValueError:
                    setattr(new_form, 'fecha_inscripcion', None)

            elif key == 'nroInscripcion':
                setattr(new_form, 'num_inscripcion', value)

            elif key == 'bienRaiz':
                parse_rol(new_form, current_form)

    def parse_json_and_get_enajenantes(current_form):
        enajenantes: List[Enajenante] = []

        if not current_form.get('enajenantes'):
            return []

        for single_enajenante in current_form['enajenantes']:
            new_enajenante = Enajenante()
            if 'RUNRUT' in single_enajenante.keys():
                new_enajenante.run_rut = single_enajenante['RUNRUT']

                person = Persona.query.filter_by(
                    run_rut=new_enajenante.run_rut).first()
                if person is None:
                    person = Persona(
                        run_rut=new_enajenante.run_rut)
                    db.session.add(person)
                    db.session.commit()

            if 'porcDerecho' in single_enajenante.keys():
                new_enajenante.porc_derecho = single_enajenante['porcDerecho']

            enajenantes.append(new_enajenante)

        return enajenantes

    def parse_json_and_get_adquirentes(current_form):
        if not current_form.get('adquirentes'):
            return []

        adquirentes: List[Enajenante] = []

        for single_adquiriente in current_form['adquirentes']:
            new_adquiriente = Adquirente()
            if 'RUNRUT' in single_adquiriente.keys():
                new_adquiriente.run_rut = single_adquiriente['RUNRUT']

                person = Persona.query.filter_by(
                    run_rut=new_adquiriente.run_rut).first()
                if person is None:
                    person = Persona(
                        run_rut=new_adquiriente.run_rut)
                    db.session.add(person)
                    db.session.commit()

            if 'porcDerecho' in single_adquiriente.keys():
                new_adquiriente.porc_derecho = single_adquiriente['porcDerecho']

            adquirentes.append(new_adquiriente)
        return adquirentes

    return run()


def is_empty(lst: list):
    return not bool(lst)


def add_formulario_to_database_from_form(db: SQLAlchemy, form: FormularioForm) -> Formulario:
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

    return new_formulario


def add_enajenantes_to_database_from_form(db: SQLAlchemy, form: Formulario, new_formulario: Formulario):
    for enajenante_data in form.enajenantes.data:
        enajenante_persona = db.session.get(Persona, enajenante_data['run_rut'])
        if not enajenante_persona:
            enajenante_persona = Persona(run_rut=enajenante_data['run_rut'])
            db.session.add(enajenante_persona)
        new_enajenante = Enajenante(porc_derecho=enajenante_data['porc_derecho'],
                                    persona=enajenante_persona,
                                    formulario=new_formulario)
        db.session.add(new_enajenante)


def add_adquirientes_to_database_from_form(db: SQLAlchemy, form: FormularioForm, new_formulario: Formulario):
    for adquirente_data in form.adquirentes.data:
        adquirente_persona = db.session.get(Persona, adquirente_data['run_rut'])
        if not adquirente_persona:
            adquirente_persona = Persona(run_rut=adquirente_data['run_rut'])
            db.session.add(adquirente_persona)
        new_adquirente = Adquirente(porc_derecho=adquirente_data['porc_derecho'],
                                    persona=adquirente_persona,
                                    formulario=new_formulario)
        db.session.add(new_adquirente)
