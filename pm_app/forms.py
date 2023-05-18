
from flask_wtf import FlaskForm
from wtforms_sqlalchemy.fields import QuerySelectField
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms.fields.html5 import DateField

from wtforms import (
    StringField, PasswordField, SubmitField, BooleanField, 
    TextAreaField, DecimalField,SelectField 
    )

from wtforms.validators import (
    DataRequired, Length, Email, EqualTo, ValidationError, Optional)

from pm_app.models import (
    User, Project, Unit, Task
    )

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    supplier = SelectField('Is the user an external supplier?')
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

class ModifyRegistrationForm(FlaskForm):
    username = StringField('Username*', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email*', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[])
    confirm_password = PasswordField('Confirm Password', validators=[EqualTo('password')])
    # supplier = SelectField('Is the user an external supplier?*', validators=[DataRequired()])
    submit = SubmitField('Change now!')

class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class UpdateAccountForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), 
                           Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    picture = FileField('Update Profile Picture', 
                         validators=[FileAllowed(['jpg', 'png','jpeg'])])
    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is taken. Please choose a different one.')

class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Post')

class RequestResetForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('There is no account with that email. You must register first.')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), 
                                     EqualTo('password')])
    submit = SubmitField('Reset Password')

class CreateProject(FlaskForm):
    hov = StringField('Unique project designation',validators=[DataRequired()])
    customer_name = StringField('Name of airline',validators=[DataRequired()])

    budget = DecimalField('Budget [CHF]', validators=[DataRequired()])
    rate = DecimalField('Hourly rate [CHF/h]', validators=[Optional()]) 
    hour_budget = DecimalField('Additional internal hourly budget [h] - if required', validators=[Optional()]) 
    
    submit = SubmitField('Create new project now!')

    def validate_hov(self, hov):
        project = Project.query.filter_by(hov=hov.data).first()
        if project:
            raise ValidationError('That HoV is already taken. Please choose a different one.')

class ModifyProject(FlaskForm):
    hov = StringField('Unique project designation',validators=[DataRequired()])
    customer_name = StringField('Name of airline',validators=[DataRequired()])

    budget = DecimalField('Budget [CHF]', validators=[DataRequired()])
    rate = DecimalField('Hourly rate [CHF/h]', validators=[Optional()]) 
    hour_budget = DecimalField('Additional internal hourly budget [h] - if required', validators=[Optional()]) 
    
    submit = SubmitField('Modify project now!')

class FindUnit(FlaskForm):
    units = SelectField('Units: ', validators=[DataRequired()])
    submit = SubmitField('Modify unit now!')

class CreateUnit(FlaskForm):
    pn = StringField("Unit's P/N",validators=[DataRequired()])
    pn_name = StringField("Unit's name (e.g. G1F)",validators=[DataRequired()])
    hov = SelectField('HoVs: ', validators=[DataRequired()])
    submit = SubmitField('Create new unit now!')

    def validate_pn(self, pn):
        unit = Unit.query.filter_by(pn=pn.data).first()
        if unit:
            raise ValidationError('That P/N is already taken. Please choose a different one.')

class ChangeUnit(FlaskForm):
    pn = StringField("Unit's P/N",validators=[DataRequired()])
    pn_name = StringField("Unit's name (e.g. G1F)",validators=[DataRequired()])
    hov = SelectField('HoVs: ', validators=[DataRequired()])
    submit = SubmitField('Create new unit now!')


class CreateTask(FlaskForm):
    task_name = StringField('Task name',validators=[DataRequired()])
    task_description = TextAreaField('Task description',validators=[Optional()])
    submit = SubmitField('Create new task now!')

    def validate_task(self):
        task = Task.query.filter_by(task_name=self.task_name.data).first()
        if task:
            raise ValidationError('That task is already taken. Please choose a different one.')

class GetHov(FlaskForm):
    hov = SelectField('HoVs: ', validators=[DataRequired()])
    submit = SubmitField('Next')

class GetUnit(FlaskForm):
    unit = SelectField('Unit: ', validators=[DataRequired()])
    submit = SubmitField('Next')

class GetTime(FlaskForm):
    date_of_work = DateField('Date of work:', format='%Y-%m-%d', validators=[DataRequired()])
    task = SelectField('Task: ', validators=[DataRequired()])
    time_amount = SelectField('Worked time [h]: ', validators=[DataRequired()])
    submit = SubmitField('Create new time entry now!')

# Create a from to choose a time entry and decide if this entry is to be deleted
class ChangeTimeEntry(FlaskForm):
    entries = SelectField('Select a time entry: ', validators=[DataRequired()])
    submit = SubmitField('Delete and update time entry now!')

class AddSupervisor(FlaskForm):
    supervisor = SelectField('Add user to supervisor', validators=[DataRequired()])
    submit = SubmitField('Add now!')

class AddAdmin(FlaskForm):
    admin = SelectField('Add user to admin', validators=[DataRequired()])
    submit = SubmitField('Add now!')

class RemoveUser(FlaskForm):
    user = SelectField('User to be removed', validators=[DataRequired()])
    submit = SubmitField('Remove now!')

class RemoveAdmin(FlaskForm):
    user = SelectField('Admin to be removed', validators=[DataRequired()])
    submit = SubmitField('Remove now!')

class RemoveSupervisor(FlaskForm):
    user = SelectField('Supervisor to be removed', validators=[DataRequired()])
    submit = SubmitField('Remove now!')

class RemoveProject(FlaskForm):
    project = SelectField('Project to be removed', validators=[DataRequired()])
    submit = SubmitField('Remove now!')

class RemoveUnit(FlaskForm):
    unit = SelectField('Unit to be removed', validators=[DataRequired()])
    submit = SubmitField('Remove now!')

class RemoveTask(FlaskForm):
    task = SelectField('Task to be removed', validators=[DataRequired()])
    submit = SubmitField('Remove now!')

class RemoveTask(FlaskForm):
    task = SelectField('Task to be removed', validators=[DataRequired()])
    submit = SubmitField('Remove now!')

class ActivateProject(FlaskForm):
    project = SelectField('Project to be re-activated', validators=[DataRequired()])
    submit = SubmitField('Re-activate now!')

class DeactivateProject(FlaskForm):
    project = SelectField('Project to be deactivated', validators=[DataRequired()])
    submit = SubmitField('Deactivate now!')

class ModifyUnit(FlaskForm):
    unit = SelectField('Unit to be modified', validators=[DataRequired()])
    project = SelectField('Change to', validators=[DataRequired()])
    submit = SubmitField('Modify now!')

class CalendarOverview(FlaskForm):
    years = SelectField('Please select a year: ', validators=[DataRequired()])
    submit = SubmitField('Show calendar')

class OverviewEntry(FlaskForm):
    pass

class GetUsers(FlaskForm):
    users = SelectField('Please select a user: ', validators=[DataRequired()])
    submit = SubmitField('Change user now!')

class GetProjects(FlaskForm):
    projects = SelectField('Please select a project: ', validators=[DataRequired()])
    submit = SubmitField('Change project now!')