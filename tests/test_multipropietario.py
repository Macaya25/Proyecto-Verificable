import unittest
from app.models import db
from flask import Flask
from app.models import Multipropietario
from datetime import date


class MultipropietarioTest(unittest.TestCase):
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

    def test_get_query(self):
        with self.app.app_context():  # Ensure execution within the application context
            mock_results = [
                Multipropietario(
                    id=1,
                    comuna='Example Comuna',
                    manzana='Example Manzana',
                    predio='Example Predio',
                    run_rut='Example RUN',
                    porc_derecho=50.0,
                    fojas=100,
                    ano_inscripcion=2022,
                    num_inscripcion=1,
                    fecha_inscripcion=date(2022, 1, 1),
                    ano_vigencia_inicial=2022,
                    ano_vigencia_final=2023
                ),
                Multipropietario(
                    id=2,
                    comuna='Another Comuna',
                    manzana='Another Manzana',
                    predio='Another Predio',
                    run_rut='Another RUN',
                    porc_derecho=0.6,
                    fojas=200,
                    ano_inscripcion=2021,
                    num_inscripcion=2,
                    fecha_inscripcion=date(2021, 1, 1),
                    ano_vigencia_inicial=2021,
                    ano_vigencia_final=2022
                )
            ]

            for result in mock_results:
                db.session.add(result)
            db.session.commit()

            results = db.session.query(Multipropietario).all()

            assert len(results) == 2
