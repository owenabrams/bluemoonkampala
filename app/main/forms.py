from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, RadioField, SubmitField, RadioField, SelectField, TextAreaField, DecimalField
from wtforms.validators import ValidationError, DataRequired, Length
from flask_babel import _, lazy_gettext as _l
from app.models import User, patientplaceofmedicalservicechoice, yesnochoice
from wtforms_sqlalchemy.fields import QuerySelectField


class EditProfileForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    about_me = TextAreaField(_l('About me'),
                             validators=[Length(min=0, max=140)])
          
                              
    lon = StringField(_l('Longitude'), validators=[DataRequired()])
    lat = StringField(_l('Latitude'), validators=[DataRequired()])

    color = StringField(_l('Color'), validators=[DataRequired()])

    submit = SubmitField(_l('Submit'))

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError(_('Please use a different username.'))

# Functions for SelectField ---------------------------------------------------------------------
def patientplaceofmedicalservicechoicequery():
    return patientplaceofmedicalservicechoice.query


def yesnochoicequery():
    return yesnochoice.query

# End Functions for SelectField ---------------------------------------------------------------------

# class patientplaceofmedicalservicechoiceForm(FlaskForm)

class EditAIDatasetForm(FlaskForm): 

    patientplaceofmedicalservice = QuerySelectField(query_factory=patientplaceofmedicalservicechoicequery, allow_blank=True)
    typeofnearesthealthcenter = QuerySelectField(query_factory=yesnochoicequery, allow_blank=True)
    address = SelectField("Nearest health center", choices=[('C','Closer to urban area'),('F','Further from urban area')], coerce=str) 
    famsize = SelectField("Family Size", choices=[("LE3","less or equal to 3 "),("GT3","Greater than 3 ")], coerce=str) 
    pstatus = SelectField("Parents cohabitation status", choices=[('T','Living together'),('A','Living apart')], coerce=str) 
    medu = SelectField("Mothers education level", choices=[(0,'None'),(1,'P1 to P4'),(2,'P5 to P7'),(3,'O Level'),(4,'A Level'),(5,'Vocational'),(6,'Higher')], coerce=str) 
    fedu = SelectField("Fathers education level", choices=[(0,'None'),(1,'P1 to P4'),(2,'P5 to P7'),(3,'O Level'),(4,'A Level'),(5,'Vocational'),(6,'Higher')], coerce=str)
    mhealth = SelectField("Mothers health", choices=[(0,'Deceased'),(1,'Severe Disability'),(2,'Moderate Disability'),(3,'Slight Disability'),(4,'Healthy')], coerce=str) 
    fhealth = SelectField("Fathers health", choices=[(0,'Deceased'),(1,'Severe Disability'),(2,'Moderate Disability'),(3,'Slight Disability'),(4,'Healthy')], coerce=str) 
    mjob = SelectField("Mothers job", choices=[(0,"At Home"),(1,"Health Care"),(2,"Civil Service"),(3,"Teacher"),(4,"Other")], coerce=str) 
    fjob = SelectField("Fathers job", choices=[(0,"At Home"),(1,"Health Care"),(2,"Civil Service"),(3,"Teacher"),(4,"Other")], coerce=str) 
    reason = SelectField("Reason they chose treatment", choices=[(0,"Close To Home"),(1,"Organization Reputation"),(2,"Specialized Medical Service"),(3,"Referral"),(4,"Other")], coerce=str)
    guardian = SelectField("Patients guardian", choices=[(0,"Mother"),(1,"Father"),(2,"Other")], coerce=str)
    traveltime = SelectField("Distance from home for treatment", choices=[(0,"<15 min"),(1,"15 to 30 min"),(2,"30 min. to 1 hour"),(3,">1 hour")], coerce=str)
    nursevisittime = SelectField("Monthly nurse visit time", choices=[(0,"<2 hours"),(1,"2 to 5 hours"),(2,"5 to 10 hours"),(3,">10 hours")], coerce=str)
    mealsdaily = SelectField("Number of daily meals", choices=[(0,"1"),(1,"2"),(2,"3"),(3,">4")], coerce=str)
    malnutritiontreatment = BooleanField(_l('Malnutrition Treatment'))
    siblingswithrelatedsickness = SelectField("Siblings with related sicknes i.e epilepsy", choices=[("LE3","less or equal to 3 "),("GT3","Greater than 3 ")], coerce=str)
    seizurespermonth = SelectField("Monthly frequency of seizures", choices=[(0,"1"),(1,"2"),(2,"3"),(3,">4")], coerce=str)
    durationofseizure = SelectField("Duration of seizure activity", choices=[(0,"2 - 5 minutes"),(1,"6 - 10 minutes"),(2,"11 - 20 minutes"),(3,">21 minutes")], coerce=str)
    activitylevel = BooleanField(_l('Indulge in physical activity?'))
    behavioralproblems = BooleanField(_l('Behavioral Problems?'))
    triggers = SelectField("Triggers of seizure activity", choices=[(0,"Food"),(1,"Cold"),(2,"Light"),(3,"Sun")], coerce=str)
    screeningfailed = SelectField("Screeenings Failed", choices=[(0,">1"),(1,"<3"),(2,">4")], coerce=str)
    extranutritionalsupport = BooleanField(_l('Extra nutritional support?'))
    famed = BooleanField(_l('Family / guardian daily home support?'))
    extrapaidsupport = BooleanField(_l('Extra treatment? Malaria, Cough '))
    
    famrelation = SelectField("Quality of family relationship", choices=[(0,"Very Bad"),(1,"Bad"),(2,"Good"),(3,"Very Good"),(4,"Excellent")], coerce=str)
    playout = BooleanField(_l('Playing out with friends?'))
    seizurestatus = SelectField("Nodding stage", choices=[(0,"Stage 1"),(1,"Stage 2"),(2,"Stage 3"),(3,"Stage 4"),(4,"Stage 5")], coerce=str)
    drugadministration = SelectField("Drug admission consistency", choices=[(0,"Very Bad"),(1,"Bad"),(2,"Good"),(3,"Very Good"),(4,"Excellent")], coerce=str)
    schoolenrolment = BooleanField(_l('Currently enroled in school?'))

    aidatasetnotes = TextAreaField(_l('Notes on patient AI dataset'),
                             validators=[Length(min=0, max=140)])

    submit = SubmitField('Submit AI dataset')


