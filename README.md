# 🕵️‍♂️ Hush-Hush Recruiter

> A smart, private AI system that automates parts of the technical hiring process — from scanning GitHub activity to interview scheduling — all without relying on job portals.

<p align="center">
  <img src="https://img.shields.io/badge/Python-Streamlit-blue?logo=python" />
  <img src="https://img.shields.io/badge/Deployed-GCP-orange?logo=googlecloud" />
  <img src="https://img.shields.io/badge/Automated-Hiring-green?logo=fastapi" />
</p>

---

## ✨ What This Project Does

This system helps recruiters:
- Find candidates from unconventional public sources
- Evaluate coding profiles (automated)
- Send communication and track interview progress
- Offer a complete interface to HR and tech panels

> Think of it as a **minimalist ATS** powered by a blend of **code scraping**, **ML filtering**, and **automated communication.**

---

## 🧠 How It Works

1. **Public Git Profiles → Ranked CSVs**
   - A backend service fetches data from public repositories
   - Profiles are scored and saved

2. **ML-based Candidate Scoring**
   - A machine learning model rates coding contributions
   - Helps recruiters shortlist automatically

3. **Smart Dashboards**
   - Built using [Streamlit](https://streamlit.io/)
   - Filter, sort, and select top candidates per role

4. **Emails + Assessment Invites**
   - Auto-sends test links and logs response time
   - Supports multiple email templates (HTML-styled)

5. **Panel Coordination**
   - HR can choose slots
   - Candidates get calendar-style invites

---

## 🛠️ Tech Highlights (Partially Hidden)

- **Frontend**: Streamlit
- **Backend**: Custom Python scripts 
- **Database**: SQL (cloud-hosted)
- **ML**: Role-based scoring model (trained offline)
- **Email**: Automated via secure SMTP
- **Security**: Secrets stored in `.env` and `.toml`

---
