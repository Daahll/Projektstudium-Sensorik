
from flask import Flask, jsonify, render_template, request, session, redirect, url_for ,flash, request, send_file
from model import db, Trainings, Ebp, Rangordnungstest, Benutzer, Proben, Probenreihen, Dreieckstest, Auswahltest, Paar_vergleich, Konz_reihe, Hed_beurteilung, Profilprüfung, Geruchserkennung, Aufgabenstellungen,Prüfvarianten
from forms import *
from uuid import uuid4
from datetime import datetime
from jinja2 import Environment
import pandas as pd
import json
import pdfkit
import os

app = Flask(__name__)

app.debug = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123@localhost/praktikum_db'
app.config['SECRET_KEY'] = 'secret_key'


db.init_app(app)

INACTIVITY_THRESHOLD = 3600 # 1 hour in seconds

path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
setted_professor_password = 'hswt_sensorik'



def zip_lists(a, b):
    return zip(a, b)

def print_form_validation_errors(form):
    for field_name, field in form._fields.items():
        if field.errors:
            error_messages = ', '.join(str(error) for error in field.errors)
            print(f"Validation errors for field '{field_name}': {error_messages}")
        else:
            print(f"No validation errors for field '{field_name}'")
    return ''  # Add this line to return an empty string
 # Add this line to return an empty string

def create_sample_in_database(form_data):
    """
    Creates a new sample record in the database with the given form data.

    :param form_data: A dictionary containing the form data.
    :type form_data: dict
    :return: None
    """
    proben_nr = form_data.get('proben_nr')
    probenname = form_data.get('probenname')
    farbe = form_data.get('farbe')
    farbintensität = form_data.get('farbintensitaet')
    geruch = form_data.get('geruch')
    geschmack = form_data.get('geschmack')
    textur = form_data.get('textur')
    konsistenz = form_data.get('konsistenz')

    sample = Proben(proben_nr=proben_nr, probenname=probenname, farbe=farbe, farbintensität=farbintensität,
                    geruch=geruch, geschmack=geschmack, textur=textur, konsistenz=konsistenz)

    db.session.add(sample)
    db.session.commit()

def update_sample_in_database(sample_id, form_data):
    try:
        sample = Proben.query.get(sample_id)
        if sample is None:
            raise ValueError("Sample not found in the database.")
        
        sample.probenname = form_data.get('probenname')
        sample.proben_nr = form_data.get('proben_nr')
        sample.farbe = form_data.get('farbe')
        sample.farbintensität = form_data.get('farbintensitaet')
        sample.geruch = form_data.get('geruch')
        sample.geschmack = form_data.get('geschmack')
        sample.textur = form_data.get('textur')
        sample.konsistenz = form_data.get('konsistenz')

        db.session.commit()
    except Exception as e:
        print(f"Error updating sample: {e}")
        db.session.rollback()

