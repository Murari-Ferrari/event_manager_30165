# File: frontend_event.py

import streamlit as st
import pandas as pd
import backend_event as db
from datetime import datetime, date, time

st.set_page_config(layout="wide")

# --- Session State Management ---
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'page' not in st.session_state:
    st.session_state.page = 'profile'
if 'selected_event_id' not in st.session_state:
    st.session_state.selected_event_id = None
if 'editing_event_id' not in st.session_state:
    st.session_state.editing_event_id = None
if 'editing_ticket_id' not in st.session_state:
    st.session_state.editing_ticket_id = None
if 'profile_created' not in st.session_state:
    st.session_state.profile_created = False

# --- UI Functions ---
def show_profile_page():
    st.title("👤 User Profile_Sai Mohan Murari Pupala_30165")
    if not st.session_state.profile_created:
        st.header("Create Your Profile")
        with st.form("create_profile_form"):
            name = st.text_input("Name", placeholder="John Doe")
            email = st.text_input("Email", placeholder="john.doe@example.com")
            organization = st.text_input("Organization (optional)")
            submit = st.form_submit_button("Create Profile")
            if submit:
                user_id = db.create_user_profile(name, email, organization)
                if user_id:
                    st.session_state.user_id = user_id
                    st.session_state.profile_created = True
                    st.success("Profile created successfully! You can now start managing events.")
                    st.rerun() # Corrected from st.experimental_rerun()
    else:
        profile = db.get_user_profile(st.session_state.user_id)
        if profile:
            st.header("Update Your Profile")
            with st.form("update_profile_form"):
                name = st.text_input("Name", value=profile['name'])
                email = st.text_input("Email", value=profile['email'])
                organization = st.text_input("Organization (optional)", value=profile['organization'])
                submit = st.form_submit_button("Update Profile")
                if submit:
                    if db.update_user_profile(st.session_state.user_id, name, email, organization):
                        st.success("Profile updated successfully!")
                        st.rerun() # Corrected from st.experimental_rerun()

def show_events_page():
    st.title("🗓️ My Events")

    with st.expander("➕ Create New Event", expanded=False):
        with st.form("create_event_form"):
            event_name = st.text_input("Event Name", placeholder="My Awesome Event")
            col1, col2 = st.columns(2)
            event_date = col1.date_input("Event Date", min_value=date.today())
            event_time = col2.time_input("Event Time", value=time(19, 0))
            location = st.text_input("Location", placeholder="Conference Hall A")
            description = st.text_area("Description")
            create_submit = st.form_submit_button("Create Event")
            if create_submit:
                if event_name:
                    db.create_event(st.session_state.user_id, event_name, event_date, event_time, location, description)
                    st.success(f"Event '{event_name}' created successfully!")
                    st.rerun() # Corrected from st.experimental_rerun()
                else:
                    st.error("Please enter an event name.")

    st.header("Your Existing Events")
    events_df = db.get_events(st.session_state.user_id)
    if not events_df.empty:
        st.dataframe(events_df[['event_name', 'event_date', 'event_time', 'total_revenue']], use_container_width=True)
        col_select, col_sort = st.columns([3,1])
        selected_event_name = col_select.selectbox(
            "Select an event to manage:",
            events_df['event_name'].tolist(),
            index=None
        )
        sort_by = col_sort.selectbox(
            "Sort Events By:",
            ["event_date", "total_revenue"],
            format_func=lambda x: "Date" if x == "event_date" else "Total Revenue"
        )
        events_df = db.get_events(st.session_state.user_id, sort_by=sort_by)
        st.dataframe(events_df[['event_name', 'event_date', 'event_time', 'total_revenue']], use_container_width=True)
        
        if selected_event_name:
            selected_event_row = events_df[events_df['event_name'] == selected_event_name].iloc[0]
            st.session_state.selected_event_id = selected_event_row['event_id']

            st.markdown("---")
            st.subheader(f"Managing: {selected_event_name}")

            col1, col2 = st.columns(2)
            with col1.expander("✏️ Edit Event Details"):
                with st.form("edit_event_form"):
                    new_name = st.text_input("Event Name", value=selected_event_row['event_name'])
                    new_date = st.date_input("Event Date", value=selected_event_row['event_date'], min_value=date.today())
                    new_time = st.time_input("Event Time", value=selected_event_row['event_time'])
                    new_location = st.text_input("Location", value=selected_event_row['location'])
                    new_description = st.text_area("Description", value=selected_event_row['description'])
                    edit_submit = st.form_submit_button("Update Event")
                    if edit_submit:
                        db.update_event(st.session_state.selected_event_id, new_name, new_date, new_time, new_location, new_description)
                        st.success("Event updated successfully!")
                        st.rerun() # Corrected from st.experimental_rerun()

            with col2.expander("🗑️ Delete Event"):
                if st.button("Delete Event", key="delete_event_btn", help="This will delete all associated tickets and attendees.", use_container_width=True):
                    db.delete_event(st.session_state.selected_event_id)
                    st.success(f"Event '{selected_event_name}' and all its data deleted successfully!")
                    st.session_state.selected_event_id = None
                    st.rerun() # Corrected from st.experimental_rerun()

            show_tickets_section(st.session_state.selected_event_id)
            show_attendees_section(st.session_state.selected_event_id)
    else:
        st.info("You haven't created any events yet.")

