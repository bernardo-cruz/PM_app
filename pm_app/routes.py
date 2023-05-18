import os
from datetime import datetime, timedelta, time

import secrets
from PIL import Image
from flask import (
    render_template, url_for, flash, redirect, request, abort, session
    )
from sqlalchemy.orm import query
from pm_app import app, db, bcrypt, mail
from pm_app.forms import (
    RegistrationForm, LoginForm, UpdateAccountForm, PostForm, 
    RequestResetForm, ResetPasswordForm, CreateProject, CreateUnit, 
    GetHov, GetUnit, GetTime,AddSupervisor, AddAdmin, RemoveUser, RemoveAdmin,
    RemoveSupervisor, RemoveProject, RemoveUnit, RemoveTask, CreateTask, DeactivateProject, ModifyUnit,
    ActivateProject, ChangeTimeEntry, OverviewEntry, CalendarOverview, GetUsers, ModifyRegistrationForm, 
    GetProjects, ModifyProject, FindUnit, ChangeUnit)
from pm_app.models import (
    User,Post, Project, Unit,db, Task , WorkedFor, Admin, Supervisor
    )
from flask_login import (
    login_user, current_user, logout_user, login_required
    )
from flask_mail import Message

@app.route("/")
@app.route("/home")
def home():
    page= request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted).paginate(per_page=5)
    return render_template(
        'home.html',
        title='Forum Page', 
        posts=posts,
        current_user=current_user,
        )

@app.route("/about")
def about():
    projects = Project.query.all()
    units = Unit.query.all()

    # Create a cost per project variable
    def cost_per_project(project_id):
        hours = 0
        cost = 0
        units = Unit.query.filter_by(project_id=project_id).all()
        # Iterate over all units of the project
        for unit in units:
            # Grab all hours of this unit
            time_amount = WorkedFor.query.filter_by(unit_id=unit.id).all()
            for t in time_amount:
                hours += t.time_amount
        cost = round(hours * Project.query.filter_by(id=project_id).first().rate, 3)
        ratio = round(cost / Project.query.filter_by(id=project_id).first().budget *100, 3)
        return [hours,cost,ratio]

    def find_total_hours(unit_pn):
        unit_s = Unit.query.filter_by(pn=unit_pn).all()
        for unt in unit_s:
            total_hours = 0
            work_data = WorkedFor.query.filter_by(unit_id=unt.id).all()
            for hour in work_data:
                total_hours += hour.time_amount
        return total_hours

    def total_costs():
        worked = WorkedFor.query.all()
        projects = Project.query.all()
        cost = 0
        budget = 0
        for work in worked:
            cost += work.time_amount * Project.query.filter_by(
                id= Unit.query.filter_by(id=work.unit_id).first().project_id
                ).first().rate
        for project in projects:
            budget += project.budget
        revenue = round(budget-cost, 3)
        ratio = round(((revenue/budget))*100, 2)
        return [
            "{:,}".format(budget), 
            "{:,}".format(cost), 
            "{:,}".format(revenue),
            "{:,}".format(ratio),
            ]

    return render_template(
        'about.html', 
        title = 'Overview all projects',
        projects = projects, 
        units = units, 
        find_total_hours = find_total_hours,
        cost_per_project = cost_per_project,
        total_costs = total_costs,
        )

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    form.supplier.choices = [("", "- Please select -")] + [(1,"Yes"),(0,"No")]
    if form.validate_on_submit():
        hashed_password = (bcrypt
                        .generate_password_hash(form.password.data)
                        .decode('utf-8'))
        user = User(
            username=form.username.data, 
            email=form.email.data, 
            password=hashed_password,
            supplier=form.supplier.data,
            )
        db.session.add(user)
        db.session.commit()
        flash('The account has been created!', 'success')
        return redirect(url_for('admin'))
    return render_template('register.html', title='Register user', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user,remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:            
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)

@app.route('/posts/new', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(
            title=form.title.data,
            content=form.content.data,
            author=current_user
            )
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html',title='New Post', form=form)

@app.route('/post/<int:post_id>')
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', 
                            title=post.title, 
                            post=post, 
                            legend='Create post')

