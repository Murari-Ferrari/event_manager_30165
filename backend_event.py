# File: backend_event.py

import psycopg2
from psycopg2 import sql
import pandas as pd
import streamlit as st
from datetime import datetime

# --- Configuration (Update with your PostgreSQL credentials) ---
DB_HOST = "localhost"
DB_NAME = "event_management_db"
DB_USER = "postgres"
DB_PASSWORD = "99Mur@ri99"

def get_db_connection():
    """Establishes and returns a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except psycopg2.OperationalError as e:
        st.error(f"Database connection failed: {e}")
        st.warning("Please check your PostgreSQL server and credentials.")
        return None

# --- CRUD Operations ---

# User Profile
def create_user_profile(name, email, organization=None):
    """Creates a new user profile."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO user_profile (name, email, organization) VALUES (%s, %s, %s) RETURNING user_id;",
                    (name, email, organization)
                )
                user_id = cur.fetchone()[0]
                conn.commit()
                return user_id
        except psycopg2.IntegrityError:
            st.error("A user with this email already exists.")
            return None
        finally:
            conn.close()
    return None

def get_user_profile(user_id):
    """Retrieves a user profile by user_id."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT user_id, name, email, organization FROM user_profile WHERE user_id = %s;",
                    (user_id,)
                )
                user_data = cur.fetchone()
                if user_data:
                    return dict(zip(['user_id', 'name', 'email', 'organization'], user_data))
        finally:
            conn.close()
    return None

def update_user_profile(user_id, name, email, organization=None):
    """Updates an existing user profile."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE user_profile SET name = %s, email = %s, organization = %s WHERE user_id = %s;",
                    (name, email, organization, user_id)
                )
                conn.commit()
                return True
        except psycopg2.IntegrityError:
            st.error("The new email is already in use by another user.")
            return False
        finally:
            conn.close()
    return False

# Events
def create_event(user_id, event_name, event_date, event_time, location, description):
    """Creates a new event."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO events (user_id, event_name, event_date, event_time, location, description) VALUES (%s, %s, %s, %s, %s, %s) RETURNING event_id;",
                    (user_id, event_name, event_date, event_time, location, description)
                )
                event_id = cur.fetchone()[0]
                conn.commit()
                return event_id
        finally:
            conn.close()
    return None

def get_events(user_id, sort_by='event_date'):
    """Retrieves all events for a given user, with sorting."""
    conn = get_db_connection()
    if conn:
        try:
            query = f"""
                SELECT
                    e.event_id,
                    e.event_name,
                    e.event_date,
                    e.event_time,
                    e.location,
                    e.description,
                    COALESCE(SUM(t.price * (SELECT COUNT(*) FROM attendees a WHERE a.ticket_id = t.ticket_id)), 0) AS total_revenue
                FROM events e
                LEFT JOIN tickets t ON e.event_id = t.event_id
                WHERE e.user_id = %s
                GROUP BY e.event_id
                ORDER BY {sort_by} DESC;
            """
            df = pd.read_sql(query, conn, params=(user_id,))
            return df
        finally:
            conn.close()
    return pd.DataFrame()

def update_event(event_id, event_name, event_date, event_time, location, description):
    """Updates an existing event."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE events SET event_name = %s, event_date = %s, event_time = %s, location = %s, description = %s WHERE event_id = %s;",
                    (event_name, event_date, event_time, location, description, event_id)
                )
                conn.commit()
                return True
        finally:
            conn.close()
    return False

def delete_event(event_id):
    """Deletes an event and all related tickets and attendees."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM attendees WHERE event_id = %s;", (event_id,))
                cur.execute("DELETE FROM tickets WHERE event_id = %s;", (event_id,))
                cur.execute("DELETE FROM events WHERE event_id = %s;", (event_id,))
                conn.commit()
                return True
        finally:
            conn.close()
    return False

# Tickets
def create_ticket(event_id, ticket_type, price, quantity_available):
    """Creates a new ticket type for an event."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO tickets (event_id, ticket_type, price, quantity_available) VALUES (%s, %s, %s, %s) RETURNING ticket_id;",
                    (event_id, ticket_type, price, quantity_available)
                )
                ticket_id = cur.fetchone()[0]
                conn.commit()
                return ticket_id
        finally:
            conn.close()
    return None

def get_tickets(event_id):
    """Retrieves all tickets for a given event."""
    conn = get_db_connection()
    if conn:
        try:
            query = "SELECT ticket_id, ticket_type, price, quantity_available FROM tickets WHERE event_id = %s;"
            df = pd.read_sql(query, conn, params=(event_id,))
            return df
        finally:
            conn.close()
    return pd.DataFrame()

