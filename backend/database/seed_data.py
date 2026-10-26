import json
import random
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from werkzeug.security import generate_password_hash
from database.db import get_db, init_db

# Geographic coordinates around Hyderabad Tech Corridors & Innovation Hubs (Lat: ~17.41 to ~17.49, Lon: ~78.34 to ~78.47)
LOCATIONS = [
    {"name": "Madhapur Tech Mindspace", "lat": 17.4483, "lon": 78.3915},
    {"name": "Hitec City Cyber Towers", "lat": 17.4504, "lon": 78.3808},
    {"name": "Gachibowli Financial District", "lat": 17.4168, "lon": 78.3428},
    {"name": "Kondapur IT Park", "lat": 17.4618, "lon": 78.3614},
    {"name": "Jubilee Hills Innovation Hub", "lat": 17.4319, "lon": 78.4073},
    {"name": "Banjara Hills Corporate Park", "lat": 17.4156, "lon": 78.4350},
    {"name": "Nanakramguda SEZ", "lat": 17.4225, "lon": 78.3385},
    {"name": "Kukatpally Tech Enclave", "lat": 17.4938, "lon": 78.3995},
    {"name": "Ameerpet Tech Centre", "lat": 17.4375, "lon": 78.4483},
    {"name": "Begumpet Tech Zone", "lat": 17.4441, "lon": 78.4721},
    {"name": "IIIT Hyderabad Knowledge Park", "lat": 17.4455, "lon": 78.3489},
    {"name": "Raidurg Metro Tech Corridor", "lat": 17.4348, "lon": 78.3872}
]