def show_tickets_section(event_id):
    st.markdown("---")
    st.subheader("🎟️ Tickets")
    
    with st.expander("➕ Create New Ticket Type", expanded=False):
        with st.form("create_ticket_form"):
            ticket_type = st.text_input("Ticket Type", placeholder="General Admission")
            col1, col2 = st.columns(2)
            price = col1.number_input("Price", min_value=0.00, format="%.2f")
            quantity = col2.number_input("Quantity Available", min_value=1, step=1)
            create_ticket_submit = st.form_submit_button("Create Ticket")
            if create_ticket_submit:
                if ticket_type and price is not None and quantity is not None:
                    db.create_ticket(event_id, ticket_type, price, quantity)
                    st.success(f"Ticket type '{ticket_type}' created successfully!")
                    st.rerun() # Corrected from st.experimental_rerun()
    
    tickets_df = db.get_tickets(event_id)
    if not tickets_df.empty:
        st.subheader("Existing Tickets")
        st.dataframe(tickets_df, use_container_width=True)
        col1, col2, col3 = st.columns(3)
        edit_ticket_id = col1.selectbox("Edit Ticket", tickets_df['ticket_id'].tolist(), index=None, key="edit_ticket_box")
        delete_ticket_id = col2.selectbox("Delete Ticket", tickets_df['ticket_id'].tolist(), index=None, key="delete_ticket_box")

        if edit_ticket_id:
            st.session_state.editing_ticket_id = edit_ticket_id
            ticket_row = tickets_df[tickets_df['ticket_id'] == edit_ticket_id].iloc[0]
            with st.form("update_ticket_form"):
                new_type = st.text_input("Ticket Type", value=ticket_row['ticket_type'])
                new_price = st.number_input("Price", value=float(ticket_row['price']), min_value=0.00, format="%.2f")
                new_quantity = st.number_input("Quantity Available", value=int(ticket_row['quantity_available']), min_value=1, step=1)
                update_submit = st.form_submit_button("Update Ticket")
                if update_submit:
                    db.update_ticket(edit_ticket_id, new_type, new_price, new_quantity)
                    st.success("Ticket updated successfully!")
                    st.rerun() # Corrected from st.experimental_rerun()
        
        if delete_ticket_id and st.button("Confirm Delete", key="delete_ticket_btn"):
            db.delete_ticket(delete_ticket_id)
            st.success("Ticket deleted successfully!")
            st.rerun() # Corrected from st.experimental_rerun()
    else:
        st.info("No tickets have been created for this event yet.")

