from flask_wtf import FlaskForm
from wtforms import (StringField, IntegerField, SubmitField, DateField, FieldList, FormField,
                     SelectField, FileField)
from wtforms.validators import DataRequired, NumberRange, InputRequired
from wtforms.widgets import HiddenInput
from models import CNE


class PersonaForm(FlaskForm):
    run_rut = StringField('RUN/RUT')
    porc_derecho = IntegerField('% Derecho')

class FormularioForm(FlaskForm):
    cne = SelectField('CNE', coerce=int, validators=[DataRequired()])
    comuna = StringField('Comuna', validators=[DataRequired()])
    manzana = StringField('Manzana', validators=[DataRequired()])
    predio = StringField('Predio', validators=[DataRequired()])
    fojas = IntegerField('Fojas', validators=[DataRequired()])
    fecha_inscripcion = DateField(
        'Fecha Inscripción', format='%Y-%m-%d', validators=[DataRequired()])
    num_inscripcion = IntegerField(
        'Número Inscripción', validators=[DataRequired()])
    adquirentes = FieldList(FormField(PersonaForm), min_entries=1)
    enajenantes = FieldList(FormField(PersonaForm), min_entries=1)
    submit = SubmitField('Registrar')

    def __init__(self, *args, **kwargs):
        super(FormularioForm, self).__init__(*args, **kwargs)
        self.cne.choices = [(cne.id, cne.descripcion) for cne in CNE.query.all()]
        if self.cne.data in [1, 'compraventa']:
            self.enajenantes[0].form.id = 1
        else:
            self.enajenantes[0].form.id = None                          

class JSONForm(FlaskForm):
    file = FileField('File', validators=[InputRequired()])
    submit = SubmitField('Upload File')