@app.route('/post/<int:post_id>/update', methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
        return render_template('create_post.html',
                            title='Update Post', 
                            form=form,
                            legend='Update Post')

@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))

@app.route("/usr/<string:username>")
def user_posts(username):
    page= request.args.get('page', 1, type=int)
    user= User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(per_page=5)
    return render_template('user_posts.html', posts=posts, user=user)

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@demo.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}
If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)

@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)

@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)

@app.route("/new_project", methods=['GET', 'POST'])
@login_required
def create_project():
    form = CreateProject()
    if form.validate_on_submit():
        project = Project(
            hov = form.hov.data, 
            customer_name = form.customer_name.data,
            budget = form.budget.data,
            hour_budget = form.hour_budget.data,
            rate = form.rate.data,
            )
        db.session.add(project)
        db.session.commit()
        flash(f'Project {form.customer_name.data} ({form.hov.data}) has been created!', 'success')
        return redirect(url_for('about'))
    return render_template('create_project.html', title='New Project', form=form)

@app.route("/new_unit", methods=['GET', 'POST'])
@login_required
def create_unit():
    form = CreateUnit()
    projects = Project.query.all()
    form.hov.choices = [("", "- Please select -")]+ [(project.id, project.hov) for project in projects]
    if form.validate_on_submit():
        project = Project.query.filter_by(id=form.hov.data).first()
        unit = Unit(
            pn=form.pn.data, 
            pn_name=form.pn_name.data, 
            project_id=form.hov.data,
            )
        db.session.add(unit)
        db.session.commit()
        flash(f'{project.hov} | Unit {form.pn_name.data} ({form.pn.data}) has been created!', 'success')
        return redirect(url_for('about'))
    return render_template(
        'create_unit.html', 
        title='New unit', 
        form=form,
        )

# Create Task 
@app.route("/new_task", methods=['GET', 'POST'])
@login_required
def create_task():
    form = CreateTask()
    if form.validate_on_submit():
        task = Task(
            task_name=form.task_name.data,
            task_description=form.task_description.data,
            )
        db.session.add(task)
        db.session.commit()
        flash(f'Task {form.task_name.data} has been created!', 'success')
        return redirect(url_for('about'))
    return render_template(
        'create_task.html', 
        title='New task', 
        form=form)

@app.route("/new_time_entry", methods=['GET', 'POST'])
@login_required
def create_time_entry():
    form = GetHov()
    projects = Project.query.all()
    form.hov.choices = [("", "- Please select -")]+ [(project.hov, project.hov) for project in projects]
    if form.validate_on_submit():
        return redirect(url_for('get_unit', hov=request.form['hov']))
    return render_template(
        'create_time_entry_1.html',
        title='HoV ?',
        form=form,
        )

@app.route("/new_time_entry/<string:hov>", methods=['GET', 'POST'])
@login_required
def get_unit(hov):
    form = GetUnit()
    project = Project.query.filter_by(hov=hov).first()
    units = Unit.query.filter_by(project_id=project.id).all()
    form.unit.choices = [("", "- Please select -")]+ [(unit.pn, str(unit.pn_name)+' | P/N '+str(unit.pn)) for unit in units]
    if form.validate_on_submit():
        return redirect(
            url_for(
                'get_time', 
                unit_id=request.form['unit'],
                hov=project)
                )
    return render_template(
        'create_time_entry_2.html',
        title='Unit ?',
        hov=hov,
        form=form,
        project=project,
        )

