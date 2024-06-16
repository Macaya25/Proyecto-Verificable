from flask_sqlalchemy import SQLAlchemy
from models import Formulario, Enajenante, Adquirente, Persona, Comuna
from tools import FILEPROPERTIES
from typing import List
from dateutil.parser import parse
import json


def process_and_save_json_into_db(db: SQLAlchemy, json_form) -> bool:
    if json_form.get('F2890') is None:
        print('Formato no valido.')
        return False

    for single_form in json_form['F2890']:
        new_form: Formulario = Formulario()

        __parse_json_and_save_form_in_db(db, new_form, single_form)

        __parse_json_and_save_enajenantes_in_db(db, single_form, new_form.n_atencion)
        __parse_json_and_save_adquirientes_in_db(db, single_form, new_form.n_atencion)
        db.session.commit()

    return True


def analyse_json_save_into_db_and_process_it(db: SQLAlchemy, multiprop_handler, submitted_file):
    if submitted_file.filename.endswith(FILEPROPERTIES.JSON_FILE_EXTENSION):
        submitted_file = json.loads(submitted_file.read().decode(FILEPROPERTIES.ENCODING_FORMAT))

        is_valid_json = process_and_save_json_into_db(db, submitted_file)
        if is_valid_json:
            converted_forms_list = multiprop_handler.convert_json_into_object_list(submitted_file)
            for form in converted_forms_list:
                multiprop_handler.process_new_formulario_object(form)
            db.session.commit()

        return True

    else:
        print('Archivo no es json.')
        return False


def __parse_json_and_set_form(db: SQLAlchemy, new_form: Formulario, current_form):
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


def __parse_json_and_save_form_in_db(db: SQLAlchemy, new_form, single_form):
    __parse_json_and_set_form(db, new_form, single_form)
    db.session.add(new_form)
    db.session.commit()


def __parse_json_and_get_enajenantes(db: SQLAlchemy, current_form):
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


def __parse_json_and_save_enajenantes_in_db(db: SQLAlchemy, single_form, new_form_id):
    enajenantes: List[Enajenante] = __parse_json_and_get_enajenantes(db, single_form)

    for single_enajenante in enajenantes:
        single_enajenante.form_id = new_form_id
        db.session.add(single_enajenante)


def __parse_json_and_save_adquirientes_in_db(db: SQLAlchemy, single_form, new_form_id):
    adquirientes: List[Adquirente] = __parse_json_and_get_adquirentes(db, single_form)

    for single_adquiriente in adquirientes:
        single_adquiriente.form_id = new_form_id
        db.session.add(single_adquiriente)


def __parse_json_and_get_adquirentes(db: SQLAlchemy, current_form):
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
