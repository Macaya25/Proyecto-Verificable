from datetime import datetime
from typing import List
from sqlalchemy import asc, and_, or_
from multipropietario.multipropietario_tools import (
    FormularioObject, reprocess_multipropietario_entries_with_new_formulario, merge_multipropietarios, ajustar_porcentajes,
    remove_from_multipropietario, reprocess_multipropietario_entries, limit_date_of_last_entries_from_multipropietario)
from multipropietario.F2890 import RegularizacionPatrimonio, CompraVenta

from models import Multipropietario, Enajenante, Adquirente, Formulario
from forms import FormularioForm
from tools import CONSTANTS


class MultipropietarioHandler:
    def process_new_formulario_object(self, db, formulario: FormularioObject):
        print('New formulario: ', formulario.num_inscripcion, formulario.fecha_inscripcion)

        if formulario.cne == CONSTANTS.CNE_REGULARIZACION:
            self.process_regularizacion_patrimonio(db, formulario)

        elif formulario.cne == CONSTANTS.CNE_COMPRAVENTA:
            self.process_compraventa(db, formulario)

        else:
            print(f"Nivel inesperado: {formulario.cne}")

        merge_multipropietarios(db, formulario)
        ajustar_porcentajes(db, formulario)

    def process_regularizacion_patrimonio(self, db, formulario: FormularioObject):

        tabla_multipropietario = self.generate_regularizacion_multipropietarios(db, formulario)
        before_current_form = self.generate_regularizacion_before_current_formulario(db, formulario)
        same_year_current_form = self.generate_regularizacion_same_current_formulario(db, formulario)
        after_current_form = self.generate_regularizacion_after_current_formulario(db, formulario)

        current_escenario = RegularizacionPatrimonio.check_escenario(tabla_multipropietario,
                                                                     before_current_form, after_current_form,
                                                                     same_year_current_form)

        match current_escenario:
            case CONSTANTS.ESCENARIO1_VALUE:
                print('E1')
                RegularizacionPatrimonio.add_form_to_multipropietario(db, formulario)

            case CONSTANTS.ESCENARIO2_VALUE:
                print('E2')
                limit_date_of_last_entries_from_multipropietario(formulario, before_current_form)
                RegularizacionPatrimonio.add_form_to_multipropietario(db, formulario)

            case CONSTANTS.ESCENARIO3_VALUE:
                print('E3')
                remove_from_multipropietario(db, after_current_form)
                reprocess_multipropietario_entries_with_new_formulario(db, self, formulario, after_current_form)

            case CONSTANTS.ESCENARIO4_VALUE:
                print('E4')

                current_date = formulario.fecha_inscripcion
                previous_date = same_year_current_form[-1].fecha_inscripcion

                if current_date > previous_date:
                    remove_from_multipropietario(db, same_year_current_form)
                    RegularizacionPatrimonio.add_form_to_multipropietario(db, formulario)

                elif current_date < previous_date:
                    reprocess_multipropietario_entries_with_new_formulario(db, self, formulario, same_year_current_form)

                elif current_date == previous_date:
                    if formulario.num_inscripcion > same_year_current_form[0].num_inscripcion:
                        remove_from_multipropietario(db, same_year_current_form)
                        RegularizacionPatrimonio.add_form_to_multipropietario(db, formulario)

                    elif formulario.num_inscripcion < same_year_current_form[0].num_inscripcion:
                        reprocess_multipropietario_entries_with_new_formulario(db, self, formulario, same_year_current_form)

                remove_from_multipropietario(db, after_current_form)
                reprocess_multipropietario_entries(db, self, after_current_form)

            case _:
                print('Escenario inesperado.')

    def process_compraventa(self, db, formulario: FormularioObject):

        tabla_multipropietario, future_multipropietarios = self.generate_compraventa_multipropietarios_tables(db, formulario)

        # Create a list of run_ruts for all enajenantes
        enajenante_run_ruts = [enajenante.run_rut for enajenante in formulario.enajenantes]

        multi_sin_enajenantes, multi_solo_enajenantes = CompraVenta.separate_multipropietario_enajenantes_from_multipropietario_list(
            tabla_multipropietario, enajenante_run_ruts)

        sum_porc_adquirientes = CompraVenta.sum_porc_derecho(formulario.adquirentes)

        if future_multipropietarios:
            forms_to_reprocess = tabla_multipropietario + future_multipropietarios
            reprocess_multipropietario_entries_with_new_formulario(db, self, formulario, forms_to_reprocess)

        else:
            current_escenario = CompraVenta.check_escenario(formulario, sum_porc_adquirientes)

            match current_escenario:
                case CONSTANTS.ESCENARIO1_VALUE:
                    print('Compraventa E1')
                    CompraVenta.sum_adquirientes_100(formulario, db, tabla_multipropietario, multi_solo_enajenantes, multi_sin_enajenantes)

                case CONSTANTS.ESCENARIO2_VALUE:
                    print('Compraventa E2')
                    CompraVenta.sum_adquirientes_0(formulario, db, multi_solo_enajenantes, multi_sin_enajenantes)

                case CONSTANTS.ESCENARIO3_VALUE:
                    print('Compraventa E3')
                    CompraVenta.enajenante_1_adquiriente_1(formulario, db, tabla_multipropietario,
                                                           multi_solo_enajenantes, multi_sin_enajenantes)
                case CONSTANTS.ESCENARIO4_VALUE:
                    print('Compraventa E4')
                    CompraVenta.multiples_adquirientes_and_enajenantes_1_99(formulario, db, tabla_multipropietario,
                                                                            multi_solo_enajenantes, multi_sin_enajenantes)

    def generate_regularizacion_multipropietarios(self, db, formulario):

        query = self.generate_regularizacion_query(db, formulario)

        tabla_multipropietario: List[Multipropietario] = query.all()

        return tabla_multipropietario

    @staticmethod
    def generate_regularizacion_query(db, formulario):
        query = db.session.query(Multipropietario).filter_by(comuna=formulario.comuna,
                                                             manzana=formulario.manzana,
                                                             predio=formulario.predio
                                                             ).order_by(asc(Multipropietario.ano_vigencia_inicial))

        return query

    def generate_regularizacion_before_current_formulario(self, db, formulario):
        query = self.generate_regularizacion_query(db, formulario)

        before_current_form_query = query.filter(
            Multipropietario.ano_vigencia_inicial < formulario.fecha_inscripcion)
        before_current_form = before_current_form_query.all()

        return before_current_form

    def generate_regularizacion_same_current_formulario(self, db, formulario):
        query = self.generate_regularizacion_query(db, formulario)

        same_year_current_form_query = query.filter(
            Multipropietario.ano_vigencia_inicial == formulario.fecha_inscripcion)
        same_year_current_form = same_year_current_form_query.all()

        return same_year_current_form

    def generate_regularizacion_after_current_formulario(self, db, formulario):
        query = self.generate_regularizacion_query(db, formulario)

        after_current_form_query = query.filter(
            Multipropietario.ano_vigencia_inicial > formulario.fecha_inscripcion)
        after_current_form = after_current_form_query.all()

        return after_current_form

    @staticmethod
    def generate_compraventa_multipropietarios_tables(db, formulario):
        query = db.session.query(Multipropietario).filter(
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

        future_query = db.session.query(Multipropietario).filter(
            and_(
                Multipropietario.comuna == formulario.comuna,
                Multipropietario.manzana == formulario.manzana,
                Multipropietario.predio == formulario.predio,
                Multipropietario.fecha_inscripcion > formulario.fecha_inscripcion
            )
        )

        tabla_multipropietario: List[Multipropietario] = query.all()
        future_multipropietarios: List[Multipropietario] = future_query.all()

        return tabla_multipropietario, future_multipropietarios

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

    def convert_formulario_into_object(self, db, formulario: Formulario) -> FormularioObject:
        enajenantes = db.session.query(Enajenante).filter_by(form_id=formulario.n_atencion).all()
        adquirentes = db.session.query(Adquirente).filter_by(form_id=formulario.n_atencion).all()

        return FormularioObject(formulario.cne, formulario.comuna, formulario.manzana, formulario.predio,
                                formulario.fojas, formulario.fecha_inscripcion, formulario.num_inscripcion,
                                enajenantes, adquirentes)

    def search_multipropietario(self, db, request):
        comuna = request.form.get('comuna')
        manzana = request.form.get('manzana')
        predio = request.form.get('predio')
        ano_vigencia = request.form.get('ano_vigencia')
        search_results = db.session.query(Multipropietario).filter(
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
