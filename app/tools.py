from enum import Enum
from models import Formulario, Enajenante, Adquirente, Persona
from flask_sqlalchemy import SQLAlchemy
from forms import FormularioForm


class CONSTANTS(Enum):
    CNE_REGULARIZACION = 99
    CNE_COMPRAVENTA = 8

    ESCENARIO1_VALUE = 1
    ESCENARIO2_VALUE = 2
    ESCENARIO3_VALUE = 3
    ESCENARIO4_VALUE = 4
    INVALID_ESCENARIO_VALUE = 0

    JSON_FILE_EXTENTION = '.json'
    ENCODING_FORMAT = 'utf-8'


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