def show_attendees_section(event_id):
    st.markdown("---")
    st.subheader("👥 Attendees")

    tickets_df = db.get_tickets(event_id)
    ticket_options = {row['ticket_type']: row['ticket_id'] for _, row in tickets_df.iterrows()}
    
    if not tickets_df.empty:
        with st.expander("📝 Register New Attendee", expanded=False):
            with st.form("register_attendee_form"):
                attendee_name = st.text_input("Name", placeholder="Jane Doe")
                attendee_email = st.text_input("Email", placeholder="jane.doe@example.com")
                selected_ticket_type = st.selectbox("Ticket Type", list(ticket_options.keys()))
                register_submit = st.form_submit_button("Register Attendee")
                if register_submit:
                    ticket_id = ticket_options[selected_ticket_type]
                    if attendee_name and attendee_email:
                        db.register_attendee(event_id, attendee_name, attendee_email, ticket_id)
                        db.send_confirmation_email(attendee_name, attendee_email, "Current Event", selected_ticket_type)
                        st.success(f"Attendee '{attendee_name}' registered successfully!")
                        st.rerun() # Corrected from st.experimental_rerun()
                    else:
                        st.error("Please fill in name and email.")

    st.subheader("Existing Attendees")
    if not tickets_df.empty:
        col_filter, col_sort = st.columns(2)
        filter_type = col_filter.selectbox("Filter by Ticket Type", ["All"] + list(ticket_options.keys()))
        sort_by = col_sort.selectbox("Sort By", ["name", "ticket_type"])
        
        attendees_df = db.get_attendees(
            event_id,
            sort_by=sort_by,
            filter_by_ticket_type=filter_type if filter_type != "All" else None
        )
        if not attendees_df.empty:
            st.dataframe(attendees_df, use_container_width=True)
        else:
            st.info("No attendees found for this event with the selected filter.")
    else:
        st.info("You must create tickets before you can register attendees.")

def show_dashboard_page():
    st.title("📊 Dashboard")
    st.markdown("---")
    st.header("Overall Performance")
    
    metrics = db.get_dashboard_metrics(st.session_state.user_id)
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Events", metrics.get("total_events", 0))
    col2.metric("Attendees", metrics.get("total_attendees", 0))
    col3.metric("Net Revenue", f"${metrics.get('net_revenue', 0):.2f}")
    col4.metric("Avg Ticket Price", f"${metrics.get('average_ticket_price', 0):.2f}")
    col5.metric("Min Price", f"${metrics.get('min_ticket_price', 0):.2f}")
    col6.metric("Max Price", f"${metrics.get('max_ticket_price', 0):.2f}")

    st.markdown("---")
    st.header("Event-Specific Insights")
    performance_df = db.get_event_performance_data(st.session_state.user_id)
    if not performance_df.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Tickets Sold vs. Available")
            st.bar_chart(performance_df, x="event_name", y=["tickets_sold", "tickets_available"])
        with col2:
            st.subheader("Revenue per Event")
            st.bar_chart(performance_df, x="event_name", y="total_revenue")
    else:
        st.info("No event performance data available.")

    st.markdown("---")
    st.header("Attendee Distribution")
    distribution_df = db.get_attendee_distribution_data(st.session_state.user_id)
    if not distribution_df.empty:
        st.dataframe(distribution_df, use_container_width=True)
        st.bar_chart(distribution_df, x="ticket_type", y="attendee_count")
    else:
        st.info("No attendee data available for distribution chart.")

# --- Main App Logic ---
st.sidebar.title("Event Manager")
if st.session_state.profile_created:
    if st.sidebar.button("👤 My Profile", use_container_width=True):
        st.session_state.page = 'profile'
    if st.sidebar.button("🗓️ My Events", use_container_width=True):
        st.session_state.page = 'events'
    if st.sidebar.button("📊 Dashboard", use_container_width=True):
        st.session_state.page = 'dashboard'

if st.session_state.user_id is None:
    show_profile_page()
else:
    if st.session_state.page == 'profile':
        show_profile_page()
    elif st.session_state.page == 'events':
        show_events_page()
    elif st.session_state.page == 'dashboard':
        show_dashboard_page()