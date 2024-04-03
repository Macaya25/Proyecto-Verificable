from flask_wtf import FlaskForm
from wtforms import (StringField, IntegerField, SubmitField, DateField, FieldList, FormField,
                     SelectField, FileField)
from wtforms.validators import DataRequired, NumberRange, InputRequired
from models import CNE, Region, Comuna

def coerce_for_select_field(value):
    return int(value) if value is not None and value != '' else None

class PersonaForm(FlaskForm):
    run_rut = StringField('RUN/RUT', validators=[DataRequired()])
    porc_derecho = IntegerField('% Derecho', validators=[
                                DataRequired(), NumberRange(min=1, max=100)])


class FormularioForm(FlaskForm):
    cne = SelectField('CNE', coerce=int, validators=[DataRequired()])
    region = SelectField('Región', coerce=int, validators=[DataRequired()])
    comuna = SelectField('Comuna', coerce=int, validators=[DataRequired()])
    manzana = StringField('Manzana', validators=[DataRequired()])
    predio = StringField('Predio', validators=[DataRequired()])
    fojas = IntegerField('Fojas', validators=[DataRequired()])
    fecha_inscripcion = DateField(
        'Fecha Inscripción', format='%Y-%m-%d', validators=[DataRequired()])
    num_inscripcion = IntegerField(
        'Número Inscripción', validators=[DataRequired()])
    enajenantes = FieldList(FormField(PersonaForm), min_entries=1)
    adquirentes = FieldList(FormField(PersonaForm), min_entries=1)
    submit = SubmitField('Registrar')

    def __init__(self, *args, **kwargs):
        super(FormularioForm, self).__init__(*args, **kwargs)
        self.cne.choices = [('', 'Seleccione CNE')] + [(cne.id, cne.descripcion)
                            for cne in CNE.query.all()]
        self.region.choices = [('', 'Seleccione Región')] + [(region.id, region.descripcion) for region in Region.query.order_by('descripcion')]
        self.comuna.choices = [('', 'Seleccione Comuna')]

        self.cne.coerce = coerce_for_select_field
        self.region.coerce = coerce_for_select_field
        self.comuna.coerce = coerce_for_select_field

class JSONForm(FlaskForm):
    file = FileField('File', validators=[InputRequired()])
    submit = SubmitField('Upload File')
