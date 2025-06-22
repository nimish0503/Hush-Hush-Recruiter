import streamlit as st
import mysql.connector
import os
from mailer import EmailService  # Ensure mailer.py is in the same directory or adjust the import path

# Set page configuration to wide layout
st.set_page_config(layout="wide")

# Database connection parameters
DB_CONFIG = {
    "host": "",
    "user": "",
    "password": "",
    "database": ""
}

# Table names
EVALUATED_TABLE = "Evaluated"
CANDIDATE_TABLE = "Candidate"
HR_INTERVIEW_TABLE = "HrInterview"

# Initialize EmailService
sender_email = os.getenv("EMAIL_ADDRESS")
sender_password = os.getenv("EMAIL_PASSWORD")
email_service = EmailService(sender_email, sender_password)

# Function to connect to the database
def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# Function to create the HrInterview table if it doesn't exist
def create_hr_interview_table():
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {HR_INTERVIEW_TABLE} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_name VARCHAR(255) NOT NULL,
                user_email VARCHAR(255) NOT NULL,
                job_role VARCHAR(255),
                submission_time DATETIME,
                additional_details TEXT
            )
        """)
        connection.commit()
    except Exception as e:
        st.error(f"Failed to create table '{HR_INTERVIEW_TABLE}': {e}")
    finally:
        cursor.close()
        connection.close()

# Function to fetch data from the Evaluated table
def fetch_data(job_role=None):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    if job_role:
        query = f"SELECT * FROM {EVALUATED_TABLE} WHERE job_role = %s"
        cursor.execute(query, (job_role,))
    else:
        query = f"SELECT * FROM {EVALUATED_TABLE}"
        cursor.execute(query)
    
    data = cursor.fetchall()
    cursor.close()
    connection.close()
    return data

# Function to check if a candidate exists in the Candidate table
def get_candidate_details(user_name):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        query = f"SELECT * FROM {CANDIDATE_TABLE} WHERE username = %s"
        cursor.execute(query, (user_name,))
        result = cursor.fetchone()
        return result
    except Exception as e:
        st.error(f"Failed to fetch candidate details: {e}")
        return None
    finally:
        cursor.close()
        connection.close()

# Function to insert candidate details into the HrInterview table
def insert_into_hr_interview(user_name, user_email, job_role, submission_time, additional_details=None):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        query = f"""
            INSERT INTO {HR_INTERVIEW_TABLE} (user_name, user_email, job_role, submission_time, additional_details)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (user_name, user_email, job_role, submission_time, additional_details))
        connection.commit()
        st.success("HR has been notified of the candidate.")
    except Exception as e:
        st.error(f"Failed to insert into {HR_INTERVIEW_TABLE}: {e}")
    finally:
        cursor.close()
        connection.close()

# Streamlit page
st.title("Evaluated Results")

# Create the HrInterview table if it doesn't exist
create_hr_interview_table()

# Filter by job role
job_roles = fetch_data()
unique_job_roles = list(set(row['job_role'] for row in job_roles))
selected_job_role = st.selectbox("Filter by Job Role", ["All"] + unique_job_roles)

# Fetch data based on selected job role
if selected_job_role == "All":
    data = fetch_data()
else:
    data = fetch_data(selected_job_role)

# Display the list of candidates
if data:
    candidates = [f"{row['user_name']} ({row['user_email']})" for row in data]
    selected_candidate = st.selectbox("Select a Candidate", candidates)
    
    # Find the selected candidate's data
    selected_candidate_data = next((row for row in data if f"{row['user_name']} ({row['user_email']})" == selected_candidate), None)
    
    if selected_candidate_data:
        st.subheader(f"Candidate: {selected_candidate_data['user_name']}")
        
        # Display detailed answers with scores
        for i in range(1, 11):
            with st.expander(f"Q{i}: {selected_candidate_data[f'Q{i}']}"):
                st.write(f"**Answer:** {selected_candidate_data[f'Answer{i}']}")
                st.write(f"**Score:** {selected_candidate_data[f'Score{i}']}")
        
        st.write(f"**Submission Time:** {selected_candidate_data['submission_time']}")
        
        # Aggregate scores and display in a metric card
        total_score = sum(selected_candidate_data[f'Score{i}'] for i in range(1, 11))
        max_score = 10 * 10  # Assuming each question is out of 10
        st.metric(label="Total Score", value=f"{total_score} / {max_score}")
        
        # Progress bar for total score
        st.progress(total_score / max_score)
        
        # Candidate summary
        st.info(f"**Candidate Summary:** {selected_candidate_data['user_name']} scored {total_score} out of {max_score}.")
        
        # Buttons for selection and rejection
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Selected", key="selected"):
                try:
                    # Get candidate details from the Candidate table
                    candidate_details = get_candidate_details(selected_candidate_data['user_name'])
                    
                    # Prepare additional details (if available)
                    additional_details = None
                    if candidate_details:
                        additional_details = f"Additional details from Candidate table: {candidate_details}"
                    
                    # Insert into HrInterview table
                    insert_into_hr_interview(
                        user_name=selected_candidate_data['user_name'],
                        user_email=selected_candidate_data['user_email'],
                        job_role=selected_candidate_data['job_role'],
                        submission_time=selected_candidate_data['submission_time'],
                        additional_details=additional_details
                    )
                    
                    # Send HR interview invitation
                    hr_email = "100003141@stud.srh-university.de"  # HR email address
                    interview_dates = ["2023-10-30", "2023-11-01"]  # Example interview dates
                    email_service.send_hr_interview_invitation(
                        hr_email=hr_email,
                        candidate_email=selected_candidate_data['user_email'],
                        candidate_name=selected_candidate_data['user_name'],
                        interview_dates=interview_dates
                    )
                    
                    st.session_state.buttons_disabled = True
                except Exception as e:
                    st.error(f"Failed to process selection: {e}")
        with col2:
            if st.button("Rejected", key="rejected"):
                try:
                    # Send rejection email to the candidate
                    email_service.send_rejection_email(
                        recipient_email=selected_candidate_data['user_email'],
                        candidate_name=selected_candidate_data['user_name']
                    )
                    st.success("The candidate has been informed about their status. Thank you for your decision.")
                    st.session_state.buttons_disabled = True
                except Exception as e:
                    st.error(f"Failed to send rejection email: {e}")
        
        # Disable buttons after one is clicked
        if 'buttons_disabled' in st.session_state and st.session_state.buttons_disabled:
            pass  # Buttons are disabled after selection
else:
    st.write("No data found.")
