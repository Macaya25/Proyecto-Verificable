from datetime import datetime
from typing import List
from models import db, Multipropietario, Formulario, Enajenante, Adquirente
from forms import FormularioForm
from tools import (is_empty, CONSTANTS, generate_multipropietario_entry_from_formulario,update_multipropietario_into_new_multipropietarios,
                   generate_form_json_from_multipropietario, process_and_save_json_into_db, FormularioObject)
from sqlalchemy import asc, and_
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
        query = Multipropietario.query.filter(
            and_(
                Multipropietario.comuna == formulario.comuna,
                Multipropietario.manzana == formulario.manzana,
                Multipropietario.predio == formulario.predio,
                Multipropietario.ano_vigencia_inicial <= formulario.fecha_inscripcion,
                (Multipropietario.ano_vigencia_final >= formulario.fecha_inscripcion) | (Multipropietario.ano_vigencia_final == None)
            )
        )
        tabla_multipropietario: List[Multipropietario] = query.all()
        run_ruts = {multipropietario.run_rut for multipropietario in tabla_multipropietario}
        # Create a list of run_ruts for all enajenantes
        enajenante_run_ruts = [enajenante.run_rut for enajenante in formulario.enajenantes]

        # Create a new list of multipropietarios that are not enajenantes
        multipropietarios_sin_enajenantes = [multipropietario for multipropietario in tabla_multipropietario if multipropietario.run_rut not in enajenante_run_ruts]
        
        def update_multipropietario_ano_final(multipropietario: Multipropietario ):
                if multipropietario.ano_vigencia_inicial.year < formulario.fecha_inscripcion.year:
                    # Set ano_vigencia_final to one year less than formulario.fecha_inscripcion
                    multipropietario.ano_vigencia_final = (formulario.fecha_inscripcion.year -1)
                    return multipropietario
                else:
                    # Set ano_vigencia_final to the same year as formulario.fecha_inscripcion
                    multipropietario.ano_vigencia_final = formulario.fecha_inscripcion     
                    return multipropietario
                
        
        def enajenante_fantasma():
            if tabla_multipropietario is None or len(tabla_multipropietario) == 0:
                return False
            # Check if each enajenante.run_rut exists in run_ruts
            for enajenante in formulario.enajenantes:
                if enajenante.run_rut not in run_ruts:
                    return False
            # If all enajenantes are found, return True
            return True
        def sum_porc_derecho_adquirentes():
            sum_porc_derecho = sum(adquirente.porc_derecho for adquirente in formulario.adquirentes)
            return sum_porc_derecho
        def sum_porc_derecho_enajenantes():
            sum_porc_derecho = sum(enajenante.porc_derecho for enajenante in formulario.enajenantes)
            return sum_porc_derecho
        sum_porc_enajenantes= sum_porc_derecho_enajenantes()
        def caso_1():
            #caso 1 ADQ 100
            for adquirente in formulario.adquirentes:
                porc_derech_nuevo= ((adquirente.porc_derecho * sum_porc_derecho_enajenantes)/100)
                new_multipropietario = generate_multipropietario_entry_from_formulario(formulario,adquirente.run_rut,porc_derech_nuevo)
                db.session.add(new_multipropietario)
            for multipropropietario in tabla_multipropietario:
                updated_multipropietario = update_multipropietario_ano_final(multipropietario)
                db.session.update(updated_multipropietario)
            for multipropropietario in multipropietarios_sin_enajenantes:
                multipropietario = update_multipropietario_into_new_multipropietarios(multipropietario,formulario)
                db.session.add(multipropietario)
        def caso_2():
            #caso 2 ADQ 0 y se reparte en partes iguales
            porc_derech_nuevo= (sum_porc_derecho_enajenantes/len(formulario.adquirentes))
            for adquirente in formulario.adquirentes:
                new_multipropietario = generate_multipropietario_entry_from_formulario(formulario,adquirente.run_rut,porc_derech_nuevo)
                db.session.add(new_multipropietario)
            for multipropropietario in tabla_multipropietario:
                updated_multipropietario = update_multipropietario_ano_final(multipropietario)
                db.session.update(updated_multipropietario)
            for multipropropietario in multipropietarios_sin_enajenantes:
                multipropietario = update_multipropietario_into_new_multipropietarios(multipropietario,formulario)
                db.session.add(multipropietario)

        def caso_3():
            #caso 3 ADQ 1-99 ENA y ADQ == 1 
            porc_derech_nuevo_adq= ((formulario.adquirentes[0].porc_derecho * sum_porc_derecho_enajenantes)/100)
            porc_derech_nuevo_ena= sum_porc_derecho_enajenantes - porc_derech_nuevo_adq
            new_multipropietario = generate_multipropietario_entry_from_formulario(formulario,formulario.adquirentes[0].run_rut,porc_derech_nuevo_adq)
            db.session.add(new_multipropietario)
            for multipropietario in tabla_multipropietario:
                if multipropietario.run_rut == formulario.enajenantes[0].run_rut:
                    multipropietario.porc_derechos = porc_derech_nuevo_ena
                    db.session.update(multipropietario)

        def caso_4():
            #caso 4 else ADQ 1-99 ENA y ADQ !=1
            for multipropietario in tabla_multipropietario:
                for enajenante in formulario.enajenantes:
                    if multipropietario.run_rut == enajenante.run_rut:
                        updated_multipropietario = update_multipropietario_ano_final(multipropietario)
                        db.session.update(updated_multipropietario)
                        multipropietario.porc_derechos -= enajenante.porc_derecho
                        if multipropietario.porc_derechos>0:
                            new_multipropietario= update_multipropietario_into_new_multipropietarios(multipropietario,formulario)
                            db.session.add(new_multipropietario)
            for adquiriente in formulario.adquirentes:
                new_multipropietario = generate_multipropietario_entry_from_formulario(formulario,adquiriente.run_rut,adquiriente.porc_derecho)
                db.session.add(new_multipropietario)
        def run_nivel1():
            if enajenante_fantasma():
                sum_porc_adquirientes = sum_porc_derecho_adquirentes()
                if sum_porc_adquirientes == 100:
                    caso_1()
                elif sum_porc_adquirientes == 0:
                    caso_2()
                elif len(formulario.enajenantes) == 1 and len(formulario.adquirientes) == 1 and 0 < sum_porc_adquirientes < 100:
                    caso_3()
                else:
                    caso_4()
            else:
                print("enajenante fantasma")
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
