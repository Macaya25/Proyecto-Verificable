from typing import List, Set
from datetime import date
from models import Multipropietario, Adquirente, Enajenante, Formulario
from tools import is_empty


class FormularioObject:
    def __init__(self, cne: int, comuna: int, manzana: str, predio: str,
                 fojas: int, fecha_inscripcion: date, num_inscripcion: int,
                 enajenantes: List[Enajenante], adquirentes: List[Adquirente]):
        self.cne = cne
        self.comuna = comuna
        self.manzana = manzana
        self.predio = predio
        self.fojas = fojas
        self.fecha_inscripcion = fecha_inscripcion
        self.num_inscripcion = num_inscripcion
        self.enajenantes = enajenantes
        self.adquirentes = adquirentes


def check_escenario(tabla_multipropietario: List[Multipropietario],
                    before_current_form: List[Multipropietario],
                    after_current_form: List[Multipropietario],
                    same_year_current_form: List[Multipropietario]) -> int:
    if is_empty(tabla_multipropietario):
        return 1

    if not is_empty(same_year_current_form):
        return 4

    if not is_empty(before_current_form) and is_empty(after_current_form):
        return 2

    if not is_empty(after_current_form):
        return 3

    else:
        return 0


def remove_from_multipropietario(db, entries_after_current_form: List[Multipropietario]):
    for entry in entries_after_current_form:
        db.session.delete(entry)


def generate_multipropietario_entry_from_formulario(
        formulario: FormularioObject,
        rut: str, derecho: int) -> Multipropietario:

    ano_vigencia_inicial = formulario.fecha_inscripcion.year
    ano_vigencia_final = None

    return Multipropietario(
        comuna=formulario.comuna,
        manzana=formulario.manzana,
        predio=formulario.predio,
        run_rut=rut,
        porc_derecho=derecho,
        fojas=formulario.fojas,
        ano_inscripcion=formulario.fecha_inscripcion.year,
        num_inscripcion=formulario.num_inscripcion,
        fecha_inscripcion=formulario.fecha_inscripcion,
        ano_vigencia_inicial=ano_vigencia_inicial,
        ano_vigencia_final=ano_vigencia_final
    )


def generate_formularios_json_from_multipropietario(entries: List[Multipropietario]):
    previous_forms = get_formularios_from_multipropietarios(entries)
    print('Previous: ', previous_forms)
    json_forms = []

    for f in previous_forms:
        print('F: ', f)
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


def get_formularios_from_multipropietarios(entries: List[Multipropietario]) -> List[Formulario]:
    forms: Set[Formulario] = set()
    for entry in entries:
        source_form = Formulario.query.filter_by(
            comuna=entry.comuna, manzana=entry.manzana, predio=entry.predio,
            fojas=entry.fojas, fecha_inscripcion=entry.fecha_inscripcion).first()
        if source_form:
            forms.add(source_form)
    sorted_forms = sorted(list(forms), key=lambda x: x.fecha_inscripcion)
    return sorted_forms
