from typing import List
from enum import Enum
from models import Formulario, Enajenante, Adquirente, Persona, Comuna, Multipropietario
from forms import FormularioForm
from flask_sqlalchemy import SQLAlchemy
from dateutil.parser import parse


class CONSTANTS(Enum):
    CNE_REGULARIZACION = 99
    CNE_COMPRAVENTA = 8


def analyze_json(db: SQLAlchemy, json_form):
    def run():
        if not json_form['F2890']:
            print('Formato no valido.')
            return

        for single_form in json_form['F2890']:
            new_form: Formulario = Formulario()

            parse_json_and_set_form(
                new_form, single_form)

            db.session.add(new_form)

            enajenantes: List[Enajenante] = parse_json_and_get_enajenantes(
                single_form)

            adquirientes: List[Adquirente] = parse_json_and_get_adquirentes(
                single_form)

            for single_enajenante in enajenantes:
                single_enajenante.form_id = new_form.n_atencion
                db.session.add(single_enajenante)

            for single_adquiriente in adquirientes:
                single_adquiriente.form_id = new_form.n_atencion
                db.session.add(single_adquiriente)

            db.session.commit()

    def parse_json_and_set_form(new_form: Formulario, current_form):
        def parse_rol(new_form: Formulario, current_form):
            for k, v in current_form['bienRaiz'].items():
                if k == 'comuna':
                    comuna_exists = db.session.query(
                        db.exists().where(Comuna.id == v)).scalar()
                    if comuna_exists:
                        setattr(new_form, 'comuna', v)
                    else:
                        setattr(new_form, 'comuna', None)
                elif k == 'manzana':
                    setattr(new_form, 'manzana', v)
                elif k == 'predio':
                    setattr(new_form, 'predio', v)

        main_keys = ['cne', 'bienRaiz', 'fojas',
                     'fecha_inscripcion', 'num_inscripcion']

        for key, value in current_form.items():
            if key != 'bienRaiz' and key in main_keys:
                setattr(new_form, key, value)
            elif key == "CNE":
                setattr(new_form, 'cne', value)
            elif key == "fechaInscripcion":
                try:
                    parse(value)
                    setattr(new_form, 'fecha_inscripcion', value)
                except ValueError:
                    setattr(new_form, 'fecha_inscripcion', None)

            elif key == 'nroInscripcion':
                setattr(new_form, 'num_inscripcion', value)

            elif key == 'bienRaiz':
                parse_rol(new_form, current_form)

    def parse_json_and_get_enajenantes(current_form):
        enajenantes: List[Enajenante] = []

        if not current_form.get('enajenantes'):
            return []

        for single_enajenante in current_form['enajenantes']:
            new_enajenante = Enajenante()
            if 'RUNRUT' in single_enajenante.keys():
                new_enajenante.run_rut = single_enajenante['RUNRUT']

                person = Persona.query.filter_by(
                    run_rut=new_enajenante.run_rut).first()
                if person is None:
                    person = Persona(
                        run_rut=new_enajenante.run_rut)
                    db.session.add(person)
                    db.session.commit()

            if 'porcDerecho' in single_enajenante.keys():
                new_enajenante.porc_derecho = single_enajenante['porcDerecho']

            enajenantes.append(new_enajenante)

        return enajenantes

    def parse_json_and_get_adquirentes(current_form):
        if not current_form.get('adquirentes'):
            return []

        adquirentes: List[Enajenante] = []

        for single_adquiriente in current_form['adquirentes']:
            new_adquiriente = Adquirente()
            if 'RUNRUT' in single_adquiriente.keys():
                new_adquiriente.run_rut = single_adquiriente['RUNRUT']

                person = Persona.query.filter_by(
                    run_rut=new_adquiriente.run_rut).first()
                if person is None:
                    person = Persona(
                        run_rut=new_adquiriente.run_rut)
                    db.session.add(person)
                    db.session.commit()

            if 'porcDerecho' in single_adquiriente.keys():
                new_adquiriente.porc_derecho = single_adquiriente['porcDerecho']

            adquirentes.append(new_adquiriente)
        return adquirentes
    run()


def is_empty(lst: list):
    return not bool(lst)


def generate_multipropietario_entry_from_formulario(
        formulario: FormularioForm,
        rut: str, derecho: int) -> Multipropietario:

    ano_vigencia_inicial = formulario.fecha_inscripcion.data.year
    ano_vigencia_final = None

    return Multipropietario(
        comuna=formulario.comuna.data,
        manzana=formulario.manzana.data,
        predio=formulario.predio.data,
        run_rut=rut,
        porc_derechos=derecho,
        fojas=formulario.fojas.data,
        ano_inscripcion=formulario.fecha_inscripcion.data.year,
        num_inscripcion=formulario.num_inscripcion.data,
        fecha_inscripcion=formulario.fecha_inscripcion.data,
        ano_vigencia_inicial=ano_vigencia_inicial,
        ano_vigencia_final=ano_vigencia_final
    )


def generate_form_json_from_multipropietario(entries: List[Multipropietario]):
    def get_previous_forms(entries: List[Multipropietario]):
        forms: List[Formulario] = []
        for entry in entries:
            source_form = Formulario.query.filter_by(
                comuna=entry.comuna, manzana=entry.manzana, predio=entry.predio, fojas=entry.fojas, fecha_inscripcion=entry.fecha_inscripcion).first()
            forms.append(source_form)
        return forms

    previous_forms = get_previous_forms(entries)

    json_forms = []

    for f in previous_forms:
        current = {}
        current['CNE'] = f.cne
        current['bienRaiz'] = {'comuna': f.comuna,
                               'manzana': f.manzana,
                               'predio': f.predio}
        current['fojas'] = f.fojas
        current['fechaInscripcion'] = f.fecha_inscripcion.strftime("%Y-%m-%d")
        current['nroInscripcion'] = f.num_inscripcion

        adquirentes: List[Adquirente] = Adquirente.query.filter_by(
            form_id=f.n_atencion).all()
        adquirentes_list = []

        for a in adquirentes:
            adquirentes_list.append(
                {'RUNRUT': a.run_rut, 'porcDerecho': a.porc_derecho})
        current['adquirentes'] = adquirentes_list

        json_forms.append(current)

    return {'F2890': json_forms}
