from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, SubmitField
from wtforms.validators import Optional

class LogFilterForm(FlaskForm):
    ip_address = StringField('IP Address', validators=[Optional()])
    status_code = SelectField('Status Code', choices=[
        ('', 'All'),
        ('200', '200 OK'),
        ('404', '404 Not Found'),
        ('500', '500 Internal Server Error'),
        ('403', '403 Forbidden')
    ], validators=[Optional()])

    method = SelectField("HTTP Method", choices=[
        ("", "All"),
        ("GET", "GET"),
        ("POST", "POST"),
    ], validators=[Optional()])

    start_time = DateField('Start Time', format='%Y-%m-%d', validators=[Optional()])
    end_time = DateField('End Time', format = '%Y-%m-%d', validators=[Optional()])
    submit = SubmitField("Apply Filters")

class ExportReportForm(FlaskForm):
    format = SelectField("Export Format", choices=[
        ("csv", "CSV"),
        ("pdf", "PDF")
    ])

    submit = SubmitField("Download Report")