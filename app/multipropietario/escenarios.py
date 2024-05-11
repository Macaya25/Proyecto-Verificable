from typing import List
from multipropietario.multipropietario_tools import (
    generate_multipropietario_entry_from_formulario, FormularioObject,
    remove_from_multipropietario, generate_formularios_json_from_multipropietario,
    get_formularios_from_multipropietarios)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Query
from models import Multipropietario, Formulario
from tools import process_and_save_json_into_db


class Nivel0:
    @staticmethod
    def escenario_1(db: SQLAlchemy, formulario: FormularioObject):
        Nivel0.add_form_to_multipropietario(db, formulario)

    @staticmethod
    def escenario_2(db: SQLAlchemy, formulario: FormularioObject, query: Query[Multipropietario]):
        last_entries = query.filter_by(ano_vigencia_final=None).all()
        for entry in last_entries:
            if entry.ano_vigencia_final is None:
                entry.ano_vigencia_final = formulario.fecha_inscripcion.year - 1

        Nivel0.add_form_to_multipropietario(db, formulario)

    @staticmethod
    def escenario_3(handler, db: SQLAlchemy, formulario: FormularioObject,
                    entries_after_current_form: List[Multipropietario]):
        json_to_reprocess: dict = generate_formularios_json_from_multipropietario(
            entries_after_current_form)

        remove_from_multipropietario(db, entries_after_current_form)

        Nivel0.add_form_to_multipropietario(db, formulario)

        Nivel0.remove_formularios_given_json(db, json_to_reprocess)
        Nivel0.reprocess_json(handler, db, json_to_reprocess)

    @staticmethod
    def escenario_4(handler, db: SQLAlchemy, formulario: FormularioObject,
                    same_year_current_form: List[Multipropietario]):

        current_date = formulario.fecha_inscripcion
        previous_date = same_year_current_form[0].fecha_inscripcion

        remove_from_multipropietario(db, same_year_current_form)

        if current_date > previous_date:
            Nivel0.add_form_to_multipropietario(db, formulario)

        elif current_date < previous_date:
            same_year_formulario_objects: List[FormularioObject] = list(map(get_formularios_from_multipropietarios,
                                                                        same_year_current_form))
            for form_object in same_year_formulario_objects:
                handler.process_new_formulario(form_object)

        elif current_date == previous_date:
            if formulario.num_inscripcion > same_year_current_form[0].num_inscripcion:
                Nivel0.add_form_to_multipropietario(db, formulario)
            elif formulario.num_inscripcion < same_year_current_form[0].num_inscripcion:
                same_year_formulario_objects: List[FormularioObject] = list(map(get_formularios_from_multipropietarios,
                                                                                same_year_current_form))
                for form_object in same_year_formulario_objects:
                    handler.process_new_formulario(form_object)

    @staticmethod
    def add_form_to_multipropietario(db: SQLAlchemy, formulario: FormularioObject):
        for adquiriente in formulario.adquirentes:
            rut_adquiriente = adquiriente.run_rut
            porc_derecho_adquiriente = adquiriente.porc_derecho

            new_multipropietario = generate_multipropietario_entry_from_formulario(
                formulario, rut_adquiriente, porc_derecho_adquiriente)
            db.session.add(new_multipropietario)

    @staticmethod
    def reprocess_json(handler, db: SQLAlchemy, json_to_reprocess):
        if process_and_save_json_into_db(db, json_to_reprocess):
            converted_forms_list = handler.convert_json_into_object_list(
                json_to_reprocess)
            for form in converted_forms_list:
                handler.process_new_form(form)

    @staticmethod
    def remove_formularios_given_json(db: SQLAlchemy, json_to_reprocess):
        for form in json_to_reprocess['F2890']:
            rol = form['bienRaiz']
            forms_to_delete: List[Formulario] = Formulario.query.filter_by(
                cne=form['CNE'], fojas=form['fojas'],
                comuna=rol['comuna'], manzana=rol['manzana'], predio=rol['predio'],
                fecha_inscripcion=form['fechaInscripcion'], num_inscripcion=form['nroInscripcion']).all()
            for f in forms_to_delete:
                db.session.delete(f)

        db.session.commit()


class Nivel1:
    @staticmethod
    def escenario_1(formulario: FormularioObject, db: SQLAlchemy, tabla_multipropietario: List[Multipropietario],
                    multipropietarios_solo_enajenantes: List[Multipropietario],
                    multipropietarios_sin_enajenantes: List[Multipropietario]):
        print('E1')
        # caso 1 ADQ 100
        for adquirente in formulario.adquirentes:
            porc_derech_nuevo = (
                (adquirente.porc_derecho * Nivel1.sum_porc_derecho(multipropietarios_solo_enajenantes))/100)
            new_multipropietario = generate_multipropietario_entry_from_formulario(
                formulario, adquirente.run_rut, porc_derech_nuevo)
            db.session.add(new_multipropietario)
        for multipropietario in tabla_multipropietario:
            Nivel1.update_multipropietario_ano_final(
                formulario, multipropietario)

        for multipropietario in multipropietarios_sin_enajenantes:
            multipropietario = Nivel1.update_multipropietario_into_new_multipropietarios(
                multipropietario, formulario)
            db.session.add(multipropietario)

    @staticmethod
    def sum_porc_derecho(lst):
        sum_porc = sum(person.porc_derecho for person in lst)
        return sum_porc

    @staticmethod
    def update_multipropietario_ano_final(formulario: FormularioObject, multipropietario: Multipropietario):
        if multipropietario.ano_vigencia_inicial < formulario.fecha_inscripcion.year:
            # Set ano_vigencia_final to one year less than formulario.fecha_inscripcion
            multipropietario.ano_vigencia_final = (
                formulario.fecha_inscripcion.year - 1)
            return multipropietario
        else:
            # Set ano_vigencia_final to the same year as formulario.fecha_inscripcion
            multipropietario.ano_vigencia_final = formulario.fecha_inscripcion
            return multipropietario

    @staticmethod
    def update_multipropietario_into_new_multipropietarios(
        multiproppietario: Multipropietario,
        formulario: Formulario
    ) -> Multipropietario:
        ano_vigencia_inicial = formulario.fecha_inscripcion.year
        ano_vigencia_final = None
        return Multipropietario(
            comuna=formulario.comuna,
            manzana=formulario.manzana,
            predio=formulario.predio,
            run_rut=multiproppietario.run_rut,
            porc_derecho=multiproppietario.porc_derecho,
            fojas=multiproppietario.fojas,
            ano_inscripcion=multiproppietario.fecha_inscripcion.year,
            num_inscripcion=multiproppietario.num_inscripcion,
            fecha_inscripcion=multiproppietario.fecha_inscripcion,
            ano_vigencia_inicial=ano_vigencia_inicial,
            ano_vigencia_final=ano_vigencia_final
        )
