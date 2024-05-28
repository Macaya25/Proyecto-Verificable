from typing import List
from multipropietario.multipropietario_tools import (
    generate_multipropietario_entry_from_formulario, FormularioObject,
    remove_from_multipropietario, generate_formularios_json_from_multipropietario,
    reprocess_formularios, add_formulario_with_multipropietarios_and_sort)
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
            remove_from_multipropietario(db, same_year_current_form)
            sorted_formularios = add_formulario_with_multipropietarios_and_sort(formulario, same_year_current_form)
            reprocess_formularios(db, handler, sorted_formularios)

        elif current_date == previous_date:
            if formulario.num_inscripcion > same_year_current_form[0].num_inscripcion:
                Nivel0.add_form_to_multipropietario(db, formulario)
            elif formulario.num_inscripcion < same_year_current_form[0].num_inscripcion:
                remove_from_multipropietario(db, same_year_current_form)
                sorted_formularios = add_formulario_with_multipropietarios_and_sort(formulario, same_year_current_form)
                reprocess_formularios(db, handler, sorted_formularios)

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
            converted_forms_list = handler.convert_json_into_object_list(json_to_reprocess)
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
                db, formulario, multipropietario)

        for multipropietario in multipropietarios_sin_enajenantes:
            multipropietario = Nivel1.update_multipropietario_into_new_multipropietarios(multipropietario, formulario)
            db.session.add(multipropietario)

    @staticmethod
    def escenario_2(formulario: FormularioObject, db: SQLAlchemy,
                    multipropietarios_solo_enajenantes: List[Multipropietario],
                    multipropietarios_sin_enajenantes: List[Multipropietario]):

        porc_derech_nuevo = (
            Nivel1.sum_porc_derecho(multipropietarios_solo_enajenantes)/len(formulario.adquirentes))

        for adquirente in formulario.adquirentes:
            new_multipropietario = generate_multipropietario_entry_from_formulario(
                formulario, adquirente.run_rut, porc_derech_nuevo)
            db.session.add(new_multipropietario)

        for multipropietario in multipropietarios_solo_enajenantes:
            Nivel1.update_multipropietario_ano_final(db, formulario, multipropietario)

        if multipropietario.ano_vigencia_inicial != formulario.fecha_inscripcion.year:
            for multipropietario in multipropietarios_sin_enajenantes:
                multipropietario = Nivel1.update_multipropietario_into_new_multipropietarios(
                    multipropietario, formulario)
                db.session.add(multipropietario)

    @staticmethod
    def escenario_3(formulario: FormularioObject, db: SQLAlchemy, tabla_multipropietario: List[Multipropietario],
                    multipropietarios_solo_enajenantes: List[Multipropietario],
                    multipropietarios_sin_enajenantes: List[Multipropietario]):
        # caso 3 ADQ 1-99 ENA y ADQ == 1
        for previous_entry in tabla_multipropietario:
            Nivel1.update_multipropietario_ano_final(db, formulario, previous_entry)

        porc_derech_nuevo_adq = (
            (formulario.adquirentes[0].porc_derecho * Nivel1.sum_porc_derecho(multipropietarios_solo_enajenantes))/100)
        porc_derech_nuevo_ena = Nivel1.sum_porc_derecho(multipropietarios_solo_enajenantes) - porc_derech_nuevo_adq
        new_multipropietario = generate_multipropietario_entry_from_formulario(
            formulario, formulario.adquirentes[0].run_rut, porc_derech_nuevo_adq)
        db.session.add(new_multipropietario)

        updated_previous_multipropietario = generate_multipropietario_entry_from_formulario(
            formulario, formulario.enajenantes[0].run_rut, porc_derech_nuevo_ena)
        db.session.add(updated_previous_multipropietario)

        for multipropietario in multipropietarios_sin_enajenantes:
            multipropietario = Nivel1.update_multipropietario_into_new_multipropietarios(multipropietario, formulario)
            db.session.add(multipropietario)

    @staticmethod
    def escenario_4(formulario: FormularioObject, db: SQLAlchemy, tabla_multipropietario: List[Multipropietario],
                    multipropietarios_sin_enajenantes: List[Multipropietario]):
        # caso 4 else ADQ 1-99 ENA y ADQ !=1
        for previous_entry in tabla_multipropietario:
            Nivel1.update_multipropietario_ano_final(db, formulario, previous_entry)

        for multipropietario in tabla_multipropietario:
            for enajenante in formulario.enajenantes:
                if multipropietario.run_rut == enajenante.run_rut:
                    final_porc_derecho = multipropietario.porc_derecho - enajenante.porc_derecho

                    if final_porc_derecho > 0:
                        updated_previous_multipropietario = generate_multipropietario_entry_from_formulario(
                            formulario, enajenante.run_rut, final_porc_derecho)
                        db.session.add(updated_previous_multipropietario)

        for adquiriente in formulario.adquirentes:
            new_multipropietario = generate_multipropietario_entry_from_formulario(
                formulario, adquiriente.run_rut, adquiriente.porc_derecho)
            db.session.add(new_multipropietario)

        for multipropietario in multipropietarios_sin_enajenantes:
            multipropietario = Nivel1.update_multipropietario_into_new_multipropietarios(
                multipropietario, formulario)
            db.session.add(multipropietario)

    @staticmethod
    def sum_porc_derecho(lst) -> float:
        sum_porc = sum(person.porc_derecho for person in lst)
        return sum_porc

    @staticmethod
    def update_multipropietario_ano_final(db: SQLAlchemy, formulario: FormularioObject,
                                          multipropietario: Multipropietario):
        if multipropietario.ano_vigencia_inicial < formulario.fecha_inscripcion.year:
            multipropietario.ano_vigencia_final = formulario.fecha_inscripcion.year - 1
        else:
            if multipropietario.ano_vigencia_inicial == formulario.fecha_inscripcion.year:
                remove_from_multipropietario(db, [multipropietario])

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

    @staticmethod
    def separate_multipropietario_enajenantes_from_multipropietario_list(
            tabla_multipropietario: List[Multipropietario], enajenante_run_ruts):
        # Create a new list of multipropietarios that are not enajenantes
        multipropietarios_sin_enajenantes = [
            multipropietario
            for multipropietario in tabla_multipropietario
            if multipropietario.run_rut not in enajenante_run_ruts
        ]

        multipropietarios_solo_enajenantes = [
            multipropietario
            for multipropietario in tabla_multipropietario
            if multipropietario.run_rut in enajenante_run_ruts]

        return multipropietarios_sin_enajenantes, multipropietarios_solo_enajenantes

    @staticmethod
    def enajenante_fantasma(tabla_multipropietario: List[Multipropietario], formulario: Formulario, run_ruts):
        if tabla_multipropietario is None or len(tabla_multipropietario) == 0:
            print('No existe tabla')
            return False
        # Check if each enajenante.run_rut exists in run_ruts
        for enajenante in formulario.enajenantes:
            if enajenante.run_rut not in run_ruts:
                return False
        # If all enajenantes are found, return True
        return True
