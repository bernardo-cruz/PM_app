from datetime import datetime

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from sqlalchemy.orm import lazyload
from pm_app import db, login_manager, app, bcrypt
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    supplier = db.Column(db.Integer, nullable=False)

    posts = db.relationship('Post', backref='author', lazy=True)
    workedfor = db.relationship('WorkedFor', backref='author', lazy=True)

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"

# Create a table of supervisors, which refer to the User.id as foreign key | supervisors see anything. Can't change anything. 
class Supervisor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Supervisors('{self.user_id}')"

# Create a table of admins, which refer to the User.id as foreign key | admins see everything. Can change everything.
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False,unique=True)

    def __repr__(self):
        return f"Admins('{self.user_id}')"

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"


# ------- Modification towards BLG -------
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True)
    hov = db.Column(db.Text(100),nullable=False, unique=True)
    customer_name = db.Column(db.Text(100),unique=False)
    budget = db.Column(db.Float, nullable=False)
    hour_budget = db.Column(db.Float, nullable=True, default=None)
    rate = db.Column(db.Float, nullable=True, default=120.0)

    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_deactivation = db.Column(db.DateTime, nullable=True, default=None)

    def __repr__(self):
        return f"Project('{self.hov}', '{self.customer_name}')"

class Unit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer,db.ForeignKey('project.id'), nullable=False)
    pn = db.Column(db.Integer,nullable=False, unique=False)
    pn_name = db.Column(db.Text(100),unique=False)

    workedfor = db.relationship('WorkedFor',backref='unit',lazy=True)

    def __repr__(self):
        return f"Unit('{self.pn_name}', '{self.pn}')"

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_name = db.Column(db.Text(100),unique=False,nullable=False)
    task_description = db.Column(db.Text(100),unique=False)
    workedfor = db.relationship('WorkedFor',backref='task',lazy=True)

    def __repr__(self):
        return f"Tasks('{self.task}')"

class WorkedFor(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer,db.ForeignKey('user.id'), nullable=False)
    unit_id = db.Column(db.Integer,db.ForeignKey('unit.id'), nullable=False)
    task_id = db.Column(db.Integer,db.ForeignKey('task.id'), nullable=False)

    time_amount = db.Column(db.Float, nullable=False)
    date_of_work = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"WorkedFor(user_id:{self.user_id}, unit_id:{self.unit_id}, task_id:{self.task_id}, time_amount:{self.time_amount}, date_of_work:{self.date_of_work})"

db.create_all()

def add_column(engine, table_name, column):
    column_name = column.compile(dialect=engine.dialect)
    column_type = column.type.compile(engine.dialect)
    engine.execute('ALTER TABLE %s ADD COLUMN %s %s' % (table_name, column_name, column_type))

def create_admin():
    hashed_password = (bcrypt
                .generate_password_hash('password')
                .decode('utf-8')
                )
    admin_1 = User(
        username = 'admin',
        email = 'admin@admin.admin',
        password = hashed_password,
        supplier = 0
        )
    db.session.add(admin_1)
    db.session.commit()

    admin = Admin(
        user_id = User.query.filter_by(username='admin').first().id
        )
    db.session.add(admin)
    db.session.commit()

def create_dummy_task():
    tasks = [
        'Project admin',
        '2D drawings',
        '3D models',
        'ILR',
        'STP',
        'STR',
        'FWR',
        'CRs',
        ]
    for task in tasks:
        task = Task(
            task_name = task,
        )
        db.session.add(task)
    db.session.commit()

def create_dummy_projects():
    hovs = [
        'DLH01',
        'SWR01',
    ]
    customers = [
        'Swiss Internations Airlines',
        'Deutsche Lufthansa'
    ]
    projects={}

    for hov in hovs:
        if 'DLH' in hov:
            projects[hov]=customers[1]
        else:
            projects[hov]=customers[0]

    for project in projects:
        prj = Project(
            hov = project,
            customer_name = projects[project],
            budget=200000,
            rate=120,
        )
        db.session.add(prj)
    db.session.commit()

    ## ==================================================
    names = ['G'+str(n) for n in range(1,10)]
    pns = ['110'+str(n)+'000' for n in range(1,10)]
    units = {}

    for n in range(len(names)):
        units[names[n]]=pns[n]    

    n=0
    for project in projects:
        for unit in units:
            unt = Unit(
                project_id=Project.query.filter_by(hov=project).first().id,
                pn=units[unit]+f'-{n}20',
                pn_name=unit,
            )
            db.session.add(unt)
        n+=1
    db.session.commit()

if Project.query.all() == []:
    create_dummy_projects()

if Task.query.all() == []:
    create_dummy_task()

if Admin.query.all() == []:
    create_admin()

