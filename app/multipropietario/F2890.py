from typing import List
from multipropietario.multipropietario_tools import (
    generate_multipropietario_entry_from_formulario, FormularioObject, remove_from_multipropietario, element_exist)
from flask_sqlalchemy import SQLAlchemy
from models import Multipropietario, Formulario
from tools import is_empty, CONSTANTS


class RegularizacionPatrimonio:

    @staticmethod
    def check_escenario(tabla_multipropietario: List[Multipropietario],
                        before_current_form: List[Multipropietario],
                        after_current_form: List[Multipropietario],
                        same_year_current_form: List[Multipropietario]) -> int:
        if is_empty(tabla_multipropietario):
            return CONSTANTS.ESCENARIO1_VALUE

        if not is_empty(same_year_current_form):
            return CONSTANTS.ESCENARIO4_VALUE

        if not is_empty(before_current_form) and is_empty(after_current_form):
            return CONSTANTS.ESCENARIO2_VALUE

        if not is_empty(after_current_form):
            return CONSTANTS.ESCENARIO3_VALUE

        else:
            return CONSTANTS.INVALID_ESCENARIO_VALUE

    @staticmethod
    def limit_date_of_last_entries_from_multipropietario(formulario: FormularioObject, previous_entries: List[Multipropietario]):
        sorted_entries = sorted(list(previous_entries), key=lambda x: x.ano_vigencia_inicial)

        last_period_year = sorted_entries[-1].ano_vigencia_inicial
        for entry in previous_entries:
            if entry.ano_vigencia_inicial == last_period_year:
                entry.ano_vigencia_final = formulario.fecha_inscripcion.year - 1

    @staticmethod
    def add_form_to_multipropietario(db: SQLAlchemy, formulario: FormularioObject):
        for adquiriente in formulario.adquirentes:
            rut_adquiriente = adquiriente.run_rut
            porc_derecho_adquiriente = adquiriente.porc_derecho

            new_multipropietario = generate_multipropietario_entry_from_formulario(
                formulario, rut_adquiriente, porc_derecho_adquiriente)
            db.session.add(new_multipropietario)