@app.route("/new_time_entry/<string:hov>/<string:unit_id>", methods=['GET', 'POST'])
@login_required
def get_time(unit_id, hov):

    form = GetTime()
    form.time_amount.choices = [("", "- Please select -")]+ [(i/10,i/10) for i in range(5,125,5)]
    tasks = Task.query.all()
    form.task.choices = [("", "- Please select -")]+ [(task.id, task.task_name) for task in tasks]
    unit = Unit.query.filter_by(pn=unit_id).first()
    if form.validate_on_submit():
        # Check if the unit_id at the day of date_of_work is unique
        if WorkedFor.query.filter_by(unit_id=unit.id, date_of_work=form.date_of_work.data).first():
            flash('Time entry already exists for this day', 'warning')
            return redirect(url_for('create_time_entry'))
        time_entry = WorkedFor(
            user_id=current_user.id,
            unit_id=unit.id,
            task_id=form.task.data,
            time_amount=form.time_amount.data,
            date_of_work=form.date_of_work.data,
            )
        flash(f'Your entry was successful for {unit.pn_name} (P/N {unit.pn}), {form.time_amount.data} [h], {form.date_of_work.data}', 'success')
        db.session.add(time_entry)
        db.session.commit()
        return redirect(url_for('about'))
    return render_template(
        'create_time_entry_3.html',
        title='Time ?',
        form=form,
        hov=hov,
        unit_id=unit_id,
        unit=unit
        )

# Change time entry - get the worked_for id, delete the entry and redirect to the create_time_entry page
@app.route("/change_time_entry/", methods=['GET', 'POST'])
@login_required
def change_time_entry():
    form = ChangeTimeEntry()
    if current_user.username == 'admin':
        entries = WorkedFor.query.all()
    else:
        entries = WorkedFor.query.filter_by(user_id=current_user.id)
    form.entries.choices = [("", "- Please select -")]+ [(
        entry.id, str(
            Unit.query.filter_by(id=entry.unit_id).first().pn_name + " " + 
            Project.query.filter_by(id=Unit.query.filter_by(id=entry.unit_id).first().project_id).first().hov + " " + 
            Task.query.filter_by(id=entry.task_id).first().task_name + " " +str(entry.time_amount) + " [h] ")
            ) for entry in entries]
    if form.validate_on_submit():
        entry = WorkedFor.query.filter_by(id=form.entries.data).first()
        db.session.delete(entry)
        db.session.commit()
        flash(f'Entry {Unit.query.filter_by(id=entry.unit_id).first().pn_name + " " + Project.query.filter_by(id=Unit.query.filter_by(id=entry.unit_id).first().project_id).first().hov + " "} has been deleted!', 'success')
        return redirect(url_for('create_time_entry'))
    return render_template(
        'change_time_entry.html',
        title='Change time entry',
        form=form,
        )

# Create a base route for admins
@app.route("/admin/")
@login_required
def admin():
    user = Admin.query.filter_by(user_id=current_user.id).first()
    if user:
        return render_template(
            'admin.html', 
            title='Admin',
            user=user,
            current_user=current_user,
            )
    else:
        flash('This area is reserved for admins only! ','danger')
        return redirect(url_for('home'))

# Create a route to add a user to supervisor
@app.route("/admin/<string:username>/add_supervisor/", methods=['GET', 'POST'])
@login_required
def add_supervisor(username):
    form = AddSupervisor()
    users = User.query.all()
    form.supervisor.choices = [("", "- Please select -")]+ [(user.id, user.username) for user in users]
    if form.validate_on_submit():
        user_id = form.supervisor.data
        id = User.query.filter_by(id=user_id).first()
        if Supervisor.query.filter_by(user_id=user_id).first():
            flash(f'User {id.username} is already supervisor!', 'danger')
            return redirect(url_for('admin'))
        else:
            supervisor = Supervisor(
                user_id=id.id,
                )
            db.session.add(supervisor)
            db.session.commit()
            flash(f'User {id.username} has been added!', 'success')
            return redirect(url_for('admin'))
    return render_template(
        'add_supervisor.html', 
        title='Add User',
        form=form,
        )

# Create a route to add a user to admin
@app.route("/admin/<string:username>/add_admin/", methods=['GET', 'POST'])
@login_required
def add_admin(username):
    form = AddAdmin()
    users = User.query.all()
    form.admin.choices = [("", "- Please select -")]+ [(user.id, user.username) for user in users]
    if form.validate_on_submit():
        user_id = form.admin.data
        id = User.query.filter_by(id=user_id).first()
        if Admin.query.filter_by(user_id=user_id).first():
            flash(f'User {id.username} is already admin!', 'danger')
            return redirect(url_for('admin'))
        else:
            admin = Admin(
                user_id=id.id,
                )
            db.session.add(admin)
            db.session.commit()
            flash(f'User {id.username} has been added!', 'success')
            return redirect(url_for('admin'))
    return render_template(
        'add_admin.html', 
        title='Add User',
        form=form,
        )

