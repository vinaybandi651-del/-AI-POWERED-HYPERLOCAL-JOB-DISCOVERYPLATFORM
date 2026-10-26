# HyperLocal Job Match ⚡
### AI-Powered Hyperlocal Job Discovery & Recommendation Platform for Students

> **Major Area:** Artificial Intelligence & Machine Learning  
> **Specific Area:** Location-Aware Collaborative Filtering + Content-Based Recommendation System  
> **Target Audience:** College / University Students seeking nearby flexible gigs and Local Businesses needing short-term workers.

---

## 🌟 Executive Summary & Innovation

Students struggle to find part-time gigs that seamlessly align with their **lecture schedules, specific skill sets, physical campus location, and expected pay**. Concurrently, local businesses (cafes, tech startups, tutoring academies, event agencies, retail stores) frequently face urgent staffing shortages.

**HyperLocal Job Match** solves this mismatch with an **AI-powered hybrid recommendation engine** that answers:
> *"Which nearby job is most suitable for this specific student, and why?"*

Rather than acting as a static job board, the engine produces **transparent, explainable match percentages (0–100%)** with fine-grained score breakdowns.

---

## 🧠 AI Recommendation Engine Architecture

```
Student Profile (Skills, Campus GPS, Calendar Availability, Target Pay)
                         ↓
            Feature Extraction & Vectorization
                         ↓
  ┌─────────────────────────────────────────────────────────────┐
  │                   Hybrid AI Ensemble Engine                 │
  ├──────────────────────────────┬──────────────────────────────┤
  │  1. Content-Based (40%)      │ TF-IDF + Cosine Similarity   │
  │                              │ Jaccard Skill Overlap        │
  ├──────────────────────────────┼──────────────────────────────┤
  │  2. Location-Aware (25%)     │ Haversine Formula (km)       │
  │                              │ Smooth Exponential Decay     │
  ├──────────────────────────────┼──────────────────────────────┤
  │  3. Schedule Fit (15%)       │ Days of Week + Shift Windows │
  ├──────────────────────────────┼──────────────────────────────┤
  │  4. Collaborative (10%)      │ Interaction History Matrix   │
  │                              │ Item/User Cosine Similarity  │
  ├──────────────────────────────┼──────────────────────────────┤
  │  5. Salary Alignment (10%)   │ Daily Equivalent Pay Ratio   │
  └──────────────────────────────┴──────────────────────────────┘
                         ↓
       Ranked Opportunities with "Why This Matches You"
```

### 1. Content-Based Filtering (TF-IDF & Cosine Similarity)
Job requirements and student profiles are mapped into high-dimensional vector spaces using Term Frequency-Inverse Document Frequency (TF-IDF):
$$\text{TF-IDF}(t, d, D) = \text{TF}(t, d) \times \log\left(\frac{1 + |D|}{1 + |\{d \in D : t \in d\}|}\right) + 1$$
Cosine similarity between profile vector $\vec{u}$ and job vector $\vec{v}$:
$$\text{Sim}_{\text{content}}(\vec{u}, \vec{v}) = \frac{\vec{u} \cdot \vec{v}}{\|\vec{u}\| \|\vec{v}\|}$$
Coupled with exact required skill match ratio:
$$\text{Score}_{\text{skills}} = \frac{|\text{StudentSkills} \cap \text{JobSkills}|}{|\text{JobSkills}|}$$

### 2. Location-Aware Matching (Haversine Formula)
Computes real-world spherical surface distance between student $(\phi_1, \lambda_1)$ and job workplace $(\phi_2, \lambda_2)$:
$$a = \sin^2\left(\frac{\Delta\phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta\lambda}{2}\right)$$
$$c = 2 \cdot \arctan2(\sqrt{a}, \sqrt{1-a})$$
$$d = R \cdot c \quad (\text{where } R = 6371\text{ km})$$
Proximity scores decay gracefully within the student's maximum willingness to travel ($D_{\text{max}}$):
$$\text{Score}_{\text{loc}} = \begin{cases} 
1.0 - \left(\frac{d}{D_{\text{max}}}\right) \times 0.60 & \text{if } d \le D_{\text{max}} \\
0.40 \times \exp(-0.25(d - D_{\text{max}})) & \text{if } d > D_{\text{max}}
\end{cases}$$

### 3. Collaborative Filtering (Interaction History Matrix)
Implicit user-job feedback matrix with calibrated action weights:
- **View Job:** $+1$
- **Search Job:** $+2$
- **Save / Bookmark:** $+3$
- **Apply for Job:** $+5$
- **Employer Shortlist / Accept:** $+7$
- **Job Completed:** $+10$
- **Application Rejected:** $-2$

Item-based collaborative filtering predicts student interest based on co-interaction patterns of peer students:
$$\hat{r}_{u, j} = \frac{\sum_{k \in \text{Interacted}(u)} \text{Sim}(j, k) \cdot r_{u, k}}{\sum_{k} |\text{Sim}(j, k)|}$$
*Cold-start fallback:* New student profiles with minimal interaction history are seamlessly seeded through content and location-based scoring.

