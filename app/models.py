from datetime import datetime
from hashlib import md5
import json
from time import time
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import redis
import rq
from app import db, login
from app.search import add_to_index, remove_from_index, query_index


class SearchableMixin(object):
    @classmethod
    def search(cls, expression, page, per_page):
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            return cls.query.filter_by(id=0), 0
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        return cls.query.filter(cls.id.in_(ids)).order_by(
            db.case(when, value=cls.id)), total

    @classmethod
    def before_commit(cls, session):
        session._changes = {
            'add': [obj for obj in session.new if isinstance(obj, cls)],
            'update': [obj for obj in session.dirty if isinstance(obj, cls)],
            'delete': [obj for obj in session.deleted if isinstance(obj, cls)]
        }

    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['add']:
            add_to_index(cls.__tablename__, obj)
        for obj in session._changes['update']:
            add_to_index(cls.__tablename__, obj)
        for obj in session._changes['delete']:
            remove_from_index(cls.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindex(cls):
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)


followers = db.Table(
    'followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    waypoints = db.relationship('Waypoint', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140), default=('Patient'))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')
    messages_sent = db.relationship('Message',
                                    foreign_keys='Message.sender_id',
                                    backref='author', lazy='dynamic')
    messages_received = db.relationship('Message',
                                        foreign_keys='Message.recipient_id',
                                        backref='recipient', lazy='dynamic')
    last_message_read_time = db.Column(db.DateTime)
    notifications = db.relationship('Notification', backref='user',
                                    lazy='dynamic')
    tasks = db.relationship('Task', backref='user', lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())
    
    def followed_AIDataset(self):
        followed = AIDataset.query.join(
            followers, (followers.c.followed_id == AIDataset.user_id)).filter(
                followers.c.follower_id == self.id)
        own = AIDataset.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(AIDataset.timestamp.desc())

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'],
            algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

    def new_messages(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return Message.query.filter_by(recipient=self).filter(
            Message.timestamp > last_read_time).count()

    def add_notification(self, name, data):
        self.notifications.filter_by(name=name).delete()
        n = Notification(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(n)
        return n

    def launch_task(self, name, description, *args, **kwargs):
        rq_job = current_app.task_queue.enqueue('app.tasks.' + name, self.id,
                                                *args, **kwargs)
        task = Task(id=rq_job.get_id(), name=name, description=description,
                    user=self)
        db.session.add(task)
        return task

    def get_tasks_in_progress(self):
        return Task.query.filter_by(user=self, complete=False).all()

    def get_task_in_progress(self, name):
        return Task.query.filter_by(name=name, user=self,
                                    complete=False).first()

    picture = db.Column(db.String(128), default='http://imgur.com/yI00Ehb.jpg')
    color = db.Column(db.String(128), default='#8DBE1A') #color for map circle
    sex = db.Column(db.String(64), index=True)
    age = db.Column(db.Float, index=True)
    dob = db.Column(db.DateTime, index=True)
    pob = db.Column(db.String(140), index=True) #Place Of Birth
    weight = db.Column(db.Float, index=True)
    height = db.Column(db.Float, index=True)
    village = db.Column(db.String(140), index=True)
    parish = db.Column(db.String(140), index=True)
    subcounty = db.Column(db.String(140), index=True)
    lon = db.Column(db.String(64))
    lat = db.Column(db.String(64))
    activitylevel = db.Column(db.String(140), index=True) # Not active, Moderately active, very active --- playing, walking, bathing, listening, talking, laughing, reading, home chores 
    
    #Case Definition
    casedefinition_name = db.Column(db.String(140), index=True) # Suspected, Probable, Confirmed - check also and fill table of "Case Definition Details"
    casedefinition_characteristics = db.Column(db.String(140), index=True) # Suspected, Probable, Confirmed - check also and fill table of "Case Definition Details"
    
    # Health Classification
    dateofonset = db.Column(db.DateTime, index=True) #if not sure, - write beginning of the year
    ageofonset = db.Column(db.Integer, index=True)
    where = db.Column(db.String(140), index=True)
    veryfirstsignssymptoms = db.Column(db.String(140), index=True) # Noticed by parent -Multiple options -Fall, Headnodding with food, stiffness, headnodiing with cold, drooling
    
    # Family Info
    guardian_father = db.Column(db.String(140))
    guardian_mother = db.Column(db.String(140))
    guardian_other = db.Column(db.String(140))
    telephone1 = db.Column(db.Integer)
    telephone2 = db.Column(db.Integer)

    #Family History
    nameofidpcamp = db.Column(db.String(140), index=True) #If any?
    yearsspentinidpcamp = db.Column(db.DateTime, index=True) #If any?
    watersourceduringonset = db.Column(db.String(140), index=True) #well, stream or river i.e agoro well
    numberofsiblings = db.Column(db.Integer, index=True)
    numberofsiblingswithnodding = db.Column(db.Integer, index=True)
    numberofsiblingsalive = db.Column(db.Integer, index=True)
    numberofsiblingswithepilepsy = db.Column(db.Integer, index=True)
    noddingrelateddeathsinfam = db.Column(db.Integer, index=True)

    # AI dataset OFFICIAL OFFICIAL

    patientplaceofmedicalservice = db.Column(db.String(140), index=True) # (grade I, grade II, grade III, grade IV, clinic, hospital, care center)
    typeofnearesthealthcenter = db.Column(db.String(140), index=True) # (grade I, grade II, grade III, grade IV, clinic, hospital, care center)
    address = db.Column(db.String(10), index=True) # (binary: 'C' – closer to urban or 'F' – further from urban / referral hospital)
    famsize = db.Column(db.String(10), index=True) # family size (binary: 'LE3' - less or equal to 3 or 'GT3' - greater than 3) 
    pstatus = db.Column(db.String(10), index=True,  default='None') # parent's cohabitation status (binary: 'T' - living together or 'A' - apart)
    medu = db.Column(db.String(140), index=True, default='None') # Mother's Education (numeric: 0 - none, 1 - primary education (P4 grade), 2 - P5 to P7 grade, 3 - O level , 4 -  A level, 5 - Vocational or 6 - higher education)
    fedu = db.Column(db.String(140), index=True, default='None') #Father's Education (numeric: 0 - none, 1 - primary education (P4 grade), 2 - P5 to P7 grade, 3 - O level , 4 -  A level, 5 - Vocational or 6 - higher education)
    mhealth = db.Column(db.String(140), index=True, default='None') # mother’s health condition (numeric: 0 - Deceased, 1 – level 1, level 2, level 3 , level 4 or level 5 healthy)
    fhealth = db.Column(db.String(140), index=True, default='None') # father’s health condition (numeric: 0 - Deceased, 1 – level 1, level 2, level 3 , level 4 or level 5 healthy)
    mjob = db.Column(db.String(140), index=True, default='None') # mother's job (nominal: 'teacher', 'health' care related, civil 'services' (e.g. administrative or police), 'at_home' or 'other')
    fjob = db.Column(db.String(140), index=True, default='None') # father's job (nominal: 'teacher', 'health' care related, civil 'services' (e.g. administrative or police), 'at_home' or 'other')
    reason = db.Column(db.String(140), index=True, default='None') # reason to choose this health service (nominal: close to 'home', charity 'reputation', 'specialized medical service' preference, referral, or 'other') 
    guardian = db.Column(db.String(140), index=True, default='None') # patient's guardian (nominal: 'mother', 'father' or 'other')
    traveltime = db.Column(db.String(140), index=True, default='None') # home to health center travel time (numeric: 1 - <15 min., 2 - 15 to 30 min., 3 - 30 min. to 1 hour, or 4 - >1 hour)
    nursevisittime = db.Column(db.String(140), index=True, default='None') # monthly nurse visit time (numeric: 1 - <2 hours, 2 - 2 to 5 hours, 3 - 5 to 10 hours, or 4 - >10 hours) 
    mealsdaily = db.Column(db.String(140), index=True, default='None') # daily meals (numeric: 1 , 2 , 3 or >4 )
    malnutritiontreatment = db.Column(db.String(10), index=True, default='None') # yes / no
    siblingswithrelatedsickness = db.Column(db.String(10), index=True, default='None') # epilepsy, nodding syndrome, disabilities, mental illnesses (binary: 'LE3' - less or equal to 3 or 'GT3' - greater than 3) 
    seizurespermonth = db.Column(db.String(140), index=True, default='None') # frequency of seizures every month
    durationofseizure = db.Column(db.String(140), index=True, default='None') # 2-5 minutes, 6-10 minutes, 11-20 minutes, more than 21 minutes
    activitylevel = db.Column(db.String(10), index=True, default='None') # (binary: yes or no)
    behavioralproblems = db.Column(db.String(140), index=True, default='None') # multiple selection Aggressive, Depression, Social Isolation, Excessive Sleep, Night Mares
    triggers = db.Column(db.String(140), index=True, default='None') # Multiple selection - Food, Cold, Light, Sun 
    screeningfailed = db.Column(db.String(10), index=True, default='None') # number of past nutrition screening failures (numeric: n if 1<=n<3, else 4) 
    extranutritionalsupport = db.Column(db.String(10), index=True, default='None') # (binary: yes or no) - - - - plumpy nut (nutritional) 
    famed = db.Column(db.String(10), index=True, default='None') # family / guardian daily health support (binary: yes or no)
    extrapaidsupport = db.Column(db.String(10), index=True, default='None')  # extra paid medication within i.e. nutrition, cough, malaria (binary: yes or no)
    famrelation = db.Column(db.String(10), index=True, default='None') # quality of family relationships (numeric: from 1 - very bad to 5 - excellent)
    playout = db.Column(db.String(10), index=True, default='None') # playing with friends (numeric: from 1 - very low to 5 - very high) 
    seizurestatus = db.Column(db.String(10), index=True, default='None') # Current seizure category (level 1, level 2, level 3 . . .) 
    drugadministration = db.Column(db.String(10), index=True, default='None') # number of times drugs not taken on time (numeric: from 0 to 93) 
    schoolenrolment = db.Column(db.String(10), index=True, default='None') # Attending any school? (binary yes / no)

    aidatasetnotes = db.Column(db.String(140))


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class AIDataset():
    #Dataset for use if I want a separate database for AIDataset
    id = db.Column(db.Integer, primary_key=True)
    patientplaceofmedicalservice = db.Column(db.String(140), index=True, default='None') # (grade I, grade II, grade III, grade IV, clinic, hospital, care center)
    #typeofnearesthealthcenter = db.Column(db.String(140), index=True, index=True, default='None') # (grade I, grade II, grade III, grade IV, clinic, hospital, care center)
    address = db.Column(db.String(10), index=True, default='None') # (binary: 'C' – closer to urban or 'F' – further from urban / referral hospital)
    famsize = db.Column(db.String(10), index=True, default='None') # family size (binary: 'LE3' - less or equal to 3 or 'GT3' - greater than 3) 
    pstatus = db.Column(db.String(10), index=True,  default='None') # parent's cohabitation status (binary: 'T' - living together or 'A' - apart)
    medu = db.Column(db.String(140), index=True, default='None') # Mother's Education (numeric: 0 - none, 1 - primary education (P4 grade), 2 - P5 to P7 grade, 3 - O level , 4 -  A level, 5 - Vocational or 6 - higher education)
    fedu = db.Column(db.String(140), index=True, default='None') #Father's Education (numeric: 0 - none, 1 - primary education (P4 grade), 2 - P5 to P7 grade, 3 - O level , 4 -  A level, 5 - Vocational or 6 - higher education)
    mhealth = db.Column(db.String(140), index=True, default='None') # mother’s health condition (numeric: 0 - Deceased, 1 – level 1, level 2, level 3 , level 4 or level 5 healthy)
    fhealth = db.Column(db.String(140), index=True, default='None') # father’s health condition (numeric: 0 - Deceased, 1 – level 1, level 2, level 3 , level 4 or level 5 healthy)
    mjob = db.Column(db.String(140), index=True, default='None') # mother's job (nominal: 'teacher', 'health' care related, civil 'services' (e.g. administrative or police), 'at_home' or 'other')
    fjob = db.Column(db.String(140), index=True, default='None') # father's job (nominal: 'teacher', 'health' care related, civil 'services' (e.g. administrative or police), 'at_home' or 'other')
    reason = db.Column(db.String(140), index=True, default='None') # reason to choose this health service (nominal: close to 'home', charity 'reputation', 'specialized medical service' preference, referral, or 'other') 
    guardian = db.Column(db.String(140), index=True, default='None') # patient's guardian (nominal: 'mother', 'father' or 'other')
    traveltime = db.Column(db.String(140), index=True, default='None') # home to health center travel time (numeric: 1 - <15 min., 2 - 15 to 30 min., 3 - 30 min. to 1 hour, or 4 - >1 hour)
    nursevisittime = db.Column(db.String(140), index=True, default='None') # monthly nurse visit time (numeric: 1 - <2 hours, 2 - 2 to 5 hours, 3 - 5 to 10 hours, or 4 - >10 hours) 
    mealsdaily = db.Column(db.String(140), index=True, default='None') # daily meals (numeric: 1 , 2 , 3 or >4 )
    malnutritiontreatment = db.Column(db.String(10), index=True, default='None') # yes / no
    siblingswithrelatedsickness = db.Column(db.String(10), index=True, default='None') # epilepsy, nodding syndrome, disabilities, mental illnesses (binary: 'LE3' - less or equal to 3 or 'GT3' - greater than 3) 
    seizurespermonth = db.Column(db.String(140), index=True, default='None') # frequency of seizures every month
    durationofseizure = db.Column(db.String(140), index=True, default='None') # 2-5 minutes, 6-10 minutes, 11-20 minutes, more than 21 minutes
    activitylevel = db.Column(db.String(10), index=True, default='None') # (binary: yes or no)
    behavioralproblems = db.Column(db.String(140), index=True, default='None') # multiple selection Aggressive, Depression, Social Isolation, Excessive Sleep, Night Mares
    triggers = db.Column(db.String(140), index=True, default='None') # Multiple selection - Food, Cold, Light, Sun 
    screeningfailed = db.Column(db.String(10), index=True, default='None') # number of past nutrition screening failures (numeric: n if 1<=n<3, else 4) 
    extranutritionalsupport = db.Column(db.String(10), index=True, default='None') # (binary: yes or no) - - - - plumpy nut (nutritional) 
    famed = db.Column(db.String(10), index=True, default='None') # family / guardian daily health support (binary: yes or no)
    extrapaidsupport = db.Column(db.String(10), index=True, default='None')  # extra paid medication within i.e. nutrition, cough, malaria (binary: yes or no)
    famrelation = db.Column(db.String(10), index=True, default='None') # quality of family relationships (numeric: from 1 - very bad to 5 - excellent)
    playout = db.Column(db.String(10), index=True, default='None') # playing with friends (numeric: from 1 - very low to 5 - very high) 
    health = db.Column(db.String(10), index=True, default='None') # current health status (numeric: from 1 - very bad to 5 - very good) 
    drugabsences = db.Column(db.String(10), index=True, default='None') # number of times drugs not taken on time (numeric: from 0 to 93) 
    schoolenrolment = db.Column(db.String(10), index=True, default='None') # Attending any school? (binary yes / no)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    body = db.Column(db.String(140))
    
    def __repr__(self):
        return '<AIDataset {}>'.format(self.body)

class Post(SearchableMixin, db.Model):
    __searchable__ = ['body']
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))

    # CDC Nutritional Status
    height = db.Column(db.Float)
    weight = db.Column(db.Float)
    bmi = db.Column(db.Float)
    muac = db.Column(db.Float)

    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    language = db.Column(db.String(5))

    def __repr__(self):
        return '<Post {}>'.format(self.body)


