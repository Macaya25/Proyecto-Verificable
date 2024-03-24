from models import Formulario, Enajenante
from flask_sqlalchemy import SQLAlchemy

def analyzeJSON(db: SQLAlchemy, JSON):
    if JSON['F2890']:
        for single_form in JSON['F2890']:
            newForm = Formulario()
            
            keys = ['cne', 'bienRaiz', 'fojas', 'fecha_inscripcion', 'num_inscripcion']
            for key, value in single_form.items():
                if key != 'bienRaiz' and key in keys:
                    setattr(newForm, key, value)
                    #print(key, value)
                elif key == "CNE":
                    setattr(newForm, 'cne', value)
                elif key == "fechaInscripcion":
                    setattr(newForm, 'fecha_inscripcion', value)
                elif key == 'nroInscripcion':
                    setattr(newForm, 'num_inscripcion', value)

                elif key == 'enajenantes':
                    for singleEnajenante in single_form['enajenantes']:
                        newEnajenante = Enajenante()
                        if 'RUNRUT' in singleEnajenante.items():
                            newEnajenante.run_rut = singleEnajenante['RUNRUT']
                        if 'porcDerecho' in singleEnajenante.items():
                            newEnajenante.porc_derecho = singleEnajenante['porcDerecho']
                        
                        print(newEnajenante)
                


            print(newForm)

    else:
        print('Formato no valido.')