# Remove user  
@app.route("/admin/<string:username>/remove_user/", methods=['GET', 'POST'])
@login_required
def remove_user(username):
    form = RemoveUser()
    users = User.query.all()
    form.user.choices = [("", "- Please select -")]+ [(user.id, user.username) for user in users if not user.username == 'admin']
    if form.validate_on_submit():
        # Add check if user is already in WorkedFor
        user_id = form.user.data
        id = User.query.filter_by(id=user_id).first()
        if id.username == 'admin':
            flash(f'{id.username} cannot be removed!', 'danger')
            return redirect(url_for('remove_user',username=current_user))
        if id:
            user = User.query.filter_by(id=user_id).first()
            admin = Admin.query.filter_by(user_id=user_id).first()
            supervisor = Supervisor.query.filter_by(user_id=user_id).first()

            db.session.delete(user)
            if admin:
                db.session.delete(admin)
            if supervisor:
                db.session.delete(supervisor)
            db.session.commit()

            flash(f'User {id.username} has been removed!', 'success')
            return redirect(url_for('admin'))
    return render_template(
        'remove_from_db.html',
        title='Remove User',
        form=form,
        )

# Remove user from admin
@app.route("/admin/<string:username>/remove_admin/", methods=['GET', 'POST'])
@login_required
def remove_admin(username):
    form = RemoveAdmin()
    admins = Admin.query.all()
    form.user.choices = [("", "- Please select -")]+ [(admin.id, User.query.filter_by(id=admin.user_id).first().username) for admin in admins if not User.query.filter_by(id=admin.user_id).first().username == 'admin']
    if form.validate_on_submit():
        user = User.query.filter_by(id=form.user.data).first()
        admin = Admin.query.filter_by(user_id=user.id).first()
        if user.username == 'admin':
            flash(f'{user.username} cannot be removed!', 'danger')
            return redirect(url_for('remove_admin',username=current_user))
        db.session.delete(admin)
        db.session.commit()
            
        flash(f'User {user.username} has been removed!', 'success')
        return redirect(url_for('admin'))
    return render_template(
        'remove_from_db.html',
        title='Remove Admin',
        form=form,
        )

# Remove user from supervisor
@app.route("/admin/<string:username>/remove_supervisor/", methods=['GET', 'POST'])
@login_required
def remove_supervisor(username):
    form = RemoveSupervisor()
    supervisors = Supervisor.query.all()
    form.user.choices = [("", "- Please select -")]+ [(supervisor.id, User.query.filter_by(id=supervisor.user_id).first().username) for supervisor in supervisors]
    if form.validate_on_submit():
        user = User.query.filter_by(id=form.user.data).first()
        supervisor = Supervisor.query.filter_by(user_id=user.id).first()

        db.session.delete(supervisor)
        db.session.commit()
            
        flash(f'User {user.username} has been removed!', 'success')
        return redirect(url_for('admin'))
    return render_template(
        'remove_from_db.html',
        title='Remove Supervisor',
        form=form,
        )

# Overview of all users
@app.route("/admin/<string:username>/users/", methods=['GET', 'POST'])
@login_required
def overview_users(username):
    users = User.query.all()
    kind = 'users'
    return render_template(
        'overview_users.html',
        title=f'Overview {kind.capitalize()}',
        kind=kind,
        infos=users,
        )

# Overview of all supervisors
@app.route("/admin/<string:username>/supervisors/", methods=['GET', 'POST'])
@login_required
def overview_supervisors(username):
    users = [usr.id for usr in User.query.all() for spr in Supervisor.query.all() if usr.id == spr.user_id ]
    users = [name for name in User.query.all() if name.id in users]
    kind = 'supervisors'
    return render_template(
        'overview_supervisors.html',
        title=f'Overview {kind.capitalize()}',
        kind=kind,
        infos=users,
        )

