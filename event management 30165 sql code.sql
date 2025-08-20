-- SQL Code to Create Database Schema for Event Management System

CREATE TABLE user_profile (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    organization VARCHAR(255)
);

CREATE TABLE events (
    event_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES user_profile(user_id),
    event_name VARCHAR(255) NOT NULL,
    event_date DATE NOT NULL,
    event_time TIME NOT NULL,
    location VARCHAR(255),
    description TEXT
);

CREATE TABLE tickets (
    ticket_id SERIAL PRIMARY KEY,
    event_id INT REFERENCES events(event_id),
    ticket_type VARCHAR(100),
    price DECIMAL(10,2),
    quantity_available INT
);

CREATE TABLE attendees (
    attendee_id SERIAL PRIMARY KEY,
    event_id INT REFERENCES events(event_id),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    ticket_id INT REFERENCES tickets(ticket_id)
);