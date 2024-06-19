import unittest
from pytest import approx
from flask import Flask
from sqlalchemy import inspect
import pandas as pd

from app.models import db, Multipropietario, Formulario, CNE, Comuna, Region
from app.json_processing import (process_and_save_json_into_db, parse_json_and_save_form_in_db,
                                 parse_json_and_save_enajenantes_in_db, parse_json_and_save_adquirientes_in_db)
from app.multipropietario.multipropietario_handler import MultipropietarioHandler
from app.multipropietario.multipropietario_tools import ajustar_porcentajes
import json
from datetime import date


class JsonProcessing(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Base de datos en memoria para pruebas
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
        if not hasattr(self.app, 'extensions') or 'sqlalchemy' not in self.app.extensions:
            db.init_app(self.app)
        with self.app.app_context():
            db.create_all()
            self.seed_data()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def seed_data(self):
        # Seed data within the app context
        df_regiones = pd.read_excel('app/regionesComunas.xlsx', sheet_name='regiones')
        df_comunas = pd.read_excel('app/regionesComunas.xlsx', sheet_name='comunas')
        df_cne_elements = pd.DataFrame({
            'id': [99, 8],
            'descripcion': ['Regularizacion de Patrimonio', 'Compraventa']
        })

        df_regiones.rename(columns={'id_region': 'id'}, inplace=True)
        df_comunas.rename(columns={'id_comuna': 'id'}, inplace=True)

        with self.app.app_context():
            for _, row in df_regiones.iterrows():
                region = Region(id=row['id'], descripcion=row['descripcion'], numero=row['numero'],
                                orden=row['orden'], descripcion_corta=row['descripcion_corta'])
                db.session.add(region)

            for _, row in df_comunas.iterrows():
                comuna = Comuna(id=row['id'], descripcion=row['descripcion'], id_region=row['id_region'])
                db.session.add(comuna)

            for _, row in df_cne_elements.iterrows():
                cne = CNE(id=row['id'], descripcion=row['descripcion'])
                db.session.add(cne)

            db.session.commit()

            # Verify data insertion
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Tables in the database: {tables}")

            region_count = db.session.query(Region).count()
            comuna_count = db.session.query(Comuna).count()
            cne_count = db.session.query(CNE).count()

            print(f"Number of rows in 'region': {region_count}")
            print(f"Number of rows in 'comuna': {comuna_count}")
            print(f"Number of rows in 'cne': {cne_count}")

        print("Tables and relationships successfully created in the SQLite database.")

    def test_seed_data_insertion(self):
        with self.app.app_context():
            regiones = db.session.query(Region).all()
            comunas = db.session.query(Comuna).all()
            cne_elements = db.session.query(CNE).all()

            print(f"Number of regions: {len(regiones)}")
            print(f"Number of comunas: {len(comunas)}")
            print(f"Number of cne elements: {len(cne_elements)}")

            assert len(regiones) > 0
            assert len(comunas) > 0
            assert len(cne_elements) > 0

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

    def test_json_processing_control4(self):
        multiprop_handler = MultipropietarioHandler()

        with self.app.app_context():
            with open('tests/control4.json', 'r') as file:
                control2_json = json.load(file)
                is_valid_json = process_and_save_json_into_db(db, control2_json)

            if is_valid_json:
                converted_forms_list = multiprop_handler.convert_json_into_object_list(control2_json)
                for form in converted_forms_list:
                    multiprop_handler.process_new_formulario_object(db, form)
                db.session.commit()

            results = db.session.query(Multipropietario).all()
            for r in results:
                print('Entry: ', r, r.ano_vigencia_inicial, r.ano_vigencia_final)

            with open("tests/control4_results.json", 'r') as file:
                expected_results = json.load(file)

                for result, expected in zip(results, expected_results):
                    assert result.comuna == expected["comuna"]
                    assert result.manzana == expected["manzana"]
                    assert result.predio == expected["predio"]
                    assert result.run_rut == expected["run_rut"]
                    assert result.porc_derecho == approx(expected["porc_derecho"], rel=1e-2)
                    assert result.fojas == expected["fojas"]
                    assert result.ano_inscripcion == expected["ano_inscripcion"]
                    assert result.num_inscripcion == expected["num_inscripcion"]
                    if result.fecha_inscripcion:
                        assert result.fecha_inscripcion.strftime('%Y-%m-%d') == expected["fecha_inscripcion"]
                    else:
                        assert expected["fecha_inscripcion"] is None
                    assert result.ano_vigencia_inicial == expected["ano_vigencia_inicial"]
                    assert result.ano_vigencia_final == expected["ano_vigencia_final"]

                assert len(results) == len(expected_results)

    def test_json_processing_control5(self):
        multiprop_handler = MultipropietarioHandler()

        with self.app.app_context():
            with open('tests/control5.json', 'r') as file:
                control2_json = json.load(file)
                is_valid_json = process_and_save_json_into_db(db, control2_json)

            if is_valid_json:
                converted_forms_list = multiprop_handler.convert_json_into_object_list(control2_json)
                for form in converted_forms_list:
                    multiprop_handler.process_new_formulario_object(db, form)
                    ajustar_porcentajes(db, form)
                db.session.commit()

            results = db.session.query(Multipropietario).all()

            print('Results: ', results)

            with open("tests/control5_results.json", 'r') as file:
                expected_results = json.load(file)

                for result, expected in zip(results, expected_results):
                    assert result.comuna == expected["comuna"]
                    assert result.manzana == expected["manzana"]
                    assert result.predio == expected["predio"]
                    assert result.run_rut == expected["run_rut"]
                    assert result.porc_derecho == approx(expected["porc_derecho"], relx=1e-2)
                    assert result.fojas == expected["fojas"]
                    assert result.ano_inscripcion == expected["ano_inscripcion"]
                    assert result.num_inscripcion == expected["num_inscripcion"]
                    if result.fecha_inscripcion:
                        assert result.fecha_inscripcion.strftime('%Y-%m-%d') == expected["fecha_inscripcion"]
                    else:
                        assert expected["fecha_inscripcion"] is None
                    assert result.ano_vigencia_inicial == expected["ano_vigencia_inicial"]
                    assert result.ano_vigencia_final == expected["ano_vigencia_final"]

                assert len(results) == len(expected_results)