# Overview of all admins
@app.route("/admin/<string:username>/admins/", methods=['GET', 'POST'])
@login_required
def overview_admins(username):
    users = [usr.id for usr in User.query.all() for adm in Admin.query.all() if usr.id == adm.user_id ]
    users = [name for name in User.query.all() if name.id in users]
    kind = 'admins'
    return render_template(
        'overview_admins.html',
        title=f'Overview {kind.capitalize()}',
        kind=kind,
        infos=users,
        )

# Overview of all units
@app.route("/admin/<string:username>/units/", methods=['GET', 'POST'])
@login_required
def overview_units(username):
    units = Unit.query.all()
    kind = 'units'
    return render_template(
        'overview_units.html',
        title=f'Overview {kind.capitalize()}',
        kind=kind,
        infos=units,
        )

# Overview of all tasks
@app.route("/admin/<string:username>/tasks/", methods=['GET', 'POST'])
@login_required
def overview_tasks(username):
    tasks = Task.query.all()
    kind = 'tasks'
    return render_template(
        'overview_tasks.html',
        title=f'Overview {kind.capitalize()}',
        kind=kind,
        infos=tasks,
        )

# Delete project 
@app.route("/admin/<string:username>/delete_project/", methods=['GET', 'POST'])
@login_required
def delete_project(username):
    form = RemoveProject()
    form.project.choices = [("", "- Please select -")]+ [(project.id, project.hov) for project in Project.query.all()]
    if form.validate_on_submit():
        project = Project.query.filter_by(id=form.project.data).first()
        unit = Unit.query.filter_by(project_id=form.project.data).first()
        if unit:
            flash(f'Project {project.hov} cannot be deleted, because it is not empty!', 'danger')
            return redirect(url_for('admin'))
        db.session.delete(project)
        db.session.commit()
        flash(f'Project {form.project.data} has been deleted!', 'success')
        return redirect(url_for('admin'))
    return render_template(
        'remove_project.html',
        title='Delete Project',
        form=form,
        )

# Delete a unit
@app.route("/admin/<string:username>/delete_unit/", methods=['GET', 'POST'])
@login_required
def delete_unit(username):
    form = RemoveUnit()
    form.unit.choices = [("", "- Please select -")]+ [(unit.id, unit.pn) for unit in Unit.query.all()]
    if form.validate_on_submit():
        unit = Unit.query.filter_by(id=form.unit.data).first()
        worked = WorkedFor.query.filter_by(unit_id=form.unit.data).all()
        if worked:
            flash(f'Unit {unit.pn} cannot be deleted, employees have already worked for that!', 'danger')
            return redirect(url_for('admin'))
        db.session.delete(unit)
        db.session.commit()
        flash(f'Unit {unit.pn_name} has been deleted!', 'success')
        return redirect(url_for('admin'))
    return render_template(
        'remove_unit.html',
        title='Delete Unit',
        form=form,
        )

# Delete a task
@app.route("/admin/<string:username>/delete_task/", methods=['GET', 'POST'])
@login_required
def delete_task(username):
    form = RemoveTask()
    form.task.choices = [("", "- Please select -")]+ [(task.id, task.task_name) for task in Task.query.all()]
    if form.validate_on_submit():
        task = Task.query.filter_by(id=form.task.data).first()
        worked = WorkedFor.query.filter_by(task_id=form.task.data).all()
        if worked:
            flash(f'Task {task.task_name} cannot be deleted, employees have already worked for that!', 'danger')
            return redirect(url_for('admin'))
        db.session.delete(task)
        db.session.commit()
        flash(f'Task {form.task.data} has been deleted!', 'success')
        return redirect(url_for('admin'))
    return render_template(
        'remove_task.html',
        title='Delete Task',
        form=form,
        )

# Deactivate a project
@app.route("/admin/<string:username>/deactivate_project/", methods=['GET', 'POST'])
@login_required
def deactivate_project(username):
    form = DeactivateProject()
    if Project.query.filter(Project.date_deactivation == None).all():
        form.project.choices = [("", "- Please select -")]+ [(project.id, project.hov) for project in Project.query.filter(Project.date_deactivation == None).all()]
    else:
        form.project.choices = [('','- No project deactivated -')]
    if form.validate_on_submit():
        project = Project.query.filter_by(id=form.project.data).first()
        if project.date_deactivation:
            flash(f'Project {project.hov} is already deactivated!', 'danger')
            return redirect(url_for('deactivate_project',username=current_user))
        else:
            project.date_deactivation = datetime.utcnow()
            db.session.commit()
            flash(f'Project {project.hov} has been deactivated!', 'success')
            return redirect(url_for('admin'))     
    return render_template(
        'activate_deactivate_project.html',
        title='Deactivate Project',
        form=form,
        )

