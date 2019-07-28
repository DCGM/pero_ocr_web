from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


class CreateDocumentForm(FlaskForm):
    document_name = StringField('DocumentName', validators=[DataRequired()])
    submit = SubmitField('Create')
