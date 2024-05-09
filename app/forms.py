from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, DateField, FieldList, FormField, SelectField, FileField, FloatField
from wtforms.validators import DataRequired, NumberRange, InputRequired
from models import CNE, Region

def coerce_for_select_field(value):
    return int(value) if value is not None and value != '' else None

class PersonaForm(FlaskForm):
    run_rut = StringField('RUN/RUT', validators=[DataRequired()])
    porc_derecho = FloatField('% Derecho', validators=[NumberRange(min=0.0, max=100.0), DataRequired()])

class FormularioForm(FlaskForm):
    cne = SelectField('CNE', coerce=coerce_for_select_field, validators=[DataRequired()])
    region = SelectField('Región', coerce=coerce_for_select_field, validators=[DataRequired()])
    comuna = SelectField('Comuna', coerce=coerce_for_select_field, validators=[DataRequired()])
    manzana = StringField('Manzana', validators=[DataRequired()])
    predio = StringField('Predio', validators=[DataRequired()])
    fojas = IntegerField('Fojas', validators=[DataRequired()])
    fecha_inscripcion = DateField('Fecha Inscripción', format='%Y-%m-%d', validators=[DataRequired()])
    num_inscripcion = IntegerField('Número Inscripción', validators=[DataRequired()])
    adquirentes = FieldList(FormField(PersonaForm), min_entries=1)
    enajenantes = FieldList(FormField(PersonaForm), min_entries=1)
    submit = SubmitField('Registrar')

    def __init__(self, *args, **kwargs):
        super(FormularioForm, self).__init__(*args, **kwargs)
        self.cne.choices = [('', 'Seleccione CNE')] + [(cne.id, cne.descripcion) for cne in CNE.query.all()]
        self.region.choices = [('', 'Seleccione Región')] + [(region.id, region.descripcion) for region in Region.query.order_by('descripcion')]
        self.comuna.choices = [('', 'Seleccione Comuna')]

    def validate(self):
        if not super(FormularioForm, self).validate():
            return False
        if self.cne.data == 99:
            for subform in self.enajenantes:
                subform.run_rut.data = None
                subform.porc_derecho.data = None
            return True
        return True

class JSONForm(FlaskForm):
    file = FileField('Archivo', validators=[InputRequired()])
    submit = SubmitField('Subir Archivo')
