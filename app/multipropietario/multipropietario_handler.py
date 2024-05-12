from datetime import datetime
from typing import List
from sqlalchemy import asc, and_, or_
from multipropietario.multipropietario_tools import (
    FormularioObject, reprocess_future_multipropietarios,
    check_escenario, get_formularios_from_multipropietarios,
    remove_from_multipropietario, reprocess_formularios)
from multipropietario.escenarios import Nivel0, Nivel1

from models import db, Multipropietario, Enajenante, Adquirente, Formulario
from forms import FormularioForm
from tools import (
    CONSTANTS)


class MultipropietarioHandler:
    def process_new_formulario(self, formulario: FormularioObject):
        print('New formulario: ', formulario.num_inscripcion,
              formulario.fecha_inscripcion)
        if formulario.cne == CONSTANTS.CNE_REGULARIZACION.value:
            print("Nivel 0")
            self.nivel_0(formulario)
        elif formulario.cne == CONSTANTS.CNE_COMPRAVENTA.value:
            print("Nivel 1")
            self.nivel_1(formulario)
        else:
            print(f"Nivel inesperado: {formulario.cne}")

    def nivel_0(self, formulario: FormularioObject):
        query = Multipropietario.query.filter_by(
            comuna=formulario.comuna,
            manzana=formulario.manzana,
            predio=formulario.predio
        ).order_by(asc(Multipropietario.ano_vigencia_inicial))
        tabla_multipropietario: List[Multipropietario] = query.all()

        before_current_form_query = query.filter(
            Multipropietario.ano_vigencia_inicial < formulario.fecha_inscripcion)
        before_current_form = before_current_form_query.all()

        same_year_current_form_query = query.filter(
            Multipropietario.ano_vigencia_inicial == formulario.fecha_inscripcion)
        same_year_current_form = same_year_current_form_query.all()

        after_current_form_query = query.filter(
            Multipropietario.ano_vigencia_inicial > formulario.fecha_inscripcion)
        after_current_form = after_current_form_query.all()

        current_escenario = check_escenario(tabla_multipropietario,
                                            before_current_form, after_current_form,
                                            same_year_current_form)

        match current_escenario:
            case 1:
                print('E1')
                Nivel0.escenario_1(db, formulario)
            case 2:
                print('E2')
                Nivel0.escenario_2(db, formulario,
                                   before_current_form_query)
            case 3:
                print('E3')
                Nivel0.escenario_3(self, db, formulario,
                                   after_current_form)
            case 4:
                print('E4')
                Nivel0.escenario_4(self, db, formulario,
                                   same_year_current_form)
            case _:
                print('Escenario inesperado.')

    def nivel_1(self, formulario: FormularioObject):
        def enajenante_fantasma():
            if tabla_multipropietario is None or len(tabla_multipropietario) == 0:
                print('No existe tabla')
                return False
            # Check if each enajenante.run_rut exists in run_ruts
            for enajenante in formulario.enajenantes:
                if enajenante.run_rut not in run_ruts:
                    return False
            # If all enajenantes are found, return True
            return True

        print('Nivel 1')
        query = Multipropietario.query.filter(
            and_(
                Multipropietario.comuna == formulario.comuna,
                Multipropietario.manzana == formulario.manzana,
                Multipropietario.predio == formulario.predio,
                Multipropietario.ano_vigencia_inicial <= formulario.fecha_inscripcion,
                or_(
                    Multipropietario.ano_vigencia_final >= formulario.fecha_inscripcion,
                    Multipropietario.ano_vigencia_final.is_(None)
                )
            )
        )

        future_query = Multipropietario.query.filter(
            and_(
                Multipropietario.comuna == formulario.comuna,
                Multipropietario.manzana == formulario.manzana,
                Multipropietario.predio == formulario.predio,
                Multipropietario.fecha_inscripcion > formulario.fecha_inscripcion
            )
        )
        future_multipropietarios: List[Multipropietario] = future_query.all()

        tabla_multipropietario: List[Multipropietario] = query.all()
        # print('Tabla: ', tabla_multipropietario)
        run_ruts = {
            multipropietario.run_rut for multipropietario in tabla_multipropietario}

        # Create a list of run_ruts for all enajenantes
        enajenante_run_ruts = [
            enajenante.run_rut for enajenante in formulario.enajenantes]

        # Create a new list of multipropietarios that are not enajenantes
        multipropietarios_sin_enajenantes = [
            multipropietario for multipropietario in tabla_multipropietario if multipropietario.run_rut not in enajenante_run_ruts]

        multipropietarios_solo_enajenantes = [
            multipropietario for multipropietario in tabla_multipropietario if multipropietario.run_rut in enajenante_run_ruts]

        # if enajenante_fantasma():
        sum_porc_adquirientes = Nivel1.sum_porc_derecho(formulario.adquirentes)

        if sum_porc_adquirientes == 100:
            if future_multipropietarios:
                print('Futuro encontrado.')
                remove_from_multipropietario(db, tabla_multipropietario)
                db.session.commit()
                past_formularios: List[Formulario] = get_formularios_from_multipropietarios(tabla_multipropietario)
                past_formularios.append(formulario)
                sorted_formularios = sorted(list(past_formularios), key=lambda x: x.fecha_inscripcion)
                print(sorted_formularios)
                reprocess_formularios(db, self, sorted_formularios)

            else:
                Nivel1.escenario_1(formulario, db, tabla_multipropietario,
                                   multipropietarios_solo_enajenantes, multipropietarios_sin_enajenantes)

        elif sum_porc_adquirientes == 0:
            print('2')
            if future_multipropietarios:
                print('Futuro encontrado.')
                remove_from_multipropietario(db, tabla_multipropietario)
                db.session.commit()
                past_formularios: List[Formulario] = get_formularios_from_multipropietarios(tabla_multipropietario)
                past_formularios.append(formulario)
                sorted_formularios = sorted(list(past_formularios), key=lambda x: x.fecha_inscripcion)
                print(sorted_formularios)
                reprocess_formularios(db, self, sorted_formularios)

            else:
                Nivel1.escenario_2(formulario, db, tabla_multipropietario,
                                   multipropietarios_solo_enajenantes, multipropietarios_sin_enajenantes)

        elif len(formulario.enajenantes) == 1 and len(formulario.adquirentes) == 1 and 0 < sum_porc_adquirientes < 100:
            print('3')
            if future_multipropietarios:
                print('Futuro encontrado.')
                remove_from_multipropietario(db, tabla_multipropietario)
                db.session.commit()
                past_formularios: List[Formulario] = get_formularios_from_multipropietarios(tabla_multipropietario)
                past_formularios.append(formulario)
                sorted_formularios = sorted(list(past_formularios), key=lambda x: x.fecha_inscripcion)
                print(sorted_formularios)
                reprocess_formularios(db, self, sorted_formularios)
            else:
                Nivel1.escenario_3(formulario, db, tabla_multipropietario,
                                   multipropietarios_solo_enajenantes, multipropietarios_sin_enajenantes)

        else:
            print('4')
            if future_multipropietarios:
                remove_from_multipropietario(db, tabla_multipropietario)
                past_formularios: List[Formulario] = get_formularios_from_multipropietarios(tabla_multipropietario)
                past_formularios.append(formulario)
                sorted_formularios = sorted(list(past_formularios), key=lambda x: x.fecha_inscripcion)
                reprocess_formularios(db, self, sorted_formularios)

            else:
                Nivel1.escenario_4(formulario, db, tabla_multipropietario,
                                   multipropietarios_solo_enajenantes, multipropietarios_sin_enajenantes)

        # else:
        #     print("enajenante fantasma")

    def convert_form_into_object(self, form: FormularioForm) -> FormularioObject:
        parsed_enajenantes = []
        parsed_adquirentes = []
        for enajenante in form.enajenantes:
            parsed_enajenantes.append(Enajenante(
                run_rut=enajenante['run_rut'].data, porc_derecho=enajenante['porc_derecho'].data))

        for adquirente in form.adquirentes:
            parsed_adquirentes.append(Enajenante(
                run_rut=adquirente['run_rut'].data, porc_derecho=adquirente['porc_derecho'].data))

        return FormularioObject(cne=form.cne.data,
                                comuna=form.comuna.data,
                                manzana=form.manzana.data,
                                predio=form.predio.data,
                                fojas=form.fojas.data,
                                fecha_inscripcion=form.fecha_inscripcion.data,
                                num_inscripcion=form.num_inscripcion.data,
                                enajenantes=parsed_enajenantes,
                                adquirentes=parsed_adquirentes)

    def convert_json_into_object_list(self, json_form: dict) -> List[FormularioObject]:
        objects = []

        for form in json_form['F2890']:
            current_comuna = current_manzana = current_predio = None

            current_cne = form.get('CNE')
            current_fojas = form.get('fojas')

            try:
                current_fecha_inscripcion = datetime.strptime(
                    form.get('fechaInscripcion'), "%Y-%m-%d").date()
            except ValueError:
                continue

            current_num_inscripcion = form.get('nroInscripcion')
            rol = form.get('bienRaiz')
            if rol:
                current_comuna = rol.get('comuna')
                current_manzana = rol.get('manzana')
                current_predio = rol.get('predio')

            parsed_enajenantes = []
            if form.get('enajenantes'):
                for enajenante in form.get('enajenantes'):
                    parsed_enajenantes.append(Enajenante(run_rut=enajenante.get('RUNRUT'),
                                                         porc_derecho=enajenante.get('porcDerecho')))

            parsed_adquirentes = []
            if form.get('adquirentes'):
                for adquirente in form.get('adquirentes'):
                    parsed_adquirentes.append(Adquirente(run_rut=adquirente.get('RUNRUT'),
                                                         porc_derecho=adquirente.get('porcDerecho')))

            current_object = FormularioObject(current_cne, current_comuna, current_manzana,
                                              current_predio, current_fojas, current_fecha_inscripcion, current_num_inscripcion,
                                              parsed_enajenantes, parsed_adquirentes)
            objects.append(current_object)

        return objects

    def convert_formulario_into_object(self, formulario: Formulario) -> FormularioObject:
        enajenantes = Enajenante.query.filter_by(form_id=formulario.n_atencion).all()
        adquirentes = Adquirente.query.filter_by(form_id=formulario.n_atencion).all()

        return FormularioObject(formulario.cne, formulario.comuna, formulario.manzana, formulario.predio,
                                formulario.fojas, formulario.fecha_inscripcion, formulario.num_inscripcion,
                                enajenantes, adquirentes)
