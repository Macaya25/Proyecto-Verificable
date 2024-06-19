from typing import List, Set
from datetime import date
from models import Multipropietario, Adquirente, Enajenante, Formulario, Comuna
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import asc


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

    def __repr__(self):
        return f"CNE: {self.cne}, Rol: {self.comuna}-{self.manzana}-{self.predio}, Fecha: {self.fecha_inscripcion}"


def remove_from_multipropietario(db, entries_after_current_form: List[Multipropietario]):
    for entry in entries_after_current_form:
        print('Removing: ', entry)
        db.session.delete(entry)
        db.session.commit()


def element_exist(session, element):
    return session.query(Multipropietario).filter_by(comuna=element.comuna,
                                                     manzana=element.manzana,
                                                     predio=element.predio,
                                                     run_rut=element.run_rut,
                                                     fojas=element.fojas,
                                                     porc_derecho=element.porc_derecho,
                                                     ano_vigencia_inicial=element.ano_vigencia_inicial,
                                                     ano_vigencia_final=element.ano_vigencia_final,
                                                     fecha_inscripcion=element.fecha_inscripcion).first()


def reprocess_multipropietario_entries_with_new_formulario(db, handler, formulario, entries: List[Multipropietario]):
    print('Multiprop: ', entries)
    sorted_formularios = add_formulario_with_multipropietarios_and_sort(db, formulario, entries)
    print('Sorted: ', sorted_formularios)
    remove_from_multipropietario(db, entries)
    reprocess_formularios(db, handler, sorted_formularios)


def limit_date_of_last_entries_from_multipropietario(formulario: FormularioObject, previous_entries: List[Multipropietario]):
    sorted_entries = sorted(list(previous_entries), key=lambda x: x.ano_vigencia_inicial)

    last_period_year = sorted_entries[-1].ano_vigencia_inicial
    for entry in previous_entries:
        if entry.ano_vigencia_inicial == last_period_year:
            entry.ano_vigencia_final = formulario.fecha_inscripcion.year - 1


def reprocess_multipropietario_entries(db, handler, entries: List[Multipropietario]):
    formularios = get_formularios_from_multipropietarios(db, entries)
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


def get_formularios_from_multipropietarios(db, entries: List[Multipropietario]) -> List[Formulario]:
    forms: Set[Formulario] = set()
    print(entries)
    for entry in entries:
        source_form = db.session.query(Formulario).filter_by(
            comuna=entry.comuna, manzana=entry.manzana, predio=entry.predio,
            fojas=entry.fojas, fecha_inscripcion=entry.fecha_inscripcion).first()
        print('Source: ', db.session.query(Comuna).all())
        if source_form:
            forms.add(source_form)
    sorted_forms = sorted(list(forms), key=lambda x: x.fecha_inscripcion)
    return sorted_forms


def reprocess_future_multipropietarios(db: SQLAlchemy, handler, future_multipropietarios: List[Multipropietario]):
    future_formularios = get_formularios_from_multipropietarios(db, future_multipropietarios)
    future_formulario_objects: List[FormularioObject] = convert_formularios_to_formulario_objects(handler, future_formularios)
    reprocess_formularios(db, handler, future_formulario_objects)


def convert_formularios_to_formulario_objects(handler, formularios: List[Formulario]):
    formulario_objects: List[FormularioObject] = list(map(handler.convert_formulario_into_object, formularios))
    return formulario_objects


def reprocess_formularios(db: SQLAlchemy, handler, formularios: List[Formulario]):
    for form_object in formularios:
        handler.process_new_formulario_object(db, form_object)
        db.session.commit()


def add_formulario_with_multipropietarios_and_sort(db, formulario: Formulario, multipropietarios: List[Multipropietario]):
    past_formularios: List[Formulario] = get_formularios_from_multipropietarios(db, multipropietarios)
    print('Formularios to reprocess: ', past_formularios)
    past_formularios.append(formulario)
    sorted_formularios = sorted(list(past_formularios), key=lambda x: x.fecha_inscripcion)
    return sorted_formularios


def merge_multipropietarios(db: SQLAlchemy, formulario: FormularioObject) -> List[Multipropietario]:
    print('Merging')
    multipropietarios = db.session.query(Multipropietario).filter_by(comuna=formulario.comuna,
                                                                     manzana=formulario.manzana,
                                                                     predio=formulario.predio
                                                                     ).order_by(asc(Multipropietario.ano_vigencia_inicial))
    temp_multipropietarios = multipropietarios.all()
    last_period_year = temp_multipropietarios[-1].ano_vigencia_inicial
    multipropietarios = multipropietarios.filter_by(ano_vigencia_inicial=last_period_year).all()

    merged_dict = {}

    for obj in multipropietarios:
        key = (obj.comuna, obj.manzana, obj.predio, obj.run_rut)

        if key in merged_dict:
            merged_dict[key].porc_derecho += obj.porc_derecho

            # Mark duplicate for deletion
            db.session.delete(obj)
        else:
            merged_dict[key] = obj

    # Update the existing multipropietarios in the database with merged values
    for key, merged_obj in merged_dict.items():
        if merged_obj.porc_derecho < 0:
            merged_obj.porc_derecho = 0
        db.session.add(merged_obj)

    # Commit the session to save the changes
    db.session.commit()


def ajustar_porcentajes(db: SQLAlchemy, formulario: FormularioObject):
    multipropietarios: List[Multipropietario] = db.session.query(Multipropietario).filter_by(
        comuna=formulario.comuna,
        manzana=formulario.manzana,
        predio=formulario.predio
    ).order_by(asc(Multipropietario.ano_vigencia_inicial))

    temp_multipropietarios = multipropietarios.all()
    last_period_year = temp_multipropietarios[-1].ano_vigencia_inicial

    multipropietarios = multipropietarios.filter_by(ano_vigencia_inicial=last_period_year).all()

    total_percentage = 0
    for multiprop in multipropietarios:
        total_percentage += multiprop.porc_derecho

    if total_percentage > 100:
        print('More than 100')
        for multiprop in multipropietarios:
            multiprop.porc_derecho = multiprop.porc_derecho * 100 / total_percentage

    elif total_percentage < 100:
        print('Percentage: ', total_percentage)
        missing_percentage = 100 - total_percentage

        missing_elements_amount = 0
        for multiprop in multipropietarios:
            print(multiprop)
            if multiprop.porc_derecho == 0:
                missing_elements_amount += 1

        for multiprop in multipropietarios:
            if multiprop.porc_derecho == 0:
                multiprop.porc_derecho = missing_percentage / missing_elements_amount
