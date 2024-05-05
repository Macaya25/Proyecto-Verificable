from typing import List
from models import db, Multipropietario
from forms import FormularioForm
from tools import is_empty, CONSTANTS, generate_multipropietario_entry_from_formulario, generate_form_json_from_multipropietario
from sqlalchemy import asc
from sqlalchemy.orm import Query


class MultipropietarioHandler:

    def process_new_form(self, formulario: FormularioForm):
        if formulario.cne.data == CONSTANTS.CNE_REGULARIZACION.value:
            print("Nivel 0")
            self.nivel_0(formulario)
        elif formulario.cne.data == CONSTANTS.CNE_COMPRAVENTA.value:
            print("Nivel 1")
            self.nivel_1(formulario)
        else:
            print(f"Nivel inesperado: {formulario.cne.data}")

    def nivel_0(self, formulario: FormularioForm):
        def run_nivel_0():
            query = Multipropietario.query.filter_by(
                comuna=formulario.comuna.data,
                manzana=formulario.manzana.data,
                predio=formulario.predio.data
            ).order_by(asc(Multipropietario.ano_vigencia_inicial))
            tabla_multipropietario: List[Multipropietario] = query.all()

            before_current_form_query = query.filter(
                Multipropietario.ano_vigencia_inicial < formulario.fecha_inscripcion.data)
            before_current_form = before_current_form_query.all()

            after_current_form_query = query.filter(
                Multipropietario.ano_vigencia_inicial >= formulario.fecha_inscripcion.data)
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
                return 3

        def nivel_0_escenario_1(formulario: FormularioForm):
            for adquiriente in formulario.adquirentes.data:
                rut_adquiriente: str = adquiriente['run_rut']
                porc_derecho_adquiriente: int = adquiriente['porc_derecho']

                new_multipropietario = generate_multipropietario_entry_from_formulario(
                    formulario, rut_adquiriente, porc_derecho_adquiriente)
                db.session.add(new_multipropietario)

        def nivel_0_escenario_2(formulario: FormularioForm, query: Query[Multipropietario]):
            last_entries = query.filter_by(ano_vigencia_final=None).all()
            for entry in last_entries:
                entry.ano_vigencia_final = formulario.fecha_inscripcion.data.year - 1

            nivel_0_escenario_1(formulario)

        def nivel_0_escenario_3(formulario: FormularioForm, entries_after_current_form: List[Multipropietario]):
            # for entry in entries_after_current_form:
            #     db.session.delete(entry)

            # nivel_0_escenario_1(formulario)

            forms: dict = generate_form_json_from_multipropietario(
                entries_after_current_form)

        run_nivel_0()

    def nivel_1(self, formulario: FormularioForm):
        pass
