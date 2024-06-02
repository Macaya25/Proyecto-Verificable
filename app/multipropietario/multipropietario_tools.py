from typing import List, Set
from datetime import date
from models import Multipropietario, Adquirente, Enajenante, Formulario
from flask_sqlalchemy import SQLAlchemy


class FormularioObject:
    def __init__(self, cne: int, comuna: int, manzana: str, predio: str,
                 fojas: int, fecha_inscripcion: date, num_inscripcion: int,
                 enajenantes: List[Enajenante], adquirentes: List[Adquirente]):
        self.cne = cne
        self.comuna = comuna
        self.manzana = manzana
        self.predio = predio
        self.fojas = fojas
        self.fecha_inscripcion = fecha_inscripcion
        self.num_inscripcion = num_inscripcion
        self.enajenantes = enajenantes
        self.adquirentes = adquirentes


def remove_from_multipropietario(db, entries_after_current_form: List[Multipropietario]):
    for entry in entries_after_current_form:
        db.session.delete(entry)


def reprocess_multipropietario_entries_with_new_formulario(db, handler, formulario, entries: List[Multipropietario]):
    remove_from_multipropietario(db, entries)
    sorted_formularios = add_formulario_with_multipropietarios_and_sort(formulario, entries)
    reprocess_formularios(db, handler, sorted_formularios)


def reprocess_multipropietario_entries(db, handler, entries: List[Multipropietario]):
    formularios = get_formularios_from_multipropietarios(entries)
    reprocess_formularios(db, handler, formularios)


def generate_multipropietario_entry_from_formulario(
        formulario: FormularioObject,
        rut: str, derecho: int) -> Multipropietario:

    ano_vigencia_inicial = formulario.fecha_inscripcion.year
    ano_vigencia_final = None

    return Multipropietario(
        comuna=formulario.comuna,
        manzana=formulario.manzana,
        predio=formulario.predio,
        run_rut=rut,
        porc_derecho=derecho,
        fojas=formulario.fojas,
        ano_inscripcion=formulario.fecha_inscripcion.year,
        num_inscripcion=formulario.num_inscripcion,
        fecha_inscripcion=formulario.fecha_inscripcion,
        ano_vigencia_inicial=ano_vigencia_inicial,
        ano_vigencia_final=ano_vigencia_final
    )


def get_formularios_from_multipropietarios(entries: List[Multipropietario]) -> List[Formulario]:
    forms: Set[Formulario] = set()
    print(entries)
    for entry in entries:
        source_form = Formulario.query.filter_by(
            comuna=entry.comuna, manzana=entry.manzana, predio=entry.predio,
            fojas=entry.fojas, fecha_inscripcion=entry.fecha_inscripcion).first()
        if source_form:
            forms.add(source_form)
    sorted_forms = sorted(list(forms), key=lambda x: x.fecha_inscripcion)
    return sorted_forms


def reprocess_future_multipropietarios(db: SQLAlchemy, handler, future_multipropietarios: List[Multipropietario]):
    future_formularios = get_formularios_from_multipropietarios(future_multipropietarios)
    future_formulario_objects: List[FormularioObject] = convert_formularios_to_formulario_objects(handler, future_formularios)
    reprocess_formularios(db, handler, future_formulario_objects)


def convert_formularios_to_formulario_objects(handler, formularios: List[Formulario]):
    formulario_objects: List[FormularioObject] = list(map(handler.convert_formulario_into_object, formularios))
    return formulario_objects


def reprocess_formularios(db: SQLAlchemy, handler, formularios: List[Formulario]):
    for form_object in formularios:
        handler.process_new_formulario_object(form_object)
        db.session.commit()


def add_formulario_with_multipropietarios_and_sort(formulario: Formulario, multipropietarios: List[Multipropietario]):
    past_formularios: List[Formulario] = get_formularios_from_multipropietarios(multipropietarios)
    past_formularios.append(formulario)
    sorted_formularios = sorted(list(past_formularios), key=lambda x: x.fecha_inscripcion)
    return sorted_formularios
