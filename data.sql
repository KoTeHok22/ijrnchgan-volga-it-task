CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL,
    First_Name TEXT NOT NULL, 
    Last_Name TEXT NOT NULL, 
    Middle_Name TEXT NOT NULL,
    avatar TEXT NOT NULL, 
    email TEXT NOT NULL, 
    hospital_id INTEGER, 
    doctor_id INTEGER, 
    pass_hash TEXT NOT NULL,
    User_Role TEXT NOT NULL,
    deleted BOOLEAN NOT NULL DEFAULT FALSE,
    reg_time TEXT NOT NULL
);

CREATE TABLE hospitals (
    id SERIAL PRIMARY KEY,
    hospital_name TEXT NOT NULL,
    cabinets JSONB NOT NULL,
    phone JSONB NOT NULL,
    email JSONB NOT NULL,
    hospital_address TEXT NOT NULL,
    deleted BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    token TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS timetable (
    id SERIAL PRIMARY KEY,
    hospital_id INTEGER REFERENCES hospitals(id),
    doctor_id INTEGER REFERENCES users(id),
    from_dt TIMESTAMP WITH TIME ZONE NOT NULL,
    to_dt TIMESTAMP WITH TIME ZONE NOT NULL,
    room TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS appointments (
    id SERIAL PRIMARY KEY,
    timetable_id INTEGER REFERENCES timetable(id),
    patient_id INTEGER REFERENCES users(id),
    appointment_time TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE TABLE IF NOT EXISTS history (
    id SERIAL PRIMARY KEY,
    date TIMESTAMP WITH TIME ZONE NOT NULL,
    pacientId INTEGER REFERENCES users(id),
    hospitalId INTEGER REFERENCES hospitals(id),
    doctorId INTEGER REFERENCES users(id),
    room TEXT,
    data TEXT
);








CREATE TABLE IF NOT EXISTS recommendations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    title TEXT NOT NULL,
    text TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS actual (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    icon TEXT,
    link TEXT,
    color TEXT,
    border TEXT
);