db.event.listen(db.session, 'before_commit', Post.before_commit)
db.event.listen(db.session, 'after_commit', Post.after_commit)

class Waypoint(SearchableMixin, db.Model):
    __searchable__ = ['place']
    id = db.Column(db.Integer, primary_key=True)
    place = db.Column(db.String(140))

    # Patient waypoint
    placelon = db.Column(db.String(64))
    placelat = db.Column(db.String(64))
    tolon = db.Column(db.String(64))
    tolat = db.Column(db.String(64))
    description = db.Column(db.String(140))

    picture = db.Column(db.String(128), default='http://imgur.com/yI00Ehb.jpg')
    color = db.Column(db.String(128), default='#8DBE1A') #color for map circle

    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    language = db.Column(db.String(5))

    def __repr__(self):
        return '<Waypoint {}>'.format(self.place)


class Trigger():
    # Trigger
    id = db.Column(db.Integer, primary_key=True)
    trigger = db.Column(db.String(140), index=True) # Multiple selection - Food, Cold, Light, Sun etc
    description = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Trigger {}>'.format(self.trigger)


class seizureTracker():
    id = db.Column(db.Integer, primary_key=True)
    typeofseizure = db.Column(db.String(140), index=True) #what happens during seizure - Level1, Level2, Level3, Level4, Level5
    frequencyofseizureperday = db.Column(db.Integer, index=True) # several options - per day, per week, after
    frequencyofseizureperweek = db.Column(db.Integer, index=True) # several options - per day, per week, after
    frequencyofseizurepermonth = db.Column(db.Integer, index=True) # several options - per day, per week, after 
    frequencyofseizureperyear = db.Column(db.Integer, index=True) # several options - per day, per week, after
    durationofseizure = db.Column(db.String(140), index=True) # 2-5 minutes, 6-10 minutes, 11-20 minutes, more than 21 minutes
    activitylevel = db.Column(db.String(140), index=True) # Not active, Moderately active, very active --- playing, walking, bathing, listening, talking, laughing, reading, home chores
    preseizureactivity = db.Column(db.String(140), index=True)# Describe - emotionally, physically, mentally, socially
    postseizureactivity = db.Column(db.String(140), index=True) # Describe - emotionally, physically, mentally, socially

    def __repr__(self):
        return '<Type of seizure {}>'.format(self.typeofseizure)

