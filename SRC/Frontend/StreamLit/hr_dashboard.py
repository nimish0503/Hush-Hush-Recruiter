import streamlit as st
import mysql.connector
from mailer import EmailService
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Database configuration
DB_CONFIG = {
    "host": "35.246.172.147",
    "user": "root",
    "password": "12345",
    "database": "psanatics"
}

def get_candidates():
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM HrInterview")
    candidates = cursor.fetchall()
    cursor.close()
    connection.close()
    return candidates

def get_candidate_details(candidate_email):
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM Candidate WHERE email = '{candidate_email}'")
    candidate_details = cursor.fetchone()
    cursor.close()
    connection.close()
    return candidate_details

def main():
    st.title("HR Interview Dashboard")

    candidates = get_candidates()

    for candidate in candidates:
        if candidate['id'] is None:
            continue

        with st.container():
            st.write(f"**Name:** {candidate['user_name']}")
            st.write(f"**Email:** {candidate['user_email']}")
            st.write(f"**Job Role:** {candidate['job_role']}")

            # Fetch additional details from the Candidate table using email
            candidate_details = get_candidate_details(candidate['user_email'])
            if candidate_details:
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.image(candidate_details["avatar_url"], width=180)
                with col2:
                    st.markdown(f"[🔗 GitHub Profile]({candidate_details['user_url']})")
                    st.markdown(f"📧 **Email:** {candidate_details['email']}")
                    st.markdown(f"📂 **Public Repos:** {candidate_details['public_repos']}")
                    st.markdown(f"👥 **Followers:** {candidate_details['followers']}")
                    st.markdown(f"🔥 **Commit Score:** `{candidate_details['commit_score']:.2f}`")

            col1, col2 = st.columns(2)

            with col1:
                date1 = st.date_input("Select first interview date", key=f"date1_{candidate['id']}")
                time1 = st.time_input("Select first interview time", key=f"time1_{candidate['id']}")

            with col2:
                date2 = st.date_input("Select second interview date ", key=f"date2_{candidate['id']}")
                time2 = st.time_input("Select second interview time", key=f"time2_{candidate['id']}")

            if st.button("Send Invitation", key=f"btn_{candidate['id']}"):
                interview_dates = [
                    datetime.combine(date1, time1).strftime("%B %d, %Y at %I:%M %p"),
                    datetime.combine(date2, time2).strftime("%B %d, %Y at %I:%M %p")
                ]
                hr_email = os.getenv("HR_EMAIL")
                candidate_email = candidate['user_email']
                candidate_name = candidate['user_name']

                email_service = EmailService(os.getenv("EMAIL_ADDRESS"), os.getenv("EMAIL_PASSWORD"))
                email_service.send_hr_interview_invitation(hr_email, candidate_email, candidate_name, interview_dates)
                st.success(f"Invitation sent to {candidate_name}")

if __name__ == "__main__":
    main()