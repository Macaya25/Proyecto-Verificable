from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship

db = SQLAlchemy()

class Formulario(db.Model):
    __tablename__ = 'formulario'
    n_atencion = db.Column(db.Integer, primary_key=True, autoincrement=True, index=True)
    cne = db.Column(db.Integer, nullable=False)
    comuna = db.Column(db.String(50), nullable=False, index=True)
    manzana = db.Column(db.String(50), nullable=False, index=True)
    predio = db.Column(db.String(50), nullable=False, index=True)
    fojas = db.Column(db.Integer, nullable=False)
    fecha_inscripcion = db.Column(db.Date, nullable=False)
    num_inscripcion = db.Column(db.Integer, nullable=False, index=True)
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
    porc_derecho = db.Column(db.Integer, nullable=False)
    form_id = db.Column(db.Integer, db.ForeignKey('formulario.n_atencion'), nullable=False)
    run_rut = db.Column(db.String(50), db.ForeignKey('persona.run_rut'), nullable=False)

class Adquirente(db.Model):
    __tablename__ = 'adquirente'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    porc_derecho = db.Column(db.Integer, nullable=False)
    form_id = db.Column(db.Integer, db.ForeignKey('formulario.n_atencion'), nullable=False)
    run_rut = db.Column(db.String(50), db.ForeignKey('persona.run_rut'), nullable=False)

class Multipropietario(db.Model):
    __tablename__ = 'multipropietario'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    comuna = db.Column(db.String(50), nullable=False, index=True)
    manzana = db.Column(db.String(50), nullable=False, index=True)
    predio = db.Column(db.String(50), nullable=False, index=True)
    run_rut = db.Column(db.String(50), db.ForeignKey('persona.run_rut'), nullable=False)
    porc_derechos = db.Column(db.Integer, nullable=False)
    fojas = db.Column(db.Integer, nullable=False)
    ano_inscripcion = db.Column(db.Integer, nullable=False)
    num_inscripcion = db.Column(db.Integer, nullable=False, index=True)
    fecha_inscripcion = db.Column(db.Date, nullable=False)
    ano_vigencia_inicial = db.Column(db.Integer, nullable=False)
    ano_vigencia_final = db.Column(db.Integer, nullable=True)