# Activate a project
@app.route("/admin/<string:username>/reactivate_project/", methods=['GET', 'POST'])
@login_required
def reactivate_project(username):
    form = ActivateProject()
    # Query all projects that are deactivated
    if Project.query.filter(Project.date_deactivation != None).all():
        form.project.choices = [("", "- Please select -")]+ [(project.id, project.hov) for project in Project.query.filter(Project.date_deactivation != None).all()]
    else:
        form.project.choices = [('','- No project deactivated -')]
    if form.validate_on_submit():
        project = Project.query.filter_by(id=form.project.data).first()
        if not project.date_deactivation:
            flash(f'Project {project.hov} is not deactivated!', 'danger')
            return redirect(url_for('reactivate_project',username=current_user))
        else:
            project.date_deactivation = None
            db.session.commit()
            flash(f'Project {project.hov} has been activated!', 'success')
            return redirect(url_for('admin'))     
    return render_template(
        'activate_deactivate_project.html',
        title='Activate Project',
        form=form,
        )

# Show active vs. deactived projects using about.html template
@app.route("/admin/<string:username>/show_project_status/", methods=['GET', 'POST'])
@login_required
def show_project_status(username):
    projects = Project.query.all()
    active_projects = [project for project in projects if not project.date_deactivation]
    deactivated_projects = [project for project in projects if project.date_deactivation]
    return render_template(
        'overview_project_status.html',
        title='Status overview projects',
        active_projects=active_projects,
        deactivated_projects=deactivated_projects,
        )

# Modify project_id of a unit
@app.route("/admin/<string:username>/modify_unit/", methods=['GET', 'POST'])
@login_required
def modify_unit(username):
    form = ModifyUnit()
    form.unit.choices = [("", "- Please select -")]+ [(unit.id, f'{unit.pn} in {Project.query.filter_by(id=unit.project_id).first().hov}') for unit in Unit.query.all()]
    form.project.choices = [("", "- Please select -")]+ [(project.id, project.hov) for project in Project.query.all()]

    def get_project_name(unit_id):
        project = Project.query.filter_by(id=unit_id).first()
        return project.hov

    if form.validate_on_submit():
        unit = Unit.query.filter_by(id=form.unit.data).first()
        project_old = Project.query.filter_by(id=unit.project_id).first()

        project_new = Project.query.filter_by(id=form.project.data).first()

        if unit.project_id == project_new.id:
            flash(f'Unit {unit.pn} already belongs to project {project_old.hov}!', 'danger')
            return redirect(url_for('modify_unit',username=current_user))
        unit.project_id = form.project.data
        db.session.commit()
        flash(f'Unit {unit.pn} has been modified from {project_old.hov} to {project_new.hov}', 'success')
        return redirect(url_for('admin'))
    return render_template(
        'modify_unit.html',
        title='Modify Unit',
        form=form,
        get_project_name=get_project_name,
        )

# Modify a user, fist get user, than modify user
@app.route("/admin/get_user/", methods=['GET', 'POST'])
@login_required
def get_user():
    form = GetUsers()
    users = User.query.all()
    form.users.choices = [("", "- Please select -")]+ [(user.id, user.username) for user in users]
    if form.validate_on_submit():
        return redirect(url_for('modify_user',user_id=form.users.data))
    return render_template(
        'change_user.html',
        title = 'User to be modified',
        form = form,
    )

