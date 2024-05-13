from flask_wtf import FlaskForm
from wtforms import (StringField, IntegerField, SubmitField, DateField, FieldList, FormField,
                     SelectField, FileField, FloatField)
from wtforms.validators import DataRequired, NumberRange, InputRequired
from models import CNE, Region, Comuna


def coerce_for_select_field(value):
    return int(value) if value is not None and value != '' else None

class SearchForm(FlaskForm):
    region = SelectField('Región', coerce=int, validators=[DataRequired()])
    comuna = SelectField('Comuna', coerce=int, validators=[DataRequired()])
    manzana = StringField('Manzana', validators=[DataRequired()])
    ano_vigencia = IntegerField('Año', validators=[DataRequired()])
    submit = SubmitField('Buscar')

    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        self.region.choices = [('', 'Seleccione Región')] + [(region.id, region.descripcion) for region in Region.query.order_by('descripcion').all()]
        self.region.coerce = lambda value: int(value) if value is not None and value != '' else None
        self.comuna.choices = [('', 'Seleccione Comuna')]
        self.comuna.coerce = lambda value: int(value) if value is not None and value != '' else None
        self.update_comunas()

    def update_comunas(self):
        region_id = self.region.data
        if region_id:
            self.comuna.choices = [(comuna.id, comuna.descripcion) for comuna in Comuna.query.filter_by(region_id=region_id).order_by('descripcion').all()]
        else:
            self.comuna.choices = [('', 'Seleccione Comuna')]

class PersonaForm(FlaskForm):
    run_rut = StringField('RUN/RUT')
    porc_derecho = FloatField('% Derecho', validators=[NumberRange(min=0, max=100)])

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
        self.cne.choices = [('', 'Seleccione CNE')] + [(cne.id, cne.descripcion) for cne in CNE.query.all()]                
        self.region.choices = [('', 'Seleccione Región')] + [(region.id, region.descripcion) for region in Region.query.order_by('descripcion')]
        self.comuna.choices = [('', 'Seleccione Comuna')]

        self.cne.coerce = coerce_for_select_field
        self.region.coerce = coerce_for_select_field
        self.comuna.coerce = coerce_for_select_field

    def validate(self, **kwargs):
        is_valid = super(FormularioForm, self).validate()

        if self.cne.data == 99:
            self.enajenantes.errors.clear()
            for subform in self.enajenantes:
                subform.run_rut.data = None
                subform.porc_derecho.data = None
            is_valid = True  

        return is_valid


class JSONForm(FlaskForm):
    file = FileField('File', validators=[InputRequired()])
    submit = SubmitField('Upload File')
