from models import Formulario, Enajenante, Persona
from flask_sqlalchemy import SQLAlchemy
from dateutil.parser import parse
from datetime import datetime

def analyzeJSON(db: SQLAlchemy, JSON):
    if JSON['F2890']:
        for single_form in JSON['F2890']:
            newForm = Formulario()
            enajenantes = []

            
            main_keys = ['cne', 'bienRaiz', 'fojas', 'fecha_inscripcion', 'num_inscripcion']
            location_keys = ['comuna', 'manzana', 'predio']

            for key, value in single_form.items():
                if key != 'bienRaiz' and key in main_keys:
                    setattr(newForm, key, value)
                elif key == "CNE":
                    setattr(newForm, 'cne', value)
                elif key == "fechaInscripcion":
                    try:
                        parse(value)
                        setattr(newForm, 'fecha_inscripcion', value)
                    except ValueError:
                        setattr(newForm, 'fecha_inscripcion', datetime(1900, 1, 1).date())
                    
                    
                elif key == 'nroInscripcion':
                    setattr(newForm, 'num_inscripcion', value)

                elif key == 'bienRaiz':
                    for k, v in single_form['bienRaiz'].items():
                        if k == 'comuna':
                            setattr(newForm, 'comuna', v)
                        elif k == 'manzana':
                            setattr(newForm, 'manzana', v)
                        elif k == 'predio':
                            setattr(newForm, 'predio', v)

                elif key == 'enajenantes':
                    for singleEnajenante in single_form['enajenantes']:
                        newEnajenante = Enajenante()
                        if 'RUNRUT' in singleEnajenante.keys():
                            newEnajenante.run_rut = singleEnajenante['RUNRUT']

                            person = Persona.query.filter_by(run_rut=newEnajenante.run_rut).first()
                            if person is None:
                                person = Persona(run_rut=newEnajenante.run_rut)
                                db.session.add(person)
                                db.session.commit()

                        if 'porcDerecho' in singleEnajenante.keys():
                            newEnajenante.porc_derecho = singleEnajenante['porcDerecho']
                        
                        enajenantes.append(newEnajenante)
                

            db.session.add(newForm)
            db.session.commit()

            for singleEnajenante in enajenantes:
                singleEnajenante.form_id = newForm.n_atencion
                db.session.add(singleEnajenante)
            db.session.commit()

    else:
        print('Formato no valido.')