# Modify the user from previous 
@app.route("/admin/<int:user_id>/modify_user/", methods=['GET', 'POST'])
@login_required
def modify_user(user_id):
    user = User.query.get_or_404(user_id)
    form = ModifyRegistrationForm()
    if not Admin.query.filter_by(user_id=current_user.id).first():
        abort(403)
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        if form.password.data:
            user.password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        db.session.commit()
        flash(f'User {user.username} has been modified!', 'success')
        return redirect(url_for('admin'))
    elif request.method == 'GET':
        # form.supplier.choices = [("", "- Please select -")] + [(1,"Yes"),(0,"No")]
        form.username.data = user.username
        form.email.data = user.email
    return render_template(
        'modify_register.html', 
        title='Modify user', 
        form=form,
        )

# Modify a project, fist get project, than modify project
@app.route("/admin/get_project/", methods=['GET', 'POST'])
@login_required
def get_project():
    form = GetProjects()
    projects = Project.query.all()
    form.projects.choices = [("", "- Please select -")]+ [(project.id, f'{project.hov} {project.customer_name}') for project in projects]
    if form.validate_on_submit():
        return redirect(url_for('modify_project',project_id=form.projects.data))
    return render_template(
        'change_project.html',
        title = 'Project to be modified',
        form = form,
    )

# Modify project 
@app.route("/admin/<int:project_id>/modify_project/", methods=['GET', 'POST'])
@login_required
def modify_project(project_id):
    project = Project.query.get_or_404(project_id)
    form = ModifyProject()
    if not Admin.query.filter_by(user_id=current_user.id).first():
        abort(403)
    if form.validate_on_submit():
        project.hov = form.hov.data 
        project.customer_name = form.customer_name.data
        project.budget = form.budget.data
        project.hour_budget = form.hour_budget.data
        project.rate = form.rate.data
        db.session.commit()
        flash(f'Project {form.customer_name.data} ({form.hov.data}) has been modified!', 'success')
        return redirect(url_for('admin'))
    elif request.method == 'GET':
        form.hov.data = project.hov
        form.customer_name.data  = project.customer_name
        form.budget.data  = project.budget
        form.rate.data  = project.rate
        form.hour_budget.data  = project.hour_budget
    return render_template('create_project.html', title='Modify Project', form=form)


# Modify a unit, fist get unit, than modify unit
@app.route("/admin/find_unit/", methods=['GET', 'POST'])
@login_required
def find_unit():
    form = FindUnit()
    units = Unit.query.all()
    form.units.choices = [("", "- Please select -")]+ [(unit.id, f'{unit.pn_name} ({unit.pn})') for unit in units]
    if form.validate_on_submit():
        return redirect(url_for('change_unit',unit_id=form.units.data))
    return render_template(
        'change_unit.html',
        subtitle = 'Units',
        title = 'Unit to be modified',
        form = form,
    )

# Modify unit 
@app.route("/admin/<int:unit_id>/change_unit/", methods=['GET', 'POST'])
@login_required
def change_unit(unit_id):
    unit = Unit.query.get_or_404(unit_id)
    form = ChangeUnit()
    if not Admin.query.filter_by(user_id=current_user.id).first():
        abort(403)
    if form.validate_on_submit():
        unit.pn_name = form.pn_name.data 
        unit.pn = form.pn.data
        unit.project_id = form.hov.data
        db.session.commit()
        flash(f'Unit {form.pn.data} ({form.pn_name.data}) has been modified!', 'success')
        return redirect(url_for('admin'))
    elif request.method == 'GET':
        form.pn_name.data = unit.pn_name
        form.pn.data  = unit.pn
        projects = Project.query.all()
        form.hov.choices  =[("", "- Please select -")]+ [(project.id,f'{project.hov} ({project.customer_name})') for project in projects]  
    return render_template(
        'create_unit.html', 
        title='Modify Unit', 
        form=form)