class BehavioralProblems():
    id = db.Column(db.Integer, primary_key=True)
    behavioralproblem = db.Column(db.String(140), index=True) # multiple selection Aggressive, Depression, Social Isolation, Excessive Sleep, Night Mares
    description = db.Column(db.String(140))

    def __repr__(self):
        return '<Behavioral Problem {}>'.format(self.behavioralproblem)


class MedicationHistory():
    # Medication Data
    id = db.Column(db.Integer, primary_key=True) 
    drug = db.Column(db.String(140), index=True)
    dosage = db.Column(db.String(140), index=True)
    startdate = db.Column(db.DateTime, index=True)
    enddate = db.Column(db.DateTime, index=True)

    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Drug {}>'.format(self.drug)


class SchoolEnrolment():
    id = db.Column(db.Integer, primary_key=True)
    school = db.Column(db.String(140), index=True)
    grade = db.Column(db.String(140), index=True)
    performance = db.Column(db.String(140))
    startdate = db.Column(db.DateTime, index=True)
    enddate = db.Column(db.DateTime, index=True)

    def __repr__(self):
        return '<School enrolment {}>'.format(self.performance)

class ScreeningFailed():
    # Screenings Failed
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), index=True)
    description = db.Column(db.String(140))
    date = db.Column(db.DateTime, index=True)

    def __repr__(self):
        return '<Screening Failed {}>'.format(self.name)