STUDENTS_DATA = [
    {
        "name": "Aarav Sharma", "email": "aarav.sharma@student.edu", "phone": "+91 9876543201",
        "degree": "B.Tech", "specialization": "Computer Science & Engineering",
        "college_name": "IIIT Hyderabad", "graduation_year": 2026,
        "fresher_status": "Fresher", "experience_level": "Fresher",
        "bio": "Aspiring Full-Stack Software Engineer with solid foundations in Data Structures, Python, Flask, React, and RESTful APIs. Passionate about scalable web systems.",
        "preferred_roles": ["Software Engineer", "Full Stack Developer", "Backend Developer"],
        "categories": ["Tech & IT", "Software Engineering"],
        "job_type": "Full-time", "expected_salary": 600000.0, "salary_type": "year",
        "max_distance": 15.0, "loc_idx": 10, "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "time_start": "09:00", "time_end": "18:00", "willingness_to_relocate": 1,
        "projects": "AI-Powered Hyperlocal Job Recommendation System with Flask and React; Scalable Microservices E-Commerce API with PostgreSQL",
        "skills": ["Python", "Flask", "React", "JavaScript", "SQL", "Git", "REST APIs"]
    },
    {
        "name": "Priya Reddy", "email": "priya.reddy@student.edu", "phone": "+91 9876543202",
        "degree": "B.Tech", "specialization": "Artificial Intelligence & Data Science",
        "college_name": "CBIT Hyderabad", "graduation_year": 2026,
        "fresher_status": "Fresher", "experience_level": "Fresher",
        "bio": "Data Science and Machine Learning graduate proficient in Python, Scikit-Learn, Pandas, SQL, and data visualization. Eager to solve real-world business problems.",
        "preferred_roles": ["Data Analyst", "Junior AI/ML Engineer", "Data Scientist Trainee"],
        "categories": ["Tech & IT", "Data & Analytics"],
        "job_type": "Full-time", "expected_salary": 550000.0, "salary_type": "year",
        "max_distance": 12.0, "loc_idx": 0, "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "time_start": "09:00", "time_end": "18:00", "willingness_to_relocate": 1,
        "projects": "Predictive Healthcare Triage System using Deep Learning; Customer Churn Prediction Dashboard with Streamlit and XGBoost",
        "skills": ["Python", "Machine Learning", "Pandas", "SQL", "Power BI", "Data Analysis", "Scikit-Learn"]
    },
    {
        "name": "Rohan Verma", "email": "rohan.verma@student.edu", "phone": "+91 9876543203",
        "degree": "BCA", "specialization": "Cloud & Web Applications",
        "college_name": "St. Francis College", "graduation_year": 2026,
        "fresher_status": "Fresher", "experience_level": "Fresher",
        "bio": "Enthusiastic Web and Cloud Developer trained in modern JavaScript, React.js, Node.js, and MongoDB. Looking for entry-level Software Developer roles.",
        "preferred_roles": ["Frontend Developer", "Junior Web Developer", "Software Engineer Trainee"],
        "categories": ["Tech & IT", "Software Engineering"],
        "job_type": "Full-time", "expected_salary": 450000.0, "salary_type": "year",
        "max_distance": 10.0, "loc_idx": 11, "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "time_start": "09:00", "time_end": "18:00", "willingness_to_relocate": 1,
        "projects": "Multi-Tenant Cloud Inventory Management System; Real-time Collaborative Markdown Editor in React & WebSockets",
        "skills": ["JavaScript", "React", "Node.js", "HTML5", "CSS3", "Tailwind CSS", "MongoDB"]
    },
    {
        "name": "Sneha Kulkarni", "email": "sneha.kulkarni@student.edu", "phone": "+91 9876543204",
        "degree": "MCA", "specialization": "Enterprise Software Engineering",
        "college_name": "JNTU Hyderabad", "graduation_year": 2026,
        "fresher_status": "Fresher", "experience_level": "Fresher",
        "bio": "Master of Computer Applications graduate with expertise in Java, Spring Boot, MySQL, and Docker. Strong understanding of Object-Oriented Design and Database Management.",
        "preferred_roles": ["Java Developer", "Backend Software Engineer", "Associate Software Engineer"],
        "categories": ["Tech & IT", "Software Engineering"],
        "job_type": "Full-time", "expected_salary": 650000.0, "salary_type": "year",
        "max_distance": 15.0, "loc_idx": 2, "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "time_start": "09:30", "time_end": "18:30", "willingness_to_relocate": 1,
        "projects": "Enterprise Banking Transaction Simulator using Spring Boot Microservices; Dockerized Distributed Caching System with Redis",
        "skills": ["Java", "Spring Boot", "MySQL", "Docker", "REST APIs", "Git", "Microservices"]
    },
    {
        "name": "Vikram Malhotra", "email": "vikram.m@student.edu", "phone": "+91 9876543205",
        "degree": "B.Com", "specialization": "Finance & Analytics",
        "college_name": "Bhavan's Vivekananda College", "graduation_year": 2026,
        "fresher_status": "Fresher", "experience_level": "Fresher",
        "bio": "Commerce graduate with keen interest in Corporate Finance, Financial Modeling, Advanced Excel, and TallyPrime. Detail-oriented and eager to join FinTech operations.",
        "preferred_roles": ["Financial Analyst Trainee", "FinTech Operations Associate", "Tax Associate"],
        "categories": ["Finance & FinTech", "Consulting & Operations"],
        "job_type": "Full-time", "expected_salary": 400000.0, "salary_type": "year",
        "max_distance": 12.0, "loc_idx": 4, "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "time_start": "09:00", "time_end": "18:00", "willingness_to_relocate": 1,
        "projects": "Financial Portfolio Risk & Variance Analysis using Monte Carlo Simulation in Excel; Comparative Ratio Analysis of Indian FinTech Sector",
        "skills": ["Financial Modeling", "Excel", "TallyPrime", "Accounting", "Corporate Finance", "GST Compliance"]
    },
    {
        "name": "Ananya Nair", "email": "ananya.nair@student.edu", "phone": "+91 9876543206",
        "degree": "BBA", "specialization": "Business Analytics & Marketing",
        "college_name": "Amity Global Business School", "graduation_year": 2026,
        "fresher_status": "Fresher", "experience_level": "Fresher",
        "bio": "Passionate Business graduate skilled in Market Research, Data Visualization with Tableau, and Growth Marketing. Exceptional communication and presentation skills.",
        "preferred_roles": ["Business Development Trainee", "Associate Product Specialist", "Marketing Trainee"],
        "categories": ["Consulting & Operations", "Marketing & Events"],
        "job_type": "Full-time", "expected_salary": 450000.0, "salary_type": "year",
        "max_distance": 12.0, "loc_idx": 3, "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "time_start": "09:00", "time_end": "18:00", "willingness_to_relocate": 1,
        "projects": "SaaS Product Go-To-Market Growth Strategy & Funnel Optimization; Digital Consumer Engagement Study for D2C Brands",
        "skills": ["Business Analysis", "Tableau", "Market Research", "Digital Marketing", "Communication", "Agile Scrum"]
    },
    {
        "name": "Karthik Iyer", "email": "karthik.iyer@student.edu", "phone": "+91 9876543207",
        "degree": "B.Tech", "specialization": "Information Technology",
        "college_name": "Vasavi College of Engineering", "graduation_year": 2025,
        "fresher_status": "Entry-Level", "experience_level": "Entry-Level",
        "bio": "Graduate software engineer with 6 months internship experience in QA Automation, Cypress, Selenium, and API testing. Strong focus on software reliability.",
        "preferred_roles": ["QA Automation Engineer", "Software Test Engineer", "SDET Trainee"],
        "categories": ["Tech & IT", "Software Engineering"],
        "job_type": "Full-time", "expected_salary": 480000.0, "salary_type": "year",
        "max_distance": 15.0, "loc_idx": 1, "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "time_start": "09:00", "time_end": "18:00", "willingness_to_relocate": 1,
        "projects": "Automated End-to-End Test Suite for E-Commerce Checkout using Cypress and Postman; Continuous Integration Pipeline with GitHub Actions",
        "skills": ["QA Automation", "Selenium", "Cypress", "Python", "JavaScript", "Jira", "Postman"]
    },
    {
        "name": "Divya Teja", "email": "divya.teja@student.edu", "phone": "+91 9876543208",
        "degree": "B.Sc", "specialization": "Data Science & Statistics",
        "college_name": "University of Hyderabad", "graduation_year": 2026,
        "fresher_status": "Fresher", "experience_level": "Fresher",
        "bio": "Analytical graduate with strong mathematical rigor, statistical inference, Python, R, and SQL. Ready for entry-level Business Intelligence and Data Analyst roles.",
        "preferred_roles": ["Data Analyst", "BI Developer Trainee", "Statistical Analyst"],
        "categories": ["Tech & IT", "Data & Analytics"],
        "job_type": "Full-time", "expected_salary": 500000.0, "salary_type": "year",
        "max_distance": 10.0, "loc_idx": 0, "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "time_start": "09:00", "time_end": "18:00", "willingness_to_relocate": 1,
        "projects": "Exploratory Data Analysis of Urban Air Quality Trends using Python and Plotly; Customer Segmentation Engine using K-Means Clustering",
        "skills": ["Python", "Statistics", "SQL", "Power BI", "Data Analysis", "Excel", "R"]
    },
    {
        "name": "Rahul Joshi", "email": "rahul.joshi@student.edu", "phone": "+91 9876543209",
        "degree": "B.Tech", "specialization": "Computer Science & Engineering",
        "college_name": "VNR VJIET", "graduation_year": 2026,
        "fresher_status": "Fresher", "experience_level": "Fresher",
        "bio": "Passionate Frontend & UI/UX Developer with solid skills in React, TypeScript, Tailwind CSS, Next.js, and Figma. Focused on creating intuitive digital experiences.",
        "preferred_roles": ["Frontend Developer", "UI/UX Engineer", "Web Developer"],
        "categories": ["Tech & IT", "Software Engineering"],
        "job_type": "Full-time", "expected_salary": 550000.0, "salary_type": "year",
        "max_distance": 15.0, "loc_idx": 7, "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "time_start": "09:00", "time_end": "18:00", "willingness_to_relocate": 1,
        "projects": "Responsive Healthcare Patient Portal with React & Tailwind; Component Design System built in Figma and Storybook",
        "skills": ["React", "TypeScript", "JavaScript", "Tailwind CSS", "Figma", "HTML5", "Git"]
    },
    {
        "name": "Meera Patel", "email": "meera.patel@student.edu", "phone": "+91 9876543210",
        "degree": "MBA", "specialization": "Human Resources & Talent Management",
        "college_name": "Osmania University", "graduation_year": 2026,
        "fresher_status": "Fresher", "experience_level": "Fresher",
        "bio": "MBA graduate specializing in HR analytics, recruitment life cycles, candidate engagement, and workplace policies. Driven to foster high-performance company cultures.",
        "preferred_roles": ["HR Trainee", "Talent Acquisition Associate", "HR Operations Executive"],
        "categories": ["Office & Administration", "Consulting & Operations"],
        "job_type": "Full-time", "expected_salary": 450000.0, "salary_type": "year",
        "max_distance": 10.0, "loc_idx": 5, "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "time_start": "09:00", "time_end": "18:00", "willingness_to_relocate": 1,
        "projects": "AI-Driven Candidate Screening & Retention Framework in Indian IT Startups; Employee Wellness & Engagement Analysis",
        "skills": ["Talent Acquisition", "HR Operations", "HR Analytics", "Communication", "Employee Engagement", "Excel"]
    },
    {
        "name": "Tanmay Deshmukh", "email": "tanmay.d@student.edu", "phone": "+91 9876543211",
        "degree": "Diploma", "specialization": "Computer Engineering",
        "college_name": "Government Polytechnic Masab Tank", "graduation_year": 2026,
        "fresher_status": "Fresher", "experience_level": "Fresher",
        "bio": "Polytechnic graduate with hands-on skills in Python programming, Linux server administration, network troubleshooting, and technical documentation.",
        "preferred_roles": ["Junior Systems Associate", "Technical Support Engineer", "Junior Python Developer"],
        "categories": ["Tech & IT", "Software Engineering"],
        "job_type": "Full-time", "expected_salary": 350000.0, "salary_type": "year",
        "max_distance": 12.0, "loc_idx": 8, "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "time_start": "09:00", "time_end": "18:00", "willingness_to_relocate": 1,
        "projects": "Automated Network Latency Monitor using Python & Bash; Campus Helpdesk Ticket Dispatcher Portal",
        "skills": ["Python", "Linux", "Networking", "Hardware Troubleshooting", "SQL", "Technical Support"]
    },
    {
        "name": "Kavya Menon", "email": "kavya.menon@student.edu", "phone": "+91 9876543212",
        "degree": "B.Com", "specialization": "Computer Applications & E-Commerce",
        "college_name": "Loyola Academy", "graduation_year": 2026,
        "fresher_status": "Fresher", "experience_level": "Fresher",
        "bio": "Commerce graduate proficient in spreadsheet analytics, billing workflows, database queries, and digital merchant onboarding.",
        "preferred_roles": ["Operations Associate", "Catalog Specialist", "Billing & MIS Executive"],
        "categories": ["Retail & Sales", "Office & Administration"],
        "job_type": "Full-time", "expected_salary": 380000.0, "salary_type": "year",
        "max_distance": 10.0, "loc_idx": 9, "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "time_start": "09:00", "time_end": "18:00", "willingness_to_relocate": 1,
        "projects": "Automated Vendor Payment Reconciliation in Excel; E-Commerce Marketplace Catalog Optimization System",
        "skills": ["Excel", "TallyPrime", "Billing", "Data Entry", "Inventory Management", "SQL Basics"]
    },
    {
        "name": "Siddharth Rao", "email": "siddharth.rao@student.edu", "phone": "+91 9876543213",
        "degree": "B.Tech", "specialization": "Electronics & Communication Engineering",
        "college_name": "Gokaraju Rangaraju Institute of Engineering", "graduation_year": 2026,
        "fresher_status": "Fresher", "experience_level": "Fresher",
        "bio": "Hardware-Software co-design enthusiast with skills in Embedded C, Microcontrollers, IoT protocols (MQTT, HTTP), and Python scripting.",
        "preferred_roles": ["Embedded Software Engineer", "IoT Systems Trainee", "Hardware Testing Engineer"],
        "categories": ["Tech & IT", "Software Engineering"],
        "job_type": "Full-time", "expected_salary": 500000.0, "salary_type": "year",
        "max_distance": 15.0, "loc_idx": 6, "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "time_start": "09:00", "time_end": "18:00", "willingness_to_relocate": 1,
        "projects": "Smart Environmental Monitoring Node with ESP32 & Cloud Dashboard; Automated Industrial Asset Tracking via BLE Beacons",
        "skills": ["Embedded C", "IoT", "Python", "Raspberry Pi", "Arduino", "Circuit Design", "Git"]
    },
    {
        "name": "Ritika Sen", "email": "ritika.sen@student.edu", "phone": "+91 9876543214",
        "degree": "BBA", "specialization": "Digital Marketing & Brand Communications",
        "college_name": "St. Joseph's Degree College", "graduation_year": 2026,
        "fresher_status": "Fresher", "experience_level": "Fresher",
        "bio": "Creative marketing graduate skilled in Search Engine Optimization, Meta Ads, Content Creation, Google Analytics, and Brand Storytelling.",
        "preferred_roles": ["Digital Marketing Associate", "Content Strategist", "SEO Trainee"],
        "categories": ["Marketing & Events", "Design & Creative"],
        "job_type": "Full-time", "expected_salary": 400000.0, "salary_type": "year",
        "max_distance": 12.0, "loc_idx": 4, "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "time_start": "09:00", "time_end": "18:00", "willingness_to_relocate": 1,
        "projects": "360-Degree Growth Marketing Campaign for an Organic D2C Startup; Organic SEO Strategy generating 50k monthly website impressions",
        "skills": ["Digital Marketing", "SEO Basics", "Content Writing", "Social Media", "Canva", "Google Analytics"]
    },
    {
        "name": "Arjun Kapoor", "email": "arjun.kapoor@student.edu", "phone": "+91 9876543215",
        "degree": "B.Tech", "specialization": "Computer Science (Cybersecurity)",
        "college_name": "JNTU College of Engineering", "graduation_year": 2026,
        "fresher_status": "Fresher", "experience_level": "Fresher",
        "bio": "Cybersecurity graduate with practical knowledge of Network Security, Penetration Testing concepts, Wireshark, Linux, and SOC monitoring fundamentals.",
        "preferred_roles": ["Cybersecurity Analyst Trainee", "SOC Analyst (L1)", "Information Security Associate"],
        "categories": ["Tech & IT", "Software Engineering"],
        "job_type": "Full-time", "expected_salary": 550000.0, "salary_type": "year",
        "max_distance": 15.0, "loc_idx": 0, "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "time_start": "09:00", "time_end": "18:00", "willingness_to_relocate": 1,
        "projects": "Vulnerability Assessment & Threat Modeling of Cloud Microservices; Automated Port Scanner and Network Packet Analyzer in Python",
        "skills": ["Cybersecurity", "Network Security", "Linux", "Python", "Wireshark", "Penetration Testing", "Ethical Hacking"]
    }
]