def update_ticket(ticket_id, ticket_type, price, quantity_available):
    """Updates an existing ticket type."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE tickets SET ticket_type = %s, price = %s, quantity_available = %s WHERE ticket_id = %s;",
                    (ticket_type, price, quantity_available, ticket_id)
                )
                conn.commit()
                return True
        finally:
            conn.close()
    return False

def delete_ticket(ticket_id):
    """Deletes a ticket type."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                # First delete related attendees
                cur.execute("DELETE FROM attendees WHERE ticket_id = %s;", (ticket_id,))
                cur.execute("DELETE FROM tickets WHERE ticket_id = %s;", (ticket_id,))
                conn.commit()
                return True
        finally:
            conn.close()
    return False

# Attendees
def register_attendee(event_id, name, email, ticket_id):
    """Registers a new attendee for an event."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO attendees (event_id, name, email, ticket_id) VALUES (%s, %s, %s, %s) RETURNING attendee_id;",
                    (event_id, name, email, ticket_id)
                )
                attendee_id = cur.fetchone()[0]
                conn.commit()
                return attendee_id
        finally:
            conn.close()
    return None

def get_attendees(event_id, sort_by='name', filter_by_ticket_type=None):
    """Retrieves attendees for an event with sorting and filtering."""
    conn = get_db_connection()
    if conn:
        try:
            query = """
                SELECT a.attendee_id, a.name, a.email, t.ticket_type
                FROM attendees a
                JOIN tickets t ON a.ticket_id = t.ticket_id
                WHERE a.event_id = %s
            """
            params = [event_id]

            if filter_by_ticket_type:
                query += " AND t.ticket_type = %s"
                params.append(filter_by_ticket_type)

            query += f" ORDER BY a.{sort_by};"

            df = pd.read_sql(query, conn, params=tuple(params))
            return df
        finally:
            conn.close()
    return pd.DataFrame()

# --- Dashboard & Insights ---
def get_dashboard_metrics(user_id):
    """Calculates and returns key metrics for the user's events."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        COUNT(DISTINCT e.event_id) AS total_events,
                        COUNT(DISTINCT a.attendee_id) AS total_attendees,
                        COALESCE(SUM(t.price), 0) AS total_possible_revenue,
                        COALESCE(AVG(t.price), 0) AS average_ticket_price,
                        COALESCE(MIN(t.price), 0) AS min_ticket_price,
                        COALESCE(MAX(t.price), 0) AS max_ticket_price,
                        COALESCE(SUM(CASE WHEN t.price > 0 THEN t.price * (SELECT COUNT(*) FROM attendees a2 WHERE a2.ticket_id = t.ticket_id) ELSE 0 END), 0) AS net_revenue
                    FROM user_profile up
                    LEFT JOIN events e ON up.user_id = e.user_id
                    LEFT JOIN tickets t ON e.event_id = t.event_id
                    LEFT JOIN attendees a ON e.event_id = a.event_id
                    WHERE up.user_id = %s;
                    """,
                    (user_id,)
                )
                metrics = cur.fetchone()
                return {
                    "total_events": metrics[0],
                    "total_attendees": metrics[1],
                    "total_possible_revenue": metrics[2],
                    "average_ticket_price": metrics[3],
                    "min_ticket_price": metrics[4],
                    "max_ticket_price": metrics[5],
                    "net_revenue": metrics[6]
                }
        finally:
            conn.close()
    return {}

def get_event_performance_data(user_id):
    """Gathers data for event performance charts."""
    conn = get_db_connection()
    if conn:
        try:
            query = """
                SELECT
                    e.event_name,
                    COALESCE(SUM(t.quantity_available), 0) AS tickets_available,
                    COUNT(a.attendee_id) AS tickets_sold,
                    COALESCE(SUM(t.price), 0) AS total_revenue
                FROM events e
                LEFT JOIN tickets t ON e.event_id = t.event_id
                LEFT JOIN attendees a ON t.ticket_id = a.ticket_id
                WHERE e.user_id = %s
                GROUP BY e.event_id, e.event_name;
            """
            df = pd.read_sql(query, conn, params=(user_id,))
            return df
        finally:
            conn.close()
    return pd.DataFrame()

def get_attendee_distribution_data(user_id):
    """Gathers data for attendee distribution by ticket type chart."""
    conn = get_db_connection()
    if conn:
        try:
            query = """
                SELECT
                    t.ticket_type,
                    COUNT(a.attendee_id) AS attendee_count
                FROM attendees a
                JOIN events e ON a.event_id = e.event_id
                JOIN tickets t ON a.ticket_id = t.ticket_id
                WHERE e.user_id = %s
                GROUP BY t.ticket_type;
            """
            df = pd.read_sql(query, conn, params=(user_id,))
            return df
        finally:
            conn.close()
    return pd.DataFrame()

# --- Communication (Simulated) ---
def send_confirmation_email(attendee_name, attendee_email, event_name, ticket_type):
    """Simulates sending a confirmation email."""
    st.info(f"Simulating email to: {attendee_email}")
    email_body = f"""
    Hello {attendee_name},

    Thank you for registering for the event: {event_name}!

    Your registration for the '{ticket_type}' ticket has been confirmed.
    We look forward to seeing you there.

    Best regards,
    The Event Management Team
    """
    st.success(f"Email sent to {attendee_email} with the following content:\n{email_body}")