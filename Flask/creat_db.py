import psycopg2

# Connect to the PostgreSQL server
conn = psycopg2.connect(
    host="localhost",
    user="postgres",
    password="123",
    dbname="praktikum_db",
    port="5432",
)

# Open a cursor to perform database operations
cur = conn.cursor()

# Create the necessary tables

# TODO: Complete tables in the database

cur.execute('''

-- Create the Fragen table
CREATE TABLE fragen (
    id SERIAL PRIMARY KEY,
    fragen_typ VARCHAR(255) NOT NULL,
    fragen_id INTEGER NOT NULL
);

-- Create the prüfvarianten table
CREATE TABLE prüfvarianten (
    id SERIAL PRIMARY KEY,
    prüfname TEXT
);

-- Create the aufgabenstellungen table
CREATE TABLE aufgabenstellungen (
    id SERIAL PRIMARY KEY,
    aufgabenstellung TEXT NOT NULL,
    aufgabentyp TEXT NOT NULL,
    prüfvarianten_id INTEGER,
    FOREIGN KEY (prüfvarianten_id) REFERENCES prüfvarianten (id) ON DELETE CASCADE
);

-- Create the Trainings table
CREATE TABLE trainings (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    fragen_id INTEGER,
    FOREIGN KEY (fragen_id) REFERENCES fragen (id) ON DELETE CASCADE
);

-- Create the Proben table
CREATE TABLE proben (
    id SERIAL PRIMARY KEY,
    proben_nr INTEGER UNIQUE NOT NULL,
    probenname VARCHAR(255) NOT NULL,
    farbe TEXT,
    farbintensität INTEGER,
    geruch TEXT,
    geschmack TEXT,
    textur TEXT,
    konsistenz TEXT
);

-- Create the probenreihen table
CREATE TABLE probenreihen (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    proben_id INTEGER,
    FOREIGN KEY (proben_id) REFERENCES proben (id) ON DELETE CASCADE
);

-- Create the Benutzer table
CREATE TABLE benutzer (
    id SERIAL PRIMARY KEY,
    benutzername TEXT NOT NULL,
    passwort TEXT NOT NULL,
    rolle BOOLEAN NOT NULL,
    training_id INTEGER,
    FOREIGN KEY (training_id) REFERENCES trainings (id) ON DELETE CASCADE
);

-- Create the dreieckstest table
CREATE TABLE dreieckstest (
    id SERIAL PRIMARY KEY,
    aufgabenstellung_id INTEGER,
    probenreihe_id INTEGER NOT NULL,
    proben_auswahl INTEGER[],
    beschreibung TEXT,
    FOREIGN KEY (probenreihe_id) REFERENCES probenreihen (id) ON DELETE CASCADE,
    FOREIGN KEY (aufgabenstellung_id) REFERENCES aufgabenstellungen (id) ON DELETE CASCADE
);

-- Create the konz_reihe table
CREATE TABLE konz_reihe (
    id SERIAL PRIMARY KEY,
    aufgabenstellung_id INTEGER,
    probenreihe_id INTEGER NOT NULL,
    antworten TEXT[],
    FOREIGN KEY (probenreihe_id) REFERENCES probenreihen (id) ON DELETE CASCADE,
    FOREIGN KEY (aufgabenstellung_id) REFERENCES aufgabenstellungen (id) ON DELETE CASCADE
);

-- Create the profilprüfung table
CREATE TABLE profilprüfung (
    id SERIAL PRIMARY KEY,
    aufgabenstellung_id INTEGER,
    proben_id INTEGER NOT NULL,
    kriterien TEXT[],
    bewertungen TEXT[],
    FOREIGN KEY (proben_id) REFERENCES proben (id) ON DELETE CASCADE,
    FOREIGN KEY (aufgabenstellung_id) REFERENCES aufgabenstellungen (id) ON DELETE CASCADE
);

-- Create the paar_vergleich table
CREATE TABLE paar_vergleich (
    id SERIAL PRIMARY KEY,
    aufgabenstellung_id INTEGER,
    proben_id_1 INTEGER NOT NULL,
    proben_id_2 INTEGER NOT NULL,
    beschreibung TEXT,
    FOREIGN KEY (proben_id_1) REFERENCES proben (id) ON DELETE CASCADE,
    FOREIGN KEY (proben_id_2) REFERENCES proben (id) ON DELETE CASCADE,
    FOREIGN KEY (aufgabenstellung_id) REFERENCES aufgabenstellungen (id) ON DELETE CASCADE
);
''')

conn.commit()

# Insertion of data into benutzer table

cur.execute('''
INSERT INTO public.benutzer(
    id, benutzername, passwort, rolle, training_id)
    VALUES 
    (1, 'Test', '123', TRUE, NULL),
    (2, 'Student1', '123', False, NULL),
    (3, 'Student2', '123', False, NULL),
    (4, 'Student3', '123', False, NULL);
''')

conn.commit()

# TODO: Insertion of data into other tables

# Close communication with the database
cur.close()
conn.close()