class PostForm(FlaskForm):
    body = TextAreaField(_l('Nurse Notes'), validators=[DataRequired()])
    
    #CDC Nutritional Status
    height = DecimalField('Height', validators=[DataRequired()] )
    weight = DecimalField('Weight', validators=[DataRequired()] )
    bmi = DecimalField('BMI', validators=[DataRequired()] )
    muac = DecimalField('MUAC', validators=[DataRequired()] )

    submit = SubmitField(_l('Submit Nutritional Status'))


class WaypointForm(FlaskForm):
    description = TextAreaField(_l('Description'), validators=[DataRequired()])
    
    #Waypoint to child's destination
    place = StringField(_l('Place'), validators=[DataRequired()])
    placelat = StringField(_l('Place Latitude'), validators=[DataRequired()])
    placelon = StringField(_l('Place longitude'), validators=[DataRequired()])
    tolat = StringField(_l('Point to Latitude'), validators=[DataRequired()])
    tolon = StringField(_l('Point to longitude'), validators=[DataRequired()])

    submit = SubmitField(_l('Submit Waypoint'))
    
class TriggerForm(FlaskForm):
    trigger = TextAreaField(_l('Trigger'), validators=[DataRequired()])
    
    #When triggers happen
    when = StringField(_l('When'), validators=[DataRequired()])

    submit = SubmitField(_l('Submit Waypoint'))


class YesnochoiceForm(FlaskForm):
    #Yes / No Options
    name = StringField('Name', validators=[DataRequired()] )
    extra = StringField('Extra Info', validators=[DataRequired()] )

    submit = SubmitField(_l('Submit Yes / No Option'))

class PatientplaceofmedicalservicechoiceForm(FlaskForm):
    #patient place of medical service Options
    name = StringField('Name', validators=[DataRequired()] )
    extra = StringField('Extra Info', validators=[DataRequired()] )

    submit = SubmitField(_l('Submit Place Of Medical Service'))

class SearchForm(FlaskForm):
    q = StringField(_l('Search'), validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'csrf_enabled' not in kwargs:
            kwargs['csrf_enabled'] = False
        super(SearchForm, self).__init__(*args, **kwargs)


class MessageForm(FlaskForm):
    message = TextAreaField(_l('Message'), validators=[
        DataRequired(), Length(min=1, max=140)])
    submit = SubmitField(_l('Submit'))