# Calender Overview
@app.route("/calendar/", methods=['GET', 'POST'])
@login_required
def calendar_overview():
    form = CalendarOverview()
    weekdays = [
        'Week','Monday','Tuesday','Wednesday',
        'Thursday','Friday',#'Saturday',#'Sunday',
        ]

    # Query all Users, Units, Projects and Tasks.     
    def query_per_date(date_obj,user=None):
        # Query all WorkedFor entries with date_obj date
        if Admin.query.filter_by(user_id=current_user.id).first():
            worked = WorkedFor.query.filter_by(date_of_work=date_obj).all()
        elif Supervisor.query.filter_by(user_id=current_user.id).first():
            worked = WorkedFor.query.filter_by(date_of_work=date_obj).all()
        else:
            worked = WorkedFor.query.filter(WorkedFor.date_of_work == date_obj, WorkedFor.user_id == current_user.id).all()
            
        entry_list = []
        for entry in worked:
            # Query all Users, Units, Projects and Tasks. 
            entry_list.append(
                dict(
                    entry_id = entry.id,
                    user = User.query.filter_by(id=entry.user_id).first().username,
                    unit = Unit.query.filter_by(id=entry.unit_id).first().pn,
                    unit_name = Unit.query.filter_by(id=entry.unit_id).first().pn_name,
                    project = Project.query.filter_by(id=Unit.query.filter_by(id=entry.unit_id).first().project_id).first().hov,
                    task = Task.query.filter_by(id=entry.task_id).first().task_name,
                    time = f'{entry.time_amount} [h]',
                    )
            )

        return entry_list

    # Returns a dictionary as follows: key = date and values = [weekday , week number]
    def year_data(year=None):

        if year is None:
            date = datetime.now()
            year = date.strftime("%Y")

        # Create placeholders boundary days of year 
        day_one_obj = datetime(int(year), 1, 1)
        day_last_obj = datetime(int(year), 12, 31)

        # Create placeholder for the date of the day one's week
        DayOneOfFirstDayWeek_obj = day_one_obj - timedelta(days = day_one_obj.weekday())

        # Create placeholder for the date of the day last's week
        DayLastOfLastDayWeek_obj = day_last_obj + timedelta(days = 6 - day_last_obj.weekday())

        # Create a nested dictionary with the week of the year as key and the correponding dates and weekdays as values. 
        calender = {
            (DayOneOfFirstDayWeek_obj + timedelta(days=day)).strftime("%d/%m/%Y"):
            {
                int(
                    (DayOneOfFirstDayWeek_obj + timedelta(days=day)).strftime("%V")
                    )+1:
                (DayOneOfFirstDayWeek_obj + timedelta(days=day)).strftime("%A"),
            }
            for day in range(
                0, (
                    DayLastOfLastDayWeek_obj - DayOneOfFirstDayWeek_obj).days + 1
                )
            }
        
        return calender
            
    def convert_dt_obj(string):
        date = dict(
            cw = int(datetime.strptime(string , "%d/%m/%Y").strftime("%V")),
            day = datetime.strptime(string , "%d/%m/%Y").strftime("%d"),
            month = datetime.strptime(string , "%d/%m/%Y").strftime("%m"),
            year = datetime.strptime(string , "%d/%m/%Y").strftime("%Y"),
            date = datetime.strptime(string , "%d/%m/%Y").strftime("%d/%m/%Y"),
            date_obj = datetime.strptime(string , "%d/%m/%Y")
        )
        return date

    return render_template(
        'calendar.html',
        title = 'Calendar Overview',
        form = form,
        weekdays = weekdays,
        year_data = year_data,
        convert_dt_obj = convert_dt_obj,
        query_per_date = query_per_date,
        )

# Summary Overview Time Entry from Calendar
@app.route("/calendar/<int:entry_id>/", methods=['GET'])
@login_required
def overview_entry(entry_id):
    form = OverviewEntry()
    worked = WorkedFor.query.filter_by(id=entry_id).first()
    user = User.query.filter_by(id=worked.user_id).first()
    unit = Unit.query.filter_by(id=worked.unit_id).first()
    project = Project.query.filter_by(
        id=Unit.query.filter_by(
            id=worked.unit_id).first().project_id
            ).first()
    task = Task.query.filter_by(id=worked.task_id).first()

    if form.validate_on_submit():
        worked.time_amount = form.time_amount.data
        db.session.commit()
        flash(f'Time entry for {user.username} has been modified!', 'success')
        return redirect(url_for('calendar_overview'))

    return render_template(
        'overview_entry.html',
        title = 'Overview Entry',
        form = form,
        worked = worked,
        user = user,
        unit = unit,
        project = project,
        task = task,
        )
    
