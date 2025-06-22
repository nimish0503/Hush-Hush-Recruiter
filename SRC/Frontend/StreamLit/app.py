import streamlit as st
import pandas as pd
import mysql.connector
import time
from datetime import datetime
from mailer import EmailService  # Import the EmailService class
import os

# Database connection parameters for the dashboard
DB_CONFIG = {
    "host": "35.246.172.147",
    "user": "root",
    "password": "12345",
    "database": "psanatics"
}

# Function to get data from MySQL
@st.cache_data(ttl=600)  # Cache for 10 minutes to reduce DB queries
def fetch_data():
    try:
        with mysql.connector.connect(**DB_CONFIG) as connection:
            query = "SELECT * FROM Candidate"
            df = pd.read_sql(query, connection)
        return df
    except Exception as e:
        st.error(f"❌ Database connection failed: {e}")
        return pd.DataFrame()

# Login credentials
USERNAME = st.secrets["credentials"]["username"]
PASSWORD = st.secrets["credentials"]["password"]

def check_credentials(username, password):
    """Check if the entered username and password are correct."""
    return username == USERNAME and password == PASSWORD

def login_page():
    st.image("images/recruiter.png", use_container_width=True)
    st.title("Doodle Recruiter Login")
    st.write("Automated Recruitment System")
    st.write("You dream it, we do it.")

    st.header("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if check_credentials(username, password):
            st.success("Logged in successfully!")
            st.write("Redirecting to the dashboard...")
            st.session_state["logged_in"] = True
            st.rerun()
        else:
            st.error("😕 Invalid username or password")

    for _ in range(10):
        st.write("")

    col1, col2, col3 = st.columns([2, 1, 1])
    with col3:
        st.image("images/Logo.png", width=100)

def dashboard():
    st.set_page_config(page_title="Recruiter Dashboard", layout="wide")

    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("Logout"):
            st.session_state["logged_in"] = False
            st.success("Logged out successfully!")
            st.rerun()

    st.title("🚀 Recruiter Dashboard")

    if "selected_candidates" not in st.session_state or not isinstance(st.session_state.selected_candidates, dict):
        st.session_state.selected_candidates = {"Data Science": {}, "Java Developer": {}, "Web Developer": {}}

    if st.session_state["logged_in"]:
        with st.sidebar:
            st.header("🔍 Filters")
            selected_role = st.selectbox("🎯 Job Role:", ["Data Science", "Java Developer", "Web Developer"])
            sort_by = st.selectbox("📊 Sort By:", ["Commit Score", "Total Commits (Last Year)", "Public Repos", "Followers"])

    sort_column_map = {
        "Commit Score": "commit_score",
        "Total Commits (Last Year)": "total_commits_last_year",
        "Public Repos": "public_repos",
        "Followers": "followers",
    }

    data = fetch_data()

    if data.empty:
        st.warning("⚠️ No data available. Please check your database connection.")
    else:
        if "job_role" not in data.columns:
            st.error("⚠️ Missing 'job_role' column in the database table.")
        else:
            filtered_data = data[data["job_role"] == selected_role]

            if sort_column_map[sort_by] not in filtered_data.columns:
                st.error(f"⚠️ Column '{sort_by}' not found in database.")
            else:
                top_candidates = filtered_data.nlargest(20, sort_column_map[sort_by])

                st.subheader(f"Top Candidates for {selected_role} (Sorted by {sort_by})")

                for _, row in top_candidates.iterrows():
                    with st.container():
                        col1, col2 = st.columns([1, 3])
                        with col1:
                            st.image(row["avatar_url"], width=200)
                        with col2:
                            st.markdown(f"### {row['username']}")
                            
                            # GitHub Badge (White)
                            st.markdown(
                                f'<a href="{row["user_url"]}">'
                                f'<img src="https://img.shields.io/badge/GitHub-Profile-white?logo=github" alt="GitHub" style="height: 28px;">'
                                f'</a>',
                                unsafe_allow_html=True
                            )
                            
                            # Email Badge (White)
                            st.markdown(
                                f'<a href="mailto:{row["email"]}">'
                                f'<img src="https://img.shields.io/badge/Email-{row["email"]}-white?logo=gmail" alt="Email" style="height: 28px;">'
                                f'</a>',
                                unsafe_allow_html=True
                            )
                            
                            # Public Repos Badge (White)
                            st.markdown(
                                f'<a href="{row["user_url"]}?tab=repositories">'
                                f'<img src="https://img.shields.io/badge/Public_Repos-{row["public_repos"]}-white?logo=github" alt="Public Repos" style="height: 28px;">'
                                f'</a>',
                                unsafe_allow_html=True
                            )
                            
                            # Followers Badge (White)
                            st.markdown(
                                f'<a href="{row["user_url"]}?tab=followers">'
                                f'<img src="https://img.shields.io/badge/Followers-{row["followers"]}-white?logo=github" alt="Followers" style="height: 28px;">'
                                f'</a>',
                                unsafe_allow_html=True
                            )
                            
                            # Commit Score Badge (White)
                            st.markdown(
                                f'<a href="{row["user_url"]}">'
                                f'<img src="https://img.shields.io/badge/Commit_Score-{row["commit_score"]:.2f}-white?logo=git" alt="Commit Score" style="height: 28px;">'
                                f'</a>',
                                unsafe_allow_html=True
                            )

                            if row["username"] in st.session_state.selected_candidates[selected_role]:
                                st.success(f"✅ {row['username']} has been selected for the coding interview process")
                            else:
                                if st.button(f"✅ Select {row['username']}", key=f"select_{row['username']}"):
                                    st.session_state.selected_candidates[selected_role][row["username"]] = {
                                        "email_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        "avatar_url": row["avatar_url"],
                                        "user_url": row["user_url"],
                                        "email": row["email"],
                                        "public_repos": row["public_repos"],
                                        "followers": row["followers"],
                                        "commit_score": row["commit_score"],
                                    }
                                    # Send shortlist email
                                    email_service = EmailService(
                                        sender_email=os.getenv("EMAIL_ADDRESS"),
                                        sender_password=os.getenv("EMAIL_PASSWORD")
                                    )
                                    email_service.send_shortlist_email(
                                        recipient_email=row["email"],
                                        candidate_name=row["username"],
                                        questionnaire_link="https://shorturl.at/nZLia",
                                        job_title=selected_role
                                    )
                                    st.success(f"📧 Email has been sent to {row['username']}.")
                                    time.sleep(2)
                                    st.rerun()
                    st.divider()

    if st.session_state["logged_in"] and st.button("View Selected Candidates"):
        st.session_state["page"] = "selected_candidates"
        st.rerun()

if __name__ == "__main__":
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        login_page()
    else:
        if "page" not in st.session_state:
            st.session_state["page"] = "dashboard"

        if st.session_state["page"] == "dashboard":
            dashboard()
        elif st.session_state["page"] == "selected_candidates":
            st.switch_page("pages/selected_candidates.py")