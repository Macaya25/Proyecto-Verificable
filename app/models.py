from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from datetime import date

db = SQLAlchemy()


class Formulario(db.Model):
    def __repr__(self) -> str:
        return f"ID: {self.n_atencion}\tCNE: {self.cne}\tFojas: {self.fojas}"

    __tablename__ = 'formulario'
    n_atencion = db.Column(db.Integer, primary_key=True,
                           autoincrement=True, index=True)
    cne = db.Column(db.Integer)
    comuna = db.Column(db.Integer, index=True)
    manzana = db.Column(db.String(50), index=True)
    predio = db.Column(db.String(50), index=True)
    fojas = db.Column(db.Integer)
    fecha_inscripcion = db.Column(db.Date)
    num_inscripcion = db.Column(db.Integer, index=True)
    enajenantes = relationship('Enajenante', backref='formulario', lazy=True)
    adquirentes = relationship('Adquirente', backref='formulario', lazy=True)


class Persona(db.Model):
    __tablename__ = 'persona'
    run_rut = db.Column(db.String(50), primary_key=True, index=True)
    enajenaciones = relationship('Enajenante', backref='persona', lazy=True)
    adquisiciones = relationship('Adquirente', backref='persona', lazy=True)


class Enajenante(db.Model):
    __tablename__ = 'enajenante'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    porc_derecho = db.Column(db.Integer)
    form_id = db.Column(db.Integer, db.ForeignKey(
        'formulario.n_atencion'), nullable=False)
    run_rut = db.Column(db.String(50), db.ForeignKey(
        'persona.run_rut'), nullable=False)


class Adquirente(db.Model):
    __tablename__ = 'adquirente'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    porc_derecho = db.Column(db.Integer)
    form_id = db.Column(db.Integer, db.ForeignKey(
        'formulario.n_atencion'), nullable=False)
    run_rut = db.Column(db.String(50), db.ForeignKey(
        'persona.run_rut'), nullable=False)


class Multipropietario(db.Model):
    __tablename__ = 'multipropietario'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    comuna: str = db.Column(db.String(50), index=True)
    manzana: str = db.Column(db.String(50), index=True)
    predio: str = db.Column(db.String(50), index=True)
    run_rut: str = db.Column(db.String(50), db.ForeignKey(
        'persona.run_rut'))
    porc_derechos: int = db.Column(db.Integer)
    fojas: int = db.Column(db.Integer)
    ano_inscripcion: int = db.Column(db.Integer)
    num_inscripcion: int = db.Column(db.Integer, index=True)
    fecha_inscripcion: date = db.Column(db.Date)
    ano_vigencia_inicial: date = db.Column(db.Integer)
    ano_vigencia_final: int = db.Column(db.Integer)


class CNE(db.Model):
    __tablename__ = 'cne'
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(255), nullable=False, index=True)


class Region(db.Model):
    __tablename__ = 'region'
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(255), nullable=False, index=True)
    numero = db.Column(db.Integer, nullable=False, index=True)
    orden = db.Column(db.Integer, nullable=False, index=True)
    descripcion_corta = db.Column(db.String(255), nullable=False, index=True)


class Comuna(db.Model):
    __tablename__ = 'comuna'
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(255), nullable=False, index=True)
    id_region = db.Column(db.Integer, db.ForeignKey(
        'region.id'), nullable=False, index=True)