### 4. Hybrid Weighted Ensemble
$$\text{Final Match Score} = (S_{\text{content}} \times w_c) + (S_{\text{loc}} \times w_l) + (S_{\text{avail}} \times w_a) + (S_{\text{cf}} \times w_{cf}) + (S_{\text{salary}} \times w_s)$$
*Default production weights:* $w_c = 0.40, w_l = 0.25, w_a = 0.15, w_{cf} = 0.10, w_s = 0.10$. Weights are dynamically configurable by administrators or through the interactive simulation laboratory.

---

## 💻 Tech Stack

- **Backend:** Python 3, Flask, SQLite3 (relational schema designed for PostgreSQL migration)
- **AI / ML:** Scikit-Learn (`TfidfVectorizer`, `cosine_similarity`), NumPy, SciPy, Pandas
- **Security:** Werkzeug password hashing (`scrypt`/`pbkdf2`), PyJWT bearer authentication, role-based decorators
- **Frontend:** Responsive HTML5, Modern CSS3 with Design System tokens, Vanilla JavaScript (ES6+), Leaflet.js (OpenStreetMap), Chart.js
- **Communication:** One-to-one in-app chat engine with real-time polling and notification bell

---

## 📁 Repository Directory Structure

```text
job discovery/
├── backend/
│   ├── app.py                      # Flask Application Server & Static Host
│   ├── database/
│   │   ├── db.py                   # SQLite Connection Manager & Helpers
│   │   ├── schema.sql              # Relational Database Schema (14 Tables)
│   │   └── seed_data.py            # 20 Students, 10 Employers, 52 Jobs Seeder
│   ├── recommendation/
│   │   ├── content_based.py        # TF-IDF, Jaccard & Experience Matching
│   │   ├── location_matching.py    # Haversine Distance & Decay Scoring
│   │   ├── collaborative.py        # Interaction Matrix & Peer Trend
│   │   └── hybrid_recommender.py   # Weighted Multi-Factor Ensemble Engine
│   ├── routes/
│   │   ├── auth.py                 # Registration, Login & Demo Accounts
│   │   ├── students.py             # Student Profile & Preferences
│   │   ├── employers.py            # Employer Business Profile & Stats
│   │   ├── jobs.py                 # Jobs Search, Radius Filters & Posting
│   │   ├── applications.py         # Multi-Stage Application Workflow
│   │   ├── saved_jobs.py           # Bookmarking & Save Interactions
│   │   ├── chat.py                 # 1-to-1 Real-time Messaging
│   │   ├── notifications.py        # Notification Alerts
│   │   ├── recommendations.py      # AI Recommendation & Simulation APIs
│   │   └── admin.py                # Admin Overview, Moderation & Weights
│   └── utils/
│       ├── geo.py                  # Haversine Algorithm Implementation
│       └── security.py             # Password Hashing & JWT Verification
│
├── frontend/
│   ├── index.html                  # Startup-Grade Landing Page
│   ├── login.html                  # Auth Login with 1-Click Persona Selectors
│   ├── register.html               # Student / Employer Dual Registration
│   ├── dashboard.html              # Student AI Recommendations Feed
│   ├── employer_dashboard.html     # Employer Job Postings & Applicant Review
│   ├── jobs.html                   # Leaflet Map Discovery & Search Filters
│   ├── job_details.html            # Deep Match Analysis & Application Modal
│   ├── profile.html                # Skills Tagger, Schedule Matrix, GPS Picker
│   ├── applications.html           # 5-Stage Visual Application Pipeline
│   ├── chat.html                   # 1-on-1 Employer-Student Chat
│   ├── admin.html                  # Admin KPI Dashboard & Weight Sliders
│   ├── ai_demo.html                # "How AI Matches You With Jobs" Interactive Lab
│   ├── css/
│   │   ├── style.css               # Core Design System
│   │   └── components.css          # Chat Bubbles, Pipeline, Map & Sliders
│   └── js/
│       └── api.js                  # Centralized Fetch Client & Session State
│
├── requirements.txt                # Python Dependencies
├── .env.example                    # Environment Configuration Template
└── README.md                       # Comprehensive Documentation
```

---

## 🚀 Quickstart Guide

### 1. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 2. (Optional) Re-seed Database
```bash
python seed.py
```
Pre-populates **20 students, 10 employers, 52 jobs with verified GPS coordinates, reviews, and dense interaction history**.

### 3. Run Automated Tests
```bash
python -m unittest discover tests
```
Runs the complete test suite (27 automated tests covering Auth, Jobs, Applications, AI Recommendation, RBAC Authorization, and End-to-End lifecycle).

### 4. Create or Reset Secure Admin Account
```bash
# Create/promote admin account with custom credentials:
python backend/create_admin.py --email vinaybandi651@gmail.com --password Admin@Secure2026 --name "Vinay Bandi"
# Or run interactively with hidden password inputs:
python backend/create_admin.py
```

### 5. Run the Automated Test Suite
```bash
# Runs full E2E test suite (Auth, Email Verification, Search/Filters, Admin Notification & Token Decision):
python backend/tests/test_full_suite.py
```

