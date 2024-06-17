from app import tools
from app.multipropietario.F2890 import RegularizacionPatrimonio


def test_is_empty_with_empty_list():
    assert tools.is_empty([]) is True


def test_regularizacion_check_escenario_empty_multipropietario():
    tabla_multipropietario = []
    before_current_form = []
    after_current_form = []
    same_year_current_form = []

    scenario = RegularizacionPatrimonio.check_escenario(
        tabla_multipropietario, before_current_form, after_current_form, same_year_current_form)

    assert scenario == tools.CONSTANTS.ESCENARIO1_VALUE
