# Projektstudium-Sensorik
 

This project is a Flask web application for managing training programs and conducting sensory tests in the field of food and beverages.

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Database Models](#database-models)
- [Contributing](#contributing)
  

## Introduction

The project aims to provide a user-friendly interface for creating and managing various types of sensory tests, such as profile evaluations, ranking tests, selection tests, and more. It allows administrators to define training programs and customize the test parameters based on specific requirements.

## Features

- Create and manage training programs
- Define different types of sensory tests, including:
  - Einfach beschreibende Prüfung (EBP)
  - Rangordnungstest
  - Auswahltest
  - Dreieckstest
  - Geruchserkennung
  - Hedonische Beurteilung
  - Konzentrationsreihe
  - Paarweise Vergleichstest
  - Profilprüfung
- Customize test parameters for each test type
- Assign tests to users and track their progress
- Collect and analyze test results
- User authentication and role-based access control

## Installation

1. Clone the repository:
git clone https://github.com/yourusername/project.git

2. Change into the project directory:
cd project

3. Create a virtual environment:
python3 -m venv venv

4. Activate the virtual environment:
- For Windows:
venv\Scripts\activate

- For Unix or Linux:
source venv/bin/activate

5. Install the dependencies:
pip install -r requirements.txt

6. Set up the database:
- Modify the database configuration in `config.py` according to your environment.
- Run the following commands to create and populate the database:

python manage.py db init
python manage.py db migrate
python manage.py db upgrade

7. Start the application:

python manage.py runserver

8. Open your web browser and visit `http://localhost:5000` to access the application.

## Usage
1. Register a new user account or log in with an existing account.

2. As an administrator, create training programs and define test parameters for each test type.

3. Assign tests to users and track their progress.

4. Users can access their assigned tests, complete them, and submit the results.

5. Administrators can view and analyze the test results.

## Database Models

The application uses SQLAlchemy and includes the following database models:

- Aufgabenstellungen
- Prüfvarianten
- Trainings
- Proben
- Probenreihen
- Benutzer
- Konz_reihe
- Profilprüfung
- Hed_beurteilung
- Auswahltest
- Geruchserkennung
- Paar_vergleich
- Ebp
- Rangordnungstest
- Dreieckstest

For detailed information about each model, refer to the source code in the `models.py` file.

## Contributing

Contributions are welcome! If you have any suggestions or improvements for the project, feel free to submit a pull request.

