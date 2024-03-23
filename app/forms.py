from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, DateField, FieldList, FormField, SelectField, FileField
from wtforms.validators import DataRequired, NumberRange, InputRequired, ValidationError
from models import CNE
import json

class PersonaForm(FlaskForm):
    run_rut = StringField('RUN/RUT', validators=[DataRequired()])
    porc_derecho = IntegerField('% Derecho', validators=[DataRequired(), NumberRange(min=1, max=100)])

class FormularioForm(FlaskForm):
    cne = SelectField('CNE', coerce=int, validators=[DataRequired()])
    comuna = StringField('Comuna', validators=[DataRequired()])
    manzana = StringField('Manzana', validators=[DataRequired()])
    predio = StringField('Predio', validators=[DataRequired()])
    fojas = IntegerField('Fojas', validators=[DataRequired()])
    fecha_inscripcion = DateField('Fecha Inscripción', format='%Y-%m-%d', validators=[DataRequired()])
    num_inscripcion = IntegerField('Número Inscripción', validators=[DataRequired()])
    enajenantes = FieldList(FormField(PersonaForm), min_entries=1)
    adquirentes = FieldList(FormField(PersonaForm), min_entries=1)
    submit = SubmitField('Registrar')

    def __init__(self, *args, **kwargs):
        super(FormularioForm, self).__init__(*args, **kwargs)
        self.cne.choices = [(cne.id, cne.descripcion) for cne in CNE.query.all()]

class JSONForm(FlaskForm):
    def validate_json_file(self, field):
        if not field.data:
            raise ValidationError('File is required.')
        
        try:
            json.loads(field.data.read().decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise ValidationError('Invalid JSON file.')
        
    file = FileField('File', validators=[InputRequired()])
    submit = SubmitField('Upload File')

