from typing import List
from models import Formulario, Enajenante, Adquirente, Persona, Comuna
from flask_sqlalchemy import SQLAlchemy
from dateutil.parser import parse


def analyze_json(db: SQLAlchemy, JSON):
    if JSON['F2890']:
        for single_form in JSON['F2890']:
            new_form: Formulario = Formulario()
            enajenantes: List[Enajenante] = []
            adquirientes: List[Adquirente] = []

            main_keys = ['cne', 'bienRaiz', 'fojas',
                         'fecha_inscripcion', 'num_inscripcion']
            # location_keys = ['comuna', 'manzana', 'predio']

            for key, value in single_form.items():
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
                    for k, v in single_form['bienRaiz'].items():
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

                elif key == 'enajenantes':
                    for single_enajenante in single_form['enajenantes']:
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

                elif key == 'adquirentes':
                    for single_adquiriente in single_form['adquirentes']:
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

                        adquirientes.append(new_adquiriente)

            db.session.add(new_form)
            db.session.commit()

            for single_enajenante in enajenantes:
                single_enajenante.form_id = new_form.n_atencion
                db.session.add(single_enajenante)
            db.session.commit()

            for single_adquiriente in adquirientes:
                single_adquiriente.form_id = new_form.n_atencion
                db.session.add(single_adquiriente)
            db.session.commit()

    else:
        print('Formato no valido.')