EMPLOYERS_DATA = [
    {
        "company": "ByteWave Technologies", "email": "careers@bytewave.io", "phone": "+91 9123456701",
        "type": "Tech & IT", "desc": "Fast-growing Enterprise SaaS and Cloud engineering company building high-scale developer platforms and AI tools.",
        "address": "Cyber Gateway, Hitec City, Hyderabad", "loc_idx": 1
    },
    {
        "company": "QuantEdge Financial Technologies", "email": "talent@quantedge.com", "phone": "+91 9123456702",
        "type": "Finance & FinTech", "desc": "FinTech enterprise powering algorithmic transaction routing, automated reconciliation, and banking API gateways.",
        "address": "Financial District, Nanakramguda, Hyderabad", "loc_idx": 2
    },
    {
        "company": "DataVerve Analytics", "email": "hiring@dataverve.ai", "phone": "+91 9123456703",
        "type": "Tech & IT", "desc": "Big Data and AI solutions consultancy helping Fortune 500 enterprises build modern analytics pipelines.",
        "address": "Mindspace IT Park, Madhapur, Hyderabad", "loc_idx": 0
    },
    {
        "company": "CloudPulse Systems", "email": "jobs@cloudpulse.net", "phone": "+91 9123456704",
        "type": "Tech & IT", "desc": "DevOps, Kubernetes orchestration, and Cloud infrastructure automation provider for global technology leaders.",
        "address": "Kondapur Botanical Garden Road, Hyderabad", "loc_idx": 3
    },
    {
        "company": "Nexus Commerce Labs", "email": "graduates@nexuscommerce.in", "phone": "+91 9123456705",
        "type": "Retail & E-commerce", "desc": "Omnichannel e-commerce enablement platform managing high-volume consumer catalogs and intelligent logistics.",
        "address": "Inorbit Mall Road, Raidurg, Hyderabad", "loc_idx": 11
    },
    {
        "company": "Spark Learning & EdTech", "email": "campus@sparklearning.com", "phone": "+91 9123456706",
        "type": "EdTech & Education", "desc": "Next-generation interactive learning platform offering adaptive STEM curriculums and student assessment systems.",
        "address": "Gachibowli Stadium Road, Hyderabad", "loc_idx": 2
    },
    {
        "company": "CyberAegis Security Solutions", "email": "soc@cyberaegis.com", "phone": "+91 9123456707",
        "type": "Tech & IT", "desc": "Managed Security Service Provider (MSSP) delivering 24/7 Security Operations Center (SOC) defense and threat mitigation.",
        "address": "Jubilee Hills Innovation Hub, Hyderabad", "loc_idx": 4
    },
    {
        "company": "CureSync HealthTech", "email": "careers@curesync.health", "phone": "+91 9123456708",
        "type": "Healthcare", "desc": "Healthcare SaaS provider digitizing electronic health records, teleconsultation workflows, and clinic management.",
        "address": "Road No 12, Banjara Hills, Hyderabad", "loc_idx": 5
    },
    {
        "company": "PixelCraft Creative Tech", "email": "hello@pixelcraft.agency", "phone": "+91 9123456709",
        "type": "Design & Creative", "desc": "Digital product design studio engineering modern web applications, mobile experiences, and enterprise design systems.",
        "address": "Ameerpet Metro Hub, Hyderabad", "loc_idx": 8
    },
    {
        "company": "Apex Global Operations", "email": "recruitment@apexoperations.in", "phone": "+91 9123456710",
        "type": "Consulting & Operations", "desc": "Strategic management and business process optimization consultancy serving IT and financial services corporations.",
        "address": "Kukatpally Housing Board Enclave, Hyderabad", "loc_idx": 7
    }
]