def get_form_data_from_json(filename):
        try:
            with open(filename, 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            data = None

        return data

def fill_ebp_form(form, question):
    aufgabe = Aufgabenstellungen.query.get(question.aufgabenstellung_id).aufgabenstellung
    form.aufgabenstellung.label = aufgabe
    form.aufgabenstellung.data = aufgabe

    probe = Proben.query.get(question.proben_id)
    form.proben_nr.label = probe.proben_nr
    form.proben_nr.data = probe.proben_nr
    return form

def fill_rangordnungstest_form(form, question):
    
    aufgabe = Aufgabenstellungen.query.get(question.aufgabenstellung_id)
    form.aufgabenstellung.label = aufgabe.aufgabenstellung
    form.aufgabenstellung.data = aufgabe.aufgabenstellung

    proben = Probenreihen.query.get(question.probenreihe_id).proben_ids

    for i, probe in enumerate(proben):
        probe = Proben.query.get(probe)
        if len(form.ränge) < len(proben):
            form.ränge.append_entry()
        if len(form.proben) < len(proben):
            form.proben.append_entry()
        form.proben[i].label = probe.proben_nr
        form.proben[i].data = probe.proben_nr
        form.ränge[i].choices = [(i, i) for i in range(1, len(proben) + 1)]

    return form

def fill_auswahltest_form(form, question):

    aufgabe = Aufgabenstellungen.query.get(question.aufgabenstellung_id)
    form.aufgabenstellung.label = aufgabe.aufgabenstellung
    form.aufgabenstellung.data = aufgabe.aufgabenstellung
    
    proben = Probenreihen.query.get(question.probenreihe_id).proben_ids
    for i, probe in enumerate(proben):
        probe = Proben.query.get(probe)
        if len(form.einordnungen) < len(proben):
            form.einordnungen.append_entry()
        if len(form.proben) < len(proben):
            form.proben.append_entry()
        if len(form.bemerkungen) < len(proben):
            form.bemerkungen.append_entry()
        form.proben[i].label = probe.proben_nr
        form.proben[i].data = probe.proben_nr
        if aufgabe.prüfvarianten_id == 7:
            form.einordnungen[i].choices = [("nicht zu erkennen", "nicht zu erkennen"), ("süß", "süß"), ("salzig", "salzig"), ("sauer", "sauer"), ("bitter", "bitter"), ("umami", "umami")]
        if aufgabe.prüfvarianten_id == 8:
            form.einordnungen[i].choices = [("neutral", "neutral"), ("KCL", "KCL"), ("NaCl", "NaCl"), ("NH4Cl", "NH4Cl"), ("CaCl2", "CaCl2"), ("Na2CO3", "Na2CO3")]
    return form

def fill_dreieckstest_form(form, question):
        
        aufgabe = Aufgabenstellungen.query.get(question.aufgabenstellung_id)
        form.aufgabenstellung.label = aufgabe.aufgabenstellung
        form.aufgabenstellung.data = aufgabe.aufgabenstellung

        proben_1 = Probenreihen.query.get(question.probenreihe_id_1).proben_ids
        proben_2 = Probenreihen.query.get(question.probenreihe_id_2).proben_ids

        for i, probe in enumerate(proben_1):
            probe = Proben.query.get(probe)
            if len(form.proben_1) < len(proben_1):
                form.proben_1.append_entry()
            form.proben_1[i].label = probe.proben_nr
            form.proben_1[i].data = probe.proben_nr

        for i, probe in enumerate(proben_2):
            probe = Proben.query.get(probe)
            if len(form.proben_2) < len(proben_2):
                form.proben_2.append_entry()
            form.proben_2[i].label = probe.proben_nr
            form.proben_2[i].data = probe.proben_nr
        form.abweichende_probe_1.choices = [(Proben.query.get(probe).proben_nr, str(Proben.query.get(probe).proben_nr)) for probe in proben_1]
        form.abweichende_probe_2.choices = [(Proben.query.get(probe).proben_nr, str(Proben.query.get(probe).proben_nr)) for probe in proben_2]
        return form

def fill_geruchserkennung_form(form, question):

    aufgabe = Aufgabenstellungen.query.get(question.aufgabenstellung_id)
    form.aufgabenstellung.label = aufgabe.aufgabenstellung
    form.aufgabenstellung.data = aufgabe.aufgabenstellung
    proben = Probenreihen.query.get(question.probenreihe_id).proben_ids
    proben_auswahl = Probenreihen.query.get(question.geruch_mit_auswahl).proben_ids

    for i, probe in enumerate(proben):
        probe = Proben.query.get(probe)
        if len(form.proben) < len(proben):
            form.proben.append_entry()
        if aufgabe.prüfvarianten_id == 6:
            if len(form.mit_auswahl) < len(proben):
                form.mit_auswahl.append_entry()
            form.mit_auswahl[i].choices = [(probe, str(Proben.query.get(probe).probenname)) for probe in proben_auswahl]
        if aufgabe.prüfvarianten_id == 5:
            if len(form.ohne_auswahl) < len(proben):
                form.ohne_auswahl.append_entry()
        form.proben[i].label = probe.proben_nr
        form.proben[i].data = probe.proben_nr
    return form

def fill_hed_beurteilung_form(form, question):
        
        aufgabe = Aufgabenstellungen.query.get(question.aufgabenstellung_id)
        form.aufgabenstellung.label = aufgabe.aufgabenstellung
        form.aufgabenstellung.data = aufgabe.aufgabenstellung
        proben = Probenreihen.query.get(question.probenreihe_id).proben_ids
        for i, probe in enumerate(proben):
            probe = Proben.query.get(probe)
            if len(form.proben) < len(proben):
                form.proben.append_entry()
            if len(form.einordnungen) < len(proben):
                form.einordnungen.append_entry()
                form.bemerkungen.append_entry()
            form.proben[i].label = probe.proben_nr
            form.proben[i].data = probe.proben_nr
        return form

def fill_konz_reihe_form(form, question):

    aufgabe = Aufgabenstellungen.query.get(question.aufgabenstellung_id)
    form.aufgabenstellung.label = aufgabe.aufgabenstellung
    form.aufgabenstellung.data = aufgabe.aufgabenstellung
    proben = Probenreihen.query.get(question.probenreihe_id).proben_ids
    for i, probe in enumerate(proben):
        probe = Proben.query.get(probe)
        if len(form.proben) < len(proben):
            form.proben.append_entry()
        if len(form.konzentration) < len(proben):
            form.konzentration.append_entry()
            form.bemerkungen.append_entry()
        form.proben[i].label = probe.proben_nr
        form.proben[i].data = probe.proben_nr
    return form

def fill_paar_vergleich_form(form, question):

    aufgabe = Aufgabenstellungen.query.get(question.aufgabenstellung_id)
    form.aufgabenstellung.label = aufgabe.aufgabenstellung
    form.aufgabenstellung.data = aufgabe.aufgabenstellung
    proben_1 = Probenreihen.query.get(question.probenreihe_id_1).proben_ids
    proben_2 = Probenreihen.query.get(question.probenreihe_id_2).proben_ids

    for i, probe in enumerate(proben_1):
        probe = Proben.query.get(probe)
        if len(form.proben_1) < len(proben_1):
            form.proben_1.append_entry()
        form.proben_1[i].label = probe.proben_nr
        form.proben_1[i].data = probe.proben_nr
    for i, probe in enumerate(proben_2):
        probe = Proben.query.get(probe)
        if len(form.proben_2) < len(proben_2):
            form.proben_2.append_entry()
        form.proben_2[i].label = probe.proben_nr
        form.proben_2[i].data = probe.proben_nr
    form.ausgeprägte_probe_1.choices = [(Proben.query.get(probe).proben_nr, str(Proben.query.get(probe).proben_nr)) for probe in proben_1]
    form.ausgeprägte_probe_2.choices = [(Proben.query.get(probe).proben_nr, str(Proben.query.get(probe).proben_nr)) for probe in proben_2]
    form.erwartung_probe.choices = [(Proben.query.get(probe).proben_nr, str(Proben.query.get(probe).proben_nr)) for probe in proben_1 + proben_2]
    
    return form

def fill_profilprüfung_form(form, question):

    aufgabe = Aufgabenstellungen.query.get(question.aufgabenstellung_id)
    form.aufgabenstellung.label = aufgabe.aufgabenstellung
    form.aufgabenstellung.data = aufgabe.aufgabenstellung
    probe = Proben.query.get(question.proben_id)
    form.probe.label = probe.proben_nr
    form.probe.data = probe.proben_nr

    for i, kriterium in enumerate(question.kriterien):
        if len(form.kriterien) < len(question.kriterien):
            form.kriterien.append_entry()
        if len(form.skalenwerte) < len(question.kriterien):
            form.skalenwerte.append_entry()
        form.kriterien[i].label = kriterium
        form.kriterien[i].data = kriterium
    return form

def save_to_json(form, filename, question_type, question_index):
    data = {}

    try:
        with open(filename, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        pass

    form_data = {}
    for field_name, field_value in form.data.items():
        if field_name != "csrf_token":
            if isinstance(field_value, list):
                form_data[field_name] = [item for item in field_value]
            else:
                form_data[field_name] = field_value

    data[str(question_type) + '-' + str(question_index)] = form_data

    with open(filename, 'w') as file:
        json.dump(data, file)


app.jinja_env.filters['zip_lists'] = zip_lists

@app.before_request
def check_inactive_user():
    
    if 'username' in session:
        user = Benutzer.query.filter_by(benutzername=session['username']).first()

        last_activity = user.last_activity if user else None
       
        if last_activity is not None:
            inactive_duration = (datetime.now() - last_activity).total_seconds()

            if inactive_duration >= INACTIVITY_THRESHOLD:
                # Log out the inactive user by clearing the session or performing any other necessary logout actions
                user.aktiv = False
                user.training_id = None
                db.session.commit()
                session.clear()
                return redirect('/login')  # Redirect the user to the login page

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    This function handles the login process.

    If the user submits a valid username and password, they are redirected to the professor dashboard.
    If the user submits an invalid username or password, they are returned to the login page with an error message.
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = Benutzer.query.filter_by(benutzername=username).first()

        if user and user.passwort == password:
            session['username'] = user.benutzername
            session['role'] = user.rolle
            if user.rolle == True:
                flash('User ' + user.benutzername + ' wurde als Professor angemeldet', 'success')
                return redirect(url_for('professor_dashboard'))
            else:
                user.last_activity = datetime.now()
                user.aktiv = True
                #user.training_id = None
                db.session.commit()
                flash('User ' + user.benutzername + ' wurde als Student angemeldet', 'success')
                return redirect(url_for('student_waitingroom'))
        else:
            return render_template('login.html', error='Invalid username or password')

    return render_template('login.html')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    
    if 'username' in session:
        # Update user's status to inactive
        user = Benutzer.query.filter_by(benutzername=session['username']).first()
        user.aktiv = False
        db.session.commit()
        session.clear()
        flash('User ' + user.benutzername + ' wurde abgemeldet', 'success')
        
    return redirect(url_for('login')) 

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    This function handles the registration process.

    If the user submits a valid username and password, a new user is created in the database and they are redirected to the login page.
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        professor_password = request.form.get('professor_password')
       

        # Check if the user wants to register as a professor and if the professor password is correct
        is_professor = 'professor' in request.form
        if is_professor and professor_password != setted_professor_password:
           
            return render_template('registery.html', error='Professor Passwort Falsch')

        # Check if the username is already taken
        existing_user = Benutzer.query.filter_by(benutzername=username).first()
        if existing_user:
           
            return render_template('registery.html', error='Benutzername ist leider schon vergeben.')

        # Set the role based on whether the user is registering as a professor or not
        role = is_professor

        # Create a new user object and assign the values
        new_user = Benutzer(benutzername=username, passwort=password, rolle=role, aktiv=False)

        db.session.add(new_user)
        db.session.commit()

        flash(f"Benutzer '{username}' wurde in die Datenbank mit aufgenommen", 'success')
        return redirect(url_for('login'))

    return render_template('registery.html')

@app.route('/manage_users', methods=['GET', 'POST'])
def manage_users():
    if 'username' not in session or session['role'] == False:
        return redirect(url_for('login'))
    users = Benutzer.query.all()
    return render_template('manage_users.html', users=users)

@app.route('/delete_user/<int:id>', methods=['POST'])
def delete_user(id):
    if 'username' not in session or session['role'] == False:
        return redirect(url_for('login'))
    user = Benutzer.query.get(id)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('manage_users'))

@app.route('/student_waitingroom')
def student_waitingroom():
    """
    This function handles the student waiting room page.

    If the user is logged in as a student, they are shown the page with the training they are assigned to.
    If the user is not logged in as a student, they are redirected to the login page.
    """
    if 'username' not in session:
        
        return redirect(url_for('login'))
  
    user = Benutzer.query.filter_by(benutzername=session['username']).first()
    print(user.training_id)
    if user.rolle == False:
        if user.training_id and user.aktiv == True:
            flash('User ' + user.benutzername + ' wartet auf Praktikum.', 'warning')   
            return redirect(url_for('training_page'))
        else:
            #flash('User ' + user.benutzername + ' wartet auf Praktikum.', 'warning')
            return render_template('student_waitingroom.html')
    else:
        return redirect(url_for('professor_dashboard'))
    
@app.route('/Error')
def error():
    """
    This function handles the error page.
    """
    return render_template('Error.html')

@app.route('/professor_dashboard', methods=['GET', 'POST'])
def professor_dashboard():
    """
    This function handles the professor dashboard page.
    If the user is logged in as a professor, they are shown the page with the available trainings.
    If the user is logged in as a student, they are redirected to the student waiting room.
    If the user is not logged in, they are redirected to the login page.
    """
    form = TrainingsViewForm()
   
    question_types_map = {
    "ebp": Ebp,
    "rangordnungstest": Rangordnungstest,
    "auswahltest": Auswahltest,
    "dreieckstest": Dreieckstest,
    "geruchserkennungstest": Geruchserkennung,
    "hed_beurteilung": Hed_beurteilung,
    "konz_reihe": Konz_reihe,
    "paar_vergleich": Paar_vergleich,
    "profilprüfung": Profilprüfung
    }

        
    if request.method == 'POST' and session.get('form_id') == request.form.get('form_id') and form.trainings.choices: #prevent double submitting and empty submit
        
        session.pop('form_id', None)
        
        if request.method == 'POST':
            form_id = request.form.get('form_id')
            action = request.form.get('action')

            index = int(action.split(' ')[1])
        if 'select' in request.form['action']:
            students = Benutzer.query.filter_by(rolle=False).all()
            
            for student in students:
                student.training_id = form.trainings.choices[index][0]
                flash(f'Praktikum {form.trainings.choices[index][1]} für user: {student.benutzername} wurde ausgewählt.', 'success')
                db.session.commit()

        if 'delete' in request.form['action']:

            training = Trainings.query.filter_by(id=form.trainings.choices[index][0]).first()

            for student in Benutzer.query.filter_by(rolle=False).all():
                if student.training_id == training.id:
                    student.training_id = None
            db.session.commit()
            
            for i in range(len(training.fragen_ids)):
                #print(question_types_map[training.fragen_typen[i]].query.filter_by(id=training.fragen_ids[i]).first())
                db.session.delete(question_types_map[training.fragen_typen[i]].query.filter_by(id=training.fragen_ids[i]).first())
                db.session.commit()
                
            db.session.delete(training)
            db.session.commit()
            return redirect(url_for('professor_dashboard'))
        
        if 'modify' in request.form['action']:
            
            return redirect(url_for('modify_training', training_id=form.trainings.choices[index][0]))
        
    
    if 'username' in session:
        username = session['username']
        user = Benutzer.query.filter_by(benutzername=username).first()
        if user.rolle == True:
            form.trainings = Trainings.query.all()
            form_id = str(uuid4()) #Create "form_id"
            session['form_id'] = form_id
             #Add "form_id" to session
            return render_template('professor_dashboard.html', form=form, form_id=form_id)
        elif user.rolle == False:
            return redirect(url_for('student_waitingroom'))
    return redirect(url_for('login'))

@app.route('/modify_training/<int:training_id>', methods=['GET', 'POST'])
def modify_training(training_id):
    # Query the database for the training with the provided id
    if 'username' not in session:
        return render_template('login.html', error="Bitte loggen Sie sich ein, um auf diese Seite zugreifen zu können.")
    if Benutzer.query.filter_by(benutzername=session['username']).first().rolle == False:
        return redirect(url_for('student_waitingroom'))
    
    question_types_models_map = {
        "ebp": Ebp,
        "rangordnungstest": Rangordnungstest,
        "auswahltest": Auswahltest,
        "dreieckstest": Dreieckstest,
        "geruchserkennungstest": Geruchserkennung,
        "hed_beurteilung": Hed_beurteilung,
        "konz_reihe": Konz_reihe,
        "paar_vergleich": Paar_vergleich,
        "profilprüfung": Profilprüfung,
        }

    question_types_forms_map = {
        "ebp": ViewEbp(),
        "rangordnungstest": ViewRangordnungstest(),
        "auswahltest": ViewAuswahltest(),
        "dreieckstest": ViewDreieckstest(),
        "geruchserkennungstest": ViewGeruchserkennung(),
        "hed_beurteilung": ViewHed_beurteilung(),
        "konz_reihe": ViewKonz_reihe(),
        "paar_vergleich": ViewPaar_vergleich(),
        "profilprüfung": ViewProfilprüfung(),
        }

    form_filling_map = {
        "ebp": fill_ebp_form,
        "rangordnungstest": fill_rangordnungstest_form,
        "auswahltest": fill_auswahltest_form,
        "dreieckstest": fill_dreieckstest_form,
        "geruchserkennungstest": fill_geruchserkennung_form,
        "hed_beurteilung": fill_hed_beurteilung_form,
        "konz_reihe": fill_konz_reihe_form,
        "paar_vergleich": fill_paar_vergleich_form,
        "profilprüfung": fill_profilprüfung_form,
        }
    
    session['question_index'] = session.get('question_index', 0)

    training = Trainings.query.filter_by(id=training_id).first()
    
    question_max = len(training.fragen_typen)

    question_type = training.fragen_typen[session['question_index']]

    question = question_types_models_map[question_type].query.get(training.fragen_ids[session['question_index']])

    aufgabe = Aufgabenstellungen.query.get(question.aufgabenstellung_id)

    prüfvariante = aufgabe.prüfvarianten_id

    form = question_types_forms_map[question_type]
    
    form = form_filling_map[question_type](form, question)

    if request.method == 'POST':
        if form.validate_on_submit():

            if 'submit' in request.form:
                if request.form['submit'] == "abgeben":
                    session['question_index'] = 0
                    return redirect(url_for('professor_dashboard'))
                if request.form['submit'] == 'weiter':
                    session['question_index'] = session['question_index'] + 1
                elif request.form['submit'] == 'zurück':
                    session['question_index'] = session['question_index'] - 1
            return redirect(url_for('modify_training', training_id=training_id))
        else:
            print_form_validation_errors(form)
    
    return render_template('training_view_page.html', question=question, question_type=question_type, form=form,
                       question_index=session['question_index'], prüfvariante=prüfvariante, question_max=question_max, training_id=training_id)
 
@app.route('/select_training/<training>')
def select_training(training):
    """
    This function handles the selection of a training by a professor.
    It sets the 'training' attribute of all students to the selected training.
    After updating the database, it redirects to the training page for the selected training.
    """
    #print(training)
    students = Benutzer.query.filter_by(rolle=False,aktiv=True).all()
    #for student in students: 
        #print(student.name, student.aktiv , student.training_id , student.last_activity),

    for student in students:
        student.training = training
        db.session.commit()
    return redirect(url_for('training_progress', students=students))  
                            
@app.route('/professor_dashboard/create_training', methods=['GET', 'POST'])
def create_training():
    """
    This function adds the ability for the professor to create trainings.
    A training can consist of multiple question_types.
    When a training is created all the data is saved to the database.
    """

    #TODO: Die anderen fragentypen hinzufügen

    form = CreateTrainingForm()
    question_types_map = {
    "ebp": form.ebp_questions,
    "rangordnungstest": form.rangordnungstest_questions,
    "auswahltest": form.auswahltest_questions,
    "dreieckstest": form.dreieckstest_questions,
    "geruchserkennung": form.geruchserkennung_questions,
    "hed_beurteilung": form.hed_beurteilung_questions,
    "konz_reihe": form.konz_reihe_questions,
    "paar_vergleich": form.paar_vergleich_questions,
    "profilprüfung": form.profilprüfung_questions,
}

    if form.validate_on_submit():
        
        if 'add_question' in request.form:
            question_type = form.question_types.data
            if question_type in question_types_map:
                question_types_map[question_type].append_entry()

        for question_type in question_types_map.keys():
            if 'delete_{}_question'.format(question_type) in request.form:
                index_to_remove = int(request.form['delete_{}_question'.format(question_type)])
                question_types_map[question_type].entries.pop(index_to_remove)
        
        if 'criteria' in request.form:
            actions = request.form['kriteria'].split(' ',2)
            operation = actions[0]
            index = int(actions[1])
            
            if operation == 'add':
                form.profilprüfung_questions[index].criteria.append_entry()    
            elif operation == 'remove':
                form.profilprüfung_questions[index].criteria.entries.pop()
                
        if 'submit' in request.form:
            
            
            fragen_ids = []
            fragen_typen = []

            for question_form in form.ebp_questions:
                proben_id = question_form.proben_id.data
                aufgabenstellung_id = question_form.aufgabenstellung_id.data
                test = Ebp(proben_id=proben_id, aufgabenstellung_id=aufgabenstellung_id)
                
                db.session.add(test)
                db.session.commit()

                fragen_ids.append(test.id)
                fragen_typen.append("ebp")

            for question_form in form.rangordnungstest_questions:
                probenreihe_id = question_form.probenreihe_id.data
                aufgabenstellung_id = question_form.aufgabenstellung_id.data

                test = Rangordnungstest(aufgabenstellung_id=aufgabenstellung_id, probenreihe_id=probenreihe_id)
                db.session.add(test)
                db.session.commit()

                fragen_ids.append(test.id)
                fragen_typen.append("rangordnungstest")
                
            for question_form in form.auswahltest_questions:
                probenreihe_id = question_form.probenreihe_id.data
                aufgabenstellung_id = question_form.aufgabenstellung_id.data

                test = Auswahltest(aufgabenstellung_id=aufgabenstellung_id, probenreihe_id=probenreihe_id)
                db.session.add(test)
                db.session.commit()

                fragen_ids.append(test.id)
                fragen_typen.append("auswahltest")

            for question_form in form.dreieckstest_questions:
                probenreihe_id_1 = question_form.probenreihe_id_1.data
                probenreihe_id_2 = question_form.probenreihe_id_2.data
                aufgabenstellung_id = question_form.aufgabenstellung_id.data

                test = Dreieckstest(aufgabenstellung_id=aufgabenstellung_id, probenreihe_id_1=probenreihe_id_1, probenreihe_id_2=probenreihe_id_2)
                db.session.add(test)
                db.session.commit()

                fragen_ids.append(test.id)
                fragen_typen.append("dreieckstest") 
                
            for question_form in form.geruchserkennung_questions:
                probenreihe_id = question_form.probenreihe_id.data
                aufgabenstellung_id = question_form.aufgabenstellung_id.data
                geruchsauswahl = question_form.geruchsauswahl.data

                test = Geruchserkennung(aufgabenstellung_id=aufgabenstellung_id, probenreihe_id=probenreihe_id, geruch_mit_auswahl=geruchsauswahl)
                db.session.add(test)
                db.session.commit()

                fragen_ids.append(test.id)
                fragen_typen.append("geruchserkennungstest")
            
            for question_form in form.hed_beurteilung_questions:
                probenreihe_id = question_form.probenreihe_id.data
                aufgabenstellung_id = question_form.aufgabenstellung_id.data

                test = Hed_beurteilung(aufgabenstellung_id=aufgabenstellung_id, probenreihe_id=probenreihe_id)
                db.session.add(test)
                db.session.commit()

                fragen_ids.append(test.id)
                fragen_typen.append("hed_beurteilung")
                
            for question_form in form.konz_reihe_questions:
                probenreihe_id = question_form.probenreihe_id.data
                aufgabenstellung_id = question_form.aufgabenstellung_id.data

                test = Konz_reihe(aufgabenstellung_id=aufgabenstellung_id, probenreihe_id=probenreihe_id)
                db.session.add(test)
                db.session.commit()

                fragen_ids.append(test.id)
                fragen_typen.append("konz_reihe")
                
            for question_form in form.paar_vergleich_questions:
                probenreihe_id_1 = question_form.probenreihe_id_1.data
                probenreihe_id_2 = question_form.probenreihe_id_2.data
                aufgabenstellung_id = question_form.aufgabenstellung_id.data

                test = Paar_vergleich(aufgabenstellung_id=aufgabenstellung_id, probenreihe_id_1=probenreihe_id_1, probenreihe_id_2=probenreihe_id_2)
                db.session.add(test)
                db.session.commit()

                fragen_ids.append(test.id)
                fragen_typen.append("paar_vergleich")
            
            for question_form in form.profilprüfung_questions:
                proben_id = question_form.proben_id.data
                aufgabenstellung_id = question_form.aufgabenstellung_id.data
                kriterien = question_form.kriterien.data

                test = Profilprüfung(aufgabenstellung_id=aufgabenstellung_id, proben_id=proben_id, kriterien=kriterien)
                db.session.add(test)
                db.session.commit()

                fragen_ids.append(test.id)
                fragen_typen.append("profilprüfung")
            
            training = Trainings(
                name=form.name.data,
                fragen_ids = fragen_ids,
                fragen_typen = fragen_typen
            )
            db.session.add(training)
            db.session.commit()

            return redirect(url_for('professor_dashboard'))
    
    if request.method == "POST" and request.form.get('kriteria'):
        action = request.form.get('kriteria').split(' ',2)
        if action[0] == 'add':
            form.profilprüfung_questions[int(action[1])].kriterien.append_entry()
        if action[0] == 'remove':
            form.profilprüfung_questions[int(action[1])].kriterien = form.profilprüfung_questions[int(action[1])].kriterien[0:len(form.profilprüfung_questions[int(action[1])].kriterien) -1]
    #print("Form validated unsuccessful")
    return render_template('create_training.html', form=form)

@app.route('/delete_task/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    if 'username' not in session:
        return render_template('login.html', error="Bitte loggen Sie sich ein, um auf diese Seite zugreifen zu können.")
    
    task = Aufgabenstellungen.query.get(task_id)
    
    if task is None:
        # Handle case when the task with the specified task_id is not found
        flash("Task not found.", "error")
    else:
        db.session.delete(task)
        db.session.commit()
        flash("Task deleted successfully.", "success")
    
    return redirect(url_for('manage_aufgabenstellungen'))                           

@app.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    if 'username' not in session:
        return render_template('login.html', error="Bitte loggen Sie sich ein, um auf diese Seite zugreifen zu können.")
    
    task = Aufgabenstellungen.query.get(task_id)
    
    if task is None:
        # Handle case when the task with the specified task_id is not found
        flash("Task not found.", "error")
        return redirect(url_for('manage_aufgabenstellungen'))
    
    if request.method == 'POST':
        aufgabenstellung = request.form.get('aufgabenstellung')
        
        # Perform necessary operations to update the task using 'aufgabenstellung'
        task.aufgabenstellung = aufgabenstellung
        db.session.commit()
        
        # Redirect to the task list page after updating the task
        flash("Task updated successfully.", "success")
        return redirect(url_for('task_list'))
    
    return render_template('edit_task.html', task=task)

@app.route('/create_task/', methods=['GET', 'POST'])
def create_task():
    if 'username' not in session:
        return render_template('login.html', error="Bitte loggen Sie sich ein, um auf diese Seite zugreifen zu können.")

    aufgabentypen = db.session.query(Aufgabenstellungen.aufgabentyp).distinct().all()
    prüfvarianten = Prüfvarianten.query.all()

    if request.method == 'POST':
        aufgabenstellung = request.form.get('aufgabenstellung')
        aufgabentyp = request.form.get('aufgabentyp')
        prüfvariante = request.form.get('prüfvariante')
        
        # Perform necessary operations to create a new task using 'aufgabenstellung', 'aufgabentyp', and 'prüfvariante'
        prüfvar = Prüfvarianten(prüfname=prüfvariante) 
        db.session.add(prüfvar)
        db.session.commit()
        prüfvar = Prüfvarianten.query.order_by(Prüfvarianten.id.desc()).first()
        task = Aufgabenstellungen(aufgabenstellung=aufgabenstellung, aufgabentyp=aufgabentyp, prüfvarianten_id=prüfvar.id)
       
        db.session.add(task)
        db.session.commit()

        # Redirect to the task list page after creating the task
        flash("Task created successfully.", "success")
        return redirect(url_for('manage_aufgabenstellungen'))

    return render_template('create_task.html', aufgabentypen=aufgabentypen, prüfvarianten=prüfvarianten)

@app.route('/professor_dashboard/manage_aufgabenstellungen/', methods=['GET', 'POST'])
def manage_aufgabenstellungen():
    if 'username' not in session:
        return render_template('login.html', error="Bitte loggen Sie sich ein, um auf diese Seite zugreifen zu können.")

    tasks = Aufgabenstellungen.query.all()
    prüfvarianten_list = Prüfvarianten.query.all()
    prüfnamen = [prüf.prüfname for prüf in prüfvarianten_list]

    return render_template('manage_aufgabenstellungen.html', tasks=tasks, prüfnamen=prüfnamen)

@app.route('/training_page/', methods=['GET', 'POST'])
def training_page():

    if 'username' not in session:
        return render_template('login.html', error="Bitte loggen Sie sich ein, um auf diese Seite zugreifen zu können.")
    user = Benutzer.query.filter_by(benutzername=session['username']).first()
    if not user.training_id:
        return redirect(url_for('student_waitingroom'))
    
    question_types_models_map = {
        "ebp": Ebp,
        "rangordnungstest": Rangordnungstest,
        "auswahltest": Auswahltest,
        "dreieckstest": Dreieckstest,
        "geruchserkennungstest": Geruchserkennung,
        "hed_beurteilung": Hed_beurteilung,
        "konz_reihe": Konz_reihe,
        "paar_vergleich": Paar_vergleich,
        "profilprüfung": Profilprüfung,
        }

    question_types_forms_map = {
        "ebp": ViewEbp(),
        "rangordnungstest": ViewRangordnungstest(),
        "auswahltest": ViewAuswahltest(),
        "dreieckstest": ViewDreieckstest(),
        "geruchserkennungstest": ViewGeruchserkennung(),
        "hed_beurteilung": ViewHed_beurteilung(),
        "konz_reihe": ViewKonz_reihe(),
        "paar_vergleich": ViewPaar_vergleich(),
        "profilprüfung": ViewProfilprüfung(),
        }

    form_filling_map = {
        "ebp": fill_ebp_form,
        "rangordnungstest": fill_rangordnungstest_form,
        "auswahltest": fill_auswahltest_form,
        "dreieckstest": fill_dreieckstest_form,
        "geruchserkennungstest": fill_geruchserkennung_form,
        "hed_beurteilung": fill_hed_beurteilung_form,
        "konz_reihe": fill_konz_reihe_form,
        "paar_vergleich": fill_paar_vergleich_form,
        "profilprüfung": fill_profilprüfung_form,
        }


    env = Environment()
    env.globals['enumerate'] = enumerate

    training = Trainings.query.filter_by(id=Benutzer.query.filter_by(benutzername=session['username']).first().training_id).first()
    question_max = len(training.fragen_typen)
    
    session['question_index'] = session.get('question_index', 0)
    print('\n\n\n')
    print("session['question_index']",session['question_index'])
    print('\n\n\n')

    if session['question_index'] >= question_max:
        session['question_index'] = 0
        return redirect(url_for('complete_training'))
    question_type = training.fragen_typen[session['question_index']]

    question = question_types_models_map[question_type].query.get(training.fragen_ids[session['question_index']])

    aufgabe = Aufgabenstellungen.query.get(question.aufgabenstellung_id)

    prüfvariante = aufgabe.prüfvarianten_id

    form = question_types_forms_map[question_type]
    
    form = form_filling_map[question_type](form, question)
    """
    print("question",question)
    print("question_type",question_type)
    print("aufgabenstellung",aufgabenstellung)
    print("additional_data",additional_data)
    print("form",form)
    print("form",form.data)
    print("validate_on_submit",form.validate_on_submit())
    """
    if request.method == 'POST':
        if form.validate_on_submit():
            #process_form_submission(question_type, form.data)
        
            #print("\n\n\n")
            #print(request.form)
            #print("\n\n\n")

            if 'submit' in request.form:
                path_to_json = './saved_submits/' + session['username'] + '-' + str(training.id) + '.json'
                if request.form['submit'] == "abgeben":
                    save_to_json(form, path_to_json, question_type, question_index=session['question_index'])
                    session['question_index'] = session['question_index'] + 1
                    return redirect(url_for('complete_training'))
                if request.form['submit'] == 'weiter':
                    save_to_json(form, path_to_json, question_type, question_index=session['question_index'])
                    session['question_index'] = session['question_index'] + 1
                elif request.form['submit'] == 'zurück':
                    save_to_json(form, path_to_json, question_type, question_index=session['question_index'])
                    session['question_index'] = session['question_index'] - 1
            return redirect(url_for('training_page'))
            
        else:
            print_form_validation_errors(form)
    

    return render_template('training_page.html', question=question, question_type=question_type, form=form,
                       question_index=session['question_index'], question_max=question_max, enumerate=enumerate,
                       prüfvariante=prüfvariante)

@app.route('/complete_training/', methods=['GET', 'POST'])
def complete_training():

    if 'username' not in session:
        return render_template('login.html', error="Bitte loggen Sie sich ein, um auf diese Seite zugreifen zu können.")
    session['question_index'] = 0
    training_id = Benutzer.query.filter_by(benutzername=session['username']).first().training_id
    path_to_json = './saved_submits/' + session['username'] + '-' + str(training_id) + '.json'
    data = get_form_data_from_json(path_to_json)
    if not data:
        return redirect(url_for('training_page'))
    return render_template('complete_training.html', data=data)

@app.route('/professor_dashboard/training_progress')
def training_progress():

    if 'username' not in session:
        return render_template('login.html', error="Bitte loggen Sie sich ein, um auf diese Seite zugreifen zu können.")
    
    training_id = Benutzer.query.filter_by(rolle=False).first().training_id

    student_names = [student.benutzername for student in Benutzer.query.filter_by(rolle=False).all()]

    training_data = []
    path_to_json = './saved_submits/'
    for student in student_names:
        training_data.append(get_form_data_from_json(path_to_json + student + '-' + str(training_id) + '.json'))

    return render_template('training_progress.html', usernames=student_names, training_data=training_data, training_name=Trainings.query.get(training_id).name)

@app.route('/professor_dashboard/training_progress/save_submits', methods=['POST'])
def save_submits():
    if 'username' not in session:
        return render_template('login.html', error="Bitte loggen Sie sich ein, um auf diese Seite zugreifen zu können.")
    
    training_id = Benutzer.query.filter_by(rolle=False).first().training_id

    student_names = [student.benutzername for student in Benutzer.query.filter_by(rolle=False).all()]

    training_data = []
    path_to_json = './saved_submits/'
    for student in student_names:
        training_data.append(get_form_data_from_json(path_to_json + student + '-' + str(training_id) + '.json'))

    path_to_pdf = './saved_pdfs/'
    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
    options = {
        'no-stop-slow-scripts': True,
    }
    html = render_template('training_progress_content.html', usernames=student_names, training_data=training_data, training_name=Trainings.query.get(training_id).name)
    if not os.path.exists(path_to_pdf):
        os.makedirs(path_to_pdf)
    if os.path.isfile(path_to_pdf + 'training_progress-' + str(training_id) + '.pdf'):
        os.remove(path_to_pdf + 'training_progress-' + str(training_id) + '.pdf')
    pdfkit.from_string(html, path_to_pdf + 'training_progress-' + str(training_id) + '.pdf', configuration=config, options=options)
    return send_file("..\\saved_pdfs\\" + 'training_progress-' + str(training_id) + '.pdf', as_attachment=True)

@app.route('/')
def dashboard():
    """
    This function handles the main dashboard page.
    """
    
    if 'username' not in session:
        return render_template('login.html')
        
    return render_template('dashboard.html')

@app.route('/view_samples/')
def view_samples():
    # Logic to retrieve sample data
    samples = Proben.query.all()
    sampleChain = Probenreihen.query.all()
    return render_template('view_samples.html', samples=samples , sampleChain=sampleChain)

@app.route('/edit_sample/<sample_id>', methods=['GET', 'POST'])
def edit_sample(sample_id):
    sample = Proben.query.get(sample_id)

    if request.method == 'POST':
        form_data = request.form
        
        update_sample_in_database(sample_id, form_data)
        return redirect(url_for('view_samples'))

    return render_template('edit_sample.html', sample=sample)

@app.route('/create_sample', methods=['GET', 'POST'])
def create_sample():
    if request.method == 'POST':
        form_data = request.form
        # Logic to create a new sample based on form data
        create_sample_in_database(form_data)
        return redirect(url_for('view_samples'))

    return render_template('create_sample.html')

@app.route('/create_sample_chain', methods=['GET', 'POST'])
def create_sample_chain():
    if request.method == 'POST':
        name = request.form['name']
        selected_proben_ids = request.form.getlist('proben_ids[]')  # Use getlist to retrieve all selected IDs

        # Process the selected proben IDs
        proben_ids = []
        for proben_id in selected_proben_ids:
            if proben_id:
                proben = Proben.query.get(proben_id)
                if proben:
                    proben_ids.append(proben_id)

        # Create a new Probenreihen instance
        sample_chain = Probenreihen(name=name, proben_ids=proben_ids)
        
        # Add the new sample chain to the database
        db.session.add(sample_chain)
        db.session.commit()

        flash('Sample chain created successfully!')
        return redirect(url_for('view_samples'))
    
    samples = Proben.query.all()
    return render_template('create_sample_chain.html', samples=samples)

@app.route('/delete_sample/<sample_id>', methods=['DELETE'])
def delete_sample(sample_id):
    sample = Proben.query.get(sample_id)
    if sample:
        # TODO: Delete the sample from the database
        db.session.delete(sample)
        db.session.commit()
        return jsonify({'message': 'Sample deleted successfully'})
    else:
        return jsonify({'message': 'Sample not found'})

@app.route('/delete_sample_chain/<sample_chain_id>', methods=['DELETE'])
def delete_sample_chain(sample_chain_id):
    sample_chain = Probenreihen.query.get(sample_chain_id)
    if sample_chain:
        db.session.delete(sample_chain)
        db.session.commit()
        return jsonify({'message': 'Sample chain deleted successfully'})
    else:
        return jsonify({'message': 'Sample chain not found'})


if __name__ == '__main__':
    app.run(debug=True)

"""
#############################################
#           Ausgelagerte Funktionen         #
#############################################



def calculate_training_progress(user):
    completed_tasks = 0
    total_tasks = 0

    training = Trainings.query.get(user.training_id)

    if training:
        total_tasks = len(training.fragen_ids)

        for fragen_id in training.fragen_ids:
            if check_task_completion(user, fragen_id):
                completed_tasks += 1

    if total_tasks > 0:
        progress = (completed_tasks / total_tasks) * 100
    else:
        progress = 0

    return progress

def check_task_completion(user, fragen_id):
    task_type = Aufgabenstellungen.query.get(fragen_id).aufgabentyp

    return True

    # Add conditions for other task types as needed

def setup_df(form_data):
    # Get the list of attributes from the form_data keys
    attributes = list(form_data.keys())

    # Filter out any non-attribute keys (e.g., 'csrf_token')
    attributes = [attr for attr in attributes if not attr.startswith('csrf_')]
    #print("attributes: ", attributes)
    #print()

    # The number of probes can be calculated as the number of entries for any attribute
    num_probes = len(form_data.get(attributes[0]))

    # Create a list to store individual row dictionaries
    rows = []

    # Iterate over each probe
    for i in range(num_probes):
        # Initialize an empty dictionary for this row
        row = {}

        # For each attribute, get the corresponding value from the form_data and add it to the dictionary
        for attribute in attributes:
            # Get the values for the current attribute at index i
            values = form_data.getlist(attribute)
            value = values[i]

            # If the value is 'y', replace it with True, otherwise replace it with False
            value = True if value == 'y' else False

            # Add the attribute and its value to the dictionary
            row[attribute] = value

        # Append the row dictionary to the list
        rows.append(row)

    # Create the DataFrame by passing the list of dictionaries and specifying the index
    df = pd.DataFrame(rows, index=range(num_probes))

    return df

def process_form_submission(question_type, form_data):
    

    #TODO: instanziate df without values if he is not existing
    #TODO:  add the columus as they are not existing in df

    
    df = pd.DataFrame()   
    def paar_vergleich():
        #print("paar_vergleich")
        #print("request.form_data",request.form )
        print()
        #print("form_data",form_data)
        #TODO: update df with values from form or request form data
        #      over write existing values or add new values

    def auswahltest():
        nonlocal df
    # Call the setup_df function to create the DataFrame
        return
        df = setup_df(form_data)
        print("request.form_data",request.form )
        print()
        for i in range(len(form_data['probe_name'])):
            probe_nr_key = f'probe_nr-{i}'
            probe_name_key = f'probe_name-{i}'
            taste_salzig_key = f'taste_salzig-{i}'
            taste_süß_key = f'taste_süß-{i}'
            taste_sauer_key = f'taste_sauer-{i}'
            taste_bitter_key = f'taste_bitter-{i}'
            taste_nicht_erkennen_key = f'taste_nicht_erkennen-{i}'

            # Retrieve the values from the request form data using the updated keys
            probe_nr = request.form.get(probe_nr_key)
            probe_name = request.form.get(probe_name_key)
            taste_salzig = request.form.get(taste_salzig_key) == 'y'
            taste_süß = request.form.get(taste_süß_key) == 'y'
            taste_sauer = request.form.get(taste_sauer_key) == 'y'
            taste_bitter = request.form.get(taste_bitter_key) == 'y'
            taste_nicht_erkennen = request.form.get(taste_nicht_erkennen_key) == 'y'

            # Update the corresponding row in the DataFrame with the new values
            df.loc[i, 'probe_nr'] = probe_nr
            df.loc[i, 'probe_name'] = probe_name
            df.loc[i, 'taste_salzig'] = taste_salzig
            df.loc[i, 'taste_süß'] = taste_süß
            df.loc[i, 'taste_sauer'] = taste_sauer
            df.loc[i, 'taste_bitter'] = taste_bitter
            df.loc[i, 'taste_nicht_erkennen'] = taste_nicht_erkennen

        print(df)



    def dreieckstest():
        print("dreieckstest")
        print("request.form_data", request.form)
        print()
        print("form_data", form_data)

        #df = setup_df(form_data)
        return
        for i in range(len(form_data['beschreibung_1'])):
            abweichende_probe_key = f'abweichende_probe_-[{form_data["probenreihen_id"][i]}]'
            beschreibung_key = f'beschreibung_-[{form_data["probenreihen_id"][i]}]'

            # Retrieve the values from the request form data using the updated keys
            abweichende_probe = request.form.get(abweichende_probe_key)
            beschreibung = request.form.get(beschreibung_key)

            # Add new columns to the DataFrame if they don't exist
            if 'abweichende_probe' not in df.columns:
                df['abweichende_probe'] = None
            if 'beschreibung' not in df.columns:
                df['beschreibung'] = None

            # Update the corresponding rows in the DataFrame with the new values
            df.loc[i, 'abweichende_probe'] = abweichende_probe
            df.loc[i, 'beschreibung'] = beschreibung

        print(df)

    def geruchserkennungtest():
        print("geruchserkennungtest")
        print("request.form_data",request.form )
        print()
        print("form_data",form_data)
        #TODO: update df with values from form or request form data
        #       add the columus as they are not existing in df 
        #       over write existing values
        geruchserkennungen = []
 

    def konz_reihe():
        print("konz_reihe")
        print("request.form_data",request.form )
        print()
        print("form_data",form_data)
        #TODO: update df with values from form or request form data
        #       add the columus as they are not existing in df 
        #       over write existing values
        probenreihen_id = form_data.get("probenreihen_id")
        # Process the form submission for "Konzentrationsreihe"
        print("Konzentrationsreihe: Probenreihe ID:", probenreihen_id)
     

    def ebp():
        
        print("ebp")
        print("request.form_data",request.form )
        print()
        print("form_data",form_data)
        #TODO: update df with values from form or request form data
        #       add the columus as they are not existing in df 
        #       over write existing values
        print("Einfach beschreibende Prüfung: form_data:", form_data)
        
        
    def rangordnungstest():
        print("rangordnungstest")
        print("request.form_data",request.form )
        print()
        print("form_data",form_data)
        #TODO: update df with values from form or request form data
        #       add the columus as they are not existing in df 
        #       over write existing values

        antworten = form_data.get('antworten')
    # Process the form submission for "Rangordnungstest"
        print("Rangordnungstest: Antworten:", antworten)
    

    def profilprüfung():
        print("profilprüfung")
        print("request.form_data",request.form )
        print()
        print("form_data",form_data)
        #TODO: update df with values from form or request form data
        #       add the columus as they are not existing in df 
        #       over write existing values
        kriterien_werte = []
    
    form_type_funcs = {
        "paar_vergleich": paar_vergleich,
        "auswahltest": auswahltest,
        "dreieckstest": dreieckstest,
        "geruchserkennungtest": geruchserkennungtest,
        "konz_reihe": konz_reihe,
        "ebp": ebp,
        "rangordnungstest": rangordnungstest,
        "profilprüfung": profilprüfung
    }

    if question_type in form_type_funcs:
        form_type_funcs[question_type]()
    else:
        print("Invalid question type")

def get_form_instance(question_type, additional_data=None):
    if question_type == 'hed_beurteilung':
        return SubmitHed_beurteilung()
    elif question_type == 'auswahltest':
        
        proben=[probe.probenname for probe in additional_data['probenreihen_id']]
        proben_nr=[probe.proben_nr for probe in additional_data['probenreihen_id']]
        return SubmitAuswahltest(proben, proben_nr)
    
    elif question_type == 'dreieckstest':
        return SubmitDreieckstest()
    elif question_type == 'geruchserkennungtest':
        return SubmitGeruchserkennung()
    elif question_type == 'ebp':
        return SubmitEbpForm()
    elif question_type == 'rangordnungstest':
        return SubmitRangordnungstest()
    elif question_type == 'profilprüfung':
        return SubmitProfilprüfung()
    elif question_type == 'konz_reihe':
        return SubmitKonz_reihe()
    elif question_type == 'paar_vergleich':
        if additional_data and 'probenreihen_id_1' in additional_data and 'probenreihen_id_2' in additional_data:
            return SubmitPaar_vergleich(additional_data['probenreihen_id_1'], additional_data['probenreihen_id_2'])
    else:
        raise ValueError(f"Unknown question_type: {question_type}")

def get_question_instance(question_type, question_id):

    session = db.session
    if question_type == "paar_vergleich":
        return session.get(Paar_vergleich, question_id)
    elif question_type == "auswahltest":
        return session.get(Auswahltest, question_id)
    elif question_type == "dreieckstest":
        return session.get(Dreieckstest, question_id)
    elif question_type == "geruchserkennungtest":
        return session.get(Geruchserkennung, question_id)
    elif question_type == "hed_beurteilung":
        return session.get(Hed_beurteilung, question_id)
    elif question_type == "konz_reihe":
        return session.get(Konz_reihe, question_id)
    elif question_type == "ebp":
        return session.get(Ebp, question_id)
    elif question_type == "rangordnungstest":
        return session.get(Rangordnungstest, question_id)
    elif question_type == "profilprüfung":
        return session.get(Profilprüfung, question_id)
    else:
        return None

def get_additional_data(question_type, question):
    additional_data = {}
    
    if question_type == "auswahltest":
        probenreihen_id = Probenreihen.query.get(question.probenreihe_id)
        additional_data["probenreihen_id"] = [Proben.query.get(probe) for probe in probenreihen_id.proben_ids]        
        
    elif question_type == "dreieckstest":
        probenreihen_id_1 = Probenreihen.query.get(question.probenreihe_id_1)
        probenreihen_id_2 = Probenreihen.query.get(question.probenreihe_id_2)
        proben_numbers_1 = [probe.proben_nr for probe in [Proben.query.get(probe) for probe in probenreihen_id_1.proben_ids]]
        proben_numbers_2 = [probe.proben_nr for probe in [Proben.query.get(probe) for probe in probenreihen_id_2.proben_ids]]
        additional_data["probenreihen_id_1"] = proben_numbers_1
        additional_data["probenreihen_id_2"] = proben_numbers_2

    elif question_type == "geruchserkennungtest":
        probenreihen_id = Probenreihen.query.get(question.probenreihe_id)
        additional_data["probenreihen_id"] = [Proben.query.get(probe) for probe in probenreihen_id.proben_ids] 

    elif question_type == "hed_beurteilung":
        probenreihen_id = Probenreihen.query.get(question.probenreihe_id)
        additional_data["probenreihen_ids"] = [Proben.query.get(probe) for probe in probenreihen_id.proben_ids] 

    elif question_type == "konz_reihe":
        probenreihen_id = Probenreihen.query.get(question.probenreihe_id)
        additional_data["stammlösung"] = request.args.get('stammlösung', '1')
        additional_data["probenreihen_id"] = [probe.proben_nr for probe in [Proben.query.get(probe) for probe in probenreihen_id.proben_ids]]

    elif question_type == "ebp":
        proben_id = Proben.query.get(question.proben_id)
        additional_data["proben_id"] = proben_id

    elif question_type == "rangordnungstest": 
        probenreihen_id = Probenreihen.query.get(question.probenreihe_id)
        additional_data["probenreihen_id"] = [Proben.query.get(probe) for probe in probenreihen_id.proben_ids]

    elif question_type == "profilprüfung":
        proben_id = Proben.query.get(question.proben_id)
        additional_data["proben_id"] = proben_id
        additional_data["kriterien"] = question.kriterien

    elif question_type == "paar_vergleich":
        
        probenreihen_id_1 = Probenreihen.query.get(question.probenreihe_id_1)
        probenreihen_id_2 = Probenreihen.query.get(question.probenreihe_id_2)
        additional_data["probenreihen_id_1"] =   [Proben.query .get(probe) for probe in probenreihen_id_1.proben_ids]
        additional_data["probenreihen_id_2"] =  [Proben.query.get(probe) for probe in probenreihen_id_2.proben_ids]

    return additional_data
"""