### 6. Run the Application
```bash
python backend/app.py
```

Open your browser to:
👉 **`http://127.0.0.1:5000`**

---

## 📬 Email-Based Application Approval Workflow

The portal features an automated email notification and review system:
1. **Application Submission:**
   - Candidate submits an application.
   - Status is initialized to **`pending`**.
   - An instant notification email is dispatched to **`vinaybandi651@gmail.com`**.
2. **Email Notification Content:**
   - Application reference code (e.g. `APP-2026-XXXXX`).
   - Candidate full name, verified email, degree, college, graduation year, target CTC, and resume link.
   - Job title, company name, compensation, and work arrangement.
   - Dual cryptographic single-use action buttons: **[Accept Candidate ✓]** and **[Reject Application ✕]**.
3. **Decision Confirmation:**
   - Clicking either button opens the secure verification screen (`confirm-action.html`).
   - Requiring a confirmation step protects against corporate email security scanners auto-triggering links.
   - The decision atomically updates the database status to `accepted` or `rejected`, sets `decided_by = vinaybandi651@gmail.com`, and records `decided_at`.
   - All sibling tokens for that application are permanently invalidated (single-use protection).
   - Applicant dashboard immediately displays **"Your application has been accepted 🎉"** or **"Your application has been rejected ✕"**.
   - The candidate is dispatched an official status update email.

### Setting Up Your Gmail SMTP App Password:
1. Go to your [Google Account Security Settings](https://myaccount.google.com/security).
2. Enable **2-Step Verification**.
3. Search for or open **App passwords**.
4. Generate an App Password for `GradMatch AI`.
5. Set your password either:
   - **Directly in Admin Dashboard:** Open `http://127.0.0.1:5000/admin.html` → scroll to **Gmail SMTP & Application Notifications** → paste the 16-character code → click **Save & Connect** → click **Send Live Test Email**!
   - **Or in `.env` / `backend/.env`:**
     ```env
     ADMIN_EMAIL=vinaybandi651@gmail.com
     SMTP_EMAIL=vinaybandi651@gmail.com
     SMTP_APP_PASSWORD=your_16_character_app_password
     APPLICATION_BASE_URL=http://127.0.0.1:5000
     ```
6. Run the live diagnostic tool:
   ```bash
   python backend/test_email.py
   ```
*(Note: If the password is not yet configured, the system operates in resilient development mode by storing emails and action tokens in `email_logs` and `action_tokens` to prevent application crashes).*

---

## 🚀 Production Deployment & Cross-Platform Support

The application is completely cross-platform (Windows, macOS, and Linux):

### 1. Environment Variables Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Key variables:
- `APPLICATION_BASE_URL`: Set to your deployed public domain (e.g. `https://your-domain.com`).
- `DATABASE_URL`: Set to PostgreSQL in production (e.g. `postgresql://user:password@host:5432/dbname`).
- `ADMIN_EMAIL`: `vinaybandi651@gmail.com`
- `SMTP_APP_PASSWORD`: Your 16-character Google App Password.

### 2. Running in Production with Gunicorn (Linux/macOS)
```bash
pip install gunicorn psycopg2-binary
gunicorn -w 4 -b 0.0.0.0:5000 "backend.app:create_app()"
```

### 3. Running with Waitress (Windows Production)
```bash
pip install waitress
python -c "from waitress import serve; from backend.app import create_app; serve(create_app(), host='0.0.0.0', port=5000)"
```

---

## 👥 Demo & Test Accounts

| Role | Email | Password | What to Observe |
|---|---|---|---|
| **Platform Administrator** | `vinaybandi651@gmail.com` | `Admin@Secure2026` | Admin dashboard, application moderation, AI weights, user metrics |
| **Tech Graduate (Aarav)** | `aarav.sharma@student.edu` | `Password@123` | Ranked #1: *Graduate Software Engineer* (92% Match) |
| **AI/ML Graduate (Priya)** | `priya.reddy@student.edu` | `Password@123` | Ranked #1: *Junior AI Engineer* (90% Match) |
| **Employer (ByteWave)** | `campus@bytewave.io` | `Password@123` | Review applicants, candidate resume links, accept/reject |

---

## 🛡️ Key REST API Endpoints

- `POST /api/auth/register`: User registration with strict validation
- `POST /api/auth/verify-email`: Account verification via token or OTP
- `POST /api/applications`: Submits job application (status initialized as `pending`, dispatches admin email)
- `GET /api/applications/my`: Candidate live application tracking
- `GET /api/applications/action/inspect`: Validates cryptographic email decision token
- `POST /api/applications/action/confirm`: Admin executes Accept/Reject from email
- `GET /api/admin/applications`: Admin panel application moderation and search
- `PATCH /api/applications/<id>/status`: Direct dashboard status override (Admin / Employer)
- `GET /api/jobs`: Filterable job search (keyword, distance radius, arrangement, fresher-friendly)

---

## 📜 Academic Attribution
Developed as a Major Capstone Project in Computer Science & Engineering (AI & Machine Learning Specialization).