# 40+ Rich Entry-Level / Fresh Graduate Jobs
JOBS_DATA = [
    # ByteWave Technologies (Emp 0 - Hitec City)
    {
        "emp_idx": 0, "title": "Graduate Software Engineer Trainee", "cat": "Tech & IT", "type": "Full-time",
        "salary_min": 500000.0, "salary_max": 700000.0, "pay": 500000.0, "freq": "year",
        "min_qual": "B.Tech", "arrangement": "Hybrid", "fresher_friendly": 1, "min_exp": 0.0,
        "loc_idx": 1, "deadline": "2026-12-15",
        "desc": "Kickstart your software engineering career with ByteWave. Work directly with senior engineers to design, build, and deploy robust cloud microservices.",
        "responsibilities": "Develop backend services in Python and Go; Write comprehensive unit tests and automated integration tests; Participate in agile sprints and code reviews.",
        "eligibility": "B.Tech/B.E. in CSE, IT or allied branches (2025/2026 graduates); Strong grasp of Data Structures, Algorithms, and Object-Oriented Programming; Zero work experience required.",
        "skills": ["Python", "Flask", "SQL", "Git", "REST APIs", "Data Structures"]
    },
    {
        "emp_idx": 0, "title": "Associate React Frontend Developer", "cat": "Tech & IT", "type": "Full-time",
        "salary_min": 450000.0, "salary_max": 650000.0, "pay": 450000.0, "freq": "year",
        "min_qual": "BCA", "arrangement": "Remote", "fresher_friendly": 1, "min_exp": 0.0,
        "loc_idx": 1, "deadline": "2026-11-30",
        "desc": "Build responsive, high-performance web user interfaces for our flagship SaaS dashboard using React, TypeScript, and modern CSS frameworks.",
        "responsibilities": "Translate Figma designs into reusable React components; Integrate REST APIs and optimize client-side rendering speed; Ensure cross-browser compatibility.",
        "eligibility": "BCA, B.Tech, or B.Sc in Computer Science; Proficiency in HTML5, CSS3, JavaScript (ES6+), and React.js; Portfolio or GitHub projects demonstrating UI skills.",
        "skills": ["React", "JavaScript", "TypeScript", "Tailwind CSS", "HTML5", "Git"]
    },
    {
        "emp_idx": 0, "title": "Junior Python & Backend API Engineer", "cat": "Tech & IT", "type": "Full-time",
        "salary_min": 550000.0, "salary_max": 750000.0, "pay": 550000.0, "freq": "year",
        "min_qual": "MCA", "arrangement": "Hybrid", "fresher_friendly": 1, "min_exp": 0.0,
        "loc_idx": 1, "deadline": "2026-12-20",
        "desc": "Join our platform core team to engineer high-throughput APIs, database query optimizations, and background queue workers.",
        "responsibilities": "Architect RESTful and GraphQL endpoints; Implement caching with Redis and schema migrations in PostgreSQL; Monitor production API metrics.",
        "eligibility": "MCA or B.Tech graduates; Solid knowledge of Python web frameworks (Flask, FastAPI, or Django); Understanding of SQL database indexes and transactions.",
        "skills": ["Python", "FastAPI", "Flask", "PostgreSQL", "SQL", "Docker", "REST APIs"]
    },
    {
        "emp_idx": 0, "title": "Associate QA Automation Engineer", "cat": "Tech & IT", "type": "Full-time",
        "salary_min": 400000.0, "salary_max": 550000.0, "pay": 400000.0, "freq": "year",
        "min_qual": "Any Graduate", "arrangement": "Hybrid", "fresher_friendly": 1, "min_exp": 0.0,
        "loc_idx": 1, "deadline": "2026-11-28",
        "desc": "Ensure the highest software quality across our cloud apps. Write automated tests, report bugs, and execute continuous integration pipelines.",
        "responsibilities": "Develop end-to-end automated UI tests using Selenium or Cypress; Verify API contract endpoints using Postman; Collaborate with developers to reproduce edge cases.",
        "eligibility": "Graduates in B.Tech, BCA, B.Sc or related fields; Familiarity with Python or JavaScript testing frameworks; Strong analytical and debugging aptitude.",
        "skills": ["QA Automation", "Selenium", "Cypress", "Python", "Postman", "Git"]
    },

    # QuantEdge Financial Technologies (Emp 1 - Financial District)
    {
        "emp_idx": 1, "title": "Graduate Trainee - FinTech Operations", "cat": "Finance & FinTech", "type": "Full-time",
        "salary_min": 420000.0, "salary_max": 580000.0, "pay": 420000.0, "freq": "year",
        "min_qual": "B.Com", "arrangement": "On-site", "fresher_friendly": 1, "min_exp": 0.0,
        "loc_idx": 2, "deadline": "2026-12-10",
        "desc": "Support real-time payment reconciliation, merchant settlement operations, and regulatory audit compliance in a high-growth FinTech hub.",
        "responsibilities": "Reconcile daily automated settlement files across partner banks; Investigate transaction anomalies; Maintain audit documentation and management reports.",
        "eligibility": "B.Com, BBA, or MBA in Finance (2025/2026 passed out); Advanced command of MS Excel (VLOOKUP, Pivot Tables, Formulas); High numerical accuracy.",
        "skills": ["Financial Modeling", "Excel", "Accounting", "Corporate Finance", "Billing"]
    },
    {
        "emp_idx": 1, "title": "Associate Java Developer - Core Banking", "cat": "Tech & IT", "type": "Full-time",
        "salary_min": 600000.0, "salary_max": 850000.0, "pay": 600000.0, "freq": "year",
        "min_qual": "B.Tech", "arrangement": "On-site", "fresher_friendly": 1, "min_exp": 0.0,
        "loc_idx": 2, "deadline": "2026-12-05",
        "desc": "Develop mission-critical banking ledger services, concurrency handlers, and secure payment APIs utilizing Java and Spring Boot.",
        "responsibilities": "Write clean, test-driven Java code; Handle multi-threaded transaction requests; Implement encryption and security protocols for sensitive financial records.",
        "eligibility": "B.Tech/MCA fresh graduates with strong Java fundamentals, OOP concepts, and SQL knowledge; 0 years experience required.",
        "skills": ["Java", "Spring Boot", "MySQL", "SQL", "Git", "Microservices"]
    },
    {
        "emp_idx": 1, "title": "Junior Financial Risk Analyst", "cat": "Finance & FinTech", "type": "Full-time",
        "salary_min": 450000.0, "salary_max": 620000.0, "pay": 450000.0, "freq": "year",
        "min_qual": "MBA", "arrangement": "Hybrid", "fresher_friendly": 1, "min_exp": 0.0,
        "loc_idx": 2, "deadline": "2026-12-15",
        "desc": "Analyze credit portfolios, detect fraud patterns, and evaluate risk models under the mentorship of senior risk strategists.",
        "responsibilities": "Build financial risk reports and scenario models; Query SQL databases to uncover payment anomalies; Prepare executive summaries for audit committees.",
        "eligibility": "MBA in Finance, M.Com, or B.Tech with financial interest; Working familiarity with SQL, Excel, and financial ratios.",
        "skills": ["Financial Modeling", "Excel", "SQL", "Data Analysis", "Corporate Finance"]
    },

    # DataVerve Analytics (Emp 2 - Madhapur)
    {
        "emp_idx": 2, "title": "Associate Data Analyst - Business Intelligence", "cat": "Tech & IT", "type": "Full-time",
        "salary_min": 480000.0, "salary_max": 680000.0, "pay": 480000.0, "freq": "year",
        "min_qual": "Any Graduate", "arrangement": "Remote", "fresher_friendly": 1, "min_exp": 0.0,
        "loc_idx": 0, "deadline": "2026-12-08",
        "desc": "Transform raw business metrics into actionable visual dashboards. Work with marketing, operations, and leadership teams to answer key business questions.",
        "responsibilities": "Write complex SQL queries to extract data; Design interactive dashboards in Power BI and Tableau; Cleanse and validate dataset hygiene.",
        "eligibility": "Any Graduate (B.Tech, B.Sc, BCA, B.Com, BBA) with strong SQL, Excel, and data visualization capabilities; Passion for data storytelling.",
        "skills": ["SQL", "Power BI", "Python", "Tableau", "Data Analysis", "Excel"]
    },
    {
        "emp_idx": 2, "title": "Junior Machine Learning Engineer Trainee", "cat": "Tech & IT", "type": "Full-time",
        "salary_min": 600000.0, "salary_max": 900000.0, "pay": 600000.0, "freq": "year",
        "min_qual": "B.Tech", "arrangement": "Hybrid", "fresher_friendly": 1, "min_exp": 0.0,
        "loc_idx": 0, "deadline": "2026-12-18",
        "desc": "Train, evaluate, and deploy real-world machine learning models for customer segmentation, churn prediction, and recommendation engines.",
        "responsibilities": "Perform feature engineering and exploratory data analysis; Train models using Scikit-Learn and PyTorch; Deploy prediction APIs using FastAPI.",
        "eligibility": "B.Tech in Computer Science, AI, Data Science or allied fields; Proficient in Python, NumPy, Pandas, and machine learning foundations; Freshers welcome.",
        "skills": ["Python", "Machine Learning", "Pandas", "Scikit-Learn", "SQL", "Git"]
    },
    {
        "emp_idx": 2, "title": "Junior Data Engineer - ETL Pipelines", "cat": "Tech & IT", "type": "Full-time",
        "salary_min": 520000.0, "salary_max": 720000.0, "pay": 520000.0, "freq": "year",
        "min_qual": "B.Tech", "arrangement": "On-site", "fresher_friendly": 1, "min_exp": 0.0,
        "loc_idx": 0, "deadline": "2026-12-12",
        "desc": "Construct automated data pipelines to ingest, transform, and load enterprise data into cloud data warehouses.",
        "responsibilities": "Write Python scripts and SQL transformations; Schedule automated data sync workflows; Monitor pipeline latency and data integrity.",
        "eligibility": "B.Tech or MCA graduate; Excellent SQL proficiency; Knowledge of Python data scripting and database design.",
        "skills": ["Python", "SQL", "PostgreSQL", "Data Analysis", "Git", "Linux"]
    },

    # CloudPulse Systems (Emp 3 - Kondapur)
    {
        "emp_idx": 3, "title": "Junior Cloud & DevOps Engineer", "cat": "Tech & IT", "type": "Full-time",
        "salary_min": 500000.0, "salary_max": 750000.0, "pay": 500000.0, "freq": "year",
        "min_qual": "B.Tech", "arrangement": "Hybrid", "fresher_friendly": 1, "min_exp": 0.0,
        "loc_idx": 3, "deadline": "2026-12-15",
        "desc": "Automate cloud infrastructure deployments, container workflows with Docker, and CI/CD pipelines on AWS and Linux environments.",
        "responsibilities": "Configure Docker containers and Kubernetes manifests; Build CI/CD automation in GitHub Actions; Monitor cloud server health and alarms.",
        "eligibility": "B.Tech in CSE, IT, ECE or Diploma in Computer Engineering; Hands-on Linux command-line skills; Familiarity with Docker and basic networking.",
        "skills": ["Linux", "Docker", "Git", "Python", "Networking", "Technical Support"]
    },
    {
        "emp_idx": 3, "title": "Associate Systems & Network Administrator", "cat": "Tech & IT", "type": "Full-time",
        "salary_min": 360000.0, "salary_max": 500000.0, "pay": 360000.0, "freq": "year",
        "min_qual": "Diploma", "arrangement": "On-site", "fresher_friendly": 1, "min_exp": 0.0,
        "loc_idx": 3, "deadline": "2026-11-25",
        "desc": "Maintain corporate internal networks, VPN gateways, server racks, and provide technical troubleshooting to engineering teams.",
        "responsibilities": "Troubleshoot LAN/WAN connections and DNS issues; Provision employee laptops with security patches; Document network topologies.",
        "eligibility": "Polytechnic Diploma in Computer Engineering/IT or B.Sc; Understanding of TCP/IP, subnets, routers, and Linux commands.",
        "skills": ["Networking", "Linux", "Hardware Troubleshooting", "Technical Support"]
    },

    # Nexus Commerce Labs (Emp 4 - Raidurg)
    {
        "emp_idx": 4, "title": "Associate Full Stack Developer", "cat": "Tech & IT", "type": "Full-time",
        "salary_min": 520000.0, "salary_max": 750000.0, "pay": 520000.0, "freq": "year",
        "min_qual": "B.Tech", "arrangement": "Hybrid", "fresher_friendly": 1, "min_exp": 0.0,
        "loc_idx": 11, "deadline": "2026-12-22",
        "desc": "Build customer-facing e-commerce shopping carts, checkout microservices, and partner integrations using modern JavaScript and Python.",
        "responsibilities": "Develop React UI modules and Python/Node backend endpoints; Optimize checkout latency; Write unit tests and maintain documentation.",
        "eligibility": "B.Tech, BCA, or MCA fresh graduates; Strong grasp of JavaScript, React, RESTful architectures, and SQL databases.",
        "skills": ["React", "JavaScript", "Python", "Node.js", "SQL", "Git"]
    },
    {
        "emp_idx": 4, "title": "Junior Business Development Trainee", "cat": "Consulting & Operations", "type": "Full-time",
        "salary_min": 400000.0, "salary_max": 600000.0, "pay": 400000.0, "freq": "year",
        "min_qual": "BBA", "arrangement": "On-site", "fresher_friendly": 1, "min_exp": 0.0,
        "loc_idx": 11, "deadline": "2026-12-01",
        "desc": "Engage retail merchants and brand sellers, demonstrate platform capabilities, and drive new seller onboarding.",
        "responsibilities": "Conduct outbound outreach to prospective brands; Deliver product demonstrations; Track lead conversion metrics in CRM.",
        "eligibility": "BBA, B.Com, or MBA fresh graduates; Energetic communication, negotiation, and relationship-building abilities.",
        "skills": ["Business Analysis", "Communication", "Market Research", "Digital Marketing", "Public Speaking"]
    },
    {
        "emp_idx": 4, "title": "Catalog & Operations Specialist", "cat": "Retail & Sales", "type": "Full-time",
        "salary_min": 350000.0, "salary_max": 480000.0, "pay": 350000.0, "freq": "year",
        "min_qual": "Any Graduate", "arrangement": "On-site", "fresher_friendly": 1, "min_exp": 0.0,
        "loc_idx": 11, "deadline": "2026-11-28",
        "desc": "Verify e-commerce product listings, audit metadata specifications, and manage merchant catalog inventory feeds.",
        "responsibilities": "Review bulk catalog uploads for accuracy; Cleanse product titles and attribute tags; Coordinate with category managers.",
        "eligibility": "Any Graduate; Good command of MS Excel, data entry speed, and sharp eye for detail.",
        "skills": ["Excel", "Inventory Management", "Data Entry", "Attention to Detail"]
    },

    # Spark Learning & EdTech (Emp 5 - Gachibowli)
    {
        "emp_idx": 5, "title": "Graduate STEM Curriculum Developer", "cat": "EdTech & Education", "type": "Full-time",
        "salary_min": 420000.0, "salary_max": 600000.0, "pay": 420000.0, "freq": "year",
        "min_qual": "B.Sc", "arrangement": "Remote", "fresher_friendly": 1, "min_exp": 0.0,
        "loc_idx": 2, "deadline": "2026-12-10",
        "desc": "Design engaging computer science and mathematics problem sets, interactive animations, and coding exercises for student learners.",
        "responsibilities": "Author step-by-step coding tutorials in Python and Scratch; Review technical curriculum for clarity; Build quiz question banks.",
        "eligibility": "B.Sc, B.Tech, or MCA with strong foundational understanding of programming and mathematical concepts; Clear written English.",
        "skills": ["Python", "Tutoring", "Mathematics", "Content Writing", "Mentorship"]
    },
    {
        "emp_idx": 5, "title": "Junior Academic Operations Coordinator", "cat": "Office & Administration", "type": "Full-time",
        "salary_min": 360000.0, "salary_max": 480000.0, "pay": 360000.0, "freq": "year",
        "min_qual": "Any Graduate", "arrangement": "Hybrid", "fresher_friendly": 1, "min_exp": 0.0,
        "loc_idx": 2, "deadline": "2026-11-30",
        "desc": "Coordinate student batch schedules, manage virtual classroom links, resolve parent inquiries, and track course completion records.",
        "responsibilities": "Maintain student enrollment databases; Resolve tier-1 scheduling queries via chat and email; Generate attendance reports.",
        "eligibility": "Any Graduate; Empathetic interpersonal skills and proficiency in Google Workspace and Excel.",
        "skills": ["Communication", "Customer Support", "Excel", "Record Keeping"]
    },

    # CyberAegis Security (Emp 6 - Jubilee Hills)
    {
        "emp_idx": 6, "title": "Junior Cybersecurity Analyst (L1 SOC)", "cat": "Tech & IT", "type": "Full-time",
        "salary_min": 480000.0, "salary_max": 680000.0, "pay": 480000.0, "freq": "year",
        "min_qual": "B.Tech", "arrangement": "Hybrid", "fresher_friendly": 1, "min_exp": 0.0,
        "loc_idx": 4, "deadline": "2026-12-15",
        "desc": "Monitor real-time SIEM alerts, detect unauthorized network intrusions, and assist senior incident responders in cyber threat containment.",
        "responsibilities": "Investigate security alerts in Splunk/Wazuh; Verify phishing email reports; Document incident remediation workflows.",
        "eligibility": "B.Tech in CSE/IT or Diploma in Computer Engineering; Familiarity with OSI layers, TCP/IP, Wireshark, and Linux security basics.",
        "skills": ["Cybersecurity", "Network Security", "Linux", "Python", "Wireshark"]
    },
    {
        "emp_idx": 6, "title": "Information Security & Compliance Associate", "cat": "Tech & IT", "type": "Full-time",
        "salary_min": 420000.0, "salary_max": 580000.0, "pay": 420000.0, "freq": "year",
        "min_qual": "Any Graduate", "arrangement": "On-site", "fresher_friendly": 1, "min_exp": 0.0,
        "loc_idx": 4, "deadline": "2026-11-25",
        "desc": "Help enterprise clients assess their cybersecurity posture, verify ISO 27001 policies, and ensure data privacy compliance.",
        "responsibilities": "Conduct security policy checklist audits; Review user access permissions; Prepare compliance evidence folders.",
        "eligibility": "Any Graduate with keen interest in Information Security, audits, and risk governance; Analytical mindset.",
        "skills": ["Cybersecurity", "Excel", "Attention to Detail", "Documentation"]
    },

    # CureSync HealthTech (Emp 7 - Banjara Hills)
    {
        "emp_idx": 7, "title": "Junior Healthcare Software Engineer", "cat": "Tech & IT", "type": "Full-time",
        "salary_min": 480000.0, "salary_max": 700000.0, "pay": 480000.0, "freq": "year",
        "min_qual": "B.Tech", "arrangement": "Hybrid", "fresher_friendly": 1, "min_exp": 0.0,
        "loc_idx": 5, "deadline": "2026-12-20",
        "desc": "Develop HIPAA-compliant electronic medical record workflows, doctor scheduling modules, and patient communication portals.",
        "responsibilities": "Write clean React and Python code; Ensure end-to-end data encryption; Integrate healthcare messaging APIs.",
        "eligibility": "B.Tech, BCA, or MCA graduates with passion for digital health systems; Good command of web technologies.",
        "skills": ["Python", "React", "JavaScript", "SQL", "Git"]
    },
    {
        "emp_idx": 7, "title": "Associate Clinical Data Coordinator", "cat": "Office & Administration", "type": "Full-time",
        "salary_min": 360000.0, "salary_max": 500000.0, "pay": 360000.0, "freq": "year",
        "min_qual": "B.Sc", "arrangement": "On-site", "fresher_friendly": 1, "min_exp": 0.0,
        "loc_idx": 5, "deadline": "2026-11-28",
        "desc": "Ensure electronic health trial records and patient diagnostic logs are accurately catalogued and securely maintained.",
        "responsibilities": "Validate patient intake forms; Check medical coding terminology for discrepancies; Prepare monthly clinical trial summaries.",
        "eligibility": "B.Sc in Life Sciences, Biotechnology, or Statistics; High degree of accuracy and confidentiality ethics.",
        "skills": ["Record Keeping", "Excel", "Attention to Detail", "Data Entry"]
    },

    # PixelCraft Creative Tech (Emp 8 - Ameerpet)
    {
        "emp_idx": 8, "title": "Associate UI/UX & Product Designer", "cat": "Design & Creative", "type": "Full-time",
        "salary_min": 450000.0, "salary_max": 650000.0, "pay": 450000.0, "freq": "year",
        "min_qual": "Any Graduate", "arrangement": "Remote", "fresher_friendly": 1, "min_exp": 0.0,
        "loc_idx": 8, "deadline": "2026-12-15",
        "desc": "Design user flows, wireframes, and pixel-perfect interactive prototypes for mobile apps and web platforms in Figma.",
        "responsibilities": "Create wireframes, high-fidelity mockups, and interactive prototypes; Maintain shared Figma design component libraries; Conduct user usability sessions.",
        "eligibility": "Any Graduate with a portfolio demonstrating UI/UX sensibilities, Figma proficiency, and design typography.",
        "skills": ["Figma", "UI Design", "Graphic Design", "HTML5", "Creativity"]
    },
    {
        "emp_idx": 8, "title": "Junior Digital Content & Growth Associate", "cat": "Marketing & Events", "type": "Full-time",
        "salary_min": 360000.0, "salary_max": 520000.0, "pay": 360000.0, "freq": "year",
        "min_qual": "BBA", "arrangement": "Remote", "fresher_friendly": 1, "min_exp": 0.0,
        "loc_idx": 8, "deadline": "2026-12-05",
        "desc": "Craft compelling brand narratives, technical blog articles, product newsletters, and manage social media growth channels.",
        "responsibilities": "Write SEO-optimized blog posts; Manage LinkedIn and Twitter company profiles; Create visual carousels using Canva.",
        "eligibility": "BBA, B.A. Mass Comm, or B.Com graduates; Outstanding written English, copywriting, and storytelling flair.",
        "skills": ["Content Writing", "Copywriting", "Digital Marketing", "SEO Basics", "Social Media", "Canva"]
    },

    # Apex Global Operations (Emp 9 - Kukatpally)
    {
        "emp_idx": 9, "title": "Associate HR & Talent Acquisition Trainee", "cat": "Office & Administration", "type": "Full-time",
        "salary_min": 380000.0, "salary_max": 520000.0, "pay": 380000.0, "freq": "year",
        "min_qual": "MBA", "arrangement": "Hybrid", "fresher_friendly": 1, "min_exp": 0.0,
        "loc_idx": 7, "deadline": "2026-12-10",
        "desc": "Source high-potential graduate talent, screen resumes, schedule technical interviews, and assist with campus placement drives.",
        "responsibilities": "Screen incoming candidate profiles; Coordinate interview panels across departments; Maintain candidate pipeline trackers in Excel.",
        "eligibility": "MBA in HR, BBA, or Any Graduate with strong interpersonal communications and organizational prowess.",
        "skills": ["Talent Acquisition", "HR Operations", "Communication", "Excel", "Employee Engagement"]
    },
    {
        "emp_idx": 9, "title": "Management Consulting Analyst Trainee", "cat": "Consulting & Operations", "type": "Full-time",
        "salary_min": 450000.0, "salary_max": 650000.0, "pay": 450000.0, "freq": "year",
        "min_qual": "BBA", "arrangement": "On-site", "fresher_friendly": 1, "min_exp": 0.0,
        "loc_idx": 7, "deadline": "2026-12-18",
        "desc": "Support client consulting engagements by conducting competitive industry benchmarking, process flow mapping, and data synthesis.",
        "responsibilities": "Gather qualitative and quantitative industry data; Build executive PowerPoint presentation decks; Assist in project milestone tracking.",
        "eligibility": "BBA, B.Com, MBA, or B.Tech graduates; Strong structured thinking, problem solving, and slide building abilities.",
        "skills": ["Business Analysis", "Market Research", "Excel", "Communication", "Agile Scrum"]
    }
]