class CompraVenta:
    @staticmethod
    def sum_adquirientes_100(formulario: FormularioObject, db: SQLAlchemy, tabla_multipropietario: List[Multipropietario],
                             multipropietarios_solo_enajenantes: List[Multipropietario],
                             multipropietarios_sin_enajenantes: List[Multipropietario]):
        # caso 1 ADQ 100
        CompraVenta.update_multipropietario_unchanged_porcentaje(db, formulario, multipropietarios_sin_enajenantes)

        for adquirente in formulario.adquirentes:
            porc_derech_nuevo = (
                (adquirente.porc_derecho * CompraVenta.sum_porc_derecho(multipropietarios_solo_enajenantes))/100)
            new_multipropietario = generate_multipropietario_entry_from_formulario(formulario, adquirente.run_rut, porc_derech_nuevo)
            db.session.add(new_multipropietario)

        CompraVenta.limit_date_or_delete_multipropietarios_entries(db, formulario, tabla_multipropietario)

    @staticmethod
    def update_multipropietario_unchanged_porcentaje(db: SQLAlchemy, formulario: Formulario, multipropietarios_sin_enajenantes):
        for multipropietario in multipropietarios_sin_enajenantes:
            multipropietario = CompraVenta.update_multipropietario_into_new_multipropietarios(multipropietario, formulario)
            db.session.add(multipropietario)

    @staticmethod
    def limit_date_or_delete_multipropietarios_entries(db: SQLAlchemy, formulario, tabla_multipropietario: List[Multipropietario]):
        for multipropietario in tabla_multipropietario:
            CompraVenta.update_multipropietario_ano_final(db, formulario, multipropietario)

    @staticmethod
    def sum_adquirientes_0(formulario: FormularioObject, db: SQLAlchemy,
                           multipropietarios_solo_enajenantes: List[Multipropietario],
                           multipropietarios_sin_enajenantes: List[Multipropietario]):
        porc_derecho_nuevo = (CompraVenta.sum_porc_derecho(multipropietarios_solo_enajenantes)/len(formulario.adquirentes))

        for adquirente in formulario.adquirentes:
            new_multipropietario = generate_multipropietario_entry_from_formulario(formulario, adquirente.run_rut, porc_derecho_nuevo)
            db.session.add(new_multipropietario)

        CompraVenta.limit_date_or_delete_multipropietarios_entries(db, formulario, multipropietarios_solo_enajenantes)

        if multipropietarios_solo_enajenantes[-1].ano_vigencia_inicial != formulario.fecha_inscripcion.year:
            CompraVenta.update_multipropietario_unchanged_porcentaje(db, formulario, multipropietarios_sin_enajenantes)

    @staticmethod
    def Enajenante_1_Adquiriente_1(formulario: FormularioObject, db: SQLAlchemy, tabla_multipropietario: List[Multipropietario],
                                   multipropietarios_solo_enajenantes: List[Multipropietario],
                                   multipropietarios_sin_enajenantes: List[Multipropietario]):
        # caso 3 ADQ 1-99 ENA y ADQ == 1

        CompraVenta.limit_date_or_delete_multipropietarios_entries(db, formulario, tabla_multipropietario)

        porc_derecho_nuevo_adq = (
            (formulario.adquirentes[0].porc_derecho * CompraVenta.sum_porc_derecho(multipropietarios_solo_enajenantes))/100)
        porc_derecho_nuevo_ena = CompraVenta.sum_porc_derecho(multipropietarios_solo_enajenantes) - porc_derecho_nuevo_adq

        CompraVenta.update_porcentaje_on_enajenantes(db, formulario, multipropietarios_solo_enajenantes, porc_derecho_nuevo_ena)
        CompraVenta.update_multipropietario_unchanged_porcentaje(db, formulario, multipropietarios_sin_enajenantes)

        new_multipropietario = generate_multipropietario_entry_from_formulario(
            formulario, formulario.adquirentes[0].run_rut, porc_derecho_nuevo_adq)
        db.session.add(new_multipropietario)

    @staticmethod
    def update_multipropietario_change_porcentaje(formulario: Formulario, multipropietario: Multipropietario, new_derecho):
        return Multipropietario(
            comuna=formulario.comuna,
            manzana=formulario.manzana,
            predio=formulario.predio,
            run_rut=multipropietario.run_rut,
            porc_derecho=new_derecho,
            fojas=multipropietario.fojas,
            ano_inscripcion=multipropietario.fecha_inscripcion.year,
            num_inscripcion=multipropietario.num_inscripcion,
            fecha_inscripcion=multipropietario.fecha_inscripcion,
            ano_vigencia_inicial=formulario.fecha_inscripcion.year,
            ano_vigencia_final=None
        )

    @staticmethod
    def update_porcentaje_on_enajenantes(db: SQLAlchemy, formulario: Formulario,
                                         multipropietarios_solo_enajenantes: List[Multipropietario], porc_derech_nuevo_ena):
        for multipropietario in multipropietarios_solo_enajenantes:
            updated_previous_multipropietario = CompraVenta.update_multipropietario_change_porcentaje(
                formulario, multipropietario, porc_derech_nuevo_ena)
            db.session.add(updated_previous_multipropietario)

    @staticmethod
    def multiples_adquirientes_and_enajenantes_1_99(formulario: FormularioObject, db: SQLAlchemy, tabla_multipropietario,
                                                    multipropietarios_sin_enajenantes: List[Multipropietario]):
        # caso 4 else ADQ 1-99 ENA y ADQ !=1

        CompraVenta.limit_date_or_delete_multipropietarios_entries(db, formulario, tabla_multipropietario)

        CompraVenta.update_multipropietario_unchanged_porcentaje(db, formulario, multipropietarios_sin_enajenantes)

        for multipropietario in tabla_multipropietario:
            for enajenante in formulario.enajenantes:
                if multipropietario.run_rut == enajenante.run_rut:
                    final_porc_derecho = multipropietario.porc_derecho - enajenante.porc_derecho

                    if final_porc_derecho > 0:
                        updated_previous_multipropietario = CompraVenta.update_multipropietario_change_porcentaje(
                            formulario, multipropietario, final_porc_derecho)

                        db.session.add(updated_previous_multipropietario)

        print('Formulario adqs: ', formulario.adquirentes)
        for adquiriente in formulario.adquirentes:
            new_multipropietario = generate_multipropietario_entry_from_formulario(
                formulario, adquiriente.run_rut, adquiriente.porc_derecho)
            if not element_exist(db.session, new_multipropietario):
                db.session.add(new_multipropietario)

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
        multipropietario: Multipropietario,
        formulario: Formulario
    ) -> Multipropietario:
        ano_vigencia_inicial = formulario.fecha_inscripcion.year
        ano_vigencia_final = None
        return Multipropietario(
            comuna=formulario.comuna,
            manzana=formulario.manzana,
            predio=formulario.predio,
            run_rut=multipropietario.run_rut,
            porc_derecho=multipropietario.porc_derecho,
            fojas=multipropietario.fojas,
            ano_inscripcion=multipropietario.fecha_inscripcion.year,
            num_inscripcion=multipropietario.num_inscripcion,
            fecha_inscripcion=multipropietario.fecha_inscripcion,
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
