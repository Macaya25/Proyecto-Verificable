import unittest
from flask import Flask
from app.models import db, Multipropietario, Formulario
from app.json_processing import (process_and_save_json_into_db, parse_json_and_save_form_in_db,
                                 parse_json_and_save_enajenantes_in_db, parse_json_and_save_adquirientes_in_db)
from app.multipropietario.multipropietario_handler import MultipropietarioHandler
import json
from datetime import date


class JsonProcessing(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Base de datos en memoria para pruebas
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        if not hasattr(self.app, 'extensions') or 'sqlalchemy' not in self.app.extensions:
            db.init_app(self.app)
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_json_parse_single_form_and_save_in_db(self):
        with self.app.app_context():
            with open('tests/control2.json', 'r') as file:
                control2_json = json.load(file)
                single_form = control2_json.get('F2890')[0]
                new_form = Formulario()
                parse_json_and_save_form_in_db(db, new_form, single_form)

                parse_json_and_save_enajenantes_in_db(db, single_form, new_form.n_atencion)
                parse_json_and_save_adquirientes_in_db(db, single_form, new_form.n_atencion)

            result_form: Formulario = db.session.query(Formulario).first()
            print(result_form)

            assert result_form.manzana == '64'
            assert result_form.predio == '32'
            assert result_form.fojas == 2
            assert result_form.fecha_inscripcion == date(2021, 6, 6)

    def test_json_processing_control2(self):
        multiprop_handler = MultipropietarioHandler()

        with self.app.app_context():
            with open('tests/control2.json', 'r') as file:
                control2_json = json.load(file)
                is_valid_json = process_and_save_json_into_db(db, control2_json)

            if is_valid_json:
                converted_forms_list = multiprop_handler.convert_json_into_object_list(control2_json)
                for form in converted_forms_list:
                    multiprop_handler.process_new_formulario_object(db, form)
                db.session.commit()

            results = db.session.query(Multipropietario).all()

            with open("tests/control2_results.json", 'r') as file:
                expected_results = json.load(file)

                for result, expected in zip(results, expected_results):
                    assert result.comuna == expected["comuna"]
                    assert result.manzana == expected["manzana"]
                    assert result.predio == expected["predio"]
                    assert result.run_rut == expected["run_rut"]
                    assert result.porc_derecho == expected["porc_derecho"]
                    assert result.fojas == expected["fojas"]
                    assert result.ano_inscripcion == expected["ano_inscripcion"]
                    assert result.num_inscripcion == expected["num_inscripcion"]
                    assert result.fecha_inscripcion.strftime('%Y-%m-%d') == expected["fecha_inscripcion"]
                    assert result.ano_vigencia_inicial == expected["ano_vigencia_inicial"]
                    assert result.ano_vigencia_final == expected["ano_vigencia_final"]

                assert len(results) == len(expected_results)
