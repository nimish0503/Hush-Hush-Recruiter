import streamlit as st

# Ensure session state for selected candidates
if "selected_candidates" not in st.session_state or not isinstance(st.session_state.selected_candidates, dict):
    st.session_state.selected_candidates = {"Data Science": {}, "Java Developer": {}, "Web Developer": {}}

# Streamlit UI Configuration
st.set_page_config(page_title="Selected Candidates", layout="wide")

# Add a logout button at the top right corner
col1, col2 = st.columns([4, 1])
with col2:
    if st.button("Logout"):
        st.session_state["logged_in"] = False
        st.success("Logged out successfully!")
        st.switch_page("app.py")  # Redirect to the login page

# Professional Header
st.title("📋 Selected Candidates")

# Filter by Job Role
selected_role = st.selectbox("🎯 Filter by Job Role:", ["Data Science", "Java Developer", "Web Developer"])

# Display Selected Candidates
st.subheader(f"Selected Candidates for {selected_role}")

if st.session_state.selected_candidates[selected_role]:
    for username, details in st.session_state.selected_candidates[selected_role].items():
        with st.container():
            col1, col2 = st.columns([1, 3])
            with col1:
                st.image(details["avatar_url"], width=250)
            with col2:
                st.markdown(f"### {username}")
                st.markdown(f"📧 **Email Sent At:** {details['email_time']}")
                st.markdown(f"🔗 **GitHub Profile:** [Link]({details['user_url']})")
                st.markdown(f"📂 **Public Repos:** {details['public_repos']}")
                st.markdown(f"👥 **Followers:** {details['followers']}")
                st.markdown(f"🔥 **Commit Score:** `{details['commit_score']:.2f}`")
        st.divider()
else:
    st.write("No candidates selected for this role yet.")

# Navigation Back to Dashboard
if st.button("Back to Dashboard"):
    st.session_state["page"] = "dashboard"
    st.switch_page("app.py")