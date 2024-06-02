from datetime import datetime
from typing import List
from sqlalchemy import asc, and_, or_
from multipropietario.multipropietario_tools import (
    FormularioObject, reprocess_multipropietario_entries_with_new_formulario,
    remove_from_multipropietario, reprocess_multipropietario_entries, limit_date_of_last_entries_from_multipropietario)
from multipropietario.F2890 import Regularizacion_Patrimonio, CompraVenta

from models import db, Multipropietario, Enajenante, Adquirente, Formulario
from forms import FormularioForm
from tools import CONSTANTS


class MultipropietarioHandler:
    def process_new_formulario_object(self, formulario: FormularioObject):
        print('New formulario: ', formulario.num_inscripcion, formulario.fecha_inscripcion)

        if formulario.cne == CONSTANTS.CNE_REGULARIZACION:
            self.process_regularizacion_patrimonio(formulario)

        elif formulario.cne == CONSTANTS.CNE_COMPRAVENTA:
            self.process_compraventa(formulario)

        else:
            print(f"Nivel inesperado: {formulario.cne}")

    def process_regularizacion_patrimonio(self, formulario: FormularioObject):

        query = Multipropietario.query.filter_by(comuna=formulario.comuna,
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

        current_escenario = Regularizacion_Patrimonio.check_escenario(tabla_multipropietario,
                                                                      before_current_form, after_current_form,
                                                                      same_year_current_form)

        match current_escenario:
            case CONSTANTS.ESCENARIO1_VALUE:
                print('E1')
                Regularizacion_Patrimonio.add_form_to_multipropietario(db, formulario)

            case CONSTANTS.ESCENARIO2_VALUE:
                print('E2')
                limit_date_of_last_entries_from_multipropietario(formulario, before_current_form)
                Regularizacion_Patrimonio.add_form_to_multipropietario(db, formulario)

            case CONSTANTS.ESCENARIO3_VALUE:
                print('E3')
                remove_from_multipropietario(db, after_current_form)
                reprocess_multipropietario_entries_with_new_formulario(db, self, formulario, after_current_form)

            case CONSTANTS.ESCENARIO4_VALUE:
                print('E4')

                current_date = formulario.fecha_inscripcion
                previous_date = same_year_current_form[0].fecha_inscripcion

                if current_date > previous_date:
                    remove_from_multipropietario(db, same_year_current_form)
                    Regularizacion_Patrimonio.add_form_to_multipropietario(db, formulario)

                elif current_date < previous_date:
                    reprocess_multipropietario_entries_with_new_formulario(db, self, formulario, same_year_current_form)

                elif current_date == previous_date:
                    if formulario.num_inscripcion > same_year_current_form[0].num_inscripcion:
                        remove_from_multipropietario(db, same_year_current_form)
                        Regularizacion_Patrimonio.add_form_to_multipropietario(db, formulario)

                    elif formulario.num_inscripcion < same_year_current_form[0].num_inscripcion:
                        reprocess_multipropietario_entries_with_new_formulario(db, self, formulario, same_year_current_form)

                remove_from_multipropietario(db, after_current_form)
                reprocess_multipropietario_entries(db, self, after_current_form)

            case _:
                print('Escenario inesperado.')

    def process_compraventa(self, formulario: FormularioObject):

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
        # run_ruts = {
        #     multipropietario.run_rut for multipropietario in tabla_multipropietario}

        # Create a list of run_ruts for all enajenantes
        enajenante_run_ruts = [
            enajenante.run_rut for enajenante in formulario.enajenantes]

        multi_sin_enajenantes, multi_solo_enajenantes = CompraVenta.separate_multipropietario_enajenantes_from_multipropietario_list(
            tabla_multipropietario, enajenante_run_ruts)

        # if enajenante_fantasma():
        sum_porc_adquirientes = CompraVenta.sum_porc_derecho(formulario.adquirentes)

        if future_multipropietarios:
            reprocess_multipropietario_entries_with_new_formulario(db, self, formulario, tabla_multipropietario)

        else:
            if sum_porc_adquirientes == 100:
                CompraVenta.escenario_1(formulario, db, tabla_multipropietario, multi_solo_enajenantes, multi_sin_enajenantes)

            elif sum_porc_adquirientes == 0:
                CompraVenta.escenario_2(formulario, db, multi_solo_enajenantes, multi_sin_enajenantes)

            elif len(formulario.enajenantes) == 1 and len(formulario.adquirentes) == 1 and 0 < sum_porc_adquirientes < 100:
                CompraVenta.escenario_3(formulario, db, tabla_multipropietario, multi_solo_enajenantes, multi_sin_enajenantes)

            else:
                CompraVenta.escenario_4(formulario, db, tabla_multipropietario, multi_sin_enajenantes)

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
                                              current_predio, current_fojas, current_fecha_inscripcion,
                                              current_num_inscripcion, parsed_enajenantes, parsed_adquirentes)
            objects.append(current_object)

        return objects

    def convert_formulario_into_object(self, formulario: Formulario) -> FormularioObject:
        enajenantes = Enajenante.query.filter_by(form_id=formulario.n_atencion).all()
        adquirentes = Adquirente.query.filter_by(form_id=formulario.n_atencion).all()

        return FormularioObject(formulario.cne, formulario.comuna, formulario.manzana, formulario.predio,
                                formulario.fojas, formulario.fecha_inscripcion, formulario.num_inscripcion,
                                enajenantes, adquirentes)

    def search_multipropietario(request):
        comuna = request.form.get('comuna')
        manzana = request.form.get('manzana')
        predio = request.form.get('predio')
        ano_vigencia = request.form.get('ano_vigencia')
        search_results = Multipropietario.query.filter(
            and_(
                Multipropietario.comuna == comuna,
                Multipropietario.manzana == manzana,
                Multipropietario.predio == predio,
                Multipropietario.ano_vigencia_inicial <= ano_vigencia,
                or_(
                    Multipropietario.ano_vigencia_final >= ano_vigencia,
                    Multipropietario.ano_vigencia_final.is_(None)
                )
            )
        ).all()

        return search_results
