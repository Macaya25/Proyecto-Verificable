from app.app import db


class Form(db.model):
    num_formulario = db.Column(db.Integer)
    cne = db.Column(db.Integer)
    comuna = db.Column()
    manzana = db.Column()
    predio = db.Column()
    fojas = db.Column()
    fecha_inscripcion = db.Column(db.DateTime)
    num_inscripcion = db.Column()

    