def seed_database(force=False):
    """Populate database with rich realistic data for testing and demonstration."""
    init_db()

    with get_db() as conn:
        cursor = conn.cursor()

        # Check if already seeded
        if force:
            tables = [
                'recommendations', 'reviews', 'messages', 'conversations',
                'notifications', 'job_interactions', 'saved_jobs', 'applications',
                'job_skills', 'jobs', 'student_skills', 'availabilities',
                'student_profiles', 'employer_profiles', 'locations', 'skills', 'users'
            ]
            for t in tables:
                try:
                    cursor.execute(f"DELETE FROM {t}")
                except Exception:
                    pass
        else:
            cursor.execute("SELECT COUNT(*) FROM users")
            if cursor.fetchone()[0] > 5:
                print("Database already contains data. Skipping re-seed.")
                return

        print("Seeding database with realistic graduate profiles, employers, and jobs...")

        # 0. Insert master Locations
        for loc in LOCATIONS:
            cursor.execute("""
                INSERT OR IGNORE INTO locations (name, area, city, latitude, longitude)
                VALUES (?, ?, 'Hyderabad', ?, ?)
            """, (loc['name'], loc['name'].split()[0], loc['lat'], loc['lon']))

        # 1. Insert Admin user
        admin_pass = generate_password_hash("Admin@123")
        cursor.execute("""
            INSERT INTO users (email, password_hash, role, full_name, phone, avatar_url, is_verified)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, ("admin@hyperlocaljobs.com", admin_pass, "admin", "System Administrator", "+91 9999900000", None))

        # 2. Insert Employers
        employer_ids = []
        default_pwd = generate_password_hash("Password@123")

        for emp in EMPLOYERS_DATA:
            loc = LOCATIONS[emp['loc_idx']]
            cursor.execute("""
                INSERT INTO users (email, password_hash, role, full_name, phone, avatar_url, is_verified)
                VALUES (?, ?, 'employer', ?, ?, ?, 1)
            """, (emp['email'], default_pwd, emp['company'], emp['phone'], None))
            u_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO employer_profiles (user_id, company_name, business_type, description, address, latitude, longitude, verified)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """, (u_id, emp['company'], emp['type'], emp['desc'], emp['address'], loc['lat'], loc['lon']))
            employer_ids.append(cursor.lastrowid)

        # 3. Insert Students & Profiles & Skills
        student_ids = []
        for s in STUDENTS_DATA:
            loc = LOCATIONS[s['loc_idx']]
            cursor.execute("""
                INSERT INTO users (email, password_hash, role, full_name, phone, avatar_url, is_verified)
                VALUES (?, ?, 'student', ?, ?, ?, 1)
            """, (s['email'], default_pwd, s['name'], s['phone'], None))
            u_id = cursor.lastrowid

            education_text = f"{s['degree']} in {s['specialization']}"

            cursor.execute("""
                INSERT INTO student_profiles (
                    user_id, education, institution, experience_level, bio,
                    preferred_categories, preferred_job_type, expected_salary, salary_type,
                    max_distance_km, latitude, longitude, address,
                    available_days, available_time_start, available_time_end, profile_completed,
                    degree, specialization, college_name, graduation_year, fresher_status,
                    preferred_roles, willingness_to_relocate, projects
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                u_id, education_text, s['college_name'], s['experience_level'], s['bio'],
                json.dumps(s['categories']), s['job_type'], s['expected_salary'], s['salary_type'],
                s['max_distance'], loc['lat'], loc['lon'], loc['name'],
                json.dumps(s['days']), s['time_start'], s['time_end'],
                s['degree'], s['specialization'], s['college_name'], s['graduation_year'], s['fresher_status'],
                json.dumps(s['preferred_roles']), s['willingness_to_relocate'], s['projects']
            ))
            s_profile_id = cursor.lastrowid
            student_ids.append(s_profile_id)

            # Insert student skills and master skills
            for sk in s['skills']:
                cursor.execute("""
                    INSERT OR IGNORE INTO skills (name, category) VALUES (?, ?)
                """, (sk, s['categories'][0] if s['categories'] else 'General'))
                cursor.execute("""
                    INSERT INTO student_skills (student_id, skill_name, proficiency)
                    VALUES (?, ?, 'Intermediate')
                """, (s_profile_id, sk))

            # Insert student availabilities
            for day in s['days']:
                cursor.execute("""
                    INSERT INTO availabilities (student_id, day_of_week, start_time, end_time)
                    VALUES (?, ?, ?, ?)
                """, (s_profile_id, day, s['time_start'], s['time_end']))

        # 4. Insert Jobs & Job Skills
        job_ids = []
        for j in JOBS_DATA:
            emp_profile_id = employer_ids[j['emp_idx']]
            loc = LOCATIONS[j['loc_idx']]

            cursor.execute("""
                INSERT INTO jobs (
                    employer_id, title, description, category, job_type,
                    pay_amount, pay_frequency, date_needed, start_time, end_time,
                    workers_needed, experience_required, location_address,
                    latitude, longitude, application_deadline, status,
                    min_qualification, work_arrangement, is_fresher_friendly,
                    min_experience_years, salary_min, salary_max,
                    responsibilities, eligibility
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                emp_profile_id, j['title'], j['desc'], j['cat'], j['type'],
                j['pay'], j['freq'], 'Immediate', '09:00', '18:00',
                2, f"Fresher / {int(j['min_exp'])} Years", loc['name'],
                loc['lat'], loc['lon'], j['deadline'],
                j['min_qual'], j['arrangement'], j['fresher_friendly'],
                j['min_exp'], j['salary_min'], j['salary_max'],
                j['responsibilities'], j['eligibility']
            ))
            job_id = cursor.lastrowid
            job_ids.append(job_id)

            for sk in j['skills']:
                cursor.execute("""
                    INSERT OR IGNORE INTO skills (name, category) VALUES (?, ?)
                """, (sk, j['cat']))
                cursor.execute("""
                    INSERT INTO job_skills (job_id, skill_name)
                    VALUES (?, ?)
                """, (job_id, sk))

        # 5. Insert Realistic Student-Job Interactions & Applications
        # Aarav (Student 0 - Tech focus): Interacts with Python, React, Web Dev jobs
        # Priya (Student 1 - Data Science): Interacts with ML, Data Analyst, SQL jobs
        # Rohan (Student 2 - BCA): Interacts with Frontend, Full Stack, Web jobs
        # Sneha (Student 3 - MCA): Interacts with Java, Backend, Cloud jobs

        for idx in [0, 1, 2, 8, 12]:
            if idx < len(job_ids):
                jid = job_ids[idx]
                cursor.execute("INSERT INTO job_interactions (student_id, job_id, interaction_type, interaction_weight) VALUES (?, ?, 'VIEW_JOB', 1)", (student_ids[0], jid))
                cursor.execute("INSERT INTO job_interactions (student_id, job_id, interaction_type, interaction_weight) VALUES (?, ?, 'SAVE_JOB', 3)", (student_ids[0], jid))
                if idx in [0, 2]:
                    ref_code = f"APP-2026-{random.randint(10000, 99999)}"
                    cursor.execute("INSERT INTO job_interactions (student_id, job_id, interaction_type, interaction_weight) VALUES (?, ?, 'APPLY_JOB', 5)", (student_ids[0], jid))
                    cursor.execute("""
                        INSERT INTO applications (job_id, student_id, cover_note, status, reference_code, status_notes)
                        VALUES (?, ?, 'Excited to contribute my Full-Stack Python and React skills to ByteWave! Portfolio projects demonstrate REST API proficiency.', 'shortlisted', ?, 'Candidate profile matches tech requirements. Scheduled for technical interview.')
                    """, (jid, student_ids[0], ref_code))

        for idx in [1, 7, 8, 9]:
            if idx < len(job_ids):
                jid = job_ids[idx]
                cursor.execute("INSERT INTO job_interactions (student_id, job_id, interaction_type, interaction_weight) VALUES (?, ?, 'VIEW_JOB', 1)", (student_ids[1], jid))
                if idx in [7, 8]:
                    ref_code = f"APP-2026-{random.randint(10000, 99999)}"
                    cursor.execute("INSERT INTO job_interactions (student_id, job_id, interaction_type, interaction_weight) VALUES (?, ?, 'APPLY_JOB', 5)", (student_ids[1], jid))
                    cursor.execute("""
                        INSERT INTO applications (job_id, student_id, cover_note, status, reference_code, status_notes)
                        VALUES (?, ?, 'Passionate about machine learning and data pipelines. Looking forward to discussing analytical projects.', 'accepted', ?, 'Welcome to the team! Offer letter dispatched.')
                    """, (jid, student_ids[1], ref_code))

        # Add more random background interactions for collaborative filtering density
        for s_idx in range(2, len(student_ids)):
            sid = student_ids[s_idx]
            random_sample = random.sample(job_ids, k=min(len(job_ids), random.randint(5, 10)))
            for jid in random_sample:
                weight = random.choice([1, 1, 2, 3, 5])
                itype = 'VIEW_JOB' if weight == 1 else ('SEARCH_JOB' if weight == 2 else ('SAVE_JOB' if weight == 3 else 'APPLY_JOB'))
                cursor.execute("INSERT INTO job_interactions (student_id, job_id, interaction_type, interaction_weight) VALUES (?, ?, ?, ?)", (sid, jid, itype, weight))
                if weight == 5:
                    ref_code = f"APP-2026-{random.randint(10000, 99999)}"
                    cursor.execute("""
                        INSERT OR IGNORE INTO applications (job_id, student_id, cover_note, status, reference_code)
                        VALUES (?, ?, 'Interested in this graduate position and eligible according to degree requirements.', 'applied', ?)
                    """, (jid, sid, ref_code))

        # 6. Insert Sample Messages and Conversations between Student and Employer
        cursor.execute("SELECT user_id FROM employer_profiles WHERE id = ?", (employer_ids[0],))
        emp0_user_id = cursor.fetchone()[0]
        cursor.execute("SELECT user_id FROM student_profiles WHERE id = ?", (student_ids[0],))
        stud0_user_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO conversations (job_id, user1_id, user2_id)
            VALUES (?, ?, ?)
        """, (job_ids[0], emp0_user_id, stud0_user_id))

        cursor.execute("""
            INSERT INTO messages (job_id, sender_id, receiver_id, message_text, is_read)
            VALUES (?, ?, ?, 'Hi Aarav, we reviewed your Graduate Software Engineer application. Your Python and Flask projects look impressive. Are you available for a video discussion tomorrow?', 1)
        """, (job_ids[0], emp0_user_id, stud0_user_id))

        cursor.execute("""
            INSERT INTO messages (job_id, sender_id, receiver_id, message_text, is_read)
            VALUES (?, ?, ?, 'Thank you! Yes absolutely, I would be delighted to join. Looking forward to speaking with the engineering team.', 1)
        """, (job_ids[0], stud0_user_id, emp0_user_id))

        # 7. Insert Reviews
        cursor.execute("""
            INSERT INTO reviews (job_id, reviewer_id, reviewee_id, rating, comment)
            VALUES (?, ?, ?, 5.0, 'Aarav demonstrated exceptional problem-solving and rapid learning during his technical assessment.')
        """, (job_ids[0], emp0_user_id, stud0_user_id))

        cursor.execute("""
            INSERT INTO reviews (job_id, reviewer_id, reviewee_id, rating, comment)
            VALUES (?, ?, ?, 4.9, 'ByteWave has an outstanding engineering culture and clear mentorship for graduate trainees.')
        """, (job_ids[0], stud0_user_id, emp0_user_id))

        # 8. Insert Notifications
        cursor.execute("""
            INSERT INTO notifications (user_id, title, message, type, link)
            VALUES (?, 'Application Shortlisted! 🎉', 'ByteWave Technologies has shortlisted your application for Graduate Software Engineer Trainee.', 'application_status', 'applications.html')
        """, (stud0_user_id,))

        cursor.execute("""
            INSERT INTO notifications (user_id, title, message, type, link)
            VALUES (?, 'New Hyperlocal Match! 📍', 'ByteWave Technologies posted a Graduate Software Engineer role in Hitec City matching your B.Tech qualification.', 'new_job', 'jobs.html')
        """, (stud0_user_id,))

        print(f"Successfully seeded: {len(EMPLOYERS_DATA)} employers, {len(STUDENTS_DATA)} students, {len(JOBS_DATA)} jobs, and dense interaction history!")

if __name__ == '__main__':
    seed_database(force=True)
