from datetime import datetime
from typing import List
from models import db, Multipropietario, Formulario, Enajenante, Adquirente
from forms import FormularioForm
from tools import (is_empty, CONSTANTS, generate_multipropietario_entry_from_formulario,
                   generate_form_json_from_multipropietario, process_and_save_json_into_db, FormularioObject)
from sqlalchemy import asc
from sqlalchemy.orm import Query


class MultipropietarioHandler:

    def process_new_form(self, formulario: FormularioObject):
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
        def run_nivel_0():
            query = Multipropietario.query.filter_by(
                comuna=formulario.comuna,
                manzana=formulario.manzana,
                predio=formulario.predio
            ).order_by(asc(Multipropietario.ano_vigencia_inicial))
            tabla_multipropietario: List[Multipropietario] = query.all()

            before_current_form_query = query.filter(
                Multipropietario.ano_vigencia_inicial < formulario.fecha_inscripcion)
            before_current_form = before_current_form_query.all()

            after_current_form_query = query.filter(
                Multipropietario.ano_vigencia_inicial > formulario.fecha_inscripcion)
            after_current_form = after_current_form_query.all()

            current_escenario = check_escenario(
                tabla_multipropietario, before_current_form, after_current_form)

            match current_escenario:
                case 1:
                    print('E1')
                    nivel_0_escenario_1(formulario)
                case 2:
                    print('E2')
                    nivel_0_escenario_2(
                        formulario, before_current_form_query)
                case 3:
                    print('E3')
                    nivel_0_escenario_3(formulario, after_current_form)
                case _:
                    print('Escenario inesperado.')

        def check_escenario(tabla_multipropietario: List[Multipropietario], before_current_form: List[Multipropietario], after_current_form: List[Multipropietario]) -> int:
            if is_empty(tabla_multipropietario):
                return 1

            if not is_empty(before_current_form) and is_empty(after_current_form):
                return 2

            if not is_empty(after_current_form):
                print('After found: ')
                for a in after_current_form:
                    print(a.ano_vigencia_inicial, a.ano_vigencia_final)
                return 3

        def nivel_0_escenario_1(formulario: FormularioObject):
            for adquiriente in formulario.adquirentes:
                rut_adquiriente: str = adquiriente.run_rut
                porc_derecho_adquiriente: int = adquiriente.porc_derecho

                new_multipropietario = generate_multipropietario_entry_from_formulario(
                    formulario, rut_adquiriente, porc_derecho_adquiriente)
                db.session.add(new_multipropietario)

        def nivel_0_escenario_2(formulario: FormularioObject, query: Query[Multipropietario]):
            last_entries = query.filter_by(ano_vigencia_final=None).all()
            for entry in last_entries:
                if entry.ano_vigencia_final is None:
                    entry.ano_vigencia_final = formulario.fecha_inscripcion.year - 1

            nivel_0_escenario_1(formulario)

        def nivel_0_escenario_3(formulario: FormularioObject, entries_after_current_form: List[Multipropietario]):
            for entry in entries_after_current_form:
                db.session.delete(entry)

            nivel_0_escenario_1(formulario)

            json_to_reprocess: dict = generate_form_json_from_multipropietario(
                entries_after_current_form)

            for form in json_to_reprocess['F2890']:
                rol = form['bienRaiz']
                forms_to_delete: List[Formulario] = Formulario.query.filter_by(
                    cne=form['CNE'], fojas=form['fojas'],
                    comuna=rol['comuna'], manzana=rol['manzana'], predio=rol['predio'],
                    fecha_inscripcion=form['fechaInscripcion'], num_inscripcion=form['nroInscripcion']).all()
                for f in forms_to_delete:
                    db.session.delete(f)

            db.session.commit()

            if process_and_save_json_into_db(db, json_to_reprocess):
                converted_forms_list = self.convert_json_into_object_list(
                    json_to_reprocess)
                for form in converted_forms_list:
                    self.process_new_form(form)

        run_nivel_0()

    def nivel_1(self, formulario: FormularioForm):
        pass

    def convert_form_into_object(self, form: FormularioForm):
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