class Cuisine():
    # Food History especially during famine add a section for "body"
    id = db.Column(db.Integer, primary_key=True)
    food = db.Column(db.String(140), index=True)
    description = db.Column(db.String(140), index=True)
    
    startdate = db.Column(db.DateTime, index=True)
    enddate = db.Column(db.DateTime, index=True)

    def __repr__(self):
        return '<Cuisine {}>'.format(self.cuisine)



class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return '<Message {}>'.format(self.body)


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.Float, index=True, default=time)
    payload_json = db.Column(db.Text)

    def get_data(self):
        return json.loads(str(self.payload_json))


class Task(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(128), index=True)
    description = db.Column(db.String(128))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    complete = db.Column(db.Boolean, default=False)

    def get_rq_job(self):
        try:
            rq_job = rq.job.Job.fetch(self.id, connection=current_app.redis)
        except (redis.exceptions.RedisError, rq.exceptions.NoSuchJobError):
            return None
        return rq_job

    def get_progress(self):
        job = self.get_rq_job()
        return job.meta.get('progress', 0) if job is not None else 100


# Start Models for selectField -----------------------------------------

class patientplaceofmedicalservicechoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    extra = db.Column(db.String(50))

    def __repr__(self):
        return '{}'.format(self.name)



class yesnochoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    extra = db.Column(db.String(50))

    def __repr__(self):
        return '{}'.format(self.name)

# End Models for selectField -----------------------------------------